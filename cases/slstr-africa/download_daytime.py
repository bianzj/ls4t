"""Index/download S3A SLSTR RBT daytime scenes, 2017-2025.

Credentials: CDSE_USERNAME/CDSE_PASSWORD, CDSE_REFRESH_TOKEN, or a private
JSON file at ~/.config/ls4t/cdse.json with username/password or refresh_token.
Raw SEN3 archives retain both viewing directions and all original bands.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import math
import netrc
import os
from pathlib import Path
import re
import shutil
import sqlite3
import time
import tempfile
import zipfile
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from shapely import make_valid
from shapely.geometry import box, mapping, shape, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

CATALOGUE = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
DOWNLOAD = "https://download.dataspace.copernicus.eu/odata/v1/Products"
TOKEN = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
ECOREGIONS = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/Resolve_Ecoregions/FeatureServer/0/query"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
EARTHDATA_COLLECTION = "C1287064221-LAADS"
NASA_HOSTS = {"ladsweb.modaps.eosdis.nasa.gov", "urs.earthdata.nasa.gov", "data.laadsdaac.earthdatacloud.nasa.gov"}
PATTERN = re.compile(r"S3A_SL_1_RBT____(\d{8}T\d{6})_(\d{8}T\d{6})_(\d{8}T\d{6})_")


class CDSESession(requests.Session):
    def rebuild_auth(self, prepared_request, response):
        original = response.request.headers.get("Authorization")
        super().rebuild_auth(prepared_request, response)
        source, target = urlparse(response.request.url), urlparse(prepared_request.url)
        groups = [{"download.dataspace.copernicus.eu", "zipper.dataspace.copernicus.eu"}, NASA_HOSTS]
        if original and target.scheme == "https" and any(source.hostname in g and target.hostname in g for g in groups):
            prepared_request.headers["Authorization"] = original


def session():
    s = CDSESession()
    s.mount("https://", HTTPAdapter(max_retries=Retry(
        total=6, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"], respect_retry_after_header=True)))
    return s


def write_json(path, obj):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def now():
    return datetime.now(timezone.utc).isoformat()


def connect(root):
    db = sqlite3.connect(root / "manifest.sqlite", timeout=60)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
      CREATE TABLE IF NOT EXISTS months (
        month TEXT PRIMARY KEY, finished TEXT, queried INTEGER, selected INTEGER);
      CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, sensing_key TEXT NOT NULL,
        acquired TEXT NOT NULL, month TEXT NOT NULL, baseline INTEGER,
        processed TEXT, catalog_bytes INTEGER, online INTEGER, sza REAL,
        metadata TEXT NOT NULL, state TEXT DEFAULT 'queued',
        local_path TEXT, sha256 TEXT, downloaded_bytes INTEGER, error TEXT,
        finished TEXT);
      CREATE INDEX IF NOT EXISTS sensing_idx ON products(sensing_key);
    """)
    return db


class ForestRegion:
    def __init__(self, geometries):
        self.geometries = []
        for geometry in geometries:
            self.geometries.extend(list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry])
        self.tree = STRtree(self.geometries)
        bounds = [g.bounds for g in self.geometries]
        self.bounds = (min(b[0] for b in bounds), min(b[1] for b in bounds),
                       max(b[2] for b in bounds), max(b[3] for b in bounds))

    def intersects(self, footprint):
        return len(self.tree.query(footprint, predicate="intersects")) > 0


def region(root):
    path = root / "africa_tropical_moist_forests.geojson"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        with session() as s:
            r = s.get(ECOREGIONS, params={
                "where": "BIOME_NUM = 1 AND REALM = 'Afrotropic'",
                "outFields": "ECO_ID,ECO_NAME,BIOME_NUM,BIOME_NAME,REALM",
                "outSR": 4326, "f": "geojson"}, timeout=(30, 180))
            r.raise_for_status()
            data = r.json()
        if not data.get("features") or data.get("exceededTransferLimit"):
            raise RuntimeError("Incomplete ecoregion response")
        # Clip to the geographical tropics. This excludes temperate South Africa.
        tropical_africa = box(-19, -23.436, 56, 23.436)
        selected = []
        for feature in data["features"]:
            geometry = make_valid(shape(feature["geometry"])).intersection(tropical_africa)
            if not geometry.is_empty:
                feature["geometry"] = mapping(geometry)
                selected.append(feature)
        data = {"type": "FeatureCollection", "features": selected,
                "provenance": {"source": ECOREGIONS, "version": "RESOLVE 2017",
                    "filter": "BIOME_NUM=1 AND REALM='Afrotropic'",
                    "clip_bounds": [-19, -23.436, 56, 23.436],
                    "note": "Ecoregion extent, not annual observed forest cover; includes Madagascar and tropical African islands."}}
        write_json(path, data)
    return ForestRegion([make_valid(shape(f["geometry"])) for f in data["features"]])


def solar_zenith(when, lon, lat):
    """NOAA approximation at the scene footprint's representative point."""
    hour = when.hour + when.minute / 60 + when.second / 3600
    days = 366 if calendar.isleap(when.year) else 365
    gamma = 2 * math.pi / days * (when.timetuple().tm_yday - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma) - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma))
    dec = (0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma))
    ha = math.radians(((hour * 60 + eqtime + 4 * lon) % 1440) / 4 - 180)
    phi = math.radians(lat)
    cosine = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(ha)
    return math.degrees(math.acos(max(-1, min(1, cosine))))


def candidate(product, roi, query_orbit_direction=None, require_descending=True):
    match = PATTERN.match(product["Name"])
    if not match or "_NT_" not in product["Name"]:
        return None
    attrs = {a["Name"]: a["Value"] for a in product.get("Attributes", [])}
    if require_descending and attrs.get("orbitDirection", query_orbit_direction) != "DESCENDING":
        return None
    footprint = make_valid(shape(product["GeoFootprint"]))
    if not roi.intersects(footprint):
        return None
    point = footprint.representative_point()
    start = datetime.fromisoformat(product["ContentDate"]["Start"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(product["ContentDate"]["End"].replace("Z", "+00:00"))
    sza = solar_zenith(start + (end - start) / 2, point.x, point.y)
    if sza >= 90:
        return None
    baseline = int(product["Name"].rsplit("_", 1)[-1].split(".")[0])
    return (product["Id"], product["Name"], "_".join(match.group(1, 2)),
            product["ContentDate"]["Start"], start.strftime("%Y-%m"), baseline,
            match.group(3), product.get("ContentLength", 0), int(product.get("Online", False)),
            sza, json.dumps(product, separators=(",", ":")))


def index_month(root, year, month, roi):
    label = f"{year}-{month:02d}"
    with connect(root) as db:
        if db.execute("SELECT 1 FROM months WHERE month=?", (label,)).fetchone():
            return label, "cached"
    end = f"{year + 1}-01" if month == 12 else f"{year}-{month + 1:02d}"
    west, south, east, north = roi.bounds
    wkt = f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"
    filters = ["Collection/Name eq 'SENTINEL-3'", "startswith(Name,'S3A_SL_1_RBT')",
        f"ContentDate/Start ge {label}-01T00:00:00Z",
        f"ContentDate/Start lt {end}-01T00:00:00Z",
        "Attributes/OData.CSC.StringAttribute/any(a:a/Name eq 'orbitDirection' and a/OData.CSC.StringAttribute/Value eq 'DESCENDING')",
        "Attributes/OData.CSC.StringAttribute/any(a:a/Name eq 'timeliness' and a/OData.CSC.StringAttribute/Value eq 'NT')",
        f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')"]
    params = {"$filter": " and ".join(filters),
              "$select": "Id,Name,ContentLength,Online,ContentDate,GeoFootprint,Checksum,S3Path",
              "$top": 1000, "$orderby": "ContentDate/Start asc"}
    url, queried, selected, visited = CATALOGUE, 0, 0, set()
    print(f"Querying {label}", flush=True)
    with session() as s, connect(root) as db:
        while url:
            if urlparse(url).hostname != "catalogue.dataspace.copernicus.eu":
                raise RuntimeError("Unexpected catalogue pagination host")
            r = s.get(url, params=params, timeout=(30, 180))
            r.raise_for_status()
            data = r.json()
            print(f"Received {label}: {len(data.get('value', []))} catalogue records", flush=True)
            if "value" not in data:
                raise RuntimeError("Invalid catalogue response")
            rows = []
            for product in data["value"]:
                if product["Id"] in visited:
                    continue
                visited.add(product["Id"])
                queried += 1
                # The server-side filter constrains orbitDirection; avoid expanding
                # every attribute (including a duplicate, long coordinates string).
                row = candidate(product, roi, query_orbit_direction="DESCENDING")
                if row:
                    rows.append(row)
                    selected += 1
            db.executemany("""INSERT OR IGNORE INTO products
                (id,name,sensing_key,acquired,month,baseline,processed,catalog_bytes,online,sza,metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", rows)
            db.commit()
            next_url = data.get("@odata.nextLink")
            if next_url == url:
                raise RuntimeError("Catalogue repeated its pagination link")
            url, params = next_url, None
        db.execute("INSERT OR REPLACE INTO months VALUES (?,?,?,?)", (label, now(), queried, selected))
        db.commit()
    return label, selected


def credentials():
    path = Path(os.environ.get("CDSE_CREDENTIALS_FILE", str(Path.home() / ".config/ls4t/cdse.json")))
    config = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
    for field in ("username", "password", "refresh_token"):
        value = os.environ.get("CDSE_" + field.upper())
        if value:
            config[field] = value
    return config


def earthdata_token_path():
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
    return base / "LS4T/credentials/earthdata-token.dpapi"


def _token_dpapi(data, decrypt=False):
    """Protect the cache with the current Windows user's DPAPI identity."""
    if os.name != "nt":
        raise OSError("Encrypted token storage requires Windows DPAPI")
    import ctypes
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source, result = Blob(len(data), buffer), Blob()
    crypto = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    function = crypto.CryptUnprotectData if decrypt else crypto.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p if decrypt else wintypes.LPCWSTR,
                         ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                         wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    description = None if decrypt else "LS4T Earthdata download token"
    if not function(ctypes.byref(source), description, None, None, None, 1, ctypes.byref(result)):
        raise OSError("Windows could not protect or unlock the Earthdata token")
    try:
        return ctypes.string_at(result.data, result.size)
    finally:
        kernel.LocalFree(result.data)


def save_earthdata_token(token):
    token = token.strip()
    if not token or "\n" in token or "\r" in token:
        raise ValueError("Invalid Earthdata token format")
    encrypted = _token_dpapi(token.encode("utf-8"))
    path = earthdata_token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix="earthdata-token-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encrypted)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def load_earthdata_token():
    path = earthdata_token_path()
    if not path.exists():
        return None
    try:
        token = _token_dpapi(path.read_bytes(), decrypt=True).decode("utf-8").strip()
        if not token or "\n" in token or "\r" in token:
            raise ValueError("Invalid token")
        return token
    except (OSError, UnicodeError, ValueError):
        raise AuthenticationRequired("The saved Earthdata token could not be unlocked; enter it again on the local connection page.") from None


def earthdata_credentials():
    path = Path(os.environ.get("EARTHDATA_CREDENTIALS_FILE", str(Path.home() / ".config/ls4t/earthdata.json")))
    config = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
    for key in ("username", "password", "token"):
        value = os.environ.get("EARTHDATA_" + key.upper())
        if value:
            config[key] = value
    if os.environ.get("LAADS_TOKEN"):
        config.setdefault("token", os.environ["LAADS_TOKEN"])
    if not config.get("token"):
        saved = load_earthdata_token()
        if saved:
            config["token"] = saved
    if not (config.get("token") or (config.get("username") and config.get("password"))):
        for name in (".netrc", "_netrc"):
            path = Path.home() / name
            if path.exists():
                entry = netrc.netrc(str(path)).authenticators("urs.earthdata.nasa.gov")
                if entry:
                    config.update(username=entry[0], password=entry[2])
                    break
    if not (config.get("token") or (config.get("username") and config.get("password"))):
        path = Path.home() / "AppData/Roaming/earthdata-download/edd-database.sqlite3"
        if path.exists():
            with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
                row = db.execute("SELECT token FROM token WHERE token IS NOT NULL AND token!='' ORDER BY id DESC LIMIT 1").fetchone()
                if row:
                    config["token"] = row[0]
    return config


class EarthdataAuth:
    def __init__(self):
        self.config = earthdata_credentials()
        self.token = self.config.get("token")

    def get(self, force=False):
        if self.token and not force:
            return self.token
        c = self.config
        if not (c.get("username") and c.get("password")):
            raise AuthenticationRequired("Earthdata requires a valid token or active username/password.")
        r = requests.post("https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
                          auth=(c["username"], c["password"]), timeout=(30, 60))
        if r.status_code in (400, 401, 403):
            raise AuthenticationRequired("Earthdata rejected the account or application authorization.")
        r.raise_for_status()
        self.token = r.json()["access_token"]
        return self.token


def earthdata_product(entry):
    """Convert CMR metadata without assuming its BOTH flag means daytime."""
    name = entry.get("producer_granule_id", "")
    if not name.startswith("S3A_SL_1_RBT____") or not name.endswith(".zip") or "_NT_" not in name:
        return None
    links = [link["href"] for link in entry.get("links", [])
             if link.get("rel", "").endswith("/data#") and not link.get("inherited")
             and urlparse(link.get("href", "")).scheme == "https"
             and urlparse(link.get("href", "")).hostname in NASA_HOSTS]
    if not links:
        raise ValueError("CMR S3A granule has no supported NASA download link")
    polygons = []
    for group in entry.get("polygons", []):
        for text in group:
            values = list(map(float, text.split()))
            pairs = list(zip(values[1::2], values[0::2]))  # CMR polygon order is latitude,longitude.
            # Unwrap antimeridian footprints so they cannot falsely span Africa.
            if pairs and max(x for x, _ in pairs) - min(x for x, _ in pairs) > 180:
                pairs = [(x + 360 if x < 0 else x, y) for x, y in pairs]
            if len(pairs) >= 4:
                polygons.append(make_valid(Polygon(pairs)))
    if not polygons:
        raise ValueError("CMR S3A granule has no polygon footprint")
    return {"Id": entry["id"], "Name": name[:-4] + ".SEN3",
            "ContentDate": {"Start": entry["time_start"], "End": entry["time_end"]},
            "GeoFootprint": mapping(unary_union(polygons)),
            "ContentLength": round(float(entry.get("granule_size", 0)) * 1024 ** 2),
            "Online": entry.get("online_access_flag", False), "DownloadUrl": links[0],
            "SourceProvider": "NASA Earthdata LAADS", "SourceMetadata": entry}


def index_month_earthdata(root, year, month, roi):
    label = f"{year}-{month:02d}"
    with connect(root) as db:
        if db.execute("SELECT 1 FROM months WHERE month=?", (label,)).fetchone():
            return label, "cached"
    end = f"{year + 1}-01" if month == 12 else f"{year}-{month + 1:02d}"
    params = {"collection_concept_id": EARTHDATA_COLLECTION,
              "temporal": f"{label}-01T00:00:00Z,{end}-01T00:00:00Z",
              "bounding_box": ",".join(map(str, roi.bounds)),
              "page_size": 1000, "sort_key[]": ["start_date", "producer_granule_id"]}
    # LAADS labels many S3A granules BOTH. Do not apply CMR's DAY filter.
    headers, seen, queried, selected = {}, set(), 0, 0
    print(f"Querying Earthdata {label}", flush=True)
    with session() as s, connect(root) as db:
        while True:
            r = s.get(CMR, params=params, headers=headers, timeout=(30, 180))
            r.raise_for_status()
            if r.headers.get("CMR-Timed-Out", "false").lower() == "true":
                raise RuntimeError("CMR query timed out; month remains incomplete")
            entries = r.json()["feed"]["entry"]
            if not entries:
                break
            rows = []
            for entry in entries:
                if entry["id"] in seen:
                    continue
                seen.add(entry["id"])
                queried += 1
                if not f"{label}-01" <= entry["time_start"] < f"{end}-01":
                    continue
                product = earthdata_product(entry)
                if product is None:
                    continue
                row = candidate(product, roi, require_descending=False)
                if row:
                    rows.append(row)
                    selected += 1
            db.executemany("""INSERT OR IGNORE INTO products
                (id,name,sensing_key,acquired,month,baseline,processed,catalog_bytes,online,sza,metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", rows)
            db.commit()
            print(f"Earthdata {label}: {queried} queried, {selected} daytime rainforest candidates", flush=True)
            after = r.headers.get("CMR-Search-After")
            if not after or len(entries) < 1000:
                break
            if headers.get("CMR-Search-After") == after:
                raise RuntimeError("CMR repeated a pagination cursor")
            headers["CMR-Search-After"] = after
        db.execute("INSERT OR REPLACE INTO months VALUES (?,?,?,?)", (label, now(), queried, selected))
        db.commit()
    return label, selected


class AuthenticationRequired(RuntimeError):
    pass


class Auth:
    def __init__(self):
        self.config = credentials()
        self.token, self.expires = None, 0

    def get(self, force=False):
        if not force and self.token and time.time() < self.expires:
            return self.token
        c = self.config
        data = {"client_id": "cdse-public"}
        if c.get("refresh_token"):
            data.update(grant_type="refresh_token", refresh_token=c["refresh_token"])
        elif c.get("username") and c.get("password"):
            data.update(grant_type="password", username=c["username"], password=c["password"])
        else:
            raise AuthenticationRequired("CDSE credentials are required to download satellite files.")
        r = requests.post(TOKEN, data=data, timeout=(30, 60))
        if r.status_code in (400, 401):
            raise AuthenticationRequired("CDSE rejected the configured credentials.")
        r.raise_for_status()
        result = r.json()
        self.token = result["access_token"]
        self.expires = time.time() + result["expires_in"] - 45
        if result.get("refresh_token"):
            c["refresh_token"] = result["refresh_token"]
        return self.token


def transfer(s, url, destination, auth):
    """Resume partial files; only publish a fully checked ZIP as complete."""
    part = destination.with_suffix(destination.suffix + ".part")
    for attempt in range(6):
        try:
            offset = part.stat().st_size if part.exists() else 0
            headers = {"Authorization": "Bearer " + auth.get(), "Accept-Encoding": "identity"}
            if offset:
                headers["Range"] = f"bytes={offset}-"
            with s.get(url, headers=headers, stream=True, timeout=(30, 180)) as r:
                if r.status_code == 401:
                    auth.get(force=True)
                    continue
                if r.status_code == 416:
                    # Re-fetch rather than trusting an unverified partial archive.
                    part.unlink(missing_ok=True)
                    continue
                r.raise_for_status()
                if r.status_code == 206:
                    content_range = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", r.headers.get("Content-Range", ""))
                    if not content_range or int(content_range[1]) != offset:
                        raise RuntimeError("Invalid Content-Range")
                    expected = int(content_range[3])
                else:
                    offset = 0
                    expected = int(r.headers["Content-Length"]) if r.headers.get("Content-Length") else None
                with part.open("ab" if offset else "wb") as handle:
                    for chunk in r.iter_content(4 * 1024 * 1024):
                        if chunk:
                            handle.write(chunk)
                if expected is not None and part.stat().st_size != expected:
                    raise RuntimeError("Incomplete HTTP body")
            with zipfile.ZipFile(part) as archive:
                if not archive.namelist() or archive.testzip() is not None:
                    raise zipfile.BadZipFile("ZIP CRC verification failed")
            with part.open("rb") as handle:
                digest = hashlib.file_digest(handle, "sha256").hexdigest()
            part.replace(destination)
            return digest, destination.stat().st_size
        except AuthenticationRequired:
            raise
        except (requests.RequestException, OSError, RuntimeError, zipfile.BadZipFile):
            if attempt == 5:
                raise
            if part.exists() and zipfile.is_zipfile(part):
                # CRC failure requires a fresh copy; interrupted bodies retain .part.
                try:
                    with zipfile.ZipFile(part) as z:
                        corrupted = z.testzip() is not None
                    if corrupted:
                        part.unlink()
                except (OSError, zipfile.BadZipFile):
                    part.unlink(missing_ok=True)
            time.sleep(min(60, 2 ** (attempt + 1)))


def deduplicate(db):
    # Early RBT baselines can shift the same granule's timestamps by 2-3 s.
    # Require the same cycle/orbit and both endpoints within 10 s; adjacent
    # 180 s granules remain distinct. Keep all source rows for provenance.
    groups = {}
    for row in db.execute("SELECT id,name,baseline,processed,state FROM products"):
        match = PATTERN.match(row["name"])
        orbit = re.match(r"\d{4}_(\d{3})_(\d{3})_", row["name"][match.end():])
        if not orbit:
            raise ValueError("Unrecognized RBT cycle/orbit fields")
        orbit_key = (orbit[1], orbit[2])
        start = datetime.strptime(match[1], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).timestamp()
        end = datetime.strptime(match[2], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).timestamp()
        groups.setdefault(orbit_key, []).append((start, end, row))
    superseded = set()
    for rows in groups.values():
        rows.sort(key=lambda r: r[0])
        for i, first in enumerate(rows):
            for j in range(i + 1, len(rows)):
                second = rows[j]
                if second[0] - first[0] > 10:
                    break
                if abs(second[1] - first[1]) > 10:
                    continue
                a, b = first[2], second[2]
                rank = lambda r: (r["baseline"], r["processed"], r["id"])
                loser = a if rank(a) < rank(b) else b
                if loser["state"] in ("queued", "failed"):
                    superseded.add(loser["id"])
    db.executemany("UPDATE products SET state='superseded' WHERE id=?", [(p,) for p in superseded])
    db.commit()


def report(root, state, error=None, period=(2017, 2025)):
    start_year, end_year = period
    date_bounds = (f"{start_year}-01-01", f"{end_year + 1}-01-01")
    month_bounds = (f"{start_year}-01", f"{end_year + 1}-01")
    expected_months = (end_year - start_year + 1) * 12
    with connect(root) as db:
        years = [dict(r) for r in db.execute("""SELECT substr(acquired,1,4) year,
            count(*) scenes, sum(catalog_bytes) catalog_bytes,
            min(acquired) first_acquisition, max(acquired) last_acquisition,
            sum(state='complete') downloaded, sum(coalesce(downloaded_bytes,0)) downloaded_bytes
            FROM products WHERE state!='superseded' AND acquired>=? AND acquired<?
            GROUP BY year ORDER BY year""", date_bounds)]
        months = db.execute("SELECT count(*) FROM months WHERE month>=? AND month<?", month_bounds).fetchone()[0]
        source = db.execute("SELECT metadata FROM products LIMIT 1").fetchone()
        provider = json.loads(source[0]).get("SourceProvider", "Copernicus CDSE") if source else None
    data = {"updated_utc": now(), "state": state, "error": error,
        "satellite": "S3A", "product": "SL_1_RBT___", "timeliness": "NT", "provider": provider,
        "period": [f"{start_year}-01-01", f"{end_year}-12-31"], "time_of_day": "day",
        "selection": "catalogue rainforest-footprint intersection AND scene representative-point solar zenith <90 degrees; CDSE additionally constrains descending orbit",
        "views": ["nadir", "oblique"], "months_indexed": months, "months_expected": expected_months,
        "catalogue_complete": months == expected_months, "years": years,
        "selected_scenes": sum(y["scenes"] for y in years),
        "downloaded_scenes": sum(y["downloaded"] for y in years),
        "estimated_raw_TB": round(sum(y["catalog_bytes"] or 0 for y in years) / 1e12, 3),
        "free_disk_TB": round(shutil.disk_usage(root).free / 1e12, 3),
        "note": "Catalogue bytes are an estimate; downloaded ZIPs require CRC checks and a local SHA256. No cloud screening; native files retain pixels outside the ecoregion. Baselines may vary between years."}
    write_json(root / "status.json", data)
    return data


def download(root, reserve_gb, period=(2017, 2025), provider="cdse"):
    update = partial(report, root, period=period)
    auth = EarthdataAuth() if provider == "earthdata" else Auth()
    auth.get()  # Fail explicitly before claiming that any transfer started.
    failures = 0
    with session() as s, connect(root) as db:
        rows = db.execute("""SELECT * FROM products WHERE state IN ('queued','failed')
            AND acquired>=? AND acquired<? ORDER BY acquired""",
            (f"{period[0]}-01-01", f"{period[1] + 1}-01-01")).fetchall()
        for row in rows:
            if not row["online"]:
                db.execute("UPDATE products SET state='failed',error='offline in catalogue' WHERE id=?", (row["id"],))
                failures += 1
                db.commit()
                continue
            if shutil.disk_usage(root).free < reserve_gb * 1e9 + max(row["catalog_bytes"] * 2, 2e9):
                update("disk_space_required")
                return
            target = root / "raw" / row["acquired"][:4] / (row["name"] + ".zip")
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                url = json.loads(row["metadata"])["DownloadUrl"] if provider == "earthdata" else f"{DOWNLOAD}({row['id']})/$value"
                if provider == "earthdata" and (urlparse(url).scheme != "https" or urlparse(url).hostname not in NASA_HOSTS):
                    raise ValueError("Untrusted Earthdata download URL")
                digest, size = transfer(s, url, target, auth)
                db.execute("""UPDATE products SET state='complete',local_path=?,sha256=?,
                    downloaded_bytes=?,error=NULL,finished=? WHERE id=?""",
                    (str(target), digest, size, now(), row["id"]))
                print(f"Downloaded {row['name']} ({size / 1e6:.1f} MB)", flush=True)
            except AuthenticationRequired:
                raise
            except Exception as exc:
                failures += 1
                db.execute("UPDATE products SET state='failed',error=? WHERE id=?",
                           (type(exc).__name__, row["id"]))
            db.commit()
            update("downloading")
    update("download_incomplete" if failures else "complete")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--provider", choices=["cdse", "earthdata"], default="cdse")
    parser.add_argument("--start-year", type=int, default=2017)
    parser.add_argument("--end-year", type=int, default=2020)
    parser.add_argument("--workers", type=int, default=3, help="Catalogue workers; satellite downloads are serial")
    parser.add_argument("--reserve-gb", type=float, default=100)
    args = parser.parse_args()
    if not 2017 <= args.start_year <= args.end_year <= 2025:
        parser.error("Year range must be within 2017-2025 and ordered")
    if args.root is None:
        args.root = Path(fr"D:\data\sentinel3\africa_rainforest_day_{args.start_year}_{args.end_year}_earthdata") if args.provider == "earthdata" else Path(r"D:\data\sentinel3\africa_rainforest_day_2017_2025")
    period = (args.start_year, args.end_year)
    update = partial(report, args.root, period=period)
    args.root.mkdir(parents=True, exist_ok=True)
    # Cross-platform process lock is released automatically if a process exits.
    with (args.root / ".download.lock").open("a+b") as lock:
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            lock.write(b"0")
            lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            with connect(args.root) as db:
                source = db.execute("SELECT metadata FROM products LIMIT 1").fetchone()
                if source:
                    existing_earthdata = json.loads(source[0]).get("SourceProvider") == "NASA Earthdata LAADS"
                    if existing_earthdata != (args.provider == "earthdata"):
                        raise ValueError("Use a separate output root for each catalogue provider")
            update("indexing")
            roi = region(args.root)
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                indexer = index_month_earthdata if args.provider == "earthdata" else index_month
                futures = [pool.submit(indexer, args.root, year, month, roi)
                           for year in range(args.start_year, args.end_year + 1) for month in range(1, 13)]
                for future in as_completed(futures):
                    try:
                        month, count = future.result()
                    except Exception:
                        # Make failures observable immediately, even if workers are still finishing.
                        update("catalogue_failed")
                        for pending in futures:
                            pending.cancel()
                        raise
                    print(f"Indexed {month}: {count}", flush=True)
                    update("indexing")
            with connect(args.root) as db:
                deduplicate(db)
            update("catalogue_ready")
            if args.download:
                download(args.root, args.reserve_gb, period=period, provider=args.provider)
        except AuthenticationRequired as exc:
            update("authentication_required", str(exc))
            print(str(exc), flush=True)
            return 2
        except Exception as exc:
            update("failed", type(exc).__name__)
            raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
