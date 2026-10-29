# AI usage for report figures and full reproduction on 29 October 2026

- Tool: ChatGPT Work / OpenAI Codex; Python 3.12.14, NumPy, pandas, Matplotlib, Pillow, Git and the GitHub connector.
- Reviewer designated by the user: **Jin Zhengyang**. The executions below were automated; no extra human approval or signature is inferred.
- Authorisation: the user explicitly requested an additional repository run, repairs if it failed, and upload of the repaired work. This replaced the earlier instruction to avoid rerunning all stages.

## Work and actual checks

1. Cloned the current public GitHub repository at 73c4640 into an empty directory and confirmed the remote commit/tree and clean worktree. Both regular and blind L1/L2/L3 ran with the pinned dependencies, 200 L2 paired-resampling fits and 500 L3 noise reconstructions per dataset.
2. Compared every scientific result field with the preserved JSON. Added the draft's five composite figure groups to the runner at 05a4352, so their tables and figures are regenerated from raw inputs and the current numerical outputs rather than a separate local drafting step.
3. A fresh clone at 05a4352 failed the retained PNG gate because L3_method.png ended before an IDAT checksum. Kept its unedited logs and file hash. The observation establishes truncation, not a known library/filesystem root cause.
4. Added validated atomic PNG publication and two regression tests at 58eb990. The tests check a large PNG and rejection of truncated bytes without replacing a valid existing image.
5. Cloned 58eb990 from GitHub into a fresh directory. Ran `python reproduce.py --dataset all`, then `python verify_reproduction.py --output-root generated/shared` and the test suite. All passed. The worktree was clean before and after numerical execution.
6. Verified 176 regular and 168 blind numeric entries with relative tolerance 1e-10 and absolute tolerance 1e-12, plus exact model/decision/other scientific labels. Only pipeline_commit differs as expected. Checked the row-major maps, 58/50 trajectories, bootstrap intervals, source/output hashes, 29 PNGs and the five report figure groups. The five final report PNGs are pixel-identical to their visually inspected prepublication outputs.
7. Published new replay evidence separately from the unchanged original submissions. Updated README, AI records and the completeness checklist.

## Report drafting disclosure

The earlier English draft followed the supplied report Guidance and used AI for drafting, technical explanations, bibliography checks and plotting. Seven numbered Vancouver references were included, with primary-source metadata checked for the external scientific papers. The report remains a draft for group review and signatures. This repository operation does not publish that draft or invent members' contributions.

## Corrections and limits

The numerical results did not require manual correction. The changes address report-figure coverage and complete figure output. They do not count as two additional physics-concept errors or recover the historical frozen commit. The original blind run, this later numerical replay, automated checking and the user's reviewer attribution are recorded separately.

Evidence: [run summary](../../validation/reproduction_2026-10-29/README.md), [machine comparison](../../validation/reproduction_2026-10-29/reproduction_audit.json), [failed PNG record](../../validation/reproduction_2026-10-29/failed_run_05a4352/failure.json), [tests](../../validation/reproduction_2026-10-29/regression_tests_stdout.txt).
