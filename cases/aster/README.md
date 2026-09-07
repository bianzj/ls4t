# ASTER cases

当前 LS4T 仓库中没有找到可确认来源的 ASTER 数据准备或 LST/LSCT 实现，因此这里先
保留传感器入口，不复制或虚构处理代码，也不在 `catalog.toml` 登记空案例。

取得现有 ASTER 脚本后，应按以下位置导入：

```text
cases/aster/<region>/<case-id>/
├── README.md
├── case.toml
├── machines/
└── stages/ 或原始实现目录
```

完成一个真实区域和日期的输入、输出验证后，再决定哪些函数足够通用，可以提升为根目录
`aster/` 标准模块。
