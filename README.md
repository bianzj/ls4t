# LS4T

LS4T 提供地表温度、组分温度反演，角度/时间/空间归一化及降尺度方法。当前版本 `0.1.0`。

Windows 日常开发入口：`C:\work\ls4t`。安装程序与推广案例入口：`D:\发布\ls4t`。

## 从哪里开始

| 内容 | 入口 | 用途 |
|---|---|---|
| 代码 | `base/` | 公共算法和各传感器处理函数 |
| 理论与思路 | [文档目录](docs/README.md)、[方法手册](docs/METHOD_INVENTORY.md) | 查公式、参数、约束及源码位置 |
| 自动化测试与小样本 | [测试说明](tests/README.md) | 查测试分类、运行命令与验证边界 |
| 浏览器工作台 | [界面说明](gui/README.md)、`gui/start.bat` | LST/LSCT、归一化及 SLSTR 批处理 |
| 当前执行案例 | [案例目录](cases/README.md) | 明确的区域、日期、输入和输出路径 |
| Windows 安装版 | [发布与安装说明](docs/WINDOWS_RELEASE.md) | 随包运行时、打包与安装验证 |
| C/D 盘安排 | [存储说明](docs/STORAGE_LAYOUT.md)、[项目关系](docs/PROJECTS.md) | 开发、分发和历史结果的实际位置 |

## 启动和测试

在本机已配置的源码环境中运行：

```bat
gui\start.bat
```

默认打开 `http://127.0.0.1:8840`。源码启动仍沿用现有 Conda 环境；分发安装版使用随包运行时。
主要测试命令和真实输入说明见 [tests/README.md](tests/README.md)。

## 理论和产品流程

公共实现保存在 `base/`。AATSR、SLSTR、MSG、MODIS、VIIRS、AHI、ASTER 各有处理接口；
接口存在不等于每种原始产品已在安装版验收。当前 GUI 主要支持数值工作台与 SLSTR 批处理。

产品链为 `L1O → L2LST/L2LSCT → L3N → L3C → L4A`。角度、时间、空间与传感器归一化
独立执行；融合要求同网格、同归一化基准。两种空间路线见 [空间处理方式](docs/SPATIAL_MODES.md)。
核模型和年温度周期见 [KERNELS_ATC.md](docs/KERNELS_ATC.md)，多变量降尺度与 TsHARP 见
[TSHARP.md](docs/TSHARP.md)。完整、可复制的合成参考脚本见
[参考组装](base/templates/references/README.md)。

## 案例和数据

当前可离线复现的真实案例为 [黑河三站 AHI+SLSTR 3×3 核拟合](cases/ahi-slstr/heihe/three-site-kernel-3x3/README.md)：
2019-05-12，大满、阿柔、四道桥，共 27 组足迹。固定输入与参考结果保留在 C 盘；
对外演示副本、ZIP 和本轮重放输出放 `D:\发布\ls4t\推广案例`。
AHI 参与拟合；阿柔全部未通过修正幅度门槛。该案例用于复现与质量控制演示，不能当作独立地面精度验证。

`tests/data/` 保留 MSG EVO、SLSTR EVO 等小范围真实输入。完整卫星数据沿用原 F/H/E 等数据位置，
历史完整结果仍在 `D:\cases\ls4t`，本轮不改变大型数据或历史批次。

新建自包含执行案例：

```bat
python base/templates/new_case.py slstr heihe summer-2022 --reference normalization
```

在生成的脚本中显式填写仓库外的输入/输出目录，再运行。通用原版与案例副本独立维护。
旧 `cases/catalog.toml`、`projects.toml` 和 `multisource-normalization/` 当前已不在活动工作树；
不按旧 README 将它们视为可运行入口。历史 `audit_cases.py` 只适用于有旧 TOML 登记的快照。
