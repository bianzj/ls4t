"""SLSTR native-array extraction stage."""

from pathlib import Path

from base.parameters import require_parameters
from slstr.slstr_data import extract_native_product, write_extracted_product


# Execution paths and years are supplied by cases.
SLSTR_RAW_ROOT = None
SLSTR_EXTRACT_ROOT = None
RAW_YEAR_TEMPLATE = "{year}/raw"
EXTRACT_YEAR_TEMPLATE = "{year}/extract"
YEARS = None
VIEWS = ("nadir", "oblique")
OVERWRITE = False


def _year_directory(root, template, year):
    return Path(root).expanduser() / template.format(year=int(year))


def slstr_extract(
    indir_raw=None,
    outdir_extract=None,
    years=None,
    views=None,
    overwrite=None,
) -> None:
    """Read SEN3 products and save native arrays without grid reconstruction."""

    if indir_raw is None:
        indir_raw = SLSTR_RAW_ROOT
    if outdir_extract is None:
        outdir_extract = SLSTR_EXTRACT_ROOT
    if years is None:
        years = YEARS
    if views is None:
        views = VIEWS
    if overwrite is None:
        overwrite = OVERWRITE

    require_parameters(indir_raw=indir_raw, outdir_extract=outdir_extract, years=years)
    for year in years:
        input_year = _year_directory(indir_raw, RAW_YEAR_TEMPLATE, year)
        output_year = _year_directory(outdir_extract, EXTRACT_YEAR_TEMPLATE, year)
        if not input_year.is_dir():
            print(f"跳过不存在的目录：{input_year}")
            continue
        products = sorted(path for path in input_year.rglob("*.SEN3") if path.is_dir())
        for index, product in enumerate(products):
            print(f"[{year}] {index + 1}/{len(products)} 提取 {product.name}")
            for view in views:
                output = output_year / product.name / view
                if output.exists() and any(output.glob("*.tif")) and not overwrite:
                    continue
                write_extracted_product(output, extract_native_product(product, view=view))
