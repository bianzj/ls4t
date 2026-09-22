"""Thin command-line routing for sensor products.

Business logic stays in the corresponding product module.  The command names
mirror the products, not a generic end-to-end workflow.
"""

from __future__ import annotations

import argparse
import json

from .slstr_data import (
    add_lst_auxiliary,
    describe_data_product,
    read_data_product,
    read_native_product,
    unpack_archive,
    write_data_product,
)
from .slstr_lst import import_legacy_coefficients, produce_slstr_lst


def _slstr_data_unpack(args: argparse.Namespace) -> int:
    print(unpack_archive(args.archive, args.output_directory))
    return 0


def _slstr_data_read(args: argparse.Namespace) -> int:
    item = read_native_product(args.product_directory, view=args.view)
    write_data_product(args.output, item)
    return 0


def _slstr_data_add_aux(args: argparse.Namespace) -> int:
    item = read_data_product(args.input)
    result = add_lst_auxiliary(item, args.auxiliary)
    write_data_product(args.output, result)
    return 0


def _slstr_data_inspect(args: argparse.Namespace) -> int:
    print(json.dumps(describe_data_product(read_data_product(args.product)), indent=2))
    return 0


def _slstr_lst_import_coefficients(args: argparse.Namespace) -> int:
    import_legacy_coefficients(args.table, args.output, version=args.version)
    return 0


def _slstr_lst_retrieve(args: argparse.Namespace) -> int:
    produce_slstr_lst(
        args.input,
        args.coefficients,
        args.output,
        grid_id=args.grid_id,
        algorithm_version=args.algorithm_version,
        uncertainty_k=args.uncertainty_k,
        start_time=args.start_time,
        end_time=args.end_time,
    )
    return 0


def add_product_parsers(commands: argparse._SubParsersAction) -> None:
    data = commands.add_parser(
        "slstr-data",
        help="produce and inspect standardized SLSTR-DATA",
        description="SLSTR-DATA owns archive unpacking, native decoding and standardized storage.",
    )
    data_commands = data.add_subparsers(dest="slstr_data_command", required=True)

    unpack = data_commands.add_parser("unpack", help="unpack one SLSTR zip archive")
    unpack.add_argument("archive")
    unpack.add_argument("output_directory")
    unpack.set_defaults(handler=_slstr_data_unpack)

    read = data_commands.add_parser("read", help="decode one SEN3 view and store SLSTR-DATA")
    read.add_argument("product_directory")
    read.add_argument("output")
    read.add_argument("--view", choices=("nadir", "oblique"), default="nadir")
    read.set_defaults(handler=_slstr_data_read)

    auxiliary = data_commands.add_parser(
        "add-aux", help="attach grid-aligned emissivity, LAI and TCWV to SLSTR-DATA"
    )
    auxiliary.add_argument("input", help="decoded SLSTR-DATA NPZ")
    auxiliary.add_argument("auxiliary", help="auxiliary NPZ")
    auxiliary.add_argument("output", help="complete SLSTR-DATA NPZ")
    auxiliary.set_defaults(handler=_slstr_data_add_aux)

    inspect = data_commands.add_parser("inspect", help="show SLSTR-DATA completeness")
    inspect.add_argument("product")
    inspect.set_defaults(handler=_slstr_data_inspect)

    lst = commands.add_parser(
        "slstr-lst",
        help="produce SLSTR L2LST",
        description="SLSTR-LST owns coefficient import and land-surface-temperature retrieval.",
    )
    lst_commands = lst.add_subparsers(dest="slstr_lst_command", required=True)

    coefficients = lst_commands.add_parser(
        "import-coefficients", help="convert one reviewed legacy SLSTR coefficient table"
    )
    coefficients.add_argument("table")
    coefficients.add_argument("output")
    coefficients.add_argument("--version", required=True)
    coefficients.set_defaults(handler=_slstr_lst_import_coefficients)

    retrieve = lst_commands.add_parser("retrieve", help="produce one SLSTR L2LST NPZ")
    retrieve.add_argument("input", help="complete SLSTR-DATA NPZ")
    retrieve.add_argument("output", help="LS4T SLSTR L2LST NPZ")
    retrieve.add_argument("--coefficients", required=True)
    retrieve.add_argument("--grid-id", required=True)
    retrieve.add_argument("--algorithm-version", required=True)
    retrieve.add_argument("--uncertainty-k", required=True, type=float)
    retrieve.add_argument("--start-time", help="UTC ISO time; overrides SLSTR-DATA metadata")
    retrieve.add_argument("--end-time", help="UTC ISO time; overrides SLSTR-DATA metadata")
    retrieve.set_defaults(handler=_slstr_lst_retrieve)
