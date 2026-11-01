# Case templates

`new_case.py` 默认把 `base/templates/references/` 中的自包含代码复制到新案例目录。
科学函数和实际执行代码都在案例自己的 `run.py`；无需导入 LS4T，无统一调度器。
也可以手动复制参考目录，或从 base 选取需要的函数粘贴到案例。

一个案例对应明确的卫星或卫星组合、研究区、科学设置和时间范围；副本可独立修改，
base 后续变化不会自动改变案例结果。来源记录只用于查对，不参与运行。

## 新建案例

从项目根目录运行：

```bash
python base/templates/new_case.py slstr heihe summer-2022 --reference normalization
python cases/slstr/heihe/summer-2022/run.py
```

多个卫星的具体任务可用组合名称，例如：

```bash
python base/templates/new_case.py slstr-modis heihe fusion-2022 --reference normalization
```

名称只确定任务目录；实际读取哪些卫星、如何配对和处理仍直接写在本任务代码中。

生成位置为 `cases/slstr/heihe/summer-2022/`。可选 `components`、`normalization`、
`kernel_atc`。安装目录内第三方依赖后可移到仓库外运行。
真实任务修改 `USE_DEMO`、输入路径、参数和末尾 `main()`，按需要增加日期循环与并行。
参考内容与输入约定见 [参考组装](references/README.md)。

## 旧配置式模板（兼容）

显式指定 `--legacy-template --mode study-area-first` 才复制 `case/` 骨架。旧案例可继续：

1. 编辑 `case.toml`，确定年份、网格、阶段及 LS4T 版本；
2. 复制 `machines/example.toml` 为 `machines/local.toml` 并填写本机路径；
3. 用 `run_standard_stage.py --list` 查看该传感器已有的标准批处理阶段；
4. 把研究区分组、下载、LSCT 权重准备和验证写入 `stages/`；
5. 新增算法可复制到本案例内；通用改进也可以人工整理回 `base/`，不自动同步。

机器文件中的路径会原样传给标准函数的 `*_root` 参数；各传感器现有的年份/日期子目录
约定并不完全相同，接入既有数据树前应先核对对应模块。特别是当前 SLSTR 批量 LST
入口默认读取 `{year}/reconstruct`；若案例从投影或研究区产品反演，应在 `stages/` 中
显式调用单产品函数，而不能假定模板替它改了数据层级。

`local.toml`、日志和输出默认被 Git 忽略。需要共享某台服务器的路径时，可提交命名为
`machines/<hostname>.toml` 的配置，但不得包含密码或访问令牌。

登记到 `catalog.toml` 后，可检查结构而不执行科学代码：

```bash
python base/templates/audit_cases.py
```

只有需要检查当前机器数据是否挂载时才加 `--strict-paths`。

## 标准代码目前能做什么

| 能力 | AATSR | MSG | SLSTR |
|---|---:|---:|---:|
| 解压/原始读取 | 是 | 原始读取 | 是 |
| 提取为标准数据产品 | 是 | 是 | 是 |
| 几何重建 | 不需要 | 不需要 | 是 |
| 投影到目标网格 | 是 | 可选 | 是 |
| 按日合并 | 案例实现 | 固定网格案例实现 | 是 |
| LST | 是 | 是 | 是 |
| LSCT | 是，需准备权重输入 | 是，需准备权重输入 | 是，需准备权重输入 |
| 研究区前拼接/裁剪 | 是 | 是 | 是 |
| 结果后拼接/裁剪 | 是 | 是 | 是 |
| 角度/时间/空间归一化 | 通用模块 | 通用模块 | 通用模块 |
| 时间合成和 TVDI | 通用模块 | 通用模块 | 通用模块 |

MODIS、VIIRS、AHI、ASTER 也有 `base/` 下的标准包，提供 prepared-array 提取、投影、显式
影像组拼接和 LST。它们的原始 HDF/NetCDF 解码器尚未全部通过机器无关验证，因此真实
案例仍可在自己的 `stages/` 中调用旧读取逻辑，再把标准数组交给 `base/` 中的模块。

| 能力 | MODIS | VIIRS | AHI | ASTER |
|---|---:|---:|---:|---:|
| 标准数组提取 | 31/32 | M15/M16 | 14/15 | 13/14 |
| 原始任务文件解码 | 案例验证中 | 案例验证中 | 案例验证中 | 尚无案例 |
| 投影 | 是 | 是 | 可选 | 是 |
| 显式影像组拼接 | 是 | 是 | 是 | 是 |
| LST | 是，需系数 | 是，需系数 | 是，需系数 | 是，需系数 |
| 两种研究区路线 | 是 | 是 | 是 | 是 |

## 模板明确不做什么

- 不自动判断哪些轨道、时次或视角可以组成一个研究区输入组；
- 不自动生成特定冠层模型所需的 LSCT `effective_weights`；
- 不统一不同数据中心的下载认证；
- 不隐藏 PBS、Slurm、systemd、并行数和机器磁盘布局；
- 不把历史 HDF5/GeoTIFF 脚本冒充为已经迁移到标准 NPZ 产品的实现。

这些内容都是具体研究和运行条件，应在案例自己的 `stages/` 与 machine profile 中明确。
