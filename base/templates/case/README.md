# {{CASE_ID}}

复制本目录后，至少填写：

- `case.toml`：研究区、时期、空间路线、阶段和算法版本；
- `machines/local.toml`：当前机器的数据路径；
- `stages/`：轨道分组、研究区拼接、LSCT 输入准备和验证等案例逻辑。

查看标准阶段：

```bash
python run_standard_stage.py --machine local --list
```

执行单个标准阶段：

```bash
python run_standard_stage.py unzip --machine local
python run_standard_stage.py extract --machine local
```

每次只运行一个阶段。模板不会自动串联整条流水线。
