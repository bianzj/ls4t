"""Make GDAL and LAPACK DLLs loadable when the conda interpreter runs un-activated."""

import os
import sys
from pathlib import Path

_root = Path(sys.executable).parent
for _sub in ("Library/mingw-w64/bin", "Library/usr/bin", "Library/bin", "bin"):
    _path = _root / _sub
    if _path.is_dir():
        os.environ["PATH"] = str(_path) + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(_path))
