# Case templates

这里提供创建真实案例的结构模板，不提供全项目统一调度器。一个案例对应一个明确的
传感器、研究区、科学设置和时间范围；同一案例可以有多个机器配置，不应为换机器复制
整套算法。

## 新建案例

从项目根目录运行：

```bash
python cases/_templates/new_case.py slstr heihe summer-2022 \
  --mode study-area-first
```

生成位置为 `cases/slstr/heihe/summer-2022/`。随后：

1. 编辑 `case.toml`，确定年份、网格、阶段及 LS4T 版本；
2. 复制 `machines/example.toml` 为 `machines/local.toml` 并填写本机路径；
3. 用 `run_standard_stage.py --list` 查看该传感器已有的标准批处理阶段；
4. 把研究区分组、下载、LSCT 权重准备和验证写入 `stages/`；
5. 可复用的科学计算移到根目录模块，不要在多个案例间复制。

机器文件中的路径会原样传给标准函数的 `*_root` 参数；各传感器现有的年份/日期子目录
约定并不完全相同，接入既有数据树前应先核对对应模块。特别是当前 SLSTR 批量 LST
入口默认读取 `{year}/reconstruct`；若案例从投影或研究区产品反演，应在 `stages/` 中
显式调用单产品函数，而不能假定模板替它改了数据层级。

`local.toml`、日志和输出默认被 Git 忽略。需要共享某台服务器的路径时，可提交命名为
`machines/<hostname>.toml` 的配置，但不得包含密码或访问令牌。

登记到 `catalog.toml` 后，可检查结构而不执行科学代码：

```bash
python cases/_templates/audit_cases.py
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

MODIS、VIIRS、AHI 目前只有 `cases/` 中的旧处理方法，尚未形成根目录标准模块。ASTER
目前没有导入实现。它们仍可用模板建立案例，但 `run_standard_stage.py` 会明确要求使用
案例自己的 `stages/`，不会假装存在标准阶段。

## 模板明确不做什么

- 不自动判断哪些轨道、时次或视角可以组成一个研究区输入组；
- 不自动生成特定冠层模型所需的 LSCT `effective_weights`；
- 不统一不同数据中心的下载认证；
- 不隐藏 PBS、Slurm、systemd、并行数和机器磁盘布局；
- 不把历史 HDF5/GeoTIFF 脚本冒充为已经迁移到标准 NPZ 产品的实现。

这些内容都是具体研究和运行条件，应在案例自己的 `stages/` 与 machine profile 中明确。
