# 2026-09-16 AATSR 生产代码扁平化时归档的内容

AATSR 的生产与实验脚本已转入 `cases/aatsr/` 根部并扁平化，只从 `base/`、`aatsr/`
导入。这里保存迁移前的旧快照与本次未纳入的部件。

```text
nested_snapshots/global/001deg_2003_2012/   迁移前 cases/aatsr/global/ 下的旧快照
                                            （导入已删除的 base.util_*，不能直接运行）
```

来源项目 `/home/hero/work/ls4t-aatsr-lsct/cases/` 仍保留完整 `support/` 与
`_archive/product_history/`（LSCT 各历史版本、站点实验、参数敏感性、备份）。
本次进入 `cases/aatsr/` 的是：生产链 6 个脚本、ERA5 TCWV、全图 LSCT 变体
（v3.1、NDVI、经纬度版）和站点四个脚本（反演、贝叶斯版、验证、时间序列）。
