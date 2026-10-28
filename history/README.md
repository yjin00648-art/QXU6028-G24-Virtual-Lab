# 可恢复的原始Git历史

`original_L1_L2.bundle` 来自此前提供的原始项目Git对象，包含4条真实提交：

| Commit | 原日期 | 信息 |
| --- | --- | --- |
| 4b1f9571983f34b5fe8ebdb6354db7846fe2ebc1 | 2026-09-21T12:09:04+08:00 | Complete G24 L1 analysis pipeline |
| 483eab1a833315fe1a86205ac039163ded88b404 | 2026-09-21T12:11:48+08:00 | Add G24 L1 checkpoint outputs |
| d6f89925f41692f6b68abbb19d62bc9d42ad7a81 | 2026-09-23T14:27:07+08:00 | Add G24 L2 analysis pipeline |
| 3afb63d39d2dd5ee359141756d59bd0daa100684 | 2026-09-23T14:59:01+08:00 | Refine G24 L2 hard-gap fit |

克隆后运行 `python restore_history.py`，在本地恢复 `archive/original-L1-L2`。工具不覆盖main、不改提交日期、不自动推送。保存bundle不等于GitHub的main拥有全部原始开发历史。

L1实际提交包记录 `432170af5121d17e8b3616488b84b6491e6d233a`；完整常规及盲测结果记录 `51814957ddcb8d34d4153c386cf2194f7be0b541`。现有材料未包含这两个Git对象，因此仅保留原始哈希，不重建或倒填。

L1提交ZIP的五张图均已提供并核对一致，Git对象缺失不表示图文件缺失。新盲测截图可证明平台显示的提交状态与时间，但不能替代代码版本对象。
