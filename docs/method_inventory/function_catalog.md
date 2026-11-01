# LS4T 函数级源码索引

由 `build_inventory.py` 对当前工作区做 AST 解析生成。
包含函数、类方法和嵌套目标函数；函数数量不等于独立算法数量。排除归档、数据与生成输出。
测试引用只是同名符号的静态文本命中，可能同名误配；不能作为覆盖率或独立精度证明。
JSON 另含调用符号、源码哈希、完整 docstring 和重复函数体分组。

```json
{
  "files": 297,
  "definitions": 1535,
  "by_root": {
    "base": 539,
    "cases": 959,
    "tests": 37
  },
  "by_kind": {
    "method": 74,
    "function": 1355,
    "nested": 106
  },
  "exact_body_duplicate_groups": 170,
  "parse_errors": 0
}
```

## base/__init__.py

源码：[打开文件](C:/work/ls4t/base/__init__.py)；70 行，0 个定义。

## base/aatsr/__init__.py

源码：[打开文件](C:/work/ls4t/base/aatsr/__init__.py)；1 行，0 个定义。

## base/aatsr/aatsr_data.py

源码：[打开文件](C:/work/ls4t/base/aatsr/aatsr_data.py)；308 行，12 个定义。

### `AatsrDataProduct.shape`

```python
AatsrDataProduct.shape(self) -> tuple[int, ...]
```

定义类型：method；[源码第 71 行](C:/work/ls4t/base/aatsr/aatsr_data.py:71)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:207](C:/work/ls4t/tests/test_africa_download.py:207)、[tests/test_dual_thermal_sensors.py:49](C:/work/ls4t/tests/test_dual_thermal_sensors.py:49)、[tests/test_flat_structure.py:202](C:/work/ls4t/tests/test_flat_structure.py:202)、[tests/test_kernel_models.py:88](C:/work/ls4t/tests/test_kernel_models.py:88)、[tests/test_msg_aatsr_comparison.py:39](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:39)、[tests/test_msg_case_dependencies.py:142](C:/work/ls4t/tests/test_msg_case_dependencies.py:142)、[tests/test_msg_evo_sample.py:30](C:/work/ls4t/tests/test_msg_evo_sample.py:30)、[tests/test_multisource_normalization.py:108](C:/work/ls4t/tests/test_multisource_normalization.py:108)、[tests/test_normalization.py:22](C:/work/ls4t/tests/test_normalization.py:22)、[tests/test_normalization_raster.py:17](C:/work/ls4t/tests/test_normalization_raster.py:17)、[tests/test_slstr_case_dependencies.py:152](C:/work/ls4t/tests/test_slstr_case_dependencies.py:152)、[tests/test_slstr_evo_sample.py:31](C:/work/ls4t/tests/test_slstr_evo_sample.py:31)、[tests/test_slstr_products.py:23](C:/work/ls4t/tests/test_slstr_products.py:23)、[tests/test_south_america_components.py:113](C:/work/ls4t/tests/test_south_america_components.py:113)、[tests/test_south_america_native_recovery.py:52](C:/work/ls4t/tests/test_south_america_native_recovery.py:52)、[tests/test_spatial_modes.py:17](C:/work/ls4t/tests/test_spatial_modes.py:17)、[tests/test_tsharp.py:62](C:/work/ls4t/tests/test_tsharp.py:62)

### `AatsrDataProduct.has_lst_auxiliary`

```python
AatsrDataProduct.has_lst_auxiliary(self) -> bool
```

定义类型：method；[源码第 75 行](C:/work/ls4t/base/aatsr/aatsr_data.py:75)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:64](C:/work/ls4t/tests/test_slstr_products.py:64)

### `AatsrDataProduct.validate`

```python
AatsrDataProduct.validate(self, require_lst_auxiliary: bool=False) -> None
```

定义类型：method；[源码第 78 行](C:/work/ls4t/base/aatsr/aatsr_data.py:78)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:49](C:/work/ls4t/tests/test_products.py:49)

### `_atomic_npz`

```python
_atomic_npz(path: Path, payload: dict[str, np.ndarray]) -> None
```

定义类型：function；[源码第 97 行](C:/work/ls4t/base/aatsr/aatsr_data.py:97)。

无 docstring；算法解释见人工审阅章节。

### `_coverage_from_name`

```python
_coverage_from_name(name: str) -> tuple[str | None, str | None]
```

定义类型：function；[源码第 108 行](C:/work/ls4t/base/aatsr/aatsr_data.py:108)。

无 docstring；算法解释见人工审阅章节。

### `unzip_gzip`

```python
unzip_gzip(input_path: str | Path, output_path: str | Path, overwrite: bool=False) -> Path
```

定义类型：function；[源码第 117 行](C:/work/ls4t/base/aatsr/aatsr_data.py:117)。

解压一个 AATSR gzip 文件。

### `read_native_product`

```python
read_native_product(input_path: str | Path, view: str='nadir') -> AatsrDataProduct
```

定义类型：function；[源码第 130 行](C:/work/ls4t/base/aatsr/aatsr_data.py:130)。

使用 ESA EPR 读取一个 AATSR N1 产品。

同名测试引用：[tests/test_dual_thermal_sensors.py:11](C:/work/ls4t/tests/test_dual_thermal_sensors.py:11)

### `add_lst_auxiliary`

```python
add_lst_auxiliary(item: AatsrDataProduct, auxiliary_file: str | Path) -> AatsrDataProduct
```

定义类型：function；[源码第 170 行](C:/work/ls4t/base/aatsr/aatsr_data.py:170)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:11](C:/work/ls4t/tests/test_slstr_products.py:11)

### `write_data_product`

```python
write_data_product(path: str | Path, item: AatsrDataProduct) -> None
```

定义类型：function；[源码第 184 行](C:/work/ls4t/base/aatsr/aatsr_data.py:184)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:12](C:/work/ls4t/tests/test_dual_thermal_sensors.py:12)、[tests/test_slstr_products.py:16](C:/work/ls4t/tests/test_slstr_products.py:16)

### `read_data_product`

```python
read_data_product(path: str | Path) -> AatsrDataProduct
```

定义类型：function；[源码第 208 行](C:/work/ls4t/base/aatsr/aatsr_data.py:208)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:10](C:/work/ls4t/tests/test_dual_thermal_sensors.py:10)、[tests/test_slstr_products.py:12](C:/work/ls4t/tests/test_slstr_products.py:12)

### `aatsr_unzip`

```python
aatsr_unzip(indir_zip=None, outdir_raw=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 231 行](C:/work/ls4t/base/aatsr/aatsr_data.py:231)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:16](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:16)、[tests/test_flat_structure.py:7](C:/work/ls4t/tests/test_flat_structure.py:7)

### `aatsr_extract`

```python
aatsr_extract(indir_raw=None, outdir_extract=None, years=None, months=None, days=None, views=None, overwrite=None) -> None
```

定义类型：function；[源码第 267 行](C:/work/ls4t/base/aatsr/aatsr_data.py:267)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:7](C:/work/ls4t/tests/test_flat_structure.py:7)

## base/aatsr/aatsr_lsct.py

源码：[打开文件](C:/work/ls4t/base/aatsr/aatsr_lsct.py)；153 行，2 个定义。

### `retrieve_aatsr_lsct`

```python
retrieve_aatsr_lsct(input_path, output_path, wavelength_um=None, component_names=None, window_size=None, ridge=None, max_condition_number=None, grid_id=None, algorithm_version=None) -> None
```

定义类型：function；[源码第 36 行](C:/work/ls4t/base/aatsr/aatsr_lsct.py:36)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_lsct`

```python
aatsr_lsct(indir_lsct_input=None, outdir_lsct=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 115 行](C:/work/ls4t/base/aatsr/aatsr_lsct.py:115)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:19](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:19)

## base/aatsr/aatsr_lst.py

源码：[打开文件](C:/work/ls4t/base/aatsr/aatsr_lst.py)；164 行，3 个定义。

### `retrieve_aatsr_lst`

```python
retrieve_aatsr_lst(item: AatsrDataProduct, coefficient_file=None) -> SplitWindowResult
```

定义类型：function；[源码第 37 行](C:/work/ls4t/base/aatsr/aatsr_lst.py:37)。

无 docstring；算法解释见人工审阅章节。

### `produce_aatsr_lst`

```python
produce_aatsr_lst(input_path, output_path, coefficient_file=None, auxiliary_file=None, grid_id=None, algorithm_version=None, uncertainty_k=None) -> None
```

定义类型：function；[源码第 57 行](C:/work/ls4t/base/aatsr/aatsr_lst.py:57)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_lst`

```python
aatsr_lst(indir_data=None, outdir_lst=None, coefficient_file=None, auxiliary_file=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 111 行](C:/work/ls4t/base/aatsr/aatsr_lst.py:111)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:18](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:18)

## base/aatsr/aatsr_project.py

源码：[打开文件](C:/work/ls4t/base/aatsr/aatsr_project.py)；107 行，2 个定义。

### `project_aatsr_product`

```python
project_aatsr_product(item, target_grid_file=None, projection_chunk_size=None, cloud_fraction_threshold=None)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/base/aatsr/aatsr_project.py:22)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_project`

```python
aatsr_project(indir_data=None, outdir_project=None, target_grid_file=None, years=None, months=None, days=None, projection_chunk_size=None, cloud_fraction_threshold=None, overwrite=None) -> None
```

定义类型：function；[源码第 43 行](C:/work/ls4t/base/aatsr/aatsr_project.py:43)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:8](C:/work/ls4t/tests/test_flat_structure.py:8)

## base/aatsr/aatsr_region.py

源码：[打开文件](C:/work/ls4t/base/aatsr/aatsr_region.py)；83 行，3 个定义。

### `_resolve_inputs`

```python
_resolve_inputs(value)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/base/aatsr/aatsr_region.py:30)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_data_region`

```python
aatsr_data_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 42 行](C:/work/ls4t/base/aatsr/aatsr_region.py:42)。

Mode 1: mosaic/crop projected data before retrieval.

同名测试引用：[tests/test_flat_structure.py:9](C:/work/ls4t/tests/test_flat_structure.py:9)

### `aatsr_result_region`

```python
aatsr_result_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 65 行](C:/work/ls4t/base/aatsr/aatsr_region.py:65)。

Mode 2: mosaic/crop LST or LSCT products retrieved scene by scene.

同名测试引用：[tests/test_flat_structure.py:9](C:/work/ls4t/tests/test_flat_structure.py:9)

## base/ahi/__init__.py

源码：[打开文件](C:/work/ls4t/base/ahi/__init__.py)；1 行，0 个定义。

## base/ahi/ahi_data.py

源码：[打开文件](C:/work/ls4t/base/ahi/ahi_data.py)；43 行，4 个定义。

### `read_native_product`

```python
read_native_product(path)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/base/ahi/ahi_data.py:30)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:11](C:/work/ls4t/tests/test_dual_thermal_sensors.py:11)

### `write_data_product`

```python
write_data_product(path, item) -> None
```

定义类型：function；[源码第 34 行](C:/work/ls4t/base/ahi/ahi_data.py:34)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:12](C:/work/ls4t/tests/test_dual_thermal_sensors.py:12)、[tests/test_slstr_products.py:16](C:/work/ls4t/tests/test_slstr_products.py:16)

### `read_data_product`

```python
read_data_product(path)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/base/ahi/ahi_data.py:38)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:10](C:/work/ls4t/tests/test_dual_thermal_sensors.py:10)、[tests/test_slstr_products.py:12](C:/work/ls4t/tests/test_slstr_products.py:12)

### `add_lst_auxiliary`

```python
add_lst_auxiliary(item, auxiliary_file)
```

定义类型：function；[源码第 42 行](C:/work/ls4t/base/ahi/ahi_data.py:42)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:11](C:/work/ls4t/tests/test_slstr_products.py:11)

## base/ahi/ahi_extract.py

源码：[打开文件](C:/work/ls4t/base/ahi/ahi_extract.py)；24 行，1 个定义。

### `ahi_extract`

```python
ahi_extract(indir_raw=None, outdir_data=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/ahi/ahi_extract.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:10](C:/work/ls4t/tests/test_flat_structure.py:10)

## base/ahi/ahi_lst.py

源码：[打开文件](C:/work/ls4t/base/ahi/ahi_lst.py)；44 行，3 个定义。

### `retrieve_ahi_lst`

```python
retrieve_ahi_lst(item, coefficient_file=None)
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/ahi/ahi_lst.py:7)。

无 docstring；算法解释见人工审阅章节。

### `produce_ahi_lst`

```python
produce_ahi_lst(input_path=None, output_path=None, coefficient_file=None, auxiliary_file=None, grid_id=None, algorithm_version=None, uncertainty_k=None) -> None
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/ahi/ahi_lst.py:11)。

无 docstring；算法解释见人工审阅章节。

### `ahi_lst`

```python
ahi_lst(indir_data=None, outdir_lst=None, coefficient_file=None, auxiliary_file=None, years=None, months=None, days=None, grid_id=None, algorithm_version=None, uncertainty_k=None, overwrite=None) -> None
```

定义类型：function；[源码第 26 行](C:/work/ls4t/base/ahi/ahi_lst.py:26)。

无 docstring；算法解释见人工审阅章节。

## base/ahi/ahi_merge.py

源码：[打开文件](C:/work/ls4t/base/ahi/ahi_merge.py)；8 行，1 个定义。

### `ahi_merge`

```python
ahi_merge(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/ahi/ahi_merge.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:11](C:/work/ls4t/tests/test_flat_structure.py:11)

## base/ahi/ahi_project.py

源码：[打开文件](C:/work/ls4t/base/ahi/ahi_project.py)；47 行，2 个定义。

### `project_ahi_product`

```python
project_ahi_product(item, target_grid_file=None, projection_chunk_size=None, cloud_fraction_threshold=None)
```

定义类型：function；[源码第 9 行](C:/work/ls4t/base/ahi/ahi_project.py:9)。

无 docstring；算法解释见人工审阅章节。

### `ahi_project`

```python
ahi_project(indir_extract=None, outdir_project=None, target_grid_file=None, years=None, months=None, days=None, projection_chunk_size=None, cloud_fraction_threshold=None, overwrite=None) -> None
```

定义类型：function；[源码第 24 行](C:/work/ls4t/base/ahi/ahi_project.py:24)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:12](C:/work/ls4t/tests/test_flat_structure.py:12)

## base/ahi/ahi_region.py

源码：[打开文件](C:/work/ls4t/base/ahi/ahi_region.py)；12 行，2 个定义。

### `ahi_data_region`

```python
ahi_data_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/ahi/ahi_region.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:13](C:/work/ls4t/tests/test_flat_structure.py:13)

### `ahi_result_region`

```python
ahi_result_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/ahi/ahi_region.py:11)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:13](C:/work/ls4t/tests/test_flat_structure.py:13)

## base/applications/__init__.py

源码：[打开文件](C:/work/ls4t/base/applications/__init__.py)；5 行，0 个定义。

## base/applications/tvdi.py

源码：[打开文件](C:/work/ls4t/base/applications/tvdi.py)；83 行，2 个定义。

### `tvdi`

```python
tvdi(normalized_temperature_k: np.ndarray, vegetation_index: np.ndarray, dry_edge_coefficients: tuple[float, float], wet_edge_coefficients: tuple[float, float]) -> np.ndarray
```

定义类型：function；[源码第 25 行](C:/work/ls4t/base/applications/tvdi.py:25)。

无 docstring；算法解释见人工审阅章节。

### `tvdi_years`

```python
tvdi_years(indir_l3=None, outdir_l4=None, years=None, dry_edge_coefficients=None, wet_edge_coefficients=None, overwrite=None) -> None
```

定义类型：function；[源码第 43 行](C:/work/ls4t/base/applications/tvdi.py:43)。

按年份手工计算 TVDI，不调用其他 L4 应用。

同名测试引用：[tests/test_flat_structure.py:18](C:/work/ls4t/tests/test_flat_structure.py:18)

## base/aster/__init__.py

源码：[打开文件](C:/work/ls4t/base/aster/__init__.py)；1 行，0 个定义。

## base/aster/aster_data.py

源码：[打开文件](C:/work/ls4t/base/aster/aster_data.py)；43 行，4 个定义。

### `read_native_product`

```python
read_native_product(path)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/base/aster/aster_data.py:30)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:11](C:/work/ls4t/tests/test_dual_thermal_sensors.py:11)

### `write_data_product`

```python
write_data_product(path, item) -> None
```

定义类型：function；[源码第 34 行](C:/work/ls4t/base/aster/aster_data.py:34)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:12](C:/work/ls4t/tests/test_dual_thermal_sensors.py:12)、[tests/test_slstr_products.py:16](C:/work/ls4t/tests/test_slstr_products.py:16)

### `read_data_product`

```python
read_data_product(path)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/base/aster/aster_data.py:38)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:10](C:/work/ls4t/tests/test_dual_thermal_sensors.py:10)、[tests/test_slstr_products.py:12](C:/work/ls4t/tests/test_slstr_products.py:12)

### `add_lst_auxiliary`

```python
add_lst_auxiliary(item, auxiliary_file)
```

定义类型：function；[源码第 42 行](C:/work/ls4t/base/aster/aster_data.py:42)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:11](C:/work/ls4t/tests/test_slstr_products.py:11)

## base/aster/aster_extract.py

源码：[打开文件](C:/work/ls4t/base/aster/aster_extract.py)；24 行，1 个定义。

### `aster_extract`

```python
aster_extract(indir_raw=None, outdir_data=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/aster/aster_extract.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:14](C:/work/ls4t/tests/test_flat_structure.py:14)

## base/aster/aster_lst.py

源码：[打开文件](C:/work/ls4t/base/aster/aster_lst.py)；44 行，3 个定义。

### `retrieve_aster_lst`

```python
retrieve_aster_lst(item, coefficient_file=None)
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/aster/aster_lst.py:7)。

无 docstring；算法解释见人工审阅章节。

### `produce_aster_lst`

```python
produce_aster_lst(input_path=None, output_path=None, coefficient_file=None, auxiliary_file=None, grid_id=None, algorithm_version=None, uncertainty_k=None) -> None
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/aster/aster_lst.py:11)。

无 docstring；算法解释见人工审阅章节。

### `aster_lst`

```python
aster_lst(indir_data=None, outdir_lst=None, coefficient_file=None, auxiliary_file=None, years=None, months=None, days=None, grid_id=None, algorithm_version=None, uncertainty_k=None, overwrite=None) -> None
```

定义类型：function；[源码第 26 行](C:/work/ls4t/base/aster/aster_lst.py:26)。

无 docstring；算法解释见人工审阅章节。

## base/aster/aster_merge.py

源码：[打开文件](C:/work/ls4t/base/aster/aster_merge.py)；8 行，1 个定义。

### `aster_merge`

```python
aster_merge(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/aster/aster_merge.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:15](C:/work/ls4t/tests/test_flat_structure.py:15)

## base/aster/aster_project.py

源码：[打开文件](C:/work/ls4t/base/aster/aster_project.py)；47 行，2 个定义。

### `project_aster_product`

```python
project_aster_product(item, target_grid_file=None, projection_chunk_size=None, cloud_fraction_threshold=None)
```

定义类型：function；[源码第 9 行](C:/work/ls4t/base/aster/aster_project.py:9)。

无 docstring；算法解释见人工审阅章节。

### `aster_project`

```python
aster_project(indir_extract=None, outdir_project=None, target_grid_file=None, years=None, months=None, days=None, projection_chunk_size=None, cloud_fraction_threshold=None, overwrite=None) -> None
```

定义类型：function；[源码第 24 行](C:/work/ls4t/base/aster/aster_project.py:24)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:16](C:/work/ls4t/tests/test_flat_structure.py:16)

## base/aster/aster_region.py

源码：[打开文件](C:/work/ls4t/base/aster/aster_region.py)；12 行，2 个定义。

### `aster_data_region`

```python
aster_data_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/aster/aster_region.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:17](C:/work/ls4t/tests/test_flat_structure.py:17)

### `aster_result_region`

```python
aster_result_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/aster/aster_region.py:11)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:17](C:/work/ls4t/tests/test_flat_structure.py:17)

## base/calibration.py

源码：[打开文件](C:/work/ls4t/base/calibration.py)；82 行，3 个定义。

### `legacy_split_window_model`

```python
legacy_split_window_model(coefficient_table: np.ndarray, view_zenith_nodes_deg: np.ndarray, water_vapour_edges: np.ndarray, *, coefficient_columns: slice=slice(-8, None), valid_temperature_range_k: tuple[float, float]=(220.0, 365.0)) -> SplitWindowModel
```

定义类型：function；[源码第 13 行](C:/work/ls4t/base/calibration.py:13)。

Convert the existing VZA-major AATSR/SLSTR text table into a model.

同名测试引用：[tests/test_calibration.py:5](C:/work/ls4t/tests/test_calibration.py:5)

### `save_split_window_model`

```python
save_split_window_model(path: str | Path, model: SplitWindowModel, *, sensor: str, version: str) -> None
```

定义类型：function；[源码第 39 行](C:/work/ls4t/base/calibration.py:39)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_calibration.py:5](C:/work/ls4t/tests/test_calibration.py:5)、[tests/test_dual_thermal_sensors.py:6](C:/work/ls4t/tests/test_dual_thermal_sensors.py:6)、[tests/test_slstr_products.py:7](C:/work/ls4t/tests/test_slstr_products.py:7)

### `load_split_window_model`

```python
load_split_window_model(path: str | Path) -> SplitWindowModel
```

定义类型：function；[源码第 71 行](C:/work/ls4t/base/calibration.py:71)。

Load versioned production coefficients from a non-pickle NPZ bundle.

同名测试引用：[tests/test_calibration.py:5](C:/work/ls4t/tests/test_calibration.py:5)

## base/composite/__init__.py

源码：[打开文件](C:/work/ls4t/base/composite/__init__.py)；13 行，0 个定义。

## base/composite/monthly_paired.py

源码：[打开文件](C:/work/ls4t/base/composite/monthly_paired.py)；137 行，3 个定义。

### `collect_month`

```python
collect_month(daily_root: Path, tag: str, year: int, month: int, view: str) -> list[dict]
```

定义类型：function；[源码第 41 行](C:/work/ls4t/base/composite/monthly_paired.py:41)。

The LST / LSCT2 file pairs of one month that can be composited.

### `monthly_paired`

```python
monthly_paired(daily_root: Path, tag: str, year: int, month: int, view: str='day') -> tuple[np.ndarray, dict, dict]
```

定义类型：function；[源码第 61 行](C:/work/ls4t/base/composite/monthly_paired.py:61)。

Mean LST / Ts / Tv of the pixels where LST and LSCT2 are both valid.

### `write_monthly_paired`

```python
write_monthly_paired(out_root: Path, year: int, month: int, tag: str, view: str, array: np.ndarray, profile: dict, stats: dict) -> Path
```

定义类型：function；[源码第 119 行](C:/work/ls4t/base/composite/monthly_paired.py:119)。

Write <out_root>/<year>/<YYYYMM>_monthly_paired_<tag>_<view>_0p01.tif.

## base/composite/temporal.py

源码：[打开文件](C:/work/ls4t/base/composite/temporal.py)；112 行，2 个定义。

### `temporal_composite`

```python
temporal_composite(temperature_k: np.ndarray, uncertainty_k: np.ndarray, quality_flag: np.ndarray, *, minimum_observations: int=1) -> CompositeResult
```

定义类型：function；[源码第 34 行](C:/work/ls4t/base/composite/temporal.py:34)。

Create one L3C field from a time-first L3N stack.

### `composite_years`

```python
composite_years(indir_l3n=None, outdir_l3c=None, years=None, minimum_observations=None, overwrite=None) -> None
```

定义类型：function；[源码第 64 行](C:/work/ls4t/base/composite/temporal.py:64)。

Composite NPZ stacks already grouped by year by the operator.

同名测试引用：[tests/test_flat_structure.py:19](C:/work/ls4t/tests/test_flat_structure.py:19)

## base/data.py

源码：[打开文件](C:/work/ls4t/base/data.py)；54 行，2 个定义。

### `write_product`

```python
write_product(path: str | Path, product: TemperatureProduct) -> None
```

定义类型：function；[源码第 16 行](C:/work/ls4t/base/data.py:16)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:6](C:/work/ls4t/tests/test_products.py:6)

### `read_product`

```python
read_product(path: str | Path) -> TemperatureProduct
```

定义类型：function；[源码第 39 行](C:/work/ls4t/base/data.py:39)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:6](C:/work/ls4t/tests/test_products.py:6)

## base/dates.py

源码：[打开文件](C:/work/ls4t/base/dates.py)；81 行，2 个定义。

### `date2DOY`

```python
date2DOY(year, month, day)
```

定义类型：function；[源码第 10 行](C:/work/ls4t/base/dates.py:10)。

日期到Day of Year 的转换 :param year: 年 :param month:  月 :param day: 日 :return: doy

同名测试引用：[tests/test_aatsr_case_dependencies.py:65](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:65)、[tests/test_msg_case_dependencies.py:81](C:/work/ls4t/tests/test_msg_case_dependencies.py:81)、[tests/test_slstr_case_dependencies.py:15](C:/work/ls4t/tests/test_slstr_case_dependencies.py:15)

### `doy2date`

```python
doy2date(year, doy)
```

定义类型：function；[源码第 50 行](C:/work/ls4t/base/dates.py:50)。

doy 到日期的转换 :param year: 年 :param doy: day of year :return:  日期（月,日）

同名测试引用：[tests/test_aatsr_case_dependencies.py:65](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:65)

## base/dual_thermal.py

源码：[打开文件](C:/work/ls4t/base/dual_thermal.py)；616 行，20 个定义。

### `DualThermalSensorSpec.__post_init__`

```python
DualThermalSensorSpec.__post_init__(self) -> None
```

定义类型：method；[源码第 58 行](C:/work/ls4t/base/dual_thermal.py:58)。

无 docstring；算法解释见人工审阅章节。

### `DualThermalDataProduct.shape`

```python
DualThermalDataProduct.shape(self) -> tuple[int, ...]
```

定义类型：method；[源码第 86 行](C:/work/ls4t/base/dual_thermal.py:86)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:207](C:/work/ls4t/tests/test_africa_download.py:207)、[tests/test_dual_thermal_sensors.py:49](C:/work/ls4t/tests/test_dual_thermal_sensors.py:49)、[tests/test_flat_structure.py:202](C:/work/ls4t/tests/test_flat_structure.py:202)、[tests/test_kernel_models.py:88](C:/work/ls4t/tests/test_kernel_models.py:88)、[tests/test_msg_aatsr_comparison.py:39](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:39)、[tests/test_msg_case_dependencies.py:142](C:/work/ls4t/tests/test_msg_case_dependencies.py:142)、[tests/test_msg_evo_sample.py:30](C:/work/ls4t/tests/test_msg_evo_sample.py:30)、[tests/test_multisource_normalization.py:108](C:/work/ls4t/tests/test_multisource_normalization.py:108)、[tests/test_normalization.py:22](C:/work/ls4t/tests/test_normalization.py:22)、[tests/test_normalization_raster.py:17](C:/work/ls4t/tests/test_normalization_raster.py:17)、[tests/test_slstr_case_dependencies.py:152](C:/work/ls4t/tests/test_slstr_case_dependencies.py:152)、[tests/test_slstr_evo_sample.py:31](C:/work/ls4t/tests/test_slstr_evo_sample.py:31)、[tests/test_slstr_products.py:23](C:/work/ls4t/tests/test_slstr_products.py:23)、[tests/test_south_america_components.py:113](C:/work/ls4t/tests/test_south_america_components.py:113)、[tests/test_south_america_native_recovery.py:52](C:/work/ls4t/tests/test_south_america_native_recovery.py:52)、[tests/test_spatial_modes.py:17](C:/work/ls4t/tests/test_spatial_modes.py:17)、[tests/test_tsharp.py:62](C:/work/ls4t/tests/test_tsharp.py:62)

### `DualThermalDataProduct.has_lst_auxiliary`

```python
DualThermalDataProduct.has_lst_auxiliary(self) -> bool
```

定义类型：method；[源码第 90 行](C:/work/ls4t/base/dual_thermal.py:90)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:64](C:/work/ls4t/tests/test_slstr_products.py:64)

### `DualThermalDataProduct.validate`

```python
DualThermalDataProduct.validate(self, require_lst_auxiliary: bool=False) -> None
```

定义类型：method；[源码第 93 行](C:/work/ls4t/base/dual_thermal.py:93)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:49](C:/work/ls4t/tests/test_products.py:49)

### `_metadata`

```python
_metadata(payload: dict[str, np.ndarray], path: Path) -> dict
```

定义类型：function；[源码第 126 行](C:/work/ls4t/base/dual_thermal.py:126)。

无 docstring；算法解释见人工审阅章节。

### `_first`

```python
_first(payload: dict[str, np.ndarray], names: Iterable[str], path: Path) -> np.ndarray
```

定义类型：function；[源码第 137 行](C:/work/ls4t/base/dual_thermal.py:137)。

无 docstring；算法解释见人工审阅章节。

### `read_prepared_product`

```python
read_prepared_product(path: str | Path, spec: DualThermalSensorSpec, product_type: type[ProductType]) -> ProductType
```

定义类型：function；[源码第 144 行](C:/work/ls4t/base/dual_thermal.py:144)。

Convert reviewed native arrays into a sensor LS4T-DATA object.  GeoTIFF is the new prepared-input format; NPZ remains readable for legacy prepared arrays. Brightness temperatures must already be decoded to kelvin.

### `write_data_product`

```python
write_data_product(path: str | Path, item: DualThermalDataProduct, spec: DualThermalSensorSpec) -> None
```

定义类型：function；[源码第 196 行](C:/work/ls4t/base/dual_thermal.py:196)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:12](C:/work/ls4t/tests/test_dual_thermal_sensors.py:12)、[tests/test_slstr_products.py:16](C:/work/ls4t/tests/test_slstr_products.py:16)

### `read_data_product`

```python
read_data_product(path: str | Path, spec: DualThermalSensorSpec, product_type: type[ProductType]) -> ProductType
```

定义类型：function；[源码第 256 行](C:/work/ls4t/base/dual_thermal.py:256)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:10](C:/work/ls4t/tests/test_dual_thermal_sensors.py:10)、[tests/test_slstr_products.py:12](C:/work/ls4t/tests/test_slstr_products.py:12)

### `add_lst_auxiliary`

```python
add_lst_auxiliary(item: ProductType, auxiliary_file: str | Path) -> ProductType
```

定义类型：function；[源码第 293 行](C:/work/ls4t/base/dual_thermal.py:293)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:11](C:/work/ls4t/tests/test_slstr_products.py:11)

### `_day`

```python
_day(root, year, month, day) -> Path
```

定义类型：function；[源码第 315 行](C:/work/ls4t/base/dual_thermal.py:315)。

无 docstring；算法解释见人工审阅章节。

### `extract_sensor_products`

```python
extract_sensor_products(spec: DualThermalSensorSpec, product_type: type[ProductType], *, indir_raw=None, outdir_data=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 319 行](C:/work/ls4t/base/dual_thermal.py:319)。

Batch-convert prepared native arrays; raw mission readers remain case-owned.

### `project_sensor_products`

```python
project_sensor_products(spec: DualThermalSensorSpec, product_type: type[ProductType], *, indir_data=None, outdir_project=None, target_grid_file=None, years=None, months=None, days=None, projection_chunk_size=None, cloud_fraction_threshold=None, overwrite=None) -> None
```

定义类型：function；[源码第 360 行](C:/work/ls4t/base/dual_thermal.py:360)。

无 docstring；算法解释见人工审阅章节。

### `resolve_paths`

```python
resolve_paths(value, sensor: str) -> list[Path]
```

定义类型：function；[源码第 414 行](C:/work/ls4t/base/dual_thermal.py:414)。

无 docstring；算法解释见人工审阅章节。

### `combine_data_products`

```python
combine_data_products(input_paths, spec: DualThermalSensorSpec, product_type: type[ProductType], bounds=None) -> ProductType
```

定义类型：function；[源码第 428 行](C:/work/ls4t/base/dual_thermal.py:428)。

无 docstring；算法解释见人工审阅章节。

### `merge_sensor_data`

```python
merge_sensor_data(input_paths, output_path, spec: DualThermalSensorSpec, product_type: type[ProductType], bounds=None) -> None
```

定义类型：function；[源码第 444 行](C:/work/ls4t/base/dual_thermal.py:444)。

无 docstring；算法解释见人工审阅章节。

### `merge_sensor_results`

```python
merge_sensor_results(input_paths, output_path, spec: DualThermalSensorSpec, bounds=None) -> None
```

定义类型：function；[源码第 459 行](C:/work/ls4t/base/dual_thermal.py:459)。

无 docstring；算法解释见人工审阅章节。

### `retrieve_sensor_lst`

```python
retrieve_sensor_lst(item: DualThermalDataProduct, spec: DualThermalSensorSpec, coefficient_file) -> SplitWindowResult
```

定义类型：function；[源码第 476 行](C:/work/ls4t/base/dual_thermal.py:476)。

无 docstring；算法解释见人工审阅章节。

### `produce_sensor_lst`

```python
produce_sensor_lst(input_path, output_path, spec: DualThermalSensorSpec, product_type: type[ProductType], coefficient_file, auxiliary_file, grid_id=None, algorithm_version=None, uncertainty_k=None) -> None
```

定义类型：function；[源码第 502 行](C:/work/ls4t/base/dual_thermal.py:502)。

无 docstring；算法解释见人工审阅章节。

### `retrieve_sensor_years`

```python
retrieve_sensor_years(spec: DualThermalSensorSpec, product_type: type[ProductType], *, indir_data=None, outdir_lst=None, coefficient_file=None, auxiliary_file=None, years=None, months=None, days=None, grid_id=None, algorithm_version=None, uncertainty_k=None, overwrite=None) -> None
```

定义类型：function；[源码第 559 行](C:/work/ls4t/base/dual_thermal.py:559)。

无 docstring；算法解释见人工审阅章节。

## base/files.py

源码：[打开文件](C:/work/ls4t/base/files.py)；490 行，20 个定义。

### `read_npz_payload`

```python
read_npz_payload(path: str | Path) -> dict[str, np.ndarray]
```

定义类型：function；[源码第 12 行](C:/work/ls4t/base/files.py:12)。

无 docstring；算法解释见人工审阅章节。

### `write_npz_atomic`

```python
write_npz_atomic(path: str | Path, payload: dict[str, np.ndarray]) -> None
```

定义类型：function；[源码第 17 行](C:/work/ls4t/base/files.py:17)。

无 docstring；算法解释见人工审阅章节。

### `search_dir`

```python
search_dir(dir, specstr)
```

定义类型：function；[源码第 48 行](C:/work/ls4t/base/files.py:48)。

查找某个路径下，含有特定标识的文件夹，需要list把标识括起来，即使只有1个 :param dir: 路径 :param specstr: :return:

### `search_file_rej`

```python
search_file_rej(dir, specstr, rejstr)
```

定义类型：function；[源码第 82 行](C:/work/ls4t/base/files.py:82)。

查找某个路径下，含有特定标识,又不含有某个标识的文件，需要list把标识括起来，即使只有1个，可以有多个“有”标识，但是只有1个“没有”标识 :param dir: 路径 :param specstr: “有”标识 :param rejstr: “没有”标识 :return: 文件名数组

### `search_dir_rej`

```python
search_dir_rej(dir, specstr, rejstr)
```

定义类型：function；[源码第 121 行](C:/work/ls4t/base/files.py:121)。

查找某个路径下，含有特定标识,又不含有某个标识的文件夹，需要list把标识括起来，即使只有1个，可以有多个“有”标识，但是只有1个“没有”标识 :param dir: 路径 :param specstr: “有”标识 :param rejstr: “没有”标识 :return: 文件夹名数组

### `read_txt_array`

```python
read_txt_array(filename, num_pass, num_col)
```

定义类型：function；[源码第 160 行](C:/work/ls4t/base/files.py:160)。

限定读取txt文本数据，考虑了要跳过的行，但是必须要给定列数 :param filename: 文件名 :param num_pass: 要跳过的行数 :param num_col: 数据的列数 :return: 返回数组

同名测试引用：[tests/test_msg_case_dependencies.py:86](C:/work/ls4t/tests/test_msg_case_dependencies.py:86)

### `read_image_gdal`

```python
read_image_gdal(filename)
```

定义类型：function；[源码第 181 行](C:/work/ls4t/base/files.py:181)。

使用gdal,读取图像文件，并格式输出 :param filename:文件名 :return: 文件，列数，行数，波段数，地理信息，投影信息

同名测试引用：[tests/test_msg_case_dependencies.py:84](C:/work/ls4t/tests/test_msg_case_dependencies.py:84)

### `read_image_dataset_gdal`

```python
read_image_dataset_gdal(filename)
```

定义类型：function；[源码第 200 行](C:/work/ls4t/base/files.py:200)。

读取图像文件，特别的，会返回数据集 :param filename: 文件名 :return: 文件，列数，行数，波段数，地理信息，投影信息，数据集

同名测试引用：[tests/test_msg_case_dependencies.py:85](C:/work/ls4t/tests/test_msg_case_dependencies.py:85)

### `getDatafromNc`

```python
getDatafromNc(fileName, objectName)
```

定义类型：function；[源码第 219 行](C:/work/ls4t/base/files.py:219)。

读取NC文件，文件名和项目名 :param fileName: 文件名 :param objectName: 项目名 :return: 值

### `write_image_gdal`

```python
write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff')
```

定义类型：function；[源码第 242 行](C:/work/ls4t/base/files.py:242)。

保存数据，输出成tif格式 :param im_data: 数组 :param im_width:  列数 :param im_height:  行数 :param im_bands:  波段数 :param im_trans:  地理坐标 :param im_proj:  投影坐标 :param path:  路径 :return: 无

### `read_h5py_item`

```python
read_h5py_item(infile, name)
```

定义类型：function；[源码第 278 行](C:/work/ls4t/base/files.py:278)。

para infile: h5py para name: string

### `mkdir_if_not_exist`

```python
mkdir_if_not_exist(dir_name, is_delete=False)
```

定义类型：function；[源码第 288 行](C:/work/ls4t/base/files.py:288)。

创建文件夹 :param dir_name: 文件夹 :param is_delete: 是否删除 :return: 是否成功

同名测试引用：[tests/test_msg_case_dependencies.py:83](C:/work/ls4t/tests/test_msg_case_dependencies.py:83)

### `unzip_file`

```python
unzip_file(zipfilename, outdir)
```

定义类型：function；[源码第 309 行](C:/work/ls4t/base/files.py:309)。

解压zip文件 :param zipfilename: 要解压文件名称 :param outdir: 输出位置

### `search_file`

```python
search_file(dir, specstr)
```

定义类型：function；[源码第 324 行](C:/work/ls4t/base/files.py:324)。

查找某个路径下，含有特定标识的文件，需要list把标识括起来，即使只有1个 :param dir: 路径 :param specstr: 特定的标识 :return: 文件名

同名测试引用：[tests/test_msg_case_dependencies.py:87](C:/work/ls4t/tests/test_msg_case_dependencies.py:87)

### `read_txt_str`

```python
read_txt_str(filename, spt)
```

定义类型：function；[源码第 360 行](C:/work/ls4t/base/files.py:360)。

读取文件数据，然后按照特定的约束进行解析，随后按照行列进行存储 :param filename: 文件名称 :param spt: 解析表示 :return: 解析后数组

### `read_image_Nc`

```python
read_image_Nc(fileName, objectName, ifscale)
```

定义类型：function；[源码第 390 行](C:/work/ls4t/base/files.py:390)。

读取NC格式的数据，没有组名，也需要指定是否需要缩放 :param fileName:  文件名 :param objectName:  目标名 :param ifscale:  是否缩放 :return:  数组

同名测试引用：[tests/test_aatsr_case_dependencies.py:66](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:66)

### `write_h5py_item`

```python
write_h5py_item(infile, name, data, dtype, if_overwrite=1, compression=None)
```

定义类型：function；[源码第 405 行](C:/work/ls4t/base/files.py:405)。

Write h5py para infile: h5py para name: string para data: numpy array para dtype: string para if_overwrite: 0 or 1 para compression: string

同名测试引用：[tests/test_aatsr_case_dependencies.py:66](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:66)

### `write_h5py_file`

```python
write_h5py_file(infile, name_list, data_list, dtype_list, compression=None, ifcover=0)
```

定义类型：function；[源码第 425 行](C:/work/ls4t/base/files.py:425)。

Write h5py para infile: h5py para name_list: para data_list: para dtype_list: para compression: gzip, lzf, szip, None (only applied to array data)

### `read_h5py_items`

```python
read_h5py_items(infile, names)
```

定义类型：function；[源码第 453 行](C:/work/ls4t/base/files.py:453)。

para infile: h5py para name: string

同名测试引用：[tests/test_aatsr_case_dependencies.py:66](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:66)

### `un_gz`

```python
un_gz(file_name, infile, outdir)
```

定义类型：function；[源码第 475 行](C:/work/ls4t/base/files.py:475)。

解压gz文件 :param file_name:要解压文件名称 :param infile:要解压文件位置 :param outdir:输出位置

同名测试引用：[tests/test_aatsr_case_dependencies.py:66](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:66)

## base/fitting.py

源码：[打开文件](C:/work/ls4t/base/fitting.py)；47 行，2 个定义。

### `fitting_unknown_linear_ls`

```python
fitting_unknown_linear_ls(y, A)
```

定义类型：function；[源码第 12 行](C:/work/ls4t/base/fitting.py:12)。

线性反演未知数，y=ax1+bx2+cx3, x3=1 :param y: 因变量 :param x: 自变量 :return:

同名测试引用：[tests/test_aatsr_case_dependencies.py:67](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:67)

### `fitting_unknown_linear_sklearn`

```python
fitting_unknown_linear_sklearn(y, A, method='ridge')
```

定义类型：function；[源码第 23 行](C:/work/ls4t/base/fitting.py:23)。

线性反演未知数， :param y: 因变量 :param x: 自变量 :param method: 方法，推荐ridge，然后是lasso，因为lasso会倾向于拟合0 :return: 回归系数

## base/kernel.py

源码：[打开文件](C:/work/ls4t/base/kernel.py)；1137 行，82 个定义。

### `kernel_Vin`

```python
kernel_Vin(vza)
```

定义类型：function；[源码第 12 行](C:/work/ls4t/base/kernel.py:12)。

Vinnikov emissivity :param vza: :return: Vin 核值

同名测试引用：[tests/test_kernel_models.py:15](C:/work/ls4t/tests/test_kernel_models.py:15)

### `kernel_LiDense`

```python
kernel_LiDense(vza, sza, raa, h=2, r=1, b=1)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/base/kernel.py:22)。

:param vza: :param sza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:19](C:/work/ls4t/tests/test_kernel_models.py:19)

### `kernel_LiSparse`

```python
kernel_LiSparse(vza, sza, raa, h=2, r=1, b=1)
```

定义类型：function；[源码第 63 行](C:/work/ls4t/base/kernel.py:63)。

:param vza: :param sza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:19](C:/work/ls4t/tests/test_kernel_models.py:19)

### `kernel_Solar`

```python
kernel_Solar(vza, sza, raa)
```

定义类型：function；[源码第 105 行](C:/work/ls4t/base/kernel.py:105)。

vinnikov solar :param vza: :param sza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:20](C:/work/ls4t/tests/test_kernel_models.py:20)

### `kernel_RLf`

```python
kernel_RLf(vza, sza, raa)
```

定义类型：function；[源码第 129 行](C:/work/ls4t/base/kernel.py:129)。

Roujean hotspot angular distance function :param vza: :param sza: :param raa: :return:

同名测试引用：[tests/test_aatsr_case_dependencies.py:98](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:98)、[tests/test_kernel_models.py:20](C:/work/ls4t/tests/test_kernel_models.py:20)

### `kernel_LSF_analytical`

```python
kernel_LSF_analytical(vza)
```

定义类型：function；[源码第 144 行](C:/work/ls4t/base/kernel.py:144)。

一种LSF核的参数化方案 :param vza: 观测天顶角 :return: LSF核值

同名测试引用：[tests/test_kernel_models.py:16](C:/work/ls4t/tests/test_kernel_models.py:16)

### `kernel_LSF`

```python
kernel_LSF(vza)
```

定义类型：function；[源码第 156 行](C:/work/ls4t/base/kernel.py:156)。

LSF核的原始计算方法 :param vza: 观测天顶角 :return: LSF核

同名测试引用：[tests/test_aatsr_case_dependencies.py:68](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:68)、[tests/test_kernel_models.py:15](C:/work/ls4t/tests/test_kernel_models.py:15)

### `kernel_TLSF`

```python
kernel_TLSF(vza, w=0.1)
```

定义类型：function；[源码第 169 行](C:/work/ls4t/base/kernel.py:169)。

LSF核的原始计算方法 :param vza: 观测天顶角 :return: LSF核

同名测试引用：[tests/test_kernel_models.py:17](C:/work/ls4t/tests/test_kernel_models.py:17)

### `kernel_VLSF`

```python
kernel_VLSF(vza, w=0.15)
```

定义类型：function；[源码第 182 行](C:/work/ls4t/base/kernel.py:182)。

LSF核的原始计算方法 :param vza: 观测天顶角 :return: LSF核

同名测试引用：[tests/test_kernel_models.py:17](C:/work/ls4t/tests/test_kernel_models.py:17)

### `kernel_Thapke`

```python
kernel_Thapke(vza, w=0.1, K=1.0)
```

定义类型：function；[源码第 195 行](C:/work/ls4t/base/kernel.py:195)。

LSF核的原始计算方法 :param vza: 观测天顶角 :return: LSF核

同名测试引用：[tests/test_kernel_models.py:18](C:/work/ls4t/tests/test_kernel_models.py:18)

### `kernel_RossThick`

```python
kernel_RossThick(vza, sza, raa)
```

定义类型：function；[源码第 209 行](C:/work/ls4t/base/kernel.py:209)。

Ross 简化模型，用于多次散射项计算 :param sza: :param vza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:21](C:/work/ls4t/tests/test_kernel_models.py:21)

### `kernel_RossThin`

```python
kernel_RossThin(vza, sza, raa)
```

定义类型：function；[源码第 233 行](C:/work/ls4t/base/kernel.py:233)。

Ross 简化模型，用于多次散射项计算 :param sza: :param vza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:21](C:/work/ls4t/tests/test_kernel_models.py:21)

### `kernel_LSFLiDense`

```python
kernel_LSFLiDense(vza, sza, raa)
```

定义类型：function；[源码第 257 行](C:/work/ls4t/base/kernel.py:257)。

LSF组分温度差 和 Li 热点核 :param vza: :param sza: :param raa: :return:

### `kernel_LSFLiDenseRossThick`

```python
kernel_LSFLiDenseRossThick(vza, sza, raa)
```

定义类型：function；[源码第 272 行](C:/work/ls4t/base/kernel.py:272)。

LSF组分温度差 和 Li 热点核 :param vza: :param sza: :param raa: :return:

### `kernel_LSFLiSparse`

```python
kernel_LSFLiSparse(vza, sza, raa)
```

定义类型：function；[源码第 288 行](C:/work/ls4t/base/kernel.py:288)。

LSF 组分差异核 LiSparse 热点核 :param vza: :param sza: :param raa: :return:

### `kernel_RossThickLiSparse`

```python
kernel_RossThickLiSparse(vza, sza, raa)
```

定义类型：function；[源码第 303 行](C:/work/ls4t/base/kernel.py:303)。

体散射核核几何光学核，分别为Ross和Li :param vza: :param sza: :param raa: :return: 体散射核核几何光学核

### `kernel_RossThickLiDense`

```python
kernel_RossThickLiDense(vza, sza, raa)
```

定义类型：function；[源码第 319 行](C:/work/ls4t/base/kernel.py:319)。

体散射核核几何光学核，分别为Ross和Li :param vza: :param sza: :param raa: :return: 体散射核核几何光学核

### `kernel_VinLiDense`

```python
kernel_VinLiDense(vza, sza, raa)
```

定义类型：function；[源码第 335 行](C:/work/ls4t/base/kernel.py:335)。

体散射核核几何光学核，分别为Ross和Li :param vza: :param sza: :param raa: :return: 体散射核核几何光学核

### `kernel_VinLiSparse`

```python
kernel_VinLiSparse(vza, sza, raa)
```

定义类型：function；[源码第 351 行](C:/work/ls4t/base/kernel.py:351)。

体散射核核几何光学核，分别为Ross和Li :param vza: :param sza: :param raa: :return: 体散射核核几何光学核

### `kernel_LSFRL`

```python
kernel_LSFRL(vza, sza, raa)
```

定义类型：function；[源码第 367 行](C:/work/ls4t/base/kernel.py:367)。

LSF and roujean-lagourade :param vza: :param sza: :param raa: :return:

### `kernel_VinSolar`

```python
kernel_VinSolar(vza, sza, raa)
```

定义类型：function；[源码第 382 行](C:/work/ls4t/base/kernel.py:382)。

Vinnikov original kernel combination :param vza: :param sza: :param raa: :return:

### `cost_kernel_VolR`

```python
cost_kernel_VolR(x, y, kvol, fhs)
```

定义类型：function；[源码第 397 行](C:/work/ls4t/base/kernel.py:397)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRB`

```python
cost_kernel_VolRB(x, y, kvol, fhs, fn)
```

定义类型：function；[源码第 409 行](C:/work/ls4t/base/kernel.py:409)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRL`

```python
cost_kernel_VolRL(x, y, kvol, fhs, fn)
```

定义类型：function；[源码第 421 行](C:/work/ls4t/base/kernel.py:421)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_RL`

```python
cost_kernel_RL(x, y, fhs, fn)
```

定义类型：function；[源码第 433 行](C:/work/ls4t/base/kernel.py:433)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_RL_dif`

```python
cost_kernel_RL_dif(x, y, fhs, fn)
```

定义类型：function；[源码第 444 行](C:/work/ls4t/base/kernel.py:444)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRL_ab`

```python
cost_kernel_VolRL_ab(x, k, y, kvol, fhs, fn)
```

定义类型：function；[源码第 454 行](C:/work/ls4t/base/kernel.py:454)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolR_ab`

```python
cost_kernel_VolR_ab(x, k, y, kvol, fhs, fn)
```

定义类型：function；[源码第 465 行](C:/work/ls4t/base/kernel.py:465)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolR_ab_k`

```python
cost_kernel_VolR_ab_k(x, a, b, c, y, kvol, fhs, fn)
```

定义类型：function；[源码第 476 行](C:/work/ls4t/base/kernel.py:476)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRL_ab_k`

```python
cost_kernel_VolRL_ab_k(x, a, b, c, y, kvol, fhs, fn)
```

定义类型：function；[源码第 486 行](C:/work/ls4t/base/kernel.py:486)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRLEB`

```python
cost_kernel_VolRLEB(x, y, kvol, fhs, fn, ref, refplus)
```

定义类型：function；[源码第 496 行](C:/work/ls4t/base/kernel.py:496)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRLEB_dif`

```python
cost_kernel_VolRLEB_dif(x, y, kvol, fhs, fn, ref, refplus)
```

定义类型：function；[源码第 508 行](C:/work/ls4t/base/kernel.py:508)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_RLEB_dif`

```python
cost_kernel_RLEB_dif(x, y, fhs, fn, ref, refplus)
```

定义类型：function；[源码第 519 行](C:/work/ls4t/base/kernel.py:519)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRLEB_dif_ab`

```python
cost_kernel_VolRLEB_dif_ab(x, k, y, kvol, fhs, fn, ref, refplus)
```

定义类型：function；[源码第 529 行](C:/work/ls4t/base/kernel.py:529)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRLEB_dif_ab_k`

```python
cost_kernel_VolRLEB_dif_ab_k(x, a, b, y, kvol, fhs, fn, ref, refplus)
```

定义类型：function；[源码第 539 行](C:/work/ls4t/base/kernel.py:539)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolREB_dif`

```python
cost_kernel_VolREB_dif(x, y, kvol, fhs, fn, ref, refplus)
```

定义类型：function；[源码第 548 行](C:/work/ls4t/base/kernel.py:548)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolR_dif`

```python
cost_kernel_VolR_dif(x, y, kvol, fhs, fn)
```

定义类型：function；[源码第 559 行](C:/work/ls4t/base/kernel.py:559)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolREBB_dif`

```python
cost_kernel_VolREBB_dif(x, y, kvol, fhs, fn, ref, refplus)
```

定义类型：function；[源码第 570 行](C:/work/ls4t/base/kernel.py:570)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolREB_dif_ab`

```python
cost_kernel_VolREB_dif_ab(x, k, y, kvol, fhs, fn, ref, refplus)
```

定义类型：function；[源码第 581 行](C:/work/ls4t/base/kernel.py:581)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolREB_dif_ab_k`

```python
cost_kernel_VolREB_dif_ab_k(x, a, b, y, kvol, fhs, fn, ref, refplus)
```

定义类型：function；[源码第 591 行](C:/work/ls4t/base/kernel.py:591)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRLE_dif`

```python
cost_kernel_VolRLE_dif(x, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 600 行](C:/work/ls4t/base/kernel.py:600)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolVRLE_dif`

```python
cost_kernel_VolVRLE_dif(x, lst1, lst2, phi1, phi2, f1, f2, fn, ref, rad)
```

定义类型：function；[源码第 611 行](C:/work/ls4t/base/kernel.py:611)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRLELSF_dif`

```python
cost_kernel_VolRLELSF_dif(x, lst1, lst2, phi1, phi2, f1, f2, fn, lsf1, lsf2, ref, rad)
```

定义类型：function；[源码第 622 行](C:/work/ls4t/base/kernel.py:622)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRE_dif`

```python
cost_kernel_VolRE_dif(x, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 634 行](C:/work/ls4t/base/kernel.py:634)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRE_dif_ab`

```python
cost_kernel_VolRE_dif_ab(x, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 645 行](C:/work/ls4t/base/kernel.py:645)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRE_dif_ab_k`

```python
cost_kernel_VolRE_dif_ab_k(x, k, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 656 行](C:/work/ls4t/base/kernel.py:656)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRLE_dif_ab`

```python
cost_kernel_VolRLE_dif_ab(x, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 666 行](C:/work/ls4t/base/kernel.py:666)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRLE_dif_ab_k`

```python
cost_kernel_VolRLE_dif_ab_k(x, k, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 677 行](C:/work/ls4t/base/kernel.py:677)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRE_dif_k`

```python
cost_kernel_VolRE_dif_k(x, a, b, lst1, lst2, phi1, phi2, f1, f2, rad)
```

定义类型：function；[源码第 688 行](C:/work/ls4t/base/kernel.py:688)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_RossR_dif_k`

```python
cost_kernel_RossR_dif_k(x, a, b, lst1, lst2, kvol1, kvol2, f1, f2, da, rad)
```

定义类型：function；[源码第 697 行](C:/work/ls4t/base/kernel.py:697)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_RossRL_dif_k`

```python
cost_kernel_RossRL_dif_k(x, a, b, lst1, lst2, kvol1, kvol2, f1, f2, fn, da, rad)
```

定义类型：function；[源码第 706 行](C:/work/ls4t/base/kernel.py:706)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolRLE_dif_k`

```python
cost_kernel_VolRLE_dif_k(x, a, b, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 715 行](C:/work/ls4t/base/kernel.py:715)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VolVRE_dif`

```python
cost_kernel_VolVRE_dif(x, lst1, lst2, phi1, phi2, f1, f2, ref, rad)
```

定义类型：function；[源码第 724 行](C:/work/ls4t/base/kernel.py:724)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_Vin`

```python
cost_kernel_Vin(x, lst1, lst2, phi1, phi2)
```

定义类型：function；[源码第 735 行](C:/work/ls4t/base/kernel.py:735)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_VinV`

```python
cost_kernel_VinV(x, lst1, lst2, phi1, phi2, ref)
```

定义类型：function；[源码第 743 行](C:/work/ls4t/base/kernel.py:743)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_RLE_dif`

```python
cost_kernel_RLE_dif(x, a, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 751 行](C:/work/ls4t/base/kernel.py:751)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_RLEB2_dif`

```python
cost_kernel_RLEB2_dif(x, a, b, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 761 行](C:/work/ls4t/base/kernel.py:761)。

无 docstring；算法解释见人工审阅章节。

### `cost_kernel_RE_dif`

```python
cost_kernel_RE_dif(x, a, lst1, lst2, phi1, phi2, f1, f2, fn, rad)
```

定义类型：function；[源码第 771 行](C:/work/ls4t/base/kernel.py:771)。

无 docstring；算法解释见人工审阅章节。

### `cost_DTC`

```python
cost_DTC(x, mea, t)
```

定义类型：function；[源码第 781 行](C:/work/ls4t/base/kernel.py:781)。

DTC 函数 :param x:未知数 :param mea: 温度 :param t: 时间 :return: 误差

### `cost_KDTC_RVT`

```python
cost_KDTC_RVT(x, mea, pst, vi, bf, tsr, tm, k=1.0)
```

定义类型：function；[源码第 799 行](C:/work/ls4t/base/kernel.py:799)。

无 docstring；算法解释见人工审阅章节。

### `cost_KDTC_DVT`

```python
cost_KDTC_DVT(x, mea, pst, vi, bf)
```

定义类型：function；[源码第 816 行](C:/work/ls4t/base/kernel.py:816)。

无 docstring；算法解释见人工审阅章节。

### `cost_RPV`

```python
cost_RPV(x, obs, sza, vza, raa)
```

定义类型：function；[源码第 838 行](C:/work/ls4t/base/kernel.py:838)。

无 docstring；算法解释见人工审阅章节。

### `fitting_kernel_R_min`

```python
fitting_kernel_R_min(fun, y, kvol, fhs, x0, bnds, method='Powell')
```

定义类型：function；[源码第 872 行](C:/work/ls4t/base/kernel.py:872)。

非线性反演/回归，基于minimize函数，能给初值，也能给边界条件 :param fun: 函数 :param y: 因变量 :param x: 自变量，是个多列数组 :param x0: 初值 :param xn: 列数 :param bnds: 边界 :param method: 方法，默认为powell，还有slsqp，L-BFGS-B，TNC， :return: 回归系数

### `fitting_kernel_RL_min`

```python
fitting_kernel_RL_min(fun, y, kvol, fhs, fn, x0, bnds, method='Powell')
```

定义类型：function；[源码第 891 行](C:/work/ls4t/base/kernel.py:891)。

非线性反演/回归，基于minimize函数，能给初值，也能给边界条件 :param fun: 函数 :param y: 因变量 :param x: 自变量，是个多列数组 :param x0: 初值 :param xn: 列数 :param bnds: 边界 :param method: 方法，默认为powell，还有slsqp，L-BFGS-B，TNC， :return: 回归系数

### `model_Vin`

```python
model_Vin(x, vza, coeffa)
```

定义类型：function；[源码第 910 行](C:/work/ls4t/base/kernel.py:910)。

无 docstring；算法解释见人工审阅章节。

### `model_VinLiDense`

```python
model_VinLiDense(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 918 行](C:/work/ls4t/base/kernel.py:918)。

无 docstring；算法解释见人工审阅章节。

### `model_VinSolar`

```python
model_VinSolar(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 927 行](C:/work/ls4t/base/kernel.py:927)。

无 docstring；算法解释见人工审阅章节。

### `model_VinLiSparse`

```python
model_VinLiSparse(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 936 行](C:/work/ls4t/base/kernel.py:936)。

无 docstring；算法解释见人工审阅章节。

### `model_LSFLiDense`

```python
model_LSFLiDense(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 945 行](C:/work/ls4t/base/kernel.py:945)。

无 docstring；算法解释见人工审阅章节。

### `model_LSFLiDenseRossThick`

```python
model_LSFLiDenseRossThick(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 954 行](C:/work/ls4t/base/kernel.py:954)。

无 docstring；算法解释见人工审阅章节。

### `model_LSFLiSparse`

```python
model_LSFLiSparse(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 964 行](C:/work/ls4t/base/kernel.py:964)。

无 docstring；算法解释见人工审阅章节。

### `model_LSFR`

```python
model_LSFR(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 973 行](C:/work/ls4t/base/kernel.py:973)。

无 docstring；算法解释见人工审阅章节。

### `model_RossThickR`

```python
model_RossThickR(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 987 行](C:/work/ls4t/base/kernel.py:987)。

无 docstring；算法解释见人工审阅章节。

### `model_RossThickLiSparse`

```python
model_RossThickLiSparse(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 1001 行](C:/work/ls4t/base/kernel.py:1001)。

无 docstring；算法解释见人工审阅章节。

### `model_RossThickLiDense`

```python
model_RossThickLiDense(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 1010 行](C:/work/ls4t/base/kernel.py:1010)。

无 docstring；算法解释见人工审阅章节。

### `model_VinR`

```python
model_VinR(coeffs, vza, sza, raa)
```

定义类型：function；[源码第 1019 行](C:/work/ls4t/base/kernel.py:1019)。

无 docstring；算法解释见人工审阅章节。

### `model_RPV`

```python
model_RPV(coeffs, sza, vza, raa)
```

定义类型：function；[源码第 1033 行](C:/work/ls4t/base/kernel.py:1033)。

无 docstring；算法解释见人工审阅章节。

### `cost_DTCRL`

```python
cost_DTCRL(x, y, t, fhs, fn)
```

定义类型：function；[源码第 1062 行](C:/work/ls4t/base/kernel.py:1062)。

无 docstring；算法解释见人工审阅章节。

### `model_DTCRL`

```python
model_DTCRL(x, t, fhs, fn)
```

定义类型：function；[源码第 1079 行](C:/work/ls4t/base/kernel.py:1079)。

无 docstring；算法解释见人工审阅章节。

### `model_DTC`

```python
model_DTC(x, t)
```

定义类型：function；[源码第 1095 行](C:/work/ls4t/base/kernel.py:1095)。

无 docstring；算法解释见人工审阅章节。

### `cost_DTCLSFRL`

```python
cost_DTCLSFRL(x, y, t, kLSF, fhs, fn)
```

定义类型：function；[源码第 1107 行](C:/work/ls4t/base/kernel.py:1107)。

无 docstring；算法解释见人工审阅章节。

### `model_DTCLSFRL`

```python
model_DTCLSFRL(x, t, kLSF, fhs, fn)
```

定义类型：function；[源码第 1123 行](C:/work/ls4t/base/kernel.py:1123)。

无 docstring；算法解释见人工审阅章节。

## base/lsct.py

源码：[打开文件](C:/work/ls4t/base/lsct.py)；615 行，16 个定义。

### `retrieve_components`

```python
retrieve_components(observed_radiance: np.ndarray, effective_weights: np.ndarray, wavelength_um: float, *, observation_uncertainty: np.ndarray | None=None, ridge: float=0.0, max_condition_number: float=1000000.0, valid_temperature_range_k: tuple[float, float]=(200.0, 380.0)) -> ComponentRetrievalResult
```

定义类型：function；[源码第 26 行](C:/work/ls4t/base/lsct.py:26)。

Solve ``weights @ component_radiance = observed_radiance`` per pixel.  The last radiance axis is observation/angle and the final weights axes are ``(observation, component)``. Invalid observations are omitted per pixel.

同名测试引用：[tests/test_msg_aatsr_comparison.py:24](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:24)、[tests/test_retrieval.py:4](C:/work/ls4t/tests/test_retrieval.py:4)

### `retrieve_components_window`

```python
retrieve_components_window(observed_radiance: np.ndarray, effective_weights: np.ndarray, wavelength_um: float, *, window_size: int=5, observation_uncertainty: np.ndarray | None=None, ridge: float=0.0, max_condition_number: float=1000000.0, valid_temperature_range_k: tuple[float, float]=(200.0, 380.0)) -> ComponentRetrievalResult
```

定义类型：function；[源码第 115 行](C:/work/ls4t/base/lsct.py:115)。

Window LSCT for cases with fewer angles than components.  Component radiances are assumed locally constant inside each moving window, while effective-emissivity weights may vary by pixel and angle. This is the production baseline corresponding to the legacy 5x

同名测试引用：[tests/test_retrieval.py:4](C:/work/ls4t/tests/test_retrieval.py:4)

### `sample_hom_Emis`

```python
sample_hom_Emis(lai, hspot, wavelength, emissivity_soil, emissivity_leaf, vza, sza, raa)
```

定义类型：function；[源码第 201 行](C:/work/ls4t/base/lsct.py:201)。

1.initial

### `sample_hom_Emis2`

```python
sample_hom_Emis2(lai, hspot, wavelength, emissivity_soil, emissivity_leaf, vza, sza, raa)
```

定义类型：function；[源码第 214 行](C:/work/ls4t/base/lsct.py:214)。

1.initial

### `cal_rad_from_lst`

```python
cal_rad_from_lst(lst, wl, lai, vza, emisS, emisV)
```

定义类型：function；[源码第 227 行](C:/work/ls4t/base/lsct.py:227)。

根据lst计算rad :param lst: 反演出来的lst nl*ns :param wl: 波长 :param lai: 叶面积 nl * ns :param vza: 天顶角 nl*ns :param emisS: 土壤发射率 nl*ns :param emisV: 植被发射率 nl*ns :return:

同名测试引用：[tests/test_slstr_case_dependencies.py:18](C:/work/ls4t/tests/test_slstr_case_dependencies.py:18)

### `cal_fvc_from_lai`

```python
cal_fvc_from_lai(thetav, lai)
```

定义类型：function；[源码第 247 行](C:/work/ls4t/base/lsct.py:247)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:17](C:/work/ls4t/tests/test_slstr_case_dependencies.py:17)

### `cal_effective_emissivity_hom`

```python
cal_effective_emissivity_hom(lai, hspot, wl, emisS, emisV, vza, sza, vaa, saa, n, m, CI=1.0)
```

定义类型：function；[源码第 257 行](C:/work/ls4t/base/lsct.py:257)。

计算均值假设下冠层的有效发射率，既能处理单点多角度输入又能处理区域输入 :param lai: 叶面积指数 float 或 nl*ns :param hspot: 热点参数 float :param wl: 波长 float :param emisS: 土壤发射率 float 或 nl*ns :param emisV: 植被发射率 float 或 nl*ns :param vza: 观测天顶角 (n,) 或 nl*ns*n :param sza: 太阳天顶角 (n,)/float 或 nl*ns*n(nl*ns) 

### `cal_rad_from_lst_fvc`

```python
cal_rad_from_lst_fvc(lst, wl, fvc, emisS, emisV)
```

定义类型：function；[源码第 340 行](C:/work/ls4t/base/lsct.py:340)。

根据lst计算rad，不输入lai，直接输入fvc，适用于NDVI反演 :param lst: 反演出来的lst nl*ns :param wl: 波长 :param fvc: 植被覆盖度 nl * ns :param emisS: 土壤发射率 nl*ns :param emisV: 植被发射率 nl*ns :return:

同名测试引用：[tests/test_aatsr_case_dependencies.py:69](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:69)

### `cal_psoil_hom`

```python
cal_psoil_hom(lai, sza)
```

定义类型：function；[源码第 358 行](C:/work/ls4t/base/lsct.py:358)。

计算均值假设下冠层的光照土壤占总土壤的比例 :param lai: 叶面积指数 :param sza: 太阳天顶角 :return: psoil 光照土壤占总土壤的比例 计算公式：psoil = exp(-G*LAI/cos(sza))

同名测试引用：[tests/test_aatsr_case_dependencies.py:69](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:69)

### `constraint_func_Nangle_2component`

```python
constraint_func_Nangle_2component(x, lst, d, ws=None, wl=10.8)
```

定义类型：function；[源码第 377 行](C:/work/ls4t/base/lsct.py:377)。

两组分温差限制,土壤植被 温差限制 :param x: 组分能量 :param ws: 窗口大小 :param lst: 垂直LST,注意此处为ws*ws*n :param d: 光照土壤与阴影土壤的温差范围,单位是K [min,max] :return: 约束条件值

### `constraint_func_Nangle_3component`

```python
constraint_func_Nangle_3component(x, lst, d12, d23, ws=None, wl=10.8)
```

定义类型：function；[源码第 402 行](C:/work/ls4t/base/lsct.py:402)。

三组分温差限制,光照阴影土壤、阴影土壤植被 温差限制 :param x: 组分能量 :param ws: 窗口大小 :param lst: 垂直LST,注意此处为ws*ws*n :param d12: 光照土壤与阴影土壤的温差范围,单位是K [min,max] :param d23: 阴影土壤与植被的温差范围,单位是K [min,max] :return: 约束条件值

### `set_weights`

```python
set_weights(window_size)
```

定义类型：function；[源码第 432 行](C:/work/ls4t/base/lsct.py:432)。

无 docstring；算法解释见人工审阅章节。

### `set_x0_bnds_Nangle_Mcomponent`

```python
set_x0_bnds_Nangle_Mcomponent(lst, n, m, ws=None, wl=10.8)
```

定义类型：function；[源码第 446 行](C:/work/ls4t/base/lsct.py:446)。

设置初值和边界 :param lst: LST,注意此处为 (n,) :param wl: 波长 :return: x0,bnds

### `set_x0_bnds_Nangle_Mcomponent_night`

```python
set_x0_bnds_Nangle_Mcomponent_night(lst, n, m, ws=None, wl=10.8)
```

定义类型：function；[源码第 475 行](C:/work/ls4t/base/lsct.py:475)。

设置初值和边界 :param lst: LST,注意此处为 (n,) :param wl: 波长 :return: x0,bnds

### `fitting_Nangle_Mcomponent_point`

```python
fitting_Nangle_Mcomponent_point(w, b, n, m, method='ridge')
```

定义类型：function；[源码第 504 行](C:/work/ls4t/base/lsct.py:504)。

多角度 多组分 点 :param w: 有效发射率矩阵, shape (n,m) :param b: 亮温矩阵, shape (n,) :param n: 角度数 :param m: 组分数 :param method: 线性求解方法 ridge、lasso、bayesianridge、ls :return: p： 组分能量，shape (m,)

### `fitting_Nangle_Mcomponent_window_quadratic`

```python
fitting_Nangle_Mcomponent_window_quadratic(w, b, n, m, mask, weight, window_size=5)
```

定义类型：function；[源码第 528 行](C:/work/ls4t/base/lsct.py:528)。

多角度 多组分 窗口内组分温度二次分布 :param w: 有效发射率矩阵 shape(ws,ws,n,m) ws:窗口大小 :param b: 亮温矩阵 shape(ws,ws,n) :param mask: 窗口掩码,能反演是1，不能是0 shape(ws,ws,n) :param n: 角度数 :param m: 组分数 :param window_size: 窗口大小 :return: p： 组分能量 shape(nl,ns,m）

## base/lsct_window.py

源码：[打开文件](C:/work/ls4t/base/lsct_window.py)；291 行，11 个定义。

### `planck`

```python
planck(wavelength, Ts)
```

定义类型：function；[源码第 16 行](C:/work/ls4t/base/lsct_window.py:16)。

基于planck公式，计算某个波长时候，从温度到辐射的转换 :param wavelength: 波长，10.5 :param Ts: 温度，可以是亮温，也可以是摄氏度 :return: 辐射

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inv_planck`

```python
inv_planck(wavelength, rad)
```

定义类型：function；[源码第 35 行](C:/work/ls4t/base/lsct_window.py:35)。

基于planck公式，计算从辐射到亮温的转换 :param wavelength: 波长,10.5 :param rad: 辐射 :return: 亮温 （300）

同名测试引用：[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `constraint_func_Nangle_2component`

```python
constraint_func_Nangle_2component(x, lst, d, ws=None, wl=10.8)
```

定义类型：function；[源码第 49 行](C:/work/ls4t/base/lsct_window.py:49)。

两组分温差限制,土壤植被 温差限制 :param x: 组分能量 :param ws: 窗口大小 :param lst: 垂直LST,注意此处为ws*ws*n :param d: 光照土壤与阴影土壤的温差范围,单位是K [min,max] :return: 约束条件值

### `constraint_func_Nangle_3component`

```python
constraint_func_Nangle_3component(x, lst, d12, d23, ws=None, wl=10.8)
```

定义类型：function；[源码第 74 行](C:/work/ls4t/base/lsct_window.py:74)。

三组分温差限制,光照阴影土壤、阴影土壤植被 温差限制 :param x: 组分能量 :param ws: 窗口大小 :param lst: 垂直LST,注意此处为ws*ws*n :param d12: 光照土壤与阴影土壤的温差范围,单位是K [min,max] :param d23: 阴影土壤与植被的温差范围,单位是K [min,max] :return: 约束条件值

### `set_weights`

```python
set_weights(window_size)
```

定义类型：function；[源码第 104 行](C:/work/ls4t/base/lsct_window.py:104)。

无 docstring；算法解释见人工审阅章节。

### `set_x0_bnds_Nangle_Mcomponent`

```python
set_x0_bnds_Nangle_Mcomponent(lst, n, m, ws=None, wl=10.8)
```

定义类型：function；[源码第 118 行](C:/work/ls4t/base/lsct_window.py:118)。

设置初值和边界 :param lst: LST,注意此处为 (n,) :param wl: 波长 :return: x0,bnds

### `fitting_unknown_nonlinear_min`

```python
fitting_unknown_nonlinear_min(fun, y, A, xn, x0, bnds, method='Powell', constraints=None, **kwargs)
```

定义类型：function；[源码第 145 行](C:/work/ls4t/base/lsct_window.py:145)。

非线性反演/回归，基于minimize函数，能给初值，也能给边界条件 参数:     fun: 目标函数，格式为fun(x, *args)     y: 因变量数组     A: 自变量矩阵     xn: 变量个数     x0: 初始值     bnds: 边界条件列表     method: 优化方法('Powell','SLSQP'等)     constraints: 约束条件     **kwargs: 传递给目标函数的额外参数 返回:     优化结果向量

### `fitting_Nangle_Mcomponent_window`

```python
fitting_Nangle_Mcomponent_window(w, b, n, m, mask, weight, constraints, x0, bounds, window_size=5, method='SLSQP')
```

定义类型：function；[源码第 174 行](C:/work/ls4t/base/lsct_window.py:174)。

多角度 多组分 窗口 :param w: 有效发射率矩阵 shape(ws,ws,n,m) ws:窗口大小 :param b: 亮温矩阵 shape(ws,ws,n) :param mask: 窗口掩码,能反演是1，不能是0 shape(ws,ws,n) :param n: 角度数 :param m: 组分数 :param window_size: 窗口大小 :param method: 非线性求解方法 BFGS/powell/SLSQP/L-BFGS-B/TNC :return: p： 组分能量 shape(nl

同名测试引用：[tests/test_aatsr_case_dependencies.py:70](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:70)

### `fitting_Nangle_Mcomponent_window.objective_func`

```python
fitting_Nangle_Mcomponent_window.objective_func(x, y, A, xn, weight)
```

定义类型：nested；[源码第 214 行](C:/work/ls4t/base/lsct_window.py:214)。

无 docstring；算法解释见人工审阅章节。

### `inv_lsct2_window`

```python
inv_lsct2_window(n, m, ws, wl, w, b, mask, lst)
```

定义类型：function；[源码第 230 行](C:/work/ls4t/base/lsct_window.py:230)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:70](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:70)、[tests/test_slstr_case_dependencies.py:138](C:/work/ls4t/tests/test_slstr_case_dependencies.py:138)

### `inv_lsct3_window`

```python
inv_lsct3_window(n, m, ws, wl, w, b, mask, lst)
```

定义类型：function；[源码第 261 行](C:/work/ls4t/base/lsct_window.py:261)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:138](C:/work/ls4t/tests/test_slstr_case_dependencies.py:138)

## base/lst.py

源码：[打开文件](C:/work/ls4t/base/lst.py)；218 行，5 个定义。

### `SplitWindowModel.__post_init__`

```python
SplitWindowModel.__post_init__(self) -> None
```

定义类型：method；[源码第 29 行](C:/work/ls4t/base/lst.py:29)。

无 docstring；算法解释见人工审阅章节。

### `SplitWindowModel.retrieve`

```python
SplitWindowModel.retrieve(self, bt1_k: np.ndarray, bt2_k: np.ndarray, emissivity1: np.ndarray, emissivity2: np.ndarray, water_vapour: np.ndarray, view_zenith_deg: np.ndarray, *, cloud_mask: np.ndarray | None=None) -> SplitWindowResult
```

定义类型：method；[源码第 45 行](C:/work/ls4t/base/lst.py:45)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_retrieval.py:14](C:/work/ls4t/tests/test_retrieval.py:14)

### `vegetation_fraction_from_lai`

```python
vegetation_fraction_from_lai(lai: np.ndarray | float, view_zenith_deg: np.ndarray | float, projection_g: float=0.5) -> np.ndarray
```

定义类型：function；[源码第 127 行](C:/work/ls4t/base/lst.py:127)。

Convert LAI to directional vegetation fraction.

### `effective_emissivity`

```python
effective_emissivity(soil_emissivity: np.ndarray | float, vegetation_emissivity: np.ndarray | float, vegetation_fraction: np.ndarray | float, *, scattering_factor: float=0.75, maximum: float=0.995) -> np.ndarray
```

定义类型：function；[源码第 145 行](C:/work/ls4t/base/lst.py:145)。

Calculate mixed-pixel emissivity used by the split-window model.

### `retrieve_dual_channel_lst`

```python
retrieve_dual_channel_lst(observation: DualChannelObservation, model: SplitWindowModel, *, scattering_factor: float=0.75) -> SplitWindowResult
```

定义类型：function；[源码第 189 行](C:/work/ls4t/base/lst.py:189)。

Run the common split-window physics without owning file traversal.

## base/metrics.py

源码：[打开文件](C:/work/ls4t/base/metrics.py)；18 行，1 个定义。

### `cal_rmse_r2`

```python
cal_rmse_r2(data1, data2, tshred=9)
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/metrics.py:11)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:71](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:71)

## base/modis/__init__.py

源码：[打开文件](C:/work/ls4t/base/modis/__init__.py)；1 行，0 个定义。

## base/modis/modis_data.py

源码：[打开文件](C:/work/ls4t/base/modis/modis_data.py)；43 行，4 个定义。

### `read_native_product`

```python
read_native_product(path)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/base/modis/modis_data.py:30)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:11](C:/work/ls4t/tests/test_dual_thermal_sensors.py:11)

### `write_data_product`

```python
write_data_product(path, item) -> None
```

定义类型：function；[源码第 34 行](C:/work/ls4t/base/modis/modis_data.py:34)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:12](C:/work/ls4t/tests/test_dual_thermal_sensors.py:12)、[tests/test_slstr_products.py:16](C:/work/ls4t/tests/test_slstr_products.py:16)

### `read_data_product`

```python
read_data_product(path)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/base/modis/modis_data.py:38)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:10](C:/work/ls4t/tests/test_dual_thermal_sensors.py:10)、[tests/test_slstr_products.py:12](C:/work/ls4t/tests/test_slstr_products.py:12)

### `add_lst_auxiliary`

```python
add_lst_auxiliary(item, auxiliary_file)
```

定义类型：function；[源码第 42 行](C:/work/ls4t/base/modis/modis_data.py:42)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:11](C:/work/ls4t/tests/test_slstr_products.py:11)

## base/modis/modis_extract.py

源码：[打开文件](C:/work/ls4t/base/modis/modis_extract.py)；24 行，1 个定义。

### `modis_extract`

```python
modis_extract(indir_raw=None, outdir_data=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/modis/modis_extract.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:26](C:/work/ls4t/tests/test_dual_thermal_sensors.py:26)、[tests/test_flat_structure.py:23](C:/work/ls4t/tests/test_flat_structure.py:23)

## base/modis/modis_lst.py

源码：[打开文件](C:/work/ls4t/base/modis/modis_lst.py)；64 行，3 个定义。

### `retrieve_modis_lst`

```python
retrieve_modis_lst(item, coefficient_file=None)
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/modis/modis_lst.py:11)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:27](C:/work/ls4t/tests/test_dual_thermal_sensors.py:27)

### `produce_modis_lst`

```python
produce_modis_lst(input_path=None, output_path=None, coefficient_file=None, auxiliary_file=None, grid_id=None, algorithm_version=None, uncertainty_k=None) -> None
```

定义类型：function；[源码第 15 行](C:/work/ls4t/base/modis/modis_lst.py:15)。

无 docstring；算法解释见人工审阅章节。

### `modis_lst`

```python
modis_lst(indir_data=None, outdir_lst=None, coefficient_file=None, auxiliary_file=None, years=None, months=None, days=None, grid_id=None, algorithm_version=None, uncertainty_k=None, overwrite=None) -> None
```

定义类型：function；[源码第 37 行](C:/work/ls4t/base/modis/modis_lst.py:37)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:27](C:/work/ls4t/tests/test_dual_thermal_sensors.py:27)

## base/modis/modis_merge.py

源码：[打开文件](C:/work/ls4t/base/modis/modis_merge.py)；10 行，1 个定义。

### `modis_merge`

```python
modis_merge(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/modis/modis_merge.py:7)。

Merge one explicit group; cases decide which scenes belong together.

同名测试引用：[tests/test_dual_thermal_sensors.py:28](C:/work/ls4t/tests/test_dual_thermal_sensors.py:28)、[tests/test_flat_structure.py:24](C:/work/ls4t/tests/test_flat_structure.py:24)

## base/modis/modis_project.py

源码：[打开文件](C:/work/ls4t/base/modis/modis_project.py)；47 行，2 个定义。

### `project_modis_product`

```python
project_modis_product(item, target_grid_file=None, projection_chunk_size=None, cloud_fraction_threshold=None)
```

定义类型：function；[源码第 9 行](C:/work/ls4t/base/modis/modis_project.py:9)。

无 docstring；算法解释见人工审阅章节。

### `modis_project`

```python
modis_project(indir_extract=None, outdir_project=None, target_grid_file=None, years=None, months=None, days=None, projection_chunk_size=None, cloud_fraction_threshold=None, overwrite=None) -> None
```

定义类型：function；[源码第 24 行](C:/work/ls4t/base/modis/modis_project.py:24)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:25](C:/work/ls4t/tests/test_flat_structure.py:25)

## base/modis/modis_region.py

源码：[打开文件](C:/work/ls4t/base/modis/modis_region.py)；12 行，2 个定义。

### `modis_data_region`

```python
modis_data_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/modis/modis_region.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:26](C:/work/ls4t/tests/test_flat_structure.py:26)

### `modis_result_region`

```python
modis_result_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/modis/modis_region.py:11)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:26](C:/work/ls4t/tests/test_flat_structure.py:26)

## base/msg/__init__.py

源码：[打开文件](C:/work/ls4t/base/msg/__init__.py)；1 行，0 个定义。

## base/msg/msg_data.py

源码：[打开文件](C:/work/ls4t/base/msg/msg_data.py)；284 行，10 个定义。

### `MsgDataProduct.shape`

```python
MsgDataProduct.shape(self) -> tuple[int, ...]
```

定义类型：method；[源码第 80 行](C:/work/ls4t/base/msg/msg_data.py:80)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:207](C:/work/ls4t/tests/test_africa_download.py:207)、[tests/test_dual_thermal_sensors.py:49](C:/work/ls4t/tests/test_dual_thermal_sensors.py:49)、[tests/test_flat_structure.py:202](C:/work/ls4t/tests/test_flat_structure.py:202)、[tests/test_kernel_models.py:88](C:/work/ls4t/tests/test_kernel_models.py:88)、[tests/test_msg_aatsr_comparison.py:39](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:39)、[tests/test_msg_case_dependencies.py:142](C:/work/ls4t/tests/test_msg_case_dependencies.py:142)、[tests/test_msg_evo_sample.py:30](C:/work/ls4t/tests/test_msg_evo_sample.py:30)、[tests/test_multisource_normalization.py:108](C:/work/ls4t/tests/test_multisource_normalization.py:108)、[tests/test_normalization.py:22](C:/work/ls4t/tests/test_normalization.py:22)、[tests/test_normalization_raster.py:17](C:/work/ls4t/tests/test_normalization_raster.py:17)、[tests/test_slstr_case_dependencies.py:152](C:/work/ls4t/tests/test_slstr_case_dependencies.py:152)、[tests/test_slstr_evo_sample.py:31](C:/work/ls4t/tests/test_slstr_evo_sample.py:31)、[tests/test_slstr_products.py:23](C:/work/ls4t/tests/test_slstr_products.py:23)、[tests/test_south_america_components.py:113](C:/work/ls4t/tests/test_south_america_components.py:113)、[tests/test_south_america_native_recovery.py:52](C:/work/ls4t/tests/test_south_america_native_recovery.py:52)、[tests/test_spatial_modes.py:17](C:/work/ls4t/tests/test_spatial_modes.py:17)、[tests/test_tsharp.py:62](C:/work/ls4t/tests/test_tsharp.py:62)

### `MsgDataProduct.has_lst_auxiliary`

```python
MsgDataProduct.has_lst_auxiliary(self) -> bool
```

定义类型：method；[源码第 84 行](C:/work/ls4t/base/msg/msg_data.py:84)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:64](C:/work/ls4t/tests/test_slstr_products.py:64)

### `MsgDataProduct.validate`

```python
MsgDataProduct.validate(self, require_lst_auxiliary: bool=False) -> None
```

定义类型：method；[源码第 87 行](C:/work/ls4t/base/msg/msg_data.py:87)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:49](C:/work/ls4t/tests/test_products.py:49)

### `_time_from_name`

```python
_time_from_name(name: str) -> str
```

定义类型：function；[源码第 104 行](C:/work/ls4t/base/msg/msg_data.py:104)。

无 docstring；算法解释见人工审阅章节。

### `read_native_product`

```python
read_native_product(input_path: str | Path, static_file=None) -> MsgDataProduct
```

定义类型：function；[源码第 113 行](C:/work/ls4t/base/msg/msg_data.py:113)。

使用 Satpy 读取一个 SEVIRI native 文件。

同名测试引用：[tests/test_dual_thermal_sensors.py:11](C:/work/ls4t/tests/test_dual_thermal_sensors.py:11)

### `add_lst_auxiliary`

```python
add_lst_auxiliary(item: MsgDataProduct, auxiliary_file: str | Path) -> MsgDataProduct
```

定义类型：function；[源码第 150 行](C:/work/ls4t/base/msg/msg_data.py:150)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:11](C:/work/ls4t/tests/test_slstr_products.py:11)

### `write_auxiliary_product`

```python
write_auxiliary_product(path: str | Path, fields: dict[str, np.ndarray]) -> None
```

定义类型：function；[源码第 166 行](C:/work/ls4t/base/msg/msg_data.py:166)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:15](C:/work/ls4t/tests/test_slstr_products.py:15)

### `write_data_product`

```python
write_data_product(path: str | Path, item: MsgDataProduct, *, reference_path: str | Path | None=None) -> None
```

定义类型：function；[源码第 177 行](C:/work/ls4t/base/msg/msg_data.py:177)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:12](C:/work/ls4t/tests/test_dual_thermal_sensors.py:12)、[tests/test_slstr_products.py:16](C:/work/ls4t/tests/test_slstr_products.py:16)

### `read_data_product`

```python
read_data_product(path: str | Path) -> MsgDataProduct
```

定义类型：function；[源码第 213 行](C:/work/ls4t/base/msg/msg_data.py:213)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:10](C:/work/ls4t/tests/test_dual_thermal_sensors.py:10)、[tests/test_slstr_products.py:12](C:/work/ls4t/tests/test_slstr_products.py:12)

### `msg_extract`

```python
msg_extract(indir_raw=None, outdir_data=None, static_file=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 242 行](C:/work/ls4t/base/msg/msg_data.py:242)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:20](C:/work/ls4t/tests/test_flat_structure.py:20)

## base/msg/msg_lsct.py

源码：[打开文件](C:/work/ls4t/base/msg/msg_lsct.py)；155 行，2 个定义。

### `retrieve_msg_lsct`

```python
retrieve_msg_lsct(input_path, output_path, wavelength_um=None, component_names=None, window_size=None, ridge=None, max_condition_number=None, grid_id=None, algorithm_version=None) -> None
```

定义类型：function；[源码第 36 行](C:/work/ls4t/base/msg/msg_lsct.py:36)。

无 docstring；算法解释见人工审阅章节。

### `msg_lsct`

```python
msg_lsct(indir_lsct_input=None, outdir_lsct=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 118 行](C:/work/ls4t/base/msg/msg_lsct.py:118)。

无 docstring；算法解释见人工审阅章节。

## base/msg/msg_lst.py

源码：[打开文件](C:/work/ls4t/base/msg/msg_lst.py)；158 行，3 个定义。

### `retrieve_msg_lst`

```python
retrieve_msg_lst(item: MsgDataProduct, coefficient_file=None)
```

定义类型：function；[源码第 35 行](C:/work/ls4t/base/msg/msg_lst.py:35)。

无 docstring；算法解释见人工审阅章节。

### `produce_msg_lst`

```python
produce_msg_lst(input_path, output_path, coefficient_file=None, auxiliary_file=None, grid_id=None, algorithm_version=None, uncertainty_k=None) -> None
```

定义类型：function；[源码第 55 行](C:/work/ls4t/base/msg/msg_lst.py:55)。

无 docstring；算法解释见人工审阅章节。

### `msg_lst`

```python
msg_lst(indir_data=None, outdir_lst=None, coefficient_file=None, auxiliary_file=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 107 行](C:/work/ls4t/base/msg/msg_lst.py:107)。

无 docstring；算法解释见人工审阅章节。

## base/msg/msg_project.py

源码：[打开文件](C:/work/ls4t/base/msg/msg_project.py)；108 行，2 个定义。

### `project_msg_product`

```python
project_msg_product(item, target_grid_file=None, projection_chunk_size=None, cloud_fraction_threshold=None)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/base/msg/msg_project.py:22)。

无 docstring；算法解释见人工审阅章节。

### `msg_project`

```python
msg_project(indir_data=None, outdir_project=None, target_grid_file=None, years=None, months=None, days=None, projection_chunk_size=None, cloud_fraction_threshold=None, overwrite=None) -> None
```

定义类型：function；[源码第 43 行](C:/work/ls4t/base/msg/msg_project.py:43)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:21](C:/work/ls4t/tests/test_flat_structure.py:21)

## base/msg/msg_region.py

源码：[打开文件](C:/work/ls4t/base/msg/msg_region.py)；82 行，3 个定义。

### `_resolve_inputs`

```python
_resolve_inputs(value)
```

定义类型：function；[源码第 29 行](C:/work/ls4t/base/msg/msg_region.py:29)。

无 docstring；算法解释见人工审阅章节。

### `msg_data_region`

```python
msg_data_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 41 行](C:/work/ls4t/base/msg/msg_region.py:41)。

Mode 1: crop/mosaic decoded MSG data before retrieval.

同名测试引用：[tests/test_flat_structure.py:22](C:/work/ls4t/tests/test_flat_structure.py:22)

### `msg_result_region`

```python
msg_result_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 64 行](C:/work/ls4t/base/msg/msg_region.py:64)。

Mode 2: crop/mosaic MSG results after image-by-image retrieval.

同名测试引用：[tests/test_flat_structure.py:22](C:/work/ls4t/tests/test_flat_structure.py:22)

## base/normalization/__init__.py

源码：[打开文件](C:/work/ls4t/base/normalization/__init__.py)；37 行，0 个定义。

## base/normalization/_fit.py

源码：[打开文件](C:/work/ls4t/base/normalization/_fit.py)；23 行，1 个定义。

### `fit_linear`

```python
fit_linear(design, target, weights)
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/normalization/_fit.py:7)。

Require residual degrees of freedom and an identifiable weighted model.

## base/normalization/_validation.py

源码：[打开文件](C:/work/ls4t/base/normalization/_validation.py)；11 行，1 个定义。

### `quality_flags`

```python
quality_flags(values)
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/normalization/_validation.py:7)。

Never turn missing/fractional/out-of-range QA values into GOOD by casting.

## base/normalization/angle.py

源码：[打开文件](C:/work/ls4t/base/normalization/angle.py)；154 行，4 个定义。

### `angular_basis`

```python
angular_basis(view_zenith_deg: np.ndarray | float, solar_zenith_deg: np.ndarray | float, relative_azimuth_deg: np.ndarray | float) -> np.ndarray
```

定义类型：function；[源码第 28 行](C:/work/ls4t/base/normalization/angle.py:28)。

无 docstring；算法解释见人工审阅章节。

### `normalize_directional`

```python
normalize_directional(temperature_k: np.ndarray, view_zenith_deg: np.ndarray, solar_zenith_deg: np.ndarray, relative_azimuth_deg: np.ndarray, coefficients_k: np.ndarray, *, reference_view_zenith_deg: float | None=None, reference_solar_zenith_deg: float | None=None, reference_relative_azimuth_deg: float | None=None) -> np.ndarray
```

定义类型：function；[源码第 48 行](C:/work/ls4t/base/normalization/angle.py:48)。

Move observed temperature to a common geometry using calibrated kernels.

同名测试引用：[tests/test_multisource_normalization.py:17](C:/work/ls4t/tests/test_multisource_normalization.py:17)、[tests/test_normalization.py:5](C:/work/ls4t/tests/test_normalization.py:5)

### `fit_directional_coefficients`

```python
fit_directional_coefficients(temperature_k, reference_temperature_k, view_zenith_deg, solar_zenith_deg, relative_azimuth_deg, *, reference_view_zenith_deg=0.0, reference_solar_zenith_deg=30.0, reference_relative_azimuth_deg=0.0, weights=1.0, quality_flag=0) -> DirectionalFit
```

定义类型：function；[源码第 91 行](C:/work/ls4t/base/normalization/angle.py:91)。

Calibrate one three-kernel model from matched same-time reference pairs.  Supply co-located, same-state reference temperatures at the stated reference geometry. Mixing unrelated dates/land covers can confound geometry and LST. rmse_k is an in-sample diagnostic

同名测试引用：[tests/test_multisource_normalization.py:15](C:/work/ls4t/tests/test_multisource_normalization.py:15)

### `angle_normalize_years`

```python
angle_normalize_years(indir_temperature=None, outdir_angle=None, years=None, overwrite=None) -> None
```

定义类型：function；[源码第 119 行](C:/work/ls4t/base/normalization/angle.py:119)。

按年份手工执行角度归一化，不调用时间或空间归一化。

同名测试引用：[tests/test_flat_structure.py:27](C:/work/ls4t/tests/test_flat_structure.py:27)

## base/normalization/annual.py

源码：[打开文件](C:/work/ls4t/base/normalization/annual.py)；143 行，8 个定义。

### `annual_phase`

```python
annual_phase(dates_or_doy, *, year_length=365) -> np.ndarray
```

定义类型：function；[源码第 21 行](C:/work/ls4t/base/normalization/annual.py:21)。

Map dates or 1-based DOY to [0,1); invalid samples/NaT become NaN.  Datetime strings must be timezone-free (or already converted to the chosen local calendar); this function does not infer timezone/overpass time. Multi-year dates align by fraction of each actu

同名测试引用：[tests/test_annual_cycle.py:34](C:/work/ls4t/tests/test_annual_cycle.py:34)

### `_annual_design`

```python
_annual_design(phase, harmonics)
```

定义类型：function；[源码第 66 行](C:/work/ls4t/base/normalization/annual.py:66)。

无 docstring；算法解释见人工审阅章节。

### `ATCFit.mean_k`

```python
ATCFit.mean_k(self) -> float
```

定义类型：method；[源码第 82 行](C:/work/ls4t/base/normalization/annual.py:82)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:11](C:/work/ls4t/tests/test_annual_cycle.py:11)、[tests/test_multisource_normalization.py:42](C:/work/ls4t/tests/test_multisource_normalization.py:42)

### `ATCFit.amplitudes_k`

```python
ATCFit.amplitudes_k(self) -> np.ndarray
```

定义类型：method；[源码第 86 行](C:/work/ls4t/base/normalization/annual.py:86)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:12](C:/work/ls4t/tests/test_annual_cycle.py:12)

### `ATCFit.peak_days`

```python
ATCFit.peak_days(self, year_length=365) -> np.ndarray
```

定义类型：method；[源码第 89 行](C:/work/ls4t/base/normalization/annual.py:89)。

First peak of EACH harmonic in [1,1+N/j), not the combined-curve peak.  Undefined phase of a zero-amplitude harmonic returns NaN.

同名测试引用：[tests/test_annual_cycle.py:13](C:/work/ls4t/tests/test_annual_cycle.py:13)

### `ATCFit.predict`

```python
ATCFit.predict(self, dates_or_doy, *, year_length=365) -> np.ndarray
```

定义类型：method；[源码第 100 行](C:/work/ls4t/base/normalization/annual.py:100)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:15](C:/work/ls4t/tests/test_annual_cycle.py:15)、[tests/test_kernel_models.py:80](C:/work/ls4t/tests/test_kernel_models.py:80)

### `ATCFit.normalize`

```python
ATCFit.normalize(self, temperature_k, dates_or_doy, *, reference, year_length=365, reference_year_length=365) -> np.ndarray
```

定义类型：method；[源码第 104 行](C:/work/ls4t/base/normalization/annual.py:104)。

Shift season while retaining anomalies; NaN observations remain NaN.

同名测试引用：[tests/test_annual_cycle.py:16](C:/work/ls4t/tests/test_annual_cycle.py:16)、[tests/test_kernel_models.py:43](C:/work/ls4t/tests/test_kernel_models.py:43)

### `fit_annual_cycle`

```python
fit_annual_cycle(temperature_k, dates_or_doy, *, harmonics=1, year_length=365, weights=1.0, quality_flag=0, minimum_coverage=0.5) -> ATCFit
```

定义类型：function；[源码第 115 行](C:/work/ls4t/base/normalization/annual.py:115)。

Fit one pixel/site at comparable solar time, geometry and spatial support.  harmonics=1 gives a standard three-coefficient ATC; 2 adds a half-year harmonic (five coefficients). Coverage is 1 minus the largest circular phase gap, after QA filtering. Repeated ye

同名测试引用：[tests/test_annual_cycle.py:10](C:/work/ls4t/tests/test_annual_cycle.py:10)

## base/normalization/downscale.py

源码：[打开文件](C:/work/ls4t/base/normalization/downscale.py)；153 行，5 个定义。

### `tsharp_cover_fraction`

```python
tsharp_cover_fraction(ndvi) -> np.ndarray
```

定义类型：function；[源码第 29 行](C:/work/ls4t/base/normalization/downscale.py:29)。

Agam simplified fractional cover: 1 - (1 - NDVI)**0.625.  NDVI is decoded, dimensionless and in [0,1]. Outside-domain values become NaN, never clipped into bare soil. Water/snow masks belong in the supplied quality flags; NDVI alone is not a water classifier. 

同名测试引用：[tests/test_tsharp.py:25](C:/work/ls4t/tests/test_tsharp.py:25)

### `downscale_temperature`

```python
downscale_temperature(coarse_temperature_k, fine_predictors, *, coarse_quality_flag=0, fine_quality_flag=0, fine_weights=None, minimum_coverage=1.0, method='linear') -> DownscaleResult
```

定义类型：function；[源码第 43 行](C:/work/ls4t/base/normalization/downscale.py:43)。

Regress on coarse predictor means, predict fine LST, restore coarse means.  fine_predictors: (fine_rows, fine_cols[, features]); NaN marks no coverage. fine_weights: positive pixel areas, default equal areas. Coverage counts invalid predictor/quality pixels in

同名测试引用：[tests/test_multisource_normalization.py:85](C:/work/ls4t/tests/test_multisource_normalization.py:85)、[tests/test_tsharp.py:35](C:/work/ls4t/tests/test_tsharp.py:35)

### `downscale_temperature.sum_blocks`

```python
downscale_temperature.sum_blocks(values)
```

定义类型：nested；[源码第 93 行](C:/work/ls4t/base/normalization/downscale.py:93)。

无 docstring；算法解释见人工审阅章节。

### `downscale_temperature.expand`

```python
downscale_temperature.expand(values)
```

定义类型：nested；[源码第 96 行](C:/work/ls4t/base/normalization/downscale.py:96)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_tsharp.py:12](C:/work/ls4t/tests/test_tsharp.py:12)

### `downscale_tsharp`

```python
downscale_tsharp(coarse_temperature_k, fine_ndvi, *, coarse_quality_flag=0, fine_quality_flag=0, fine_weights=None, minimum_coverage=1.0) -> DownscaleResult
```

定义类型：function；[源码第 144 行](C:/work/ls4t/base/normalization/downscale.py:144)。

TsHARP convenience entry; coefficients are [intercept_K, slope_K_per_fc].

同名测试引用：[tests/test_tsharp.py:51](C:/work/ls4t/tests/test_tsharp.py:51)

## base/normalization/fusion.py

源码：[打开文件](C:/work/ls4t/base/normalization/fusion.py)；184 行，2 个定义。

### `fuse_l3n`

```python
fuse_l3n(inputs: Sequence[NormalizedField], *, innovation_threshold_sigma: float | None=None, minimum_sensors: int | None=None) -> FusionResult
```

定义类型：function；[源码第 46 行](C:/work/ls4t/base/normalization/fusion.py:46)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization.py:6](C:/work/ls4t/tests/test_normalization.py:6)

### `fusion_years`

```python
fusion_years(input_roots=None, output_root=None, years=None, innovation_threshold_sigma=None, minimum_sensors=None, overwrite=None) -> None
```

定义类型：function；[源码第 110 行](C:/work/ls4t/base/normalization/fusion.py:110)。

按相同年份和相对文件名融合多个已归一化传感器目录。

同名测试引用：[tests/test_flat_structure.py:28](C:/work/ls4t/tests/test_flat_structure.py:28)

## base/normalization/kernels.py

源码：[打开文件](C:/work/ls4t/base/normalization/kernels.py)；250 行，13 个定义。

### `available_kernels`

```python
available_kernels() -> dict
```

定义类型：function；[源码第 58 行](C:/work/ls4t/base/normalization/kernels.py:58)。

Return independent metadata dictionaries, safe for JSON configuration.

### `KernelTerm.__post_init__`

```python
KernelTerm.__post_init__(self)
```

定义类型：method；[源码第 69 行](C:/work/ls4t/base/normalization/kernels.py:69)。

无 docstring；算法解释见人工审阅章节。

### `evaluate_kernel`

```python
evaluate_kernel(term: KernelTerm | str, vza, sza, raa) -> np.ndarray
```

定义类型：function；[源码第 85 行](C:/work/ls4t/base/normalization/kernels.py:85)。

Evaluate one kernel without changing input arrays; preserve broadcast shape.

同名测试引用：[tests/test_kernel_models.py:29](C:/work/ls4t/tests/test_kernel_models.py:29)

### `KernelModel.__post_init__`

```python
KernelModel.__post_init__(self)
```

定义类型：method；[源码第 118 行](C:/work/ls4t/base/normalization/kernels.py:118)。

无 docstring；算法解释见人工审阅章节。

### `KernelModel.design_matrix`

```python
KernelModel.design_matrix(self, vza, sza, raa) -> np.ndarray
```

定义类型：method；[源码第 126 行](C:/work/ls4t/base/normalization/kernels.py:126)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:38](C:/work/ls4t/tests/test_kernel_models.py:38)

### `KernelModel.to_dict`

```python
KernelModel.to_dict(self) -> dict
```

定义类型：method；[源码第 129 行](C:/work/ls4t/base/normalization/kernels.py:129)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:52](C:/work/ls4t/tests/test_kernel_models.py:52)

### `KernelModel.from_dict`

```python
KernelModel.from_dict(cls, config: dict) -> KernelModel
```

定义类型：method；[源码第 133 行](C:/work/ls4t/base/normalization/kernels.py:133)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:52](C:/work/ls4t/tests/test_kernel_models.py:52)

### `kernel_model`

```python
kernel_model(preset: str) -> KernelModel
```

定义类型：function；[源码第 137 行](C:/work/ls4t/base/normalization/kernels.py:137)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:36](C:/work/ls4t/tests/test_kernel_models.py:36)

### `KernelFit.predict`

```python
KernelFit.predict(self, vza, sza, raa) -> np.ndarray
```

定义类型：method；[源码第 153 行](C:/work/ls4t/base/normalization/kernels.py:153)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:15](C:/work/ls4t/tests/test_annual_cycle.py:15)、[tests/test_kernel_models.py:80](C:/work/ls4t/tests/test_kernel_models.py:80)

### `KernelFit.normalize`

```python
KernelFit.normalize(self, temperature_k, vza, sza, raa, *, reference_vza=0.0, reference_sza=None, reference_raa=0.0) -> np.ndarray
```

定义类型：method；[源码第 156 行](C:/work/ls4t/base/normalization/kernels.py:156)。

Preserve the observed residual; default is nadir at the SAME solar angle.

同名测试引用：[tests/test_annual_cycle.py:16](C:/work/ls4t/tests/test_annual_cycle.py:16)、[tests/test_kernel_models.py:43](C:/work/ls4t/tests/test_kernel_models.py:43)

### `_replace_parameters`

```python
_replace_parameters(model, keys, values)
```

定义类型：function；[源码第 166 行](C:/work/ls4t/base/normalization/kernels.py:166)。

无 docstring；算法解释见人工审阅章节。

### `fit_kernel_model`

```python
fit_kernel_model(model: KernelModel, temperature_k, vza, sza, raa, *, weights=1.0, quality_flag=0, solver='linear', parameter_bounds=None, method='Powell', options=None) -> KernelFit
```

定义类型：function；[源码第 172 行](C:/work/ls4t/base/normalization/kernels.py:172)。

Fit ONE co-located/same-state angular sample set, not a mixed image/time pool.  Linear: all kernel shape parameters are fixed. Minimize: variable projection estimates ONLY named shape parameters (e.g. {'rl.k': (0.1, 3.)}); WLS solves coefficients at each evalu

同名测试引用：[tests/test_kernel_models.py:41](C:/work/ls4t/tests/test_kernel_models.py:41)

### `fit_kernel_model.objective`

```python
fit_kernel_model.objective(values)
```

定义类型：nested；[源码第 217 行](C:/work/ls4t/base/normalization/kernels.py:217)。

无 docstring；算法解释见人工审阅章节。

## base/normalization/profile.py

源码：[打开文件](C:/work/ls4t/base/normalization/profile.py)；42 行，3 个定义。

### `NormalizationProfile.__post_init__`

```python
NormalizationProfile.__post_init__(self) -> None
```

定义类型：method；[源码第 22 行](C:/work/ls4t/base/normalization/profile.py:22)。

无 docstring；算法解释见人工审阅章节。

### `NormalizationProfile.profile_id`

```python
NormalizationProfile.profile_id(self) -> str
```

定义类型：method；[源码第 33 行](C:/work/ls4t/base/normalization/profile.py:33)。

无 docstring；算法解释见人工审阅章节。

### `NormalizationProfile.assert_compatible`

```python
NormalizationProfile.assert_compatible(self, other: 'NormalizationProfile') -> None
```

定义类型：method；[源码第 38 行](C:/work/ls4t/base/normalization/profile.py:38)。

无 docstring；算法解释见人工审阅章节。

## base/normalization/raster.py

源码：[打开文件](C:/work/ls4t/base/normalization/raster.py)；230 行，10 个定义。

### `_band_number`

```python
_band_number(dataset, selector)
```

定义类型：function；[源码第 16 行](C:/work/ls4t/base/normalization/raster.py:16)。

无 docstring；算法解释见人工审阅章节。

### `_read`

```python
_read(path, band=None, *, scale=None, offset=None)
```

定义类型：function；[源码第 29 行](C:/work/ls4t/base/normalization/raster.py:29)。

无 docstring；算法解释见人工审阅章节。

### `_same_grid`

```python
_same_grid(first, second, *, nested=False)
```

定义类型：function；[源码第 52 行](C:/work/ls4t/base/normalization/raster.py:52)。

无 docstring；算法解释见人工审阅章节。

### `_field`

```python
_field(value, grid)
```

定义类型：function；[源码第 77 行](C:/work/ls4t/base/normalization/raster.py:77)。

无 docstring；算法解释见人工审阅章节。

### `_protect`

```python
_protect(output, values)
```

定义类型：function；[源码第 89 行](C:/work/ls4t/base/normalization/raster.py:89)。

无 docstring；算法解释见人工审阅章节。

### `_prepare`

```python
_prepare(input_path, output_path, stage, *, temperature_band, quality_band, temperature_scale, temperature_offset, overwrite)
```

定义类型：function；[源码第 95 行](C:/work/ls4t/base/normalization/raster.py:95)。

无 docstring；算法解释见人工审阅章节。

### `_save`

```python
_save(output, reference, values, flags, provenance, stage, input_path, parameters, extra=None)
```

定义类型：function；[源码第 120 行](C:/work/ls4t/base/normalization/raster.py:120)。

无 docstring；算法解释见人工审阅章节。

### `angle_normalize_raster`

```python
angle_normalize_raster(input_path, output_path, *, view_zenith_deg, solar_zenith_deg, relative_azimuth_deg, coefficients_k, reference_view_zenith_deg=0.0, reference_solar_zenith_deg=30.0, reference_relative_azimuth_deg=0.0, temperature_band=None, quality_band=None, temperature_scale=None, temperature_offset=None, overwrite=False)
```

定义类型：function；[源码第 133 行](C:/work/ls4t/base/normalization/raster.py:133)。

Normalize one source to explicit reference geometry; coefficients are required.

同名测试引用：[tests/test_normalization_raster.py:32](C:/work/ls4t/tests/test_normalization_raster.py:32)

### `time_normalize_raster`

```python
time_normalize_raster(input_path, output_path, *, local_solar_time_hour, amplitude_k, peak_hour, reference_hour=13.5, temperature_band=None, quality_band=None, temperature_scale=None, temperature_offset=None, overwrite=False)
```

定义类型：function；[源码第 162 行](C:/work/ls4t/base/normalization/raster.py:162)。

Normalize one source to a common local solar hour using supplied DTC parameters.

同名测试引用：[tests/test_normalization_raster.py:54](C:/work/ls4t/tests/test_normalization_raster.py:54)

### `downscale_raster`

```python
downscale_raster(input_path, output_path, *, predictors, fine_quality_flag=0, fine_weights=None, minimum_coverage=1.0, temperature_band=None, quality_band=None, temperature_scale=None, temperature_offset=None, overwrite=False, method='linear')
```

定义类型：function；[源码第 182 行](C:/work/ls4t/base/normalization/raster.py:182)。

Sharpen to the first predictor's grid; method=tsharp takes one NDVI band.

同名测试引用：[tests/test_normalization_raster.py:64](C:/work/ls4t/tests/test_normalization_raster.py:64)

## base/normalization/sensor.py

源码：[打开文件](C:/work/ls4t/base/normalization/sensor.py)；95 行，2 个定义。

### `SensorHarmonization.apply`

```python
SensorHarmonization.apply(self, temperature_k: np.ndarray, uncertainty_k: np.ndarray) -> tuple[np.ndarray, np.ndarray]
```

定义类型：method；[源码第 33 行](C:/work/ls4t/base/normalization/sensor.py:33)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization.py:44](C:/work/ls4t/tests/test_normalization.py:44)

### `sensor_normalize_years`

```python
sensor_normalize_years(indir_space=None, outdir_sensor=None, years=None, sensor_name=None, reference_sensor_name=None, slope=None, offset_k=None, calibration_uncertainty_k=None, overwrite=None) -> None
```

定义类型：function；[源码第 46 行](C:/work/ls4t/base/normalization/sensor.py:46)。

按年份手工执行传感器间标定。

同名测试引用：[tests/test_flat_structure.py:29](C:/work/ls4t/tests/test_flat_structure.py:29)

## base/normalization/space.py

源码：[打开文件](C:/work/ls4t/base/normalization/space.py)；148 行，3 个定义。

### `_aggregate_flags`

```python
_aggregate_flags(flags: np.ndarray, row_index: np.ndarray, column_index: np.ndarray, target_shape: tuple[int, int], valid_mask: np.ndarray) -> np.ndarray
```

定义类型：function；[源码第 21 行](C:/work/ls4t/base/normalization/space.py:21)。

无 docstring；算法解释见人工审阅章节。

### `aggregate_to_grid`

```python
aggregate_to_grid(values: np.ndarray, row_index: np.ndarray, column_index: np.ndarray, target_shape: tuple[int, int], *, weights: np.ndarray | None=None) -> tuple[np.ndarray, np.ndarray]
```

定义类型：function；[源码第 51 行](C:/work/ls4t/base/normalization/space.py:51)。

Aggregate irregular/duplicate source samples without hiding out-of-grid indices.

同名测试引用：[tests/test_normalization.py:9](C:/work/ls4t/tests/test_normalization.py:9)

### `space_normalize_years`

```python
space_normalize_years(indir_time=None, outdir_space=None, years=None, target_shape=None, overwrite=None) -> None
```

定义类型：function；[源码第 90 行](C:/work/ls4t/base/normalization/space.py:90)。

按年份把温度和不确定度聚合到目标网格。

同名测试引用：[tests/test_flat_structure.py:30](C:/work/ls4t/tests/test_flat_structure.py:30)、[tests/test_normalization.py:9](C:/work/ls4t/tests/test_normalization.py:9)

## base/normalization/time.py

源码：[打开文件](C:/work/ls4t/base/normalization/time.py)；129 行，4 个定义。

### `diurnal_anomaly`

```python
diurnal_anomaly(local_solar_time_hour: np.ndarray | float, amplitude_k: np.ndarray | float, peak_hour: np.ndarray | float) -> np.ndarray
```

定义类型：function；[源码第 24 行](C:/work/ls4t/base/normalization/time.py:24)。

无 docstring；算法解释见人工审阅章节。

### `normalize_local_solar_time`

```python
normalize_local_solar_time(temperature_k: np.ndarray, local_solar_time_hour: np.ndarray, amplitude_k: np.ndarray, peak_hour: np.ndarray, *, reference_hour: float | None=None) -> np.ndarray
```

定义类型：function；[源码第 40 行](C:/work/ls4t/base/normalization/time.py:40)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_multisource_normalization.py:47](C:/work/ls4t/tests/test_multisource_normalization.py:47)、[tests/test_normalization.py:10](C:/work/ls4t/tests/test_normalization.py:10)

### `fit_diurnal_cycle`

```python
fit_diurnal_cycle(temperature_k, local_solar_time_hour, *, weights=1.0, quality_flag=0, minimum_span_hours=6.0) -> DiurnalFit
```

定义类型：function；[源码第 69 行](C:/work/ls4t/base/normalization/time.py:69)。

Fit one 24-hour harmonic to one site's/day's geometry-normalized samples.  Hours must use the same local solar time convention as the target. The minimum circular time coverage prevents fitting a narrow overpass cluster. This empirical baseline does not model 

同名测试引用：[tests/test_multisource_normalization.py:41](C:/work/ls4t/tests/test_multisource_normalization.py:41)

### `time_normalize_years`

```python
time_normalize_years(indir_angle=None, outdir_time=None, years=None, overwrite=None) -> None
```

定义类型：function；[源码第 99 行](C:/work/ls4t/base/normalization/time.py:99)。

按年份手工执行地方太阳时归一化。

同名测试引用：[tests/test_flat_structure.py:31](C:/work/ls4t/tests/test_flat_structure.py:31)

## base/parameters.py

源码：[打开文件](C:/work/ls4t/base/parameters.py)；12 行，1 个定义。

### `require_parameters`

```python
require_parameters(**parameters) -> None
```

定义类型：function；[源码第 4 行](C:/work/ls4t/base/parameters.py:4)。

Reject missing execution-specific parameters with a useful message.

## base/product.py

源码：[打开文件](C:/work/ls4t/base/product.py)；116 行，7 个定义。

### `ProductMetadata.__post_init__`

```python
ProductMetadata.__post_init__(self) -> None
```

定义类型：method；[源码第 36 行](C:/work/ls4t/base/product.py:36)。

无 docstring；算法解释见人工审阅章节。

### `ProductMetadata.to_dict`

```python
ProductMetadata.to_dict(self) -> dict[str, Any]
```

定义类型：method；[源码第 50 行](C:/work/ls4t/base/product.py:50)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:52](C:/work/ls4t/tests/test_kernel_models.py:52)

### `ProductMetadata.from_dict`

```python
ProductMetadata.from_dict(cls, value: Mapping[str, Any]) -> 'ProductMetadata'
```

定义类型：method；[源码第 57 行](C:/work/ls4t/base/product.py:57)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:52](C:/work/ls4t/tests/test_kernel_models.py:52)

### `TemperatureProduct.validate`

```python
TemperatureProduct.validate(self) -> None
```

定义类型：method；[源码第 71 行](C:/work/ls4t/base/product.py:71)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:49](C:/work/ls4t/tests/test_products.py:49)

### `product_filename`

```python
product_filename(metadata: ProductMetadata, extension: str='npz') -> str
```

定义类型：function；[源码第 97 行](C:/work/ls4t/base/product.py:97)。

Create the stable LS4T product name without owning directory layout.

同名测试引用：[tests/test_products.py:5](C:/work/ls4t/tests/test_products.py:5)

### `product_filename.stamp`

```python
product_filename.stamp(value: str) -> str
```

定义类型：nested；[源码第 100 行](C:/work/ls4t/base/product.py:100)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:70](C:/work/ls4t/tests/test_msg_evo_sample.py:70)、[tests/test_south_america_components.py:55](C:/work/ls4t/tests/test_south_america_components.py:55)、[tests/test_south_america_monthly_components.py:98](C:/work/ls4t/tests/test_south_america_monthly_components.py:98)

### `product_filename.slug`

```python
product_filename.slug(value: str) -> str
```

定义类型：nested；[源码第 104 行](C:/work/ls4t/base/product.py:104)。

无 docstring；算法解释见人工审阅章节。

## base/quality.py

源码：[打开文件](C:/work/ls4t/base/quality.py)；43 行，3 个定义。

### `new_flags`

```python
new_flags(shape: tuple[int, ...]) -> np.ndarray
```

定义类型：function；[源码第 34 行](C:/work/ls4t/base/quality.py:34)。

无 docstring；算法解释见人工审阅章节。

### `set_flag`

```python
set_flag(flags: np.ndarray, mask: np.ndarray, flag: QualityFlag) -> None
```

定义类型：function；[源码第 38 行](C:/work/ls4t/base/quality.py:38)。

无 docstring；算法解释见人工审阅章节。

### `usable`

```python
usable(flags: np.ndarray, reject: QualityFlag=INVALID_FLAGS) -> np.ndarray
```

定义类型：function；[源码第 42 行](C:/work/ls4t/base/quality.py:42)。

无 docstring；算法解释见人工审阅章节。

## base/radiometry.py

源码：[打开文件](C:/work/ls4t/base/radiometry.py)；112 行，5 个定义。

### `planck_radiance`

```python
planck_radiance(wavelength_um: float, temperature_k: np.ndarray | float) -> np.ndarray
```

定义类型：function；[源码第 15 行](C:/work/ls4t/base/radiometry.py:15)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_physics.py:3](C:/work/ls4t/tests/test_physics.py:3)、[tests/test_retrieval.py:7](C:/work/ls4t/tests/test_retrieval.py:7)

### `inverse_planck`

```python
inverse_planck(wavelength_um: float, radiance: np.ndarray | float) -> np.ndarray
```

定义类型：function；[源码第 27 行](C:/work/ls4t/base/radiometry.py:27)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:48](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:48)、[tests/test_physics.py:3](C:/work/ls4t/tests/test_physics.py:3)

### `decode_temperature`

```python
decode_temperature(raw: np.ndarray, *, scale: float, offset: float=0.0, fill_value: int | float | None=None, source_unit: str='K') -> np.ndarray
```

定义类型：function；[源码第 39 行](C:/work/ls4t/base/radiometry.py:39)。

Decode a stored temperature into kelvin; this is unit decoding, not L3N.

同名测试引用：[tests/test_physics.py:3](C:/work/ls4t/tests/test_physics.py:3)

### `planck`

```python
planck(wavelength, Ts)
```

定义类型：function；[源码第 77 行](C:/work/ls4t/base/radiometry.py:77)。

基于planck公式，计算某个波长时候，从温度到辐射的转换 :param wavelength: 波长，10.5 :param Ts: 温度，可以是亮温，也可以是摄氏度 :return: 辐射

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inv_planck`

```python
inv_planck(wavelength, rad)
```

定义类型：function；[源码第 100 行](C:/work/ls4t/base/radiometry.py:100)。

基于planck公式，计算从辐射到亮温的转换 :param wavelength: 波长,10.5 :param rad: 辐射 :return: 亮温 （300）

同名测试引用：[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

## base/raster.py

源码：[打开文件](C:/work/ls4t/base/raster.py)；274 行，10 个定义。

### `_gdal`

```python
_gdal()
```

定义类型：function；[源码第 13 行](C:/work/ls4t/base/raster.py:13)。

无 docstring；算法解释见人工审阅章节。

### `metadata`

```python
metadata(schema: str, **values: object) -> dict[str, str]
```

定义类型：function；[源码第 22 行](C:/work/ls4t/base/raster.py:22)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:57](C:/work/ls4t/tests/test_africa_download.py:57)、[tests/test_dual_thermal_sensors.py:53](C:/work/ls4t/tests/test_dual_thermal_sensors.py:53)、[tests/test_normalization_raster.py:38](C:/work/ls4t/tests/test_normalization_raster.py:38)、[tests/test_products.py:10](C:/work/ls4t/tests/test_products.py:10)、[tests/test_slstr_products.py:95](C:/work/ls4t/tests/test_slstr_products.py:95)、[tests/test_south_america_native_recovery.py:65](C:/work/ls4t/tests/test_south_america_native_recovery.py:65)、[tests/test_spatial_modes.py:39](C:/work/ls4t/tests/test_spatial_modes.py:39)

### `write_raster`

```python
write_raster(path: str | Path, fields: dict[str, np.ndarray], metadata_values: dict[str, str], reference_path: str | Path | None=None, *, nodata: float | None=None) -> None
```

定义类型：function；[源码第 29 行](C:/work/ls4t/base/raster.py:29)。

无 docstring；算法解释见人工审阅章节。

### `read_raster`

```python
read_raster(path: str | Path) -> tuple[dict[str, np.ndarray], dict[str, str]]
```

定义类型：function；[源码第 93 行](C:/work/ls4t/base/raster.py:93)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization_raster.py:9](C:/work/ls4t/tests/test_normalization_raster.py:9)

### `write_temperature_product`

```python
write_temperature_product(path: str | Path, product, *, reference_path: str | Path | None=None) -> None
```

定义类型：function；[源码第 116 行](C:/work/ls4t/base/raster.py:116)。

Write a validated TemperatureProduct to named-band GeoTIFF.

### `read_temperature_product`

```python
read_temperature_product(path: str | Path)
```

定义类型：function；[源码第 149 行](C:/work/ls4t/base/raster.py:149)。

Read a named-band GeoTIFF as a TemperatureProduct.

### `getSRSPair`

```python
getSRSPair(dataset)
```

定义类型：function；[源码第 192 行](C:/work/ls4t/base/raster.py:192)。

获得给定数据的投影参考系和地理参考系 :param dataset: GDAL地理数据 :return: 投影参考系和地理参考系

### `writevrt_nadir`

```python
writevrt_nadir(infile, datafile, xfile, yfile)
```

定义类型：function；[源码第 204 行](C:/work/ls4t/base/raster.py:204)。

无 docstring；算法解释见人工审阅章节。

### `writevrt_obliq`

```python
writevrt_obliq(infile, datafile, xfile, yfile)
```

定义类型：function；[源码第 209 行](C:/work/ls4t/base/raster.py:209)。

无 docstring；算法解释见人工审阅章节。

### `write_vrt`

```python
write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, noDataValue=65535, bandnumber=1)
```

定义类型：function；[源码第 214 行](C:/work/ls4t/base/raster.py:214)。

导出用于gdal vrt的配置文件 # 与函数配合使用，outfile为转成的文件路径，resampleAlg为重采样的 # dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour) :param vrtfile:  该配置文件名称 :param datafile:  所要操作的文件名称 :param xfile:  经度坐标文件 lon :param yfile:  纬度坐标文件 lat 

## base/rt/__init__.py

源码：[打开文件](C:/work/ls4t/base/rt/__init__.py)；1 行，0 个定义。

## base/rt/emissivity.py

源码：[打开文件](C:/work/ls4t/base/rt/emissivity.py)；73 行，2 个定义。

### `emissivity_direct`

```python
emissivity_direct(Pcom, Ecom)
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/rt/emissivity.py:11)。

无 docstring；算法解释见人工审阅章节。

### `emissivity_scatter_analytical`

```python
emissivity_scatter_analytical(lai, emis_l, emis_s, vza, sza)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/base/rt/emissivity.py:38)。

组分有效发射率，组分观测比例*组分发射率 + 多次散射项 :param lai:  叶面积指数 :param Psoil:  土壤观测比例 :param Pleaf:  叶片观测比例 :param Psoil_sunlit:  光照土壤观测比例 :param Pleaf_sunlit:  光照叶片观测比例 :param emis_l: 叶片发射率 :param emis_s: 土壤发射率 :param vza:    观测天顶角 :param sza:    太阳天顶角 :return:

## base/rt/gap.py

源码：[打开文件](C:/work/ls4t/base/rt/gap.py)；34 行，2 个定义。

### `gap_probability_hom_analytical`

```python
gap_probability_hom_analytical(lai, xza, CI=1.0, G=0.5)
```

定义类型：function；[源码第 10 行](C:/work/ls4t/base/rt/gap.py:10)。

计算均质场景的透过率 :param lai: 叶面积指数 :param xza: 观测/太阳天顶角 :param CI: 聚集指数 :param G: 投影比例 :return: 透过率

同名测试引用：[tests/test_msg_case_dependencies.py:91](C:/work/ls4t/tests/test_msg_case_dependencies.py:91)、[tests/test_slstr_case_dependencies.py:21](C:/work/ls4t/tests/test_slstr_case_dependencies.py:21)

### `gap_probability_hom_hemisphere_analytical`

```python
gap_probability_hom_hemisphere_analytical(lai, CI=1.0)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/base/rt/gap.py:23)。

均质场景的半球平均透过率，一种参数化估算方案 :param lai: 叶面积指数 :param CI:  聚集指数 :return: 半球平均透过率

## base/rt/hom.py

源码：[打开文件](C:/work/ls4t/base/rt/hom.py)；135 行，6 个定义。

### `Hom.set_structure`

```python
Hom.set_structure(self, leaf_area_index, hspot)
```

定义类型：method；[源码第 41 行](C:/work/ls4t/base/rt/hom.py:41)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:97](C:/work/ls4t/tests/test_slstr_case_dependencies.py:97)

### `Hom.set_thermal`

```python
Hom.set_thermal(self, temperature_soil_sunlit, temperature_soil_shaded, temperature_leaf_sunlit, temperature_leaf_shaded)
```

定义类型：method；[源码第 45 行](C:/work/ls4t/base/rt/hom.py:45)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:96](C:/work/ls4t/tests/test_slstr_case_dependencies.py:96)

### `Hom.set_optical`

```python
Hom.set_optical(self, wavelength, emissivity_soil, emissivity_leaf)
```

定义类型：method；[源码第 51 行](C:/work/ls4t/base/rt/hom.py:51)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:98](C:/work/ls4t/tests/test_slstr_case_dependencies.py:98)

### `Hom.set_angle`

```python
Hom.set_angle(self, view_zenith_angle, solar_zenith_angle, relative_azimuth_angle)
```

定义类型：method；[源码第 57 行](C:/work/ls4t/base/rt/hom.py:57)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:99](C:/work/ls4t/tests/test_slstr_case_dependencies.py:99)

### `Hom.run_emis`

```python
Hom.run_emis(self, ifradiance=0)
```

定义类型：method；[源码第 77 行](C:/work/ls4t/base/rt/hom.py:77)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:108](C:/work/ls4t/tests/test_slstr_case_dependencies.py:108)

### `Hom.run`

```python
Hom.run(self, ifradiance=0)
```

定义类型：method；[源码第 101 行](C:/work/ls4t/base/rt/hom.py:101)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:241](C:/work/ls4t/tests/test_africa_download.py:241)、[tests/test_beijing_building_structure.py:8](C:/work/ls4t/tests/test_beijing_building_structure.py:8)、[tests/test_beijing_lai_8day.py:10](C:/work/ls4t/tests/test_beijing_lai_8day.py:10)、[tests/test_normalization_raster.py:81](C:/work/ls4t/tests/test_normalization_raster.py:81)、[tests/test_slstr_case_dependencies.py:3](C:/work/ls4t/tests/test_slstr_case_dependencies.py:3)、[tests/test_south_america_components.py:91](C:/work/ls4t/tests/test_south_america_components.py:91)、[tests/test_south_america_monthly_components.py:99](C:/work/ls4t/tests/test_south_america_monthly_components.py:99)、[tests/test_standalone_cases.py:31](C:/work/ls4t/tests/test_standalone_cases.py:31)

## base/rt/hotspot.py

源码：[打开文件](C:/work/ls4t/base/rt/hotspot.py)；179 行，3 个定义。

### `hotspot_layer`

```python
hotspot_layer(lai, hspot, vza, sza, vsa, CIs=1, CIv=1, G=0.5)
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/rt/hotspot.py:11)。

热点函数，用于土壤热点计算 :param lai: 叶面积指数 :param hspot: 热点系数 :param vza:  观测天顶角 :param sza:  太阳天顶角 :param vsa:  观测-太阳方位角 :param CIi:  聚集指数 :param CIv:  聚集指数 :param G:  投影系数 :return: 双向透过率

同名测试引用：[tests/test_slstr_case_dependencies.py:23](C:/work/ls4t/tests/test_slstr_case_dependencies.py:23)

### `hotspot_analytical`

```python
hotspot_analytical(lai, hspot, vza, sza, vsa, CIi=1, CIv=1, G=0.5)
```

定义类型：function；[源码第 64 行](C:/work/ls4t/base/rt/hotspot.py:64)。

多层植被热点的累计策略，假设为上下两层，上层可视假设全部被光照，下层可视认为层间独立 与 num 相比 ， 热点窄一点，值稍微低一点 :param lai:  叶面积指数 :param hspot:  热点系数 :param vza:  观测天顶角 :param sza:  太阳天顶角 :param vsa:  冠岑-太阳方位角 :param CIi:  聚集指数 :param CIv:  聚集指数 :param G:  投影系数 :return: 光照植被所占的比例，不归一化，双向透过率

### `hotspot_vegetation_volume`

```python
hotspot_vegetation_volume(lai, sza, CI=1.0, G=0.5)
```

定义类型：function；[源码第 162 行](C:/work/ls4t/base/rt/hotspot.py:162)。

植被体系的整体的光照比例 :param lai: 叶面积指数 :param sza: 太阳天顶角 :param CI:  聚集指数 :param G:  投影系数 :return:  光照比例

## base/rt/physicsF.py

源码：[打开文件](C:/work/ls4t/base/rt/physicsF.py)；31 行，2 个定义。

### `planck`

```python
planck(Ts, wavelength=10.8)
```

定义类型：function；[源码第 10 行](C:/work/ls4t/base/rt/physicsF.py:10)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inv_planck`

```python
inv_planck(rad, wavelength=10.8)
```

定义类型：function；[源码第 25 行](C:/work/ls4t/base/rt/physicsF.py:25)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

## base/rt/proportion.py

源码：[打开文件](C:/work/ls4t/base/rt/proportion.py)；19 行，1 个定义。

### `proportion_bidirectional_hom_one`

```python
proportion_bidirectional_hom_one(lai, hspot, vza, sza, vsa)
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/rt/proportion.py:11)。

无 docstring；算法解释见人工审阅章节。

## base/rt/radiance.py

源码：[打开文件](C:/work/ls4t/base/rt/radiance.py)；37 行，2 个定义。

### `radiance_direct`

```python
radiance_direct(Ecom, Rcom)
```

定义类型：function；[源码第 10 行](C:/work/ls4t/base/rt/radiance.py:10)。

无 docstring；算法解释见人工审阅章节。

### `radiance_scatter`

```python
radiance_scatter(Ecom, Rcom)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/base/rt/radiance.py:30)。

无 docstring；算法解释见人工审阅章节。

## base/rt/scatter.py

源码：[打开文件](C:/work/ls4t/base/rt/scatter.py)；35 行，1 个定义。

### `multiple_scattering_analytical_sunlit`

```python
multiple_scattering_analytical_sunlit(lai, vza, sza, refl_soil, refl_leaf)
```

定义类型：function；[源码第 12 行](C:/work/ls4t/base/rt/scatter.py:12)。

    参数化的方案计算多次散射,区分光照和阴影 :param lai: 叶面积指数 :param vza: 观测天顶角 :param sza: 太阳天顶角 :param Kleaf: 比例系数 :param refl_soil: 土壤反射率 :param refl_leaf: 叶片反射率 :return:

## base/slstr/__init__.py

源码：[打开文件](C:/work/ls4t/base/slstr/__init__.py)；1 行，0 个定义。

## base/slstr/slstr_data.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_data.py)；868 行，35 个定义。

### `SlstrExtractedProduct.validate`

```python
SlstrExtractedProduct.validate(self) -> None
```

定义类型：method；[源码第 69 行](C:/work/ls4t/base/slstr/slstr_data.py:69)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:49](C:/work/ls4t/tests/test_products.py:49)

### `SlstrDataProduct.shape`

```python
SlstrDataProduct.shape(self) -> tuple[int, ...]
```

定义类型：method；[源码第 109 行](C:/work/ls4t/base/slstr/slstr_data.py:109)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:207](C:/work/ls4t/tests/test_africa_download.py:207)、[tests/test_dual_thermal_sensors.py:49](C:/work/ls4t/tests/test_dual_thermal_sensors.py:49)、[tests/test_flat_structure.py:202](C:/work/ls4t/tests/test_flat_structure.py:202)、[tests/test_kernel_models.py:88](C:/work/ls4t/tests/test_kernel_models.py:88)、[tests/test_msg_aatsr_comparison.py:39](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:39)、[tests/test_msg_case_dependencies.py:142](C:/work/ls4t/tests/test_msg_case_dependencies.py:142)、[tests/test_msg_evo_sample.py:30](C:/work/ls4t/tests/test_msg_evo_sample.py:30)、[tests/test_multisource_normalization.py:108](C:/work/ls4t/tests/test_multisource_normalization.py:108)、[tests/test_normalization.py:22](C:/work/ls4t/tests/test_normalization.py:22)、[tests/test_normalization_raster.py:17](C:/work/ls4t/tests/test_normalization_raster.py:17)、[tests/test_slstr_case_dependencies.py:152](C:/work/ls4t/tests/test_slstr_case_dependencies.py:152)、[tests/test_slstr_evo_sample.py:31](C:/work/ls4t/tests/test_slstr_evo_sample.py:31)、[tests/test_slstr_products.py:23](C:/work/ls4t/tests/test_slstr_products.py:23)、[tests/test_south_america_components.py:113](C:/work/ls4t/tests/test_south_america_components.py:113)、[tests/test_south_america_native_recovery.py:52](C:/work/ls4t/tests/test_south_america_native_recovery.py:52)、[tests/test_spatial_modes.py:17](C:/work/ls4t/tests/test_spatial_modes.py:17)、[tests/test_tsharp.py:62](C:/work/ls4t/tests/test_tsharp.py:62)

### `SlstrDataProduct.has_lst_auxiliary`

```python
SlstrDataProduct.has_lst_auxiliary(self) -> bool
```

定义类型：method；[源码第 113 行](C:/work/ls4t/base/slstr/slstr_data.py:113)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:64](C:/work/ls4t/tests/test_slstr_products.py:64)

### `SlstrDataProduct.validate`

```python
SlstrDataProduct.validate(self, *, require_lst_auxiliary: bool=False) -> None
```

定义类型：method；[源码第 116 行](C:/work/ls4t/base/slstr/slstr_data.py:116)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:49](C:/work/ls4t/tests/test_products.py:49)

### `_safe_archive_target`

```python
_safe_archive_target(root: Path, member: ZipInfo) -> Path
```

定义类型：function；[源码第 157 行](C:/work/ls4t/base/slstr/slstr_data.py:157)。

无 docstring；算法解释见人工审阅章节。

### `unpack_archive`

```python
unpack_archive(archive: str | Path, output_directory: str | Path) -> Path
```

定义类型：function；[源码第 172 行](C:/work/ls4t/base/slstr/slstr_data.py:172)。

Unpack one SLSTR archive without overwriting an existing directory.

同名测试引用：[tests/test_slstr_products.py:14](C:/work/ls4t/tests/test_slstr_products.py:14)

### `_read_netcdf`

```python
_read_netcdf(path: Path, variable_name: str) -> np.ndarray
```

定义类型：function；[源码第 200 行](C:/work/ls4t/base/slstr/slstr_data.py:200)。

无 docstring；算法解释见人工审阅章节。

### `_resize_nearest`

```python
_resize_nearest(value: np.ndarray, shape: tuple[int, int]) -> np.ndarray
```

定义类型：function；[源码第 218 行](C:/work/ls4t/base/slstr/slstr_data.py:218)。

无 docstring；算法解释见人工审阅章节。

### `_utc_timestamp`

```python
_utc_timestamp(value: str) -> str
```

定义类型：function；[源码第 229 行](C:/work/ls4t/base/slstr/slstr_data.py:229)。

无 docstring；算法解释见人工审阅章节。

### `_coverage_from_name`

```python
_coverage_from_name(name: str) -> tuple[str | None, str | None]
```

定义类型：function；[源码第 234 行](C:/work/ls4t/base/slstr/slstr_data.py:234)。

无 docstring；算法解释见人工审阅章节。

### `extract_native_product`

```python
extract_native_product(product_directory: str | Path, *, view: str='nadir') -> SlstrExtractedProduct
```

定义类型：function；[源码第 241 行](C:/work/ls4t/base/slstr/slstr_data.py:241)。

Read native SLSTR arrays without reconstructing them to one grid.

### `reconstruct_product`

```python
reconstruct_product(item: SlstrExtractedProduct) -> SlstrDataProduct
```

定义类型：function；[源码第 289 行](C:/work/ls4t/base/slstr/slstr_data.py:289)。

Align geolocation, cloud and tie-point geometry to the thermal grid.

同名测试引用：[tests/test_flat_structure.py:34](C:/work/ls4t/tests/test_flat_structure.py:34)

### `read_native_product`

```python
read_native_product(product_directory: str | Path, *, view: str='nadir') -> SlstrDataProduct
```

定义类型：function；[源码第 310 行](C:/work/ls4t/base/slstr/slstr_data.py:310)。

Compatibility helper for one product; batch jobs use separate stages.

同名测试引用：[tests/test_dual_thermal_sensors.py:11](C:/work/ls4t/tests/test_dual_thermal_sensors.py:11)

### `add_lst_auxiliary`

```python
add_lst_auxiliary(item: SlstrDataProduct, auxiliary_file: str | Path) -> SlstrDataProduct
```

定义类型：function；[源码第 316 行](C:/work/ls4t/base/slstr/slstr_data.py:316)。

Attach grid-aligned emissivity, LAI and TCWV arrays to SLSTR-DATA.

同名测试引用：[tests/test_slstr_products.py:11](C:/work/ls4t/tests/test_slstr_products.py:11)

### `_gdal`

```python
_gdal()
```

定义类型：function；[源码第 329 行](C:/work/ls4t/base/slstr/slstr_data.py:329)。

无 docstring；算法解释见人工审阅章节。

### `_write_tiff`

```python
_write_tiff(path: str | Path, fields: dict[str, np.ndarray], metadata: dict[str, str], reference_path: str | Path | None=None) -> None
```

定义类型：function；[源码第 340 行](C:/work/ls4t/base/slstr/slstr_data.py:340)。

无 docstring；算法解释见人工审阅章节。

### `_read_tiff`

```python
_read_tiff(path: str | Path, default_field: str | None=None) -> tuple[dict[str, np.ndarray], dict[str, str]]
```

定义类型：function；[源码第 403 行](C:/work/ls4t/base/slstr/slstr_data.py:403)。

无 docstring；算法解释见人工审阅章节。

### `_metadata`

```python
_metadata(schema: str, **values: object) -> dict[str, str]
```

定义类型：function；[源码第 430 行](C:/work/ls4t/base/slstr/slstr_data.py:430)。

无 docstring；算法解释见人工审阅章节。

### `write_auxiliary_product`

```python
write_auxiliary_product(path: str | Path, fields: dict[str, np.ndarray]) -> None
```

定义类型：function；[源码第 437 行](C:/work/ls4t/base/slstr/slstr_data.py:437)。

Write the six LST auxiliary fields as a named-band GeoTIFF.

同名测试引用：[tests/test_slstr_products.py:15](C:/work/ls4t/tests/test_slstr_products.py:15)

### `read_auxiliary_product`

```python
read_auxiliary_product(path: str | Path, shape: tuple[int, int] | None=None) -> dict[str, np.ndarray]
```

定义类型：function；[源码第 450 行](C:/work/ls4t/base/slstr/slstr_data.py:450)。

Read named LST auxiliary fields from a GeoTIFF.

### `write_lsct_input`

```python
write_lsct_input(path: str | Path, observed_radiance: np.ndarray, effective_weights: np.ndarray, *, observation_uncertainty: np.ndarray | None=None, latitude_deg: np.ndarray | None=None, longitude_deg: np.ndarray | None=None, metadata: dict[str, object] | None=None) -> None
```

定义类型：function；[源码第 481 行](C:/work/ls4t/base/slstr/slstr_data.py:481)。

Write multidimensional LSCT input as a named-band GeoTIFF.

### `read_lsct_input`

```python
read_lsct_input(path: str | Path) -> dict[str, np.ndarray | dict[str, object]]
```

定义类型：function；[源码第 531 行](C:/work/ls4t/base/slstr/slstr_data.py:531)。

Read named-band multidimensional LSCT input from GeoTIFF.

### `read_lsct_input.stack`

```python
read_lsct_input.stack(prefix: str, shape: tuple[int, ...]) -> np.ndarray
```

定义类型：nested；[源码第 542 行](C:/work/ls4t/base/slstr/slstr_data.py:542)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:37](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:37)、[tests/test_tsharp.py:82](C:/work/ls4t/tests/test_tsharp.py:82)

### `write_extracted_product`

```python
write_extracted_product(path: str | Path, item: SlstrExtractedProduct) -> None
```

定义类型：function；[源码第 564 行](C:/work/ls4t/base/slstr/slstr_data.py:564)。

Store extraction fields as individual GeoTIFF files in one view directory.

### `read_extracted_product`

```python
read_extracted_product(path: str | Path) -> SlstrExtractedProduct
```

定义类型：function；[源码第 589 行](C:/work/ls4t/base/slstr/slstr_data.py:589)。

Load one extraction-stage view directory.

### `write_data_product`

```python
write_data_product(path: str | Path, item: SlstrDataProduct, *, reference_path: str | Path | None=None) -> None
```

定义类型：function；[源码第 639 行](C:/work/ls4t/base/slstr/slstr_data.py:639)。

Store an SLSTR-DATA product as a named-band GeoTIFF.

同名测试引用：[tests/test_dual_thermal_sensors.py:12](C:/work/ls4t/tests/test_dual_thermal_sensors.py:12)、[tests/test_slstr_products.py:16](C:/work/ls4t/tests/test_slstr_products.py:16)

### `read_data_product`

```python
read_data_product(path: str | Path) -> SlstrDataProduct
```

定义类型：function；[源码第 680 行](C:/work/ls4t/base/slstr/slstr_data.py:680)。

Load and validate an SLSTR-DATA GeoTIFF.

同名测试引用：[tests/test_dual_thermal_sensors.py:10](C:/work/ls4t/tests/test_dual_thermal_sensors.py:10)、[tests/test_slstr_products.py:12](C:/work/ls4t/tests/test_slstr_products.py:12)

### `write_lst_product`

```python
write_lst_product(path: str | Path, product, *, reference_path: str | Path | None=None) -> None
```

定义类型：function；[源码第 716 行](C:/work/ls4t/base/slstr/slstr_data.py:716)。

Store an SLSTR LST product as a named-band GeoTIFF.

### `read_lst_product`

```python
read_lst_product(path: str | Path)
```

定义类型：function；[源码第 744 行](C:/work/ls4t/base/slstr/slstr_data.py:744)。

Load an SLSTR L2LST GeoTIFF.

同名测试引用：[tests/test_slstr_products.py:13](C:/work/ls4t/tests/test_slstr_products.py:13)

### `describe_data_product`

```python
describe_data_product(item: SlstrDataProduct) -> dict[str, object]
```

定义类型：function；[源码第 777 行](C:/work/ls4t/base/slstr/slstr_data.py:777)。

Return a concise status record for command-line inspection.

### `slstr_unzip`

```python
slstr_unzip(indir_zip=None, outdir_raw=None, years=None, overwrite=None, start_index=None) -> None
```

定义类型：function；[源码第 793 行](C:/work/ls4t/base/slstr/slstr_data.py:793)。

Compatibility wrapper for :mod:`slstr.slstr_unzip`.

同名测试引用：[tests/test_flat_structure.py:41](C:/work/ls4t/tests/test_flat_structure.py:41)

### `slstr_extract`

```python
slstr_extract(indir_raw=None, outdir_extract=None, years=None, views=None, overwrite=None) -> None
```

定义类型：function；[源码第 807 行](C:/work/ls4t/base/slstr/slstr_data.py:807)。

Compatibility wrapper for :mod:`slstr.slstr_extract`.

同名测试引用：[tests/test_flat_structure.py:36](C:/work/ls4t/tests/test_flat_structure.py:36)

### `slstr_reconstruct`

```python
slstr_reconstruct(indir_extract=None, outdir_reconstruct=None, years=None, overwrite=None) -> None
```

定义类型：function；[源码第 821 行](C:/work/ls4t/base/slstr/slstr_data.py:821)。

Compatibility wrapper for :mod:`slstr.slstr_reconstruct`.

同名测试引用：[tests/test_flat_structure.py:39](C:/work/ls4t/tests/test_flat_structure.py:39)

### `slstr_project`

```python
slstr_project(indir_reconstruct=None, outdir_project=None, target_grid_file=None, years=None, projection_chunk_size=None, cloud_fraction_threshold=None, overwrite=None) -> None
```

定义类型：function；[源码第 834 行](C:/work/ls4t/base/slstr/slstr_data.py:834)。

Compatibility wrapper for :mod:`slstr.slstr_project`.

同名测试引用：[tests/test_flat_structure.py:38](C:/work/ls4t/tests/test_flat_structure.py:38)

### `slstr_merge`

```python
slstr_merge(indir_project=None, outdir_merge=None, years=None, overwrite=None) -> None
```

定义类型：function；[源码第 858 行](C:/work/ls4t/base/slstr/slstr_data.py:858)。

Compatibility wrapper for :mod:`slstr.slstr_merge`.

同名测试引用：[tests/test_flat_structure.py:37](C:/work/ls4t/tests/test_flat_structure.py:37)、[tests/test_slstr_products.py:19](C:/work/ls4t/tests/test_slstr_products.py:19)

## base/slstr/slstr_extract.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_extract.py)；57 行，2 个定义。

### `_year_directory`

```python
_year_directory(root, template, year)
```

定义类型：function；[源码第 19 行](C:/work/ls4t/base/slstr/slstr_extract.py:19)。

无 docstring；算法解释见人工审阅章节。

### `slstr_extract`

```python
slstr_extract(indir_raw=None, outdir_extract=None, years=None, views=None, overwrite=None) -> None
```

定义类型：function；[源码第 23 行](C:/work/ls4t/base/slstr/slstr_extract.py:23)。

Read SEN3 products and save native arrays without grid reconstruction.

同名测试引用：[tests/test_flat_structure.py:36](C:/work/ls4t/tests/test_flat_structure.py:36)

## base/slstr/slstr_grid.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_grid.py)；47 行，0 个定义。

## base/slstr/slstr_lsct.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_lsct.py)；154 行，2 个定义。

### `retrieve_slstr_lsct`

```python
retrieve_slstr_lsct(input_path, output_path, wavelength_um=None, component_names=None, window_size=None, ridge=None, max_condition_number=None, grid_id=None, algorithm_version=None) -> None
```

定义类型：function；[源码第 35 行](C:/work/ls4t/base/slstr/slstr_lsct.py:35)。

反演一个准备好的多角度 SLSTR LSCT 输入文件。

### `slstr_lsct`

```python
slstr_lsct(indir_lsct_input=None, outdir_lsct=None, years=None, overwrite=None) -> None
```

定义类型：function；[源码第 119 行](C:/work/ls4t/base/slstr/slstr_lsct.py:119)。

按年份批量反演 SLSTR 组分温度。

## base/slstr/slstr_lst.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_lst.py)；207 行，4 个定义。

### `import_legacy_coefficients`

```python
import_legacy_coefficients(table_path: str | Path, output_path: str | Path, *, version: str) -> None
```

定义类型：function；[源码第 42 行](C:/work/ls4t/base/slstr/slstr_lst.py:42)。

Convert the reviewed 15-column SLSTR table into a versioned model.

### `retrieve_slstr_lst`

```python
retrieve_slstr_lst(item: SlstrDataProduct, coefficient_file=None) -> SplitWindowResult
```

定义类型：function；[源码第 60 行](C:/work/ls4t/base/slstr/slstr_lst.py:60)。

Run the SLSTR split-window algorithm on a complete SLSTR-DATA product.

### `produce_slstr_lst`

```python
produce_slstr_lst(input_path: str | Path, output_path: str | Path, coefficient_file=None, auxiliary_file=None, *, grid_id: str, algorithm_version: str, uncertainty_k: float, start_time: str | None=None, end_time: str | None=None) -> None
```

定义类型：function；[源码第 83 行](C:/work/ls4t/base/slstr/slstr_lst.py:83)。

Produce one validated LS4T SLSTR L2LST product.

同名测试引用：[tests/test_slstr_products.py:18](C:/work/ls4t/tests/test_slstr_products.py:18)

### `slstr_lst`

```python
slstr_lst(indir_data=None, outdir_lst=None, coefficient_file=None, auxiliary_file=None, years=None, grid_id=None, algorithm_version=None, uncertainty_k=None, overwrite=None, input_year_template=None) -> None
```

定义类型：function；[源码第 144 行](C:/work/ls4t/base/slstr/slstr_lst.py:144)。

按年份处理重建后的 SLSTR-DATA 文件。

同名测试引用：[tests/test_slstr_products.py:18](C:/work/ls4t/tests/test_slstr_products.py:18)

## base/slstr/slstr_merge.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_merge.py)；64 行，3 个定义。

### `_year_directory`

```python
_year_directory(root, template, year)
```

定义类型：function；[源码第 19 行](C:/work/ls4t/base/slstr/slstr_merge.py:19)。

无 docstring；算法解释见人工审阅章节。

### `_merge_products`

```python
_merge_products(items)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/base/slstr/slstr_merge.py:23)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:19](C:/work/ls4t/tests/test_slstr_products.py:19)

### `slstr_merge`

```python
slstr_merge(indir_project=None, outdir_merge=None, years=None, overwrite=None) -> None
```

定义类型：function；[源码第 29 行](C:/work/ls4t/base/slstr/slstr_merge.py:29)。

Merge projected scenes by day and view.

同名测试引用：[tests/test_flat_structure.py:37](C:/work/ls4t/tests/test_flat_structure.py:37)、[tests/test_slstr_products.py:19](C:/work/ls4t/tests/test_slstr_products.py:19)

## base/slstr/slstr_project.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_project.py)；183 行，5 个定义。

### `_year_directory`

```python
_year_directory(root, template, year)
```

定义类型：function；[源码第 24 行](C:/work/ls4t/base/slstr/slstr_project.py:24)。

无 docstring；算法解释见人工审阅章节。

### `_target_grid_indices`

```python
_target_grid_indices(item, target_grid_file, projection_chunk_size)
```

定义类型：function；[源码第 28 行](C:/work/ls4t/base/slstr/slstr_project.py:28)。

Return target row/column indices for valid source longitude/latitude.

### `_project_field`

```python
_project_field(values, row, column, target_shape)
```

定义类型：function；[源码第 78 行](C:/work/ls4t/base/slstr/slstr_project.py:78)。

无 docstring；算法解释见人工审阅章节。

### `project_product`

```python
project_product(item, target_grid_file, projection_chunk_size=None, cloud_fraction_threshold=None) -> SlstrDataProduct
```

定义类型：function；[源码第 90 行](C:/work/ls4t/base/slstr/slstr_project.py:90)。

Project one reconstructed product to the target raster grid.

### `slstr_project`

```python
slstr_project(indir_reconstruct=None, outdir_project=None, target_grid_file=None, years=None, projection_chunk_size=None, cloud_fraction_threshold=None, overwrite=None) -> None
```

定义类型：function；[源码第 131 行](C:/work/ls4t/base/slstr/slstr_project.py:131)。

Project reconstructed products to the selected target grid.

同名测试引用：[tests/test_flat_structure.py:38](C:/work/ls4t/tests/test_flat_structure.py:38)

## base/slstr/slstr_reconstruct.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_reconstruct.py)；58 行，2 个定义。

### `_year_directory`

```python
_year_directory(root, template, year)
```

定义类型：function；[源码第 18 行](C:/work/ls4t/base/slstr/slstr_reconstruct.py:18)。

无 docstring；算法解释见人工审阅章节。

### `slstr_reconstruct`

```python
slstr_reconstruct(indir_extract=None, outdir_reconstruct=None, years=None, overwrite=None) -> None
```

定义类型：function；[源码第 22 行](C:/work/ls4t/base/slstr/slstr_reconstruct.py:22)。

Align extracted tie-point fields to each product's thermal grid.

同名测试引用：[tests/test_flat_structure.py:39](C:/work/ls4t/tests/test_flat_structure.py:39)

## base/slstr/slstr_region.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_region.py)；85 行，3 个定义。

### `_resolve_inputs`

```python
_resolve_inputs(value)
```

定义类型：function；[源码第 32 行](C:/work/ls4t/base/slstr/slstr_region.py:32)。

无 docstring；算法解释见人工审阅章节。

### `slstr_data_region`

```python
slstr_data_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 44 行](C:/work/ls4t/base/slstr/slstr_region.py:44)。

Mode 1: form one study-area data product before retrieval.

同名测试引用：[tests/test_flat_structure.py:40](C:/work/ls4t/tests/test_flat_structure.py:40)

### `slstr_result_region`

```python
slstr_result_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 67 行](C:/work/ls4t/base/slstr/slstr_region.py:67)。

Mode 2: form one study-area result after scene-by-scene retrieval.

同名测试引用：[tests/test_flat_structure.py:40](C:/work/ls4t/tests/test_flat_structure.py:40)

## base/slstr/slstr_scene_skip.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_scene_skip.py)；45 行，2 个定义。

### `load_scene_skip`

```python
load_scene_skip(root: Path, year: int) -> dict[str, set[str]]
```

定义类型：function；[源码第 19 行](C:/work/ls4t/base/slstr/slstr_scene_skip.py:19)。

``{scene: {views that cannot contribute}}`` from the coverage audit.  A missing or unreadable list is not an error: the callers then behave exactly as before.

### `is_useless`

```python
is_useless(skip: dict[str, set[str]], scene: str, views: tuple[str, ...]) -> bool
```

定义类型：function；[源码第 42 行](C:/work/ls4t/base/slstr/slstr_scene_skip.py:42)。

True when every view this stage needs is on the useless list.

## base/slstr/slstr_unzip.py

源码：[打开文件](C:/work/ls4t/base/slstr/slstr_unzip.py)；66 行，2 个定义。

### `_year_directory`

```python
_year_directory(root, template, year)
```

定义类型：function；[源码第 24 行](C:/work/ls4t/base/slstr/slstr_unzip.py:24)。

无 docstring；算法解释见人工审阅章节。

### `slstr_unzip`

```python
slstr_unzip(indir_zip=None, outdir_raw=None, years=None, overwrite=None, start_index=None) -> None
```

定义类型：function；[源码第 28 行](C:/work/ls4t/base/slstr/slstr_unzip.py:28)。

Unpack all SLSTR ZIP files in the selected yearly directories.

同名测试引用：[tests/test_flat_structure.py:41](C:/work/ls4t/tests/test_flat_structure.py:41)

## base/spatial.py

源码：[打开文件](C:/work/ls4t/base/spatial.py)；554 行，18 个定义。

### `bounds_mask`

```python
bounds_mask(latitude, longitude, bounds: Bounds) -> np.ndarray
```

定义类型：function；[源码第 24 行](C:/work/ls4t/base/spatial.py:24)。

Return pixels inside ``(west, south, east, north)`` lon/lat bounds.

### `study_area_window`

```python
study_area_window(latitude, longitude, bounds: Bounds)
```

定义类型：function；[源码第 50 行](C:/work/ls4t/base/spatial.py:50)。

Return a minimal rectangular window and its exact in-bounds mask.

### `_array_fields`

```python
_array_fields(item)
```

定义类型：function；[源码第 62 行](C:/work/ls4t/base/spatial.py:62)。

无 docstring；算法解释见人工审阅章节。

### `crop_observation`

```python
crop_observation(item, bounds: Bounds)
```

定义类型：function；[源码第 72 行](C:/work/ls4t/base/spatial.py:72)。

Crop an AATSR, SLSTR, or MSG data product to lon/lat bounds.

同名测试引用：[tests/test_spatial_modes.py:7](C:/work/ls4t/tests/test_spatial_modes.py:7)

### `_pick`

```python
_pick(stack: np.ndarray, selected: np.ndarray) -> np.ndarray
```

定义类型：function；[源码第 93 行](C:/work/ls4t/base/spatial.py:93)。

无 docstring；算法解释见人工审阅章节。

### `_first_finite`

```python
_first_finite(stack: np.ndarray) -> np.ndarray
```

定义类型：function；[源码第 97 行](C:/work/ls4t/base/spatial.py:97)。

无 docstring；算法解释见人工审阅章节。

### `mosaic_observations`

```python
mosaic_observations(items: Iterable[object], primary_field: str, angle_field: str='view_zenith_deg')
```

定义类型：function；[源码第 105 行](C:/work/ls4t/base/spatial.py:105)。

Mosaic same-grid decoded scenes, preferring clear low-view-angle pixels.

同名测试引用：[tests/test_spatial_modes.py:9](C:/work/ls4t/tests/test_spatial_modes.py:9)

### `target_grid_indices`

```python
target_grid_indices(longitude, latitude, target_grid_file: str | Path, chunk_size: int=100000)
```

定义类型：function；[源码第 178 行](C:/work/ls4t/base/spatial.py:178)。

Map source longitude/latitude to row/column indices of a GDAL raster.

### `_project_field`

```python
_project_field(values, row, column, target_shape)
```

定义类型：function；[源码第 235 行](C:/work/ls4t/base/spatial.py:235)。

无 docstring；算法解释见人工审阅章节。

### `project_observation`

```python
project_observation(item, target_grid_file: str | Path, chunk_size: int=100000, cloud_fraction_threshold: float=0.0)
```

定义类型：function；[源码第 253 行](C:/work/ls4t/base/spatial.py:253)。

Project every same-shape array in a decoded observation product.

### `crop_temperature_product`

```python
crop_temperature_product(product: TemperatureProduct, bounds: Bounds) -> TemperatureProduct
```

定义类型：function；[源码第 293 行](C:/work/ls4t/base/spatial.py:293)。

Crop an LST/LSCT result carrying latitude and longitude variables.

同名测试引用：[tests/test_spatial_modes.py:8](C:/work/ls4t/tests/test_spatial_modes.py:8)

### `mosaic_temperature_products`

```python
mosaic_temperature_products(products: Iterable[TemperatureProduct]) -> TemperatureProduct
```

定义类型：function；[源码第 325 行](C:/work/ls4t/base/spatial.py:325)。

Mosaic same-grid scene results, selecting the best valid overlap pixel.

同名测试引用：[tests/test_spatial_modes.py:10](C:/work/ls4t/tests/test_spatial_modes.py:10)

### `resize_data`

```python
resize_data(preArray, nl, ns, method='cv2.INTER_NEAREST')
```

定义类型：function；[源码第 452 行](C:/work/ls4t/base/spatial.py:452)。

数组的缩放，用到了cv2库，方法主要有： ‘最邻近‘cv2.INTER_NEAREST，‘双线性插值’cv2.INTER_LINEAR，‘三次立方’cv2.INTER_CUBIC，’等面积’cv2.INTER_AREA :param preArray: 原有数组 :param nl: 目标行数 :param ns: 目标列数 :param method:  缩放方法,默认是双线性插值 :return: 返回缩放后的数组

同名测试引用：[tests/test_msg_case_dependencies.py:92](C:/work/ls4t/tests/test_msg_case_dependencies.py:92)、[tests/test_slstr_case_dependencies.py:113](C:/work/ls4t/tests/test_slstr_case_dependencies.py:113)

### `geo2lonlat`

```python
geo2lonlat(dataset, x, y)
```

定义类型：function；[源码第 468 行](C:/work/ls4t/base/spatial.py:468)。

将投影坐标转为经纬度坐标（具体的投影坐标系由给定数据确定） :param dataset: GDAL地理数据 :param x: 投影坐标x :param y: 投影坐标y :return: 投影坐标(x, y)对应的经纬度坐标(lon, lat)

### `lonlat2geo`

```python
lonlat2geo(dataset, lat, lon)
```

定义类型：function；[源码第 486 行](C:/work/ls4t/base/spatial.py:486)。

将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定），尤其注意，不同版本经度和纬度是反的 :param dataset: GDAL地理数据 :param lon: 地理坐标lon经度 :param lat: 地理坐标lat纬度 :return: 经纬度坐标(lon, lat)对应的投影坐标

### `geo2imagexy`

```python
geo2imagexy(dataset, x, y)
```

定义类型：function；[源码第 507 行](C:/work/ls4t/base/spatial.py:507)。

根据GDAL的六 参数模型将给定的投影或地理坐标转为影像图上坐标（行列号） :param dataset: GDAL地理数据 :param x: 投影或地理坐标x :param y: 投影或地理坐标y :return: 影坐标或地理坐标(x, y)对应的影像图上行列号(row, col) nl ns

### `imagexy2geo`

```python
imagexy2geo(dataset, row, col)
```

定义类型：function；[源码第 521 行](C:/work/ls4t/base/spatial.py:521)。

根据GDAL的六参数模型将影像图上坐标（行列号）转为投影坐标或地理坐标（根据具体数据的坐标系统转换） :param dataset: GDAL地理数据 :param row: 像素的行号 :param col: 像素的列号 :return: 行列号(row, col)对应的投影坐标或地理坐标(x, y)

### `loc2map`

```python
loc2map(lat, lon, dataset)
```

定义类型：function；[源码第 535 行](C:/work/ls4t/base/spatial.py:535)。

经纬度转图上行列号 :param lat: 纬度 :param lon: 经度 :param dataset: 数据集，提供了地理和投影信息 :return: 行列号

同名测试引用：[tests/test_msg_case_dependencies.py:92](C:/work/ls4t/tests/test_msg_case_dependencies.py:92)

## base/stream_era5.py

源码：[打开文件](C:/work/ls4t/base/stream_era5.py)；168 行，8 个定义。

### `forcing_day`

```python
forcing_day(output_root: Path, day: date) -> Path
```

定义类型：function；[源码第 29 行](C:/work/ls4t/base/stream_era5.py:29)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_stream_era5.py:12](C:/work/ls4t/tests/test_stream_era5.py:12)

### `_variable`

```python
_variable(dataset, name: str, first: int, last: int) -> np.ndarray
```

定义类型：function；[源码第 33 行](C:/work/ls4t/base/stream_era5.py:33)。

无 docstring；算法解释见人工审阅章节。

### `_orient`

```python
_orient(data: np.ndarray, longitude_order: str) -> np.ndarray
```

定义类型：function；[源码第 42 行](C:/work/ls4t/base/stream_era5.py:42)。

无 docstring；算法解释见人工审阅章节。

### `_write_h5`

```python
_write_h5(path: Path, data: np.ndarray, longitude_order: str) -> None
```

定义类型：function；[源码第 52 行](C:/work/ls4t/base/stream_era5.py:52)。

无 docstring；算法解释见人工审阅章节。

### `_validate_month`

```python
_validate_month(instant, accumulated, year: int, month: int, longitude_order: str) -> tuple[int, int]
```

定义类型：function；[源码第 59 行](C:/work/ls4t/base/stream_era5.py:59)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_stream_era5.py:12](C:/work/ls4t/tests/test_stream_era5.py:12)

### `_write_day`

```python
_write_day(instant, accumulated, output_root: Path, day: date, longitude_order: str) -> Path
```

定义类型：function；[源码第 85 行](C:/work/ls4t/base/stream_era5.py:85)。

无 docstring；算法解释见人工审阅章节。

### `extract_month`

```python
extract_month(source: Path, output_root: Path, year: int, month: int, *, accumulated_source: Path | None=None, longitude_order: str='0-360') -> list[Path]
```

定义类型：function；[源码第 116 行](C:/work/ls4t/base/stream_era5.py:116)。

Read a single monthly NetCDF, or split instant/accumulation files.

同名测试引用：[tests/test_stream_era5.py:12](C:/work/ls4t/tests/test_stream_era5.py:12)

### `check_day`

```python
check_day(output_root: Path, day: date) -> list[str]
```

定义类型：function；[源码第 140 行](C:/work/ls4t/base/stream_era5.py:140)。

Return missing/corrupt forcing-file names; never modify the output.

同名测试引用：[tests/test_stream_era5.py:12](C:/work/ls4t/tests/test_stream_era5.py:12)

## base/templates/audit_cases.py

源码：[打开文件](C:/work/ls4t/base/templates/audit_cases.py)；81 行，2 个定义。

### `load`

```python
load(path: Path) -> dict
```

定义类型：function；[源码第 16 行](C:/work/ls4t/base/templates/audit_cases.py:16)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization.py:97](C:/work/ls4t/tests/test_normalization.py:97)、[tests/test_standalone_cases.py:43](C:/work/ls4t/tests/test_standalone_cases.py:43)

### `main`

```python
main() -> None
```

定义类型：function；[源码第 21 行](C:/work/ls4t/base/templates/audit_cases.py:21)。

无 docstring；算法解释见人工审阅章节。

## base/templates/case/run_standard_stage.py

源码：[打开文件](C:/work/ls4t/base/templates/case/run_standard_stage.py)；164 行，5 个定义。

### `find_repository_root`

```python
find_repository_root(start: Path) -> Path
```

定义类型：function；[源码第 16 行](C:/work/ls4t/base/templates/case/run_standard_stage.py:16)。

无 docstring；算法解释见人工审阅章节。

### `load_toml`

```python
load_toml(path: Path) -> dict
```

定义类型：function；[源码第 101 行](C:/work/ls4t/base/templates/case/run_standard_stage.py:101)。

无 docstring；算法解释见人工审阅章节。

### `parse_args`

```python
parse_args() -> argparse.Namespace
```

定义类型：function；[源码第 108 行](C:/work/ls4t/base/templates/case/run_standard_stage.py:108)。

无 docstring；算法解释见人工审阅章节。

### `stage_arguments`

```python
stage_arguments(function, case: dict, machine: dict) -> dict
```

定义类型：function；[源码第 116 行](C:/work/ls4t/base/templates/case/run_standard_stage.py:116)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 142 行](C:/work/ls4t/base/templates/case/run_standard_stage.py:142)。

无 docstring；算法解释见人工审阅章节。

## base/templates/new_case.py

源码：[打开文件](C:/work/ls4t/base/templates/new_case.py)；78 行，3 个定义。

### `parse_args`

```python
parse_args() -> argparse.Namespace
```

定义类型：function；[源码第 20 行](C:/work/ls4t/base/templates/new_case.py:20)。

无 docstring；算法解释见人工审阅章节。

### `validate_slug`

```python
validate_slug(name: str, value: str) -> None
```

定义类型：function；[源码第 40 行](C:/work/ls4t/base/templates/new_case.py:40)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 45 行](C:/work/ls4t/base/templates/new_case.py:45)。

无 docstring；算法解释见人工审阅章节。

## base/templates/references/components/run.py

源码：[打开文件](C:/work/ls4t/base/templates/references/components/run.py)；334 行，13 个定义。

### `new_flags`

```python
new_flags(shape: tuple[int, ...]) -> np.ndarray
```

定义类型：function；[源码第 46 行](C:/work/ls4t/base/templates/references/components/run.py:46)。

无 docstring；算法解释见人工审阅章节。

### `set_flag`

```python
set_flag(flags: np.ndarray, mask: np.ndarray, flag: QualityFlag) -> None
```

定义类型：function；[源码第 51 行](C:/work/ls4t/base/templates/references/components/run.py:51)。

无 docstring；算法解释见人工审阅章节。

### `usable`

```python
usable(flags: np.ndarray, reject: QualityFlag=INVALID_FLAGS) -> np.ndarray
```

定义类型：function；[源码第 56 行](C:/work/ls4t/base/templates/references/components/run.py:56)。

无 docstring；算法解释见人工审阅章节。

### `planck_radiance`

```python
planck_radiance(wavelength_um: float, temperature_k: np.ndarray | float) -> np.ndarray
```

定义类型：function；[源码第 69 行](C:/work/ls4t/base/templates/references/components/run.py:69)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_physics.py:3](C:/work/ls4t/tests/test_physics.py:3)、[tests/test_retrieval.py:7](C:/work/ls4t/tests/test_retrieval.py:7)

### `inverse_planck`

```python
inverse_planck(wavelength_um: float, radiance: np.ndarray | float) -> np.ndarray
```

定义类型：function；[源码第 82 行](C:/work/ls4t/base/templates/references/components/run.py:82)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:48](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:48)、[tests/test_physics.py:3](C:/work/ls4t/tests/test_physics.py:3)

### `retrieve_components`

```python
retrieve_components(observed_radiance: np.ndarray, effective_weights: np.ndarray, wavelength_um: float, *, observation_uncertainty: np.ndarray | None=None, ridge: float=0.0, max_condition_number: float=1000000.0, valid_temperature_range_k: tuple[float, float]=(200.0, 380.0)) -> ComponentRetrievalResult
```

定义类型：function；[源码第 105 行](C:/work/ls4t/base/templates/references/components/run.py:105)。

Solve ``weights @ component_radiance = observed_radiance`` per pixel.  The last radiance axis is observation/angle and the final weights axes are ``(observation, component)``. Invalid observations are omitted per pixel.

同名测试引用：[tests/test_msg_aatsr_comparison.py:24](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:24)、[tests/test_retrieval.py:4](C:/work/ls4t/tests/test_retrieval.py:4)

### `retrieve_components_window`

```python
retrieve_components_window(observed_radiance: np.ndarray, effective_weights: np.ndarray, wavelength_um: float, *, window_size: int=5, observation_uncertainty: np.ndarray | None=None, ridge: float=0.0, max_condition_number: float=1000000.0, valid_temperature_range_k: tuple[float, float]=(200.0, 380.0)) -> ComponentRetrievalResult
```

定义类型：function；[源码第 195 行](C:/work/ls4t/base/templates/references/components/run.py:195)。

Window LSCT for cases with fewer angles than components.  Component radiances are assumed locally constant inside each moving window, while effective-emissivity weights may vary by pixel and angle. This is the production baseline corresponding to the legacy 5x

同名测试引用：[tests/test_retrieval.py:4](C:/work/ls4t/tests/test_retrieval.py:4)

### `validate_storage`

```python
validate_storage()
```

定义类型：function；[源码第 265 行](C:/work/ls4t/base/templates/references/components/run.py:265)。

无 docstring；算法解释见人工审阅章节。

### `validate_storage.overlap`

```python
validate_storage.overlap(left, right)
```

定义类型：nested；[源码第 275 行](C:/work/ls4t/base/templates/references/components/run.py:275)。

无 docstring；算法解释见人工审阅章节。

### `inputs`

```python
inputs()
```

定义类型：function；[源码第 283 行](C:/work/ls4t/base/templates/references/components/run.py:283)。

无 docstring；算法解释见人工审阅章节。

### `save_result`

```python
save_result(name, source, **arrays)
```

定义类型：function；[源码第 305 行](C:/work/ls4t/base/templates/references/components/run.py:305)。

无 docstring；算法解释见人工审阅章节。

### `demo_input`

```python
demo_input()
```

定义类型：function；[源码第 315 行](C:/work/ls4t/base/templates/references/components/run.py:315)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_standalone_cases.py:69](C:/work/ls4t/tests/test_standalone_cases.py:69)

### `main`

```python
main()
```

定义类型：function；[源码第 321 行](C:/work/ls4t/base/templates/references/components/run.py:321)。

无 docstring；算法解释见人工审阅章节。

## base/templates/references/kernel_atc/run.py

源码：[打开文件](C:/work/ls4t/base/templates/references/kernel_atc/run.py)；802 行，44 个定义。

### `new_flags`

```python
new_flags(shape: tuple[int, ...]) -> np.ndarray
```

定义类型：function；[源码第 54 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:54)。

无 docstring；算法解释见人工审阅章节。

### `set_flag`

```python
set_flag(flags: np.ndarray, mask: np.ndarray, flag: QualityFlag) -> None
```

定义类型：function；[源码第 59 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:59)。

无 docstring；算法解释见人工审阅章节。

### `usable`

```python
usable(flags: np.ndarray, reject: QualityFlag=INVALID_FLAGS) -> np.ndarray
```

定义类型：function；[源码第 64 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:64)。

无 docstring；算法解释见人工审阅章节。

### `fit_linear`

```python
fit_linear(design, target, weights)
```

定义类型：function；[源码第 69 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:69)。

Require residual degrees of freedom and an identifiable weighted model.

### `quality_flags`

```python
quality_flags(values)
```

定义类型：function；[源码第 89 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:89)。

Never turn missing/fractional/out-of-range QA values into GOOD by casting.

### `kernel_Vin`

```python
kernel_Vin(vza)
```

定义类型：function；[源码第 97 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:97)。

Vinnikov emissivity :param vza: :return: Vin 核值

同名测试引用：[tests/test_kernel_models.py:15](C:/work/ls4t/tests/test_kernel_models.py:15)

### `kernel_LiDense`

```python
kernel_LiDense(vza, sza, raa, h=2, r=1, b=1)
```

定义类型：function；[源码第 108 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:108)。

:param vza: :param sza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:19](C:/work/ls4t/tests/test_kernel_models.py:19)

### `kernel_LiSparse`

```python
kernel_LiSparse(vza, sza, raa, h=2, r=1, b=1)
```

定义类型：function；[源码第 150 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:150)。

:param vza: :param sza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:19](C:/work/ls4t/tests/test_kernel_models.py:19)

### `kernel_Solar`

```python
kernel_Solar(vza, sza, raa)
```

定义类型：function；[源码第 193 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:193)。

vinnikov solar :param vza: :param sza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:20](C:/work/ls4t/tests/test_kernel_models.py:20)

### `kernel_RLf`

```python
kernel_RLf(vza, sza, raa)
```

定义类型：function；[源码第 218 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:218)。

Roujean hotspot angular distance function :param vza: :param sza: :param raa: :return:

同名测试引用：[tests/test_aatsr_case_dependencies.py:98](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:98)、[tests/test_kernel_models.py:20](C:/work/ls4t/tests/test_kernel_models.py:20)

### `kernel_LSF_analytical`

```python
kernel_LSF_analytical(vza)
```

定义类型：function；[源码第 234 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:234)。

一种LSF核的参数化方案 :param vza: 观测天顶角 :return: LSF核值

同名测试引用：[tests/test_kernel_models.py:16](C:/work/ls4t/tests/test_kernel_models.py:16)

### `kernel_LSF`

```python
kernel_LSF(vza)
```

定义类型：function；[源码第 247 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:247)。

LSF核的原始计算方法 :param vza: 观测天顶角 :return: LSF核

同名测试引用：[tests/test_aatsr_case_dependencies.py:68](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:68)、[tests/test_kernel_models.py:15](C:/work/ls4t/tests/test_kernel_models.py:15)

### `kernel_TLSF`

```python
kernel_TLSF(vza, w=0.1)
```

定义类型：function；[源码第 261 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:261)。

LSF核的原始计算方法 :param vza: 观测天顶角 :return: LSF核

同名测试引用：[tests/test_kernel_models.py:17](C:/work/ls4t/tests/test_kernel_models.py:17)

### `kernel_VLSF`

```python
kernel_VLSF(vza, w=0.15)
```

定义类型：function；[源码第 275 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:275)。

LSF核的原始计算方法 :param vza: 观测天顶角 :return: LSF核

同名测试引用：[tests/test_kernel_models.py:17](C:/work/ls4t/tests/test_kernel_models.py:17)

### `kernel_Thapke`

```python
kernel_Thapke(vza, w=0.1, K=1.0)
```

定义类型：function；[源码第 289 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:289)。

LSF核的原始计算方法 :param vza: 观测天顶角 :return: LSF核

同名测试引用：[tests/test_kernel_models.py:18](C:/work/ls4t/tests/test_kernel_models.py:18)

### `kernel_RossThick`

```python
kernel_RossThick(vza, sza, raa)
```

定义类型：function；[源码第 304 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:304)。

Ross 简化模型，用于多次散射项计算 :param sza: :param vza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:21](C:/work/ls4t/tests/test_kernel_models.py:21)

### `kernel_RossThin`

```python
kernel_RossThin(vza, sza, raa)
```

定义类型：function；[源码第 329 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:329)。

Ross 简化模型，用于多次散射项计算 :param sza: :param vza: :param raa: :return:

同名测试引用：[tests/test_kernel_models.py:21](C:/work/ls4t/tests/test_kernel_models.py:21)

### `available_kernels`

```python
available_kernels() -> dict
```

定义类型：function；[源码第 391 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:391)。

Return independent metadata dictionaries, safe for JSON configuration.

### `KernelTerm.__post_init__`

```python
KernelTerm.__post_init__(self)
```

定义类型：method；[源码第 403 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:403)。

无 docstring；算法解释见人工审阅章节。

### `evaluate_kernel`

```python
evaluate_kernel(term: KernelTerm | str, vza, sza, raa) -> np.ndarray
```

定义类型：function；[源码第 420 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:420)。

Evaluate one kernel without changing input arrays; preserve broadcast shape.

同名测试引用：[tests/test_kernel_models.py:29](C:/work/ls4t/tests/test_kernel_models.py:29)

### `KernelModel.__post_init__`

```python
KernelModel.__post_init__(self)
```

定义类型：method；[源码第 454 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:454)。

无 docstring；算法解释见人工审阅章节。

### `KernelModel.design_matrix`

```python
KernelModel.design_matrix(self, vza, sza, raa) -> np.ndarray
```

定义类型：method；[源码第 462 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:462)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:38](C:/work/ls4t/tests/test_kernel_models.py:38)

### `KernelModel.to_dict`

```python
KernelModel.to_dict(self) -> dict
```

定义类型：method；[源码第 465 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:465)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:52](C:/work/ls4t/tests/test_kernel_models.py:52)

### `KernelModel.from_dict`

```python
KernelModel.from_dict(cls, config: dict) -> KernelModel
```

定义类型：method；[源码第 469 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:469)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:52](C:/work/ls4t/tests/test_kernel_models.py:52)

### `kernel_model`

```python
kernel_model(preset: str) -> KernelModel
```

定义类型：function；[源码第 474 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:474)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:36](C:/work/ls4t/tests/test_kernel_models.py:36)

### `KernelFit.predict`

```python
KernelFit.predict(self, vza, sza, raa) -> np.ndarray
```

定义类型：method；[源码第 491 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:491)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:15](C:/work/ls4t/tests/test_annual_cycle.py:15)、[tests/test_kernel_models.py:80](C:/work/ls4t/tests/test_kernel_models.py:80)

### `KernelFit.normalize`

```python
KernelFit.normalize(self, temperature_k, vza, sza, raa, *, reference_vza=0.0, reference_sza=None, reference_raa=0.0) -> np.ndarray
```

定义类型：method；[源码第 494 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:494)。

Preserve the observed residual; default is nadir at the SAME solar angle.

同名测试引用：[tests/test_annual_cycle.py:16](C:/work/ls4t/tests/test_annual_cycle.py:16)、[tests/test_kernel_models.py:43](C:/work/ls4t/tests/test_kernel_models.py:43)

### `_replace_parameters`

```python
_replace_parameters(model, keys, values)
```

定义类型：function；[源码第 505 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:505)。

无 docstring；算法解释见人工审阅章节。

### `fit_kernel_model`

```python
fit_kernel_model(model: KernelModel, temperature_k, vza, sza, raa, *, weights=1.0, quality_flag=0, solver='linear', parameter_bounds=None, method='Powell', options=None) -> KernelFit
```

定义类型：function；[源码第 512 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:512)。

Fit ONE co-located/same-state angular sample set, not a mixed image/time pool.  Linear: all kernel shape parameters are fixed. Minimize: variable projection estimates ONLY named shape parameters (e.g. {'rl.k': (0.1, 3.)}); WLS solves coefficients at each evalu

同名测试引用：[tests/test_kernel_models.py:41](C:/work/ls4t/tests/test_kernel_models.py:41)

### `fit_kernel_model.objective`

```python
fit_kernel_model.objective(values)
```

定义类型：nested；[源码第 557 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:557)。

无 docstring；算法解释见人工审阅章节。

### `annual_phase`

```python
annual_phase(dates_or_doy, *, year_length=365) -> np.ndarray
```

定义类型：function；[源码第 594 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:594)。

Map dates or 1-based DOY to [0,1); invalid samples/NaT become NaN.  Datetime strings must be timezone-free (or already converted to the chosen local calendar); this function does not infer timezone/overpass time. Multi-year dates align by fraction of each actu

同名测试引用：[tests/test_annual_cycle.py:34](C:/work/ls4t/tests/test_annual_cycle.py:34)

### `_annual_design`

```python
_annual_design(phase, harmonics)
```

定义类型：function；[源码第 640 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:640)。

无 docstring；算法解释见人工审阅章节。

### `ATCFit.mean_k`

```python
ATCFit.mean_k(self) -> float
```

定义类型：method；[源码第 657 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:657)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:11](C:/work/ls4t/tests/test_annual_cycle.py:11)、[tests/test_multisource_normalization.py:42](C:/work/ls4t/tests/test_multisource_normalization.py:42)

### `ATCFit.amplitudes_k`

```python
ATCFit.amplitudes_k(self) -> np.ndarray
```

定义类型：method；[源码第 661 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:661)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:12](C:/work/ls4t/tests/test_annual_cycle.py:12)

### `ATCFit.peak_days`

```python
ATCFit.peak_days(self, year_length=365) -> np.ndarray
```

定义类型：method；[源码第 664 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:664)。

First peak of EACH harmonic in [1,1+N/j), not the combined-curve peak.  Undefined phase of a zero-amplitude harmonic returns NaN.

同名测试引用：[tests/test_annual_cycle.py:13](C:/work/ls4t/tests/test_annual_cycle.py:13)

### `ATCFit.predict`

```python
ATCFit.predict(self, dates_or_doy, *, year_length=365) -> np.ndarray
```

定义类型：method；[源码第 675 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:675)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:15](C:/work/ls4t/tests/test_annual_cycle.py:15)、[tests/test_kernel_models.py:80](C:/work/ls4t/tests/test_kernel_models.py:80)

### `ATCFit.normalize`

```python
ATCFit.normalize(self, temperature_k, dates_or_doy, *, reference, year_length=365, reference_year_length=365) -> np.ndarray
```

定义类型：method；[源码第 679 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:679)。

Shift season while retaining anomalies; NaN observations remain NaN.

同名测试引用：[tests/test_annual_cycle.py:16](C:/work/ls4t/tests/test_annual_cycle.py:16)、[tests/test_kernel_models.py:43](C:/work/ls4t/tests/test_kernel_models.py:43)

### `fit_annual_cycle`

```python
fit_annual_cycle(temperature_k, dates_or_doy, *, harmonics=1, year_length=365, weights=1.0, quality_flag=0, minimum_coverage=0.5) -> ATCFit
```

定义类型：function；[源码第 691 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:691)。

Fit one pixel/site at comparable solar time, geometry and spatial support.  harmonics=1 gives a standard three-coefficient ATC; 2 adds a half-year harmonic (five coefficients). Coverage is 1 minus the largest circular phase gap, after QA filtering. Repeated ye

同名测试引用：[tests/test_annual_cycle.py:10](C:/work/ls4t/tests/test_annual_cycle.py:10)

### `validate_storage`

```python
validate_storage()
```

定义类型：function；[源码第 722 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:722)。

无 docstring；算法解释见人工审阅章节。

### `validate_storage.overlap`

```python
validate_storage.overlap(left, right)
```

定义类型：nested；[源码第 732 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:732)。

无 docstring；算法解释见人工审阅章节。

### `inputs`

```python
inputs()
```

定义类型：function；[源码第 740 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:740)。

无 docstring；算法解释见人工审阅章节。

### `save_result`

```python
save_result(name, source, **arrays)
```

定义类型：function；[源码第 762 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:762)。

无 docstring；算法解释见人工审阅章节。

### `demo_input`

```python
demo_input()
```

定义类型：function；[源码第 772 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:772)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_standalone_cases.py:69](C:/work/ls4t/tests/test_standalone_cases.py:69)

### `main`

```python
main()
```

定义类型：function；[源码第 784 行](C:/work/ls4t/base/templates/references/kernel_atc/run.py:784)。

无 docstring；算法解释见人工审阅章节。

## base/templates/references/normalization/run.py

源码：[打开文件](C:/work/ls4t/base/templates/references/normalization/run.py)；432 行，20 个定义。

### `new_flags`

```python
new_flags(shape: tuple[int, ...]) -> np.ndarray
```

定义类型：function；[源码第 46 行](C:/work/ls4t/base/templates/references/normalization/run.py:46)。

无 docstring；算法解释见人工审阅章节。

### `set_flag`

```python
set_flag(flags: np.ndarray, mask: np.ndarray, flag: QualityFlag) -> None
```

定义类型：function；[源码第 51 行](C:/work/ls4t/base/templates/references/normalization/run.py:51)。

无 docstring；算法解释见人工审阅章节。

### `usable`

```python
usable(flags: np.ndarray, reject: QualityFlag=INVALID_FLAGS) -> np.ndarray
```

定义类型：function；[源码第 56 行](C:/work/ls4t/base/templates/references/normalization/run.py:56)。

无 docstring；算法解释见人工审阅章节。

### `fit_linear`

```python
fit_linear(design, target, weights)
```

定义类型：function；[源码第 61 行](C:/work/ls4t/base/templates/references/normalization/run.py:61)。

Require residual degrees of freedom and an identifiable weighted model.

### `quality_flags`

```python
quality_flags(values)
```

定义类型：function；[源码第 81 行](C:/work/ls4t/base/templates/references/normalization/run.py:81)。

Never turn missing/fractional/out-of-range QA values into GOOD by casting.

### `angular_basis`

```python
angular_basis(view_zenith_deg: np.ndarray | float, solar_zenith_deg: np.ndarray | float, relative_azimuth_deg: np.ndarray | float) -> np.ndarray
```

定义类型：function；[源码第 101 行](C:/work/ls4t/base/templates/references/normalization/run.py:101)。

无 docstring；算法解释见人工审阅章节。

### `normalize_directional`

```python
normalize_directional(temperature_k: np.ndarray, view_zenith_deg: np.ndarray, solar_zenith_deg: np.ndarray, relative_azimuth_deg: np.ndarray, coefficients_k: np.ndarray, *, reference_view_zenith_deg: float | None=None, reference_solar_zenith_deg: float | None=None, reference_relative_azimuth_deg: float | None=None) -> np.ndarray
```

定义类型：function；[源码第 122 行](C:/work/ls4t/base/templates/references/normalization/run.py:122)。

Move observed temperature to a common geometry using calibrated kernels.

同名测试引用：[tests/test_multisource_normalization.py:17](C:/work/ls4t/tests/test_multisource_normalization.py:17)、[tests/test_normalization.py:5](C:/work/ls4t/tests/test_normalization.py:5)

### `diurnal_anomaly`

```python
diurnal_anomaly(local_solar_time_hour: np.ndarray | float, amplitude_k: np.ndarray | float, peak_hour: np.ndarray | float) -> np.ndarray
```

定义类型：function；[源码第 163 行](C:/work/ls4t/base/templates/references/normalization/run.py:163)。

无 docstring；算法解释见人工审阅章节。

### `normalize_local_solar_time`

```python
normalize_local_solar_time(temperature_k: np.ndarray, local_solar_time_hour: np.ndarray, amplitude_k: np.ndarray, peak_hour: np.ndarray, *, reference_hour: float | None=None) -> np.ndarray
```

定义类型：function；[源码第 180 行](C:/work/ls4t/base/templates/references/normalization/run.py:180)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_multisource_normalization.py:47](C:/work/ls4t/tests/test_multisource_normalization.py:47)、[tests/test_normalization.py:10](C:/work/ls4t/tests/test_normalization.py:10)

### `tsharp_cover_fraction`

```python
tsharp_cover_fraction(ndvi) -> np.ndarray
```

定义类型：function；[源码第 214 行](C:/work/ls4t/base/templates/references/normalization/run.py:214)。

Agam simplified fractional cover: 1 - (1 - NDVI)**0.625.  NDVI is decoded, dimensionless and in [0,1]. Outside-domain values become NaN, never clipped into bare soil. Water/snow masks belong in the supplied quality flags; NDVI alone is not a water classifier. 

同名测试引用：[tests/test_tsharp.py:25](C:/work/ls4t/tests/test_tsharp.py:25)

### `downscale_temperature`

```python
downscale_temperature(coarse_temperature_k, fine_predictors, *, coarse_quality_flag=0, fine_quality_flag=0, fine_weights=None, minimum_coverage=1.0, method='linear') -> DownscaleResult
```

定义类型：function；[源码第 229 行](C:/work/ls4t/base/templates/references/normalization/run.py:229)。

Regress on coarse predictor means, predict fine LST, restore coarse means.  fine_predictors: (fine_rows, fine_cols[, features]); NaN marks no coverage. fine_weights: positive pixel areas, default equal areas. Coverage counts invalid predictor/quality pixels in

同名测试引用：[tests/test_multisource_normalization.py:85](C:/work/ls4t/tests/test_multisource_normalization.py:85)、[tests/test_tsharp.py:35](C:/work/ls4t/tests/test_tsharp.py:35)

### `downscale_temperature.sum_blocks`

```python
downscale_temperature.sum_blocks(values)
```

定义类型：nested；[源码第 279 行](C:/work/ls4t/base/templates/references/normalization/run.py:279)。

无 docstring；算法解释见人工审阅章节。

### `downscale_temperature.expand`

```python
downscale_temperature.expand(values)
```

定义类型：nested；[源码第 282 行](C:/work/ls4t/base/templates/references/normalization/run.py:282)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_tsharp.py:12](C:/work/ls4t/tests/test_tsharp.py:12)

### `downscale_tsharp`

```python
downscale_tsharp(coarse_temperature_k, fine_ndvi, *, coarse_quality_flag=0, fine_quality_flag=0, fine_weights=None, minimum_coverage=1.0) -> DownscaleResult
```

定义类型：function；[源码第 331 行](C:/work/ls4t/base/templates/references/normalization/run.py:331)。

TsHARP convenience entry; coefficients are [intercept_K, slope_K_per_fc].

同名测试引用：[tests/test_tsharp.py:51](C:/work/ls4t/tests/test_tsharp.py:51)

### `validate_storage`

```python
validate_storage()
```

定义类型：function；[源码第 343 行](C:/work/ls4t/base/templates/references/normalization/run.py:343)。

无 docstring；算法解释见人工审阅章节。

### `validate_storage.overlap`

```python
validate_storage.overlap(left, right)
```

定义类型：nested；[源码第 353 行](C:/work/ls4t/base/templates/references/normalization/run.py:353)。

无 docstring；算法解释见人工审阅章节。

### `inputs`

```python
inputs()
```

定义类型：function；[源码第 361 行](C:/work/ls4t/base/templates/references/normalization/run.py:361)。

无 docstring；算法解释见人工审阅章节。

### `save_result`

```python
save_result(name, source, **arrays)
```

定义类型：function；[源码第 383 行](C:/work/ls4t/base/templates/references/normalization/run.py:383)。

无 docstring；算法解释见人工审阅章节。

### `demo_input`

```python
demo_input()
```

定义类型：function；[源码第 393 行](C:/work/ls4t/base/templates/references/normalization/run.py:393)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_standalone_cases.py:69](C:/work/ls4t/tests/test_standalone_cases.py:69)

### `main`

```python
main()
```

定义类型：function；[源码第 407 行](C:/work/ls4t/base/templates/references/normalization/run.py:407)。

无 docstring；算法解释见人工审阅章节。

## base/viirs/__init__.py

源码：[打开文件](C:/work/ls4t/base/viirs/__init__.py)；1 行，0 个定义。

## base/viirs/viirs_data.py

源码：[打开文件](C:/work/ls4t/base/viirs/viirs_data.py)；43 行，4 个定义。

### `read_native_product`

```python
read_native_product(path)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/base/viirs/viirs_data.py:30)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:11](C:/work/ls4t/tests/test_dual_thermal_sensors.py:11)

### `write_data_product`

```python
write_data_product(path, item) -> None
```

定义类型：function；[源码第 34 行](C:/work/ls4t/base/viirs/viirs_data.py:34)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:12](C:/work/ls4t/tests/test_dual_thermal_sensors.py:12)、[tests/test_slstr_products.py:16](C:/work/ls4t/tests/test_slstr_products.py:16)

### `read_data_product`

```python
read_data_product(path)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/base/viirs/viirs_data.py:38)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:10](C:/work/ls4t/tests/test_dual_thermal_sensors.py:10)、[tests/test_slstr_products.py:12](C:/work/ls4t/tests/test_slstr_products.py:12)

### `add_lst_auxiliary`

```python
add_lst_auxiliary(item, auxiliary_file)
```

定义类型：function；[源码第 42 行](C:/work/ls4t/base/viirs/viirs_data.py:42)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_products.py:11](C:/work/ls4t/tests/test_slstr_products.py:11)

## base/viirs/viirs_extract.py

源码：[打开文件](C:/work/ls4t/base/viirs/viirs_extract.py)；24 行，1 个定义。

### `viirs_extract`

```python
viirs_extract(indir_raw=None, outdir_data=None, years=None, months=None, days=None, overwrite=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/viirs/viirs_extract.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:42](C:/work/ls4t/tests/test_flat_structure.py:42)

## base/viirs/viirs_lst.py

源码：[打开文件](C:/work/ls4t/base/viirs/viirs_lst.py)；44 行，3 个定义。

### `retrieve_viirs_lst`

```python
retrieve_viirs_lst(item, coefficient_file=None)
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/viirs/viirs_lst.py:7)。

无 docstring；算法解释见人工审阅章节。

### `produce_viirs_lst`

```python
produce_viirs_lst(input_path=None, output_path=None, coefficient_file=None, auxiliary_file=None, grid_id=None, algorithm_version=None, uncertainty_k=None) -> None
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/viirs/viirs_lst.py:11)。

无 docstring；算法解释见人工审阅章节。

### `viirs_lst`

```python
viirs_lst(indir_data=None, outdir_lst=None, coefficient_file=None, auxiliary_file=None, years=None, months=None, days=None, grid_id=None, algorithm_version=None, uncertainty_k=None, overwrite=None) -> None
```

定义类型：function；[源码第 26 行](C:/work/ls4t/base/viirs/viirs_lst.py:26)。

无 docstring；算法解释见人工审阅章节。

## base/viirs/viirs_merge.py

源码：[打开文件](C:/work/ls4t/base/viirs/viirs_merge.py)；8 行，1 个定义。

### `viirs_merge`

```python
viirs_merge(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/viirs/viirs_merge.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:43](C:/work/ls4t/tests/test_flat_structure.py:43)

## base/viirs/viirs_project.py

源码：[打开文件](C:/work/ls4t/base/viirs/viirs_project.py)；47 行，2 个定义。

### `project_viirs_product`

```python
project_viirs_product(item, target_grid_file=None, projection_chunk_size=None, cloud_fraction_threshold=None)
```

定义类型：function；[源码第 9 行](C:/work/ls4t/base/viirs/viirs_project.py:9)。

无 docstring；算法解释见人工审阅章节。

### `viirs_project`

```python
viirs_project(indir_extract=None, outdir_project=None, target_grid_file=None, years=None, months=None, days=None, projection_chunk_size=None, cloud_fraction_threshold=None, overwrite=None) -> None
```

定义类型：function；[源码第 24 行](C:/work/ls4t/base/viirs/viirs_project.py:24)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:44](C:/work/ls4t/tests/test_flat_structure.py:44)

## base/viirs/viirs_region.py

源码：[打开文件](C:/work/ls4t/base/viirs/viirs_region.py)；12 行，2 个定义。

### `viirs_data_region`

```python
viirs_data_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 7 行](C:/work/ls4t/base/viirs/viirs_region.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:45](C:/work/ls4t/tests/test_flat_structure.py:45)

### `viirs_result_region`

```python
viirs_result_region(input_paths=None, output_path=None, bounds=None) -> None
```

定义类型：function；[源码第 11 行](C:/work/ls4t/base/viirs/viirs_region.py:11)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:45](C:/work/ls4t/tests/test_flat_structure.py:45)

## cases/aatsr/aatsr_001deg_stats.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py)；282 行，10 个定义。

### `parse_date`

```python
parse_date(value: str) -> date
```

定义类型：function；[源码第 43 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:43)。

无 docstring；算法解释见人工审阅章节。

### `month_days`

```python
month_days(year: int, month: int) -> list[date]
```

定义类型：function；[源码第 52 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:52)。

无 docstring；算法解释见人工审阅章节。

### `make_arrays`

```python
make_arrays() -> tuple[dict[str, np.ndarray], np.ndarray]
```

定义类型：function；[源码第 57 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:57)。

无 docstring；算法解释见人工审阅章节。

### `source_files`

```python
source_files(source_root: Path, current: date) -> list[Path]
```

定义类型：function；[源码第 67 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:67)。

无 docstring；算法解释见人工审阅章节。

### `ancillary_paths`

```python
ancillary_paths(source_root: Path, current: date, lsct_path: Path) -> dict[str, Path]
```

定义类型：function；[源码第 76 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:76)。

无 docstring；算法解释见人工审阅章节。

### `add_source_file`

```python
add_source_file(source_root: Path, current: date, lsct_path: Path, day_sums: dict[str, np.ndarray], day_count: np.ndarray, night_sums: dict[str, np.ndarray], night_count: np.ndarray, monthly_sums: dict[str, np.ndarray] | None, monthly_count: np.ndarray | None, error_log: Path) -> bool
```

定义类型：function；[源码第 86 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:86)。

无 docstring；算法解释见人工审阅章节。

### `add_source_file.accumulate`

```python
add_source_file.accumulate(mask: np.ndarray, target_sums: dict[str, np.ndarray], target_count: np.ndarray) -> None
```

定义类型：nested；[源码第 144 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:144)。

无 docstring；算法解释见人工审阅章节。

### `write_product`

```python
write_product(path: Path, period: str, sums: dict[str, np.ndarray], count: np.ndarray, current: date | None=None) -> None
```

定义类型：function；[源码第 176 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:176)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:6](C:/work/ls4t/tests/test_products.py:6)

### `process_month`

```python
process_month(source_root: Path, output_root: Path, year: int, month: int, start: date, end: date, error_log: Path) -> None
```

定义类型：function；[源码第 206 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:206)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 260 行](C:/work/ls4t/cases/aatsr/aatsr_001deg_stats.py:260)。

无 docstring；算法解释见人工审阅章节。

## cases/aatsr/aatsr_data.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_data.py)；370 行，0 个定义。

## cases/aatsr/aatsr_era5_tcw.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_era5_tcw.py)；168 行，1 个定义。

### `write_vrt`

```python
write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, noDataValue=65535, bandnumber=1)
```

定义类型：function；[源码第 36 行](C:/work/ls4t/cases/aatsr/aatsr_era5_tcw.py:36)。

导出用于gdal vrt的配置文件 # 与函数配合使用，outfile为转成的文件路径，resampleAlg为重采样的 # dst_ds = gdal.Warp(outfile, vrtfile, geoloc=True, resampleAlg=gdal.GRIORA_NearestNeighbour) :param vrtfile:  该配置文件名称 :param datafile:  所要操作的文件名称 :param xfile:  经度坐标文件 lon :param yfile:  纬度坐标文件 lat 

## cases/aatsr/aatsr_lsct.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_lsct.py)；307 行，4 个定义。

### `fitting_with_ridge`

```python
fitting_with_ridge(bb, ww)
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/aatsr/aatsr_lsct.py:25)。

无 docstring；算法解释见人工审阅章节。

### `cal_fvc_from_lai`

```python
cal_fvc_from_lai(thetav, lai)
```

定义类型：function；[源码第 33 行](C:/work/ls4t/cases/aatsr/aatsr_lsct.py:33)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:17](C:/work/ls4t/tests/test_slstr_case_dependencies.py:17)

### `inv_mpl_agl_multiple_2`

```python
inv_mpl_agl_multiple_2(lst_n, lst_o, emis_s, emis_v, fvcN, fvcO, wl=10.8)
```

定义类型：function；[源码第 43 行](C:/work/ls4t/cases/aatsr/aatsr_lsct.py:43)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_read_aux_data`

```python
aatsr_read_aux_data(indir_emis, indir_type)
```

定义类型：function；[源码第 50 行](C:/work/ls4t/cases/aatsr/aatsr_lsct.py:50)。

aatsr 读取辅助数据 :param indir_emis: 发射率 :param indir_type:  地表类型 :return: 土壤发射率、植被发射率、分类、密度、树覆盖比例、树冠高度，观测天顶角、方位角

## cases/aatsr/aatsr_lsct_latlon.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_lsct_latlon.py)；481 行，6 个定义。

### `fitting_with_ridge`

```python
fitting_with_ridge(bb, ww)
```

定义类型：function；[源码第 29 行](C:/work/ls4t/cases/aatsr/aatsr_lsct_latlon.py:29)。

无 docstring；算法解释见人工审阅章节。

### `cal_fvc_from_lai`

```python
cal_fvc_from_lai(thetav, lai)
```

定义类型：function；[源码第 36 行](C:/work/ls4t/cases/aatsr/aatsr_lsct_latlon.py:36)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:17](C:/work/ls4t/tests/test_slstr_case_dependencies.py:17)

### `aatsr_read_aux_data`

```python
aatsr_read_aux_data(indir_emis, indir_type)
```

定义类型：function；[源码第 46 行](C:/work/ls4t/cases/aatsr/aatsr_lsct_latlon.py:46)。

aatsr 读取辅助数据 :param indir_emis: 发射率 :param indir_type:  地表类型 :return: 土壤发射率、植被发射率、分类、密度、树覆盖比例、树冠高度，观测天顶角、方位角

### `process_column`

```python
process_column(ks, nl, ns, off, wV, wS, rad_n, rad_o, mask0, wl)
```

定义类型：function；[源码第 75 行](C:/work/ls4t/cases/aatsr/aatsr_lsct_latlon.py:75)。

处理单列的所有像素（按列处理，提高数据局部性）

### `process_column_batch`

```python
process_column_batch(column_batch, nl, ns, off, wV, wS, rad_n, rad_o, mask0, wl)
```

定义类型：function；[源码第 128 行](C:/work/ls4t/cases/aatsr/aatsr_lsct_latlon.py:128)。

批量处理多列，减少进程启动开销

### `process_column_batch_new`

```python
process_column_batch_new(column_batch, nl, ns, off, wV, wS, rad_n, rad_o, mask0, wl)
```

定义类型：function；[源码第 188 行](C:/work/ls4t/cases/aatsr/aatsr_lsct_latlon.py:188)。

批量处理多列，减少进程启动开销

## cases/aatsr/aatsr_lsct_ndvi.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_lsct_ndvi.py)；247 行，2 个定义。

### `aatsr_inv_lsct2_window`

```python
aatsr_inv_lsct2_window(n, m, ws, wl, w, b, mask, lst)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/aatsr/aatsr_lsct_ndvi.py:23)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_inv_lsct2_Line`

```python
aatsr_inv_lsct2_Line(n, m, ws, wl, w, b, mask, lst)
```

定义类型：function；[源码第 53 行](C:/work/ls4t/cases/aatsr/aatsr_lsct_ndvi.py:53)。

无 docstring；算法解释见人工审阅章节。

## cases/aatsr/aatsr_lsct_v31.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_lsct_v31.py)；320 行，1 个定义。

### `inv_lsct2_v3_1`

```python
inv_lsct2_v3_1(w, b, mask, lst, n, m=2, ws=5, wl=10.8, method='ls', ifcons=0)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/aatsr/aatsr_lsct_v31.py:30)。

多角度 多组分 窗口反演 BFGS/powell/SLSQP/L-BFGS-B/TNC 优化版: 移除了 np.matrix，优化了 Bayesian 矩阵运算

## cases/aatsr/aatsr_lst.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_lst.py)；297 行，1 个定义。

### `cal_fvc_from_lai`

```python
cal_fvc_from_lai(thetav, lai)
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/aatsr/aatsr_lst.py:15)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:17](C:/work/ls4t/tests/test_slstr_case_dependencies.py:17)

## cases/aatsr/aatsr_monthly_3files.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_monthly_3files.py)；197 行，8 个定义。

### `month_ids`

```python
month_ids() -> list[int]
```

定义类型：function；[源码第 42 行](C:/work/ls4t/cases/aatsr/aatsr_monthly_3files.py:42)。

无 docstring；算法解释见人工审阅章节。

### `source_paths`

```python
source_paths(month_id: int) -> tuple[Path, Path]
```

定义类型：function；[源码第 50 行](C:/work/ls4t/cases/aatsr/aatsr_monthly_3files.py:50)。

无 docstring；算法解释见人工审阅章节。

### `check_sources`

```python
check_sources(months: list[int]) -> None
```

定义类型：function；[源码第 55 行](C:/work/ls4t/cases/aatsr/aatsr_monthly_3files.py:55)。

无 docstring；算法解释见人工审阅章节。

### `create_output`

```python
create_output(path: Path, dataset_name: str, months: list[int]) -> h5py.File
```

定义类型：function；[源码第 63 行](C:/work/ls4t/cases/aatsr/aatsr_monthly_3files.py:63)。

无 docstring；算法解释见人工审阅章节。

### `read_block`

```python
read_block(handle: h5py.File, field: str, row0: int, row1: int) -> np.ndarray
```

定义类型：function；[源码第 100 行](C:/work/ls4t/cases/aatsr/aatsr_monthly_3files.py:100)。

无 docstring；算法解释见人工审阅章节。

### `weighted_field`

```python
weighted_field(day: h5py.File, night: h5py.File, field: str, row0: int, row1: int) -> np.ndarray
```

定义类型：function；[源码第 104 行](C:/work/ls4t/cases/aatsr/aatsr_monthly_3files.py:104)。

无 docstring；算法解释见人工审阅章节。

### `composite_temperature`

```python
composite_temperature(day: h5py.File, night: h5py.File, row0: int, row1: int) -> np.ndarray
```

定义类型：function；[源码第 128 行](C:/work/ls4t/cases/aatsr/aatsr_monthly_3files.py:128)。

无 docstring；算法解释见人工审阅章节。

### `build`

```python
build() -> None
```

定义类型：function；[源码第 150 行](C:/work/ls4t/cases/aatsr/aatsr_monthly_3files.py:150)。

无 docstring；算法解释见人工审阅章节。

## cases/aatsr/aatsr_site_inv.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_site_inv.py)；417 行，4 个定义。

### `inv_lsct2_window`

```python
inv_lsct2_window(n, m, ws, wl, w, b, mask, lst, ifday=1)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv.py:17)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:70](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:70)、[tests/test_slstr_case_dependencies.py:138](C:/work/ls4t/tests/test_slstr_case_dependencies.py:138)

### `inv_lsct3_window`

```python
inv_lsct3_window(n, m, ws, wl, w, b, mask, lst)
```

定义类型：function；[源码第 50 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv.py:50)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:138](C:/work/ls4t/tests/test_slstr_case_dependencies.py:138)

### `optimize_LAI`

```python
optimize_LAI(lai, ndviN, ndviF, vzaN, vzaF, CI=1.0, ndvi_max=0.87, ndvi_min=0.04, G=0.5)
```

定义类型：function；[源码第 82 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv.py:82)。

优化LAI、CI、NDVI_s和NDVI_v参数  参数: lai: 初始LAI值 (25个像元的数组) ndviN: 近角度NDVI观测值 (25个像元的数组) ndviF: 远角度NDVI观测值 (25个像元的数组)   CI: 初始聚集指数 (默认1.0) ndvi_max: 初始纯植被NDVI估计 (默认0.87) ndvi_min: 初始纯土壤NDVI估计 (默认0.04) G: 叶倾角分布参数 (固定0.5)  返回: result: 优化结果字典

### `optimize_LAI.objective_function`

```python
optimize_LAI.objective_function(params)
```

定义类型：nested；[源码第 110 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv.py:110)。

目标函数: 最小化所有方程的残差平方和 params: 参数向量 [LAI_1, LAI_2, ..., LAI_25, CI, NDVI_s, NDVI_v]

## cases/aatsr/aatsr_site_inv_bayes.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py)；855 行，7 个定义。

### `inv_lsct2_window`

```python
inv_lsct2_window(n, m, ws, wl, w, b, mask, lst, ifday=1)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py:23)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:70](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:70)、[tests/test_slstr_case_dependencies.py:138](C:/work/ls4t/tests/test_slstr_case_dependencies.py:138)

### `inv_lsct3_window`

```python
inv_lsct3_window(n, m, ws, wl, w, b, mask, lst)
```

定义类型：function；[源码第 56 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py:56)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:138](C:/work/ls4t/tests/test_slstr_case_dependencies.py:138)

### `cal_fvc_from_lai`

```python
cal_fvc_from_lai(thetav, lai)
```

定义类型：function；[源码第 88 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py:88)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:17](C:/work/ls4t/tests/test_slstr_case_dependencies.py:17)

### `line_inv_2_s`

```python
line_inv_2_s(wNLine, wOLine, radNLine, radOLine, maskLine, nl=1024)
```

定义类型：function；[源码第 97 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py:97)。

this is for the sample rec

### `line_inv_3_s`

```python
line_inv_3_s(wNLine, wOLine, radNLine, radOLine, maskLine, nl=1024)
```

定义类型：function；[源码第 235 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py:235)。

this is for the sample rec

### `doMultiple_line_inv_2_s`

```python
doMultiple_line_inv_2_s(param)
```

定义类型：function；[源码第 374 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py:374)。

无 docstring；算法解释见人工审阅章节。

### `inv_mpl_agl_multiple_2`

```python
inv_mpl_agl_multiple_2(lst_n, lst_o, emis_s, emis_v, fvcN, fvcO, wl=10.8)
```

定义类型：function；[源码第 377 行](C:/work/ls4t/cases/aatsr/aatsr_site_inv_bayes.py:377)。

无 docstring；算法解释见人工审阅章节。

## cases/aatsr/aatsr_site_series.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_site_series.py)；681 行，7 个定义。

### `filter_sites_by_year_range`

```python
filter_sites_by_year_range(fileNames, indir_merge, start_year=2002, end_year=2012)
```

定义类型：function；[源码第 16 行](C:/work/ls4t/cases/aatsr/aatsr_site_series.py:16)。

筛选出在指定年份范围内都有数据的站点

### `analyze_site_temporal_trend`

```python
analyze_site_temporal_trend(siteName, data)
```

定义类型：function；[源码第 50 行](C:/work/ls4t/cases/aatsr/aatsr_site_series.py:50)。

分析单个站点的时间趋势（按月计算RMSE），加入云掩码筛选

### `plot_site_trend`

```python
plot_site_trend(siteName, monthly_results, output_dir)
```

定义类型：function；[源码第 117 行](C:/work/ls4t/cases/aatsr/aatsr_site_series.py:117)。

绘制单个站点的RMSE月度时间趋势图，显示验证数据数量

### `plot_combined_trend`

```python
plot_combined_trend(all_sites_results, output_dir)
```

定义类型：function；[源码第 158 行](C:/work/ls4t/cases/aatsr/aatsr_site_series.py:158)。

绘制所有站点的综合月度RMSE趋势图（云掩码筛选后）

### `calculate_overall_seasonal_pattern`

```python
calculate_overall_seasonal_pattern(all_sites_results)
```

定义类型：function；[源码第 279 行](C:/work/ls4t/cases/aatsr/aatsr_site_series.py:279)。

使用全体数据计算每个月的平均RMSE（季节节律基准）

### `deseasonalize_with_overall_pattern`

```python
deseasonalize_with_overall_pattern(monthly_data, overall_monthly_means)
```

定义类型：function；[源码第 331 行](C:/work/ls4t/cases/aatsr/aatsr_site_series.py:331)。

使用全体数据的季节节律基准进行去季节化

### `analyze_temporal_trend_with_deseasonalization`

```python
analyze_temporal_trend_with_deseasonalization(all_sites_results, output_dir)
```

定义类型：function；[源码第 345 行](C:/work/ls4t/cases/aatsr/aatsr_site_series.py:345)。

分析反演精度随时间变化的趋势（使用全体数据的季节节律）

## cases/aatsr/aatsr_site_validate.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_site_validate.py)；322 行，2 个定义。

### `get_timezone`

```python
get_timezone(lat, lon)
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/aatsr/aatsr_site_validate.py:25)。

获取时区信息

### `plot_density`

```python
plot_density(data1, data2, ind, label1, label2, dif_therhold, outfile)
```

定义类型：function；[源码第 31 行](C:/work/ls4t/cases/aatsr/aatsr_site_validate.py:31)。

无 docstring；算法解释见人工审阅章节。

## cases/aatsr/aatsr_unzip.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/aatsr_unzip.py)；28 行，0 个定义。

## cases/aatsr/util_aatsr.py

源码：[打开文件](C:/work/ls4t/cases/aatsr/util_aatsr.py)；267 行，17 个定义。

### `aatsr_read_aux_data`

```python
aatsr_read_aux_data(indir_emis='/home/hero/data/base/0_base/emis/', indir_type='/home/hero/data/base/0_base/type/')
```

定义类型：function；[源码第 13 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:13)。

aatsr 读取辅助数据 :param indir_emis: 发射率 :param indir_type:  地表类型 :return: 土壤发射率、植被发射率、分类、密度、观测天顶角、方位角

### `aatsr_read_crown_data`

```python
aatsr_read_crown_data(indir_veg_pra)
```

定义类型：function；[源码第 43 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:43)。

读取植被参数 :param indir_veg_pra: 地址 :return: 树密度、覆盖度、树冠高度

### `aatsr_clo_optimized`

```python
aatsr_clo_optimized(clo)
```

定义类型：function；[源码第 62 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:62)。

优化版：使用位运算检查最低两位 最低位(第0位)表示是否为陆地(1)，第1位表示是否有云(0) 只有陆地且无云时返回True  :param clo: 十进制整数或数组 :return: 是否符合条件(bool或np.ndarray)

### `aatsr_read_sites_obs`

```python
aatsr_read_sites_obs(infile, ifNDVI=1)
```

定义类型：function；[源码第 80 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:80)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_read_sites_clo`

```python
aatsr_read_sites_clo(infile)
```

定义类型：function；[源码第 98 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:98)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_read_sites_lst`

```python
aatsr_read_sites_lst(infile)
```

定义类型：function；[源码第 106 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:106)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_read_sites_angle`

```python
aatsr_read_sites_angle(infile)
```

定义类型：function；[源码第 113 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:113)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_read_sites_emis`

```python
aatsr_read_sites_emis(infile)
```

定义类型：function；[源码第 121 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:121)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_read_sites_loc`

```python
aatsr_read_sites_loc(infile)
```

定义类型：function；[源码第 128 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:128)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_read_sites_time`

```python
aatsr_read_sites_time(infile)
```

定义类型：function；[源码第 134 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:134)。

无 docstring；算法解释见人工审阅章节。

### `aatsr_read_lst`

```python
aatsr_read_lst(infile_lst)
```

定义类型：function；[源码第 142 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:142)。

读取aatsr h5 lst数据 :param infile_lst: lst文件地址 :return: 两角度LST

同名测试引用：[tests/test_aatsr_case_dependencies.py:90](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:90)

### `aatsr_read_NDVI`

```python
aatsr_read_NDVI(infile_obs)
```

定义类型：function；[源码第 154 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:154)。

读取aatsr h5 obs数据并计算NDVI :param infile_obs: obs文件地址 :return: 两角度NDVI

### `aatsr_read_obs`

```python
aatsr_read_obs(infile_obs)
```

定义类型：function；[源码第 174 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:174)。

读取aatsr h5 obs数据 :param infile_obs: obs文件地址 :return: 两角度红、近红外

### `aatsr_read_clo`

```python
aatsr_read_clo(infile_clo)
```

定义类型：function；[源码第 186 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:186)。

读取aatsr h5 clo数据(自动计算并保存mask) :param infile_clo: clo文件地址 :return: 两角度clo

同名测试引用：[tests/test_aatsr_case_dependencies.py:90](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:90)

### `aatsr_read_loc`

```python
aatsr_read_loc(infile_loc, iflonlat=0)
```

定义类型：function；[源码第 215 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:215)。

读取aatsr h5 loc数据 :param infile_loc: loc文件地址 :param iflonlat: 是否返回经纬度，0-否，1-是 :return: 像元索引(行列)，可选经纬度

### `aatsr_read_lai`

```python
aatsr_read_lai(infile_aux)
```

定义类型：function；[源码第 232 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:232)。

读取aatsr h5 aux数据 :param infile_aux: aux文件地址 :return: LAI

### `aatsr_read_angle`

```python
aatsr_read_angle(infile_ang, ifsun=1, ifview=1)
```

定义类型：function；[源码第 244 行](C:/work/ls4t/cases/aatsr/util_aatsr.py:244)。

读取aatsr h5 ang数据 :param infile_ang: ang文件地址 :return: 太阳天顶角、方位角

同名测试引用：[tests/test_aatsr_case_dependencies.py:90](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:90)

## cases/beijing-building-structure/integrate_with_lai.py

源码：[打开文件](C:/work/ls4t/cases/beijing-building-structure/integrate_with_lai.py)；111 行，2 个定义。

### `sha256`

```python
sha256(p)
```

定义类型：function；[源码第 21 行](C:/work/ls4t/cases/beijing-building-structure/integrate_with_lai.py:21)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:152](C:/work/ls4t/tests/test_africa_download.py:152)、[tests/test_msg_evo_sample.py:44](C:/work/ls4t/tests/test_msg_evo_sample.py:44)、[tests/test_standalone_cases.py:61](C:/work/ls4t/tests/test_standalone_cases.py:61)

### `main`

```python
main()
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/beijing-building-structure/integrate_with_lai.py:27)。

无 docstring；算法解释见人工审阅章节。

## cases/beijing-building-structure/quicklook.py

源码：[打开文件](C:/work/ls4t/cases/beijing-building-structure/quicklook.py)；31 行，0 个定义。

## cases/beijing-building-structure/run.py

源码：[打开文件](C:/work/ls4t/cases/beijing-building-structure/run.py)；180 行，10 个定义。

### `sha256`

```python
sha256(p)
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/beijing-building-structure/run.py:27)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:152](C:/work/ls4t/tests/test_africa_download.py:152)、[tests/test_msg_evo_sample.py:44](C:/work/ls4t/tests/test_msg_evo_sample.py:44)、[tests/test_standalone_cases.py:61](C:/work/ls4t/tests/test_standalone_cases.py:61)

### `save`

```python
save(name, obj)
```

定义类型：function；[源码第 33 行](C:/work/ls4t/cases/beijing-building-structure/run.py:33)。

无 docstring；算法解释见人工审阅章节。

### `overlap_matrix`

```python
overlap_matrix(target_start, target_step, target_size, source_start, source_step, source_size)
```

定义类型：function；[源码第 36 行](C:/work/ls4t/cases/beijing-building-structure/run.py:36)。

Sparse exact interval-intersection lengths, in metres, on an increasing axis.

同名测试引用：[tests/test_beijing_building_structure.py:13](C:/work/ls4t/tests/test_beijing_building_structure.py:13)

### `rectangles`

```python
rectangles(geometries)
```

定义类型：function；[源码第 48 行](C:/work/ls4t/cases/beijing-building-structure/run.py:48)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_building_structure.py:22](C:/work/ls4t/tests/test_beijing_building_structure.py:22)

### `write_raster`

```python
write_raster(path, array, profile, desc, nodata=NODATA)
```

定义类型：function；[源码第 55 行](C:/work/ls4t/cases/beijing-building-structure/run.py:55)。

无 docstring；算法解释见人工审阅章节。

### `coarse_statistics`

```python
coarse_statistics(h, valid, built, patches, profile, size)
```

定义类型：function；[源码第 61 行](C:/work/ls4t/cases/beijing-building-structure/run.py:61)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_building_structure.py:30](C:/work/ls4t/tests/test_beijing_building_structure.py:30)

### `coarse_statistics.aggregate`

```python
coarse_statistics.aggregate(a)
```

定义类型：nested；[源码第 63 行](C:/work/ls4t/cases/beijing-building-structure/run.py:63)。

无 docstring；算法解释见人工审阅章节。

### `lai_grid`

```python
lai_grid(h, valid, built, profile)
```

定义类型：function；[源码第 85 行](C:/work/ls4t/cases/beijing-building-structure/run.py:85)。

无 docstring；算法解释见人工审阅章节。

### `lai_grid.integrate`

```python
lai_grid.integrate(a)
```

定义类型：nested；[源码第 92 行](C:/work/ls4t/cases/beijing-building-structure/run.py:92)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 122 行](C:/work/ls4t/cases/beijing-building-structure/run.py:122)。

无 docstring；算法解释见人工审阅章节。

## cases/beijing-building-structure/verify.py

源码：[打开文件](C:/work/ls4t/cases/beijing-building-structure/verify.py)；67 行，0 个定义。

## cases/beijing-buildings-urban-g/audit_sources.py

源码：[打开文件](C:/work/ls4t/cases/beijing-buildings-urban-g/audit_sources.py)；27 行，0 个定义。

## cases/beijing-buildings-urban-g/extract.py

源码：[打开文件](C:/work/ls4t/cases/beijing-buildings-urban-g/extract.py)；90 行，2 个定义。

### `scan`

```python
scan(task)
```

定义类型：function；[源码第 12 行](C:/work/ls4t/cases/beijing-buildings-urban-g/extract.py:12)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 64 行](C:/work/ls4t/cases/beijing-buildings-urban-g/extract.py:64)。

无 docstring；算法解释见人工审阅章节。

## cases/beijing-buildings-urban-g/finalize.py

源码：[打开文件](C:/work/ls4t/cases/beijing-buildings-urban-g/finalize.py)；42 行，0 个定义。

## cases/beijing-buildings-urban-g/review_units_fractions.py

源码：[打开文件](C:/work/ls4t/cases/beijing-buildings-urban-g/review_units_fractions.py)；95 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/beijing-buildings-urban-g/review_units_fractions.py:15)。

无 docstring；算法解释见人工审阅章节。

## cases/beijing-buildings-urban-g/run.py

源码：[打开文件](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py)；240 行，9 个定义。

### `union_areas`

```python
union_areas(cells, buildings, tree=None)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:17)。

Return union area per cell; intersections are unioned before measuring.

### `prepare_vectors`

```python
prepare_vectors(boundary)
```

定义类型：function；[源码第 33 行](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:33)。

无 docstring；算法解释见人工审阅章节。

### `prepare_vectors.consume`

```python
prepare_vectors.consume(lines)
```

定义类型：nested；[源码第 42 行](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:42)。

无 docstring；算法解释见人工审阅章节。

### `raster_products`

```python
raster_products(frame, inside, profile)
```

定义类型：function；[源码第 92 行](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:92)。

无 docstring；算法解释见人工审阅章节。

### `write_raster`

```python
write_raster(path, array, profile, dtype, nodata, description)
```

定义类型：function；[源码第 121 行](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:121)。

无 docstring；算法解释见人工审阅章节。

### `verify`

```python
verify(a, inside, profile, frame)
```

定义类型：function；[源码第 130 行](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:130)。

无 docstring；算法解释见人工审阅章节。

### `preview`

```python
preview(a, inside, profile)
```

定义类型：function；[源码第 153 行](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:153)。

无 docstring；算法解释见人工审阅章节。

### `integrate`

```python
integrate(summary)
```

定义类型：function；[源码第 175 行](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:175)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 205 行](C:/work/ls4t/cases/beijing-buildings-urban-g/run.py:205)。

无 docstring；算法解释见人工审阅章节。

## cases/beijing-buildings-urban-g/test_methods.py

源码：[打开文件](C:/work/ls4t/cases/beijing-buildings-urban-g/test_methods.py)；21 行，3 个定义。

### `test_overlapping_footprints_union_not_sum`

```python
test_overlapping_footprints_union_not_sum()
```

定义类型：function；[源码第 5 行](C:/work/ls4t/cases/beijing-buildings-urban-g/test_methods.py:5)。

无 docstring；算法解释见人工审阅章节。

### `test_exact_ten_percent_threshold_and_hole`

```python
test_exact_ten_percent_threshold_and_hole()
```

定义类型：function；[源码第 10 行](C:/work/ls4t/cases/beijing-buildings-urban-g/test_methods.py:10)。

无 docstring；算法解释见人工审阅章节。

### `test_empty_and_edge_touching_cells`

```python
test_empty_and_edge_touching_cells()
```

定义类型：function；[源码第 18 行](C:/work/ls4t/cases/beijing-buildings-urban-g/test_methods.py:18)。

无 docstring；算法解释见人工审阅章节。

## cases/landsat-beijing-lai/download_2026_extension.py

源码：[打开文件](C:/work/ls4t/cases/landsat-beijing-lai/download_2026_extension.py)；24 行，0 个定义。

## cases/landsat-beijing-lai/extend_2026.py

源码：[打开文件](C:/work/ls4t/cases/landsat-beijing-lai/extend_2026.py)；160 行，5 个定义。

### `link_once`

```python
link_once(src, dst)
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/landsat-beijing-lai/extend_2026.py:25)。

无 docstring；算法解释见人工审阅章节。

### `calendar_to_date`

```python
calendar_to_date(cutoff)
```

定义类型：function；[源码第 31 行](C:/work/ls4t/cases/landsat-beijing-lai/extend_2026.py:31)。

无 docstring；算法解释见人工审阅章节。

### `prepare_private_ndvi`

```python
prepare_private_ndvi(d, profile, inside)
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/landsat-beijing-lai/extend_2026.py:39)。

Prepare only missing new-scene QA caches, preserving the old NDVI collection.

### `main`

```python
main()
```

定义类型：function；[源码第 69 行](C:/work/ls4t/cases/landsat-beijing-lai/extend_2026.py:69)。

无 docstring；算法解释见人工审阅章节。

### `main.progress`

```python
main.progress(**kw)
```

定义类型：nested；[源码第 83 行](C:/work/ls4t/cases/landsat-beijing-lai/extend_2026.py:83)。

无 docstring；算法解释见人工审阅章节。

## cases/landsat-beijing-lai/make_float_vrt.py

源码：[打开文件](C:/work/ls4t/cases/landsat-beijing-lai/make_float_vrt.py)；60 行，0 个定义。

## cases/landsat-beijing-lai/quicklook.py

源码：[打开文件](C:/work/ls4t/cases/landsat-beijing-lai/quicklook.py)；50 行，0 个定义。

## cases/landsat-beijing-lai/run.py

源码：[打开文件](C:/work/ls4t/cases/landsat-beijing-lai/run.py)；440 行，15 个定义。

### `utcnow`

```python
utcnow()
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:39)。

无 docstring；算法解释见人工审阅章节。

### `save_json`

```python
save_json(path, value)
```

定义类型：function；[源码第 42 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:42)。

无 docstring；算法解释见人工审阅章节。

### `sha256`

```python
sha256(path)
```

定义类型：function；[源码第 47 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:47)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:152](C:/work/ls4t/tests/test_africa_download.py:152)、[tests/test_msg_evo_sample.py:44](C:/work/ls4t/tests/test_msg_evo_sample.py:44)、[tests/test_standalone_cases.py:61](C:/work/ls4t/tests/test_standalone_cases.py:61)

### `basis`

```python
basis(dates)
```

定义类型：function；[源码第 54 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:54)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_lai_8day.py:42](C:/work/ls4t/tests/test_beijing_lai_8day.py:42)

### `build_calendar`

```python
build_calendar(first, last)
```

定义类型：function；[源码第 60 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:60)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_lai_8day.py:17](C:/work/ls4t/tests/test_beijing_lai_8day.py:17)

### `inventory`

```python
inventory(cfg)
```

定义类型：function；[源码第 72 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:72)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:39](C:/work/ls4t/tests/test_south_america_components.py:39)

### `make_scene`

```python
make_scene(scene, cfg, profile)
```

定义类型：function；[源码第 102 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:102)。

无 docstring；算法解释见人工审阅章节。

### `fit_curve`

```python
fit_curve(values, design, years, quarters, omit_lo, omit_hi, times, ridge, n_min, y_min, q_min)
```

定义类型：function；[源码第 148 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:148)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_lai_8day.py:47](C:/work/ls4t/tests/test_beijing_lai_8day.py:47)

### `estimate_bracket`

```python
estimate_bracket(t, x, values, design, target_x, beta, fitted, max_linear, max_residual, local_max, left, right)
```

定义类型：function；[源码第 177 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:177)。

无 docstring；算法解释见人工审阅章节。

### `estimate`

```python
estimate(t, x, values, design, target_x, beta, fitted, max_linear, max_residual, local_max, omit_lo, omit_hi)
```

定义类型：function；[源码第 208 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:208)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_lai_8day.py:27](C:/work/ls4t/tests/test_beijing_lai_8day.py:27)

### `reconstruct`

```python
reconstruct(cube, inside, x, design, years, quarters, centers, target_design, starts, stops, ridge, n_min, y_min, q_min, max_linear, max_residual, local_max)
```

定义类型：function；[源码第 221 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:221)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_lai_8day.py:34](C:/work/ls4t/tests/test_beijing_lai_8day.py:34)

### `numerical_checks`

```python
numerical_checks()
```

定义类型：function；[源码第 258 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:258)。

无 docstring；算法解释见人工审阅章节。

### `run`

```python
run(cfg)
```

定义类型：function；[源码第 270 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:270)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:241](C:/work/ls4t/tests/test_africa_download.py:241)、[tests/test_beijing_building_structure.py:8](C:/work/ls4t/tests/test_beijing_building_structure.py:8)、[tests/test_beijing_lai_8day.py:10](C:/work/ls4t/tests/test_beijing_lai_8day.py:10)、[tests/test_normalization_raster.py:81](C:/work/ls4t/tests/test_normalization_raster.py:81)、[tests/test_slstr_case_dependencies.py:3](C:/work/ls4t/tests/test_slstr_case_dependencies.py:3)、[tests/test_south_america_components.py:91](C:/work/ls4t/tests/test_south_america_components.py:91)、[tests/test_south_america_monthly_components.py:99](C:/work/ls4t/tests/test_south_america_monthly_components.py:99)、[tests/test_standalone_cases.py:31](C:/work/ls4t/tests/test_standalone_cases.py:31)

### `run.progress`

```python
run.progress(**kw)
```

定义类型：nested；[源码第 282 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:282)。

无 docstring；算法解释见人工审阅章节。

### `validate`

```python
validate(root, cfg)
```

定义类型：function；[源码第 400 行](C:/work/ls4t/cases/landsat-beijing-lai/run.py:400)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:49](C:/work/ls4t/tests/test_products.py:49)

## cases/landsat-beijing-lai/validate_2026.py

源码：[打开文件](C:/work/ls4t/cases/landsat-beijing-lai/validate_2026.py)；65 行，0 个定义。

## cases/landsat-beijing-lai/verify.py

源码：[打开文件](C:/work/ls4t/cases/landsat-beijing-lai/verify.py)；139 行，2 个定义。

### `digest`

```python
digest(p)
```

定义类型：function；[源码第 13 行](C:/work/ls4t/cases/landsat-beijing-lai/verify.py:13)。

无 docstring；算法解释见人工审阅章节。

### `run`

```python
run()
```

定义类型：function；[源码第 19 行](C:/work/ls4t/cases/landsat-beijing-lai/verify.py:19)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:241](C:/work/ls4t/tests/test_africa_download.py:241)、[tests/test_beijing_building_structure.py:8](C:/work/ls4t/tests/test_beijing_building_structure.py:8)、[tests/test_beijing_lai_8day.py:10](C:/work/ls4t/tests/test_beijing_lai_8day.py:10)、[tests/test_normalization_raster.py:81](C:/work/ls4t/tests/test_normalization_raster.py:81)、[tests/test_slstr_case_dependencies.py:3](C:/work/ls4t/tests/test_slstr_case_dependencies.py:3)、[tests/test_south_america_components.py:91](C:/work/ls4t/tests/test_south_america_components.py:91)、[tests/test_south_america_monthly_components.py:99](C:/work/ls4t/tests/test_south_america_monthly_components.py:99)、[tests/test_standalone_cases.py:31](C:/work/ls4t/tests/test_standalone_cases.py:31)

## cases/msg/assessment/analyze_station_full_2018_2024.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py)；286 行，14 个定义。

### `save_json`

```python
save_json(name, data)
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:20)。

无 docstring；算法解释见人工审阅章节。

### `dates`

```python
dates(x)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:23)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:65](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:65)、[tests/test_annual_cycle.py:33](C:/work/ls4t/tests/test_annual_cycle.py:33)、[tests/test_beijing_lai_8day.py:41](C:/work/ls4t/tests/test_beijing_lai_8day.py:41)、[tests/test_msg_case_dependencies.py:81](C:/work/ls4t/tests/test_msg_case_dependencies.py:81)、[tests/test_slstr_case_dependencies.py:15](C:/work/ls4t/tests/test_slstr_case_dependencies.py:15)

### `ground_all`

```python
ground_all(sites)
```

定义类型：function；[源码第 28 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:28)。

无 docstring；算法解释见人工审阅章节。

### `match`

```python
match(x, ground)
```

定义类型：function；[源码第 42 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:42)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:252](C:/work/ls4t/tests/test_africa_download.py:252)、[tests/test_annual_cycle.py:43](C:/work/ls4t/tests/test_annual_cycle.py:43)、[tests/test_dual_thermal_sensors.py:107](C:/work/ls4t/tests/test_dual_thermal_sensors.py:107)、[tests/test_flat_structure.py:184](C:/work/ls4t/tests/test_flat_structure.py:184)、[tests/test_kernel_atc_case.py:47](C:/work/ls4t/tests/test_kernel_atc_case.py:47)、[tests/test_kernel_models.py:56](C:/work/ls4t/tests/test_kernel_models.py:56)、[tests/test_multisource_normalization.py:23](C:/work/ls4t/tests/test_multisource_normalization.py:23)、[tests/test_normalization.py:59](C:/work/ls4t/tests/test_normalization.py:59)、[tests/test_normalization_raster.py:58](C:/work/ls4t/tests/test_normalization_raster.py:58)、[tests/test_retrieval.py:35](C:/work/ls4t/tests/test_retrieval.py:35)、[tests/test_slstr_products.py:42](C:/work/ls4t/tests/test_slstr_products.py:42)、[tests/test_south_america_components.py:114](C:/work/ls4t/tests/test_south_america_components.py:114)、[tests/test_south_america_monthly_components.py:56](C:/work/ls4t/tests/test_south_america_monthly_components.py:56)、[tests/test_south_america_native_recovery.py:65](C:/work/ls4t/tests/test_south_america_native_recovery.py:65)、[tests/test_stream_era5.py:76](C:/work/ls4t/tests/test_stream_era5.py:76)

### `aggregate`

```python
aggregate(x, scale)
```

定义类型：function；[源码第 50 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:50)。

无 docstring；算法解释见人工审阅章节。

### `metrics`

```python
metrics(pairs, groupcols, scales=('instantaneous', 'monthly_calendar', 'monthly_hour'))
```

定义类型：function；[源码第 56 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:56)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:71](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:71)

### `summary`

```python
summary(met, keys)
```

定义类型：function；[源码第 67 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:67)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:97](C:/work/ls4t/tests/test_msg_evo_sample.py:97)、[tests/test_slstr_evo_sample.py:35](C:/work/ls4t/tests/test_slstr_evo_sample.py:35)

### `paired`

```python
paired(x, components=COMPONENTS)
```

定义类型：function；[源码第 71 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:71)。

无 docstring；算法解释见人工审阅章节。

### `legacy_pairs`

```python
legacy_pairs(x, soil='shaded_soil', residual=True, bounds=(0, 60), joint=True)
```

定义类型：function；[源码第 79 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:79)。

无 docstring；算法解释见人工审阅章节。

### `legacy_audit`

```python
legacy_audit(archive, ground)
```

定义类型：function；[源码第 90 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:90)。

无 docstring；算法解释见人工审阅章节。

### `archive_fingerprint`

```python
archive_fingerprint(pred, archive)
```

定义类型：function；[源码第 129 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:129)。

无 docstring；算法解释见人工审阅章节。

### `input_audit`

```python
input_audit(completes)
```

定义类型：function；[源码第 160 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:160)。

无 docstring；算法解释见人工审阅章节。

### `common_controls`

```python
common_controls(matches)
```

定义类型：function；[源码第 185 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:185)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 209 行](C:/work/ls4t/cases/msg/assessment/analyze_station_full_2018_2024.py:209)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/assess_production_need.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/assess_production_need.py)；121 行，2 个定义。

### `distribution`

```python
distribution(x)
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/msg/assessment/assess_production_need.py:27)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 34 行](C:/work/ls4t/cases/msg/assessment/assess_production_need.py:34)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/audit_iodc_geolocation.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/audit_iodc_geolocation.py)；100 行，6 个定义。

### `read`

```python
read(path)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/msg/assessment/audit_iodc_geolocation.py:17)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:262](C:/work/ls4t/tests/test_africa_download.py:262)

### `summary`

```python
summary(pred, observed)
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/msg/assessment/audit_iodc_geolocation.py:20)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:97](C:/work/ls4t/tests/test_msg_evo_sample.py:97)、[tests/test_slstr_evo_sample.py:35](C:/work/ls4t/tests/test_slstr_evo_sample.py:35)

### `metadata`

```python
metadata(f)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/audit_iodc_geolocation.py:30)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:57](C:/work/ls4t/tests/test_africa_download.py:57)、[tests/test_dual_thermal_sensors.py:53](C:/work/ls4t/tests/test_dual_thermal_sensors.py:53)、[tests/test_normalization_raster.py:38](C:/work/ls4t/tests/test_normalization_raster.py:38)、[tests/test_products.py:10](C:/work/ls4t/tests/test_products.py:10)、[tests/test_slstr_products.py:95](C:/work/ls4t/tests/test_slstr_products.py:95)、[tests/test_south_america_native_recovery.py:65](C:/work/ls4t/tests/test_south_america_native_recovery.py:65)、[tests/test_spatial_modes.py:39](C:/work/ls4t/tests/test_spatial_modes.py:39)

### `metadata.cv`

```python
metadata.cv(v)
```

定义类型：nested；[源码第 32 行](C:/work/ls4t/cases/msg/assessment/audit_iodc_geolocation.py:32)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/msg/assessment/audit_iodc_geolocation.py:39)。

无 docstring；算法解释见人工审阅章节。

### `main.mapped`

```python
main.mapped(raw, label, missing)
```

定义类型：nested；[源码第 62 行](C:/work/ls4t/cases/msg/assessment/audit_iodc_geolocation.py:62)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/audit_joint_10k_threshold.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/audit_joint_10k_threshold.py)；99 行，2 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/audit_joint_10k_threshold.py:11)。

无 docstring；算法解释见人工审阅章节。

### `main.table`

```python
main.table(d)
```

定义类型：nested；[源码第 70 行](C:/work/ls4t/cases/msg/assessment/audit_joint_10k_threshold.py:70)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_calibration.py:11](C:/work/ls4t/tests/test_calibration.py:11)

## cases/msg/assessment/audit_msg_5x5_products.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/audit_msg_5x5_products.py)；49 行，0 个定义。

## cases/msg/assessment/audit_station_landcover.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/audit_station_landcover.py)；39 行，2 个定义。

### `sha`

```python
sha(p)
```

定义类型：function；[源码第 10 行](C:/work/ls4t/cases/msg/assessment/audit_station_landcover.py:10)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `main`

```python
main()
```

定义类型：function；[源码第 12 行](C:/work/ls4t/cases/msg/assessment/audit_station_landcover.py:12)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/audit_station_original_parameters.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/audit_station_original_parameters.py)；61 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 12 行](C:/work/ls4t/cases/msg/assessment/audit_station_original_parameters.py:12)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/audit_station_replay_extremes.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/audit_station_replay_extremes.py)；53 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/audit_station_replay_extremes.py:11)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/compare_evo_5x5.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/compare_evo_5x5.py)；278 行，5 个定义。

### `write_readme`

```python
write_readme(out, report)
```

定义类型：function；[源码第 28 行](C:/work/ls4t/cases/msg/assessment/compare_evo_5x5.py:28)。

无 docstring；算法解释见人工审阅章节。

### `write_readme.pick`

```python
write_readme.pick(scope, method, component)
```

定义类型：nested；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/compare_evo_5x5.py:30)。

无 docstring；算法解释见人工审阅章节。

### `write_readme.table`

```python
write_readme.table(scope)
```

定义类型：nested；[源码第 32 行](C:/work/ls4t/cases/msg/assessment/compare_evo_5x5.py:32)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_calibration.py:11](C:/work/ls4t/tests/test_calibration.py:11)

### `load_station`

```python
load_station(path, method)
```

定义类型：function；[源码第 107 行](C:/work/ls4t/cases/msg/assessment/compare_evo_5x5.py:107)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 116 行](C:/work/ls4t/cases/msg/assessment/compare_evo_5x5.py:116)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/compare_existing_europe12_parameters.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/compare_existing_europe12_parameters.py)；105 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 14 行](C:/work/ls4t/cases/msg/assessment/compare_existing_europe12_parameters.py:14)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/compare_monthly_hour_factors.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/compare_monthly_hour_factors.py)；130 行，3 个定义。

### `window_prepare`

```python
window_prepare(data, h, w1size, w2size, hotspot)
```

定义类型：function；[源码第 12 行](C:/work/ls4t/cases/msg/assessment/compare_monthly_hour_factors.py:12)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 29 行](C:/work/ls4t/cases/msg/assessment/compare_monthly_hour_factors.py:29)。

无 docstring；算法解释见人工审阅章节。

### `main.evaluate`

```python
main.evaluate(name, component, mask, support, family)
```

定义类型：nested；[源码第 72 行](C:/work/ls4t/cases/msg/assessment/compare_monthly_hour_factors.py:72)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/compare_source_time_correction.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/compare_source_time_correction.py)；188 行，6 个定义。

### `masks`

```python
masks(x)
```

定义类型：function；[源码第 21 行](C:/work/ls4t/cases/msg/assessment/compare_source_time_correction.py:21)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_lai_8day.py:1](C:/work/ls4t/tests/test_beijing_lai_8day.py:1)

### `aggregate`

```python
aggregate(x, mask)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/compare_source_time_correction.py:26)。

无 docstring；算法解释见人工审阅章节。

### `score`

```python
score(g, basis, support)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/compare_source_time_correction.py:30)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 45 行](C:/work/ls4t/cases/msg/assessment/compare_source_time_correction.py:45)。

无 docstring；算法解释见人工审阅章节。

### `plots`

```python
plots(metrics, comparison)
```

定义类型：function；[源码第 154 行](C:/work/ls4t/cases/msg/assessment/compare_source_time_correction.py:154)。

无 docstring；算法解释见人工审阅章节。

### `report`

```python
report(comparison)
```

定义类型：function；[源码第 175 行](C:/work/ls4t/cases/msg/assessment/compare_source_time_correction.py:175)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:62](C:/work/ls4t/tests/test_africa_download.py:62)、[tests/test_kernel_atc_case.py:19](C:/work/ls4t/tests/test_kernel_atc_case.py:19)、[tests/test_south_america_components.py:83](C:/work/ls4t/tests/test_south_america_components.py:83)、[tests/test_south_america_remaining.py:36](C:/work/ls4t/tests/test_south_america_remaining.py:36)

## cases/msg/assessment/complete_2017_monthly.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/complete_2017_monthly.py)；95 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 14 行](C:/work/ls4t/cases/msg/assessment/complete_2017_monthly.py:14)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/complete_validation_analysis.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/complete_validation_analysis.py)；49 行，1 个定义。

### `rmse`

```python
rmse(a, b)
```

定义类型：function；[源码第 7 行](C:/work/ls4t/cases/msg/assessment/complete_validation_analysis.py:7)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:111](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:111)

## cases/msg/assessment/display-lsct.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/display-lsct.py)；0 行，0 个定义。

## cases/msg/assessment/display-lst-lai.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/display-lst-lai.py)；0 行，0 个定义。

## cases/msg/assessment/display-studyarea.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/display-studyarea.py)；0 行，0 个定义。

## cases/msg/assessment/draw_station_workflow.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/draw_station_workflow.py)；16 行，0 个定义。

## cases/msg/assessment/evaluate_baseline_range_0_60.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/evaluate_baseline_range_0_60.py)；113 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 12 行](C:/work/ls4t/cases/msg/assessment/evaluate_baseline_range_0_60.py:12)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/evaluate_europe_10_16.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/evaluate_europe_10_16.py)；90 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/evaluate_europe_10_16.py:11)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/evaluate_evo_11_16.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/evaluate_evo_11_16.py)；72 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/evaluate_evo_11_16.py:11)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/evaluate_evo_range_0_60.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/evaluate_evo_range_0_60.py)；115 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 12 行](C:/work/ls4t/cases/msg/assessment/evaluate_evo_range_0_60.py:12)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/export_monthly_hour_compatible.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/export_monthly_hour_compatible.py)；229 行，5 个定义。

### `read_json_retry`

```python
read_json_retry(path)
```

定义类型：function；[源码第 32 行](C:/work/ls4t/cases/msg/assessment/export_monthly_hour_compatible.py:32)。

无 docstring；算法解释见人工审阅章节。

### `pid_exists`

```python
pid_exists(pid)
```

定义类型：function；[源码第 42 行](C:/work/ls4t/cases/msg/assessment/export_monthly_hour_compatible.py:42)。

无 docstring；算法解释见人工审阅章节。

### `layout`

```python
layout(reference)
```

定义类型：function；[源码第 61 行](C:/work/ls4t/cases/msg/assessment/export_monthly_hour_compatible.py:61)。

无 docstring；算法解释见人工审阅章节。

### `export_one`

```python
export_one(source, group, destination, schema, reference)
```

定义类型：function；[源码第 71 行](C:/work/ls4t/cases/msg/assessment/export_monthly_hour_compatible.py:71)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 135 行](C:/work/ls4t/cases/msg/assessment/export_monthly_hour_compatible.py:135)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/finalize_evo_parameter_search.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/finalize_evo_parameter_search.py)；148 行，4 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/finalize_evo_parameter_search.py:11)。

无 docstring；算法解释见人工审阅章节。

### `main.get`

```python
main.get(label)
```

定义类型：nested；[源码第 18 行](C:/work/ls4t/cases/msg/assessment/finalize_evo_parameter_search.py:18)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:111](C:/work/ls4t/tests/test_africa_download.py:111)

### `main.m`

```python
main.m(label, split)
```

定义类型：nested；[源码第 28 行](C:/work/ls4t/cases/msg/assessment/finalize_evo_parameter_search.py:28)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:239](C:/work/ls4t/tests/test_africa_download.py:239)、[tests/test_beijing_building_structure.py:10](C:/work/ls4t/tests/test_beijing_building_structure.py:10)、[tests/test_beijing_lai_8day.py:14](C:/work/ls4t/tests/test_beijing_lai_8day.py:14)、[tests/test_msg_aatsr_comparison.py:17](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:17)、[tests/test_slstr_case_dependencies.py:142](C:/work/ls4t/tests/test_slstr_case_dependencies.py:142)、[tests/test_south_america_monthly_components.py:11](C:/work/ls4t/tests/test_south_america_monthly_components.py:11)

### `main.row`

```python
main.row(label, title, split)
```

定义类型：nested；[源码第 29 行](C:/work/ls4t/cases/msg/assessment/finalize_evo_parameter_search.py:29)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:55](C:/work/ls4t/tests/test_africa_download.py:55)、[tests/test_retrieval.py:61](C:/work/ls4t/tests/test_retrieval.py:61)

## cases/msg/assessment/finalize_manuscript_validation.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/finalize_manuscript_validation.py)；35 行，1 个定义。

### `picture_hashes`

```python
picture_hashes(doc)
```

定义类型：function；[源码第 18 行](C:/work/ls4t/cases/msg/assessment/finalize_manuscript_validation.py:18)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/finalize_parameter_argument.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/finalize_parameter_argument.py)；88 行，1 个定义。

### `fixed_savefig`

```python
fixed_savefig(fig, *args, **kwargs)
```

定义类型：function；[源码第 54 行](C:/work/ls4t/cases/msg/assessment/finalize_parameter_argument.py:54)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/icos_time.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/icos_time.py)；56 行，4 个定义。

### `sha256_file`

```python
sha256_file(path)
```

定义类型：function；[源码第 10 行](C:/work/ls4t/cases/msg/assessment/icos_time.py:10)。

无 docstring；算法解释见人工审阅章节。

### `source_contract`

```python
source_contract(path)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/msg/assessment/icos_time.py:17)。

无 docstring；算法解释见人工审阅章节。

### `local_interval_start_utc`

```python
local_interval_start_utc(values, offset_hours)
```

定义类型：function；[源码第 37 行](C:/work/ls4t/cases/msg/assessment/icos_time.py:37)。

无 docstring；算法解释见人工审阅章节。

### `clean_ground`

```python
clean_ground(path)
```

定义类型：function；[源码第 42 行](C:/work/ls4t/cases/msg/assessment/icos_time.py:42)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_compatible/audit_geometry.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_geometry.py)；115 行，6 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 16 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_geometry.py:16)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `cv`

```python
cv(value)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_geometry.py:22)。

无 docstring；算法解释见人工审阅章节。

### `source_path`

```python
source_path(stamp, view, projected=False)
```

定义类型：function；[源码第 28 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_geometry.py:28)。

无 docstring；算法解释见人工审阅章节。

### `metadata`

```python
metadata(path)
```

定义类型：function；[源码第 33 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_geometry.py:33)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:57](C:/work/ls4t/tests/test_africa_download.py:57)、[tests/test_dual_thermal_sensors.py:53](C:/work/ls4t/tests/test_dual_thermal_sensors.py:53)、[tests/test_normalization_raster.py:38](C:/work/ls4t/tests/test_normalization_raster.py:38)、[tests/test_products.py:10](C:/work/ls4t/tests/test_products.py:10)、[tests/test_slstr_products.py:95](C:/work/ls4t/tests/test_slstr_products.py:95)、[tests/test_south_america_native_recovery.py:65](C:/work/ls4t/tests/test_south_america_native_recovery.py:65)、[tests/test_spatial_modes.py:39](C:/work/ls4t/tests/test_spatial_modes.py:39)

### `summary`

```python
summary(pred, observed)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_geometry.py:38)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:97](C:/work/ls4t/tests/test_msg_evo_sample.py:97)、[tests/test_slstr_evo_sample.py:35](C:/work/ls4t/tests/test_slstr_evo_sample.py:35)

### `main`

```python
main()
```

定义类型：function；[源码第 43 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_geometry.py:43)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_compatible/audit_msg_ls4t.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py)；278 行，10 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:20)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `decode_lst`

```python
decode_lst(raw, nodata)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:26)。

无 docstring；算法解释见人工审阅章节。

### `check_grid`

```python
check_grid(tif, grid)
```

定义类型：function；[源码第 34 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:34)。

无 docstring；算法解释见人工审阅章节。

### `check_commit`

```python
check_commit(hdf, tif, identity)
```

定义类型：function；[源码第 41 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:41)。

无 docstring；算法解释见人工审阅章节。

### `sample_ancillary`

```python
sample_ancillary(path, lat, lon)
```

定义类型：function；[源码第 47 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:47)。

无 docstring；算法解释见人工审阅章节。

### `scalar_pixel`

```python
scalar_pixel(stamp, y, x, identity, geometry, input_files, scalar)
```

定义类型：function；[源码第 66 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:66)。

无 docstring；算法解释见人工审阅章节。

### `audit_scene`

```python
audit_scene(root, stamp, identity)
```

定义类型：function；[源码第 115 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:115)。

无 docstring；算法解释见人工审阅章节。

### `audit_month`

```python
audit_month(root, stamp, identity, pixels)
```

定义类型：function；[源码第 169 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:169)。

无 docstring；算法解释见人工审阅章节。

### `audit_actual_pixels`

```python
audit_actual_pixels(root, stamp, identity)
```

定义类型：function；[源码第 221 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:221)。

Supplement the root's whole-product audit with independent scalar replay.

### `main`

```python
main()
```

定义类型：function；[源码第 250 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_msg_ls4t.py:250)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_compatible/audit_output.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_output.py)；135 行，4 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 13 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_output.py:13)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `grid_check`

```python
grid_check(ds, reference)
```

定义类型：function；[源码第 21 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_output.py:21)。

无 docstring；算法解释见人工审阅章节。

### `commit_check`

```python
commit_check(path)
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_output.py:27)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 35 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/audit_output.py:35)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_compatible/msg_view_geometry.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py)；127 行，8 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:22)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `native_path`

```python
native_path(stamp, view)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:26)。

无 docstring；算法解释见人工审阅章节。

### `_decode`

```python
_decode(value)
```

定义类型：function；[源码第 32 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:32)。

无 docstring；算法解释见人工审阅章节。

### `read_position`

```python
read_position(stamp, view)
```

定义类型：function；[源码第 40 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:40)。

无 docstring；算法解释见人工审阅章节。

### `look_angles`

```python
look_angles(lat, lon, satellite_lat, satellite_lon, radius=SATELLITE_GEOCENTRIC_RADIUS_M)
```

定义类型：function；[源码第 60 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:60)。

WGS84 geodetic ground -> ECEF -> local ENU; azimuth N=0,E=90.  Satellite latitude is the geocentric sub-satellite direction supplied by the source. Ground height is zero. The orbit radius is explicit, not fitted. Azimuth looks from the ground towards the satel

### `_validate_plan`

```python
_validate_plan(plan)
```

定义类型：function；[源码第 87 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:87)。

无 docstring；算法解释见人工审阅章节。

### `geometry_metadata`

```python
geometry_metadata(stamp, plan)
```

定义类型：function；[源码第 99 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:99)。

Cheap per-scene eligibility check; does not allocate full-grid angles.

### `view_geometry`

```python
view_geometry(stamp, lat, lon, base_static, plan)
```

定义类型：function；[源码第 114 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/msg_view_geometry.py:114)。

Producer interface; retain original pixel convention supplied by caller.  base_static is accepted for interface compatibility; its old view-angle fields are intentionally excluded from the returned scene-specific angles.

## cases/msg/assessment/msg_compatible/preflight_msg_ls4t.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_compatible/preflight_msg_ls4t.py)；108 行，3 个定义。

### `months`

```python
months(start, end)
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/preflight_msg_ls4t.py:25)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:96](C:/work/ls4t/tests/test_africa_download.py:96)、[tests/test_dual_thermal_sensors.py:154](C:/work/ls4t/tests/test_dual_thermal_sensors.py:154)

### `inspect_grid`

```python
inspect_grid(path, reference)
```

定义类型：function；[源码第 32 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/preflight_msg_ls4t.py:32)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 51 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/preflight_msg_ls4t.py:51)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_compatible/produce_msg_ls4t.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py)；889 行，40 个定义。

### `json_text`

```python
json_text(value)
```

定义类型：function；[源码第 76 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:76)。

无 docstring；算法解释见人工审阅章节。

### `hash_object`

```python
hash_object(value)
```

定义类型：function；[源码第 80 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:80)。

无 docstring；算法解释见人工审阅章节。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 87 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:87)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `atomic_json`

```python
atomic_json(path, value)
```

定义类型：function；[源码第 95 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:95)。

无 docstring；算法解释见人工审阅章节。

### `append_json`

```python
append_json(path, value)
```

定义类型：function；[源码第 103 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:103)。

无 docstring；算法解释见人工审阅章节。

### `now`

```python
now()
```

定义类型：function；[源码第 109 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:109)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:96](C:/work/ls4t/tests/test_africa_download.py:96)

### `planck`

```python
planck(t)
```

定义类型：function；[源码第 113 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:113)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inverse`

```python
inverse(r)
```

定义类型：function；[源码第 118 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:118)。

无 docstring；算法解释见人工审阅章节。

### `hotspot`

```python
hotspot(lai, vza, sza, vsa)
```

定义类型：function；[源码第 123 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:123)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:23](C:/work/ls4t/tests/test_slstr_case_dependencies.py:23)

### `retrieve`

```python
retrieve(d)
```

定义类型：function；[源码第 133 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:133)。

Legacy scalar-center-equivalent two 5x5 stages and center joint solve.

同名测试引用：[tests/test_retrieval.py:14](C:/work/ls4t/tests/test_retrieval.py:14)

### `retrieve.total`

```python
retrieve.total(a)
```

定义类型：nested；[源码第 152 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:152)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:34](C:/work/ls4t/tests/test_south_america_monthly_components.py:34)

### `retrieve.solve`

```python
retrieve.solve(aa, ab, bb, u, v)
```

定义类型：nested；[源码第 157 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:157)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:73](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:73)

### `decode_lst`

```python
decode_lst(raw, nodata=None)
```

定义类型：function；[源码第 204 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:204)。

无 docstring；算法解释见人工审阅章节。

### `decode_lai`

```python
decode_lai(raw, nodata=None)
```

定义类型：function；[源码第 215 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:215)。

无 docstring；算法解释见人工审阅章节。

### `paths`

```python
paths(stamp, input_root=Path('E:/'))
```

定义类型：function；[源码第 224 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:224)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:90](C:/work/ls4t/tests/test_south_america_monthly_components.py:90)

### `static_paths`

```python
static_paths(input_root)
```

定义类型：function；[源码第 234 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:234)。

无 docstring；算法解释见人工审阅章节。

### `grid_info`

```python
grid_info(input_root)
```

定义类型：function；[源码第 243 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:243)。

无 docstring；算法解释见人工审阅章节。

### `grid_check`

```python
grid_check(dataset, grid)
```

定义类型：function；[源码第 255 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:255)。

无 docstring；算法解释见人工审阅章节。

### `sample_ancillary`

```python
sample_ancillary(path, lat, lon)
```

定义类型：function；[源码第 267 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:267)。

Legacy nearest-cell truncation, with each ancillary's own declared CRS.

### `load_static`

```python
load_static(input_root, grid)
```

定义类型：function；[源码第 298 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:298)。

无 docstring；算法解释见人工审阅章节。

### `file_manifest`

```python
file_manifest(files)
```

定义类型：function；[源码第 330 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:330)。

无 docstring；算法解释见人工审阅章节。

### `load_geometry_module`

```python
load_geometry_module(path)
```

定义类型：function；[源码第 334 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:334)。

无 docstring；算法解释见人工审阅章节。

### `build_identity`

```python
build_identity(args, grid)
```

定义类型：function；[源码第 346 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:346)。

无 docstring；算法解释见人工审阅章节。

### `assert_current_identity`

```python
assert_current_identity(identity, config)
```

定义类型：function；[源码第 371 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:371)。

无 docstring；算法解释见人工审阅章节。

### `worker_init`

```python
worker_init(config, identity, plan)
```

定义类型：function；[源码第 379 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:379)。

无 docstring；算法解释见人工审阅章节。

### `instant_path`

```python
instant_path(root, stamp)
```

定义类型：function；[源码第 391 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:391)。

无 docstring；算法解释见人工审阅章节。

### `scene_tif_path`

```python
scene_tif_path(root, stamp)
```

定义类型：function；[源码第 395 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:395)。

无 docstring；算法解释见人工审阅章节。

### `attrs`

```python
attrs(file, identity)
```

定义类型：function；[源码第 399 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:399)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:178](C:/work/ls4t/tests/test_msg_case_dependencies.py:178)、[tests/test_south_america_components.py:125](C:/work/ls4t/tests/test_south_america_components.py:125)

### `data_attrs`

```python
data_attrs(dataset, identity, encoding='dn')
```

定义类型：function；[源码第 414 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:414)。

无 docstring；算法解释见人工审阅章节。

### `create_tif`

```python
create_tif(path, identity, dtype, timestamp, scale, nodata)
```

定义类型：function；[源码第 421 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:421)。

无 docstring；算法解释见人工审阅章节。

### `commit_path`

```python
commit_path(hdf)
```

定义类型：function；[源码第 441 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:441)。

无 docstring；算法解释见人工审阅章节。

### `check_resume`

```python
check_resume(hdf, tif, identity, signature, allow_source_refresh=False)
```

定义类型：function；[源码第 445 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:445)。

无 docstring；算法解释见人工审阅章节。

### `commit_products`

```python
commit_products(hdf_temp, tif_temp, hdf, tif, identity, signature, record)
```

定义类型：function；[源码第 475 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:475)。

无 docstring；算法解释见人工审阅章节。

### `produce_scene`

```python
produce_scene(stamp)
```

定义类型：function；[源码第 484 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:484)。

无 docstring；算法解释见人工审阅章节。

### `scene_job`

```python
scene_job(stamp)
```

定义类型：function；[源码第 567 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:567)。

无 docstring；算法解释见人工审阅章节。

### `monthly`

```python
monthly(root, month, hour, files, expected, omissions, identity, tile_rows=256)
```

定义类型：function；[源码第 576 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:576)。

MSG-compatible DN means; GeoTIFF stores direct Kelvin float32 values.

同名测试引用：[tests/test_south_america_monthly_components.py:1](C:/work/ls4t/tests/test_south_america_monthly_components.py:1)

### `inventory`

```python
inventory(args)
```

定义类型：function；[源码第 666 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:666)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:39](C:/work/ls4t/tests/test_south_america_components.py:39)

### `production_lock`

```python
production_lock(root)
```

定义类型：function；[源码第 699 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:699)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 717 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:717)。

无 docstring；算法解释见人工审阅章节。

### `main.publish`

```python
main.publish()
```

定义类型：nested；[源码第 773 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/produce_msg_ls4t.py:773)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_compatible/validate_view_geometry.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_compatible/validate_view_geometry.py)；45 行，2 个定义。

### `read`

```python
read(path, key)
```

定义类型：function；[源码第 10 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/validate_view_geometry.py:10)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:262](C:/work/ls4t/tests/test_africa_download.py:262)

### `main`

```python
main()
```

定义类型：function；[源码第 19 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/validate_view_geometry.py:19)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_compatible/verify_msg_ls4t.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_msg_ls4t.py)；176 行，8 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_msg_ls4t.py:20)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `radiation`

```python
radiation(temperature)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_msg_ls4t.py:22)。

无 docstring；算法解释见人工审阅章节。

### `temperature`

```python
temperature(radiance)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_msg_ls4t.py:26)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:97](C:/work/ls4t/tests/test_msg_evo_sample.py:97)、[tests/test_normalization.py:29](C:/work/ls4t/tests/test_normalization.py:29)、[tests/test_physics.py:7](C:/work/ls4t/tests/test_physics.py:7)、[tests/test_south_america_native_recovery.py:63](C:/work/ls4t/tests/test_south_america_native_recovery.py:63)

### `load_scalar`

```python
load_scalar()
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_msg_ls4t.py:30)。

无 docstring；算法解释见人工审阅章节。

### `oracle`

```python
oracle(d, scalar)
```

定义类型：function；[源码第 41 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_msg_ls4t.py:41)。

无 docstring；算法解释见人工审阅章节。

### `copy_case`

```python
copy_case(d)
```

定义类型：function；[源码第 84 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_msg_ls4t.py:84)。

无 docstring；算法解释见人工审阅章节。

### `variants`

```python
variants(d, index)
```

定义类型：function；[源码第 86 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_msg_ls4t.py:86)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 108 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_msg_ls4t.py:108)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_compatible/verify_product_schema.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_product_schema.py)；116 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/msg_compatible/verify_product_schema.py:11)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_declared/accept_declared.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_declared/accept_declared.py)；47 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 9 行](C:/work/ls4t/cases/msg/assessment/msg_declared/accept_declared.py:9)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_declared/audit_declared_output.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py)；311 行，12 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:22)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `declaration_source`

```python
declaration_source(path)
```

定义类型：function；[源码第 29 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:29)。

Read each frozen static declaration once, never treat it as ephemeris.

### `check_declared_position`

```python
check_declared_position(stamp, view, position, identity)
```

定义类型：function；[源码第 40 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:40)。

无 docstring；算法解释见人工审阅章节。

### `decode_lst`

```python
decode_lst(raw, nodata)
```

定义类型：function；[源码第 55 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:55)。

无 docstring；算法解释见人工审阅章节。

### `check_grid`

```python
check_grid(tif, grid)
```

定义类型：function；[源码第 63 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:63)。

无 docstring；算法解释见人工审阅章节。

### `check_commit`

```python
check_commit(hdf, tif, identity)
```

定义类型：function；[源码第 70 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:70)。

无 docstring；算法解释见人工审阅章节。

### `sample_ancillary`

```python
sample_ancillary(path, lat, lon)
```

定义类型：function；[源码第 76 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:76)。

无 docstring；算法解释见人工审阅章节。

### `scalar_pixel`

```python
scalar_pixel(stamp, y, x, identity, geometry, input_files, scalar)
```

定义类型：function；[源码第 95 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:95)。

无 docstring；算法解释见人工审阅章节。

### `audit_scene`

```python
audit_scene(root, stamp, identity)
```

定义类型：function；[源码第 141 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:141)。

无 docstring；算法解释见人工审阅章节。

### `audit_month`

```python
audit_month(root, stamp, identity, pixels)
```

定义类型：function；[源码第 195 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:195)。

无 docstring；算法解释见人工审阅章节。

### `audit_actual_pixels`

```python
audit_actual_pixels(root, stamp, identity)
```

定义类型：function；[源码第 251 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:251)。

Supplement the root's whole-product audit with independent scalar replay.

### `main`

```python
main()
```

定义类型：function；[源码第 280 行](C:/work/ls4t/cases/msg/assessment/msg_declared/audit_declared_output.py:280)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_declared/msg_view_geometry.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_declared/msg_view_geometry.py)；82 行，4 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/msg_declared/msg_view_geometry.py:22)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `look_angles`

```python
look_angles(lat, lon, satellite_lat, satellite_lon, radius=SATELLITE_GEOCENTRIC_RADIUS_M)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/msg_declared/msg_view_geometry.py:26)。

无 docstring；算法解释见人工审阅章节。

### `geometry_metadata`

```python
geometry_metadata(stamp, plan)
```

定义类型：function；[源码第 49 行](C:/work/ls4t/cases/msg/assessment/msg_declared/msg_view_geometry.py:49)。

无 docstring；算法解释见人工审阅章节。

### `view_geometry`

```python
view_geometry(stamp, lat, lon, base_static, plan)
```

定义类型：function；[源码第 73 行](C:/work/ls4t/cases/msg/assessment/msg_declared/msg_view_geometry.py:73)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_declared/produce_msg_ls4t.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py)；889 行，40 个定义。

### `json_text`

```python
json_text(value)
```

定义类型：function；[源码第 76 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:76)。

无 docstring；算法解释见人工审阅章节。

### `hash_object`

```python
hash_object(value)
```

定义类型：function；[源码第 80 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:80)。

无 docstring；算法解释见人工审阅章节。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 87 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:87)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `atomic_json`

```python
atomic_json(path, value)
```

定义类型：function；[源码第 95 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:95)。

无 docstring；算法解释见人工审阅章节。

### `append_json`

```python
append_json(path, value)
```

定义类型：function；[源码第 103 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:103)。

无 docstring；算法解释见人工审阅章节。

### `now`

```python
now()
```

定义类型：function；[源码第 109 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:109)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:96](C:/work/ls4t/tests/test_africa_download.py:96)

### `planck`

```python
planck(t)
```

定义类型：function；[源码第 113 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:113)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inverse`

```python
inverse(r)
```

定义类型：function；[源码第 118 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:118)。

无 docstring；算法解释见人工审阅章节。

### `hotspot`

```python
hotspot(lai, vza, sza, vsa)
```

定义类型：function；[源码第 123 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:123)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:23](C:/work/ls4t/tests/test_slstr_case_dependencies.py:23)

### `retrieve`

```python
retrieve(d)
```

定义类型：function；[源码第 133 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:133)。

Legacy scalar-center-equivalent two 5x5 stages and center joint solve.

同名测试引用：[tests/test_retrieval.py:14](C:/work/ls4t/tests/test_retrieval.py:14)

### `retrieve.total`

```python
retrieve.total(a)
```

定义类型：nested；[源码第 152 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:152)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:34](C:/work/ls4t/tests/test_south_america_monthly_components.py:34)

### `retrieve.solve`

```python
retrieve.solve(aa, ab, bb, u, v)
```

定义类型：nested；[源码第 157 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:157)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:73](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:73)

### `decode_lst`

```python
decode_lst(raw, nodata=None)
```

定义类型：function；[源码第 204 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:204)。

无 docstring；算法解释见人工审阅章节。

### `decode_lai`

```python
decode_lai(raw, nodata=None)
```

定义类型：function；[源码第 215 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:215)。

无 docstring；算法解释见人工审阅章节。

### `paths`

```python
paths(stamp, input_root=Path('E:/'))
```

定义类型：function；[源码第 224 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:224)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:90](C:/work/ls4t/tests/test_south_america_monthly_components.py:90)

### `static_paths`

```python
static_paths(input_root)
```

定义类型：function；[源码第 234 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:234)。

无 docstring；算法解释见人工审阅章节。

### `grid_info`

```python
grid_info(input_root)
```

定义类型：function；[源码第 243 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:243)。

无 docstring；算法解释见人工审阅章节。

### `grid_check`

```python
grid_check(dataset, grid)
```

定义类型：function；[源码第 255 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:255)。

无 docstring；算法解释见人工审阅章节。

### `sample_ancillary`

```python
sample_ancillary(path, lat, lon)
```

定义类型：function；[源码第 267 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:267)。

Legacy nearest-cell truncation, with each ancillary's own declared CRS.

### `load_static`

```python
load_static(input_root, grid)
```

定义类型：function；[源码第 298 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:298)。

无 docstring；算法解释见人工审阅章节。

### `file_manifest`

```python
file_manifest(files)
```

定义类型：function；[源码第 330 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:330)。

无 docstring；算法解释见人工审阅章节。

### `load_geometry_module`

```python
load_geometry_module(path)
```

定义类型：function；[源码第 334 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:334)。

无 docstring；算法解释见人工审阅章节。

### `build_identity`

```python
build_identity(args, grid)
```

定义类型：function；[源码第 346 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:346)。

无 docstring；算法解释见人工审阅章节。

### `assert_current_identity`

```python
assert_current_identity(identity, config)
```

定义类型：function；[源码第 371 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:371)。

无 docstring；算法解释见人工审阅章节。

### `worker_init`

```python
worker_init(config, identity, plan)
```

定义类型：function；[源码第 379 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:379)。

无 docstring；算法解释见人工审阅章节。

### `instant_path`

```python
instant_path(root, stamp)
```

定义类型：function；[源码第 391 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:391)。

无 docstring；算法解释见人工审阅章节。

### `scene_tif_path`

```python
scene_tif_path(root, stamp)
```

定义类型：function；[源码第 395 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:395)。

无 docstring；算法解释见人工审阅章节。

### `attrs`

```python
attrs(file, identity)
```

定义类型：function；[源码第 399 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:399)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:178](C:/work/ls4t/tests/test_msg_case_dependencies.py:178)、[tests/test_south_america_components.py:125](C:/work/ls4t/tests/test_south_america_components.py:125)

### `data_attrs`

```python
data_attrs(dataset, identity, encoding='dn')
```

定义类型：function；[源码第 414 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:414)。

无 docstring；算法解释见人工审阅章节。

### `create_tif`

```python
create_tif(path, identity, dtype, timestamp, scale, nodata)
```

定义类型：function；[源码第 421 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:421)。

无 docstring；算法解释见人工审阅章节。

### `commit_path`

```python
commit_path(hdf)
```

定义类型：function；[源码第 441 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:441)。

无 docstring；算法解释见人工审阅章节。

### `check_resume`

```python
check_resume(hdf, tif, identity, signature, allow_source_refresh=False)
```

定义类型：function；[源码第 445 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:445)。

无 docstring；算法解释见人工审阅章节。

### `commit_products`

```python
commit_products(hdf_temp, tif_temp, hdf, tif, identity, signature, record)
```

定义类型：function；[源码第 475 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:475)。

无 docstring；算法解释见人工审阅章节。

### `produce_scene`

```python
produce_scene(stamp)
```

定义类型：function；[源码第 484 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:484)。

无 docstring；算法解释见人工审阅章节。

### `scene_job`

```python
scene_job(stamp)
```

定义类型：function；[源码第 567 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:567)。

无 docstring；算法解释见人工审阅章节。

### `monthly`

```python
monthly(root, month, hour, files, expected, omissions, identity, tile_rows=256)
```

定义类型：function；[源码第 576 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:576)。

MSG-compatible DN means; GeoTIFF stores direct Kelvin float32 values.

同名测试引用：[tests/test_south_america_monthly_components.py:1](C:/work/ls4t/tests/test_south_america_monthly_components.py:1)

### `inventory`

```python
inventory(args)
```

定义类型：function；[源码第 666 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:666)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:39](C:/work/ls4t/tests/test_south_america_components.py:39)

### `production_lock`

```python
production_lock(root)
```

定义类型：function；[源码第 699 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:699)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 717 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:717)。

无 docstring；算法解释见人工审阅章节。

### `main.publish`

```python
main.publish()
```

定义类型：nested；[源码第 773 行](C:/work/ls4t/cases/msg/assessment/msg_declared/produce_msg_ls4t.py:773)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_declared/verify_msg_ls4t.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_msg_ls4t.py)；176 行，8 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_msg_ls4t.py:20)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `radiation`

```python
radiation(temperature)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_msg_ls4t.py:22)。

无 docstring；算法解释见人工审阅章节。

### `temperature`

```python
temperature(radiance)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_msg_ls4t.py:26)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:97](C:/work/ls4t/tests/test_msg_evo_sample.py:97)、[tests/test_normalization.py:29](C:/work/ls4t/tests/test_normalization.py:29)、[tests/test_physics.py:7](C:/work/ls4t/tests/test_physics.py:7)、[tests/test_south_america_native_recovery.py:63](C:/work/ls4t/tests/test_south_america_native_recovery.py:63)

### `load_scalar`

```python
load_scalar()
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_msg_ls4t.py:30)。

无 docstring；算法解释见人工审阅章节。

### `oracle`

```python
oracle(d, scalar)
```

定义类型：function；[源码第 41 行](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_msg_ls4t.py:41)。

无 docstring；算法解释见人工审阅章节。

### `copy_case`

```python
copy_case(d)
```

定义类型：function；[源码第 84 行](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_msg_ls4t.py:84)。

无 docstring；算法解释见人工审阅章节。

### `variants`

```python
variants(d, index)
```

定义类型：function；[源码第 86 行](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_msg_ls4t.py:86)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 108 行](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_msg_ls4t.py:108)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_declared/verify_product_schema.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_product_schema.py)；116 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/msg_declared/verify_product_schema.py:11)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/build_static_geometry.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/build_static_geometry.py)；102 行，3 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 19 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/build_static_geometry.py:19)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `build`

```python
build(reference, plan, output, tile_rows=128)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/build_static_geometry.py:23)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 91 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/build_static_geometry.py:91)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/collection_lineage.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/collection_lineage.py)；105 行，5 个定义。

### `load_registry`

```python
load_registry(plan, protocol, grid, sha, hash_object)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/collection_lineage.py:17)。

无 docstring；算法解释见人工审阅章节。

### `assert_file_identity`

```python
assert_file_identity(source, record, identity)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/collection_lineage.py:38)。

无 docstring；算法解释见人工审阅章节。

### `scene_equivalent`

```python
scene_equivalent(source, record, context, hash_object)
```

定义类型：function；[源码第 54 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/collection_lineage.py:54)。

Return false for changed inputs/selected geometry, never relabel bytes.

### `check_month_sources`

```python
check_month_sources(files, sources, records, identity)
```

定义类型：function；[源码第 81 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/collection_lineage.py:81)。

Bind legacy monthly inputs to this run's validated scene records.

### `monthly_source_identity`

```python
monthly_source_identity(source, identity)
```

定义类型：function；[源码第 101 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/collection_lineage.py:101)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/merge_collection.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/merge_collection.py)；110 行，1 个定义。

### `prepare`

```python
prepare(root, static_root, input_root)
```

定义类型：function；[源码第 14 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/merge_collection.py:14)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:175](C:/work/ls4t/tests/test_africa_download.py:175)

## cases/msg/assessment/msg_hybrid/msg_view_geometry.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py)；208 行，9 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:26)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `_decode`

```python
_decode(value)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:30)。

无 docstring；算法解释见人工审阅章节。

### `native_path`

```python
native_path(stamp, view, input_root)
```

定义类型：function；[源码第 40 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:40)。

无 docstring；算法解释见人工审阅章节。

### `_read_metadata`

```python
_read_metadata(path, stamp, expected_longitude, legacy_placeholder)
```

定义类型：function；[源码第 46 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:46)。

无 docstring；算法解释见人工审阅章节。

### `_select_position`

```python
_select_position(stamp, view, epoch, plan)
```

定义类型：function；[源码第 72 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:72)。

无 docstring；算法解释见人工审阅章节。

### `_record_metadata`

```python
_record_metadata(metadata)
```

定义类型：function；[源码第 112 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:112)。

无 docstring；算法解释见人工审阅章节。

### `geometry_metadata`

```python
geometry_metadata(stamp, plan)
```

定义类型：function；[源码第 123 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:123)。

无 docstring；算法解释见人工审阅章节。

### `look_angles`

```python
look_angles(lat, lon, satellite_lat, satellite_lon, radius=SATELLITE_GEOCENTRIC_RADIUS_M)
```

定义类型：function；[源码第 154 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:154)。

无 docstring；算法解释见人工审阅章节。

### `view_geometry`

```python
view_geometry(stamp, lat, lon, base_static, plan)
```

定义类型：function；[源码第 177 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/msg_view_geometry.py:177)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py)；957 行，42 个定义。

### `json_text`

```python
json_text(value)
```

定义类型：function；[源码第 79 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:79)。

无 docstring；算法解释见人工审阅章节。

### `hash_object`

```python
hash_object(value)
```

定义类型：function；[源码第 83 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:83)。

无 docstring；算法解释见人工审阅章节。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 90 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:90)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `atomic_json`

```python
atomic_json(path, value)
```

定义类型：function；[源码第 98 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:98)。

无 docstring；算法解释见人工审阅章节。

### `append_json`

```python
append_json(path, value)
```

定义类型：function；[源码第 106 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:106)。

无 docstring；算法解释见人工审阅章节。

### `now`

```python
now()
```

定义类型：function；[源码第 112 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:112)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:96](C:/work/ls4t/tests/test_africa_download.py:96)

### `planck`

```python
planck(t)
```

定义类型：function；[源码第 116 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:116)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inverse`

```python
inverse(r)
```

定义类型：function；[源码第 121 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:121)。

无 docstring；算法解释见人工审阅章节。

### `hotspot`

```python
hotspot(lai, vza, sza, vsa)
```

定义类型：function；[源码第 126 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:126)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:23](C:/work/ls4t/tests/test_slstr_case_dependencies.py:23)

### `retrieve`

```python
retrieve(d)
```

定义类型：function；[源码第 136 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:136)。

Legacy scalar-center-equivalent two 5x5 stages and center joint solve.

同名测试引用：[tests/test_retrieval.py:14](C:/work/ls4t/tests/test_retrieval.py:14)

### `retrieve.total`

```python
retrieve.total(a)
```

定义类型：nested；[源码第 155 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:155)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:34](C:/work/ls4t/tests/test_south_america_monthly_components.py:34)

### `retrieve.solve`

```python
retrieve.solve(aa, ab, bb, u, v)
```

定义类型：nested；[源码第 160 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:160)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:73](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:73)

### `decode_lst`

```python
decode_lst(raw, nodata=None)
```

定义类型：function；[源码第 207 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:207)。

无 docstring；算法解释见人工审阅章节。

### `decode_lai`

```python
decode_lai(raw, nodata=None)
```

定义类型：function；[源码第 218 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:218)。

无 docstring；算法解释见人工审阅章节。

### `paths`

```python
paths(stamp, input_root=Path('E:/'))
```

定义类型：function；[源码第 227 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:227)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:90](C:/work/ls4t/tests/test_south_america_monthly_components.py:90)

### `static_paths`

```python
static_paths(input_root)
```

定义类型：function；[源码第 237 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:237)。

无 docstring；算法解释见人工审阅章节。

### `grid_info`

```python
grid_info(input_root)
```

定义类型：function；[源码第 246 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:246)。

无 docstring；算法解释见人工审阅章节。

### `grid_check`

```python
grid_check(dataset, grid)
```

定义类型：function；[源码第 258 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:258)。

无 docstring；算法解释见人工审阅章节。

### `sample_ancillary`

```python
sample_ancillary(path, lat, lon)
```

定义类型：function；[源码第 270 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:270)。

Legacy nearest-cell truncation, with each ancillary's own declared CRS.

### `load_static`

```python
load_static(input_root, grid, geometry_plan)
```

定义类型：function；[源码第 301 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:301)。

无 docstring；算法解释见人工审阅章节。

### `file_manifest`

```python
file_manifest(files)
```

定义类型：function；[源码第 338 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:338)。

无 docstring；算法解释见人工审阅章节。

### `load_geometry_module`

```python
load_geometry_module(path)
```

定义类型：function；[源码第 342 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:342)。

无 docstring；算法解释见人工审阅章节。

### `build_identity`

```python
build_identity(args, grid)
```

定义类型：function；[源码第 354 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:354)。

无 docstring；算法解释见人工审阅章节。

### `assert_current_identity`

```python
assert_current_identity(identity, config)
```

定义类型：function；[源码第 390 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:390)。

无 docstring；算法解释见人工审阅章节。

### `worker_init`

```python
worker_init(config, identity, plan)
```

定义类型：function；[源码第 401 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:401)。

无 docstring；算法解释见人工审阅章节。

### `instant_path`

```python
instant_path(root, stamp)
```

定义类型：function；[源码第 413 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:413)。

无 docstring；算法解释见人工审阅章节。

### `scene_tif_path`

```python
scene_tif_path(root, stamp)
```

定义类型：function；[源码第 417 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:417)。

无 docstring；算法解释见人工审阅章节。

### `attrs`

```python
attrs(file, identity)
```

定义类型：function；[源码第 421 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:421)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:178](C:/work/ls4t/tests/test_msg_case_dependencies.py:178)、[tests/test_south_america_components.py:125](C:/work/ls4t/tests/test_south_america_components.py:125)

### `data_attrs`

```python
data_attrs(dataset, identity, encoding='dn')
```

定义类型：function；[源码第 436 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:436)。

无 docstring；算法解释见人工审阅章节。

### `create_tif`

```python
create_tif(path, identity, dtype, timestamp, scale, nodata)
```

定义类型：function；[源码第 443 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:443)。

无 docstring；算法解释见人工审阅章节。

### `commit_path`

```python
commit_path(hdf)
```

定义类型：function；[源码第 463 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:463)。

无 docstring；算法解释见人工审阅章节。

### `archive_replaced_pair`

```python
archive_replaced_pair(hdf, tif, record)
```

定义类型：function；[源码第 467 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:467)。

无 docstring；算法解释见人工审阅章节。

### `check_resume`

```python
check_resume(hdf, tif, identity, signature, allow_source_refresh=False, context=None)
```

定义类型：function；[源码第 479 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:479)。

无 docstring；算法解释见人工审阅章节。

### `commit_products`

```python
commit_products(hdf_temp, tif_temp, hdf, tif, identity, signature, record)
```

定义类型：function；[源码第 523 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:523)。

无 docstring；算法解释见人工审阅章节。

### `produce_scene`

```python
produce_scene(stamp)
```

定义类型：function；[源码第 532 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:532)。

无 docstring；算法解释见人工审阅章节。

### `scene_job`

```python
scene_job(stamp)
```

定义类型：function；[源码第 617 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:617)。

无 docstring；算法解释见人工审阅章节。

### `monthly`

```python
monthly(root, month, hour, files, expected, omissions, identity, tile_rows=256, validated_records=None)
```

定义类型：function；[源码第 626 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:626)。

MSG-compatible DN means; GeoTIFF stores direct Kelvin float32 values.

同名测试引用：[tests/test_south_america_monthly_components.py:1](C:/work/ls4t/tests/test_south_america_monthly_components.py:1)

### `inventory`

```python
inventory(args)
```

定义类型：function；[源码第 717 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:717)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:39](C:/work/ls4t/tests/test_south_america_components.py:39)

### `production_lock`

```python
production_lock(root)
```

定义类型：function；[源码第 750 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:750)。

无 docstring；算法解释见人工审阅章节。

### `assert_code_review`

```python
assert_code_review(path, geometry_module, geometry_plan)
```

定义类型：function；[源码第 768 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:768)。

Review applies only to the exact producer/helper/plan bytes reviewed.

### `main`

```python
main()
```

定义类型：function；[源码第 780 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:780)。

无 docstring；算法解释见人工审阅章节。

### `main.publish`

```python
main.publish()
```

定义类型：nested；[源码第 839 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/produce_msg_ls4t.py:839)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/resume_preflight.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/resume_preflight.py)；33 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/resume_preflight.py:11)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py)；337 行，12 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:25)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `canonical_functions`

```python
canonical_functions(path)
```

定义类型：function；[源码第 33 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:33)。

无 docstring；算法解释见人工审阅章节。

### `independent_angles`

```python
independent_angles(latitude, longitude, orbit_latitude, orbit_longitude)
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:39)。

Analytic ENU components, independent of the helper's ECEF subtraction.

### `angle_error`

```python
angle_error(actual, expected)
```

定义类型：function；[源码第 58 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:58)。

无 docstring；算法解释见人工审阅章节。

### `audit_cache`

```python
audit_cache(plan, hashes)
```

定义类型：function；[源码第 62 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:62)。

无 docstring；算法解释见人工审阅章节。

### `audit_core`

```python
audit_core()
```

定义类型：function；[源码第 126 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:126)。

无 docstring；算法解释见人工审阅章节。

### `audit_core.temperature_body`

```python
audit_core.temperature_body(function)
```

定义类型：nested；[源码第 139 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:139)。

无 docstring；算法解释见人工审阅章节。

### `audit_core.NormalizeMonthlyProvenance.visit_Expr`

```python
audit_core.NormalizeMonthlyProvenance.visit_Expr(self, node)
```

定义类型：method；[源码第 153 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:153)。

无 docstring；算法解释见人工审阅章节。

### `audit_core.NormalizeMonthlyProvenance.visit_If`

```python
audit_core.NormalizeMonthlyProvenance.visit_If(self, node)
```

定义类型：method；[源码第 157 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:157)。

无 docstring；算法解释见人工审阅章节。

### `audit_positions`

```python
audit_positions(plan)
```

定义类型：function；[源码第 176 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:176)。

无 docstring；算法解释见人工审阅章节。

### `audit_guards`

```python
audit_guards(hashes)
```

定义类型：function；[源码第 214 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:214)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 274 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_hybrid_implementation.py:274)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/review_legacy_reuse_evidence.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_legacy_reuse_evidence.py)；71 行，2 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_legacy_reuse_evidence.py:15)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `main`

```python
main()
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_legacy_reuse_evidence.py:23)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/review_lineage_fixtures.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_lineage_fixtures.py)；215 行，5 个定义。

### `rejected`

```python
rejected(call, expected=RuntimeError)
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_lineage_fixtures.py:20)。

无 docstring；算法解释见人工审阅章节。

### `geometry`

```python
geometry(stamp, mode)
```

定义类型：function；[源码第 28 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_lineage_fixtures.py:28)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:15](C:/work/ls4t/tests/test_africa_download.py:15)、[tests/test_beijing_building_structure.py:19](C:/work/ls4t/tests/test_beijing_building_structure.py:19)、[tests/test_kernel_models.py:1](C:/work/ls4t/tests/test_kernel_models.py:1)、[tests/test_south_america_remaining.py:1](C:/work/ls4t/tests/test_south_america_remaining.py:1)

### `selected`

```python
selected(old, mode)
```

定义类型：function；[源码第 42 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_lineage_fixtures.py:42)。

无 docstring；算法解释见人工审阅章节。

### `write_scene`

```python
write_scene(root, stamp, identity, encoded, old_geometry)
```

定义类型：function；[源码第 51 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_lineage_fixtures.py:51)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 78 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/review_lineage_fixtures.py:78)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/verify_hybrid_geometry.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_hybrid_geometry.py)；119 行，2 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_hybrid_geometry.py:15)。

无 docstring；算法解释见人工审阅章节。

### `main.write`

```python
main.write(view, latitude, longitude, acquisition=stamp, projection=None)
```

定义类型：nested；[源码第 39 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_hybrid_geometry.py:39)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:96](C:/work/ls4t/tests/test_south_america_components.py:96)、[tests/test_south_america_monthly_components.py:108](C:/work/ls4t/tests/test_south_america_monthly_components.py:108)

## cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py)；176 行，8 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py:20)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `radiation`

```python
radiation(temperature)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py:22)。

无 docstring；算法解释见人工审阅章节。

### `temperature`

```python
temperature(radiance)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py:26)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:97](C:/work/ls4t/tests/test_msg_evo_sample.py:97)、[tests/test_normalization.py:29](C:/work/ls4t/tests/test_normalization.py:29)、[tests/test_physics.py:7](C:/work/ls4t/tests/test_physics.py:7)、[tests/test_south_america_native_recovery.py:63](C:/work/ls4t/tests/test_south_america_native_recovery.py:63)

### `load_scalar`

```python
load_scalar()
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py:30)。

无 docstring；算法解释见人工审阅章节。

### `oracle`

```python
oracle(d, scalar)
```

定义类型：function；[源码第 41 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py:41)。

无 docstring；算法解释见人工审阅章节。

### `copy_case`

```python
copy_case(d)
```

定义类型：function；[源码第 84 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py:84)。

无 docstring；算法解释见人工审阅章节。

### `variants`

```python
variants(d, index)
```

定义类型：function；[源码第 86 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py:86)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 108 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_msg_ls4t.py:108)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_hybrid/verify_product_schema.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_product_schema.py)；117 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/msg_hybrid/verify_product_schema.py:11)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/msg_monthly_composites.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py)；392 行，12 个定义。

### `now`

```python
now()
```

定义类型：function；[源码第 53 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:53)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:96](C:/work/ls4t/tests/test_africa_download.py:96)

### `atomic_json`

```python
atomic_json(path, data)
```

定义类型：function；[源码第 57 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:57)。

无 docstring；算法解释见人工审阅章节。

### `inventory`

```python
inventory(input_root, output_root)
```

定义类型：function；[源码第 73 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:73)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:39](C:/work/ls4t/tests/test_south_america_components.py:39)

### `signature`

```python
signature(sources)
```

定义类型：function；[源码第 118 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:118)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:131](C:/work/ls4t/tests/test_flat_structure.py:131)

### `load_source`

```python
load_source(path, collection)
```

定义类型：function；[源码第 122 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:122)。

无 docstring；算法解释见人工审阅章节。

### `grid_matches`

```python
grid_matches(left, right)
```

定义类型：function；[源码第 151 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:151)。

无 docstring；算法解释见人工审阅章节。

### `Accumulator.__init__`

```python
Accumulator.__init__(self, shape, bands)
```

定义类型：method；[源码第 158 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:158)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:116](C:/work/ls4t/tests/test_africa_download.py:116)、[tests/test_stream_era5.py:16](C:/work/ls4t/tests/test_stream_era5.py:16)

### `Accumulator.add`

```python
Accumulator.add(self, value, valid, stamp)
```

定义类型：method；[源码第 163 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:163)。

无 docstring；算法解释见人工审阅章节。

### `process_job`

```python
process_job(key, sources, outpath, update=None)
```

定义类型：function；[源码第 169 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:169)。

无 docstring；算法解释见人工审阅章节。

### `verify_output`

```python
verify_output(path, positions=None)
```

定义类型：function；[源码第 254 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:254)。

Independent scalar reconstruction, without using the accumulator code.

### `main`

```python
main()
```

定义类型：function；[源码第 312 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:312)。

无 docstring；算法解释见人工审阅章节。

### `main.update`

```python
main.update(done, total, stamp)
```

定义类型：nested；[源码第 360 行](C:/work/ls4t/cases/msg/assessment/msg_monthly_composites.py:360)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/parameter_argument_monthly_hour.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py)；330 行，10 个定义。

### `sha`

```python
sha(p)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:22)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `js`

```python
js(name, value)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:23)。

无 docstring；算法解释见人工审阅章节。

### `md`

```python
md(df)
```

定义类型：function；[源码第 24 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:24)。

无 docstring；算法解释见人工审阅章节。

### `design`

```python
design()
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:30)。

无 docstring；算法解释见人工审阅章节。

### `design.add`

```python
design.add(name, c)
```

定义类型：nested；[源码第 32 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:32)。

无 docstring；算法解释见人工审阅章节。

### `scalar_window_check`

```python
scalar_window_check(data, pre, c)
```

定义类型：function；[源码第 48 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:48)。

无 docstring；算法解释见人工审阅章节。

### `scalar_window_check.fit`

```python
scalar_window_check.fit(size, stage, first=0.0)
```

定义类型：nested；[源码第 63 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:63)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:10](C:/work/ls4t/tests/test_annual_cycle.py:10)、[tests/test_kernel_models.py:39](C:/work/ls4t/tests/test_kernel_models.py:39)、[tests/test_multisource_normalization.py:15](C:/work/ls4t/tests/test_multisource_normalization.py:15)

### `main`

```python
main()
```

定义类型：function；[源码第 79 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:79)。

无 docstring；算法解释见人工审阅章节。

### `render`

```python
render(summary, coverage, members, configs)
```

定义类型：function；[源码第 206 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:206)。

无 docstring；算法解释见人工审阅章节。

### `report`

```python
report(summary, coverage, members, configs)
```

定义类型：function；[源码第 248 行](C:/work/ls4t/cases/msg/assessment/parameter_argument_monthly_hour.py:248)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:62](C:/work/ls4t/tests/test_africa_download.py:62)、[tests/test_kernel_atc_case.py:19](C:/work/ls4t/tests/test_kernel_atc_case.py:19)、[tests/test_south_america_components.py:83](C:/work/ls4t/tests/test_south_america_components.py:83)、[tests/test_south_america_remaining.py:36](C:/work/ls4t/tests/test_south_america_remaining.py:36)

## cases/msg/assessment/prepare_manuscript_validation.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/prepare_manuscript_validation.py)；155 行，4 个定义。

### `agg`

```python
agg(a)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/msg/assessment/prepare_manuscript_validation.py:17)。

无 docstring；算法解释见人工审阅章节。

### `metrics`

```python
metrics(g)
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/prepare_manuscript_validation.py:22)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:71](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:71)

### `savefig`

```python
savefig(fig, name)
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/msg/assessment/prepare_manuscript_validation.py:27)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 32 行](C:/work/ls4t/cases/msg/assessment/prepare_manuscript_validation.py:32)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/produce_msg_5x5.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py)；356 行，16 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 46 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:46)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `atomic_json`

```python
atomic_json(path, obj)
```

定义类型：function；[源码第 53 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:53)。

无 docstring；算法解释见人工审阅章节。

### `planck`

```python
planck(t)
```

定义类型：function；[源码第 60 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:60)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inverse`

```python
inverse(r)
```

定义类型：function；[源码第 65 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:65)。

无 docstring；算法解释见人工审阅章节。

### `hotspot`

```python
hotspot(lai, vza, sza, vsa)
```

定义类型：function；[源码第 70 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:70)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_slstr_case_dependencies.py:23](C:/work/ls4t/tests/test_slstr_case_dependencies.py:23)

### `retrieve`

```python
retrieve(d)
```

定义类型：function；[源码第 80 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:80)。

Exact rolling equivalent of the station-center algorithm, in physical units.

同名测试引用：[tests/test_retrieval.py:14](C:/work/ls4t/tests/test_retrieval.py:14)

### `retrieve.total`

```python
retrieve.total(a)
```

定义类型：nested；[源码第 96 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:96)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:34](C:/work/ls4t/tests/test_south_america_monthly_components.py:34)

### `retrieve.solve`

```python
retrieve.solve(aa, ab, bb, u, v)
```

定义类型：nested；[源码第 98 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:98)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:73](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:73)

### `paths`

```python
paths(stamp)
```

定义类型：function；[源码第 142 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:142)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:90](C:/work/ls4t/tests/test_south_america_monthly_components.py:90)

### `load_static`

```python
load_static()
```

定义类型：function；[源码第 150 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:150)。

无 docstring；算法解释见人工审阅章节。

### `grid_check`

```python
grid_check(ds, shape, gt, pr)
```

定义类型：function；[源码第 174 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:174)。

无 docstring；算法解释见人工审阅章节。

### `attrs`

```python
attrs(f, gt, pr)
```

定义类型：function；[源码第 179 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:179)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:178](C:/work/ls4t/tests/test_msg_case_dependencies.py:178)、[tests/test_south_america_components.py:125](C:/work/ls4t/tests/test_south_america_components.py:125)

### `instant_path`

```python
instant_path(root, stamp)
```

定义类型：function；[源码第 185 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:185)。

无 docstring；算法解释见人工审阅章节。

### `produce_scene`

```python
produce_scene(stamp, root, static, latt, lonn, gt, pr, tile=256)
```

定义类型：function；[源码第 189 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:189)。

无 docstring；算法解释见人工审阅章节。

### `monthly`

```python
monthly(root, month, hour, files, expected, missing, gt, pr)
```

定义类型：function；[源码第 243 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:243)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:1](C:/work/ls4t/tests/test_south_america_monthly_components.py:1)

### `main`

```python
main()
```

定义类型：function；[源码第 296 行](C:/work/ls4t/cases/msg/assessment/produce_msg_5x5.py:296)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/relocate_case_code_paths.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/relocate_case_code_paths.py)；64 行，3 个定义。

### `sha`

```python
sha(p)
```

定义类型：function；[源码第 14 行](C:/work/ls4t/cases/msg/assessment/relocate_case_code_paths.py:14)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `definitions`

```python
definitions(text)
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/msg/assessment/relocate_case_code_paths.py:15)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 18 行](C:/work/ls4t/cases/msg/assessment/relocate_case_code_paths.py:18)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/remove_figure8_counts.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/remove_figure8_counts.py)；19 行，0 个定义。

## cases/msg/assessment/report_joint_station_parameters.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/report_joint_station_parameters.py)；163 行，2 个定义。

### `table`

```python
table(df, cols)
```

定义类型：function；[源码第 10 行](C:/work/ls4t/cases/msg/assessment/report_joint_station_parameters.py:10)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_calibration.py:11](C:/work/ls4t/tests/test_calibration.py:11)

### `main`

```python
main()
```

定义类型：function；[源码第 16 行](C:/work/ls4t/cases/msg/assessment/report_joint_station_parameters.py:16)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/report_msg_5x5_europe.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/report_msg_5x5_europe.py)；134 行，4 个定义。

### `f`

```python
f(x)
```

定义类型：function；[源码第 8 行](C:/work/ls4t/cases/msg/assessment/report_msg_5x5_europe.py:8)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:61](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:61)、[tests/test_africa_download.py:24](C:/work/ls4t/tests/test_africa_download.py:24)、[tests/test_dual_thermal_sensors.py:50](C:/work/ls4t/tests/test_dual_thermal_sensors.py:50)、[tests/test_flat_structure.py:132](C:/work/ls4t/tests/test_flat_structure.py:132)、[tests/test_kernel_atc_case.py:24](C:/work/ls4t/tests/test_kernel_atc_case.py:24)、[tests/test_kernel_models.py:64](C:/work/ls4t/tests/test_kernel_models.py:64)、[tests/test_msg_case_dependencies.py:77](C:/work/ls4t/tests/test_msg_case_dependencies.py:77)、[tests/test_msg_evo_sample.py:77](C:/work/ls4t/tests/test_msg_evo_sample.py:77)、[tests/test_south_america_components.py:30](C:/work/ls4t/tests/test_south_america_components.py:30)、[tests/test_south_america_monthly_components.py:89](C:/work/ls4t/tests/test_south_america_monthly_components.py:89)、[tests/test_south_america_remaining.py:25](C:/work/ls4t/tests/test_south_america_remaining.py:25)、[tests/test_spatial_modes.py:19](C:/work/ls4t/tests/test_spatial_modes.py:19)

### `main`

```python
main()
```

定义类型：function；[源码第 10 行](C:/work/ls4t/cases/msg/assessment/report_msg_5x5_europe.py:10)。

无 docstring；算法解释见人工审阅章节。

### `main.cell`

```python
main.cell(comp)
```

定义类型：nested；[源码第 36 行](C:/work/ls4t/cases/msg/assessment/report_msg_5x5_europe.py:36)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_building_structure.py:31](C:/work/ls4t/tests/test_beijing_building_structure.py:31)、[tests/test_south_america_monthly_components.py:23](C:/work/ls4t/tests/test_south_america_monthly_components.py:23)

### `main.actualcell`

```python
main.actualcell(comp)
```

定义类型：nested；[源码第 53 行](C:/work/ls4t/cases/msg/assessment/report_msg_5x5_europe.py:53)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/report_station_direct_europe.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/report_station_direct_europe.py)；125 行，4 个定义。

### `f`

```python
f(x)
```

定义类型：function；[源码第 8 行](C:/work/ls4t/cases/msg/assessment/report_station_direct_europe.py:8)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:61](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:61)、[tests/test_africa_download.py:24](C:/work/ls4t/tests/test_africa_download.py:24)、[tests/test_dual_thermal_sensors.py:50](C:/work/ls4t/tests/test_dual_thermal_sensors.py:50)、[tests/test_flat_structure.py:132](C:/work/ls4t/tests/test_flat_structure.py:132)、[tests/test_kernel_atc_case.py:24](C:/work/ls4t/tests/test_kernel_atc_case.py:24)、[tests/test_kernel_models.py:64](C:/work/ls4t/tests/test_kernel_models.py:64)、[tests/test_msg_case_dependencies.py:77](C:/work/ls4t/tests/test_msg_case_dependencies.py:77)、[tests/test_msg_evo_sample.py:77](C:/work/ls4t/tests/test_msg_evo_sample.py:77)、[tests/test_south_america_components.py:30](C:/work/ls4t/tests/test_south_america_components.py:30)、[tests/test_south_america_monthly_components.py:89](C:/work/ls4t/tests/test_south_america_monthly_components.py:89)、[tests/test_south_america_remaining.py:25](C:/work/ls4t/tests/test_south_america_remaining.py:25)、[tests/test_spatial_modes.py:19](C:/work/ls4t/tests/test_spatial_modes.py:19)

### `main`

```python
main()
```

定义类型：function；[源码第 10 行](C:/work/ls4t/cases/msg/assessment/report_station_direct_europe.py:10)。

无 docstring；算法解释见人工审阅章节。

### `main.cell`

```python
main.cell(comp)
```

定义类型：nested；[源码第 31 行](C:/work/ls4t/cases/msg/assessment/report_station_direct_europe.py:31)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_beijing_building_structure.py:31](C:/work/ls4t/tests/test_beijing_building_structure.py:31)、[tests/test_south_america_monthly_components.py:23](C:/work/ls4t/tests/test_south_america_monthly_components.py:23)

### `main.stat`

```python
main.stat(comp, scale)
```

定义类型：nested；[源码第 42 行](C:/work/ls4t/cases/msg/assessment/report_station_direct_europe.py:42)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:43](C:/work/ls4t/tests/test_msg_evo_sample.py:43)

## cases/msg/assessment/report_station_full_2018_2024.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/report_station_full_2018_2024.py)；235 行，5 个定义。

### `fmt`

```python
fmt(x, d=2)
```

定义类型：function；[源码第 10 行](C:/work/ls4t/cases/msg/assessment/report_station_full_2018_2024.py:10)。

无 docstring；算法解释见人工审阅章节。

### `table`

```python
table(frame, columns, headers=None)
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/report_station_full_2018_2024.py:11)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_calibration.py:11](C:/work/ls4t/tests/test_calibration.py:11)

### `main`

```python
main()
```

定义类型：function；[源码第 18 行](C:/work/ls4t/cases/msg/assessment/report_station_full_2018_2024.py:18)。

无 docstring；算法解释见人工审阅章节。

### `main.val`

```python
main.val(comp, scale)
```

定义类型：nested；[源码第 39 行](C:/work/ls4t/cases/msg/assessment/report_station_full_2018_2024.py:39)。

无 docstring；算法解释见人工审阅章节。

### `main.control`

```python
main.control(comp, model)
```

定义类型：nested；[源码第 50 行](C:/work/ls4t/cases/msg/assessment/report_station_full_2018_2024.py:50)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/revise_review_closure.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/revise_review_closure.py)；129 行，4 个定义。

### `change`

```python
change(i, text)
```

定义类型：function；[源码第 14 行](C:/work/ls4t/cases/msg/assessment/revise_review_closure.py:14)。

无 docstring；算法解释见人工审阅章节。

### `before`

```python
before(anchor, text)
```

定义类型：function；[源码第 63 行](C:/work/ls4t/cases/msg/assessment/revise_review_closure.py:63)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_atc_case.py:34](C:/work/ls4t/tests/test_kernel_atc_case.py:34)、[tests/test_slstr_case_dependencies.py:4](C:/work/ls4t/tests/test_slstr_case_dependencies.py:4)、[tests/test_south_america_remaining.py:60](C:/work/ls4t/tests/test_south_america_remaining.py:60)、[tests/test_standalone_cases.py:54](C:/work/ls4t/tests/test_standalone_cases.py:54)

### `table`

```python
table(caption, headers, records, widths=None)
```

定义类型：function；[源码第 76 行](C:/work/ls4t/cases/msg/assessment/revise_review_closure.py:76)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_calibration.py:11](C:/work/ls4t/tests/test_calibration.py:11)

### `value`

```python
value(c)
```

定义类型：function；[源码第 107 行](C:/work/ls4t/cases/msg/assessment/revise_review_closure.py:107)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_dual_thermal_sensors.py:111](C:/work/ls4t/tests/test_dual_thermal_sensors.py:111)、[tests/test_normalization.py:17](C:/work/ls4t/tests/test_normalization.py:17)、[tests/test_slstr_products.py:96](C:/work/ls4t/tests/test_slstr_products.py:96)、[tests/test_south_america_monthly_components.py:91](C:/work/ls4t/tests/test_south_america_monthly_components.py:91)、[tests/test_spatial_modes.py:14](C:/work/ls4t/tests/test_spatial_modes.py:14)

## cases/msg/assessment/revise_v6_validation.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/revise_v6_validation.py)；103 行，2 个定义。

### `replace`

```python
replace(p, text)
```

定义类型：function；[源码第 16 行](C:/work/ls4t/cases/msg/assessment/revise_v6_validation.py:16)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:75](C:/work/ls4t/tests/test_africa_download.py:75)、[tests/test_south_america_components.py:103](C:/work/ls4t/tests/test_south_america_components.py:103)、[tests/test_standalone_cases.py:75](C:/work/ls4t/tests/test_standalone_cases.py:75)

### `main`

```python
main()
```

定义类型：function；[源码第 21 行](C:/work/ls4t/cases/msg/assessment/revise_v6_validation.py:21)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/run_single_scene_windows.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/run_single_scene_windows.py)；250 行，7 个定义。

### `Tee.__init__`

```python
Tee.__init__(self, stream, log)
```

定义类型：method；[源码第 27 行](C:/work/ls4t/cases/msg/assessment/run_single_scene_windows.py:27)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:116](C:/work/ls4t/tests/test_africa_download.py:116)、[tests/test_stream_era5.py:16](C:/work/ls4t/tests/test_stream_era5.py:16)

### `Tee.write`

```python
Tee.write(self, text)
```

定义类型：method；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/run_single_scene_windows.py:30)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:96](C:/work/ls4t/tests/test_south_america_components.py:96)、[tests/test_south_america_monthly_components.py:108](C:/work/ls4t/tests/test_south_america_monthly_components.py:108)

### `Tee.flush`

```python
Tee.flush(self)
```

定义类型：method；[源码第 35 行](C:/work/ls4t/cases/msg/assessment/run_single_scene_windows.py:35)。

无 docstring；算法解释见人工审阅章节。

### `sha256`

```python
sha256(path)
```

定义类型：function；[源码第 40 行](C:/work/ls4t/cases/msg/assessment/run_single_scene_windows.py:40)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:152](C:/work/ls4t/tests/test_africa_download.py:152)、[tests/test_msg_evo_sample.py:44](C:/work/ls4t/tests/test_msg_evo_sample.py:44)、[tests/test_standalone_cases.py:61](C:/work/ls4t/tests/test_standalone_cases.py:61)

### `replace_once`

```python
replace_once(source, old, new)
```

定义类型：function；[源码第 48 行](C:/work/ls4t/cases/msg/assessment/run_single_scene_windows.py:48)。

无 docstring；算法解释见人工审阅章节。

### `comparison`

```python
comparison(new_path, archive_path)
```

定义类型：function；[源码第 54 行](C:/work/ls4t/cases/msg/assessment/run_single_scene_windows.py:54)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_atc_case.py:1](C:/work/ls4t/tests/test_kernel_atc_case.py:1)、[tests/test_msg_aatsr_comparison.py:13](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:13)

### `main`

```python
main()
```

定义类型：function；[源码第 104 行](C:/work/ls4t/cases/msg/assessment/run_single_scene_windows.py:104)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/run_station_full_2018_2024.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/run_station_full_2018_2024.py)；202 行，8 个定义。

### `sha`

```python
sha(p)
```

定义类型：function；[源码第 24 行](C:/work/ls4t/cases/msg/assessment/run_station_full_2018_2024.py:24)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `atomic`

```python
atomic(path, obj)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/run_station_full_2018_2024.py:30)。

无 docstring；算法解释见人工审阅章节。

### `functions`

```python
functions()
```

定义类型：function；[源码第 38 行](C:/work/ls4t/cases/msg/assessment/run_station_full_2018_2024.py:38)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:85](C:/work/ls4t/tests/test_flat_structure.py:85)

### `load`

```python
load(p)
```

定义类型：function；[源码第 45 行](C:/work/ls4t/cases/msg/assessment/run_station_full_2018_2024.py:45)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization.py:97](C:/work/ls4t/tests/test_normalization.py:97)、[tests/test_standalone_cases.py:43](C:/work/ls4t/tests/test_standalone_cases.py:43)

### `worker`

```python
worker(job)
```

定义类型：function；[源码第 51 行](C:/work/ls4t/cases/msg/assessment/run_station_full_2018_2024.py:51)。

无 docstring；算法解释见人工审阅章节。

### `worker.read`

```python
worker.read(p)
```

定义类型：nested；[源码第 61 行](C:/work/ls4t/cases/msg/assessment/run_station_full_2018_2024.py:61)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:262](C:/work/ls4t/tests/test_africa_download.py:262)

### `worker.many`

```python
worker.many(paths)
```

定义类型：nested；[源码第 63 行](C:/work/ls4t/cases/msg/assessment/run_station_full_2018_2024.py:63)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 160 行](C:/work/ls4t/cases/msg/assessment/run_station_full_2018_2024.py:160)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/run_station_test.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/run_station_test.py)；147 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/msg/assessment/run_station_test.py:25)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/search_evo_parameters.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py)；288 行，10 个定义。

### `planck`

```python
planck(t, mode='physical')
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:23)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inverse`

```python
inverse(r, mode='physical')
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:30)。

无 docstring；算法解释见人工审阅章节。

### `solve`

```python
solve(r1, r2, a1, b1, a2, b2, size=5, spatial=False)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:38)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:73](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:73)

### `solve.total`

```python
solve.total(x)
```

定义类型：nested；[源码第 41 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:41)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:34](C:/work/ls4t/tests/test_south_america_monthly_components.py:34)

### `prepare`

```python
prepare(data, hspot, mode, window, residual, hotspot)
```

定义类型：function；[源码第 57 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:57)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:175](C:/work/ls4t/tests/test_africa_download.py:175)

### `retrieve`

```python
retrieve(pre, data, lmbda, delta, mode='physical', cap=False, return_raw=False)
```

定义类型：function；[源码第 77 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:77)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_retrieval.py:14](C:/work/ls4t/tests/test_retrieval.py:14)

### `load_data`

```python
load_data(out)
```

定义类型：function；[源码第 109 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:109)。

无 docstring；算法解释见人工审阅章节。

### `load_data.read`

```python
load_data.read(p)
```

定义类型：nested；[源码第 120 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:120)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:262](C:/work/ls4t/tests/test_africa_download.py:262)

### `metrics`

```python
metrics(pred, panel, mask)
```

定义类型：function；[源码第 155 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:155)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:71](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:71)

### `main`

```python
main()
```

定义类型：function；[源码第 179 行](C:/work/ls4t/cases/msg/assessment/search_evo_parameters.py:179)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/select_existing_landcover_parameters.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/select_existing_landcover_parameters.py)；162 行，4 个定义。

### `sha`

```python
sha(p)
```

定义类型：function；[源码第 12 行](C:/work/ls4t/cases/msg/assessment/select_existing_landcover_parameters.py:12)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `js`

```python
js(name, value)
```

定义类型：function；[源码第 13 行](C:/work/ls4t/cases/msg/assessment/select_existing_landcover_parameters.py:13)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 16 行](C:/work/ls4t/cases/msg/assessment/select_existing_landcover_parameters.py:16)。

无 docstring；算法解释见人工审阅章节。

### `main.evaluate_split`

```python
main.evaluate_split(split)
```

定义类型：nested；[源码第 39 行](C:/work/ls4t/cases/msg/assessment/select_existing_landcover_parameters.py:39)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/select_joint_station_parameters.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py)；304 行，12 个定义。

### `sha`

```python
sha(p)
```

定义类型：function；[源码第 24 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:24)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `write_json`

```python
write_json(name, data)
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:25)。

无 docstring；算法解释见人工审阅章节。

### `physical_mask`

```python
physical_mask(data)
```

定义类型：function；[源码第 28 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:28)。

无 docstring；算法解释见人工审阅章节。

### `load_panel`

```python
load_panel()
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:39)。

无 docstring；算法解释见人工审阅章节。

### `score_specs`

```python
score_specs(panel, split)
```

定义类型：function；[源码第 83 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:83)。

Weights: domain -> equal sites -> equal years -> equal months -> records.

### `projected`

```python
projected(temp, panel)
```

定义类型：function；[源码第 102 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:102)。

无 docstring；算法解释见人工审阅章节。

### `evaluate`

```python
evaluate(temp, panel, specs)
```

定义类型：function；[源码第 106 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:106)。

无 docstring；算法解释见人工审阅章节。

### `prediction`

```python
prediction(data, config, ns, pre=None)
```

定义类型：function；[源码第 117 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:117)。

无 docstring；算法解释见人工审阅章节。

### `normalized`

```python
normalized(result, baseline)
```

定义类型：function；[源码第 124 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:124)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization.py:17](C:/work/ls4t/tests/test_normalization.py:17)

### `qualified`

```python
qualified(result, coverage, baseline, basecov)
```

定义类型：function；[源码第 130 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:130)。

无 docstring；算法解释见人工审阅章节。

### `validation_tables`

```python
validation_tables(predictions, panel)
```

定义类型：function；[源码第 140 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:140)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 181 行](C:/work/ls4t/cases/msg/assessment/select_joint_station_parameters.py:181)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/select_landcover_parameters.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py)；324 行，17 个定义。

### `sha`

```python
sha(p)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:23)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `js`

```python
js(name, value)
```

定义类型：function；[源码第 24 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:24)。

无 docstring；算法解释见人工审阅章节。

### `md`

```python
md(df)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:26)。

无 docstring；算法解释见人工审阅章节。

### `predict`

```python
predict(data, config, ns, pre=None)
```

定义类型：function；[源码第 32 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:32)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_annual_cycle.py:15](C:/work/ls4t/tests/test_annual_cycle.py:15)、[tests/test_kernel_models.py:80](C:/work/ls4t/tests/test_kernel_models.py:80)

### `make_specs`

```python
make_specs(panel)
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:39)。

无 docstring；算法解释见人工审阅章节。

### `cell_metrics`

```python
cell_metrics(values, baseline, spec)
```

定义类型：function；[源码第 55 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:55)。

无 docstring；算法解释见人工审阅章节。

### `cell_metrics.means`

```python
cell_metrics.means(mask)
```

定义类型：nested；[源码第 58 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:58)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_tsharp.py:10](C:/work/ls4t/tests/test_tsharp.py:10)

### `cell_metrics.means.avg`

```python
cell_metrics.means.avg(x)
```

定义类型：nested；[源码第 60 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:60)。

无 docstring；算法解释见人工审阅章节。

### `cell_metrics.rmse`

```python
cell_metrics.rmse(p, r, ok)
```

定义类型：nested；[源码第 66 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:66)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:111](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:111)

### `evaluate`

```python
evaluate(temp, base_temp, panel, specs)
```

定义类型：function；[源码第 72 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:72)。

无 docstring；算法解释见人工审阅章节。

### `check_cell_independently`

```python
check_cell_independently(values, baseline, spec, expected)
```

定义类型：function；[源码第 76 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:76)。

无 docstring；算法解释见人工审阅章节。

### `check_cell_independently.aggregate`

```python
check_cell_independently.aggregate(x)
```

定义类型：nested；[源码第 79 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:79)。

无 docstring；算法解释见人工审阅章节。

### `check_cell_independently.rms`

```python
check_cell_independently.rms(x)
```

定义类型：nested；[源码第 85 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:85)。

无 docstring；算法解释见人工审阅章节。

### `rank`

```python
rank(arr, base, specs, group, exclude=None)
```

定义类型：function；[源码第 91 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:91)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_kernel_models.py:87](C:/work/ls4t/tests/test_kernel_models.py:87)、[tests/test_msg_evo_sample.py:130](C:/work/ls4t/tests/test_msg_evo_sample.py:130)、[tests/test_multisource_normalization.py:23](C:/work/ls4t/tests/test_multisource_normalization.py:23)

### `conventional`

```python
conventional(temp, base_temp, panel, model, group)
```

定义类型：function；[源码第 114 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:114)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 137 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:137)。

无 docstring；算法解释见人工审阅章节。

### `report`

```python
report(selection, val, summary, folds, lc)
```

定义类型：function；[源码第 261 行](C:/work/ls4t/cases/msg/assessment/select_landcover_parameters.py:261)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:62](C:/work/ls4t/tests/test_africa_download.py:62)、[tests/test_kernel_atc_case.py:19](C:/work/ls4t/tests/test_kernel_atc_case.py:19)、[tests/test_south_america_components.py:83](C:/work/ls4t/tests/test_south_america_components.py:83)、[tests/test_south_america_remaining.py:36](C:/work/ls4t/tests/test_south_america_remaining.py:36)

## cases/msg/assessment/stratify_parameter_landcover.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/stratify_parameter_landcover.py)；102 行，2 个定义。

### `cachegroup`

```python
cachegroup(code)
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/msg/assessment/stratify_parameter_landcover.py:15)。

无 docstring；算法解释见人工审阅章节。

### `md`

```python
md(df)
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/msg/assessment/stratify_parameter_landcover.py:39)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/streamline_paper_narrative.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/streamline_paper_narrative.py)；73 行，2 个定义。

### `put`

```python
put(i, text)
```

定义类型：function；[源码第 12 行](C:/work/ls4t/cases/msg/assessment/streamline_paper_narrative.py:12)。

无 docstring；算法解释见人工审阅章节。

### `delete`

```python
delete(i)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/msg/assessment/streamline_paper_narrative.py:17)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/streamline_validation_text.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/streamline_validation_text.py)；71 行，2 个定义。

### `put`

```python
put(i, text)
```

定义类型：function；[源码第 16 行](C:/work/ls4t/cases/msg/assessment/streamline_validation_text.py:16)。

无 docstring；算法解释见人工审阅章节。

### `substitute`

```python
substitute(i, old, new)
```

定义类型：function；[源码第 21 行](C:/work/ls4t/cases/msg/assessment/streamline_validation_text.py:21)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/summarize_europe_12_sites.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/summarize_europe_12_sites.py)；63 行，2 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/assessment/summarize_europe_12_sites.py:11)。

无 docstring；算法解释见人工审阅章节。

### `main.summarize`

```python
main.summarize(x)
```

定义类型：nested；[源码第 19 行](C:/work/ls4t/cases/msg/assessment/summarize_europe_12_sites.py:19)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/summarize_production_pilots.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/summarize_production_pilots.py)；89 行，4 个定义。

### `sha256`

```python
sha256(path)
```

定义类型：function；[源码第 13 行](C:/work/ls4t/cases/msg/assessment/summarize_production_pilots.py:13)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:152](C:/work/ls4t/tests/test_africa_download.py:152)、[tests/test_msg_evo_sample.py:44](C:/work/ls4t/tests/test_msg_evo_sample.py:44)、[tests/test_standalone_cases.py:61](C:/work/ls4t/tests/test_standalone_cases.py:61)

### `output_from_report`

```python
output_from_report(path)
```

定义类型：function；[源码第 21 行](C:/work/ls4t/cases/msg/assessment/summarize_production_pilots.py:21)。

无 docstring；算法解释见人工审阅章节。

### `compare`

```python
compare(candidate, reference)
```

定义类型：function；[源码第 29 行](C:/work/ls4t/cases/msg/assessment/summarize_production_pilots.py:29)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 60 行](C:/work/ls4t/cases/msg/assessment/summarize_production_pilots.py:60)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/test_europe12_hotspot_windows.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/test_europe12_hotspot_windows.py)；172 行，3 个定义。

### `sha`

```python
sha(p)
```

定义类型：function；[源码第 19 行](C:/work/ls4t/cases/msg/assessment/test_europe12_hotspot_windows.py:19)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `save`

```python
save(name, obj)
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/msg/assessment/test_europe12_hotspot_windows.py:20)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/test_europe12_hotspot_windows.py:22)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/update_figure8_document.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/update_figure8_document.py)；30 行，0 个定义。

## cases/msg/assessment/update_monthly_hour_title.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/update_monthly_hour_title.py)；19 行，0 个定义。

## cases/msg/assessment/validate_existing_evo_grid.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/validate_existing_evo_grid.py)；208 行，6 个定义。

### `sha256`

```python
sha256(path)
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/msg/assessment/validate_existing_evo_grid.py:25)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:152](C:/work/ls4t/tests/test_africa_download.py:152)、[tests/test_msg_evo_sample.py:44](C:/work/ls4t/tests/test_msg_evo_sample.py:44)、[tests/test_standalone_cases.py:61](C:/work/ls4t/tests/test_standalone_cases.py:61)

### `correction`

```python
correction(celsius)
```

定义类型：function；[源码第 33 行](C:/work/ls4t/cases/msg/assessment/validate_existing_evo_grid.py:33)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_tsharp.py:40](C:/work/ls4t/tests/test_tsharp.py:40)

### `correction.planck`

```python
correction.planck(t)
```

定义类型：nested；[源码第 34 行](C:/work/ls4t/cases/msg/assessment/validate_existing_evo_grid.py:34)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `score`

```python
score(frame)
```

定义类型：function；[源码第 40 行](C:/work/ls4t/cases/msg/assessment/validate_existing_evo_grid.py:40)。

无 docstring；算法解释见人工审阅章节。

### `finite_mean`

```python
finite_mean(a, axis)
```

定义类型：function；[源码第 48 行](C:/work/ls4t/cases/msg/assessment/validate_existing_evo_grid.py:48)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 54 行](C:/work/ls4t/cases/msg/assessment/validate_existing_evo_grid.py:54)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/validate_msg_5x5_europe.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/validate_msg_5x5_europe.py)；191 行，3 个定义。

### `sha`

```python
sha(p)
```

定义类型：function；[源码第 19 行](C:/work/ls4t/cases/msg/assessment/validate_msg_5x5_europe.py:19)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `score`

```python
score(obs, pred)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/assessment/validate_msg_5x5_europe.py:26)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 35 行](C:/work/ls4t/cases/msg/assessment/validate_msg_5x5_europe.py:35)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/validate_station_direct_europe.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/validate_station_direct_europe.py)；181 行，4 个定义。

### `sha`

```python
sha(path)
```

定义类型：function；[源码第 19 行](C:/work/ls4t/cases/msg/assessment/validate_station_direct_europe.py:19)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:151](C:/work/ls4t/tests/test_africa_download.py:151)

### `main`

```python
main()
```

定义类型：function；[源码第 22 行](C:/work/ls4t/cases/msg/assessment/validate_station_direct_europe.py:22)。

无 docstring；算法解释见人工审阅章节。

### `main.load`

```python
main.load(path)
```

定义类型：nested；[源码第 56 行](C:/work/ls4t/cases/msg/assessment/validate_station_direct_europe.py:56)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization.py:97](C:/work/ls4t/tests/test_normalization.py:97)、[tests/test_standalone_cases.py:43](C:/work/ls4t/tests/test_standalone_cases.py:43)

### `main.read`

```python
main.read(path)
```

定义类型：nested；[源码第 60 行](C:/work/ls4t/cases/msg/assessment/validate_station_direct_europe.py:60)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:262](C:/work/ls4t/tests/test_africa_download.py:262)

## cases/msg/assessment/validate_station_test.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/validate_station_test.py)；92 行，2 个定义。

### `scores`

```python
scores(reference, estimate)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/msg/assessment/validate_station_test.py:17)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 24 行](C:/work/ls4t/cases/msg/assessment/validate_station_test.py:24)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/verify_disk_layout.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/verify_disk_layout.py)；132 行，4 个定义。

### `read_json`

```python
read_json(path)
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/msg/assessment/verify_disk_layout.py:15)。

无 docstring；算法解释见人工审阅章节。

### `write_json`

```python
write_json(path, data)
```

定义类型：function；[源码第 19 行](C:/work/ls4t/cases/msg/assessment/verify_disk_layout.py:19)。

无 docstring；算法解释见人工审阅章节。

### `sha256`

```python
sha256(path)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/msg/assessment/verify_disk_layout.py:23)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:152](C:/work/ls4t/tests/test_africa_download.py:152)、[tests/test_msg_evo_sample.py:44](C:/work/ls4t/tests/test_msg_evo_sample.py:44)、[tests/test_standalone_cases.py:61](C:/work/ls4t/tests/test_standalone_cases.py:61)

### `main`

```python
main()
```

定义类型：function；[源码第 31 行](C:/work/ls4t/cases/msg/assessment/verify_disk_layout.py:31)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/assessment/verify_msg_5x5.py

源码：[打开文件](C:/work/ls4t/cases/msg/assessment/verify_msg_5x5.py)；62 行，1 个定义。

### `main`

```python
main()
```

定义类型：function；[源码第 8 行](C:/work/ls4t/cases/msg/assessment/verify_msg_5x5.py:8)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/experiments/msg_lsct_2c_window.py

源码：[打开文件](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py)；312 行，8 个定义。

### `planck`

```python
planck(wavelength, Ts)
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:11)。

基于planck公式，计算某个波长时候，从温度到辐射的转换 :param wavelength: 波长，10.5 :param Ts: 温度，可以是亮温，也可以是摄氏度 :return: 辐射

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inv_planck`

```python
inv_planck(wavelength, rad)
```

定义类型：function；[源码第 33 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:33)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `solve_3x3_least_squares`

```python
solve_3x3_least_squares(rad_euro, rad_iodc, w)
```

定义类型：function；[源码第 44 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:44)。

无 docstring；算法解释见人工审阅章节。

### `solve_3x3_least_squares.clean_nan`

```python
solve_3x3_least_squares.clean_nan(img)
```

定义类型：nested；[源码第 54 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:54)。

无 docstring；算法解释见人工审阅章节。

### `solve_3x3_least_squares.box_sum`

```python
solve_3x3_least_squares.box_sum(img)
```

定义类型：nested；[源码第 68 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:68)。

无 docstring；算法解释见人工审阅章节。

### `solve_5x5_least_squares_robust`

```python
solve_5x5_least_squares_robust(rad_euro, rad_iodc, w)
```

定义类型：function；[源码第 106 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:106)。

无 docstring；算法解释见人工审阅章节。

### `solve_5x5_least_squares_robust.clean_nan`

```python
solve_5x5_least_squares_robust.clean_nan(img)
```

定义类型：nested；[源码第 112 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:112)。

无 docstring；算法解释见人工审阅章节。

### `solve_5x5_least_squares_robust.box_sum_5x5`

```python
solve_5x5_least_squares_robust.box_sum_5x5(img)
```

定义类型：nested；[源码第 126 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_2c_window.py:126)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/experiments/msg_lsct_3c_constrained.py

源码：[打开文件](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py)；708 行，16 个定义。

### `solve_constrained_vectorized`

```python
solve_constrained_vectorized(rad_e, rad_i, w2, w3, w5, w6, bs1_fixed, dif=0.5)
```

定义类型：function；[源码第 14 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:14)。

完全向量化的约束求解：修正了边界代入公式中的 dif 逻辑。 约束条件： 1. bs2 <= bs1_fixed 2. |bs2 - bv| <= dif  =>  bv - dif <= bs2 <= bv + dif

### `solve_constrained_vectorized.get_sse`

```python
solve_constrained_vectorized.get_sse(b2, v)
```

定义类型：nested；[源码第 25 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:25)。

无 docstring；算法解释见人工审阅章节。

### `solve_constrained_vectorized1`

```python
solve_constrained_vectorized1(rad_e, rad_i, w2, w3, w5, w6, bs1_fixed, dif=0.5)
```

定义类型：function；[源码第 97 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:97)。

只应用约束 1: bs2 <= bs1_fixed

### `solve_constrained_vectorized2`

```python
solve_constrained_vectorized2(rad_e, rad_i, w2, w3, w5, w6, bs1_fixed, dif=0.5)
```

定义类型：function；[源码第 119 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:119)。

只应用约束 2: |bs2 - bv| <= dif

### `solve_constrained_vectorized2.get_sse`

```python
solve_constrained_vectorized2.get_sse(b2, v)
```

定义类型：nested；[源码第 126 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:126)。

无 docstring；算法解释见人工审阅章节。

### `hotspot_layer`

```python
hotspot_layer(lai, hspot, vza, sza, vsa, CIs=1.0, CIv=1.0, G=0.5)
```

定义类型：function；[源码第 162 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:162)。

计算双向透过率(w:光照土壤比例)和单向透过率(b:总土壤比例)

同名测试引用：[tests/test_slstr_case_dependencies.py:23](C:/work/ls4t/tests/test_slstr_case_dependencies.py:23)

### `calculate_scattering_angle`

```python
calculate_scattering_angle(sza, saa, vza, vaa)
```

定义类型：function；[源码第 187 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:187)。

计算太阳方向与观测方向的夹角 (散射角/相位角) 输入参数均为角度 (Degrees)

### `planck`

```python
planck(wavelength, Ts)
```

定义类型：function；[源码第 214 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:214)。

基于planck公式，计算某个波长时候，从温度到辐射的转换 :param wavelength: 波长，10.5 :param Ts: 温度，可以是亮温，也可以是摄氏度 :return: 辐射

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inv_planck`

```python
inv_planck(wavelength, rad)
```

定义类型：function；[源码第 236 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:236)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `solve_5x5_three_components`

```python
solve_5x5_three_components(rad_euro, rad_iodc, w)
```

定义类型：function；[源码第 250 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:250)。

求解三组分模型: w1*bs1 + w2*bs2 + w3*bv = rad_e               w4*bs1 + w5*bs2 + w6*bv = rad_i w shape: (H, W, 6)

### `solve_5x5_three_components.clean_nan`

```python
solve_5x5_three_components.clean_nan(img)
```

定义类型：nested；[源码第 263 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:263)。

无 docstring；算法解释见人工审阅章节。

### `solve_5x5_three_components.box_sum`

```python
solve_5x5_three_components.box_sum(img)
```

定义类型：nested；[源码第 283 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:283)。

无 docstring；算法解释见人工审阅章节。

### `solve_2x2_system_5x5`

```python
solve_2x2_system_5x5(rad1, rad2, w_a1, w_b1, w_a2, w_b2, size=5)
```

定义类型：function；[源码第 329 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:329)。

使用 5x5 窗口最小二乘法求解方程组: w_a1*X + w_b1*Y = rad1 w_a2*X + w_b2*Y = rad2  X, Y: 待求的两组分辐射 (如 X=光照土壤, Y=阴影土壤+植被)

### `solve_2x2_system_5x5.clean`

```python
solve_2x2_system_5x5.clean(img)
```

定义类型：nested；[源码第 341 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:341)。

无 docstring；算法解释见人工审阅章节。

### `solve_2x2_system_5x5.box_sum`

```python
solve_2x2_system_5x5.box_sum(img)
```

定义类型：nested；[源码第 358 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:358)。

无 docstring；算法解释见人工审阅章节。

### `solve_joint_vectorized_with_prior`

```python
solve_joint_vectorized_with_prior(rad_e, rad_i, w, x_prior, lmbda=0.5)
```

定义类型：function；[源码第 395 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_constrained.py:395)。

联合反演：利用分步结果作为先验知识进行全图平差

## cases/msg/experiments/msg_lsct_3c_diagnostics.py

源码：[打开文件](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py)；632 行，12 个定义。

### `hotspot_layer`

```python
hotspot_layer(lai, hspot, vza, sza, vsa, CIs=1.0, CIv=1.0, G=0.5)
```

定义类型：function；[源码第 14 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:14)。

计算双向透过率(w:光照土壤比例)和单向透过率(b:总土壤比例)

同名测试引用：[tests/test_slstr_case_dependencies.py:23](C:/work/ls4t/tests/test_slstr_case_dependencies.py:23)

### `calculate_scattering_angle`

```python
calculate_scattering_angle(sza, saa, vza, vaa)
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:39)。

计算太阳方向与观测方向的夹角 (散射角/相位角) 输入参数均为角度 (Degrees)

### `solve_5x5_three_components`

```python
solve_5x5_three_components(rad_euro, rad_iodc, w)
```

定义类型：function；[源码第 69 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:69)。

求解三组分模型: w1*bs1 + w2*bs2 + w3*bv = rad_e               w4*bs1 + w5*bs2 + w6*bv = rad_i w shape: (H, W, 6)

### `solve_5x5_three_components.clean_nan`

```python
solve_5x5_three_components.clean_nan(img)
```

定义类型：nested；[源码第 82 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:82)。

无 docstring；算法解释见人工审阅章节。

### `solve_5x5_three_components.box_sum`

```python
solve_5x5_three_components.box_sum(img)
```

定义类型：nested；[源码第 102 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:102)。

无 docstring；算法解释见人工审阅章节。

### `solve_2x2_system_5x5`

```python
solve_2x2_system_5x5(rad1, rad2, w_a1, w_b1, w_a2, w_b2, size=5)
```

定义类型：function；[源码第 148 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:148)。

使用 5x5 窗口最小二乘法求解方程组: w_a1*X + w_b1*Y = rad1 w_a2*X + w_b2*Y = rad2  X, Y: 待求的两组分辐射 (如 X=光照土壤, Y=阴影土壤+植被)

### `solve_2x2_system_5x5.clean`

```python
solve_2x2_system_5x5.clean(img)
```

定义类型：nested；[源码第 160 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:160)。

无 docstring；算法解释见人工审阅章节。

### `solve_2x2_system_5x5.box_sum`

```python
solve_2x2_system_5x5.box_sum(img)
```

定义类型：nested；[源码第 177 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:177)。

无 docstring；算法解释见人工审阅章节。

### `solve_constrained_vectorized1`

```python
solve_constrained_vectorized1(rad_e, rad_i, w2, w3, w5, w6, bs1_fixed, dif=0.5)
```

定义类型：function；[源码第 213 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:213)。

只应用约束 1: bs2 <= bs1_fixed

### `solve_constrained_vectorized2`

```python
solve_constrained_vectorized2(rad_e, rad_i, w2, w3, w5, w6, bs1_fixed, dif=0.5)
```

定义类型：function；[源码第 235 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:235)。

只应用约束 2: |bs2 - bv| <= dif

### `solve_constrained_vectorized2.get_sse`

```python
solve_constrained_vectorized2.get_sse(b2, v)
```

定义类型：nested；[源码第 242 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:242)。

无 docstring；算法解释见人工审阅章节。

### `solve_joint_vectorized_with_prior`

```python
solve_joint_vectorized_with_prior(rad_e, rad_i, w, x_prior, lmbda=0.5)
```

定义类型：function；[源码第 278 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_diagnostics.py:278)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/experiments/msg_lsct_3c_two_stage.py

源码：[打开文件](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py)；424 行，8 个定义。

### `planck`

```python
planck(wavelength, Ts)
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:15)。

基于planck公式，计算某个波长时候，从温度到辐射的转换 :param wavelength: 波长，10.5 :param Ts: 温度，可以是亮温，也可以是摄氏度 :return: 辐射

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inv_planck`

```python
inv_planck(wavelength, rad)
```

定义类型：function；[源码第 37 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:37)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `solve_5x5_three_components`

```python
solve_5x5_three_components(rad_euro, rad_iodc, w)
```

定义类型：function；[源码第 51 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:51)。

求解三组分模型: w1*bs1 + w2*bs2 + w3*bv = rad_e               w4*bs1 + w5*bs2 + w6*bv = rad_i w shape: (H, W, 6)

### `solve_5x5_three_components.clean_nan`

```python
solve_5x5_three_components.clean_nan(img)
```

定义类型：nested；[源码第 64 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:64)。

无 docstring；算法解释见人工审阅章节。

### `solve_5x5_three_components.box_sum`

```python
solve_5x5_three_components.box_sum(img)
```

定义类型：nested；[源码第 84 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:84)。

无 docstring；算法解释见人工审阅章节。

### `solve_2x2_system_5x5`

```python
solve_2x2_system_5x5(rad1, rad2, w_a1, w_b1, w_a2, w_b2, size=5)
```

定义类型：function；[源码第 132 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:132)。

使用 5x5 窗口最小二乘法求解方程组: w_a1*X + w_b1*Y = rad1 w_a2*X + w_b2*Y = rad2  X, Y: 待求的两组分辐射 (如 X=光照土壤, Y=阴影土壤+植被)

### `solve_2x2_system_5x5.clean`

```python
solve_2x2_system_5x5.clean(img)
```

定义类型：nested；[源码第 144 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:144)。

无 docstring；算法解释见人工审阅章节。

### `solve_2x2_system_5x5.box_sum`

```python
solve_2x2_system_5x5.box_sum(img)
```

定义类型：nested；[源码第 161 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_two_stage.py:161)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/experiments/msg_lsct_3c_window.py

源码：[打开文件](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py)；415 行，8 个定义。

### `planck`

```python
planck(wavelength, Ts)
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:15)。

基于planck公式，计算某个波长时候，从温度到辐射的转换 :param wavelength: 波长，10.5 :param Ts: 温度，可以是亮温，也可以是摄氏度 :return: 辐射

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `inv_planck`

```python
inv_planck(wavelength, rad)
```

定义类型：function；[源码第 37 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:37)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `solve_5x5_three_components`

```python
solve_5x5_three_components(rad_euro, rad_iodc, w)
```

定义类型：function；[源码第 51 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:51)。

求解三组分模型: w1*bs1 + w2*bs2 + w3*bv = rad_e               w4*bs1 + w5*bs2 + w6*bv = rad_i w shape: (H, W, 6)

### `solve_5x5_three_components.clean_nan`

```python
solve_5x5_three_components.clean_nan(img)
```

定义类型：nested；[源码第 64 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:64)。

无 docstring；算法解释见人工审阅章节。

### `solve_5x5_three_components.box_sum`

```python
solve_5x5_three_components.box_sum(img)
```

定义类型：nested；[源码第 84 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:84)。

无 docstring；算法解释见人工审阅章节。

### `solve_3x3_three_components`

```python
solve_3x3_three_components(rad_euro, rad_iodc, w)
```

定义类型：function；[源码第 130 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:130)。

求解三组分模型 (3x3 窗口最小二乘法): w1*bs1 + w2*bs2 + w3*bv = rad_e w4*bs1 + w5*bs2 + w6*bv = rad_i w shape: (H, W, 6)

### `solve_3x3_three_components.clean_nan`

```python
solve_3x3_three_components.clean_nan(img)
```

定义类型：nested；[源码第 147 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:147)。

无 docstring；算法解释见人工审阅章节。

### `solve_3x3_three_components.box_sum_3x3`

```python
solve_3x3_three_components.box_sum_3x3(img)
```

定义类型：nested；[源码第 167 行](C:/work/ls4t/cases/msg/experiments/msg_lsct_3c_window.py:167)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_download.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_download.py)；68 行，0 个定义。

## cases/msg/msg_extract_euro.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_extract_euro.py)；168 行，1 个定义。

### `write_image_gdal`

```python
write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff', nodata_value=None)
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/msg_extract_euro.py:11)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_extract_iodc.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_extract_iodc.py)；169 行，1 个定义。

### `write_image_gdal`

```python
write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff', nodata_value=None)
```

定义类型：function；[源码第 11 行](C:/work/ls4t/cases/msg/msg_extract_iodc.py:11)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_lsct_iter.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_lsct_iter.py)；701 行，14 个定义。

### `hotspot_layer`

```python
hotspot_layer(lai, hspot, vza, sza, vsa, CIs=1.0, CIv=1.0, G=0.5)
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:26)。

计算双向透过率(w:光照土壤比例)和单向透过率(b:总土壤比例)

同名测试引用：[tests/test_slstr_case_dependencies.py:23](C:/work/ls4t/tests/test_slstr_case_dependencies.py:23)

### `calculate_scattering_angle`

```python
calculate_scattering_angle(sza, saa, vza, vaa)
```

定义类型：function；[源码第 51 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:51)。

计算太阳方向与观测方向的夹角 (散射角/相位角) 输入参数均为角度 (Degrees)

### `solve_5x5_three_components`

```python
solve_5x5_three_components(rad_euro, rad_iodc, w)
```

定义类型：function；[源码第 81 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:81)。

求解三组分模型: w1*bs1 + w2*bs2 + w3*bv = rad_e               w4*bs1 + w5*bs2 + w6*bv = rad_i w shape: (H, W, 6)

### `solve_5x5_three_components.clean_nan`

```python
solve_5x5_three_components.clean_nan(img)
```

定义类型：nested；[源码第 94 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:94)。

无 docstring；算法解释见人工审阅章节。

### `solve_5x5_three_components.box_sum`

```python
solve_5x5_three_components.box_sum(img)
```

定义类型：nested；[源码第 114 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:114)。

无 docstring；算法解释见人工审阅章节。

### `solve_2x2_system_5x5`

```python
solve_2x2_system_5x5(rad1, rad2, w_a1, w_b1, w_a2, w_b2, size=5)
```

定义类型：function；[源码第 160 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:160)。

使用 5x5 窗口最小二乘法求解方程组: w_a1*X + w_b1*Y = rad1 w_a2*X + w_b2*Y = rad2  X, Y: 待求的两组分辐射 (如 X=光照土壤, Y=阴影土壤+植被)

### `solve_2x2_system_5x5.clean`

```python
solve_2x2_system_5x5.clean(img)
```

定义类型：nested；[源码第 172 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:172)。

无 docstring；算法解释见人工审阅章节。

### `solve_2x2_system_5x5.box_sum`

```python
solve_2x2_system_5x5.box_sum(img)
```

定义类型：nested；[源码第 189 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:189)。

无 docstring；算法解释见人工审阅章节。

### `solve_constrained_vectorized1`

```python
solve_constrained_vectorized1(rad_e, rad_i, w2, w3, w5, w6, bs1_fixed, dif=0.5)
```

定义类型：function；[源码第 225 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:225)。

只应用约束 1: bs2 <= bs1_fixed

### `solve_constrained_vectorized2`

```python
solve_constrained_vectorized2(rad_e, rad_i, w2, w3, w5, w6, bs1_fixed, dif=0.5)
```

定义类型：function；[源码第 247 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:247)。

只应用约束 2: |bs2 - bv| <= dif

### `solve_constrained_vectorized2.get_sse`

```python
solve_constrained_vectorized2.get_sse(b2, v)
```

定义类型：nested；[源码第 254 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:254)。

无 docstring；算法解释见人工审阅章节。

### `solve_joint_vectorized_with_prior`

```python
solve_joint_vectorized_with_prior(rad_e, rad_i, w, x_prior, lmbda=0.5)
```

定义类型：function；[源码第 290 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:290)。

无 docstring；算法解释见人工审阅章节。

### `parse_hours`

```python
parse_hours(value)
```

定义类型：function；[源码第 334 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:334)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:146](C:/work/ls4t/tests/test_msg_case_dependencies.py:146)

### `parse_args`

```python
parse_args()
```

定义类型：function；[源码第 341 行](C:/work/ls4t/cases/msg/msg_lsct_iter.py:341)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_lst_fit.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_lst_fit.py)；581 行，20 个定义。

### `parse_hours`

```python
parse_hours(value: str | None) -> set[int] | None
```

定义类型：function；[源码第 64 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:64)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:146](C:/work/ls4t/tests/test_msg_case_dependencies.py:146)

### `timestamp_from_name`

```python
timestamp_from_name(path: Path) -> datetime
```

定义类型：function；[源码第 73 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:73)。

无 docstring；算法解释见人工审阅章节。

### `grid_index`

```python
grid_index(latitude: np.ndarray, longitude: np.ndarray, rows: int, columns: int, resolution: float) -> tuple[np.ndarray, np.ndarray]
```

定义类型：function；[源码第 80 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:80)。

无 docstring；算法解释见人工审阅章节。

### `read_raster`

```python
read_raster(path: Path, scale: float=1.0) -> np.ndarray
```

定义类型：function；[源码第 96 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:96)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization_raster.py:9](C:/work/ls4t/tests/test_normalization_raster.py:9)

### `sample_global_raster`

```python
sample_global_raster(path: Path, row_index: np.ndarray, column_index: np.ndarray, scale: float=1.0, dtype=np.float32) -> np.ndarray
```

定义类型：function；[源码第 110 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:110)。

无 docstring；算法解释见人工审阅章节。

### `load_coefficients`

```python
load_coefficients(path: Path) -> np.ndarray
```

定义类型：function；[源码第 133 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:133)。

无 docstring；算法解释见人工审阅章节。

### `load_lai`

```python
load_lai(path: Path) -> np.ndarray
```

定义类型：function；[源码第 142 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:142)。

无 docstring；算法解释见人工审阅章节。

### `tcwv_path`

```python
tcwv_path(root: Path, timestamp: datetime) -> Path
```

定义类型：function；[源码第 154 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:154)。

无 docstring；算法解释见人工审阅章节。

### `load_tcwv_slice`

```python
load_tcwv_slice(root: Path, timestamp: datetime) -> np.ndarray
```

定义类型：function；[源码第 158 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:158)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:172](C:/work/ls4t/tests/test_msg_case_dependencies.py:172)

### `solar_day_mask`

```python
solar_day_mask(timestamp: datetime, latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray
```

定义类型：function；[源码第 183 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:183)。

无 docstring；算法解释见人工审阅章节。

### `retrieve_lst`

```python
retrieve_lst(bt108: np.ndarray, bt120: np.ndarray, view_zenith: np.ndarray, tcwv_cm: np.ndarray, soil_emissivity108: np.ndarray, soil_emissivity120: np.ndarray, vegetation_emissivity108: np.ndarray, vegetation_emissivity120: np.ndarray, lai: np.ndarray, land_mask: np.ndarray, day_mask: np.ndarray, coefficients_day: np.ndarray, coefficients_night: np.ndarray) -> np.ndarray
```

定义类型：function；[源码第 213 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:213)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:186](C:/work/ls4t/tests/test_msg_case_dependencies.py:186)

### `find_lai_file`

```python
find_lai_file(lai_root: Path, timestamp: datetime) -> Path
```

定义类型：function；[源码第 309 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:309)。

无 docstring；算法解释见人工审阅章节。

### `read_native_brightness_temperatures`

```python
read_native_brightness_temperatures(path: Path) -> tuple[np.ndarray, np.ndarray]
```

定义类型：function；[源码第 317 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:317)。

无 docstring；算法解释见人工审阅章节。

### `read_brightness_temperatures`

```python
read_brightness_temperatures(path: Path, input_format: str) -> tuple[np.ndarray, np.ndarray]
```

定义类型：function；[源码第 333 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:333)。

无 docstring；算法解释见人工审阅章节。

### `write_product`

```python
write_product(path: Path, lst: np.ndarray, timestamp: datetime, source: Path) -> None
```

定义类型：function；[源码第 349 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:349)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_products.py:6](C:/work/ls4t/tests/test_products.py:6)

### `build_static_inputs`

```python
build_static_inputs(args, profile: DiskProfile) -> dict[str, np.ndarray]
```

定义类型：function；[源码第 369 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:369)。

无 docstring；算法解释见人工审阅章节。

### `process_file`

```python
process_file(path: Path, args, profile: DiskProfile, static: dict, coefficients) -> Path
```

定义类型：function；[源码第 412 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:412)。

无 docstring；算法解释见人工审阅章节。

### `discover`

```python
discover(args) -> list[Path]
```

定义类型：function；[源码第 457 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:457)。

无 docstring；算法解释见人工审阅章节。

### `parse_args`

```python
parse_args()
```

定义类型：function；[源码第 482 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:482)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 516 行](C:/work/ls4t/cases/msg/msg_lst_fit.py:516)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_project_euro.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_project_euro.py)；8 行，0 个定义。

## cases/msg/msg_project_euro_lai.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_project_euro_lai.py)；8 行，0 个定义。

## cases/msg/msg_project_hdf5.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_project_hdf5.py)；251 行，7 个定义。

### `parse_hours`

```python
parse_hours(value: str | None) -> set[int] | None
```

定义类型：function；[源码第 55 行](C:/work/ls4t/cases/msg/msg_project_hdf5.py:55)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_case_dependencies.py:146](C:/work/ls4t/tests/test_msg_case_dependencies.py:146)

### `iter_dates`

```python
iter_dates(start: date, end: date)
```

定义类型：function；[源码第 64 行](C:/work/ls4t/cases/msg/msg_project_hdf5.py:64)。

无 docstring；算法解释见人工审阅章节。

### `load_static_latlon`

```python
load_static_latlon(latitude_path: Path, longitude_path: Path)
```

定义类型：function；[源码第 71 行](C:/work/ls4t/cases/msg/msg_project_hdf5.py:71)。

无 docstring；算法解释见人工审阅章节。

### `write_image`

```python
write_image(path: Path, data: np.ndarray, transform, projection: str) -> None
```

定义类型：function；[源码第 86 行](C:/work/ls4t/cases/msg/msg_project_hdf5.py:86)。

无 docstring；算法解释见人工审阅章节。

### `project_directory`

```python
project_directory(input_directory: Path, output_directory: Path, variable: str, source_latitude: np.ndarray, source_longitude: np.ndarray, hours: set[int] | None=None, overwrite: bool=False) -> dict[str, int]
```

定义类型：function；[源码第 111 行](C:/work/ls4t/cases/msg/msg_project_hdf5.py:111)。

无 docstring；算法解释见人工审阅章节。

### `build_parser`

```python
build_parser(default_product: str | None=None) -> argparse.ArgumentParser
```

定义类型：function；[源码第 187 行](C:/work/ls4t/cases/msg/msg_project_hdf5.py:187)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main(default_product: str | None=None) -> None
```

定义类型：function；[源码第 208 行](C:/work/ls4t/cases/msg/msg_project_hdf5.py:208)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_project_iodc.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_project_iodc.py)；8 行，0 个定义。

## cases/msg/msg_site_extract_csv.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_extract_csv.py)；154 行，0 个定义。

## cases/msg/msg_site_extract_lai.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_extract_lai.py)；152 行，0 个定义。

## cases/msg/msg_site_extract_lst.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_extract_lst.py)；201 行，0 个定义。

## cases/msg/msg_site_extract_series.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_extract_series.py)；205 行，3 个定义。

### `site_pixels`

```python
site_pixels() -> pd.DataFrame
```

定义类型：function；[源码第 53 行](C:/work/ls4t/cases/msg/msg_site_extract_series.py:53)。

无 docstring；算法解释见人工审阅章节。

### `day_iter`

```python
day_iter(start: str, end: str, step: int)
```

定义类型：function；[源码第 76 行](C:/work/ls4t/cases/msg/msg_site_extract_series.py:76)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> int
```

定义类型：function；[源码第 86 行](C:/work/ls4t/cases/msg/msg_site_extract_series.py:86)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_site_extract_static.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_extract_static.py)；112 行，0 个定义。

## cases/msg/msg_site_fit.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_fit.py)；223 行，3 个定义。

### `fitting_DTCRL`

```python
fitting_DTCRL(obs, pst, fhs, fn, x0)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/msg/msg_site_fit.py:17)。

无 docstring；算法解释见人工审阅章节。

### `fitting_DTC`

```python
fitting_DTC(obs, pst, x0)
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/msg/msg_site_fit.py:23)。

无 docstring；算法解释见人工审阅章节。

### `fitting_DTCLSFRL`

```python
fitting_DTCLSFRL(obs, pst, klsf, fhs, fn, x0)
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/msg/msg_site_fit.py:27)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_site_repro_lsct.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_repro_lsct.py)；315 行，5 个定义。

### `load_evora`

```python
load_evora() -> dict
```

定义类型：function；[源码第 81 行](C:/work/ls4t/cases/msg/msg_site_repro_lsct.py:81)。

无 docstring；算法解释见人工审阅章节。

### `corrected`

```python
corrected(frame: pd.DataFrame, col: str, emis: float) -> pd.Series
```

定义类型：function；[源码第 94 行](C:/work/ls4t/cases/msg/msg_site_repro_lsct.py:94)。

Emissivity/sky correction of the legacy recipe, kept in degC.

同名测试引用：[tests/test_kernel_models.py:43](C:/work/ls4t/tests/test_kernel_models.py:43)

### `hourly`

```python
hourly(frame: pd.DataFrame, inf_col: str, mea_col: str, thr: float | None) -> pd.DataFrame
```

定义类型：function；[源码第 101 行](C:/work/ls4t/cases/msg/msg_site_repro_lsct.py:101)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_stream_era5.py:76](C:/work/ls4t/tests/test_stream_era5.py:76)

### `metrics`

```python
metrics(obs, pred) -> dict
```

定义类型：function；[源码第 120 行](C:/work/ls4t/cases/msg/msg_site_repro_lsct.py:120)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:71](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:71)

### `main`

```python
main() -> int
```

定义类型：function；[源码第 140 行](C:/work/ls4t/cases/msg/msg_site_repro_lsct.py:140)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_site_repro_lst.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_repro_lst.py)；217 行，6 个定义。

### `load_satellite`

```python
load_satellite() -> pd.DataFrame
```

定义类型：function；[源码第 74 行](C:/work/ls4t/cases/msg/msg_site_repro_lst.py:74)。

无 docstring；算法解释见人工审阅章节。

### `load_measured`

```python
load_measured() -> pd.DataFrame
```

定义类型：function；[源码第 84 行](C:/work/ls4t/cases/msg/msg_site_repro_lst.py:84)。

无 docstring；算法解释见人工审阅章节。

### `build_reference`

```python
build_reference(df_merge: pd.DataFrame) -> pd.DataFrame
```

定义类型：function；[源码第 93 行](C:/work/ls4t/cases/msg/msg_site_repro_lst.py:93)。

无 docstring；算法解释见人工审阅章节。

### `wide_table`

```python
wide_table(df_merge: pd.DataFrame) -> pd.DataFrame
```

定义类型：function；[源码第 104 行](C:/work/ls4t/cases/msg/msg_site_repro_lst.py:104)。

无 docstring；算法解释见人工审阅章节。

### `metrics`

```python
metrics(y_true: pd.Series, y_pred: pd.Series) -> dict
```

定义类型：function；[源码第 118 行](C:/work/ls4t/cases/msg/msg_site_repro_lst.py:118)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:71](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:71)

### `main`

```python
main() -> int
```

定义类型：function；[源码第 125 行](C:/work/ls4t/cases/msg/msg_site_repro_lst.py:125)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_site_stats.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_stats.py)；249 行，0 个定义。

## cases/msg/msg_site_validate.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_validate.py)；347 行，7 个定义。

### `calculate_tsheld`

```python
calculate_tsheld(sza_arr)
```

定义类型：function；[源码第 28 行](C:/work/ls4t/cases/msg/msg_site_validate.py:28)。

无 docstring；算法解释见人工审阅章节。

### `kelvin2celsius`

```python
kelvin2celsius(series)
```

定义类型：function；[源码第 33 行](C:/work/ls4t/cases/msg/msg_site_validate.py:33)。

无 docstring；算法解释见人工审阅章节。

### `read_field_data`

```python
read_field_data(site_id, field_dir=FIELD_DATA_DIR)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/cases/msg/msg_site_validate.py:38)。

无 docstring；算法解释见人工审阅章节。

### `batch_match_inversion_field`

```python
batch_match_inversion_field(site_inv_df, field_df, site_name, time_window=30)
```

定义类型：function；[源码第 71 行](C:/work/ls4t/cases/msg/msg_site_validate.py:71)。

无 docstring；算法解释见人工审阅章节。

### `calculate_metrics`

```python
calculate_metrics(obs, pred)
```

定义类型：function；[源码第 150 行](C:/work/ls4t/cases/msg/msg_site_validate.py:150)。

无 docstring；算法解释见人工审阅章节。

### `process_single_site`

```python
process_single_site(site, full_inversion_df)
```

定义类型：function；[源码第 173 行](C:/work/ls4t/cases/msg/msg_site_validate.py:173)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 221 行](C:/work/ls4t/cases/msg/msg_site_validate.py:221)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_site_validate_multisite.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py)；416 行，9 个定义。

### `load_satellite`

```python
load_satellite(path: str=SITE_RESULTS) -> pd.DataFrame
```

定义类型：function；[源码第 70 行](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py:70)。

Load the cached site extraction, or a fresh sample written by extract_site_series.py.

### `load_field`

```python
load_field(site: str) -> pd.DataFrame | None
```

定义类型：function；[源码第 90 行](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py:90)。

无 docstring；算法解释见人工审阅章节。

### `bracket_hourly`

```python
bracket_hourly(field: pd.DataFrame) -> pd.DataFrame
```

定义类型：function；[源码第 113 行](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py:113)。

Mean of the two half-hour slots bracketing each overpass hour.

### `match`

```python
match(sat: pd.DataFrame, field: pd.DataFrame, mode: str) -> pd.DataFrame
```

定义类型：function；[源码第 120 行](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py:120)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:252](C:/work/ls4t/tests/test_africa_download.py:252)、[tests/test_annual_cycle.py:43](C:/work/ls4t/tests/test_annual_cycle.py:43)、[tests/test_dual_thermal_sensors.py:107](C:/work/ls4t/tests/test_dual_thermal_sensors.py:107)、[tests/test_flat_structure.py:184](C:/work/ls4t/tests/test_flat_structure.py:184)、[tests/test_kernel_atc_case.py:47](C:/work/ls4t/tests/test_kernel_atc_case.py:47)、[tests/test_kernel_models.py:56](C:/work/ls4t/tests/test_kernel_models.py:56)、[tests/test_multisource_normalization.py:23](C:/work/ls4t/tests/test_multisource_normalization.py:23)、[tests/test_normalization.py:59](C:/work/ls4t/tests/test_normalization.py:59)、[tests/test_normalization_raster.py:58](C:/work/ls4t/tests/test_normalization_raster.py:58)、[tests/test_retrieval.py:35](C:/work/ls4t/tests/test_retrieval.py:35)、[tests/test_slstr_products.py:42](C:/work/ls4t/tests/test_slstr_products.py:42)、[tests/test_south_america_components.py:114](C:/work/ls4t/tests/test_south_america_components.py:114)、[tests/test_south_america_monthly_components.py:56](C:/work/ls4t/tests/test_south_america_monthly_components.py:56)、[tests/test_south_america_native_recovery.py:65](C:/work/ls4t/tests/test_south_america_native_recovery.py:65)、[tests/test_stream_era5.py:76](C:/work/ls4t/tests/test_stream_era5.py:76)

### `metrics`

```python
metrics(obs, pred) -> dict
```

定义类型：function；[源码第 132 行](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py:132)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_aatsr_case_dependencies.py:71](C:/work/ls4t/tests/test_aatsr_case_dependencies.py:71)

### `tsheld`

```python
tsheld(sza: np.ndarray) -> np.ndarray
```

定义类型：function；[源码第 154 行](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py:154)。

无 docstring；算法解释见人工审阅章节。

### `solar_zenith`

```python
solar_zenith(site: str, times: pd.Series) -> np.ndarray
```

定义类型：function；[源码第 158 行](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py:158)。

Solar zenith angle for a site, used when the extraction carries no SZA.

同名测试引用：[tests/test_africa_download.py:45](C:/work/ls4t/tests/test_africa_download.py:45)

### `qc_cascade`

```python
qc_cascade(merged: pd.DataFrame, inf_col: str, mea_col: str) -> pd.DataFrame
```

定义类型：function；[源码第 172 行](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py:172)。

Legacy vs improved quality control, evaluated on the same matched sample.

### `main`

```python
main() -> int
```

定义类型：function；[源码第 196 行](C:/work/ls4t/cases/msg/msg_site_validate_multisite.py:196)。

无 docstring；算法解释见人工审阅章节。

## cases/msg/msg_smoke_test.py

源码：[打开文件](C:/work/ls4t/cases/msg/msg_smoke_test.py)；162 行，4 个定义。

### `file_hash`

```python
file_hash(path: Path) -> str
```

定义类型：function；[源码第 21 行](C:/work/ls4t/cases/msg/msg_smoke_test.py:21)。

无 docstring；算法解释见人工审阅章节。

### `projected_filename`

```python
projected_filename(product_name: str, stamp: str) -> str
```

定义类型：function；[源码第 29 行](C:/work/ls4t/cases/msg/msg_smoke_test.py:29)。

无 docstring；算法解释见人工审阅章节。

### `parse_args`

```python
parse_args()
```

定义类型：function；[源码第 37 行](C:/work/ls4t/cases/msg/msg_smoke_test.py:37)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 47 行](C:/work/ls4t/cases/msg/msg_smoke_test.py:47)。

无 docstring；算法解释见人工审阅章节。

## cases/multisource-normalization/fit_models.py

源码：[打开文件](C:/work/ls4t/cases/multisource-normalization/fit_models.py)；136 行，4 个定义。

### `demo_samples`

```python
demo_samples()
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/multisource-normalization/fit_models.py:20)。

Controlled synthetic samples only; never label scores as ground accuracy.

同名测试引用：[tests/test_kernel_atc_case.py:17](C:/work/ls4t/tests/test_kernel_atc_case.py:17)

### `_samples`

```python
_samples(data, prefix, fields)
```

定义类型：function；[源码第 37 行](C:/work/ls4t/cases/multisource-normalization/fit_models.py:37)。

无 docstring；算法解释见人工审阅章节。

### `run_comparison`

```python
run_comparison(data, config)
```

定义类型：function；[源码第 51 行](C:/work/ls4t/cases/multisource-normalization/fit_models.py:51)。

Compare on a common held-out mask per domain; do not pick models on tests.

同名测试引用：[tests/test_kernel_atc_case.py:19](C:/work/ls4t/tests/test_kernel_atc_case.py:19)

### `main`

```python
main()
```

定义类型：function；[源码第 107 行](C:/work/ls4t/cases/multisource-normalization/fit_models.py:107)。

无 docstring；算法解释见人工审阅章节。

## cases/multisource-normalization/run.py

源码：[打开文件](C:/work/ls4t/cases/multisource-normalization/run.py)；168 行，7 个定义。

### `_resolve`

```python
_resolve(value, root)
```

定义类型：function；[源码第 21 行](C:/work/ls4t/cases/multisource-normalization/run.py:21)。

无 docstring；算法解释见人工审阅章节。

### `run_stage`

```python
run_stage(config_path, stage, *, overwrite=False)
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/multisource-normalization/run.py:30)。

Paths resolve relative to config, never relative to the caller's cwd.

同名测试引用：[tests/test_normalization_raster.py:94](C:/work/ls4t/tests/test_normalization_raster.py:94)

### `run_stage.inputs`

```python
run_stage.inputs(value)
```

定义类型：nested；[源码第 49 行](C:/work/ls4t/cases/multisource-normalization/run.py:49)。

无 docstring；算法解释见人工审阅章节。

### `run_stage.auxiliaries`

```python
run_stage.auxiliaries(value)
```

定义类型：nested；[源码第 61 行](C:/work/ls4t/cases/multisource-normalization/run.py:61)。

无 docstring；算法解释见人工审阅章节。

### `create_demo`

```python
create_demo(directory, *, downscale_method='linear', products_directory=None)
```

定义类型：function；[源码第 79 行](C:/work/ls4t/cases/multisource-normalization/run.py:79)。

Create two synthetic sensor scenes with known geometry/time biases.

同名测试引用：[tests/test_normalization_raster.py:91](C:/work/ls4t/tests/test_normalization_raster.py:91)

### `create_demo.save`

```python
create_demo.save(name, values, pixel)
```

定义类型：nested；[源码第 99 行](C:/work/ls4t/cases/multisource-normalization/run.py:99)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 143 行](C:/work/ls4t/cases/multisource-normalization/run.py:143)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/adaptive_year_run.py

源码：[打开文件](C:/work/ls4t/cases/slstr/adaptive_year_run.py)；156 行，6 个定义。

### `disk_busy_ms`

```python
disk_busy_ms(device)
```

定义类型：function；[源码第 17 行](C:/work/ls4t/cases/slstr/adaptive_year_run.py:17)。

无 docstring；算法解释见人工审阅章节。

### `available_gib`

```python
available_gib()
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/slstr/adaptive_year_run.py:25)。

无 docstring；算法解释见人工审阅章节。

### `history`

```python
history(path, region, stage)
```

定义类型：function；[源码第 32 行](C:/work/ls4t/cases/slstr/adaptive_year_run.py:32)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization_raster.py:101](C:/work/ls4t/tests/test_normalization_raster.py:101)

### `valid_report`

```python
valid_report(path, stage)
```

定义类型：function；[源码第 60 行](C:/work/ls4t/cases/slstr/adaptive_year_run.py:60)。

无 docstring；算法解释见人工审阅章节。

### `choose_workers`

```python
choose_workers(rows, region, stage)
```

定义类型：function；[源码第 77 行](C:/work/ls4t/cases/slstr/adaptive_year_run.py:77)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 98 行](C:/work/ls4t/cases/slstr/adaptive_year_run.py:98)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/run_amazon_europe_annual.py

源码：[打开文件](C:/work/ls4t/cases/slstr/run_amazon_europe_annual.py)；146 行，7 个定义。

### `stamp`

```python
stamp() -> str
```

定义类型：function；[源码第 40 行](C:/work/ls4t/cases/slstr/run_amazon_europe_annual.py:40)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:70](C:/work/ls4t/tests/test_msg_evo_sample.py:70)、[tests/test_south_america_components.py:55](C:/work/ls4t/tests/test_south_america_components.py:55)、[tests/test_south_america_monthly_components.py:98](C:/work/ls4t/tests/test_south_america_monthly_components.py:98)

### `report_path`

```python
report_path(region: str, year: int, stage: str) -> Path
```

定义类型：function；[源码第 44 行](C:/work/ls4t/cases/slstr/run_amazon_europe_annual.py:44)。

无 docstring；算法解释见人工审阅章节。

### `expected_exclusions`

```python
expected_exclusions(region: str, year: int) -> list[str]
```

定义类型：function；[源码第 52 行](C:/work/ls4t/cases/slstr/run_amazon_europe_annual.py:52)。

无 docstring；算法解释见人工审阅章节。

### `checked`

```python
checked(path: Path, stage: str, region: str, root: Path, year: int, bounds: tuple[float, ...]) -> bool
```

定义类型：function；[源码第 57 行](C:/work/ls4t/cases/slstr/run_amazon_europe_annual.py:57)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:102](C:/work/ls4t/tests/test_africa_download.py:102)

### `record`

```python
record(region: str, year: int, stage: str, code: int, path: Path) -> None
```

定义类型：function；[源码第 75 行](C:/work/ls4t/cases/slstr/run_amazon_europe_annual.py:75)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:41](C:/work/ls4t/tests/test_msg_evo_sample.py:41)

### `run_stage`

```python
run_stage(region: str, root: Path, year: int, bounds: tuple[float, ...], disk: str, stage: str, lst_report: Path | None=None) -> Path
```

定义类型：function；[源码第 82 行](C:/work/ls4t/cases/slstr/run_amazon_europe_annual.py:82)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization_raster.py:94](C:/work/ls4t/tests/test_normalization_raster.py:94)

### `main`

```python
main() -> int
```

定义类型：function；[源码第 123 行](C:/work/ls4t/cases/slstr/run_amazon_europe_annual.py:123)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_daily_mosaic_scene.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py)；585 行，17 个定义。

### `load_case`

```python
load_case(case_dir: Path, machine: str) -> dict
```

定义类型：function；[源码第 65 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:65)。

Read one case: grid window from case.toml, roots from the machine profile.

### `load_window`

```python
load_window(path: Path) -> dict
```

定义类型：function；[源码第 97 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:97)。

无 docstring；算法解释见人工审阅章节。

### `scene_day`

```python
scene_day(scene: str) -> str
```

定义类型：function；[源码第 104 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:104)。

无 docstring；算法解释见人工审阅章节。

### `scene_hhmmss`

```python
scene_hhmmss(scene: str) -> int
```

定义类型：function；[源码第 108 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:108)。

Acquisition start time of the granule as HHMMSS (the time of every pixel it contributes; the disk has no per-pixel time band).

### `day_scenes`

```python
day_scenes(root: Path, year: int, product: str) -> dict[str, list[str]]
```

定义类型：function；[源码第 115 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:115)。

无 docstring；算法解释见人工审阅章节。

### `make_geoloc_vrt`

```python
make_geoloc_vrt(vrt_path: Path, lon_path: Path, lat_path: Path, sources: list[tuple[Path, int]]) -> None
```

定义类型：function；[源码第 136 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:136)。

VRT of ``sources`` ((path, band) pairs) with the lon/lat pair as geolocation.  The cloud flag travels through the same VRT as the product band, so one ``gdal.Warp`` reads the data and its mask and the two cannot drift apart.

### `write_geolocation_raster`

```python
write_geolocation_raster(path: Path, array: np.ndarray, limit: float) -> None
```

定义类型：function；[源码第 184 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:184)。

Materialise integer hundredths-of-degree geolocation as Float32 degrees.  GDAL reads the geolocation arrays as plain degrees, so the x100 storage has to be unpacked first; invalid fill values become NaN.

### `write_array_raster`

```python
write_array_raster(path: Path, array: np.ndarray, gdal_type: int) -> None
```

定义类型：function；[源码第 202 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:202)。

In-memory copy of a scene band (used for the cropped LST window).

### `read_full`

```python
read_full(path: Path) -> np.ndarray
```

定义类型：function；[源码第 213 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:213)。

无 docstring；算法解释见人工审阅章节。

### `read_rows`

```python
read_rows(path: Path, rows=None) -> np.ndarray
```

定义类型：function；[源码第 222 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:222)。

无 docstring；算法解释见人工审阅章节。

### `footprint_box`

```python
footprint_box(root: Path, year: int, scene: str, view: str)
```

定义类型：function；[源码第 238 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:238)。

无 docstring；算法解释见人工审阅章节。

### `solar_zenith_deg`

```python
solar_zenith_deg(when: datetime, lat, lon)
```

定义类型：function；[源码第 254 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:254)。

Solar zenith angle (deg) - same formulas as the South America case.

同名测试引用：[tests/test_msg_evo_sample.py:106](C:/work/ls4t/tests/test_msg_evo_sample.py:106)、[tests/test_normalization_raster.py:36](C:/work/ls4t/tests/test_normalization_raster.py:36)

### `scene_is_day`

```python
scene_is_day(scene: str, box, win: dict, threshold: float) -> bool
```

定义类型：function；[源码第 272 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:272)。

Day when the median solar zenith angle of the footprint is below the threshold.

### `warp_block`

```python
warp_block(root: Path, year: int, scene: str, spec: dict, lon_path: Path, lat_path: Path, data_path: Path, window_box, tmpdir: Path, cloud_path: Path | None=None) -> np.ndarray | None
```

定义类型：function；[源码第 290 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:290)。

Warp one scene onto the requested sub-grid; returns the warped block.  With ``cloud_path`` the scene cloud flag is warped alongside the product and any pixel that is not clear (``cloud != 0``) is dropped.

### `composite_day`

```python
composite_day(task) -> dict
```

定义类型：function；[源码第 358 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:358)。

无 docstring；算法解释见人工审阅章节。

### `write_raster`

```python
write_raster(path: Path, array: np.ndarray, gdal_type: int, res: float, uint16_predictor: bool, win: dict) -> None
```

定义类型：function；[源码第 481 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:481)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 506 行](C:/work/ls4t/cases/slstr/slstr_daily_mosaic_scene.py:506)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_data_area.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_data_area.py)；983 行，0 个定义。

## cases/slstr/slstr_data_batch.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_data_batch.py)；396 行，6 个定义。

### `write_image_gdal`

```python
write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff', nodata_value=None)
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/slstr/slstr_data_batch.py:27)。

无 docstring；算法解释见人工审阅章节。

### `writevrt_nadir`

```python
writevrt_nadir(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 90 行](C:/work/ls4t/cases/slstr/slstr_data_batch.py:90)。

无 docstring；算法解释见人工审阅章节。

### `writevrt_obliq`

```python
writevrt_obliq(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 96 行](C:/work/ls4t/cases/slstr/slstr_data_batch.py:96)。

无 docstring；算法解释见人工审阅章节。

### `write_vrt`

```python
write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, bandnumber=1, data_type='UInt16', pixel_offset=0, pixel_step=1, line_offset=0, line_step=1, nodata_value=0, use_nan_for_float=False)
```

定义类型：function；[源码第 102 行](C:/work/ls4t/cases/slstr/slstr_data_batch.py:102)。

无 docstring；算法解释见人工审阅章节。

### `scale_and_convert_to_uint16`

```python
scale_and_convert_to_uint16(data, scale_factor, clip_range=(0, 65535))
```

定义类型：function；[源码第 148 行](C:/work/ls4t/cases/slstr/slstr_data_batch.py:148)。

无 docstring；算法解释见人工审阅章节。

### `process_single_scene`

```python
process_single_scene(k, fileName, indir_raw, indir_tif, cfg)
```

定义类型：function；[源码第 160 行](C:/work/ls4t/cases/slstr/slstr_data_batch.py:160)。

k: 索引 fileName: 文件名 indir_raw: 输入根目录 indir_tif: 输出根目录 cfg: 包含所有 ifextract_n, ratioforsimple 等开关的配置字典

## cases/slstr/slstr_data_scene.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_data_scene.py)；797 行，5 个定义。

### `write_image_gdal`

```python
write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff', nodata_value=None)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/cases/slstr/slstr_data_scene.py:38)。

保存数据，输出成tif格式 :param im_data: 数组 :param im_width: 列数 :param im_height: 行数 :param im_bands: 波段数 :param im_trans: 地理坐标 :param im_proj: 投影坐标 :param path: 路径 :param imageType: 输出格式（字符串，如'GTiff'） :param nodata_value: nodata值（可选） :return: 无

### `writevrt_nadir`

```python
writevrt_nadir(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 132 行](C:/work/ls4t/cases/slstr/slstr_data_scene.py:132)。

无 docstring；算法解释见人工审阅章节。

### `writevrt_obliq`

```python
writevrt_obliq(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 138 行](C:/work/ls4t/cases/slstr/slstr_data_scene.py:138)。

无 docstring；算法解释见人工审阅章节。

### `write_vrt`

```python
write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, bandnumber=1, data_type='UInt16', pixel_offset=0, pixel_step=1, line_offset=0, line_step=1, nodata_value=0, use_nan_for_float=False)
```

定义类型：function；[源码第 144 行](C:/work/ls4t/cases/slstr/slstr_data_scene.py:144)。

智能处理nodatavalue的VRT生成函数  :param nodata_value: 显式指定nodata值，如果为None则自动选择 :param use_nan_for_float: 浮点类型是否使用NaN作为nodata :return: 成功返回1

### `scale_and_convert_to_uint16`

```python
scale_and_convert_to_uint16(data, scale_factor, clip_range=(0, 65535))
```

定义类型：function；[源码第 212 行](C:/work/ls4t/cases/slstr/slstr_data_scene.py:212)。

缩放数据并转换为UInt16 :param data: 输入数据 :param scale_factor: 缩放因子 :param clip_range: 裁剪范围 :return: UInt16数据

## cases/slstr/slstr_data_scene_latlon.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_data_scene_latlon.py)；405 行，6 个定义。

### `write_image_gdal`

```python
write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff', nodata_value=None)
```

定义类型：function；[源码第 36 行](C:/work/ls4t/cases/slstr/slstr_data_scene_latlon.py:36)。

保存数据，输出成tif格式 :param im_data: 数组 :param im_width: 列数 :param im_height: 行数 :param im_bands: 波段数 :param im_trans: 地理坐标 :param im_proj: 投影坐标 :param path: 路径 :param imageType: 输出格式（字符串，如'GTiff'） :param nodata_value: nodata值（可选） :return: 无

### `writevrt_nadir`

```python
writevrt_nadir(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 130 行](C:/work/ls4t/cases/slstr/slstr_data_scene_latlon.py:130)。

无 docstring；算法解释见人工审阅章节。

### `writevrt_obliq`

```python
writevrt_obliq(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 136 行](C:/work/ls4t/cases/slstr/slstr_data_scene_latlon.py:136)。

无 docstring；算法解释见人工审阅章节。

### `write_vrt`

```python
write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, bandnumber=1, data_type='UInt16', pixel_offset=0, pixel_step=1, line_offset=0, line_step=1, nodata_value=0, use_nan_for_float=False)
```

定义类型：function；[源码第 142 行](C:/work/ls4t/cases/slstr/slstr_data_scene_latlon.py:142)。

智能处理nodatavalue的VRT生成函数  :param nodata_value: 显式指定nodata值，如果为None则自动选择 :param use_nan_for_float: 浮点类型是否使用NaN作为nodata :return: 成功返回1

### `scale_and_convert_to_uint16`

```python
scale_and_convert_to_uint16(data, scale_factor, clip_range=(0, 65535))
```

定义类型：function；[源码第 210 行](C:/work/ls4t/cases/slstr/slstr_data_scene_latlon.py:210)。

缩放数据并转换为UInt16 :param data: 输入数据 :param scale_factor: 缩放因子 :param clip_range: 裁剪范围 :return: UInt16数据

### `scale_and_convert_to_int16`

```python
scale_and_convert_to_int16(data, scale_factor, offset=0.0, clip_range=(-32768, 32767), fill_value=-32767)
```

定义类型：function；[源码第 231 行](C:/work/ls4t/cases/slstr/slstr_data_scene_latlon.py:231)。

将浮点数据缩放并转换为 Int16（有符号16位整数）  Parameters: ----------- data : numpy.ndarray     输入数据（浮点型经纬度等） scale_factor : float     缩放因子（例如 0.01 表示乘以100后存储） offset : float     偏置值（例如经纬度可能有偏移） clip_range : tuple     Int16的有效范围，默认 (-32768, 32767) fill_value : int     无效值的填充值（建

## cases/slstr/slstr_data_scene_origin.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_data_scene_origin.py)；597 行，5 个定义。

### `write_image_gdal`

```python
write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff', nodata_value=None)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/cases/slstr/slstr_data_scene_origin.py:38)。

保存数据，输出成tif格式 :param im_data: 数组 :param im_width: 列数 :param im_height: 行数 :param im_bands: 波段数 :param im_trans: 地理坐标 :param im_proj: 投影坐标 :param path: 路径 :param imageType: 输出格式（字符串，如'GTiff'） :param nodata_value: nodata值（可选） :return: 无

### `writevrt_nadir`

```python
writevrt_nadir(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 132 行](C:/work/ls4t/cases/slstr/slstr_data_scene_origin.py:132)。

无 docstring；算法解释见人工审阅章节。

### `writevrt_obliq`

```python
writevrt_obliq(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 138 行](C:/work/ls4t/cases/slstr/slstr_data_scene_origin.py:138)。

无 docstring；算法解释见人工审阅章节。

### `write_vrt`

```python
write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, bandnumber=1, data_type='UInt16', pixel_offset=0, pixel_step=1, line_offset=0, line_step=1, nodata_value=0, use_nan_for_float=False)
```

定义类型：function；[源码第 144 行](C:/work/ls4t/cases/slstr/slstr_data_scene_origin.py:144)。

智能处理nodatavalue的VRT生成函数  :param nodata_value: 显式指定nodata值，如果为None则自动选择 :param use_nan_for_float: 浮点类型是否使用NaN作为nodata :return: 成功返回1

### `scale_and_convert_to_uint16`

```python
scale_and_convert_to_uint16(data, scale_factor, clip_range=(0, 65535))
```

定义类型：function；[源码第 212 行](C:/work/ls4t/cases/slstr/slstr_data_scene_origin.py:212)。

缩放数据并转换为UInt16 :param data: 输入数据 :param scale_factor: 缩放因子 :param clip_range: 裁剪范围 :return: UInt16数据

## cases/slstr/slstr_data_scene_years.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_data_scene_years.py)；49 行，1 个定义。

### `main`

```python
main() -> int
```

定义类型：function；[源码第 18 行](C:/work/ls4t/cases/slstr/slstr_data_scene_years.py:18)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_era5_tcwv_daily.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_era5_tcwv_daily.py)；98 行，0 个定义。

## cases/slstr/slstr_lsct2_area.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lsct2_area.py)；103 行，0 个定义。

## cases/slstr/slstr_lsct2_scene.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lsct2_scene.py)；309 行，0 个定义。

## cases/slstr/slstr_lsct2_scene_parallel.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py)；622 行，13 个定义。

### `has_classified_empty_marker`

```python
has_classified_empty_marker(path: Path) -> bool
```

定义类型：function；[源码第 103 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:103)。

True only for a marker written with the reason-aware schema.  Legacy markers said only ``no valid pixel``.  Those are intentionally rediscovered once so cloud, water/non-land and processing failures are no longer collapsed into one bucket.

### `doy4`

```python
doy4(year: int, day: date) -> int
```

定义类型：function；[源码第 119 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:119)。

无 docstring；算法解释见人工审阅章节。

### `lai_file`

```python
lai_file(year: int, day: date) -> Path | None
```

定义类型：function；[源码第 123 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:123)。

无 docstring；算法解释见人工审阅章节。

### `discover`

```python
discover(root: Path, out_root: Path, out_layer: str, year: int, skip_scenes: set[str], only_days: set[str] | None=None, cloud_fallback_only: bool=False) -> dict[str, list[str]]
```

定义类型：function；[源码第 136 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:136)。

Scenes with an LST result but without an LSCT2 output, grouped by day.

### `load_state`

```python
load_state(emis_dir: Path, type_ref: Path, window: tuple[int, int, int, int]) -> dict
```

定义类型：function；[源码第 179 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:179)。

Load only the case window of the global rasters.  ``emis_dir``/``type_ref`` default to ``<root>/base/...`` but can be pointed at another disk: the heihe root has no ``base/`` of its own, its scenes are indexed on the same 0.01 deg grid as ``/media/hero/rs``.

### `load_state.read_window`

```python
load_state.read_window(path: Path, dtype) -> np.ndarray
```

定义类型：nested；[源码第 189 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:189)。

无 docstring；算法解释见人工审阅章节。

### `_init_worker`

```python
_init_worker(state: dict, root: str, out_root: str, out_layer: str, type_ref: str) -> None
```

定义类型：function；[源码第 221 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:221)。

无 docstring；算法解释见人工审阅章节。

### `index_map`

```python
index_map(ref_ds, lat: np.ndarray, lon: np.ndarray)
```

定义类型：function；[源码第 233 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:233)。

Same indices as loc2map() returns (row index first, then column index).

### `read_cloud`

```python
read_cloud(path: Path) -> np.ndarray | None
```

定义类型：function；[源码第 239 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:239)。

Read a cloud mask, treating a missing or corrupt TIFF as unavailable.

### `scene_window`

```python
scene_window(root: Path, year: int, by_day: dict[str, list[str]], days: list[str], type_ref: Path) -> tuple[int, int, int, int]
```

定义类型：function；[源码第 250 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:250)。

Return the smallest global-grid window containing this processing batch.

### `lsct2_scene`

```python
lsct2_scene(scene: str, year: int, lat: np.ndarray, lon: np.ndarray, lai0: np.ndarray, out_file: Path) -> str
```

定义类型：function；[源码第 287 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:287)。

Run one scene and return a written/skipped/no-valid reason status.  ``no_valid_*`` statuses deliberately distinguish water/non-land footprints from cloudy land observations.  Water and scenes outside the case are not missing land products; cloud and low-LAI st

### `process_day`

```python
process_day(task)
```

定义类型：function；[源码第 454 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:454)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 514 行](C:/work/ls4t/cases/slstr/slstr_lsct2_scene_parallel.py:514)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_lsct3_area.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lsct3_area.py)；105 行，0 个定义。

## cases/slstr/slstr_lsct3_bayes_scene.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py)；425 行，13 个定义。

### `read`

```python
read(path: Path) -> np.ndarray
```

定义类型：function；[源码第 46 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:46)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:262](C:/work/ls4t/tests/test_africa_download.py:262)

### `solar_from_time`

```python
solar_from_time(scene: str, lat: np.ndarray, lon: np.ndarray)
```

定义类型：function；[源码第 56 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:56)。

无 docstring；算法解释见人工审阅章节。

### `derivative`

```python
derivative(T)
```

定义类型：function；[源码第 79 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:79)。

无 docstring；算法解释见人工审阅章节。

### `box_sum`

```python
box_sum(a: np.ndarray) -> np.ndarray
```

定义类型：function；[源码第 83 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:83)。

无 docstring；算法解释见人工审阅章节。

### `write`

```python
write(path: Path, data: np.ndarray, description: str)
```

定义类型：function；[源码第 87 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:87)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:96](C:/work/ls4t/tests/test_south_america_components.py:96)、[tests/test_south_america_monthly_components.py:108](C:/work/ls4t/tests/test_south_america_monthly_components.py:108)

### `setup`

```python
setup(root: str, bounds: tuple[float, float, float, float], lai_root: str | None=None, base_root: str | None=None)
```

定义类型：function；[源码第 100 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:100)。

无 docstring；算法解释见人工审阅章节。

### `lai_path_for_scene`

```python
lai_path_for_scene(year: int, scene: str) -> Path
```

定义类型：function；[源码第 111 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:111)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:107](C:/work/ls4t/tests/test_south_america_components.py:107)

### `lai_for_scene`

```python
lai_for_scene(year: int, scene: str)
```

定义类型：function；[源码第 127 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:127)。

无 docstring；算法解释见人工审阅章节。

### `cached_result`

```python
cached_result(root: Path, year: int, scene_name: str, bounds) -> tuple | None
```

定义类型：function；[源码第 137 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:137)。

Reuse complete products or a current, explicit empty result.

同名测试引用：[tests/test_south_america_components.py:58](C:/work/ls4t/tests/test_south_america_components.py:58)

### `input_stamps`

```python
input_stamps(root: Path, year: int, scene_name: str) -> dict
```

定义类型：function；[源码第 180 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:180)。

Record source changes without hashing every full-scene raster.

### `mark_empty`

```python
mark_empty(out: Path, year: int, scene_name: str, reason: str)
```

定义类型：function；[源码第 195 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:195)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:52](C:/work/ls4t/tests/test_south_america_components.py:52)

### `scene`

```python
scene(year: int, scene_name: str)
```

定义类型：function；[源码第 210 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:210)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:26](C:/work/ls4t/tests/test_africa_download.py:26)、[tests/test_dual_thermal_sensors.py:129](C:/work/ls4t/tests/test_dual_thermal_sensors.py:129)、[tests/test_multisource_normalization.py:77](C:/work/ls4t/tests/test_multisource_normalization.py:77)、[tests/test_normalization.py:81](C:/work/ls4t/tests/test_normalization.py:81)、[tests/test_south_america_components.py:85](C:/work/ls4t/tests/test_south_america_components.py:85)、[tests/test_south_america_monthly_components.py:89](C:/work/ls4t/tests/test_south_america_monthly_components.py:89)、[tests/test_south_america_remaining.py:36](C:/work/ls4t/tests/test_south_america_remaining.py:36)、[tests/test_spatial_modes.py:19](C:/work/ls4t/tests/test_spatial_modes.py:19)、[tests/test_standalone_cases.py:74](C:/work/ls4t/tests/test_standalone_cases.py:74)、[tests/test_tsharp.py:9](C:/work/ls4t/tests/test_tsharp.py:9)

### `main`

```python
main()
```

定义类型：function；[源码第 370 行](C:/work/ls4t/cases/slstr/slstr_lsct3_bayes_scene.py:370)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_lsct3_scene.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lsct3_scene.py)；337 行，1 个定义。

### `fitting_with_ridge`

```python
fitting_with_ridge(bb, ww)
```

定义类型：function；[源码第 28 行](C:/work/ls4t/cases/slstr/slstr_lsct3_scene.py:28)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_lst_area.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lst_area.py)；393 行，0 个定义。

## cases/slstr/slstr_lst_batch.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lst_batch.py)；200 行，1 个定义。

### `invert_lst`

```python
invert_lst(indir, infile_bt8, infile_bt9, infile_vza)
```

定义类型：function；[源码第 58 行](C:/work/ls4t/cases/slstr/slstr_lst_batch.py:58)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_lst_scene.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lst_scene.py)；452 行，0 个定义。

## cases/slstr/slstr_lst_scene_parallel.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py)；574 行，15 个定义。

### `find_base_file`

```python
find_base_file(base: Path, name: str) -> Path
```

定义类型：function；[源码第 95 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:95)。

The case keeps its auxiliary files in emis/, type/ and base/ subfolders.

### `doy4`

```python
doy4(year: int, day: date) -> int
```

定义类型：function；[源码第 104 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:104)。

无 docstring；算法解释见人工审阅章节。

### `lai_file`

```python
lai_file(year: int, day: date) -> Path | None
```

定义类型：function；[源码第 108 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:108)。

无 docstring；算法解释见人工审阅章节。

### `tcwv_file`

```python
tcwv_file(tcwv_root: Path, day_str: str) -> Path | None
```

定义类型：function；[源码第 134 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:134)。

无 docstring；算法解释见人工审阅章节。

### `load_tcwv_cm`

```python
load_tcwv_cm(path: Path) -> np.ndarray
```

定义类型：function；[源码第 139 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:139)。

Decode known HDF5 layouts; integer fields require an explicit scale.

同名测试引用：[tests/test_south_america_components.py:115](C:/work/ls4t/tests/test_south_america_components.py:115)

### `scene_overlaps_bounds`

```python
scene_overlaps_bounds(tif_dir: Path, bounds: tuple[float, float, float, float]) -> bool
```

定义类型：function；[源码第 158 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:158)。

Conservative footprint screen from subsampled oblique geolocation.

### `discover`

```python
discover(root: Path, year: int, overwrite: bool=False, bounds: tuple[float, float, float, float] | None=None, excluded: set[str] | None=None) -> dict[str, list[str]]
```

定义类型：function；[源码第 183 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:183)。

Scene directories with usable input views, including existing results on overwrite.

### `drop_file_cache`

```python
drop_file_cache(path: Path) -> None
```

定义类型：function；[源码第 226 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:226)。

Release clean input pages after GDAL/HDF5 has closed the file.

### `load_state`

```python
load_state(root: Path, base: Path, type_ref: Path, emis_pair: tuple[str, str]) -> dict
```

定义类型：function；[源码第 240 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:240)。

Global base rasters; inherited by the workers through fork.

### `_init_worker`

```python
_init_worker(state: dict, root: str, out_root: str, tcwv_root: str) -> None
```

定义类型：function；[源码第 257 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:257)。

无 docstring；算法解释见人工审阅章节。

### `_init_worker_from_files`

```python
_init_worker_from_files(root, base, type_ref, emis_pair, out_root, tcwv_root, overwrite, lai_root)
```

定义类型：function；[源码第 264 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:264)。

Windows spawns workers; avoid pickling multi-GB global raster arrays.

### `grid_index`

```python
grid_index(lat: np.ndarray, lon: np.ndarray, nrow: int, ncol: int, res: float) -> tuple[np.ndarray, np.ndarray]
```

定义类型：function；[源码第 271 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:271)。

Row/column of a global north-to-south, -180..180 regular grid.

### `lst_view`

```python
lst_view(view: str, tif_dir: Path, out_file: Path, lai0: np.ndarray, tcw_day: np.ndarray, hour: int, overwrite: bool) -> str
```

定义类型：function；[源码第 281 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:281)。

LST for one view of one scene: 'written', 'empty' or 'skipped'.

### `process_day`

```python
process_day(task) -> dict
```

定义类型：function；[源码第 384 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:384)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 447 行](C:/work/ls4t/cases/slstr/slstr_lst_scene_parallel.py:447)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_monthly_paired.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_monthly_paired.py)；133 行，3 个定义。

### `load_case`

```python
load_case(case_dir: Path, machine: str) -> dict
```

定义类型：function；[源码第 36 行](C:/work/ls4t/cases/slstr/slstr_monthly_paired.py:36)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 54 行](C:/work/ls4t/cases/slstr/slstr_monthly_paired.py:54)。

无 docstring；算法解释见人工审阅章节。

### `main.log`

```python
main.log(text: str) -> None
```

定义类型：nested；[源码第 82 行](C:/work/ls4t/cases/slstr/slstr_monthly_paired.py:82)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_proj_scene.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_proj_scene.py)；228 行，5 个定义。

### `write_image_gdal`

```python
write_image_gdal(im_data, im_width, im_height, im_bands, im_trans, im_proj, path, imageType='GTiff', nodata_value=None)
```

定义类型：function；[源码第 15 行](C:/work/ls4t/cases/slstr/slstr_proj_scene.py:15)。

保存数据，输出成tif格式 :param im_data: 数组 :param im_width: 列数 :param im_height: 行数 :param im_bands: 波段数 :param im_trans: 地理坐标 :param im_proj: 投影坐标 :param path: 路径 :param imageType: 输出格式（字符串，如'GTiff'） :param nodata_value: nodata值（可选） :return: 无

### `writevrt_nadir`

```python
writevrt_nadir(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 109 行](C:/work/ls4t/cases/slstr/slstr_proj_scene.py:109)。

无 docstring；算法解释见人工审阅章节。

### `writevrt_obliq`

```python
writevrt_obliq(infile, datafile, xfile, yfile, data_type='UInt16', nodata_value=0)
```

定义类型：function；[源码第 115 行](C:/work/ls4t/cases/slstr/slstr_proj_scene.py:115)。

无 docstring；算法解释见人工审阅章节。

### `write_vrt`

```python
write_vrt(vrtfile, datafile, xfile, yfile, xscale, yscale, bandnumber=1, data_type='UInt16', pixel_offset=0, pixel_step=1, line_offset=0, line_step=1, nodata_value=0, use_nan_for_float=False)
```

定义类型：function；[源码第 121 行](C:/work/ls4t/cases/slstr/slstr_proj_scene.py:121)。

智能处理nodatavalue的VRT生成函数  :param nodata_value: 显式指定nodata值，如果为None则自动选择 :param use_nan_for_float: 浮点类型是否使用NaN作为nodata :return: 成功返回1

### `scale_and_convert_to_uint16`

```python
scale_and_convert_to_uint16(data, scale_factor, clip_range=(0, 65535))
```

定义类型：function；[源码第 189 行](C:/work/ls4t/cases/slstr/slstr_proj_scene.py:189)。

缩放数据并转换为UInt16 :param data: 输入数据 :param scale_factor: 缩放因子 :param clip_range: 裁剪范围 :return: UInt16数据

## cases/slstr/slstr_scene_coverage.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_scene_coverage.py)；300 行，4 个定义。

### `load_case`

```python
load_case(case_dir: Path, machine: str) -> dict
```

定义类型：function；[源码第 52 行](C:/work/ls4t/cases/slstr/slstr_scene_coverage.py:52)。

无 docstring；算法解释见人工审阅章节。

### `sample_geo`

```python
sample_geo(path: Path, sample_rows: int=SAMPLE_ROWS, bands: int=3) -> np.ndarray
```

定义类型：function；[源码第 71 行](C:/work/ls4t/cases/slstr/slstr_scene_coverage.py:71)。

``bands`` evenly spaced row bands of a geolocation band, in degrees.  The nodata value is *kept*: latitude and longitude have to be filtered with one shared mask, otherwise the two arrays shrink by different amounts and stop being pixel aligned.

### `classify_scene`

```python
classify_scene(root: Path, year: int, scene: str, window: dict, classif0: np.ndarray, res: float, sample_rows: int=SAMPLE_ROWS, bands: int=3, row0: int=0, col0: int=0) -> dict
```

定义类型：function；[源码第 91 行](C:/work/ls4t/cases/slstr/slstr_scene_coverage.py:91)。

Which views of this scene can touch the window on a valid land class.  ``useless`` lists the views that cannot: no sampled pixel both inside the window and on a land-cover class the retrieval keeps (``0 < class < 17``).

### `main`

```python
main() -> None
```

定义类型：function；[源码第 172 行](C:/work/ls4t/cases/slstr/slstr_scene_coverage.py:172)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_unzip_batch.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_unzip_batch.py)；201 行，4 个定义。

### `safe_print`

```python
safe_print(*args, **kwargs)
```

定义类型：function；[源码第 54 行](C:/work/ls4t/cases/slstr/slstr_unzip_batch.py:54)。

线程安全的打印函数

### `unzip_file_SLSTR`

```python
unzip_file_SLSTR(zipfilename, outdir)
```

定义类型：function；[源码第 60 行](C:/work/ls4t/cases/slstr/slstr_unzip_batch.py:60)。

解压zip文件中指定的文件 :param zipfilename: 要解压文件名称 :param outdir: 输出位置

### `process_single_file`

```python
process_single_file(file_info)
```

定义类型：function；[源码第 89 行](C:/work/ls4t/cases/slstr/slstr_unzip_batch.py:89)。

处理单个文件的解压任务 :param file_info: 包含文件信息的元组 (i, total, fileName, fileName0, year, indir_zip, outdir_unzip) :return: (fileName, success_status)

### `main`

```python
main()
```

定义类型：function；[源码第 122 行](C:/work/ls4t/cases/slstr/slstr_unzip_batch.py:122)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr/slstr_unzip_scene.py

源码：[打开文件](C:/work/ls4t/cases/slstr/slstr_unzip_scene.py)；20 行，0 个定义。

## cases/slstr-africa/connect_earthdata.py

源码：[打开文件](C:/work/ls4t/cases/slstr-africa/connect_earthdata.py)；152 行，8 个定义。

### `page`

```python
page(content)
```

定义类型：function；[源码第 21 行](C:/work/ls4t/cases/slstr-africa/connect_earthdata.py:21)。

无 docstring；算法解释见人工审阅章节。

### `ConnectionServer.__init__`

```python
ConnectionServer.__init__(self, root)
```

定义类型：method；[源码第 32 行](C:/work/ls4t/cases/slstr-africa/connect_earthdata.py:32)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:116](C:/work/ls4t/tests/test_africa_download.py:116)、[tests/test_stream_era5.py:16](C:/work/ls4t/tests/test_stream_era5.py:16)

### `Handler.log_message`

```python
Handler.log_message(self, *args)
```

定义类型：method；[源码第 43 行](C:/work/ls4t/cases/slstr-africa/connect_earthdata.py:43)。

无 docstring；算法解释见人工审阅章节。

### `Handler.reply`

```python
Handler.reply(self, status, content)
```

定义类型：method；[源码第 46 行](C:/work/ls4t/cases/slstr-africa/connect_earthdata.py:46)。

无 docstring；算法解释见人工审阅章节。

### `Handler.authorized`

```python
Handler.authorized(self)
```

定义类型：method；[源码第 57 行](C:/work/ls4t/cases/slstr-africa/connect_earthdata.py:57)。

无 docstring；算法解释见人工审阅章节。

### `Handler.do_GET`

```python
Handler.do_GET(self)
```

定义类型：method；[源码第 62 行](C:/work/ls4t/cases/slstr-africa/connect_earthdata.py:62)。

无 docstring；算法解释见人工审阅章节。

### `Handler.do_POST`

```python
Handler.do_POST(self)
```

定义类型：method；[源码第 82 行](C:/work/ls4t/cases/slstr-africa/connect_earthdata.py:82)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 138 行](C:/work/ls4t/cases/slstr-africa/connect_earthdata.py:138)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-africa/download_daytime.py

源码：[打开文件](C:/work/ls4t/cases/slstr-africa/download_daytime.py)；706 行，28 个定义。

### `CDSESession.rebuild_auth`

```python
CDSESession.rebuild_auth(self, prepared_request, response)
```

定义类型：method；[源码第 47 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:47)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:177](C:/work/ls4t/tests/test_africa_download.py:177)

### `session`

```python
session()
```

定义类型：function；[源码第 56 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:56)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:172](C:/work/ls4t/tests/test_africa_download.py:172)

### `write_json`

```python
write_json(path, obj)
```

定义类型：function；[源码第 64 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:64)。

无 docstring；算法解释见人工审阅章节。

### `now`

```python
now()
```

定义类型：function；[源码第 70 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:70)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:96](C:/work/ls4t/tests/test_africa_download.py:96)

### `connect`

```python
connect(root)
```

定义类型：function；[源码第 74 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:74)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:51](C:/work/ls4t/tests/test_africa_download.py:51)

### `ForestRegion.__init__`

```python
ForestRegion.__init__(self, geometries)
```

定义类型：method；[源码第 94 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:94)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:116](C:/work/ls4t/tests/test_africa_download.py:116)、[tests/test_stream_era5.py:16](C:/work/ls4t/tests/test_stream_era5.py:16)

### `ForestRegion.intersects`

```python
ForestRegion.intersects(self, footprint)
```

定义类型：method；[源码第 103 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:103)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:210](C:/work/ls4t/tests/test_africa_download.py:210)

### `region`

```python
region(root)
```

定义类型：function；[源码第 107 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:107)。

无 docstring；算法解释见人工审阅章节。

### `solar_zenith`

```python
solar_zenith(when, lon, lat)
```

定义类型：function；[源码第 138 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:138)。

NOAA approximation at the scene footprint's representative point.

同名测试引用：[tests/test_africa_download.py:45](C:/work/ls4t/tests/test_africa_download.py:45)

### `candidate`

```python
candidate(product, roi, query_orbit_direction=None, require_descending=True)
```

定义类型：function；[源码第 155 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:155)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:35](C:/work/ls4t/tests/test_africa_download.py:35)

### `index_month`

```python
index_month(root, year, month, roi)
```

定义类型：function；[源码第 178 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:178)。

无 docstring；算法解释见人工审阅章节。

### `credentials`

```python
credentials()
```

定义类型：function；[源码第 232 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:232)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:233](C:/work/ls4t/tests/test_africa_download.py:233)

### `earthdata_token_path`

```python
earthdata_token_path()
```

定义类型：function；[源码第 242 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:242)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:249](C:/work/ls4t/tests/test_africa_download.py:249)

### `_token_dpapi`

```python
_token_dpapi(data, decrypt=False)
```

定义类型：function；[源码第 247 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:247)。

Protect the cache with the current Windows user's DPAPI identity.

### `save_earthdata_token`

```python
save_earthdata_token(token)
```

定义类型：function；[源码第 277 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:277)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:234](C:/work/ls4t/tests/test_africa_download.py:234)

### `load_earthdata_token`

```python
load_earthdata_token()
```

定义类型：function；[源码第 298 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:298)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:236](C:/work/ls4t/tests/test_africa_download.py:236)

### `earthdata_credentials`

```python
earthdata_credentials()
```

定义类型：function；[源码第 311 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:311)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:240](C:/work/ls4t/tests/test_africa_download.py:240)

### `EarthdataAuth.__init__`

```python
EarthdataAuth.__init__(self)
```

定义类型：method；[源码第 343 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:343)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:116](C:/work/ls4t/tests/test_africa_download.py:116)、[tests/test_stream_era5.py:16](C:/work/ls4t/tests/test_stream_era5.py:16)

### `EarthdataAuth.get`

```python
EarthdataAuth.get(self, force=False)
```

定义类型：method；[源码第 347 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:347)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:111](C:/work/ls4t/tests/test_africa_download.py:111)

### `earthdata_product`

```python
earthdata_product(entry)
```

定义类型：function；[源码第 362 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:362)。

Convert CMR metadata without assuming its BOTH flag means daytime.

同名测试引用：[tests/test_africa_download.py:196](C:/work/ls4t/tests/test_africa_download.py:196)

### `index_month_earthdata`

```python
index_month_earthdata(root, year, month, roi)
```

定义类型：function；[源码第 393 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:393)。

无 docstring；算法解释见人工审阅章节。

### `Auth.__init__`

```python
Auth.__init__(self)
```

定义类型：method；[源码第 451 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:451)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:116](C:/work/ls4t/tests/test_africa_download.py:116)、[tests/test_stream_era5.py:16](C:/work/ls4t/tests/test_stream_era5.py:16)

### `Auth.get`

```python
Auth.get(self, force=False)
```

定义类型：method；[源码第 455 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:455)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:111](C:/work/ls4t/tests/test_africa_download.py:111)

### `transfer`

```python
transfer(s, url, destination, auth)
```

定义类型：function；[源码第 478 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:478)。

Resume partial files; only publish a fully checked ZIP as complete.

同名测试引用：[tests/test_africa_download.py:99](C:/work/ls4t/tests/test_africa_download.py:99)、[tests/test_msg_aatsr_comparison.py:1](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:1)

### `deduplicate`

```python
deduplicate(db)
```

定义类型：function；[源码第 534 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:534)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:59](C:/work/ls4t/tests/test_africa_download.py:59)

### `report`

```python
report(root, state, error=None, period=(2017, 2025))
```

定义类型：function；[源码第 567 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:567)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:62](C:/work/ls4t/tests/test_africa_download.py:62)、[tests/test_kernel_atc_case.py:19](C:/work/ls4t/tests/test_kernel_atc_case.py:19)、[tests/test_south_america_components.py:83](C:/work/ls4t/tests/test_south_america_components.py:83)、[tests/test_south_america_remaining.py:36](C:/work/ls4t/tests/test_south_america_remaining.py:36)

### `download`

```python
download(root, reserve_gb, period=(2017, 2025), provider='cdse')
```

定义类型：function；[源码第 597 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:597)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:19](C:/work/ls4t/tests/test_africa_download.py:19)

### `main`

```python
main()
```

定义类型：function；[源码第 637 行](C:/work/ls4t/cases/slstr-africa/download_daytime.py:637)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-america/audit_remaining.py

源码：[打开文件](C:/work/ls4t/cases/slstr-america/audit_remaining.py)；182 行，7 个定义。

### `save`

```python
save(path, data)
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/slstr-america/audit_remaining.py:27)。

无 docstring；算法解释见人工审阅章节。

### `load_array`

```python
load_array(path)
```

定义类型：function；[源码第 34 行](C:/work/ls4t/cases/slstr-america/audit_remaining.py:34)。

无 docstring；算法解释见人工审阅章节。

### `geometry`

```python
geometry(folder, view, scene)
```

定义类型：function；[源码第 44 行](C:/work/ls4t/cases/slstr-america/audit_remaining.py:44)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:15](C:/work/ls4t/tests/test_africa_download.py:15)、[tests/test_beijing_building_structure.py:19](C:/work/ls4t/tests/test_beijing_building_structure.py:19)、[tests/test_kernel_models.py:1](C:/work/ls4t/tests/test_kernel_models.py:1)、[tests/test_south_america_remaining.py:1](C:/work/ls4t/tests/test_south_america_remaining.py:1)

### `classify`

```python
classify(item, root, raw_index)
```

定义类型：function；[源码第 78 行](C:/work/ls4t/cases/slstr-america/audit_remaining.py:78)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_remaining.py:36](C:/work/ls4t/tests/test_south_america_remaining.py:36)

### `summarize_empty_markers`

```python
summarize_empty_markers(root, workers)
```

定义类型：function；[源码第 110 行](C:/work/ls4t/cases/slstr-america/audit_remaining.py:110)。

无 docstring；算法解释见人工审阅章节。

### `summarize_empty_markers.marker_reason`

```python
summarize_empty_markers.marker_reason(path)
```

定义类型：nested；[源码第 111 行](C:/work/ls4t/cases/slstr-america/audit_remaining.py:111)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main(argv=None)
```

定义类型：function；[源码第 132 行](C:/work/ls4t/cases/slstr-america/audit_remaining.py:132)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-america/monthly_components.py

源码：[打开文件](C:/work/ls4t/cases/slstr-america/monthly_components.py)；372 行，12 个定义。

### `save`

```python
save(path, data)
```

定义类型：function；[源码第 48 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:48)。

无 docstring；算法解释见人工审阅章节。

### `stamp`

```python
stamp(path)
```

定义类型：function；[源码第 56 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:56)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:70](C:/work/ls4t/tests/test_msg_evo_sample.py:70)、[tests/test_south_america_components.py:55](C:/work/ls4t/tests/test_south_america_components.py:55)、[tests/test_south_america_monthly_components.py:98](C:/work/ls4t/tests/test_south_america_monthly_components.py:98)

### `fingerprint`

```python
fingerprint(data)
```

定义类型：function；[源码第 61 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:61)。

无 docstring；算法解释见人工审阅章节。

### `read`

```python
read(path)
```

定义类型：function；[源码第 65 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:65)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:262](C:/work/ls4t/tests/test_africa_download.py:262)

### `decode_geo`

```python
decode_geo(raw, nodata, limit)
```

定义类型：function；[源码第 73 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:73)。

Decode both native signed coordinates and the legacy offset encoding.

同名测试引用：[tests/test_south_america_monthly_components.py:17](C:/work/ls4t/tests/test_south_america_monthly_components.py:17)

### `bin_scene`

```python
bin_scene(values, lat, lon, bounds=BOUNDS, resolution=RESOLUTION)
```

定义类型：function；[源码第 87 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:87)。

Return unique grid cells and the five joint-valid scene means.

同名测试引用：[tests/test_south_america_monthly_components.py:26](C:/work/ls4t/tests/test_south_america_monthly_components.py:26)

### `accumulate_day`

```python
accumulate_day(total, count, day)
```

定义类型：function；[源码第 116 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:116)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:39](C:/work/ls4t/tests/test_south_america_monthly_components.py:39)

### `make_manifest`

```python
make_manifest(root, years)
```

定义类型：function；[源码第 122 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:122)。

无 docstring；算法解释见人工审阅章节。

### `write_tif`

```python
write_tif(path, total, count)
```

定义类型：function；[源码第 167 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:167)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization_raster.py:12](C:/work/ls4t/tests/test_normalization_raster.py:12)、[tests/test_south_america_monthly_components.py:67](C:/work/ls4t/tests/test_south_america_monthly_components.py:67)

### `verify_tif`

```python
verify_tif(path)
```

定义类型：function；[源码第 200 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:200)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:68](C:/work/ls4t/tests/test_south_america_monthly_components.py:68)

### `month_job`

```python
month_job(task)
```

定义类型：function；[源码第 231 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:231)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:100](C:/work/ls4t/tests/test_south_america_monthly_components.py:100)

### `main`

```python
main()
```

定义类型：function；[源码第 312 行](C:/work/ls4t/cases/slstr-america/monthly_components.py:312)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-america/recover_local_raw.py

源码：[打开文件](C:/work/ls4t/cases/slstr-america/recover_local_raw.py)；264 行，11 个定义。

### `digest`

```python
digest(path)
```

定义类型：function；[源码第 33 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:33)。

无 docstring；算法解释见人工审阅章节。

### `native`

```python
native(path, variable, expected_product=None)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:38)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_monthly_components.py:23](C:/work/ls4t/tests/test_south_america_monthly_components.py:23)、[tests/test_south_america_native_recovery.py:1](C:/work/ls4t/tests/test_south_america_native_recovery.py:1)

### `encode`

```python
encode(values, kind)
```

定义类型：function；[源码第 46 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:46)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:235](C:/work/ls4t/tests/test_africa_download.py:235)、[tests/test_south_america_native_recovery.py:19](C:/work/ls4t/tests/test_south_america_native_recovery.py:19)

### `write`

```python
write(path, values, kind)
```

定义类型：function；[源码第 59 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:59)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:96](C:/work/ls4t/tests/test_south_america_components.py:96)、[tests/test_south_america_monthly_components.py:108](C:/work/ls4t/tests/test_south_america_monthly_components.py:108)

### `tie_grid`

```python
tie_grid(values, view, shape)
```

定义类型：function；[源码第 72 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:72)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_native_recovery.py:36](C:/work/ls4t/tests/test_south_america_native_recovery.py:36)

### `image_grid`

```python
image_grid(values, width)
```

定义类型：function；[源码第 81 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:81)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_native_recovery.py:51](C:/work/ls4t/tests/test_south_america_native_recovery.py:51)

### `extract`

```python
extract(task)
```

定义类型：function；[源码第 90 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:90)。

无 docstring；算法解释见人工审阅章节。

### `extract.read`

```python
extract.read(file, variable)
```

定义类型：nested；[源码第 95 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:95)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:262](C:/work/ls4t/tests/test_africa_download.py:262)

### `check_components`

```python
check_components(folder)
```

定义类型：function；[源码第 128 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:128)。

无 docstring；算法解释见人工审阅章节。

### `publish`

```python
publish(record, stage, destination, backup_root)
```

定义类型：function；[源码第 147 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:147)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main(argv=None)
```

定义类型：function；[源码第 185 行](C:/work/ls4t/cases/slstr-america/recover_local_raw.py:185)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-america/run_components.py

源码：[打开文件](C:/work/ls4t/cases/slstr-america/run_components.py)；203 行，7 个定义。

### `save`

```python
save(path: Path, data) -> None
```

定义类型：function；[源码第 31 行](C:/work/ls4t/cases/slstr-america/run_components.py:31)。

无 docstring；算法解释见人工审阅章节。

### `run_lock`

```python
run_lock(path: Path)
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/slstr-america/run_components.py:39)。

A process-owned OS lock is released even after an interrupted run.

同名测试引用：[tests/test_south_america_components.py:93](C:/work/ls4t/tests/test_south_america_components.py:93)

### `inventory`

```python
inventory(root: Path, year: int, bounds) -> dict
```

定义类型：function；[源码第 62 行](C:/work/ls4t/cases/slstr-america/run_components.py:62)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:39](C:/work/ls4t/tests/test_south_america_components.py:39)

### `inventory.inspect`

```python
inventory.inspect(name)
```

定义类型：nested；[源码第 70 行](C:/work/ls4t/cases/slstr-america/run_components.py:70)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_flat_structure.py:1](C:/work/ls4t/tests/test_flat_structure.py:1)

### `run`

```python
run(command: list[str], log: Path) -> int
```

定义类型：function；[源码第 113 行](C:/work/ls4t/cases/slstr-america/run_components.py:113)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:241](C:/work/ls4t/tests/test_africa_download.py:241)、[tests/test_beijing_building_structure.py:8](C:/work/ls4t/tests/test_beijing_building_structure.py:8)、[tests/test_beijing_lai_8day.py:10](C:/work/ls4t/tests/test_beijing_lai_8day.py:10)、[tests/test_normalization_raster.py:81](C:/work/ls4t/tests/test_normalization_raster.py:81)、[tests/test_slstr_case_dependencies.py:3](C:/work/ls4t/tests/test_slstr_case_dependencies.py:3)、[tests/test_south_america_components.py:91](C:/work/ls4t/tests/test_south_america_components.py:91)、[tests/test_south_america_monthly_components.py:99](C:/work/ls4t/tests/test_south_america_monthly_components.py:99)、[tests/test_standalone_cases.py:31](C:/work/ls4t/tests/test_standalone_cases.py:31)

### `process_year`

```python
process_year(root: Path, year: int, bounds, paths: dict, workers: int, output: Path, *, audit_only=False, limit=None) -> dict
```

定义类型：function；[源码第 119 行](C:/work/ls4t/cases/slstr-america/run_components.py:119)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main(argv=None) -> int
```

定义类型：function；[源码第 161 行](C:/work/ls4t/cases/slstr-america/run_components.py:161)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-america/run_standard_stage.py

源码：[打开文件](C:/work/ls4t/cases/slstr-america/run_standard_stage.py)；164 行，5 个定义。

### `find_repository_root`

```python
find_repository_root(start: Path) -> Path
```

定义类型：function；[源码第 16 行](C:/work/ls4t/cases/slstr-america/run_standard_stage.py:16)。

无 docstring；算法解释见人工审阅章节。

### `load_toml`

```python
load_toml(path: Path) -> dict
```

定义类型：function；[源码第 101 行](C:/work/ls4t/cases/slstr-america/run_standard_stage.py:101)。

无 docstring；算法解释见人工审阅章节。

### `parse_args`

```python
parse_args() -> argparse.Namespace
```

定义类型：function；[源码第 108 行](C:/work/ls4t/cases/slstr-america/run_standard_stage.py:108)。

无 docstring；算法解释见人工审阅章节。

### `stage_arguments`

```python
stage_arguments(function, case: dict, machine: dict) -> dict
```

定义类型：function；[源码第 116 行](C:/work/ls4t/cases/slstr-america/run_standard_stage.py:116)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 142 行](C:/work/ls4t/cases/slstr-america/run_standard_stage.py:142)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-europe/run_standard_stage.py

源码：[打开文件](C:/work/ls4t/cases/slstr-europe/run_standard_stage.py)；164 行，5 个定义。

### `find_repository_root`

```python
find_repository_root(start: Path) -> Path
```

定义类型：function；[源码第 16 行](C:/work/ls4t/cases/slstr-europe/run_standard_stage.py:16)。

无 docstring；算法解释见人工审阅章节。

### `load_toml`

```python
load_toml(path: Path) -> dict
```

定义类型：function；[源码第 101 行](C:/work/ls4t/cases/slstr-europe/run_standard_stage.py:101)。

无 docstring；算法解释见人工审阅章节。

### `parse_args`

```python
parse_args() -> argparse.Namespace
```

定义类型：function；[源码第 108 行](C:/work/ls4t/cases/slstr-europe/run_standard_stage.py:108)。

无 docstring；算法解释见人工审阅章节。

### `stage_arguments`

```python
stage_arguments(function, case: dict, machine: dict) -> dict
```

定义类型：function；[源码第 116 行](C:/work/ls4t/cases/slstr-europe/run_standard_stage.py:116)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 142 行](C:/work/ls4t/cases/slstr-europe/run_standard_stage.py:142)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-heihe/run_standard_stage.py

源码：[打开文件](C:/work/ls4t/cases/slstr-heihe/run_standard_stage.py)；164 行，5 个定义。

### `find_repository_root`

```python
find_repository_root(start: Path) -> Path
```

定义类型：function；[源码第 16 行](C:/work/ls4t/cases/slstr-heihe/run_standard_stage.py:16)。

无 docstring；算法解释见人工审阅章节。

### `load_toml`

```python
load_toml(path: Path) -> dict
```

定义类型：function；[源码第 101 行](C:/work/ls4t/cases/slstr-heihe/run_standard_stage.py:101)。

无 docstring；算法解释见人工审阅章节。

### `parse_args`

```python
parse_args() -> argparse.Namespace
```

定义类型：function；[源码第 108 行](C:/work/ls4t/cases/slstr-heihe/run_standard_stage.py:108)。

无 docstring；算法解释见人工审阅章节。

### `stage_arguments`

```python
stage_arguments(function, case: dict, machine: dict) -> dict
```

定义类型：function；[源码第 116 行](C:/work/ls4t/cases/slstr-heihe/run_standard_stage.py:116)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 142 行](C:/work/ls4t/cases/slstr-heihe/run_standard_stage.py:142)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-huailai/stages/audit_outputs.py

源码：[打开文件](C:/work/ls4t/cases/slstr-huailai/stages/audit_outputs.py)；127 行，3 个定义。

### `complete`

```python
complete(path: Path, names: set[str]) -> bool
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/slstr-huailai/stages/audit_outputs.py:30)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:41](C:/work/ls4t/tests/test_south_america_components.py:41)

### `source_thermal_missing`

```python
source_thermal_missing(tif: Path) -> bool
```

定义类型：function；[源码第 34 行](C:/work/ls4t/cases/slstr-huailai/stages/audit_outputs.py:34)。

True when every extracted S8/S9 view contains only source fill/zero.

### `main`

```python
main() -> int
```

定义类型：function；[源码第 47 行](C:/work/ls4t/cases/slstr-huailai/stages/audit_outputs.py:47)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-huailai/stages/prepare_reuse.py

源码：[打开文件](C:/work/ls4t/cases/slstr-huailai/stages/prepare_reuse.py)；101 行，4 个定义。

### `files_complete`

```python
files_complete(path: Path, required: set[str]) -> bool
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/slstr-huailai/stages/prepare_reuse.py:27)。

无 docstring；算法解释见人工审阅章节。

### `reusable`

```python
reusable(layer: str, path: Path) -> bool
```

定义类型：function；[源码第 32 行](C:/work/ls4t/cases/slstr-huailai/stages/prepare_reuse.py:32)。

无 docstring；算法解释见人工审阅章节。

### `link_dir`

```python
link_dir(link: Path, target: Path) -> str
```

定义类型：function；[源码第 43 行](C:/work/ls4t/cases/slstr-huailai/stages/prepare_reuse.py:43)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> int
```

定义类型：function；[源码第 54 行](C:/work/ls4t/cases/slstr-huailai/stages/prepare_reuse.py:54)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-xizang/stages/apply_inventory.py

源码：[打开文件](C:/work/ls4t/cases/slstr-xizang/stages/apply_inventory.py)；150 行，4 个定义。

### `complete`

```python
complete(path: Path, required: set[str]) -> bool
```

定义类型：function；[源码第 26 行](C:/work/ls4t/cases/slstr-xizang/stages/apply_inventory.py:26)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:41](C:/work/ls4t/tests/test_south_america_components.py:41)

### `write_json`

```python
write_json(path: Path, payload: dict) -> None
```

定义类型：function；[源码第 30 行](C:/work/ls4t/cases/slstr-xizang/stages/apply_inventory.py:30)。

无 docstring；算法解释见人工审阅章节。

### `link_dir`

```python
link_dir(link: Path, target: Path) -> str
```

定义类型：function；[源码第 36 行](C:/work/ls4t/cases/slstr-xizang/stages/apply_inventory.py:36)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> int
```

定义类型：function；[源码第 47 行](C:/work/ls4t/cases/slstr-xizang/stages/apply_inventory.py:47)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-xizang/stages/audit_outputs.py

源码：[打开文件](C:/work/ls4t/cases/slstr-xizang/stages/audit_outputs.py)；120 行，2 个定义。

### `all_files`

```python
all_files(path: Path, names: set[str]) -> bool
```

定义类型：function；[源码第 27 行](C:/work/ls4t/cases/slstr-xizang/stages/audit_outputs.py:27)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> int
```

定义类型：function；[源码第 31 行](C:/work/ls4t/cases/slstr-xizang/stages/audit_outputs.py:31)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-xizang/stages/delete_archives_after_raw.py

源码：[打开文件](C:/work/ls4t/cases/slstr-xizang/stages/delete_archives_after_raw.py)；141 行，4 个定义。

### `evenly_spaced`

```python
evenly_spaced(records: list[dict], count: int) -> list[dict]
```

定义类型：function；[源码第 23 行](C:/work/ls4t/cases/slstr-xizang/stages/delete_archives_after_raw.py:23)。

无 docstring；算法解释见人工审阅章节。

### `audit`

```python
audit(records: list[dict], root: Path, sample_per_year: int) -> tuple[list[dict], list[dict]]
```

定义类型：function；[源码第 29 行](C:/work/ls4t/cases/slstr-xizang/stages/delete_archives_after_raw.py:29)。

Full structural audit plus an evenly distributed full-data read sample.

同名测试引用：[tests/test_south_america_remaining.py:11](C:/work/ls4t/tests/test_south_america_remaining.py:11)

### `write_json`

```python
write_json(path: Path, payload: dict) -> None
```

定义类型：function；[源码第 72 行](C:/work/ls4t/cases/slstr-xizang/stages/delete_archives_after_raw.py:72)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> int
```

定义类型：function；[源码第 79 行](C:/work/ls4t/cases/slstr-xizang/stages/delete_archives_after_raw.py:79)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-xizang/stages/delete_outside_xizang_archives.py

源码：[打开文件](C:/work/ls4t/cases/slstr-xizang/stages/delete_outside_xizang_archives.py)；67 行，2 个定义。

### `write_json`

```python
write_json(path: Path, payload: dict) -> None
```

定义类型：function；[源码第 14 行](C:/work/ls4t/cases/slstr-xizang/stages/delete_outside_xizang_archives.py:14)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> int
```

定义类型：function；[源码第 20 行](C:/work/ls4t/cases/slstr-xizang/stages/delete_outside_xizang_archives.py:20)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-xizang/stages/inventory_and_reuse.py

源码：[打开文件](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py)；258 行，10 个定义。

### `canonical_scene`

```python
canonical_scene(path: Path) -> str
```

定义类型：function；[源码第 43 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:43)。

无 docstring；算法解释见人工审阅章节。

### `archive_info`

```python
archive_info(path: Path) -> dict
```

定义类型：function；[源码第 47 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:47)。

无 docstring；算法解释见人工审阅章节。

### `complete_dir`

```python
complete_dir(path: Path, required: set[str]) -> bool
```

定义类型：function；[源码第 68 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:68)。

无 docstring；算法解释见人工审阅章节。

### `zip_geo`

```python
zip_geo(path: Path) -> tuple[np.ndarray, np.ndarray]
```

定义类型：function；[源码第 72 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:72)。

无 docstring；算法解释见人工审阅章节。

### `tif_geo`

```python
tif_geo(path: Path) -> tuple[np.ndarray, np.ndarray]
```

定义类型：function；[源码第 88 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:88)。

无 docstring；算法解释见人工审阅章节。

### `intersects`

```python
intersects(lat: np.ndarray, lon: np.ndarray) -> bool
```

定义类型：function；[源码第 100 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:100)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:210](C:/work/ls4t/tests/test_africa_download.py:210)

### `symlink_dir`

```python
symlink_dir(link: Path, target: Path) -> str
```

定义类型：function；[源码第 106 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:106)。

无 docstring；算法解释见人工审阅章节。

### `prepare_hierarchy`

```python
prepare_hierarchy(root: Path) -> None
```

定义类型：function；[源码第 119 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:119)。

无 docstring；算法解释见人工审阅章节。

### `write_json`

```python
write_json(path: Path, payload: dict) -> None
```

定义类型：function；[源码第 126 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:126)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> int
```

定义类型：function；[源码第 133 行](C:/work/ls4t/cases/slstr-xizang/stages/inventory_and_reuse.py:133)。

无 docstring；算法解释见人工审阅章节。

## cases/slstr-xizang/stages/stage_raw.py

源码：[打开文件](C:/work/ls4t/cases/slstr-xizang/stages/stage_raw.py)；100 行，3 个定义。

### `complete`

```python
complete(path: Path) -> bool
```

定义类型：function；[源码第 25 行](C:/work/ls4t/cases/slstr-xizang/stages/stage_raw.py:25)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_south_america_components.py:41](C:/work/ls4t/tests/test_south_america_components.py:41)

### `extract_one`

```python
extract_one(task: tuple[Path, Path]) -> dict
```

定义类型：function；[源码第 29 行](C:/work/ls4t/cases/slstr-xizang/stages/stage_raw.py:29)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> int
```

定义类型：function；[源码第 56 行](C:/work/ls4t/cases/slstr-xizang/stages/stage_raw.py:56)。

无 docstring；算法解释见人工审阅章节。

## cases/stream/global/era5/run.py

源码：[打开文件](C:/work/ls4t/cases/stream/global/era5/run.py)；104 行，2 个定义。

### `download_month`

```python
download_month(destination: Path, year: int, month: int) -> Path
```

定义类型：function；[源码第 39 行](C:/work/ls4t/cases/stream/global/era5/run.py:39)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main() -> None
```

定义类型：function；[源码第 60 行](C:/work/ls4t/cases/stream/global/era5/run.py:60)。

无 docstring；算法解释见人工审阅章节。

## tests/examples/msg_aatsr_comparison.py

源码：[打开文件](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py)；411 行，19 个定义。

### `planck`

```python
planck(t)
```

定义类型：function；[源码第 34 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:34)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:26](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:26)、[tests/test_msg_case_dependencies.py:90](C:/work/ls4t/tests/test_msg_case_dependencies.py:90)、[tests/test_slstr_case_dependencies.py:20](C:/work/ls4t/tests/test_slstr_case_dependencies.py:20)

### `least_squares`

```python
least_squares(a, b, ridge=0.0)
```

定义类型：function；[源码第 38 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:38)。

无 docstring；算法解释见人工审阅章节。

### `quadratic`

```python
quadratic(w, y, good)
```

定义类型：function；[源码第 46 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:46)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:39](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:39)

### `posterior`

```python
posterior(a, b, prior)
```

定义类型：function；[源码第 54 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:54)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:74](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:74)、[tests/test_south_america_components.py:67](C:/work/ls4t/tests/test_south_america_components.py:67)

### `constrained`

```python
constrained(a, b, center_lst, spatial_weights, delta_constraint=True)
```

定义类型：function；[源码第 60 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:60)。

AATSR SLSQP assumptions, with BOTH Planck terms at MSG's wavelength.  Keep the legacy approximate radiance-difference and bracketing constraints; explicitly reject unsuccessful or infeasible optimizer results.

### `constrained.cons`

```python
constrained.cons(x)
```

定义类型：nested；[源码第 75 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:75)。

无 docstring；算法解释见人工审阅章节。

### `constrained.fun`

```python
constrained.fun(x)
```

定义类型：nested；[源码第 81 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:81)。

无 docstring；算法解释见人工审阅章节。

### `constrained.jac`

```python
constrained.jac(x)
```

定义类型：nested；[源码第 84 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:84)。

无 docstring；算法解释见人工审阅章节。

### `solve_window`

```python
solve_window(y, w, center_lst, method, exclude_center=False)
```

定义类型：function；[源码第 106 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:106)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:30](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:30)

### `production_functions`

```python
production_functions()
```

定义类型：function；[源码第 137 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:137)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_aatsr_comparison.py:64](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:64)

### `msg_iter`

```python
msg_iter(y, w, functions, common_residual_mask=False)
```

定义类型：function；[源码第 149 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:149)。

Current repository production: 3x3 / 5x5, delta=3 radiance, lambda=100.

同名测试引用：[tests/test_msg_aatsr_comparison.py:64](C:/work/ls4t/tests/test_msg_aatsr_comparison.py:64)

### `three_weights`

```python
three_weights(manifest, data, index, valid)
```

定义类型：function；[源码第 171 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:171)。

无 docstring；算法解释见人工审阅章节。

### `metric`

```python
metric(pred, ref)
```

定义类型：function；[源码第 190 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:190)。

无 docstring；算法解释见人工审阅章节。

### `evaluate_reference`

```python
evaluate_reference(center, source, output)
```

定义类型：function；[源码第 197 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:197)。

无 docstring；算法解释见人工审阅章节。

### `constraint_ablation`

```python
constraint_ablation(temps, errs, center, output)
```

定义类型：function；[源码第 230 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:230)。

无 docstring；算法解释见人工审阅章节。

### `write_report`

```python
write_report(output, rows, ground, cv, ablation)
```

定义类型：function；[源码第 261 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:261)。

无 docstring；算法解释见人工审阅章节。

### `write_report.table`

```python
write_report.table(items, columns)
```

定义类型：nested；[源码第 262 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:262)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_calibration.py:11](C:/work/ls4t/tests/test_calibration.py:11)

### `write_report.table.fmt`

```python
write_report.table.fmt(v)
```

定义类型：nested；[源码第 265 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:265)。

无 docstring；算法解释见人工审阅章节。

### `main`

```python
main()
```

定义类型：function；[源码第 302 行](C:/work/ls4t/tests/examples/msg_aatsr_comparison.py:302)。

无 docstring；算法解释见人工审阅章节。

## tests/examples/msg_evo_sample.py

源码：[打开文件](C:/work/ls4t/tests/examples/msg_evo_sample.py)；452 行，14 个定义。

### `sha256`

```python
sha256(path: Path) -> str
```

定义类型：function；[源码第 32 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:32)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_africa_download.py:152](C:/work/ls4t/tests/test_africa_download.py:152)、[tests/test_msg_evo_sample.py:44](C:/work/ls4t/tests/test_msg_evo_sample.py:44)、[tests/test_standalone_cases.py:61](C:/work/ls4t/tests/test_standalone_cases.py:61)

### `write_json`

```python
write_json(path: Path, value: dict) -> None
```

定义类型：function；[源码第 40 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:40)。

无 docstring；算法解释见人工审阅章节。

### `write_stack`

```python
write_stack(path, arrays, names, transform, projection, unit='', **metadata)
```

定义类型：function；[源码第 44 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:44)。

GeoTIFF bands are ordered exactly as their manifest time/field axis.

### `read_stack`

```python
read_stack(path: Path)
```

定义类型：function；[源码第 70 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:70)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:112](C:/work/ls4t/tests/test_msg_evo_sample.py:112)

### `source_crop`

```python
source_crop(path: Path, window, transform, projection)
```

定义类型：function；[源码第 82 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:82)。

无 docstring；算法解释见人工审阅章节。

### `copy_product_window`

```python
copy_product_window(source: Path, target: Path, window, raw)
```

定义类型：function；[源码第 103 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:103)。

Keep the production GeoTIFF encoding; only crop its spatial extent.

### `calibration`

```python
calibration(path: Path, variable: str, stamp: str)
```

定义类型：function；[源码第 118 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:118)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_calibration.py:5](C:/work/ls4t/tests/test_calibration.py:5)、[tests/test_dual_thermal_sensors.py:6](C:/work/ls4t/tests/test_dual_thermal_sensors.py:6)、[tests/test_slstr_products.py:7](C:/work/ls4t/tests/test_slstr_products.py:7)

### `decode`

```python
decode(raw, nodata, information, variable)
```

定义类型：function；[源码第 141 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:141)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:92](C:/work/ls4t/tests/test_msg_evo_sample.py:92)

### `sample_auxiliary`

```python
sample_auxiliary(path, latitude, longitude)
```

定义类型：function；[源码第 156 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:156)。

Sample each ancillary with its own CRS/affine, without reading a global image.

### `extract`

```python
extract(source_root: Path, output: Path=SAMPLE, year=2017, month=10)
```

定义类型：function；[源码第 183 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:183)。

Only source reads; write small, portable arrays and their provenance below tests/.

### `load_sample`

```python
load_sample(sample: Path=SAMPLE)
```

定义类型：function；[源码第 302 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:302)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:104](C:/work/ls4t/tests/test_msg_evo_sample.py:104)、[tests/test_slstr_evo_sample.py:28](C:/work/ls4t/tests/test_slstr_evo_sample.py:28)

### `prepare_frame`

```python
prepare_frame(manifest, data, index, components=2)
```

定义类型：function；[源码第 339 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:339)。

Decode already-calibrated LST to emissivity-weighted radiance, not brightness temperature.

同名测试引用：[tests/test_msg_evo_sample.py:107](C:/work/ls4t/tests/test_msg_evo_sample.py:107)

### `run_sample`

```python
run_sample(sample: Path=SAMPLE, output: Path | None=None, components=2)
```

定义类型：function；[源码第 374 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:374)。

Run each instant independently; never combine different acquisition times.

同名测试引用：[tests/test_msg_evo_sample.py:97](C:/work/ls4t/tests/test_msg_evo_sample.py:97)、[tests/test_slstr_evo_sample.py:35](C:/work/ls4t/tests/test_slstr_evo_sample.py:35)

### `main`

```python
main()
```

定义类型：function；[源码第 429 行](C:/work/ls4t/tests/examples/msg_evo_sample.py:429)。

无 docstring；算法解释见人工审阅章节。

## tests/examples/slstr_evo_sample.py

源码：[打开文件](C:/work/ls4t/tests/examples/slstr_evo_sample.py)；190 行，4 个定义。

### `load_sample`

```python
load_sample(sample: Path=SAMPLE)
```

定义类型：function；[源码第 34 行](C:/work/ls4t/tests/examples/slstr_evo_sample.py:34)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:104](C:/work/ls4t/tests/test_msg_evo_sample.py:104)、[tests/test_slstr_evo_sample.py:28](C:/work/ls4t/tests/test_slstr_evo_sample.py:28)

### `write_tif`

```python
write_tif(path: Path, values: np.ndarray, *, scale: float=1.0, dtype: int=gdal.GDT_Int16, missing: int=-32768) -> None
```

定义类型：function；[源码第 58 行](C:/work/ls4t/tests/examples/slstr_evo_sample.py:58)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_normalization_raster.py:12](C:/work/ls4t/tests/test_normalization_raster.py:12)、[tests/test_south_america_monthly_components.py:67](C:/work/ls4t/tests/test_south_america_monthly_components.py:67)

### `run_sample`

```python
run_sample(output: Path=DEFAULT_OUTPUT, sample: Path=SAMPLE, *, force_night: bool=False) -> dict
```

定义类型：function；[源码第 77 行](C:/work/ls4t/tests/examples/slstr_evo_sample.py:77)。

无 docstring；算法解释见人工审阅章节。

同名测试引用：[tests/test_msg_evo_sample.py:97](C:/work/ls4t/tests/test_msg_evo_sample.py:97)、[tests/test_slstr_evo_sample.py:35](C:/work/ls4t/tests/test_slstr_evo_sample.py:35)

### `main`

```python
main() -> None
```

定义类型：function；[源码第 177 行](C:/work/ls4t/tests/examples/slstr_evo_sample.py:177)。

无 docstring；算法解释见人工审阅章节。
