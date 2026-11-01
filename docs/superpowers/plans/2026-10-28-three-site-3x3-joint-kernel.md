# Three-site 3x3 joint kernel implementation

Goal: implement the user's 3x3 window and two SLSTR views plus one AHI request on the already selected 2019-10-30 date. All three sites retain their actual station coordinates.

Design: a 3x3 window on the AHI 2 km archived grid (~6x6 km) contains up to nine complete matched triplets. SLSTR is archived at 1 km: each AHI footprint contains four corresponding SLSTR cells per view. Fit two shared LSF/RL coefficients with fixed RL k=1 and eliminate each footprint's temperature baseline. Evaluate the nonlinear footprint correction exactly by correcting native SLSTR temperatures before radiance aggregation. AHI now participates in calibration; evaluation is leave-one-complete-footprint-out (especially the station centre), not an independent AHI holdout. Do not count four subpixels as four AHI observations.

Files: new standalone `cases/ahi-slstr/heihe/three-site-kernel-3x3/` with copied audited `functions.py` and `prepare.py`, a joint solver `joint.py`, a driver `run.py`, explicit config and README. The prior 30 km case/results remain intact. External outputs under the existing D:/cases/ls4t hierarchy.

Constraints: keep the date fixed; do not select parameters/days on heldout residuals; no sensor-offset fit or claims of spectral harmonization. Keep existing cloud, time, grid checks; omit NDVI similarity filtering inside the explicitly requested 3x3 window and record that change. Use paired residuals normalized by equal 1 K coarse-view noise assumption: (o-n)/sqrt(2) and (a-(n+o)/2)/sqrt(1.5). This assumes equal independent view error for fitting weights, not measured uncertainty. Crossvalidation shares a small local neighborhood and is not independent regional/ground validation.

Checklist
- [x] Add failing tests for nonlinear native support closure, offset-invariant joint coefficients, leave-one-footprint exclusion, unique 3x3 geometry and invalid sample rejection.
- [x] Copy only needed case-local functions/adapters; implement joint residual and 3x3 extraction without cross-case imports.
- [x] Run three-site experiment, preserve raw window grids/QA and export all-fit and leave-one-out results separately.
- [x] Test, replay outside repository, independently verify metrics/grid and visually inspect plots; request focused independent review.

Ledger: User directly requests implementation without confirmation; continue in authoritative existing checkout and preserve all unrelated changes. Prior tests and data receipts are references, not proof of this new solver.

Completed: 2019-10-30 S3A + AHI, all three sites have exactly 9 complete triplets. DM/HZZ match within2min, SDQ1min. Per-site all-window two-coefficient fits have 27 coarse-view inputs and18 contrasts;54 leave-one-out fits across three sites and two model variants each use8 triplets, with all heldout views excluded.

Final canonical output: `D:/cases/ls4t/ahi-slstr-three-site-kernel-3x3/run_20261028_215846_312715`. Independent copied-code replay: `replay_20261028_215925_364587`; coefficients, models.json and predictions.csv identical. Earlier exploratory runs remain for provenance and are superseded by the delivery manifest.

AHI-minus-SLSTR-nadir footprint-LOO RMSE: DM2.508784->0.795271K, HZZ1.340399->1.479671K; SDQ3.106967->2.258678K is diagnostic only because all9 SDQ corrections fail the predeclared native10K correction bound. DM centre heldout difference2.522958->0.162447K. Do not describe AHI as independent validation now that it is a calibration input.

39 focused tests passed. Native-temperature QA regression observed failing then passing. Review identified CSV float parsing instability; round_trip parsing restores exact replay without changing thresholds.20 source files and11 output hashes verified, exact3x3 grid and all54 excluded-footprint lists checked, metrics recomputed independently, rejected usable outputs confirmedNaN, final plot visually inspected. Independent reviewer confirmed both findings closed.

Station replacement (user request, 2026-10-28): HZZ replaced with AR (100.4643 E, 38.0473 N). Original 2019-10-30 S3A had 8 SLSTR-valid AR footprints but zero AHI-QA-valid triplets; retained as run_20261028_232557_864423. Without changing QA thresholds or scoring model residuals, scan dates ascending from 2019-05-01, S3A then S3B, and select the first acquisition with nine complete triplets at each of DM/AR/SDQ: 2019-05-12 S3B. Candidate audit: site_replacement_AR_selection_20261028.json in the output parent.

Replacement canonical output: run_20261028_233133_228292; standalone copied-code replay: replay_20261028_233148_892367. All 39 focused tests passed again; output and source hashes verified, model/prediction files exactly reproduced, all 3x3 grids and heldout exclusions checked. DM footprint-LOO RMSE 3.343->1.104 K, SDQ 2.138->1.141 K, both 9/9 accepted. AR 1.169->0.905 K is diagnostic only: 0/9 pass the native 10 K correction bound. Do not interpret this as validated AR normalization. Delivery manifest now points to this replacement run; original HZZ results remain unchanged.
