# AATSR global 0.01°

这是当前确认可运行的全球 AATSR 生产案例。主要入口：

- `aatsr_001deg_stats.py`：日/月统计，可按日期区间续跑；
- `generate_daily_monthly_cloud.py`：云筛选统计；
- `aatsr_monthly_3files.py`：把 2003–2011 月结果整理为 Ts、T、Tv 三个时间堆栈文件。

当前脚本仍直接使用 Hero 机器路径，`machines/hero.toml` 先作为路径和服务清单；后续修改
入口时应从该配置读取，而不是继续增加新的绝对路径。
