"""Grid indexing copied from the historical SLSTR LST helper."""
import os
import numpy as np
def drop_file_cache(path):
    # Advisory page-cache release is Linux-specific and has no effect on Windows.
    if not hasattr(os, "posix_fadvise") or not hasattr(os, "O_CLOEXEC"):
        return
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
        try:
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        finally:
            os.close(fd)
    except OSError:
        pass
def grid_index(lat, lon, nrow, ncol, res):
    row = np.rint((90.0 - lat) / res).astype(np.int32)
    col = np.rint((lon + 180.0) / res).astype(np.int32)
    np.clip(row, 0, nrow - 1, out=row)
    np.clip(col, 0, ncol - 1, out=col)
    return row, col
