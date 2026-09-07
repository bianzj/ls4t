# 产品化代码结构

## 组织原则

代码按产品归属，不按统一流程框架组织：

- `aatsr_data.py`、`slstr_data.py`、`msg_data.py` 负责各自传感器数据；较长的
  SLSTR 批处理阶段另按阶段拆成 `slstr_unzip.py`、`slstr_extract.py`、
  `slstr_reconstruct.py`、`slstr_project.py` 和 `slstr_merge.py`。
- `*_lst.py` 只负责地表温度反演。
- `*_lsct.py` 只负责组分温度反演。
- 角度、时间、空间、传感器归一化和融合分别集中在 `normalization/`。
- `base/` 只保存稳定公共算法、质量标识和产品读写，不能加入目录遍历或传感器流程。
- `base/spatial.py` 只保存同网格投影、裁剪和像元选择算法；输入文件如何分组仍由
  AATSR、SLSTR、MSG 各自的 `*_region.py` 决定。

## 执行单位

常规批处理的执行单位是“一个输入目录 + 一个输出目录 + 若干年份或日期”。空间
拼接的执行单位则是“一组相邻、同次获取、同视角、同目标网格的影像”，避免把
一天内不同过境或 nadir/oblique 结果误拼在一起。

公开批处理函数负责遍历年份和产品；单景读取、反演函数只作为内部算法或外部精细调用入口。不同传感器保留自己的日期结构和参数，不要求相同函数签名。

## 手工运行

每个文件顶部集中定义所有运行中可能修改的参数。函数参数为 `None` 时读取顶部定义，传入参数时覆盖顶部定义。

每个阶段独立执行，不自动衔接。例如 SLSTR 中：

- `slstr_unzip.py` 中的 `slstr_unzip()`
- `slstr_extract.py` 中的 `slstr_extract()`
- `slstr_reconstruct.py` 中的 `slstr_reconstruct()`
- `slstr_project.py` 中的 `slstr_project()`
- `slstr_merge.py` 中的 `slstr_merge()`

`slstr_data.py` 保留数据模型和旧导入兼容层，避免迁移期间的调用突然失效；
新运行代码应优先直接运行上述阶段文件。

文件末尾一次只手工选择其中一个函数。项目不提供总调度器和统一 CLI。

## 目录

```text

├── base/
├── aatsr/
├── slstr/
├── msg/
├── normalization/
├── composite.py
└── applications.py
```

旧脚本仍是实际数据回归的依据，但不属于新的运行源码。

## 空间处理边界

- `*_project.py`：逐景投影到统一目标网格，不负责拼接或反演。
- `*_data_region()`：在反演前从同组数据形成完整研究区。
- `*_lst.py` / `*_lsct.py`：只处理输入数据，不决定采用哪种空间路线。
- `*_result_region()`：在逐景反演后从同组结果形成完整研究区。

LST 结果固定携带 `latitude_deg` 和 `longitude_deg`。LSCT 输入包含这两个数组时，
结果也会保留它们，从而支持反演后的裁剪和拼接。
