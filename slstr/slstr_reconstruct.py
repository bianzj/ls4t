"""SLSTR geometry and quality reconstruction stage."""

from pathlib import Path

from slstr.slstr_data import read_extracted_product, reconstruct_product, write_data_product


# 修改本文件顶部参数即可手工运行重建阶段
SLSTR_EXTRACT_ROOT = Path("/media/hero/slstr-euro")
SLSTR_RECONSTRUCT_ROOT = Path("/media/hero/slstr-euro")
EXTRACT_YEAR_TEMPLATE = "{year}/extract"
RECONSTRUCT_YEAR_TEMPLATE = "{year}/reconstruct"
YEARS = range(2021, 2026)
OVERWRITE = False


def _year_directory(root, template, year):
    return Path(root).expanduser() / template.format(year=int(year))


def slstr_reconstruct(
    indir_extract=None,
    outdir_reconstruct=None,
    years=None,
    overwrite=None,
) -> None:
    """Align extracted tie-point fields to each product's thermal grid."""

    if indir_extract is None:
        indir_extract = SLSTR_EXTRACT_ROOT
    if outdir_reconstruct is None:
        outdir_reconstruct = SLSTR_RECONSTRUCT_ROOT
    if years is None:
        years = YEARS
    if overwrite is None:
        overwrite = OVERWRITE

    for year in years:
        input_year = _year_directory(indir_extract, EXTRACT_YEAR_TEMPLATE, year)
        output_year = _year_directory(outdir_reconstruct, RECONSTRUCT_YEAR_TEMPLATE, year)
        if not input_year.is_dir():
            print(f"跳过不存在的目录：{input_year}")
            continue
        inputs = sorted(input_year.rglob("*.npz"))
        for index, input_path in enumerate(inputs):
            output_path = output_year / input_path.relative_to(input_year)
            if output_path.exists() and not overwrite:
                continue
            print(f"[{year}] {index + 1}/{len(inputs)} 重建 {input_path.name}")
            write_data_product(output_path, reconstruct_product(read_extracted_product(input_path)))


if __name__ == "__main__":
    slstr_reconstruct()
