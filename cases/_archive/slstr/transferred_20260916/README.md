# 2026-09-16 从 SLSTR 运行项目转入但当前不用的内容

SLSTR 生产代码转入 `cases/slstr/` 时只保留五个环节：解压、重整、投影、LST 反演和
LSCT 反演。这里存放同一次搬运中一起带过来、但不属于这五个环节的实现，全部来自
`git@github.com:bianzj/ls4t-slstr.git`（提交 `b856b44` 及当时未提交的工作树）。

```text
auxiliary/          ERA5 TCWV、MODIS LAI、文件清单等外部数据预处理
regions/            欧洲、南美区域拼接与出图、覆盖率/数据状态报告、shell 驱动、geojson
tcw/                由 ERA5 生成 TCWV 逐日 H5 的脚本（batch、study_area、one_by_one）
file_checks/        提取结果与原文件的核对清理脚本
unused_support/     五个环节的依赖图里没有用到的 support 模块
nested_scripts/     迁移时先放入 cases/slstr/ 的嵌套脚本（implementation/、batch/）
support/            迁移时的 support 夹层原件，扁平化后整体退役
```

扁平化后的 case 脚本只从 `base/`、`slstr/` 导入，对应实现在
`cases/slstr/production.toml` 的 `[dependencies]` 里登记，数值由
`tests/test_slstr_case_dependencies.py` 的 golden 测试锁定。

恢复方式：`nested_scripts/` 和 `support/` 保留迁移前的原样（导入仍是
`cases.slstr.support`），需要对照或回退时成对放回 `cases/slstr/`。重新启用 ERA5/TCWV
预处理时至少需要 `tcw/` 下的脚本和 `unused_support/util_download.py`、`util_kernel.py`、
`util_plot.py` 等被它们依赖的模块。

注：`inv_lsct2_window` / `inv_lsct3_window` 没有被搬进 `base/` 的那一版覆盖到，它们于
2026-09-16 从 AATSR 产品历史 `cases/_archive/aatsr/product_history/util/util_ls4t.py`
逐字恢复到 `base/lsct_window.py`（由 `base/lsct.py` 转出），不在本归档内维护。
