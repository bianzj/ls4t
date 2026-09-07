"""Small shared foundations for the flat LS4T source tree.

Sensor traversal and processing parameters do not belong here.  ``base`` only
contains stable numerical algorithms, product records and file I/O.
"""

from .calibration import (
    legacy_split_window_model,
    load_split_window_model,
    save_split_window_model,
)
from .files import read_npz_payload, write_npz_atomic
from .dual_thermal import (
    DualThermalDataProduct,
    DualThermalSensorSpec,
)
from .lsct import ComponentRetrievalResult, retrieve_components, retrieve_components_window
from .lst import (
    DualChannelObservation,
    SplitWindowModel,
    SplitWindowResult,
    retrieve_dual_channel_lst,
)
from .product import ProductLevel, ProductMetadata, TemperatureProduct, product_filename
from .product_io import read_product, write_product
from .quality import QualityFlag
from .radiometry import decode_temperature, inverse_planck, planck_radiance
from .spatial import (
    bounds_mask,
    crop_observation,
    crop_temperature_product,
    mosaic_observations,
    mosaic_temperature_products,
    project_observation,
    study_area_window,
)

__all__ = [
    "ComponentRetrievalResult",
    "DualChannelObservation",
    "DualThermalDataProduct",
    "DualThermalSensorSpec",
    "ProductLevel",
    "ProductMetadata",
    "QualityFlag",
    "SplitWindowModel",
    "SplitWindowResult",
    "TemperatureProduct",
    "bounds_mask",
    "crop_observation",
    "crop_temperature_product",
    "decode_temperature",
    "inverse_planck",
    "legacy_split_window_model",
    "load_split_window_model",
    "mosaic_observations",
    "mosaic_temperature_products",
    "planck_radiance",
    "product_filename",
    "project_observation",
    "read_npz_payload",
    "read_product",
    "retrieve_components",
    "retrieve_components_window",
    "retrieve_dual_channel_lst",
    "save_split_window_model",
    "study_area_window",
    "write_product",
    "write_npz_atomic",
]
