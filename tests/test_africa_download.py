"""Downloader contract checks; live catalogue/credential checks are separate."""
import hashlib
import importlib.util
import io
from pathlib import Path
from datetime import datetime, timezone
import zipfile
import subprocess
import sys

import pytest

requests = pytest.importorskip("requests")
pytest.importorskip("shapely")
from shapely.geometry import box, mapping

spec = importlib.util.spec_from_file_location(
    "africa_download", Path(__file__).resolve().parents[1] / "cases/slstr-africa/download_daytime.py")
download = importlib.util.module_from_spec(spec)
spec.loader.exec_module(download)


def product(hour=10, direction="DESCENDING", satellite="S3A", baseline=3):
    start = f"20170320T{hour:02d}0000"
    end = f"20170320T{hour:02d}0300"
    return {"Id": "scene", "Name": f"{satellite}_SL_1_RBT____{start}_{end}_20181003T235019_0179_012_349______LR1_R_NT_{baseline:03d}.SEN3",
            "ContentDate": {"Start": f"2017-03-20T{hour:02d}:00:00Z", "End": f"2017-03-20T{hour:02d}:03:00Z"},
            "Attributes": [{"Name": "orbitDirection", "Value": direction}],
            "ContentLength": 100, "Online": True,
            "GeoFootprint": mapping(box(-1, -1, 1, 1))}


def test_selection_rejects_night_other_satellite_and_nonforest():
    roi = download.ForestRegion([box(-0.5, -0.5, 0.5, 0.5)])
    assert download.candidate(product(), roi) is not None
    assert download.candidate(product(hour=22), roi) is None
    assert download.candidate(product(direction="ASCENDING"), roi) is None
    assert download.candidate(product(satellite="S3B"), roi) is None
    outside = download.ForestRegion([box(20, 20, 21, 21)])
    assert download.candidate(product(), outside) is None


def test_solar_rule_uses_longitude_and_utc():
    when = datetime(2020, 3, 20, 10, tzinfo=timezone.utc)
    assert download.solar_zenith(when, 30, 0) < 5
    assert download.solar_zenith(when, -150, 0) > 170


def test_baseline_preference_and_month_coverage(tmp_path):
    roi = download.ForestRegion([box(-1, -1, 1, 1)])
    with download.connect(tmp_path) as db:
        for baseline in [3, 4]:
            p = product(baseline=baseline)
            p["Id"] = str(baseline)
            row = download.candidate(p, roi)
            db.execute("""INSERT INTO products
                (id,name,sensing_key,acquired,month,baseline,processed,catalog_bytes,online,sza,metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", row)
        download.deduplicate(db)
        states = dict(db.execute("SELECT id,state FROM products"))
        assert states == {"3": "superseded", "4": "queued"}
    status = download.report(tmp_path, "catalogue_ready")
    assert status["years"][0]["scenes"] == 1
    assert not status["catalogue_complete"]
    assert status["downloaded_scenes"] == 0


def test_early_baseline_timing_shift_is_not_a_new_observation(tmp_path):
    roi = download.ForestRegion([box(-1, -1, 1, 1)])
    with download.connect(tmp_path) as db:
        for baseline, delta in [(2, 0), (3, 3)]:
            p = product(baseline=baseline)
            p["Id"] = str(baseline)
            if delta:
                p["Name"] = p["Name"].replace("T100000", "T100003").replace("T100300", "T100303")
                p["ContentDate"] = {"Start": "2017-03-20T10:00:03Z", "End": "2017-03-20T10:03:03Z"}
            row = download.candidate(p, roi)
            db.execute("""INSERT INTO products
                (id,name,sensing_key,acquired,month,baseline,processed,catalog_bytes,online,sza,metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", row)
        download.deduplicate(db)
        assert dict(db.execute("SELECT id,state FROM products")) == {"2": "superseded", "3": "queued"}


def test_year_scope_restricts_downloads_and_status(tmp_path, monkeypatch):
    roi = download.ForestRegion([box(-1, -1, 1, 1)])
    with download.connect(tmp_path) as db:
        for year in (2020, 2021):
            p = product()
            p["Id"] = str(year)
            p["Name"] = p["Name"].replace("2017", str(year))
            p["ContentDate"] = {k: v.replace("2017", str(year)) for k, v in p["ContentDate"].items()}
            db.execute("""INSERT INTO products
                (id,name,sensing_key,acquired,month,baseline,processed,catalog_bytes,online,sza,metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", download.candidate(p, roi))
            db.execute("INSERT INTO months VALUES (?,?,?,?)", (f"{year}-03", "now", 1, 1))
    seen = []
    monkeypatch.setattr(download, "Auth", Auth)
    monkeypatch.setattr(download, "transfer", lambda s, url, target, auth: (seen.append(url) or "hash", 100))
    download.download(tmp_path, reserve_gb=0, period=(2017, 2020))
    assert len(seen) == 1 and "(2020)" in seen[0]
    status = download.report(tmp_path, "checked", period=(2017, 2020))
    assert status["period"] == ["2017-01-01", "2020-12-31"]
    assert status["months_expected"] == 48
    assert status["months_indexed"] == 1
    assert status["selected_scenes"] == 1
    assert [row["year"] for row in status["years"]] == ["2020"]


class Auth:
    def get(self, **kwargs):
        return "test-token"


class Response:
    def __init__(self, status, body, headers):
        self.status_code, self.body, self.headers = status, body, headers

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError()

    def iter_content(self, size):
        yield self.body


def archive_bytes():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("scene.SEN3/xfdumanifest.xml", "test payload")
    return data.getvalue()


def test_resume_partial_zip_and_check_hash(tmp_path):
    body = archive_bytes()
    target = tmp_path / "scene.zip"
    partial = tmp_path / "scene.zip.part"
    partial.write_bytes(body[:30])

    class Session:
        def get(self, url, headers, **kwargs):
            assert headers["Range"] == "bytes=30-"
            return Response(206, body[30:], {"Content-Range": f"bytes 30-{len(body)-1}/{len(body)}"})

    sha, size = download.transfer(Session(), "https://download.dataspace.copernicus.eu/test", target, Auth())
    assert sha == hashlib.sha256(body).hexdigest()
    assert size == len(body)
    assert target.read_bytes() == body
    assert not partial.exists()


def test_server_ignoring_range_replaces_partial(tmp_path):
    body = archive_bytes()
    target = tmp_path / "scene.zip"
    (tmp_path / "scene.zip.part").write_bytes(b"wrong partial")

    class Session:
        def get(self, url, **kwargs):
            return Response(200, body, {"Content-Length": str(len(body))})

    download.transfer(Session(), "https://download.dataspace.copernicus.eu/test", target, Auth())
    assert target.read_bytes() == body


def test_auth_only_forwarded_to_trusted_download_hosts():
    session = download.CDSESession()
    response = requests.Response()
    response.request = requests.Request("GET", "https://download.dataspace.copernicus.eu/a",
        headers={"Authorization": "Bearer test"}).prepare()
    trusted = requests.Request("GET", "https://zipper.dataspace.copernicus.eu/b").prepare()
    session.rebuild_auth(trusted, response)
    assert trusted.headers["Authorization"] == "Bearer test"
    other = requests.Request("GET", "https://example.org/b", headers={"Authorization": "Bearer test"}).prepare()
    session.rebuild_auth(other, response)
    assert "Authorization" not in other.headers


def cmr_entry(hour=10):
    p = product(hour=hour)
    return {"id": "G123-LAADS", "producer_granule_id": p["Name"].replace(".SEN3", ".zip"),
        "time_start": p["ContentDate"]["Start"], "time_end": p["ContentDate"]["End"],
        "day_night_flag": "BOTH", "granule_size": "1.5", "online_access_flag": True,
        "polygons": [["-1 -1 -1 1 1 1 1 -1 -1 -1"]],
        "links": [{"rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                   "href": "https://data.laadsdaac.earthdatacloud.nasa.gov/prod-lads/test.zip"}]}


def test_cmr_both_flag_is_filtered_using_solar_geometry():
    roi = download.ForestRegion([box(-1, -1, 1, 1)])
    day = download.earthdata_product(cmr_entry(10))
    night = download.earthdata_product(cmr_entry(22))
    assert download.candidate(day, roi, require_descending=False)
    assert download.candidate(night, roi, require_descending=False) is None
    assert day["ContentLength"] == 1572864
    assert day["SourceMetadata"]["day_night_flag"] == "BOTH"


def test_cmr_latitude_longitude_order_and_dateline():
    entry = cmr_entry()
    entry["polygons"] = [["-5 20 -5 25 5 25 5 20 -5 20"]]
    assert download.shape(download.earthdata_product(entry)["GeoFootprint"]).bounds == (20, -5, 25, 5)
    entry["polygons"] = [["-5 175 -5 -175 5 -175 5 175 -5 175"]]
    polygon = download.shape(download.earthdata_product(entry)["GeoFootprint"])
    assert not polygon.intersects(box(-20, -24, 56, 24))


def test_earthdata_auth_does_not_cross_to_copernicus():
    session = download.CDSESession()
    response = requests.Response()
    response.request = requests.Request("GET", "https://data.laadsdaac.earthdatacloud.nasa.gov/test",
        headers={"Authorization": "Bearer test"}).prepare()
    urs = requests.Request("GET", "https://urs.earthdata.nasa.gov/test").prepare()
    session.rebuild_auth(urs, response)
    assert urs.headers["Authorization"] == "Bearer test"
    cdse = requests.Request("GET", "https://download.dataspace.copernicus.eu/test",
        headers={"Authorization": "Bearer test"}).prepare()
    session.rebuild_auth(cdse, response)
    assert "Authorization" not in cdse.headers


@pytest.mark.skipif(download.os.name != "nt", reason="Windows DPAPI")
def test_token_cache_is_encrypted_and_survives_process_restart(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("EARTHDATA_CREDENTIALS_FILE", str(tmp_path / "no-config.json"))
    for name in ("EARTHDATA_TOKEN", "LAADS_TOKEN", "EARTHDATA_USERNAME", "EARTHDATA_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    fake_token = "unit-test-earthdata-token-no-real-credentials"
    path = download.save_earthdata_token(fake_token)
    assert fake_token.encode() not in path.read_bytes()
    assert download.load_earthdata_token() == fake_token
    code = ("import importlib.util; "
            f"s=importlib.util.spec_from_file_location('d',{str(spec.origin)!r}); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            f"assert m.earthdata_credentials()['token']=={fake_token!r}; print('cache_ok')")
    child = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
    assert child.returncode == 0
    assert child.stdout.strip() == "cache_ok"


@pytest.mark.skipif(download.os.name != "nt", reason="Windows DPAPI")
def test_corrupt_token_cache_requires_reentry_without_deleting_it(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    path = download.earthdata_token_path()
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not-a-dpapi-blob")
    with pytest.raises(download.AuthenticationRequired, match="could not be unlocked"):
        download.load_earthdata_token()
    assert path.read_bytes() == b"not-a-dpapi-blob"


def test_explicit_earthdata_token_takes_precedence_over_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("EARTHDATA_CREDENTIALS_FILE", str(tmp_path / "no-config.json"))
    monkeypatch.setenv("EARTHDATA_TOKEN", "explicit-test-token")
    monkeypatch.delenv("LAADS_TOKEN", raising=False)
    def unexpected_cache_read():
        raise AssertionError("Explicit credentials should not read the cache")
    monkeypatch.setattr(download, "load_earthdata_token", unexpected_cache_read)
    assert download.earthdata_credentials()["token"] == "explicit-test-token"
