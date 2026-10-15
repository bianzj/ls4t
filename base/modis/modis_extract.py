"""MODIS prepared-array extraction stage; cases own native HDF decoding."""

from base.dual_thermal import extract_sensor_products
from base.modis.modis_data import ModisDataProduct, SPEC


def modis_extract(
    indir_raw=None,
    outdir_data=None,
    years=None,
    months=None,
    days=None,
    overwrite=None,
) -> None:
    extract_sensor_products(
        SPEC,
        ModisDataProduct,
        indir_raw=indir_raw,
        outdir_data=outdir_data,
        years=years,
        months=months,
        days=days,
        overwrite=overwrite,
    )
