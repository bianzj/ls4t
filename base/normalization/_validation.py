"""Quality decoding shared by normalization array and raster APIs."""
import numpy as np

from base.quality import QualityFlag


def quality_flags(values):
    """Never turn missing/fractional/out-of-range QA values into GOOD by casting."""
    values = np.asarray(values, dtype=float)
    valid = np.isfinite(values) & (values >= 0) & (values <= 65535) & (values == np.floor(values))
    return np.where(valid, values, int(QualityFlag.INPUT_INVALID)).astype(np.uint16)
