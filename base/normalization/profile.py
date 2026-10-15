from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True)
class NormalizationProfile:
    """The contract that makes independently normalized fields compatible."""

    name: str
    version: str
    grid_id: str
    temporal_interval: str
    reference_view_zenith_deg: float = 0.0
    reference_solar_zenith_deg: float = 30.0
    reference_relative_azimuth_deg: float = 0.0
    reference_local_solar_time_hour: float = 13.5
    unit: str = "K"

    def __post_init__(self) -> None:
        if not self.name or not self.version or not self.grid_id or not self.temporal_interval:
            raise ValueError("name, version, grid_id and temporal_interval are required")
        if self.unit != "K":
            raise ValueError("L3N internal and product temperature unit must be K")
        if not 0 <= self.reference_view_zenith_deg < 90:
            raise ValueError("reference view zenith must be in [0, 90)")
        if not 0 <= self.reference_local_solar_time_hour < 24:
            raise ValueError("reference local solar time must be in [0, 24)")

    @property
    def profile_id(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
        return f"{self.name}-{self.version}-{digest}"

    def assert_compatible(self, other: "NormalizationProfile") -> None:
        if self.profile_id != other.profile_id:
            raise ValueError(
                f"normalization profiles are incompatible: {self.profile_id} != {other.profile_id}"
            )
