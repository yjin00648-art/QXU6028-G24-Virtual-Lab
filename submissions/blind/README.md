# G24 blind test submission files

I checked the three files listed in the Practical Methods Guide against our original QMplus ZIP. Each file below uses its submitted name and matches its corresponding ZIP member byte for byte.

| File | Contents | SHA-256 |
| --- | --- | --- |
| [blind_results.json](blind_results.json) | Original G24 blind L1–L3 results | `c968b19d8eb48053f1d7395645892a485d495a5b7ad9a6ffdff8a4c653b2016f` |
| [run_log.txt](run_log.txt) | Original run log supplied for the blind test | `e822b1c33aa4fb801385b1979d115826f3272c954a42fe5a9787bd7b8fb8c289` |
| [pipeline_commit.txt](pipeline_commit.txt) | Commit identifier recorded in the blind submission | `86a19db322e8677a248176f2f195d3c7dc29557ffb9c4ca172da34fafd84b169` |

## QMplus receipt for 24 September 2026

Attempt 1 shows `G24_Blind_Submission.zip` with the status “Submitted for grading”. The ZIP contains the three blind files and the regular `G24_L3_Working_Pack.zip`.

| Receipt field | UK time (BST) | Singapore time (UTC+8) |
| --- | --- | --- |
| Deadline | 09:00 | 16:00 |
| Last modified | 10:42 | 17:42 |

QMplus displayed “Assignment was submitted 1 hour 42 mins late”. In my timeline I use UK local time for the QMplus display and Singapore time for my work on the blind analysis.

[Original QMplus ZIP](../../evidence/submitted_archives/G24_Blind_Submission.zip) · [Receipt screenshot](../../evidence/submission_screenshots/blind_submission_status.png) · [Receipt transcription](../../evidence/blind_receipt.json) · [My work timeline and time zones](../../evidence/blind_work_timeline.json)

## Recorded analysis version

The original `pipeline_commit.txt` records `51814957ddcb8d34d4153c386cf2194f7be0b541`. The Git object for this commit is unavailable in the retained history. The 10 November 2026 clean-checkout replay verified the blind scientific results and records its generating commit in the audit. [Retained Git history](../../history/README.md) · [Replay audit](../../validation/final_2026-11-10/reproduction_audit.json)
