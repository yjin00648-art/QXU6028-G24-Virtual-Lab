# AI Error and Correction Ledger (Group G24)

This ledger records genuine defects we identified during our post-session audit (28–29 October 2026) and final verification (10 November 2026) of AI-assisted scripts. The original legacy scripts are retained in `L2/code/` for transparency, and the negative-control outputs are stored in `validation/final_2026-11-10/negative_controls.json`. We do not present these later audit findings as September lab-session entries.

## E01: Hard-coded narrow gap-search window for unknown datasets (L2 physics-model error)

- **Original implementation:** The legacy script `L2/code/analysis_L2_optimized.py` restricted the refined gap search to a fixed window of 1.90–2.20 kBT tailored to the regular G24 dataset.
- **Detection evidence:** Running the unmodified G24 blind L2 dataset through the legacy script triggered `AssertionError: Preliminary gap optimum lies on the search boundary.` Physically, constraining the unknown bandgap to a dataset-specific window truncates wider thermal gaps at the search boundary and prevents valid parameter inversion.
- **Correction:** In `g24lab/l2.py`, we replaced the fixed window with a shared global search across the full prescribed domain (0.50–8.00 kBT) for both regular and blind datasets. The final regular result uses the prescribed 0.25 kBT grid. Refined mode adds a local search around the global optimum for the blind replay and checkpoint comparison. The 200-replicate bootstrap uses the full domain library.
- **Verification:** On the G24 blind dataset, the corrected pipeline recovers `hard_gap` with Eg/kBT = 3.5306 without boundary truncation; an additional synthetic control at Eg/kBT = 6.0 also passed numerical checks.

## E02: Missing valid gapless-cone return path when the 15% selection rule fails (L2 physics-model error)

- **Original implementation:** The same legacy L2 script assumed a gapped solution and raised an exception whenever the hard-gap model failed the 15% RMS reduction criterion, instead of returning the gapless cone class.
- **Detection evidence:** An initial noiseless cone control stopped early at the E01 search-boundary assertion. On 10 November 2026, we constructed a perturbed synthetic paired response that passed both boundary checks and reached the 15% decision stage; the legacy script raised `The refined hard-gap model did not pass the 15% rule.` Physically, omitting a valid cone branch violates the thermal-resolution selection criterion (r_gap < 0.85 * r_cone and Eg >= 1 kBT) and prevents honest classification of gapless or thermally indistinguishable spectra.
- **Correction:** We implemented the complete two-condition selection rule (`r_gap < 0.85 * r_cone` and `Eg/kBT >= 1.0`) in `g24lab/l2.py`, returning `cone` with `Eg/kBT = 0` whenever either criterion is not met, and applied the same rule inside every bootstrap replicate.
- **Verification:** On the perturbed synthetic control, the shared pipeline found a candidate optimum near 1.9901 kBT with hard-gap RMS 0.1041422 versus cone RMS 0.1161550 (10.34% improvement, below 15%) and correctly returned `cone`, `Eg/kBT = 0`. A noiseless cone control returned `cone`, `Eg/kBT = 0` (RMS ~ 5.45e-16). Both controls are reproducible via `python -m tests.negative_controls` and documented in [negative_controls.json](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10/negative_controls.json). Synthetic controls are used solely for software verification and are never substituted for G24 experimental data.

## E03: Report figure panels excluded from the one-command runner (29 October 2026, reproducibility fix)

- **Detection:** Our first six-stage clean replay passed, but the five composite figures in the report draft still relied on a separate local plotting script rather than `reproduce.py`.
- **Correction:** In commit `05a4352`, we added `g24lab/report_figures.py` and invoked it at the end of `python reproduce.py --dataset all` so all five figure groups are generated directly from raw inputs and newly computed CSV/JSON outputs.
- **Verification:** A clean-clone run regenerated all five PNG/SVG figure groups with verified numerical inputs, including the newly computed global residual scan in Figure 2.
- **Classification:** Reproducibility coverage fix rather than an additional physics-model error.

## E04: Truncated PNG output in a fresh-clone replay (29 October 2026, output-integrity fix)

- **Detection:** At commit `05a4352`, the regular `L3_method.png` file truncated at 196,764 bytes before the third IDAT checksum (compared with 392,530 bytes when complete). Our PNG integrity check caught the defect and halted the run. Logs and metadata are retained in [full_replay_stdout.txt](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/reproduction_2026-10-29/failed_run_05a4352/full_replay_stdout.txt) and [failure.json](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/reproduction_2026-10-29/failed_run_05a4352/failure.json).
- **Correction:** At commit `58eb990`, we updated figure saving to render PNG bytes in memory, decode and verify them, write and flush to a temporary file, read back, and atomically replace the target file.
- **Verification:** Added regression tests verifying large-image decoding and rejection of truncated bytes without overwriting a valid file. All 12 tests and the fresh-clone six-stage run passed with unchanged scientific outputs.
- **Classification:** Output-integrity fix rather than an additional physics-model error.

## Provenance and audit summary

- E01 and E02 are two independently verified L2 physics-model implementation errors with reproducible detection and correction evidence ([final_2026-11-10 README](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10/README.md)).
- E03 and E04 document reproducibility and file-integrity defects resolved during clean-clone testing.
- All five L1 checkpoint PNGs are preserved intact in our archive. The QMplus blind receipt records a 1 h 42 min late upload, and the original September Git object `51814957` could not be recovered from local history; we disclose both limitations transparently alongside the clean-checkout reproduction at `d53604c`.
