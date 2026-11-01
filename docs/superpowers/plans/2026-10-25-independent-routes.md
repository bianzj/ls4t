# Independent routes correction

User explicitly requested component retrieval and normalization be separate routes.
No confirmation required; implementation updates existing canonical GUI in place.

- [x] Component route computes temperatures and fit diagnostics only; no reference geometry.
- [x] Independent normalization backend accepts existing LST and view angles. Fit a one-parameter secant slope from same-sensor angular pairs, or supply a calibrated slope. No known-input/component solver dependency.
- [x] Separate endpoint, sample, parameters, actions, result schemas and exports.
- [x] Per-route browser drafts and results; no automatic route chaining.
- [x] Controlled tests and HTTP interface separation tests; legacy retrieval values unchanged.
- [x] Desktop/mobile and route-switch browser QA; independent review. Incomplete route drafts restore without invoking import validation.

The new angle sample uses frozen existing LST. It is exploratory single-case
secant calibration with cross-sensor transfer warnings, not ground validation.
