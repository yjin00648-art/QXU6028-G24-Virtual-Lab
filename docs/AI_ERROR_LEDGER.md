# AI 错误与修正台账

2026-10-28复核中实际发现的缺陷。原程序保留在 `L2/code/`；反例原始结果见 `validation/negative_controls.json`。以下记录不冒充九月份已形成的历史错误台账。

## E01：为未知带隙固定常规数据专用窗口

- 原实现：`L2/code/analysis_L2_optimized.py` 使用1.90–2.20 kBT的固定细化窗口。
- 发现依据：输入未经修改的G24盲测L2数据，触发 `AssertionError: Preliminary gap optimum lies on the search boundary.`。
- 原因：待反演参数不应事先被限定在常规数据的窄窗口，课程允许域为0.50–8.00 kBT。
- 修正：`g24lab/l2.py` 对两套数据使用同一全域搜索，再按计算所得最优点自动细化；bootstrap使用全域库。
- 验证：保存的反例结果返回hard_gap、Eg/kBT=3.5306；此前Eg/kBT=6.0的明确模拟对照也通过数值测试。

## E02：细化程序没有合法cone返回路径

- 原实现：同一旧程序主要输出hard_gap，不满足条件时抛出异常，没有正常的cone输出分支。
- 发现依据：课程cone正向模型生成的无噪声模拟对照触发旧程序异常，未返回已知cone真值。该数据明确标为synthetic，仅用于验证。
- 修正：严格执行 r_gap < 0.85*r_cone 且 Eg/kBT≥1，否则返回cone、Eg=0；bootstrap同样执行选模规则。
- 验证：修复后该对照返回cone、Eg/kBT=0、RMS约5.45e-16；0.85边界和最小带隙门槛测试通过。

E01、E02是两条真实复现的物理模型相关实现缺陷。它们不等同于凭空补写的历史单位或符号概念错误；模拟对照不充当本组实验数据。

## 其他整理问题

- 旧一键流程未完整接入带隙扫描图。共享绘图代码已接入扫描、实测轨迹连线和双通道顺序图；本次未重新执行全套绘图，不能声称这些图已由本次运行生成。
- 用户本次L1包已有全部五张PNG，不能再称“四张图缺失”。缺少对应旧Git提交对象是另一项版本证据限制。
- 用户新提供的盲测截图已补充提交状态和显示时间；如实记录平台显示的迟交1小时42分，不将其改写为按时提交。


## E03: report panel groups were outside the one-command runner (29 October)

- Detection: the initial complete six-stage replay passed, but the five composite figures in the English report draft still depended on a separate drafting script and earlier local tables.
- Correction: commit 05a4352 adds g24lab/report_figures.py and calls it at the end of the all-dataset command. It reads the newly computed CSV/JSON and untouched inputs, with no private workspace path or archived numerical table.
- Verification: the final clean-clone run generated all five PNG/SVG figure groups, validated their numerical sources, and matched the inspected draft panels. Figure 2 uses the newly computed global residual scan.
- Classification: reproducibility coverage, not an additional physics-concept error.

## E04: incomplete PNG in a fresh-clone replay (29 October)

- Observed at commit 05a4352: regular L3_method.png was 196764 bytes and stopped before the third IDAT checksum. The pipeline correctly stopped with an integrity error. The retained file matches the prefix of the initial complete 392530-byte image.
- Evidence: [failed stdout](../validation/reproduction_2026-10-29/failed_run_05a4352/full_replay_stdout.txt) and [failure metadata](../validation/reproduction_2026-10-29/failed_run_05a4352/failure.json).
- Correction at 58eb990: render PNG bytes in memory; validate and decode them; write, flush and read back a temporary file; atomically replace the final path. The final PNG integrity gate remains active.
- Verification: a large-image decode test passes; truncated bytes are rejected while a previous valid image remains intact. All 12 tests and the final fresh-clone six-stage command pass. Original inputs and scientific results are unchanged.
- Limit: the incomplete file is observed; its underlying rendering/filesystem cause is not independently established. This is an output-integrity issue, not an additional physics error.

The earlier note that full plotting had not been run describes the 28 October scope. It is superseded for the current code by [the successful 29 October reproduction](../validation/reproduction_2026-10-29/README.md). The missing September source object and the evidential limit on two independent physics-concept errors remain unchanged.
