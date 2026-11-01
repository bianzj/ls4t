# Known-input retrieval and directional workbench

Goal: keep the existing batch UI and add an executable, independently callable
known-LAI/TCWV/emissivity workflow with a real remote-sensing AHI + SLSTR example.

User requested direct implementation without confirmation. Work in the authoritative
checkout because the current GUI and normalization work are uncommitted; preserve
all unrelated changes. No production jobs, source archives or data are modified.

Design: existing Python HTTP server + separate vanilla JS workbench. Slate/white
workspace, teal actions, soil orange and canopy green in the angular chart. Left:
fixed inputs and fit controls; right: observations, component results, direction
curve, residuals and provenance. Keep batch tasks as a separate navigation tab.

- [x] Backend: test physical recovery, fixed-input invariance, reference-angle
  identity, missing/invalid inputs, rank-deficient geometry and holdout isolation.
  Implement `base/known_inputs.py` using existing split-window and Hom RT modules,
  bounded temperature-only least squares and explicit per-sensor wavelengths.
- [x] Sample: extract a compact, geolocated real case from E:/remote-sensing;
  record units, timestamp decoding, pairing, cloud mask and file hashes. Known
  parameters used as scenario assumptions must be labeled. Keep AHI held out by
  default; numerical closure is not ground accuracy or spectral harmonization.
- [x] API/UI: add workbench endpoints, fixed parameters, observation editing,
  fit/optimization/reference controls, results/curve and JSON export/import.
- [x] Verify: targeted regression suite, real sample replay, browser interaction,
  desktop/mobile screenshots, independent final review and concise delivery.

Review focus: rank deficiency; changed inputs invalidate displayed results;
LST inputs must not be atmosphere-corrected twice; out-of-range coefficient lookup;
sample timestamps and footprints must be explicit and not inferred as exact.

Implementation record:
- Selected 2019-01-01 02:50 UTC, 112.000463E / 32.006484N; selection uses only
  coverage, mask and distance to predetermined centre. 24 source hashes recorded.
- Known scenario parameters fixed; default SLSTR-only fit with AHI held out.
- Real sample heldout residual 0.323685 K; no claim of ground accuracy.
- 46 focused tests passed, including API, malformed input, offline replay,
  source-pixel scaling, 2/3-component controlled cases, priors and legacy imports.
- Old batch imports failed because case files had already been removed before
  this task. Preserved two byte-identical committed drivers under gui/legacy,
  with commit/hash manifest; did not restore deleted case directories.
- Independent review found partial JSON import could leave old results current.
  Added validation before mutation and invalidation before field writes; tested
  malformed import in the browser and confirmed unchanged previous configuration.
- No merge/push or data-production run. Existing branch and unrelated edits retained.
