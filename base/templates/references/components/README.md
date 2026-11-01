# components

本目录可以复制到任意位置；`run.py` 内含所需科学函数，无 LS4T 仓库依赖。

需要 Python 3.10+；`pip install -r requirements.txt`，然后 `python run.py`。
默认运行合成演示并写入 `$LS4T_PRODUCT_ROOT/<案例目录名>/demo.npz`，重复运行拒绝覆盖。
接入真实数据：改 `USE_DEMO=False`、`DATA_ROOT`、`INPUT_FILES`、`OUTPUT_DIR` 和末尾 `main()`。
输入 NPZ 的字段、形状和示例见本文件 `demo_input()`；必需字段在 `main()` 中直接读取。
温度为 K，角度为度，小时为地方太阳时；QA 采用本文件 QualityFlag，不可直接传卫星原生 QA。
函数来源、原文件及函数文本哈希见 `SOURCE_SNAPSHOT.json`。副本后续独立维护，不自动同步。
`requirements.txt` 是最低依赖要求，并非冻结环境；正式实验另存实际环境清单。
演示验证代码执行与数值关系，不代表真实遥感产品精度。输出内记录输入来源和执行脚本哈希。

运行前设置 `LS4T_DATA_ROOT`、`LS4T_PRODUCT_ROOT`，或直接填写代码中的外部路径。
没有默认存储目录；未指定时在写文件前退出。禁止数据和产品进入代码目录或互相嵌套。
