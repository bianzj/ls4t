# SLSTR Amazon three-component daytime feasibility trial

This case is adapted from the tracked `cases/slstr/slstr_lsct3_bayes_scene.py` at LS4T commit `9c17aa2ada8e5da7ca902b02ae6f3fc66cb34d90` (original SHA-256 in config.json). The historical code was absent from the working tree; this is a separate trial case and has not been established as byte-identical to the code that generated previous products.

Changes: paths point to existing Windows input and H: LAI; the output root is isolated from source and historical results; the Linux cache hint is a no-op on Windows; batched `numpy.linalg.solve` uses explicit column vectors for NumPy 2; provenance and QA were added. Existing LST is input and is not recomputed. In addition to three independent components, `soil.tif` is the oblique-direction soil mixture, not a fourth independent component.

The current user-selected quality policy is daytime only (0 <= solar zenith < 90 degrees), with a 285 K (11.85 C) lower threshold. If either view's input LST is below 285 K, remove both observations at that grid position before any 5x5 accumulation. Require both views to pass at the output center. If any of the three retrieved component temperatures is below 285 K, set all four output bands to NoData=0. Values equal to 285 K pass. Temperatures are rejected rather than clipped to the threshold; source LST files remain unchanged. The inverse objective and fixed two-step solver are unchanged.

Current trial output: `E:/lsct/lsct3/feasibility_20261101_day285K`. The previous unfiltered trial remains at `E:/lsct/lsct3/feasibility_20261101_numpy2`; `diagnose_cloud_cold.py` explicitly reads that preserved trial's report to reproduce its diagnostic. Monthly products are not reprocessed by this case. This is an empirical temperature screen, not a complete cloud classification or independent accuracy validation.

Set a new nonexistent `output_root` in config.json before rerunning, to prevent accidental overwrites. From PowerShell:

```powershell
$env:PATH='C:/work/miniconda/envs/python311;C:/work/miniconda/envs/python311/Library/bin;C:/work/miniconda/envs/python311/Scripts;'+$env:PATH
$env:PYTHONPATH='C:/work/ls4t'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
C:/work/miniconda/envs/python311/python.exe -B C:/work/ls4t/cases/slstr/amazon-3component-feasibility/run.py
```

Output files are on the native oblique swath grid; their transform is pixel-index based, so use the included lat_obliq.tif/lon_obliq.tif to geolocate. LAI and geolocation encode scale factors; inspect input metadata. Agreement with existing product is not independent scientific validation. The method has no posterior uncertainty bands; it can produce extreme soil estimates.
