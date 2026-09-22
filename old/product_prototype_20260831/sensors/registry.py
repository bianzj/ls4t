from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensorDefinition:
    name: str
    platform_type: str
    thermal_wavelengths_um: tuple[float, ...]
    supports_multi_angle: bool
    native_l1_reader: str


_SENSORS: dict[str, SensorDefinition] = {}


def register_sensor(definition: SensorDefinition) -> None:
    key = definition.name.upper()
    if key in _SENSORS:
        raise ValueError(f"sensor already registered: {definition.name}")
    _SENSORS[key] = definition


def get_sensor(name: str) -> SensorDefinition:
    try:
        return _SENSORS[name.upper()]
    except KeyError as error:
        raise KeyError(f"unknown sensor {name!r}; available: {', '.join(list_sensors())}") from error


def list_sensors() -> tuple[str, ...]:
    return tuple(sorted(_SENSORS))


for _definition in (
    SensorDefinition("AATSR", "polar", (10.8, 12.0), True, "aatsr"),
    SensorDefinition("SLSTR", "polar", (10.85, 12.0), True, "slstr"),
    SensorDefinition("MSG", "geostationary", (10.8, 12.0), False, "msg"),
    SensorDefinition("AHI", "geostationary", (10.4, 11.2, 12.4), False, "ahi"),
    SensorDefinition("MODIS", "polar", (11.0, 12.0), False, "modis"),
    SensorDefinition("VIIRS", "polar", (10.76, 12.01), False, "viirs"),
):
    register_sensor(_definition)

