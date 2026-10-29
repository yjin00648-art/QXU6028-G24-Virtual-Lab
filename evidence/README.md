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

盲测截图同时显示截止为24 September 2026, 9:00 AM，平台标记迟交1小时42分。截图未打印时区；用户后续明确这是英国当地时间。按Europe/London在2026-09-24的BST（UTC+1）换算，截止为新加坡16:00，最后修改/提交为新加坡17:42。`blind_receipt.json` 保留平台原文，并注明用户提供的时区解释及换算，不推断任何迟交处罚。

用户确认提交包身份，截图支持文件名、状态与显示时间；截图本身不包含平台文件的加密哈希，也不补造缺失的历史Git对象。原始结果和日志保持不变。

## 用户补充的代码就绪与盲测时间

2026-10-29，Jin Zhengyang说明全部常规L1、L2、L3代码和运行图于11:15完成，盲测操作时段为11:15—12:10，按同一日同一时钟计算为55分钟。原话与结构化记录保存在 [user_reported_timeline.json](user_reported_timeline.json)，其文件哈希单独列在INDEX.json的supplementary_user_statements中。

用户随后明确：“截图时间为UK时间，真实时间你可以认为是新加坡（UTC+8）时间”。操作时间据此使用Asia/Singapore，平台时间使用Europe/London；关联日期取自截图和原日志的2026-09-24，不将该日期表述为用户另行重述过的事实。

| 事件 | 新加坡（UTC+8） | 英国（当日BST，UTC+1） |
| --- | --- | --- |
| 常规代码和运行图完成（用户说明） | 11:15 | 04:15 |
| 盲测操作（用户说明） | 11:15—12:10 | 04:15—05:10 |
| 平台截止 | 16:00 | 09:00 |
| 平台最后修改/提交 | 17:42 | 10:42 |

操作时段55分钟；用户说明的盲测结束与平台提交相隔5小时32分。这里只区分计算和提交事件，不推断间隔原因。英国夏令时日期由 [GOV.UK](https://www.gov.uk/when-do-the-clocks-change)核对，换算使用Python zoneinfo。该时间补充不新增历史Git对象，也未改写原始盲测结果、运行日志或哈希。
