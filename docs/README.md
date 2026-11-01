# LS4T 理论、流程与发布文档

本页整理现有文档的用途，不把文档存在当作算法或科学精度已通过验证。

| 主题 | 文档 | 内容 |
|---|---|---|
| 函数与公式总表 | [METHOD_INVENTORY](METHOD_INVENTORY.md) | 反演、归一化、降尺度公式、参数、源码位置与限制；行号随代码变化 |
| AATSR 反演 | [AATSR_METHODS](AATSR_METHODS.md) | 地表与组分温度方法 |
| 核函数和周期 | [KERNELS_ATC](KERNELS_ATC.md) | 角度核、组合拟合、年温度周期 |
| 降尺度 | [TSHARP](TSHARP.md) | TsHARP 假设、输入与质量边界 |
| 产品定义 | [PRODUCT_ARCHITECTURE](PRODUCT_ARCHITECTURE.md) | L1O、L2LST/LSCT、L3N/L3C、L4A |
| 处理顺序 | [PIPELINE](PIPELINE.md)、[SPATIAL_MODES](SPATIAL_MODES.md) | 逐景/研究区路线、投影与归一化顺序 |
| 案例组织 | [CASE_EXECUTION_BOUNDARY](CASE_EXECUTION_BOUNDARY.md)、[CASE_WORKFLOW](CASE_WORKFLOW.md) | 公共函数与独立执行案例的边界；旧登记工具按历史快照使用 |
| 存储与项目关系 | [STORAGE_LAYOUT](STORAGE_LAYOUT.md)、[PROJECTS](PROJECTS.md) | Windows 当前目录、外部数据和历史记录 |
| 安装与构建 | [WINDOWS_RELEASE](WINDOWS_RELEASE.md) | 随包依赖、用户状态、打包及本轮验收范围 |

历史迁移、清理、文件审计和设计草案仍保留原文件，按各文档日期理解；当前实际入口以
[根 README](../README.md)、[当前案例](../cases/README.md) 和 D 盘发布清单为准。
