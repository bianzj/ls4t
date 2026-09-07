"""AHI prepared-array extraction stage; cases own native NetCDF decoding."""

from ahi.ahi_data import AhiDataProduct, SPEC
from base.dual_thermal import extract_sensor_products


def ahi_extract(
    indir_raw=None,
    outdir_data=None,
    years=None,
    months=None,
    days=None,
    overwrite=None,
) -> None:
    extract_sensor_products(
        SPEC,
        AhiDataProduct,
        indir_raw=indir_raw,
        outdir_data=outdir_data,
        years=years,
        months=months,
        days=days,
        overwrite=overwrite,
    )
