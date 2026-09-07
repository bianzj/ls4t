# ASTER cases

当前 LS4T 仓库中没有找到可确认来源的 ASTER 真实运行实例，因此这里先保留案例入口，
不复制或虚构地区、日期和机器配置，也不在 `catalog.toml` 登记空案例。机器无关的
标准产品、投影、拼接和可配置 LST 接口位于根目录 `aster/`。

取得现有 ASTER 脚本后，应按以下位置导入：

```text
cases/aster/<region>/<case-id>/
├── README.md
├── case.toml
├── machines/
└── stages/ 或原始实现目录
```

完成一个真实区域和日期的输入、输出验证后，再把 ASTER HDF 原生解码器从案例提升到
根目录 `aster/aster_extract.py`；现阶段标准提取入口接收已经解码为开尔文的数组。
