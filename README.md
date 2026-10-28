# QXU6028 G24 — Virtual Lab

G24 小组常规 L1 / L2 / L3 与 blind L1 / L2 / L3 的代码、原始数据和历史结果。
本次整理日期：2026-10-28。建议使用私有仓库，并单独给组员和教师授权。

## 六个实验目录

| 目录 | 内容 | 历史结果来源 |
| --- | --- | --- |
| `L1` | 载流子计数、修正因子及补充四图脚本 | `G24_L1_Checkpoint_with_4_figures.zip` |
| `L2` | RH / Rs 联合拟合与细化带隙搜索 | `G24_L2_Checkpoint_complete.zip` |
| `L3` | 零均值重建、分辨率和检测限 | `G24_L3_Checkpoint.zip` |
| `blind_L1` | 盲测 L1 代码、数据、图表和验证记录 | `G24_Blind_L1_L2_L3_Complete(1).zip` |
| `blind_L2` | 盲测 L2 代码、数据、图表和验证记录 | 同一盲测完整包 |
| `blind_L3` | 盲测 L3 代码、数据、图表和验证记录 | 同一盲测完整包 |

每个目录的 `code/` 是恢复的原脚本，`data/` 是未经修改的原始输入，
`recorded/` 是已保存的历史输出。`PROVENANCE.json` 记录复制来源与 SHA-256。

盲测原本是一次 L1/L2/L3 联合运行，而不是三个独立提交包。因此，三个 blind
目录各保留一份完全相同的完整 `blind_results.json`、`run_log.txt` 和
`pipeline_commit.txt`；请分别查看对应的 L1、L2、L3 字段。
常规 L1/L2 的 JSON 则是当时的阶段快照，后续未完成阶段的 null 是原文件内容。

## 运行

推荐 Python 3.11 或 3.12，并安装 Git。先创建并提交仓库代码，再运行：

```bash
python -m pip install -r requirements.txt
python reproduce.py --dataset regular
python reproduce.py --dataset blind
```

一次运行六项：

```bash
python reproduce.py --dataset all
```

输出在 `generated/regular/` 和 `generated/blind/`，不会覆盖 `recorded/`。
脚本会先按原 manifest 核对输入，再依次执行 L1、L2、L3，并生成真实终端日志。
盲测的空白 `blind_results.json` 仅在临时输入目录复制为脚本需要的模板文件名，
不会修改原始数据。未处于已提交的 Git 仓库时，重跑结果会明确标为
`PENDING_ARCHIVAL_REPLAY`，不能把该占位符当作正式提交哈希。

## 历史结果与方法边界

| 项目 | 常规 | Blind |
| --- | ---: | ---: |
| L1 correction factor | 3.5852776731 | 3.1581735677 |
| L2 Eg/kBT（历史细化版本） | 2.0730 | 3.5306 |
| L2 EF 点数 | 58 | 50 |
| L3 map 点数 | 100 | 100 |

这里保留的是先前聊天中按“调整带隙降低残差”要求制作的细化版本。
课程指南的原始 L2 搜索步长是 0.25 kBT；`analysis_L2.py` 保留了该基础实现，
`analysis_L2_optimized.py` 则是历史细化版本。本次整理不修改或重新判定历史结果。

**请注意可复现性边界：**恢复出的常规和 blind 细化 L2 脚本具有不同的固定搜索窗口；
blind L3 脚本也放宽了数据集标识检查。本次新增的 `reproduce.py` 只是组织这些已有脚本的
重跑入口，不能据此证明它们在历史盲测前已是同一个冻结管线。需要正式证明冻结流程时，
应核对原始本地 Git 历史和课程要求，不能用新仓库提交替换旧哈希。

`recorded/` 中的 commit 值原样保留；新运行只记录实际新仓库的 HEAD。
本次仓库导入不会恢复原来的 Git 历史，也不会虚构小组成员贡献。

## 小组协作

仓库拥有者可在 GitHub 的 Settings → Collaborators 中邀请经确认的组员账号。
不要把密码、访问令牌、`.env` 或其他私人文件加入仓库。此整理未添加公开许可证，
也未向组员发送邀请；课程提供的数据和材料不据此获得公开再分发许可。
