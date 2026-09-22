"""Sensor-product entry points.

Product modules own complete product responsibilities.  For example,
``slstr_data`` owns SLSTR decoding and standardized storage, while
``slstr_lst`` owns SLSTR L2LST retrieval.  Shared physical algorithms remain
in the lower-level ``physics`` and ``retrieval`` packages.
"""

from .slstr_data import SlstrDataProduct, read_data_product, write_data_product
from .slstr_lst import produce_slstr_lst

__all__ = [
    "SlstrDataProduct",
    "produce_slstr_lst",
    "read_data_product",
    "write_data_product",
]
