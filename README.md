# LS4T

LS4T 按产品组织可复用代码，并用自动化测试和最小样例验证。项目不提供统一 CLI，
也不把不同传感器强制包装成相同接口；真实生产运行统一由 `cases/` 中的脚本配置。

`/home/hero/work/ls4t` 是通用算法和产品结构的主项目。AATSR、MSG、SLSTR 的实际
运行脚本分别维护在独立的 case 项目中；主项目的 `cases/` 保存案例说明、历史案例和
这些独立项目的关联。项目关系见 [cases/README.md](cases/README.md)。

## 源码结构

```text
ls4t/
├── base/                    公共数值、质量、产品读写和空间算法
├── aatsr/
│   ├── aatsr_data.py        AATSR 解压与数据提取
│   ├── aatsr_project.py     AATSR 逐景投影
│   ├── aatsr_region.py      AATSR 研究区前处理/结果后处理
│   ├── aatsr_lst.py         AATSR 地表温度
│   └── aatsr_lsct.py        AATSR 组分温度
├── slstr/
│   ├── slstr_data.py        SLSTR 数据模型、单景读写和兼容入口
│   ├── slstr_unzip.py       SLSTR 压缩包解压
│   ├── slstr_extract.py     SLSTR 原生数组提取
│   ├── slstr_reconstruct.py SLSTR 网格重建
│   ├── slstr_project.py     SLSTR 投影到目标栅格
│   ├── slstr_merge.py       SLSTR 按日合并
│   ├── slstr_region.py      SLSTR 研究区前处理/结果后处理
│   ├── slstr_lst.py         SLSTR 地表温度
│   └── slstr_lsct.py        SLSTR 组分温度
├── msg/
│   ├── msg_data.py          MSG 数据读取
│   ├── msg_project.py       MSG 投影（目标网格不同时使用）
│   ├── msg_region.py        MSG 研究区前处理/结果后处理
│   ├── msg_lst.py           MSG 地表温度
│   └── msg_lsct.py          MSG 组分温度
├── normalization/
│   ├── angle.py             角度归一化
│   ├── time.py              地方太阳时归一化
│   ├── space.py             空间归一化
│   ├── sensor.py            传感器归一化
│   └── fusion.py            多传感器融合
├── composite/               时间合成
├── applications/            TVDI 等 L4 应用
└── cases/                    实际案例、历史实验和独立 case 项目索引
```

源码直接从项目根目录开始，不再增加名为 `src/` 的中间层，也不使用统一流程包。

## 代码、测试和案例边界

根目录模块只保存函数、数据模型和稳定算法，不保存 `/home/...`、`/media/...` 等
机器路径，也不提供直接执行的 `__main__`。`tests/` 使用合成数据和临时目录验证算法；
输入目录、输出目录、年份、研究区、覆盖策略和本次启用的阶段全部放在 `cases/`。

每个阶段仍保持独立，不自动调用下一阶段。案例脚本显式传入运行参数，例如：

```python
from pathlib import Path

from slstr.slstr_extract import slstr_extract

CASE_ROOT = Path("data/slstr-example")

slstr_extract(
    indir_raw=CASE_ROOT / "raw",
    outdir_extract=CASE_ROOT / "extract",
    years=range(2022, 2025),
)
```

如果缺少执行所需的路径或年份，核心批处理函数会提示到 `cases/` 中配置，而不会使用
开发者机器上的隐式默认值。历史运行材料位于 `cases/legacy/`，当前 AATSR、MSG、
SLSTR 生产案例见 [cases/README.md](cases/README.md)。

## 产品层级

```text
L1O → L2LST / L2LSCT → L3N → L3C → L4A
```

角度、时间、空间和传感器归一化分别手工执行。融合只接受已经处于相同网格和归一化基准的 L3N 数据。

旧目录保留为迁移和回归依据，不作为新源码运行入口。详细边界见 [docs/PRODUCT_ARCHITECTURE.md](docs/PRODUCT_ARCHITECTURE.md) 和 [docs/PIPELINE.md](docs/PIPELINE.md)。

## 两种空间处理方式

项目明确保留两条路线，不自动混合：

1. **先形成研究区，再反演**：原始数据 → 提取 → 逐景投影 →
   `*_data_region()` 拼接/裁剪相邻影像 → LST/LSCT。适合多个相邻条带共同覆盖
   一个研究区，辅助数据和反演都按完整研究区处理。
2. **逐景反演，再形成研究区**：原始数据 → 提取 → 逐景投影 → 逐景 LST/LSCT →
   `*_result_region()` 拼接/裁剪。适合保留逐景质量、过境时间和中间结果。

三个传感器分别使用 `aatsr_region.py`、`slstr_region.py` 和 `msg_region.py`。
传入同一组的文件必须属于同一次获取、同一视角和同一目标网格；不应把不同时次
或不同视角混在一次拼接中。详细运行顺序见
[docs/SPATIAL_MODES.md](docs/SPATIAL_MODES.md)。
