"""SLSTR daily merge stage."""

from pathlib import Path

from base.parameters import require_parameters
from base.spatial import mosaic_observations
from slstr.slstr_data import read_data_product, write_data_product


# Execution paths and years are supplied by cases.
SLSTR_PROJECT_ROOT = None
SLSTR_MERGE_ROOT = None
PROJECT_YEAR_TEMPLATE = "{year}/project"
MERGE_YEAR_TEMPLATE = "{year}/merge"
YEARS = None
OVERWRITE = False


def _year_directory(root, template, year):
    return Path(root).expanduser() / template.format(year=int(year))


def _merge_products(items):
    if not items:
        raise ValueError("没有可合并的 SLSTR 产品")
    return mosaic_observations(items, primary_field="bt8_k")


def slstr_merge(
    indir_project=None,
    outdir_merge=None,
    years=None,
    overwrite=None,
) -> None:
    """Merge projected scenes by day and view."""

    if indir_project is None:
        indir_project = SLSTR_PROJECT_ROOT
    if outdir_merge is None:
        outdir_merge = SLSTR_MERGE_ROOT
    if years is None:
        years = YEARS
    if overwrite is None:
        overwrite = OVERWRITE

    require_parameters(indir_project=indir_project, outdir_merge=outdir_merge, years=years)
    for year in years:
        input_year = _year_directory(indir_project, PROJECT_YEAR_TEMPLATE, year)
        output_year = _year_directory(outdir_merge, MERGE_YEAR_TEMPLATE, year)
        if not input_year.is_dir():
            continue
        groups = {}
        for input_path in sorted(input_year.rglob("*.tif")):
            item = read_data_product(input_path)
            if not item.start_time:
                raise ValueError(f"SLSTR 产品缺少时间：{input_path}")
            date = item.start_time[:10]
            groups.setdefault((date, item.view), []).append(item)
        for (date, view), items in sorted(groups.items()):
            output_path = output_year / date[5:7] / date[8:10] / f"{view}.tif"
            if output_path.exists() and not overwrite:
                continue
            print(f"[{date}] 合并 {len(items)} 景 {view} 数据")
            write_data_product(output_path, _merge_products(items))
