# LS4T 测试与最小验证

顶层现有 38 个 `test_*.py` 文件；参数化执行数与函数定义数不同。
自动化测试检验实现契约，真实小样本重放检验可复现性，两者均不自动代表独立地面精度。

## 主要类别

| 类别 | 代表文件 |
|---|---|
| 基础物理、反演与定标 | `test_physics.py`、`test_retrieval.py`、`test_calibration.py`、`test_known_inputs.py` |
| 核模型、时间与空间归一化 | `test_kernel_models.py`、`test_annual_cycle.py`、`test_normalization*.py`、`test_multisource_normalization.py`、`test_tsharp.py` |
| 产品、传感器与空间流程 | `test_products.py`、`test_dual_thermal_sensors.py`、`test_slstr_products.py`、`test_spatial_modes.py` |
| 界面与任务执行 | `test_gui.py`、`test_gui_tasks.py`、`test_workbench_api.py`、`test_separate_routes.py`、`test_workspace_tools.py` |
| 独立模板与案例 | `test_standalone_cases.py`、`test_kernel_atc_case.py`、`test_three_site_kernel*.py` |
| 历史任务依赖与区域实验 | `test_*case_dependencies.py`、South America/Beijing/ERA5 等文件；按实际依赖和案例保留状态解释跳过或失败 |
| 真实输入夹具 | `test_msg_evo_sample.py`、`test_slstr_evo_sample.py` |

## 源码环境运行

先将现有 Conda 环境的 DLL 目录加入 PATH，再运行；不直接替换已配置环境：

```bat
set "LS4T_TEST_ENV=C:\work\miniconda\envs\python311"
set "PATH=%LS4T_TEST_ENV%;%LS4T_TEST_ENV%\Library\bin;%LS4T_TEST_ENV%\Scripts;%PATH%"
"%LS4T_TEST_ENV%\python.exe" -B -m pytest tests -q -p no:cacheprovider
```

快速检查核心反演和黑河 3×3：

```bat
"%LS4T_TEST_ENV%\python.exe" -B -m pytest tests/test_retrieval.py tests/test_three_site_kernel_3x3.py -q -p no:cacheprovider
```

已有 MSG EVO 小样本为 10×10 窗口的真实影像裁剪，SLSTR EVO 样本见
[examples/README.md](examples/README.md) 和各样本说明。原始产品、定标、NoData 和参考解须一起解释。
黑河真实数据重放见 [案例说明](../cases/ahi-slstr/heihe/three-site-kernel-3x3/README.md)。

本轮完整执行结果和已知失败以 `D:\发布\ls4t\安装文件\0.1.0\验证记录` 的日志、
JUnit XML 和验收 JSON 为准，不用先前的 12 项检查替代全量结果。
