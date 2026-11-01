"""Configure only the Python runtime shipped with the LS4T application."""
import os
from pathlib import Path
import sys

_root = Path(sys.executable).resolve().parent
_dll_handles = []
for _folder in (_root, _root / "DLLs", _root / "Library" / "bin"):
    if _folder.is_dir():
        os.environ["PATH"] = str(_folder) + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            _dll_handles.append(os.add_dll_directory(str(_folder)))
os.environ["GDAL_DATA"] = str(_root / "Library" / "share" / "gdal")
os.environ["PROJ_DATA"] = str(_root / "Library" / "share" / "proj")
os.environ["PROJ_LIB"] = os.environ["PROJ_DATA"]
os.environ.setdefault("MPLBACKEND", "Agg")
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")
