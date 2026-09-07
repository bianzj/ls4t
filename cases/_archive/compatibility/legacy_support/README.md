# Legacy support

This directory isolates the historical `base.util_*` and radiative-transfer
modules from the maintained root-level `base` package. It is not installed with
LS4T.

Use it only for legacy reproduction:

```bash
PYTHONPATH=cases/_archive/compatibility/legacy_support:. \
  python cases/_archive/legacy/unclassified/<script>.py
```
