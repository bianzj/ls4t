# LS4T

LS4T 只分两部分：

- **`base/`**：函数库和案例模板。通用算法、各传感器的标准处理函数都在这里，
  `base/templates/` 是可以复制到 `cases/` 的案例模板；
- **`cases/`**：单个执行案例。一个案例对应一个传感器、研究区和时间范围，真实数据路径、
  年份、机器和并行方式都写在案例里。

在案例中怎么用 `base/` 不做限制：可以复制 `base/templates/` 里的模板改配置后运行，
也可以直接写脚本调用 `base/` 中的通用函数。

```text
ls4t/
├── base/                        函数库 + 案例模板
│   ├── *.py、rt/                公共数值、质量、产品读写、空间算法、辐射传输
│   ├── aatsr/                   AATSR 解压、提取、投影、研究区、LST、LSCT
│   ├── slstr/                   SLSTR 解压、提取、重建、投影、合并、研究区、LST、LSCT
│   ├── msg/                     MSG 读取、投影、研究区、LST、LSCT
│   ├── modis/ viirs/ ahi/ aster/  双热通道提取、投影、拼接、研究区和 LST
│   ├── normalization/           角度、时间、空间、传感器归一化和融合
│   ├── composite/               时间合成
│   ├── applications/            TVDI 等 L4 应用
│   └── templates/               案例模板（case/ 骨架、new_case.py、audit_cases.py）
├── cases/                       执行案例（aatsr/、msg/、slstr/、slstr-heihe/ …）
│   └── _archive/                不再使用的历史脚本
├── tests/                       合成与真实输入自动化测试
├── docs/                        设计与流程说明
└── old/                         尚未分类的旧代码，不作为运行入口
```

## 新建并运行一个案例

两种方式任选，也可以混用。

**1. 复制模板**（标准阶段 + 配置文件）：

```bash
python base/templates/new_case.py slstr heihe summer-2022 --mode study-area-first
# 编辑 cases/slstr/heihe/summer-2022/case.toml 与 machines/local.toml
python cases/slstr/heihe/summer-2022/run_standard_stage.py --list
python cases/slstr/heihe/summer-2022/run_standard_stage.py extract --machine local
```

**2. 直接写脚本调用函数**：

```python
from pathlib import Path

from base.slstr.slstr_extract import slstr_extract

CASE_ROOT = Path("data/slstr-example")

slstr_extract(
    indir_raw=CASE_ROOT / "raw",
    outdir_extract=CASE_ROOT / "extract",
    years=range(2022, 2025),
)
```

在项目根目录运行案例脚本（或先 `pip install -e .`），`base` 即可直接导入。

## 边界

- `base/` 中除 `templates/` 外只放函数、数据模型和稳定算法，不写 `/home/...`、`/media/...`
  等机器路径，也没有 `__main__` 入口；
- 缺少路径或年份时，批处理函数会报错提示到 `cases/` 中配置，不使用隐式默认值；
- 每个阶段独立，不自动调用下一阶段；
- 在案例中验证过、且两个以上案例都需要的计算，整理后移入 `base/` 并补测试。

案例登记在 `cases/catalog.toml`；AATSR、MSG、SLSTR 三个独立私有运行项目的来源索引在
`cases/projects.toml`。登记后可以只检查结构、不执行科学代码：

```bash
python base/templates/audit_cases.py
```

详细结构见 [cases/README.md](cases/README.md) 和 [base/templates/README.md](base/templates/README.md)。

## MSG 真实数据测试样例

`tests/data/msg_evo_201710_10x10/` 保存 EVO 站点周围 10×10 像元的 2017 年 10 月
真实 MSG 数据：EURO/IODC 各 744 个逐小时 LST、31 个每日 LAI、观测角与发射率，
以及计算的太阳角和来源记录。输入沿用真实投影产品的 `PRODUCTS/.../年/月/日/`
目录和原文件名：一个时次一个单波段 UInt16 TIFF，保留原始定标编码与 NoData，
仅裁剪空间窗口。可直接离线运行土壤/植被组分反演，不依赖原始数据盘。

```bash
python tests/examples/msg_evo_sample.py run
python -m pytest tests/test_msg_evo_sample.py -q
```

需要 GDAL 和科学计算依赖；安装可使用 `pip install -e '.[msg-sample]'`。数据定义、
三组分参考解、重新提取命令和科学限制见 [样例说明](tests/examples/README.md)。

## 产品层级

```text
L1O → L2LST / L2LSCT → L3N → L3C → L4A
```

角度、时间、空间和传感器归一化分别手工执行。融合只接受已经处于相同网格和归一化基准的 L3N 数据。

MODIS、VIIRS、AHI 的现有旧任务状态为 `draft`；ASTER 尚无真实任务，但 `base/aster/`
已经提供标准产品与处理接口。详细边界见 [docs/PRODUCT_ARCHITECTURE.md](docs/PRODUCT_ARCHITECTURE.md) 和
[docs/PIPELINE.md](docs/PIPELINE.md)。实际案例的新建、机器配置、版本升级和归档流程见
[docs/CASE_WORKFLOW.md](docs/CASE_WORKFLOW.md)。

## 两种空间处理方式

项目明确保留两条路线，不自动混合：

1. **先形成研究区，再反演**：原始数据 → 提取 → 可选投影 →
   `*_data_region()` 拼接/裁剪相邻影像 → LST/LSCT。
2. **逐景反演，再形成研究区**：原始数据 → 提取 → 几何重建 → 添加辅助数据 →
   逐景 LST/LSCT → `*_result_region()` 拼接/裁剪。SLSTR 当前单景处理采用这条路线，
   投影是可选的，但几何重建是 LST 反演的前置条件。

SLSTR 观测和 LST 主流程从原始 `SEN3/*.nc` 提取后，MSG 主流程从 `.nat` 读取后，统一使用
GeoTIFF 保存中间数据和 LST 结果；不使用 NPZ 影像中间产品。

各传感器使用自己的 `*_region.py`；MODIS、VIIRS、AHI、ASTER 还提供独立的
`*_merge.py`，要求案例显式给出同一次获取的影像组。
传入同一组的文件必须属于同一次获取、同一视角和同一目标网格；不应把不同时次
或不同视角混在一次拼接中。详细运行顺序见
[docs/SPATIAL_MODES.md](docs/SPATIAL_MODES.md)。
