from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from typing import Any

import numpy as np

from .io import read_product, write_product
from .normalization import NormalizationInput, NormalizationProfile, normalize_temperature
from .normalization.fusion import fuse_l3n
from .normalization.harmonization import SensorHarmonization
from .normalization.pipeline import NormalizationResult
from .operations import validate_product
from .products import fused_product, normalized_product, profile_from_product, product_filename
from .production.cli import add_product_parsers
from .sensors import list_sensors


def _json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def _normalize(args: argparse.Namespace) -> int:
    config = _json(args.config)
    profile = NormalizationProfile(**config["profile"])
    with np.load(args.input, allow_pickle=False) as source:
        optional_flags = source["quality_flag"] if "quality_flag" in source.files else None
        item = NormalizationInput(
            sensor=config["sensor"],
            grid_id=config["input_grid_id"],
            temporal_interval=config["input_temporal_interval"],
            temperature_k=source["temperature_k"],
            uncertainty_k=source["uncertainty_k"],
            view_zenith_deg=source["view_zenith_deg"],
            solar_zenith_deg=source["solar_zenith_deg"],
            relative_azimuth_deg=source["relative_azimuth_deg"],
            local_solar_time_hour=source["local_solar_time_hour"],
            directional_coefficients_k=source["directional_coefficients_k"],
            diurnal_amplitude_k=source["diurnal_amplitude_k"],
            diurnal_peak_hour=source["diurnal_peak_hour"],
            quality_flag=optional_flags,
        )
    harmonization = None
    if "harmonization" in config:
        harmonization = SensorHarmonization(**config["harmonization"])
    result = normalize_temperature(item, profile, harmonization=harmonization)
    product = normalized_product(
        result,
        start_time=config["start_time"],
        end_time=config["end_time"],
        algorithm_version=config["algorithm_version"],
        source_products=config.get("source_products", (args.input,)),
    )
    write_product(args.output, product)
    return 0


def _fuse(args: argparse.Namespace) -> int:
    products = [read_product(path) for path in args.inputs]
    sensor_names = [item.metadata.sensor.upper() for item in products]
    if len(set(sensor_names)) != len(sensor_names):
        raise ValueError("fusion inputs must contain at most one product per sensor")
    periods = {(item.metadata.start_time, item.metadata.end_time) for item in products}
    if len(periods) != 1:
        raise ValueError("fusion inputs must cover the same start_time and end_time")
    normalized: list[NormalizationResult] = []
    for product in products:
        profile = profile_from_product(product)
        if "lst" not in product.variables or "lst" not in product.uncertainty:
            raise ValueError("fusion requires L3N lst and lst uncertainty")
        normalized.append(
            NormalizationResult(
                product.metadata.sensor,
                product.variables["lst"],
                product.uncertainty["lst"],
                product.quality_flag,
                profile,
            )
        )
    result = fuse_l3n(
        normalized,
        innovation_threshold_sigma=args.innovation_sigma,
        minimum_sensors=args.minimum_sensors,
    )
    product = fused_product(
        result,
        start_time=products[0].metadata.start_time,
        end_time=products[0].metadata.end_time,
        algorithm_version=args.algorithm_version,
        source_products=tuple(args.inputs),
    )
    write_product(args.output, product)
    return 0


def _validate(args: argparse.Namespace) -> int:
    product = read_product(args.product)
    report = validate_product(product)
    output = {**asdict(report), "metadata": product.metadata.to_dict()}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def _inspect(args: argparse.Namespace) -> int:
    product = read_product(args.product)
    output = {
        "filename": product_filename(product.metadata),
        "metadata": product.metadata.to_dict(),
        "variables": {name: list(value.shape) for name, value in product.variables.items()},
        "uncertainty": {name: list(value.shape) for name, value in product.uncertainty.items()},
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ls4t", description="LS4T operational product processor")
    commands = parser.add_subparsers(dest="command", required=True)

    sensors = commands.add_parser("sensors", help="list configured sensors")
    sensors.set_defaults(handler=lambda _args: print("\n".join(list_sensors())) or 0)

    add_product_parsers(commands)

    normalize = commands.add_parser("normalize", help="produce a single-sensor L3N product")
    normalize.add_argument("input", help="standardized NPZ input")
    normalize.add_argument("output", help="L3N product path")
    normalize.add_argument("--config", required=True, help="operational JSON configuration")
    normalize.set_defaults(handler=_normalize)

    fusion = commands.add_parser("fuse", help="fuse compatible L3N products into LS4T_MULTI_L3N")
    fusion.add_argument("inputs", nargs="+", help="input L3N product files")
    fusion.add_argument("--output", required=True)
    fusion.add_argument("--algorithm-version", default="fusion-v1")
    fusion.add_argument("--innovation-sigma", type=float, default=4.0)
    fusion.add_argument("--minimum-sensors", type=int, default=1)
    fusion.set_defaults(handler=_fuse)

    validate = commands.add_parser("validate", help="validate an LS4T product")
    validate.add_argument("product")
    validate.set_defaults(handler=_validate)

    inspect = commands.add_parser("inspect", help="show product metadata and variables")
    inspect.add_argument("product")
    inspect.set_defaults(handler=_inspect)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (KeyError, ValueError, OSError, RuntimeError) as error:
        parser.error(str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
