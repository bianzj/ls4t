# 代码、数据、产品分离

本仓库只保留代码、配置、说明和明确保留的少量测试夹具。实际输入、辅助数据、
中间产品、最终结果均由具体任务指向用户已有的外部位置，不要求统一目录名称。

新参考脚本没有默认存储根目录。运行前在代码中填写 DATA_ROOT、OUTPUT_DIR，
或设置 LS4T_DATA_ROOT、LS4T_PRODUCT_ROOT；未指定时在写文件前退出。
两个存储根须在代码目录外且互不包含。同名任务可修改 CASE_ID。

保留例外：tests/data 离线夹具、tests/outputs 可重复测试产物，以及
cases/msg/Validation_Stats_Nadir_vs_Obs.csv 这一份固定验证基准。

2026-10-28：按用户要求增加固定案例样本例外：
`cases/ahi-slstr/heihe/three-site-kernel-3x3/data/2019-05-12-s3b/`。
仅保存三站27个配对足迹、参考结果和来源/选日记录，用于离线复现核拟合。
原始完整栅格仍在外部数据盘，新计算结果仍写到显式指定的外部目录。

2026-10-24：撤销此前临时创建的 C:/work/ls4t-data、ls4t-products、ls4t-maintenance。
26 个合成演示文件已删除；1,098 个历史结果和整理记录保留到已有的 D:/cases/ls4t。
MSG 历史结果位于 D:/cases/ls4t/msg/official-results；三个读取历史评估的脚本已更新路径。
保留文件均逐文件核验 SHA-256。清单和原路径映射位于：
D:/cases/ls4t/_maintenance/20261024/removed_generated_roots.json。
这些外部历史档案位置不作为新任务必须采用的输入/输出布局。
