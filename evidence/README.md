# QMplus 提交材料与时间证据

[盲测提交文件](../submissions/blind/README.md) 提供手册所列的三个独立文件及其 SHA-256 值，可直接与原始 ZIP 和回执核对。

我核对了本组在 QMplus 提交的三份 ZIP，`submitted_archives/` 保存提交时的原始文件。

| 文件 | 核对结果 |
| --- | --- |
| `G24_L1_4figures.zip` | 含阶段结果、修正因子图、四张补充图、说明和原提交哈希；所有成员与 L1/recorded 一致 |
| `G24_L2_Checkpoint.zip` | 含阶段结果、模型图、EF轨迹图、带隙残差扫描和说明；所有文件与 L2/recorded 一致 |
| `G24_Blind_Submission.zip` | 含正式盲测三文件及一个 L3 工作包；三文件与现有三个 blind/recorded 目录一致 |

我在 2026-11-10 核对了常规 L3 与盲测在 QMplus 同包提交的记录。归档 ZIP 内的 `G24_L3_Working_Pack.zip` 包含常规数据、代码及预览结果和图表。预览检查点记录的是占位符 `PENDING_LOCAL_L3_COMMIT`。[期末证据记录](../validation/final_2026-11-10/README.md)

同日收到的 L2 检查点 ZIP 与本目录归档逐字节一致，且其 `commit_hash.txt` 对应 `history/original_L1_L2.bundle` 内可恢复的 `3afb63d` 提交。

`INDEX.json` 保存上述 ZIP 和四张截图的 SHA-256、字节数与来源。截图为原文件副本。

| 截图 | 显示内容 |
| --- | --- |
| `L1_submission_status.png` | Submitted for grading；23 September 2026, 8:37 AM；G24_L1_4figures.zip |
| `L2_submission_status_1.png` / `L2_submission_status_2.png` | 同一次L2提交；Submitted for grading；23 September 2026, 9:28 AM；G24_L2_Checkpoint.zip |
| `blind_submission_status.png` | Blind test L3；Attempt 1；Submitted for grading；Not graded；24 September 2026, 10:42 AM；G24_Blind_Submission.zip |

盲测截图显示截止时间为 2026-09-24 09:00，平台标记迟交 1 小时 42 分钟。截图未显示时区。我在 2026-10-29 补充说明，截图使用英国当地时间，当天为 BST（UTC+1）。换算为新加坡时间，截止为 16:00，最后修改时间为 17:42。[平台原文与时间换算](blind_receipt.json)

我用截图核对了提交文件名、状态和显示时间。文件哈希来自我保留的归档副本。可恢复的 Git 对象见[原始版本记录](../history/README.md)。

## 我记录的代码就绪与盲测时间

我在 2026-10-29 补充记录了这段时间线。常规 L1–L3 代码和运行图于 11:15 就绪，我在 11:15—12:10 进行盲测分析，共 55 分钟。原话和换算见[我的操作时间线](blind_work_timeline.json)，该文件的哈希见 [INDEX.json](INDEX.json)。

我按新加坡时区记录操作时间，按英国当地时区读取 QMplus 截图。换算日期 2026-09-24 取自截图和原始运行日志。

| 事件 | 新加坡（UTC+8） | 英国（当日BST，UTC+1） |
| --- | --- | --- |
| 常规代码和运行图就绪 | 11:15 | 04:15 |
| 我进行盲测分析 | 11:15—12:10 | 04:15—05:10 |
| 平台截止 | 16:00 | 09:00 |
| 平台显示的最后修改时间 | 17:42 | 10:42 |

我记录的盲测结束时间与平台显示的最后修改时间相隔 5 小时 32 分钟。我用 Python `zoneinfo` 换算时间，并核对了英国夏令时的实施日期。[GOV.UK](https://www.gov.uk/when-do-the-clocks-change)
