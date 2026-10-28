# QXU6028 G24 — Virtual Lab

本仓库保存常规 L1/L2/L3、盲测 L1/L2/L3 的原始输入、分析代码、图表和结果，以及用户确认已上传 QMplus 的三个 ZIP。
2026-10-28 本次更新仅整理、核对和上传已有结果，没有重新运行六项数值计算。

## 结果与实际提交文件

| 路径 | 内容与来源 |
| --- | --- |
| `results.json` | 完整常规结果；与 `L3/recorded/results.json` 字节一致。L1、L2 字段分别与本次提交的检查点一致 |
| `blind_results.json` | 本次 `G24_Blind_Submission.zip` 内的原始盲测结果，字节不变 |
| `submissions/blind/` | 从上述实际盲测 ZIP 原样提取的 `blind_results.json`、`run_log.txt`、`pipeline_commit.txt` |
| `evidence/submitted_archives/` | `G24_L1_4figures.zip`、`G24_L2_Checkpoint.zip`、`G24_Blind_Submission.zip`，均为用户确认的 QMplus 提交包 |
| `evidence/submission_screenshots/` | L1、L2 和本次补充的盲测提交状态截图 |
| `evidence/INDEX.json` | 原始 ZIP、截图的字节数与 SHA-256；盲测提交时间的原样转录 |
| `validation/archive_verification.json` | 不重跑分析的文件、JSON结构、原始数据和提交包一致性检查 |

根目录的结果是**已有完整结果的归档副本**。它们保留原 `pipeline_commit`，没有将当前仓库的新增提交冒填为当时计算版本。常规 L1/L2 检查点中后续阶段的 null 是当时阶段快照；根目录 `results.json` 已包含完整 L1、L2、L3。

## L1 的四张图

实际提交的 `G24_L1_4figures.zip` 已包含：

- 正式修正因子图 `L1_factor_sweep.png`；
- 四张补充图：`L1_electron_population.png`、`L1_hole_population.png`、`L1_hall_coefficient.png`、`L1_sheet_resistance.png`。

因此是 **1 张正式图 + 4 张补充图，共 5 张 PNG**。提交包与 `L1/recorded/` 内的图逐字节一致，没有缺少另一套“四张旧图”。补充图的原说明使用 L2 的 hard-gap 模型（Eg/kBT=2.073），不替代 L1 的修正因子图。

## 盲测提交时间

用户提供的 QMplus “Blind test L3” 截图显示：

| 项目 | 截图原文信息 |
| --- | --- |
| Attempt / Status | Attempt 1 / Submitted for grading |
| Grading | Not graded |
| Due | Thursday, 24 September 2026, 9:00 AM |
| Last modified | Thursday, 24 September 2026, 10:42 AM |
| Time remaining | Assignment was submitted 1 hour 42 mins late |
| File | G24_Blind_Submission.zip |

截图没有显示时区，以上时间按平台原显示保存，不自行换算，也不据此推断评分处罚。截图现已补齐提交时间证据；它与计算代码的冻结 Git 对象是不同的证据。

盲测提交包内还包含 `G24_L3_Working_Pack.zip`；其中的 `preview_outputs/` 是工作包预览，不用来替换根目录完整常规结果或正式盲测结果。

## 六个实验目录与当前代码

六目录 `L1/`、`L2/`、`L3/`、`blind_L1/`、`blind_L2/`、`blind_L3/` 中：`data/` 保存未修改的原始数据；`code/` 保存历史脚本；`recorded/` 保存已有输出。原整理来源与哈希仍见 `PROVENANCE.json`。

`g24lab/` 与更新后的 `reproduce.py` 是当前共享实现：两套数据使用相同的全域带隙搜索和选模代码；修复了旧细化脚本的窄窗口和缺少正常 cone 返回分支。旧脚本与原始输出保留不变。

## 验证已有材料，无需重跑数值计算

推荐 Python 3.12；依赖见 `requirements.txt`。从 GitHub 克隆后运行：

```bash
python -m pip install -r requirements.txt
python reproduce.py --verify-only
```

该命令只检查原始数据哈希、三个 ZIP、截图哈希、完整 JSON、58/50 点 EF 轨迹、100 点零均值地图和提交包的一致性，不拟合、不重建、不重新绘图，不修改原结果。

## 需要时重新计算

```bash
python reproduce.py --dataset all
```

也可选择 `--dataset regular` 或 `--dataset blind`，或通过 `--data-dir` 指向一套完整 G24 输入。新输出写入 `generated/shared/regular/` 和 `generated/shared/blind/`，不会覆盖提交包、根结果或历史 `recorded/`。重复运行用新的 `--output-dir`。

代码与配置须先提交，运行时自动记录实际 HEAD。当前实现会生成新的日志、图表和结果；本次没有执行这项完整运行，不能把归档结果描述为本次新版管线生成。

`pipeline_config.json` 记录模式和种子。默认 refined 模式在完整 0.50–8.00 kBT 区间搜索后自动细化，不按常规/盲测设置不同固定窗口；bootstrap 使用该全域库。书面课程的 0.25 kBT 网格可用：

```bash
python reproduce.py --dataset all --gap-mode course --output-dir generated/course_grid
```

数值测试和本次已验证的旧代码反例：

```bash
python -m unittest discover -s tests -v
python -m tests.negative_controls
```

此前已通过10项数值测试；反例结果保存在 `validation/negative_controls.json`，人工记录范围见 `docs/AI_USAGE.md` 和 `docs/AI_ERROR_LEDGER.md`。

## AI 使用记录与检查人

**Checked by: Jin Zhengyang.** 检查人姓名由用户于2026-10-28明确提供；不据此倒填原始检查时间。

当前完整日志见 [docs/AI_USAGE.md](docs/AI_USAGE.md)，分别覆盖 [L1](docs/ai_usage/L1.md)、[L2](docs/ai_usage/L2.md)、[L3](docs/ai_usage/L3.md)、[盲测](docs/ai_usage/BLIND.md) 和 [仓库整理](docs/ai_usage/REPOSITORY.md) 的工具、用途、指令摘要、采用/修改内容及检查证据。

L3和盲测日志依据已保留文件事后整理，未冒充找回的逐字历史提示词。原始L1/L2日志保持原字节；旧L1快照中的检查人占位文字已由当前补充日志中的Jin Zhengyang取代，不再作为待填写的当前信息。

## 已有结果摘要

| 项目 | 常规 | Blind |
| --- | ---: | ---: |
| L1 correction factor | 3.5852776731 | 3.1581735677 |
| L2 model | hard_gap | hard_gap |
| L2 Eg/kBT | 2.0730 | 3.5306 |
| L2 EF 点数 | 58 | 50 |
| L3 map 点数 | 100 | 100 |
| L3 decision | clear fail | clear pass |

## 原始版本记录

用户已确认：**这是其第一个GitHub仓库，2026-10-28之前没有创建过GitHub仓库。** 当前GitHub仓库的真实历史从2026-10-28的初始化与导入开始。此前ZIP内携带的是本地Git对象，不能据此推定用户以前建立过GitHub仓库，也不据此认定谁亲自完成了这些本地提交。

`history/original_L1_L2.bundle` 保存4条可恢复的真实 L1/L2 提交；`python restore_history.py` 可在本地恢复 `archive/original-L1-L2` 分支。原 L1 提交包记录的 `432170af...` 和完整常规/盲测记录的 `51814957...` 目前只有原始哈希文本，没有在已提供材料中找到相应 Git 提交对象。这是版本证据的边界，**不表示 L1 的四张图缺失**。本次不改写旧哈希或提交日期。

按用户本次指定范围，本次仓库更新不上传正式报告、签字贡献声明或自评；也没有更改 QMplus 上的既有提交。
