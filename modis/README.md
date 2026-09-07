# MODIS standard methods

The public stages are `modis_extract`, `modis_project`, `modis_merge`,
`modis_data_region` / `modis_result_region`, and `modis_lst`. Thermal channels
are MODIS 31 and 32.

`modis_extract` currently accepts reviewed prepared-array NPZ files with kelvin
`bt31_k` / `bt32_k`, geolocation, view zenith, cloud mask and UTC metadata.
Mission HDF decoding remains in `cases/modis/` until it is validated without
machine paths. Cases also own scene grouping, study bounds and execution paths.
