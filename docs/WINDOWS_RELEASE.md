# LS4T Windows 发布

发布入口：`D:\发布\ls4t`。`安装文件\0.1.0` 保存安装 EXE、源码 ZIP、依赖/校验记录；
`推广案例` 保存完整可分发案例和本轮离线重放结果。

## 安装版

安装器为当前用户安装，不要求管理员权限；可选择路径。默认目录为 `%LOCALAPPDATA%\Programs\LS4T`。
开始菜单的 LS4T 入口运行 `LS4T.exe`，启动本地浏览器工作台。关闭运行窗口或按 Ctrl+C 停止服务。
安装器只管理程序文件；卸载保留用户配置和用户自行选择的结果目录。

随包提供独立 Python 3.11、NumPy、SciPy、scikit-learn、pandas、h5py、GDAL/PROJ、netCDF4、
matplotlib 及相关依赖。随包 Python 可直接运行离线案例，不依赖开发机 `C:\work\miniconda`。
安装版的运行时与源码快照在构建阶段固定，清单记录实际版本与 SHA256。
Satpy 和 pyepr 等可选原始产品读取依赖未随此包提供；不把所有传感器原始产品处理列为已验收能力。

已支持的工作台包括 LST、组分温度反演、时间/角度/空间归一化及 SLSTR 批处理。
生产批处理所需的完整卫星影像、LAI、水汽、发射率及地类数据需要用户显式指定外部路径，
不会随安装器复制整套数据。界面内置样例仅作方法和流程演示。

安装版配置与任务保存在 `%LOCALAPPDATA%\LS4T`。源码启动仍沿用原有 `gui/local.json`
和 `gui/tasks.json`；可通过 `LS4T_STATE_DIR` 指定独立状态目录、`LS4T_PYTHON` 指定运行解释器。

## 构建

`scripts/build_windows.py` 在 Windows 使用既有环境和 NSIS 构建；不修改现有 Conda 环境，
不覆盖既有构建目录或同名发布文件。示例：

```bat
python scripts/build_windows.py --python-env C:\work\miniconda --makensis C:\path\to\makensis.exe --staging C:\project\ls4t\new-build --output-root D:\发布\ls4t\安装文件\0.1.0
```

源码快照包含当前公共算法、工作台、文档、测试、小样本和选定案例，不含 `.git`、用户任务、
账号认证、完整影像、临时日志和历史归档。当前工作树已有未提交改动，不能只用 HEAD 识别本包；
必须同时保留 `SOURCE_MANIFEST.json` 的逐文件哈希。

本轮整体使用原冻结案例的 `C:\work\miniconda` 科学运行时，包括 NumPy 2.2.6、
SciPy 1.17.1、pandas 3.0.2 及其匹配的 BLAS/MKL DLL。两个现有开发环境均保持原位；
不混用两个环境的数值二进制库，不降低案例校验阈值、不改参考结果。
构建在打包前必须实际重放固定案例并通过原始校验。

本轮实际安装、启动、计算、离线案例与测试结果记录在发布目录的 `验证记录`。
单机隔离目录验证不能替代另一台干净 Windows 上的兼容性测试，软件测试也不等于科学精度认证。
