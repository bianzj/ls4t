# LS4T 工作区与工作树

## 当前入口

`/home/hero/work/ls4t` 是唯一的当前主工作目录，使用 `bianzj` 分支。新的公共算法、
产品实现、测试和文档都进入这里。当前代码入口是扁平化的 `src/`：

- `src/aatsr/`：AATSR 数据、投影、研究区、LST 和 LSCT；
- `src/slstr/`：SLSTR 解压、提取、重建、投影、合并、研究区、LST 和 LSCT；
- `src/msg/`：MSG 数据、投影、研究区、LST 和 LSCT；
- `src/base/`：跨传感器公共产品、质量控制、读写和空间算法；
- `src/normalization/`：角度、时间、空间和传感器归一化。

根目录下的 `aatsr_lst/`、`slstr_lst/`、`msg_lst/`、`cases/`、`base/` 和 `old/`
属于兼容、实验或迁移材料，不作为新公共代码入口。

## `/home/hero/work` 中的目录

| 目录 | 分支 | 定位 | 处理原则 |
| --- | --- | --- | --- |
| `ls4t` | `bianzj` | 当前主仓库 | 日常开发和最终发布 |
| `ls4t-aatsr-lsct` | `atsr-lsct` | AATSR 历史算法与 0.01° 统计运行脚本 | 保留运行参数；通用改进移入 `src/aatsr/` |
| `ls4t-msg-lsct` | `msg-lsct` | MSG LSCT 实验、验证和月合成脚本 | 保留实验配置；稳定算法移入 `src/msg/` |
| `ls4t-slstr-lsct` | `slstr-lsct` | SLSTR 区域处理和旧逐景流程 | 保留区域参数；稳定算法移入 `src/slstr/` |

后三个目录由 `git worktree` 管理，共享 `/home/hero/work/ls4t/.git` 的对象和分支，
不能当作普通重复目录直接复制或删除。

## 两类代码的归属

1. 可复用产品代码放在主仓库 `src/<sensor>/`，函数参数优先使用 `None`，文件顶部保留
   可手工修改的默认参数。数据、LST、LSCT 继续分阶段运行。
2. 与数据盘路径、年份、研究区或一次运行紧密绑定的脚本留在对应传感器工作树，或在
   主仓库的 `cases/` 中作为明确命名的案例保存。
3. 两种空间模式都保留：先拼接/裁剪研究区再反演，以及逐景反演后再拼接/裁剪。
4. HDF5、GeoTIFF、日志、临时文件和 Python/Numba 缓存不进入 Git；结果放在数据盘。
5. 从工作树向主仓库迁移时只移入通用逻辑，不把本机绝对路径和单次实验参数带进
   `src/`。

## 当前保留项

- AATSR 工作树中的 `aatsr_001deg_stats.py` 和 `aatsr_monthly_3files.py` 是有效运行脚本，
  在确认通用接口之前保留在原位置。
- MSG 工作树保存较新的 LSCT 实验与验证脚本；其中生成图、日志、`__MACOSX`、
  `.DS_Store` 和 `__pycache__` 不作为源码迁移。
- SLSTR 工作树的分支差异主要是区域数据路径、年份和逐景运行参数，暂不覆盖主仓库的
  通用实现。
- 各工作树现有未提交内容均视为在用材料，整理时不得用 `reset --hard` 或强制清理。

## 日常检查

在主工作目录运行：

```bash
git worktree list
git status --short --branch
git -C /home/hero/work/ls4t-aatsr-lsct status --short --branch
git -C /home/hero/work/ls4t-msg-lsct status --short --branch
git -C /home/hero/work/ls4t-slstr-lsct status --short --branch
```

删除某个工作树前，必须先确认其分支已保存、未提交文件已归档，并确认没有 systemd
服务或 Python 进程引用该路径。
