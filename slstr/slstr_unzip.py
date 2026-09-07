"""SLSTR archive unpacking stage.

This stage only turns yearly ZIP archives into SEN3 directories.  It does not
extract arrays or run any temperature algorithm.
"""

from pathlib import Path
import shutil

from slstr.slstr_data import unpack_archive


# 修改本文件顶部参数即可手工运行解压阶段
SLSTR_ZIP_ROOT = Path("/media/hero/slstr-euro")
SLSTR_RAW_ROOT = Path("/media/hero/slstr-euro")
ZIP_YEAR_TEMPLATE = "{year}/zip"
RAW_YEAR_TEMPLATE = "{year}/raw"
YEARS = range(2021, 2026)
OVERWRITE = False
START_INDEX = 0


def _year_directory(root, template, year):
    return Path(root).expanduser() / template.format(year=int(year))


def slstr_unzip(
    indir_zip=None,
    outdir_raw=None,
    years=None,
    overwrite=None,
    start_index=None,
) -> None:
    """Unpack all SLSTR ZIP files in the selected yearly directories."""

    if indir_zip is None:
        indir_zip = SLSTR_ZIP_ROOT
    if outdir_raw is None:
        outdir_raw = SLSTR_RAW_ROOT
    if years is None:
        years = YEARS
    if overwrite is None:
        overwrite = OVERWRITE
    if start_index is None:
        start_index = START_INDEX

    for year in years:
        input_year = _year_directory(indir_zip, ZIP_YEAR_TEMPLATE, year)
        output_year = _year_directory(outdir_raw, RAW_YEAR_TEMPLATE, year)
        if not input_year.is_dir():
            print(f"跳过不存在的目录：{input_year}")
            continue
        archives = sorted(input_year.rglob("*.zip"))
        for index, archive in enumerate(archives):
            if index < int(start_index):
                continue
            destination = output_year / archive.stem
            if destination.exists() and any(destination.iterdir()):
                if not overwrite:
                    print(f"已存在，跳过：{destination}")
                    continue
                shutil.rmtree(destination)
            print(f"[{year}] {index + 1}/{len(archives)} 解压 {archive.name}")
            unpack_archive(archive, destination)


if __name__ == "__main__":
    slstr_unzip()
