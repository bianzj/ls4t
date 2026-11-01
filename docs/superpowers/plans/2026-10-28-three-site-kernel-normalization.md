# Three-site single-day kernel normalization

**Goal:** Execute an auditable AHI/SLSTR single-day LSF-RL experiment at DM, HZZ and SDQ, with all AHI observations held out.

**Architecture:** A standalone case under `cases/ahi-slstr/heihe/three-site-kernel/`; copy the LSF and RL formulas from the current LS4T kernels with source hashes. Fit within-pixel SLSTR oblique-minus-nadir kernel differences, using site-specific coefficients and spatial-block splits. Keep input and output outside the repository.

**Spec:** User-approved kernel-driven discussion in this chat; three core sites requested. Sites selected from existing Heihe station table: DM, HZZ, SDQ. No component retrieval, no ground-based fitting or date selection.

**Constraints:** Existing canonical checkout contains unrelated work; add only new case/test/docs files, do not reset, move, commit or modify those changes. Reuse the current branch and filesystem; the user requests direct implementation without confirmation. Data: explicit `H:/data/rs/data2019`; outputs explicitly within existing `D:/cases/ls4t`. No imports from base or other cases in delivered case.

## Tasks
- [x] Audit source grids, encoding, QA and site coordinates; select one common day by availability and QA only.
- [x] Add numerical tests for pair-difference recovery, rank rejection, block isolation, nadir identity and AHI leakage invariance; observe missing-implementation failure.
- [x] Implement standalone extraction, fixed-width LSF / LSF-RL fits, target-angle correction and diagnostics. Partition only within a single acquisition per site; retain site/land-cover heterogeneity limits.
- [x] Run real three-site experiment; export configurations, source receipts, pair rows, coefficients, common-cohort metrics, station diagnostics and plots externally.
- [x] Run focused tests and source-independent replay verification; review leakage, QA, grid and reproducibility; report actual results including failures.

## Review focus
- Coarse or repeated geometry must not be mistaken for independent angular samples.
- No missing QA, invalid HHMM, cloud flags or no-data values treated as valid.
- Near-constant geometry may leave two kernel coefficients unidentifiable; flag/reject rather than hide with ridge.
- Date/model/width selection must not use AHI residuals or ground temperatures.
- Station-centre inference must be excluded from fit and large/extrapolated corrections reported explicitly.

## Execution ledger
- Source relocation discovered: previous E:/remote-sensing path no longer exists; current Heihe archive and station coordinates verified on H:.
- Standalone case will be implemented in place to retain current uncommitted kernel sources and repository conventions.
- Seven scientific invariant tests were observed failing for the missing implementation and then passing.
- Geometry/NDVI-only summer audit found no date with independent calibration support at SDQ after the 10 km central-block buffer. Before any real-data kernel fit, extend the search to the full available AHI May-October 2019 season. Preserve all cloud/homogeneity/split rules; do not relax based on AHI residuals.
- First eligible common scene after 365 date/platform checks: 2019-10-30 S3A. Selected before kernel fitting. DM/HZZ UTC04:02, SDQ03:59; AHI04:00. 1781 two-kilometre footprints; 98/117/123 independent-block holdout footprints at DM/HZZ/SDQ respectively.
- Independent review found and fixed a nonlinear-aggregation error: fit and correct at native 1 km resolution, then aggregate corrected radiances to 2 km. Added failing/passing native-background counterexample. Also added midnight rejection and strict model-status/input-checksum/prediction replay checks. No scientific thresholds or date were changed after outcomes.
- Final result: `D:/cases/ls4t/ahi-slstr-three-site-kernel/run_20261028_213251_812268`. Initial diagnostic run `run_20261028_212313_217718` is superseded by native-correction results.
- Main LSF-RL spatial-holdout AHI/SLSTR RMSE: DM 2.346 -> 19.722 K and HZZ 5.394 -> 32.291 K (both rejected by predeclared 10 K correction bound); SDQ 1.299 -> 1.027 K (accepted). Do not present diagnostic rejected temperatures as valid products. Single-kernel LSF comparison retained without selecting by held-out AHI score.
- Verification: 33 selected tests pass; 20 source files including station table hash-verified unchanged; 13 output checksums verified; independent metric recomputation and rejection-to-NaN checked. External frozen-code replay `replay_20261028_213307_597649`: max coefficient change 3.23e-11, prediction agreement within 1e-7 K. Both final figures visually inspected. Independent review closed with no major/important unresolved issue.
