# QMplus 提交材料与时间证据

`submitted_archives/` 中三份 ZIP 是用户本次明确确认已上传 QMplus 的文件，按原字节归档：

| 文件 | 核对结果 |
| --- | --- |
| `G24_L1_4figures.zip` | 含阶段结果、修正因子图、四张补充图、说明和原提交哈希；所有成员与 L1/recorded 一致 |
| `G24_L2_Checkpoint.zip` | 含阶段结果、模型图、EF轨迹图、带隙残差扫描和说明；所有文件与 L2/recorded 一致 |
| `G24_Blind_Submission.zip` | 含正式盲测三文件及一个 L3 工作包；三文件与现有三个 blind/recorded 目录一致 |

L3 工作包中的 `preview_outputs/` 是预览，未用来覆盖正式完整结果。

`INDEX.json` 保存上述 ZIP 和四张截图的 SHA-256、字节数与来源。截图为原文件副本。

| 截图 | 显示内容 |
| --- | --- |
| `L1_submission_status.png` | Submitted for grading；23 September 2026, 8:37 AM；G24_L1_4figures.zip |
| `L2_submission_status_1.png` / `L2_submission_status_2.png` | 同一次L2提交；Submitted for grading；23 September 2026, 9:28 AM；G24_L2_Checkpoint.zip |
| `blind_submission_status.png` | Blind test L3；Attempt 1；Submitted for grading；Not graded；24 September 2026, 10:42 AM；G24_Blind_Submission.zip |

盲测截图同时显示截止为24 September 2026, 9:00 AM，平台标记迟交1小时42分。时区未显示，按平台原文保存。`blind_receipt.json` 是该截图的结构化转录，不推断任何迟交处罚。

用户确认提交包身份，截图支持文件名、状态与显示时间；截图本身不包含平台文件的加密哈希，也不补造缺失的历史Git对象。原始结果和日志保持不变。
