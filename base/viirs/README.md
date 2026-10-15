# VIIRS standard methods

The public stages cover prepared-array extraction, projection, explicit scene
mosaic, region-before/region-after processing and split-window LST using M15
and M16. GeoTIFF is the new prepared/data/result format; legacy prepared NPZ
files remain readable. Native VNP/VJ1 NetCDF decoding and bow-tie handling
remain in `cases/viirs/` until validated as a machine-independent reader.
