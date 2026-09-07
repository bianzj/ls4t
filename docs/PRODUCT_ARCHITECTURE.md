# 产品化代码结构

## 组织原则

代码按产品归属，不按统一流程框架组织：

- 各传感器的 `*_data.py` 负责标准数据产品；较长的
  SLSTR 批处理阶段另按阶段拆成 `slstr_unzip.py`、`slstr_extract.py`、
  `slstr_reconstruct.py`、`slstr_project.py` 和 `slstr_merge.py`。
- `*_lst.py` 只负责地表温度反演。
- `*_lsct.py` 只负责组分温度反演。
- 角度、时间、空间、传感器归一化和融合分别集中在 `normalization/`。
- `base/` 只保存稳定公共算法、质量标识和产品读写，不能加入目录遍历或传感器流程。
- `base/spatial.py` 只保存同网格投影、裁剪和像元选择算法；输入文件如何分组仍由
  各传感器的 `*_merge.py` 或 `*_region.py` 决定。
- MODIS、VIIRS、AHI、ASTER 共用 `base/dual_thermal.py` 的标准产品和双通道算法，
  但在各自根目录包中保留传感器名称、通道和公开入口。

## 执行单位

常规批处理的执行单位是“一个输入目录 + 一个输出目录 + 若干年份或日期”。空间
拼接的执行单位则是“一组相邻、同次获取、同视角、同目标网格的影像”，避免把
一天内不同过境或 nadir/oblique 结果误拼在一起。

公开批处理函数负责遍历年份和产品；单景读取、反演函数只作为内部算法或外部精细调用入口。不同传感器保留自己的日期结构和参数，不要求相同函数签名。

## 执行边界

根目录模块不保存实际输入输出路径、年份或研究区，也不直接执行。`cases/` 中的脚本
集中定义这些运行参数，并显式传给对应阶段函数。

每个阶段独立执行，不自动衔接。例如 SLSTR 中：

- `slstr_unzip.py` 中的 `slstr_unzip()`
- `slstr_extract.py` 中的 `slstr_extract()`
- `slstr_reconstruct.py` 中的 `slstr_reconstruct()`
- `slstr_project.py` 中的 `slstr_project()`
- `slstr_merge.py` 中的 `slstr_merge()`

`slstr_data.py` 保留数据模型和旧导入兼容层，避免迁移期间的调用突然失效；新的
case 应优先从上述阶段模块导入函数。项目不提供总调度器和统一 CLI。

## 目录

```text
ls4t/
├── base/
├── aatsr/
├── slstr/
├── msg/
├── modis/
├── viirs/
├── ahi/
├── aster/
├── normalization/
├── composite/
├── applications/
└── cases/
```

旧脚本仍是实际数据回归的依据，但不属于新的运行源码。

## 空间处理边界

- `*_project.py`：逐景投影到统一目标网格，不负责拼接或反演。
- `*_data_region()`：在反演前从同组数据形成完整研究区。
- `*_lst.py` / `*_lsct.py`：只处理输入数据，不决定采用哪种空间路线。
- `*_result_region()`：在逐景反演后从同组结果形成完整研究区。

LST 结果固定携带 `latitude_deg` 和 `longitude_deg`。LSCT 输入包含这两个数组时，
结果也会保留它们，从而支持反演后的裁剪和拼接。
