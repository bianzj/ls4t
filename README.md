# LS4T

LS4T 按产品组织代码，按目录和年份手工运行。项目不提供统一 CLI，也不把不同传感器强制包装成相同接口。

`/home/hero/work/ls4t` 是当前唯一主工作目录。`/home/hero/work` 下名称以
`ls4t-` 开头的其它目录是同一 Git 仓库的传感器工作树，用于保留历史实验、区域参数和
运行脚本，不是独立项目。工作树职责和整理规则见
[docs/WORKTREES.md](docs/WORKTREES.md)。

## 源码结构

```text
src/
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
├── composite.py             时间合成
└── applications.py          TVDI 等 L4 应用
```

没有 `src/ls4t/`、`production/`、`products/` 或统一流程包。

## 参数和运行方式

每个可手工运行的文件都遵守同一规则：

1. 文件最上面集中定义输入目录、输出目录、年份、日期、阈值和覆盖方式。
2. 函数参数默认是 `None`。
3. 参数为 `None` 时使用文件顶部的默认参数；外部传值时使用外部参数。
4. 一个函数只完成一个阶段，不自动调用下一个阶段。
5. 文件末尾只保留本次需要执行的一个函数。

例如直接提取 SLSTR：

```python
if __name__ == "__main__":
    slstr_extract()
```

每个 SLSTR 阶段都有自己的文件；例如解压运行
`PYTHONPATH=src python src/slstr/slstr_unzip.py`，投影运行
`PYTHONPATH=src python src/slstr/slstr_project.py`。只修改所选文件顶部的参数，
不会自动调用其它阶段。`slstr_data.py` 中仍保留同名兼容入口，旧脚本可以继续导入。

需要投影时手动改成：

```python
if __name__ == "__main__":
    slstr_project()
```

从项目根目录运行：

```bash
PYTHONPATH=src python src/slstr/slstr_extract.py
```

外部程序也可以直接调用某个批处理函数：

```python
from slstr.slstr_data import slstr_extract

slstr_extract(
    indir_raw="/data/slstr/raw",
    outdir_extract="/data/slstr/extract",
    years=range(2022, 2025),
)
```

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
