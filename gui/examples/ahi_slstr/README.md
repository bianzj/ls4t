# AHI + SLSTR 独立路线样例

当前界面分为组分反演与角度归一化两条独立路线。`sample.json` 用于组分反演；
`normalization.json` 直接使用已保存的 LST，独立标定 secant 角度系数并归一化。
`result.json` 保留首次版本的完整历史基准（包含旧的组分模型方向转移），不作为
当前归一化路线的参考结果。当前组分接口只返回组分温度和拟合诊断。
当前角度路线结果见 `normalization_result.json`，不依赖组分温度。


本目录是明确保留的小型离线测试夹具：真实卫星观测摘取值、两份分裂窗系数、
固定参考结果与界面验收图。大体积源文件保留在 `E:/remote-sensing`，没有改写。

## 重放

在 LS4T 根目录执行 `gui/start.bat`，打开工作台，加载样例并运行。
也可独立调用后端（不需要浏览器、原始数据盘或网络）：

```powershell
$env:PATH = 'C:\work\miniconda\envs\python311\Library\bin;' + $env:PATH
C:\work\miniconda\envs\python311\python.exe gui/run_known_sample.py --output D:/examples/ls4t/ahi-slstr-result.json
```

`sample.json` 保存输入与完整源文件 SHA-256；`source_pixels.npz` 保存读取的原始像元。
`result.json` 是固定参考结果。重新摘取使用 `gui/prepare_known_sample.py`，需要原始数据盘和 GDAL。
系数来自本机 Seebor 白天表，分别标记为 AHI 与 SLSTR，不可交换使用。

## 样例内容

- 2019-01-01 02:50 UTC，112.000463°E、32.006484°N。
- AHI 原格网约 2 km；SLSTR 四个 1 km 像元按各通道 Planck 辐射平均到同一网格。
- 样本选择仅依据预先指定区域、有效覆盖和云筛选，未按反演误差挑选。
- LAI = 0.387（MUSYQ）；TCWV = 0.628 cm（归档 TCW 的编码假设）。
- 土壤发射率 0.971/0.977（MODIS 波段代理）；植被发射率 0.985/0.990 为可编辑情景假设。
- 仅 SLSTR 双视角拟合土壤/植被温度；AHI 留出，不进入温度目标函数或先验选择。

固定输入下土壤/植被温度为 272.186917 / 284.659093 K；
AHI 留出差值 0.323685 K。天底归一化 LST：SLSTR 双视角 274.606219 K，
AHI 约 274.939 K（以 result.json 完整数值为准）。

## 科学边界

这是**真实观测 + 已知参数情景的程序重放**，没有独立地面组分温度验证。
双视角对应两组分，没有额外拟合自由度，零残差不代表准确。
角度修正为 `T_obs + M(reference) - M(observed)`，保留模型残差；
保持观测时刻、太阳几何与波长，不消除 AHI/SLSTR 光谱差异。

本地归档的时间按 HHMM UTC 解码、水汽按 kg/m²×100 解码：与数值范围及
AHI 配对一致，但没有重新审核原始 L1 时间和水汽生成程序，因此属于显式假设。
SLSTR 辅助角度、时间、云字段为 10 km 最近邻；AHI 观测方向采用 140.7°E
标称同步轨道计算。AHI 有效性使用同期已有 LST 的有效像元作代理，未重新执行原生云检测。
这些限制均随输入/结果导出。样例不能用来证明业务精度或宣称归一化普遍改善误差。

数据类型背景：[Copernicus SLSTR 产品说明](https://sentiwiki.copernicus.eu/web/slstr-products)。
