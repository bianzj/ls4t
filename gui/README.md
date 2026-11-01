# LS4T 地表温度反演与归一化工作台

首页 `/` 提供两个工作台，所有功能均有独立地址、参数和结果。

| 工作台 | 功能 | 地址 |
|---|---|---|
| 反演工作台 | 地表温度反演 | `/retrieval/surface` |
| 反演工作台 | 地表组分温度反演 | `/retrieval/components` |
| 反演工作台 | 地表温度批处理（全链路） | `/retrieval/batch` |
| 归一化工作台 | 时间归一化 | `/normalization/time` |
| 归一化工作台 | 角度归一化 | `/normalization/angle` |
| 归一化工作台 | 空间归一化 | `/normalization/space` |
| 归一化工作台 | 归一化（批处理） | `/normalization/batch` |

地表温度反演仅执行亮温 → LST；已有 LST 保留原值。使用 `gui.workspace_tools.run_surface`，
接口 `POST /api/surface/run`。云污染观测会被拒绝，不调用组分求解。

时间归一化使用已有 `normalize_local_solar_time` 单谐波模型，给定振幅和峰值时刻，
所有时刻均为**地方太阳时**。空间归一化使用已有 `aggregate_to_grid`，按明确的目标行列号
和正权重聚合，空格为缺测。它不自动重投影或降尺度。这两个页面的默认数据是受控演示，
不是 AHI/SLSTR 地面精度验证。接口分别为 `POST /api/time/run`、`POST /api/space/run`。

归一化批处理接收各归一化页面导出的 JSON 配置，逐任务独立执行（最多 64 项），
返回成功/失败和每项结果；单项异常不终止其他任务。接口 `POST /api/normalization/batch`，
请求为 `{"jobs": [配置1, 配置2]}`，支持 `route=time/space/normalization`。
Python 后端入口为 `gui.workspace_tools.run_time/run_space/run_batch`。

各页面通过浏览器 sessionStorage 保存当前标签页的草稿和结果；导航、刷新可恢复，
关闭会话前请导出需要长期保存的配置和结果。修改输入立即使旧结果失效。
全链路页面沿用原有 SLSTR 任务队列：LST 任务可由 zip 开始自动解压和重整，组分反演作为单独阶段任务。

## 组分与角度路线

### 组分温度反演

固定 LAI、水汽和土壤/植被双波段发射率，从亮温或已有 LST 求解两/三组分温度。
温度优化是本路线内的可选设置。只输出组分温度与拟合诊断，不执行角度归一化。
后端：`base.known_inputs.run_workbench`；接口：`POST /api/retrieval/run`。
旧 `/api/workbench/run` 也只执行组分反演。

### 角度归一化

直接输入已有 LST、观测天顶角、目标天顶角。使用独立 secant 模型
`T(theta) = a + c * (sec(theta) - 1)`，可以从同地表、同传感器、近同时的
多角度 LST 标定系数，或直接输入已有系数（支持单条 LST）。
只输出归一化 LST、角度修正量与标定诊断；不读取 LAI、水汽或发射率，
不运行组分反演或组分温度优化。模型不包含太阳/相对方位角效应。
后端：`base.normalization.workbench.normalize_observations`；
接口：`POST /api/normalization/run`；样例：`GET /api/normalization/sample`。

各路线分别保存当前会话的配置和结果，切换不会自动运行另一条路线。
配置和结果导出带 route 标识；其他路线的配置不可误导入当前路线。

AHI + SLSTR 样例见 [说明](examples/ahi_slstr/README.md)。
归一化的 `normalization.json` 使用已保存的 LST 输入，SLSTR 双视角标定一个
角度系数，AHI 仅作为探索性迁移检验；不在载入或运行时调用组分温度反演。
两角度没有额外标定自由度，低残差不代表地面精度。

独立命令行：

```powershell
python gui/run_known_sample.py --config gui/examples/ahi_slstr/sample.json --output D:/examples/ls4t/components.json
python gui/run_known_sample.py --config gui/examples/ahi_slstr/normalization.json --output D:/examples/ls4t/normalized.json
```

## 原有批量处理

在浏览器里建立并运行 SLSTR 处理任务。左侧是任务列表，右侧是所选任务的执行情况：状态、进度、完成/跳过/失败的景数、失败原因和日志。

## 启动

双击 `gui/start.bat`，或在 ls4t 根目录执行：

```bat
gui\start.bat            :: 默认 http://127.0.0.1:8840 并自动打开浏览器
gui\start.bat --port 8850 --no-browser
```

`start.bat` 会先把 `C:\work\miniconda\envs\python311` 的 `Library\bin` 等目录加入 PATH。不激活环境直接运行这个解释器时，LAPACK 无法加载，LSCT 会崩溃。使用别的 conda 环境时，设置 `LS4T_PYTHON_ENV` 环境变量。

服务只监听本机 127.0.0.1，并拒绝跨站请求。

## 三种任务

新建任务时先选类型，再选输入目录、输出目录和处理年份。一个任务处理所选年份里的全部场景。已有结果的场景自动跳过，中断后重新运行会接着做；勾选“覆盖已有结果”则重新计算。

| 类型 | 输入目录 | 输出目录里的结果 | 另需选择 |
|---|---|---|---|
| 解压 | `.SEN3.zip`，一般按年份分目录，也可以平铺 | `年份/raw/<场景>.SEN3/`：只取 19 个需要的 NetCDF | — |
| LST 反演 | 解压后的 `.SEN3` 目录（解压任务的输出，或已解压的原始数据）；给 zip 目录也可以，会先解压 | `年份/tif/<场景>/`：重整后的条带 GeoTIFF；`年份/lst/<场景>/lst_nadir.tif`、`lst_obliq.tif`（K×100，0 为无效） | LAI、TCWV、辅助数据目录、土壤发射率两个波段、IGBP 类型图、是否处理夜间场景 |
| LSCT 反演 | LST 反演任务的输出目录（读取其中的 `年份/tif` 与 `年份/lst`） | `年份/lsct/<场景>/lsct2.tif`（波段 1 土壤、波段 2 植被，K） | LAI、辅助数据目录、土壤发射率两个波段、IGBP 类型图、是否处理夜间场景 |

全球数据的要求：

- **LAI：** 0.01°，`年份/LAI_YYYYDDD.h5`，或分在 `lai_2002-2020_0p01deg`、`lai_2021-2025_0p01deg` 里。
- **TCWV：** ERA5 小时数据，`年份/tcwv_YYYYMMDD.h5`。
- **辅助数据目录：** 需包含 `IGBP_Emi.txt`。LST 反演另外需要 `Sentinel3A_SLSTR_SW_Seebor_Coef_Day.txt`。
- **土壤发射率两个波段：** 从辅助数据目录的 tif 中选择，默认选 MODIS LSE11、LSE12。两个波段和类型图都必须是 0.01° 全球格网（36000×18000）。

表单会即时检查每一项，并逐年确认所选年份都有 LAI 和 TCWV。配置不完整时可以先保存，但不能运行。

其他说明：

- 任务列表保存在 `gui/tasks.json`。删除任务只是把它从列表移除，不会删除任何数据。
- 每次运行的日志在 `输出目录/_gui/<运行编号>.log`。最近一次运行的结果摘要记在任务里，服务重启后仍能看到。
- 一次只运行一个任务，其余任务排队等待。
- 右上角“运行环境”设置 Python 解释器和并行进程数，保存在 `gui/local.json`。LST 的每个计算进程约占 5 GB 内存，设置进程数时按内存估算。
- 输出目录结构与 `cases/slstr` 生产脚本相同，命令行和界面的结果可以混用。

## 与生产脚本的关系

- **LST 和 LSCT：** 逐景调用 `gui/legacy/slstr_lst_scene_parallel.py`、`slstr_lsct2_scene_parallel.py` 的 `process_day`。原案例脚本已被迁出，GUI 保留逐字节一致的已提交版本副本；来源提交和 SHA-256 记录于 `gui/legacy/SOURCE.json`，算法、常数和输出格式不变。
- **土壤发射率：** 使用任务里选的两个波段。LST 直接把文件路径传给生产函数；LSCT 按生产函数 `load_state` 相同的窗口读取方式和缩放构造状态，不加载它用不到的夜间系数。
- **重整：** 编码沿用 `cases/slstr-america/recover_local_raw.py`：
  - 经纬度：有符号 int16，度×100
  - 亮温：uint16，K×100，0 表示缺失
  - 角度：uint16，度×100，65535 表示缺失
  - 云标识：uint16 位掩码
  - 只取前 1200 行；tie-point 用线性插值

  没有使用 `slstr_data_scene_origin.py`，因为它会把负经纬度截成 0。
- **昼夜判断：** 与 `slstr_data_scene_origin.py` 相同，看天底中心像元 [500, 500] 的太阳天顶角，小于 85° 算白天。生产算法只有白天分裂窗系数，所以默认跳过夜间场景。
- **TCWV 文件格式：** 本机各年份的格式不同，界面统一处理：
  - `/data`、`/tcw`、`/tcwv` 三种数据集名都能识别
  - uint16 且没有 scale_factor 的按 ×100 解码
  - 整个小时全为 0 的视为缺失，落在这个小时的场景标为失败，不做反演
- **LSCT 分批：** 按场景的空间范围分批，每批的底图窗口不超过 4000 万像元。

## 文件

```text
gui/
├── server.py     HTTP 服务、任务运行队列（子进程执行，可取消）
├── worker.py     运行子进程入口
├── drivers.py    解压、LST、LSCT 三种任务的实现，调用 cases/slstr 生产模块
├── tasks.py      任务类型、保存与配置检查（gui/tasks.json）
├── layout.py     场景发现与输出目录约定
├── gdal_env.py   让未激活的 conda 解释器能加载 GDAL
├── settings.py   运行环境（gui/local.json）
├── start.bat     启动脚本
└── static/       页面
```
