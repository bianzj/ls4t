"""Small named-band GeoTIFF helpers shared by raster products."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

import numpy as np


def _gdal():
    try:
        from osgeo import gdal
    except ModuleNotFoundError as error:
        raise RuntimeError("GeoTIFF I/O requires the GDAL Python bindings") from error
    gdal.UseExceptions()
    return gdal


def metadata(schema: str, **values: object) -> dict[str, str]:
    return {
        "LS4T_SCHEMA": schema,
        "LS4T_METADATA": json.dumps(values, ensure_ascii=False, sort_keys=True),
    }


def write_raster(
    path: str | Path,
    fields: dict[str, np.ndarray],
    metadata_values: dict[str, str],
    reference_path: str | Path | None = None,
) -> None:
    gdal = _gdal()
    destination = Path(path)
    if destination.suffix.lower() not in {".tif", ".tiff"}:
        raise ValueError(f"raster output must be GeoTIFF: {destination}")
    if not fields:
        raise ValueError("GeoTIFF must contain at least one field")
    arrays = {name: np.asarray(value) for name, value in fields.items()}
    shape = next(iter(arrays.values())).shape
    if any(value.ndim != 2 or value.shape != shape for value in arrays.values()):
        raise ValueError("all GeoTIFF fields must be matching two-dimensional arrays")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.", suffix=".tif", dir=destination.parent, delete=False
    ) as temporary_file:
        temporary = Path(temporary_file.name)
    temporary.unlink(missing_ok=True)
    dataset = gdal.GetDriverByName("GTiff").Create(
        str(temporary),
        int(shape[1]),
        int(shape[0]),
        len(arrays),
        gdal.GDT_Float32,
        options=["COMPRESS=DEFLATE"],
    )
    if dataset is None:
        raise RuntimeError(f"cannot create GeoTIFF: {destination}")
    try:
        if reference_path is not None:
            reference = gdal.Open(str(reference_path), gdal.GA_ReadOnly)
            if reference is None:
                raise FileNotFoundError(f"cannot open GeoTIFF reference: {reference_path}")
            transform = reference.GetGeoTransform()
            projection = reference.GetProjection()
            reference = None
            if transform:
                dataset.SetGeoTransform(transform)
            if projection:
                dataset.SetProjection(projection)
        for index, (name, value) in enumerate(arrays.items(), start=1):
            band = dataset.GetRasterBand(index)
            band.WriteArray(np.asarray(value, dtype=np.float32))
            band.SetDescription(name)
            band.SetMetadataItem("LS4T_FIELD", name)
        for key, value in metadata_values.items():
            dataset.SetMetadataItem(str(key), str(value))
        dataset.FlushCache()
    finally:
        dataset = None
    try:
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def read_raster(path: str | Path) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    gdal = _gdal()
    source = Path(path)
    if source.suffix.lower() not in {".tif", ".tiff"} or not source.is_file():
        raise FileNotFoundError(f"GeoTIFF does not exist: {source}")
    dataset = gdal.Open(str(source), gdal.GA_ReadOnly)
    if dataset is None:
        raise ValueError(f"cannot open GeoTIFF: {source}")
    try:
        fields = {}
        for index in range(1, dataset.RasterCount + 1):
            band = dataset.GetRasterBand(index)
            name = band.GetDescription() or band.GetMetadataItem("LS4T_FIELD")
            if not name and dataset.RasterCount == 1:
                name = source.stem
            if not name:
                raise ValueError(f"GeoTIFF band {index} has no field name: {source}")
            fields[name] = np.asarray(band.ReadAsArray()).copy()
        return fields, dataset.GetMetadata_Dict()
    finally:
        dataset = None


def write_temperature_product(
    path: str | Path,
    product,
    *,
    reference_path: str | Path | None = None,
) -> None:
    """Write a validated TemperatureProduct to named-band GeoTIFF."""

    product.validate()
    if Path(path).suffix.lower() == ".npz":
        from .data import write_product

        write_product(path, product)
        return
    fields = {
        f"variable__{name}": np.asarray(value)
        for name, value in product.variables.items()
    }
    fields["quality_flag"] = np.asarray(product.quality_flag)
    fields.update(
        {
            f"uncertainty__{name}": np.asarray(value)
            for name, value in product.uncertainty.items()
        }
    )
    write_raster(
        path,
        fields,
        metadata("ls4t.temperature/v1", product_metadata=product.metadata.to_dict()),
        reference_path,
    )


def read_temperature_product(path: str | Path):
    """Read a named-band GeoTIFF as a TemperatureProduct."""

    if Path(path).suffix.lower() == ".npz":
        from .data import read_product

        return read_product(path)

    from .product import ProductMetadata, TemperatureProduct

    fields, file_metadata = read_raster(path)
    if file_metadata.get("LS4T_SCHEMA") != "ls4t.temperature/v1":
        raise ValueError(f"not a temperature GeoTIFF: {path}")
    if "quality_flag" not in fields:
        raise ValueError(f"temperature GeoTIFF has no quality_flag: {path}")
    values = json.loads(file_metadata["LS4T_METADATA"])
    product = TemperatureProduct(
        ProductMetadata.from_dict(values["product_metadata"]),
        {
            name.removeprefix("variable__"): np.asarray(value, dtype=float)
            for name, value in fields.items()
            if name.startswith("variable__")
        },
        np.asarray(fields["quality_flag"], dtype=np.uint16),
        {
            name.removeprefix("uncertainty__"): np.asarray(value, dtype=float)
            for name, value in fields.items()
            if name.startswith("uncertainty__")
        },
    )
    product.validate()
    return product


# ---------------------------------------------------------------------------
# SLSTR case dependencies, moved verbatim from the run project on 2026-09-16
# ---------------------------------------------------------------------------
try:
    from osgeo import osr
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    osr = None


def getSRSPair(dataset):
    '''
    获得给定数据的投影参考系和地理参考系
    :param dataset: GDAL地理数据
    :return: 投影参考系和地理参考系
    '''
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(dataset.GetProjection())
    geosrs = prosrs.CloneGeogCS()
    return prosrs, geosrs


def writevrt_nadir(infile, datafile, xfile, yfile):
    write_vrt(infile, datafile, xfile, yfile, 1500, 1200)
    return 1


def writevrt_obliq(infile, datafile, xfile, yfile):
    write_vrt(infile, datafile, xfile, yfile, 900, 1200)
    return 1


def write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, noDataValue = 65535, bandnumber = 1):
    '''
    导出用于gdal vrt的配置文件
    # 与函数配合使用，outfile为转成的文件路径，resampleAlg为重采样的
    # dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour)
    :param vrtfile:  该配置文件名称
    :param datafile:  所要操作的文件名称
    :param xfile:  经度坐标文件 lon
    :param yfile:  纬度坐标文件 lat
    :param xscale:  列数
    :param yscale:  行数
    :param noDataValue: 无值填补
    :param bandnumber:  波段数据
    :return: 无
    '''
    f = open(vrtfile, 'w')
    f.write(r'<VRTDataset rasterXSize="%d"'%xscale + 'rasterYSize="%d">'%yscale)
    f.write('\n')
    f.write(r'  <Metadata domain="GEOLOCATION">')
    f.write('\n')
    f.write(r'    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AXIS["Long",EAST],AXIS["Lat",NORTH]]</MDI>')
    # f.write(r'    <MDI key="SRS">GEOGCS["WGS 84(DD)",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG", "9122"],AUTHORITY["EPSG", "4490"]</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="X_DATASET">' + xfile + r'</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="X_BAND">1</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="PIXEL_OFFSET">0</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="PIXEL_STEP">1</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="Y_DATASET">' + yfile + r'</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="Y_BAND">1</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="LINE_OFFSET">0</MDI>')
    f.write('\n')
    f.write(r'    <MDI key="LINE_STEP">1</MDI>')
    f.write('\n')
    f.write(r'  </Metadata>')
    f.write('\n')
    f.write(r'  <VRTRasterBand dataType = "Float32" band = "%d">'%bandnumber)
    f.write('\n')
    f.write(r'    <ColorInterp>Gray</ColorInterp >')
    f.write('\n')
    f.write(r'    <NoDataValue>%d</NoDataValue >'%noDataValue)
    f.write('\n')
    f.write(r'    <SimpleSource>')
    f.write('\n')
    f.write(r'      <SourceFilename relativeToVRT = "1" >' + datafile + r'</SourceFilename>')
    f.write('\n')
    f.write(r'      <SourceBand>1</SourceBand>')
    f.write('\n')
    f.write(r'    </SimpleSource>')
    f.write('\n')
    f.write(r'  </VRTRasterBand>')
    f.write('\n')
    f.write('</VRTDataset>')
    f.close()
    return 1

