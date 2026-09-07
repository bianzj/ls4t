# LS4T cases

这里是实际研究和生产入口。项目采用固定的三层边界：

```text
根目录模块                 标准、可复用的处理能力
tests/                     合成数据自动化测试
cases/<sensor>/<region>/   真实数据、研究区、机器和运行实现
```

## 当前工作区

```text
cases/
├── _templates/                         新案例模板和生成工具
├── _archive/                           非活动、重复或混杂材料
├── ahi/
│   └── unclassified/legacy_draft/      AHI 历史方法，draft
├── aster/                              ASTER 待导入说明，暂无实现
├── aatsr/
│   └── global/001deg_2003_2012/        全球 0.01° 日/月统计
├── modis/
│   └── unclassified/legacy_draft/      MODIS 历史方法，draft
├── msg/
│   └── europe_africa/dual_disk/        MSG + IODC 双星盘案例
├── slstr/
    ├── heihe/study_area_2022/          黑河，研究区优先
    └── europe_south_africa/
        └── scene_first_migrated/       欧洲/南非，逐景优先迁移快照
└── viirs/
    └── unclassified/legacy_draft/      VIIRS 历史方法，draft
```

只有带 `case.toml` 的目录才算一个已登记案例。`draft` 表示代码已经归到案例，但区域、
机器路径、依赖和结果还没有完成验证，不能当作生产入口。当前状态和入口见
`catalog.toml`；三个独立运行项目的来源提交见 `projects.toml`。

## 一个案例应包含什么

```text
cases/slstr/heihe/summer-2022/
├── README.md                 目的、输入、输出和运行顺序
├── case.toml                 传感器、区域、时期、空间路线、算法版本
├── machines/
│   ├── hero.toml             可提交的某台机器路径/并行设置
│   └── local.toml            本机临时配置，Git 忽略
└── stages/
    ├── 01_download.py
    ├── 02_prepare.py
    ├── 03_retrieve.py
    └── 04_validate.py
```

同一研究可以有多台机器配置，不必复制算法；黑河、非洲、欧洲或不同产品版本则分别建立
案例。案例可以采用旧 HDF5/GeoTIFF 实现，也可以调用标准 NPZ 模块，但必须在
`case.toml` 的 `standard_core` 中如实记录。

## 两种空间路线

1. `study-area-first`：相邻影像先投影、拼接或裁剪为完整研究区，再反演 LST/LSCT。
2. `scene-first`：逐景完成 LST/LSCT，再拼接或裁剪结果。

MSG 固定网格案例还可标记 `fixed-grid`；全球日/月统计可标记 `temporal-composite`。
轨道和时次分组是科学条件，必须由案例显式提供，标准代码不会猜测。

## 新建与归档

```bash
python cases/_templates/new_case.py slstr heihe summer-2022 \
  --mode study-area-first
```

不再使用的脚本先移到 `_archive/`，不立即删除。归档内容不作为生产入口，不参与当前
案例的默认检查；需要恢复时按模板重新登记和验证。
