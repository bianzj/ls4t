# African tropical rainforest S3A acquisition

Run `start_download.ps1` to download the requested 2017-2020 daytime subset
(48 months) from NASA Earthdata LAADS. Use `-Provider earthdata
-StartYear 2017 -EndYear 2020` to set the scope explicitly. `-Provider cdse`
selects the previously implemented Copernicus route and its separate manifest.
Existing monthly catalogue records and completed files are reused on restart.

- Satellite: Sentinel-3A only; SLSTR `SL_1_RBT___`, non-time-critical (NT).
- Acquisition dates: 2017-01-01 through 2020-12-31, inclusive, UTC, as requested.
- Earthdata collection: `C1287064221-LAADS`, `S3A_SL_1_RBT`, version 1,
  LAADS ArchiveSet 450. Download links are obtained from current CMR metadata,
  including migrated Earthdata Cloud URLs, rather than guessed archive paths.
- Daytime: estimated solar zenith below 90 degrees at a representative point
  of the scene footprint. CDSE also constrains descending orbit. This selects daytime
  granules; it does not apply a pixel-level solar mask to the original data.
- Many LAADS S3A granules are labelled `BOTH` in CMR, so a server-side `DAY`
  filter would discard valid daytime scenes. Solar geometry is applied locally.
- A live CMR query on 2026-10-20 returned 2017 availability beginning on
  January 17, not January 1. The manifest/status retain actual acquisition dates;
  missing archive coverage must not be described as a complete observation year.
- Region: RESOLVE 2017, Afrotropic moist broadleaf forest biome (1), clipped
  to tropical Africa, 23.436 S to 23.436 N. This covers Congo, Guinea,
  tropical East African forests, Madagascar and African tropical islands.
  The boundary describes ecoregions, not measured annual forest cover.
- Full original SEN3 ZIPs retain nadir/oblique data and all bands, geolocation,
  geometry, quality flags and metadata. These are raw observations, not LST
  retrievals. Scenes include nonforest pixels outside the selected ecoregions.
- No cloud-cover threshold is imposed. Pixel-level cloud screening belongs
  in the later extraction/retrieval pipeline.
- For matching cycle/orbit and sensing intervals (both endpoints within
  10 seconds, to handle early baseline timing shifts), keep the highest
  available baseline, then the latest processing time. Baselines may
  differ across years; this does not establish a homogeneous climate record.

Default Earthdata output: `D:\data\sentinel3\africa_rainforest_day_2017_2020_earthdata`.
The CDSE output remains `D:\data\sentinel3\africa_rainforest_day_2017_2025`.
`status.json` distinguishes catalogue completion, authentication requirements,
active transfers, disk limits, failures and download completion.
`manifest.sqlite` retains source metadata and per-file status, local SHA256,
verified ZIP size, processing baseline and download errors. The `months`
table distinguishes unqueried months from successfully queried empty months.

For Earthdata, set `EARTHDATA_TOKEN` (or `LAADS_TOKEN`), or
`EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`. Alternatively use the private
file `%USERPROFILE%\.config\ls4t\earthdata.json` with `token` or
`username`/`password` fields. `EARTHDATA_CREDENTIALS_FILE` selects another
private file. Standard `.netrc`/`_netrc` URS entries and Earthdata Download's
saved token are also supported. Active username/password credentials use
the official `find_or_create_token` endpoint without revoking existing tokens.

When Earthdata is already signed in inside the browser but no script token is
configured, `connect_earthdata.py` provides a temporary loopback-only connection
page. In the Earthdata profile, choose **Generate Token**, then paste the token
into the local password field. The helper verifies the ZIP signature from a
real pending NASA archive, saves the token using Windows DPAPI, and resumes
the 2017-2020 download automatically. The encrypted cache is stored at
`%LOCALAPPDATA%\LS4T\credentials\earthdata-token.dpapi`, outside the repository
and data archive. Subsequent downloads read it automatically under the same
Windows user. Plaintext tokens are never saved in files or logs. Explicit
environment/configuration tokens take precedence over the encrypted cache.
An unreadable or expired token requires re-entry. The form requires a per-run
nonce and same-origin submission, and expires after 30 minutes. Opening the
form or signing in to the website does not itself start a satellite transfer.

For CDSE, set `CDSE_USERNAME` and `CDSE_PASSWORD`, or `CDSE_REFRESH_TOKEN`, in the launch
environment. Alternatively put `username`/`password` or `refresh_token` in a
private JSON file at `%USERPROFILE%\.config\ls4t\cdse.json`. The optional
`CDSE_CREDENTIALS_FILE` environment variable selects a different private file.
Credentials and tokens are never written to this repository or the logs.

The downloader reserves 100 GB of free space and stops with
`disk_space_required` if the next full product cannot fit. No data are removed
automatically. A generated manifest does not mean satellite data are downloaded.

Sources:

- https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/S3A_SL_1_RBT/
- https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
- https://urs.earthdata.nasa.gov/documentation/for_users/user_token
- https://documentation.dataspace.copernicus.eu/APIs/OData.html
- https://sentiwiki.copernicus.eu/web/slstr-products
- https://developers.google.com/earth-engine/datasets/catalog/RESOLVE_ECOREGIONS_2017
