# MSG cases

- `lsct/`：来自私有项目 `bianzj/ls4t-msg@fdaa5bc` 的当前 LSCT、投影、合成和验证脚本。
- `preprocess/`：MSG 原始数据和 LST 的前处理脚本。
- `field/`：站点提取与统计。
- `auxiliary/`、`download/`：ERA5、LAI 和下载辅助步骤。
- `validation/`、`experiments/`：早期拟合、验证和显示实验。
- `archive/lsct_snapshot/`：主仓库整理前保存的 LSCT 快照和结果材料。

MSG 原生固定网格通常按完整研究区处理。若先裁剪再反演，应在脚本说明中明确写为
`study-area-first`。
