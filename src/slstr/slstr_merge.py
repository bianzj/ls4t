"""SLSTR daily merge stage."""

from pathlib import Path

import numpy as np

from slstr.slstr_data import LST_AUXILIARY_FIELDS, SlstrDataProduct, read_data_product, write_data_product


# 修改本文件顶部参数即可手工运行合并阶段
SLSTR_PROJECT_ROOT = Path("/media/hero/slstr-euro")
SLSTR_MERGE_ROOT = Path("/media/hero/slstr-euro")
PROJECT_YEAR_TEMPLATE = "{year}/project"
MERGE_YEAR_TEMPLATE = "{year}/merge"
YEARS = range(2021, 2026)
OVERWRITE = False


def _year_directory(root, template, year):
    return Path(root).expanduser() / template.format(year=int(year))


def _merge_products(items):
    if not items:
        raise ValueError("没有可合并的 SLSTR 产品")
    shape = items[0].shape
    view = items[0].view
    if any(item.shape != shape or item.view != view for item in items):
        raise ValueError("合并产品必须具有相同网格和视角")

    def mean(name):
        with np.errstate(invalid="ignore"):
            return np.nanmean(
                np.stack([np.asarray(getattr(item, name), float) for item in items]), axis=0
            )

    optional = {
        name: mean(name) if all(getattr(item, name) is not None for item in items) else None
        for name in LST_AUXILIARY_FIELDS
    }
    starts = [item.start_time for item in items if item.start_time]
    ends = [item.end_time for item in items if item.end_time]
    result = SlstrDataProduct(
        source_product=";".join(item.source_product for item in items),
        view=view,
        start_time=min(starts) if starts else None,
        end_time=max(ends) if ends else None,
        bt8_k=mean("bt8_k"),
        bt9_k=mean("bt9_k"),
        view_zenith_deg=mean("view_zenith_deg"),
        latitude_deg=mean("latitude_deg"),
        longitude_deg=mean("longitude_deg"),
        cloud_mask=np.all(np.stack([item.cloud_mask for item in items]), axis=0),
        auxiliary_source=";".join(
            item.auxiliary_source for item in items if item.auxiliary_source
        ) or None,
        **optional,
    )
    result.validate()
    return result


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

    for year in years:
        input_year = _year_directory(indir_project, PROJECT_YEAR_TEMPLATE, year)
        output_year = _year_directory(outdir_merge, MERGE_YEAR_TEMPLATE, year)
        if not input_year.is_dir():
            continue
        groups = {}
        for input_path in sorted(input_year.rglob("*.npz")):
            item = read_data_product(input_path)
            if not item.start_time:
                raise ValueError(f"SLSTR 产品缺少时间：{input_path}")
            date = item.start_time[:10]
            groups.setdefault((date, item.view), []).append(item)
        for (date, view), items in sorted(groups.items()):
            output_path = output_year / date[5:7] / date[8:10] / f"{view}.npz"
            if output_path.exists() and not overwrite:
                continue
            print(f"[{date}] 合并 {len(items)} 景 {view} 数据")
            write_data_product(output_path, _merge_products(items))


if __name__ == "__main__":
    slstr_merge()
