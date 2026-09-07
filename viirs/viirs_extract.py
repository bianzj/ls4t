"""VIIRS prepared-array extraction stage; cases own native NetCDF decoding."""

from base.dual_thermal import extract_sensor_products
from viirs.viirs_data import SPEC, ViirsDataProduct


def viirs_extract(
    indir_raw=None,
    outdir_data=None,
    years=None,
    months=None,
    days=None,
    overwrite=None,
) -> None:
    extract_sensor_products(
        SPEC,
        ViirsDataProduct,
        indir_raw=indir_raw,
        outdir_data=outdir_data,
        years=years,
        months=months,
        days=days,
        overwrite=overwrite,
    )
