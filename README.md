# QXU6028 G24 — Virtual Lab

本仓库保存常规 L1/L2/L3、盲测 L1/L2/L3 的原始输入、分析代码、图表和结果，以及用户确认已上传 QMplus 的三个 ZIP。
2026-10-28 的整理更新仅核对和上传已有结果。2026-10-29 用户另行授权完整复现；新运行与原始提交分别记录，不覆盖历史结果。

## 2026-10-29 完整复现已通过

从 GitHub 新克隆源版本 [58eb990](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/commit/58eb990c11c72b8a4e8584c8d9ea2def72337d54)，成功执行 `python reproduce.py --dataset all`。常规176项、盲测168项数值及所有科学标签/判定均与原归档一致；两套数据各完成200次L2重采样和500次L3噪声重建。另自动生成报告五组组合图，12项测试通过。

记录见 [完整复现说明及日志](validation/reproduction_2026-10-29/README.md) 和 [机器核对报告](validation/reproduction_2026-10-29/reproduction_audit.json)。中途实际出现的L3 PNG截断失败及修复证据也保留在该目录。原始盲测三文件、提交包与根目录历史结果不变；新结果记录真实源提交号，位于核验目录的 `regular/results.json`、`blind/results.json`。

这次运行验证当前代码的可复现性，不倒填九月份的冻结时间或未恢复的历史Git对象。


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

截图本身没有打印时区；用户于2026-10-29明确说明截图为英国当地时间、操作时间按新加坡（UTC+8）记录。原显示文字保留不变，并在下表增加换算，不据此推断评分处罚。截图已提供平台提交时间证据；代码版本的核验另行记录。

### 用户补充的操作时间线

2026-10-29，Jin Zhengyang补充说明：

| 事件 | 新加坡时间（UTC+8） | 英国当地时间（当日BST，UTC+1） |
| --- | --- | --- |
| 完成全部常规L1、L2、L3代码及运行图（用户说明） | 11:15 | 04:15 |
| 进行盲测（用户说明） | 11:15—12:10 | 04:15—05:10 |
| QMplus显示的截止时间 | 16:00 | 09:00 |
| QMplus显示的最后修改/提交时间 | 17:42 | 10:42 |

以上日期沿用截图和原日志关联的2026-09-24；用户此次明确的是两组时间的时区。当天英国实行夏令时，新加坡比英国快7小时，[英国政府时钟变更表](https://www.gov.uk/when-do-the-clocks-change)列明2026年夏令时从3月29日持续到10月25日。盲测操作时段为55分钟；12:10计算完成与17:42的平台提交是不同事件，不能将计算结束时间直接写成平台提交时间。平台显示的迟交1小时42分保持不变。来源、原话与换算结果见 [用户时间说明](evidence/user_reported_timeline.json) 和 [平台时间记录](evidence/blind_receipt.json)。这项补充不独立证明历史代码版本。

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

完整 `--dataset all` 还自动调用 `g24lab/report_figures.py`，在 `generated/shared/report_figures/` 生成英文初稿使用的五组组合图，分别保存 PNG 和 SVG：L1 两种计数及 C；L2 联合拟合、分通道叠图和残差；有重采样区间的 EF 轨迹；常规/盲测地图；L3 正则化、PSF 和噪声验证。组合图使用这次新算出的 CSV/JSON，不读取旧的 `recorded/` 表或其他工作目录。

完整运行后核对所有科学结果字段、源代码/输出哈希及五组图：

```bash
python verify_reproduction.py --output-root generated/shared
```

核查报告写入 `generated/shared/reproduction_audit.json`。`pipeline_commit` 是唯一允许与原始结果不同的字段，因为新运行必须记录这次真实使用的代码版本；其余数值、标签和轨迹均比较，数值容差为相对 `1e-10`、绝对 `1e-12`。

代码与配置须先提交，运行时自动记录实际 HEAD。当前实现会生成新的日志、图表和结果；归档结果仍保留当时哈希，新运行不能冒充历史盲测。

`pipeline_config.json` 记录模式和种子。默认 refined 模式在完整 0.50–8.00 kBT 区间搜索后自动细化，不按常规/盲测设置不同固定窗口；bootstrap 使用该全域库。书面课程的 0.25 kBT 网格可用：

```bash
python reproduce.py --dataset all --gap-mode course --output-dir generated/course_grid
```

数值测试和本次已验证的旧代码反例：

```bash
python -m unittest discover -s tests -v
python -m tests.negative_controls
```

2026-10-29 在已提交源版本58eb990上通过12项测试（10项数值检查、2项PNG完整性回归）。此前的旧代码反例仍保存在 `validation/negative_controls.json`；本次失败/修复和成功运行分别记录在 `validation/reproduction_2026-10-29/`，使用范围见 `docs/AI_USAGE.md` 和 `docs/AI_ERROR_LEDGER.md`。

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
