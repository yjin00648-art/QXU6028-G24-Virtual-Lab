# G24 final reproduction on 10 November 2026

The root [results.json](../../results.json) records the final regular L1–L3 results generated at [d53604c](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/commit/d53604c798420cd6f82ff5376989e3006d339980). The regular fit uses the 31 hard-gap candidates from 0.50 to 8.00 kBT in 0.25 kBT steps. The blind run uses the refined mode to reproduce the archived blind results.

```bash
python -m pip install -r requirements.txt
python reproduce.py --dataset all
python verify_reproduction.py --output-root generated/shared
python -m unittest discover -s tests -v
```

The [reproduction audit](reproduction_audit.json) records the environment, both dataset checks and the figure hashes. It passed for the final regular JSON and original blind scientific fields. The source and output hashes were checked and [all 12 tests passed](tests_stdout.txt). The five SVGs are in [report_figures](report_figures/). A new run generates the PNG and SVG versions.

## L2 course grid and submitted checkpoint

| Regular L2 result | Final course grid | September checkpoint |
| --- | ---: | ---: |
| Selected model | hard_gap | hard_gap |
| Eg/kBT | 2.00 | 2.0730 |
| p16–p84 / kBT | 2.00–2.00 | 2.00–2.13 |
| Hard-gap RMS | 0.01145077 | 0.01080589 |
| EF trajectory length | 58 | 58 |

The mean Hall coefficient changes sign between indices 28 and 29. Of 200 course-grid resamples, 169 selected 2.00 kBT and 31 selected 2.25 kBT. The [resample values](L2_bootstrap_gaps.csv), [course scan](L2_gap_residual_sweep.csv) and [trajectory table](L2_calculations.csv) give the underlying results. The percentile interval falls in one grid bin at this resolution.

The [checkpoint comparison](checkpoint_comparison.json) verifies the supplied L2 ZIP against the archived bytes. Its 31 coarse-grid residuals agree with the new run, and the referenced `3afb63d` commit is recoverable from the original bundle. Eleven EF assignments differ when the 0.25 kBT grid replaces the refined fit. The regular L1 and L3 numerical results agree with the archive within the stated tolerances.

## Submission and decision evidence

The archived QMplus ZIP contains the blind submission files and the regular L3 working pack. The L3 preview contains the result, map, method figure and note, and records `PENDING_LOCAL_L3_COMMIT`. The final run records the actual source used for the regular L3 outputs. The historical blind commit association remains unverified.

The [negative controls](negative_controls.json) exercise the old search boundary and the missing cone decision separately. The decision control uses synthetic data to reach the 15% guard and verify that the shared selector returns a cone when the hard-gap improvement is insufficient.
