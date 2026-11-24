# AI Usage for Report Figures and Full Reproduction (29 October 2026)

- **Tool:** ChatGPT Work / OpenAI Codex; Python 3.12.14, NumPy, pandas, Matplotlib, Pillow and Git.
- **Review.** I’m Jin Zhengyang. I used Codex to run and verify the following reproduction steps.

## Reproduction steps and checks

1. Cloned our public GitHub repository at `73c4640` into an empty directory and ran both regular and blind L1–L3 pipelines with pinned dependencies (200 L2 paired resamples and 500 L3 noise reconstructions per dataset).
2. Added `g24lab/report_figures.py` at `05a4352` so all five composite report figures are regenerated directly by `python reproduce.py --dataset all` from raw data and newly computed outputs.
3. Detected a truncated `L3_method.png` output at `05a4352` via our PNG integrity check and archived the original failure logs and hash.
4. Added in-memory PNG decode verification, atomic file replacement and two regression tests at `58eb990`.
5. Cloned `58eb990` into a fresh directory and ran `python reproduce.py --dataset all`, `python verify_reproduction.py --output-root generated/shared` and the 12-test suite. All checks passed.
6. Verified 176 regular and 168 blind numeric entries (relative tolerance 1e-10, absolute tolerance 1e-12), all scientific labels/decisions, row-major maps, 58/50 trajectories, bootstrap intervals, 29 PNGs and all five report figure groups. Only `pipeline_commit` differed as expected to record the actual source commit.
7. Published the replay evidence separately without altering original submission archives.

## Scope and limits

These updates resolved figure-pipeline coverage (E03) and PNG output integrity (E04) without changing any scientific result. They are documented as reproducibility fixes rather than additional physics-model errors and do not retroactively recover the missing September Git object `51814957`.

Evidence: [run summary](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/reproduction_2026-10-29/README.md), [machine comparison](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/reproduction_2026-10-29/reproduction_audit.json), [failed PNG record](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/reproduction_2026-10-29/failed_run_05a4352/failure.json), [tests](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/reproduction_2026-10-29/regression_tests_stdout.txt).
