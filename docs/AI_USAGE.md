# AI 使用记录：仓库整理与续传

日期：2026-10-28。工具：ChatGPT Work / OpenAI Codex。
原始 `AI_usage_log_L1_original.txt`、`AI_usage_log_L2_original.txt` 保持不变。

用户先要求延续“分支 · 阅读作业要求”聊天中的GitHub工作。之后明确：无需再次重跑所有代码；补充盲测提交时间截图及实际提交的三个ZIP；更新根目录reproduce.py、README并上传results.json；正式报告、签字贡献声明和自评不在本次上传范围。

## 本次采用的处理

- 核对本次附件的三个ZIP，保存原字节、文件清单和SHA-256；保存盲测提交截图及原显示时间。
- 确认L1包已有一张修正因子图和四张补充图，修正“缺少旧四图”的误解。
- 将现有完整常规 `L3/recorded/results.json` 原样发布到根目录；其L1、L2字段与本次检查点一致。
- 从实际盲测ZIP原样提取三文件；根 `blind_results.json` 与提交包一致。未替换原始pipeline_commit。
- 合入此前准备的共享分析模块、配置、测试，接入新版reproduce.py；新增 `--verify-only`，只做已有材料一致性核验。
- 此前已运行10项数值测试，全部通过；两个旧程序失败反例实际触发，结果见 `validation/negative_controls.json`。模拟cone对照清楚标为synthetic，没有混入原始测量。
- 本次只运行语法、帮助入口及只读归档核验，未执行六项完整拟合、重建或绘图，未生成冒充旧盲测的新日志。
- 保存包含4条真实旧L1/L2提交的Git bundle和本地恢复工具；未虚构其余历史对象。

完整归档核验结果见 `validation/archive_verification.json`。本记录描述AI实际操作，不代填学生检查人、学生贡献、签字或个人自评，也没有改动QMplus的原提交。
