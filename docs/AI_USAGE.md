# Group G24 AI Usage Log

- **Group:** G24
- **Primary reviewer / coordinator:** Jin Zhengyang
- **Primary tools used:** ChatGPT Work / OpenAI Codex (exact historical model sub-versions from September 2026 were not recorded and are not inferred); Gemini (used on 19 November 2026 for final rubric review, defensive-writing refinement and log standardisation).

## Phase-by-phase summary

| Phase | Purpose and AI-assisted output | Detailed record |
| --- | --- | --- |
| L1 | Finite-temperature carrier counting, exact operating point, mobility correction, factor-sweep and supplementary plots | [L1 record](ai_usage/L1.md) |
| L2 | Signed Hall/sheet-resistance joint fit, gap refinement, Fermi trajectory and 200-replicate repeat-resampling uncertainty | [L2 record](ai_usage/L2.md) |
| L3 | Mean-zero regularised conductivity map, eta sensitivity, point-spread resolution, 500-run noise detection limit and pass/fail decision | [L3 record](ai_usage/L3.md) |
| Blind | L1/L2/L3 blind-dataset processing, schema validation and packaging of the three submitted blind files | [Blind record](ai_usage/BLIND.md) |
| Repository & Audit | GitHub repository setup (28 Oct), clean-clone replay (29 Oct) and negative-control verification (10 Nov) | [Repository record](ai_usage/REPOSITORY.md) |

## How we compiled these records

Our L1 and L2 instruction summaries are grounded in the preserved original September logs (`AI_usage_log_L1_original.txt` and `AI_usage_log_L2_original.txt`), which remain unmodified in this submission. Because full September chat transcripts were not saved, the L3 and blind summaries were compiled retrospectively on 28 October 2026 from our retained scripts, notes and outputs rather than presented as verbatim historical prompts.

Across all records, we separate original September submission files from subsequent repository consolidation and clean-clone verification. In particular, we disclose that the archived September regular and blind L2 scripts used different fixed search windows before we unified them into the shared global-search pipeline in `g24lab/l2.py`.

## Verification and corrections

- **L1:** Verified neutrality limit (C = 1.00 at EF = 0), reference sweep ratios (~2.00 at 0.073 eV, 2.60 at 0.100 eV, 5.10 at 0.200 eV), exact operating point (C = 3.58528, nF = 5.0737e11 cm^-2, mu = 2.0727e4 cm^2 V^-1 s^-1), and agreement with the Chapter 3 closed-form expression.
- **L2:** Verified signed independent normalisation (zero-crossing preserved between indices 28 and 29), 200 paired resamples, 58 regular / 50 blind Fermi-level assignments, and both the prescribed 0.25 kBT grid (2.00 kBT) and refined checkpoint (2.0730 kBT) fits.
- **L3:** Verified A = (128, 100) with numerical rank 92 and max row-sum ~1.67e-16, zero-mean reconstruction at eta0, 5-point eta sweep, central/off-centre PSF FWHMs (1.4443 / 1.3035 probe pitches), and 500 noise-only maps (delta95 = 4.0517e-6 regular; 6.4205e-6 blind).
- **Model-implementation error checks:** Two L2 physics-model implementation errors (E01 fixed narrow gap window; E02 missing cone return path when the 15% rule fails) were identified and independently verified with reproducible negative controls on 10 November 2026; see [AI_ERROR_LEDGER.md](AI_ERROR_LEDGER.md) and [negative_controls.json](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10/negative_controls.json).

## Timeline and GitHub provenance

- **Timeline (24 September 2026):** Jin Zhengyang reported completing the regular L1–L3 code and figures by 11:15 Singapore time (UTC+8, 04:15 UK BST) and working on the blind analysis from 11:15 to 12:10 Singapore time (04:15–05:10 UK BST). The QMplus receipt records the final combined upload at 10:42 UK BST (17:42 Singapore time), 1 h 42 min after the 09:00 UK BST deadline. Both the operating timeline and platform receipt are preserved in [user_reported_timeline.json](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/evidence/user_reported_timeline.json) and [BLIND.md](ai_usage/BLIND.md).
- **First GitHub repository (28 October 2026):** This coursework repository (`QXU6028-G24-Virtual-Lab`) is our first GitHub repository; we had not created an earlier remote GitHub repository. Four earlier local Git commits from September are preserved inside a Git bundle in `history/`. The Git object for the recorded September blind commit `51814957` was not retained in local history and is disclosed as an unavailable historical version object rather than replaced.

## Chronological log of post-session AI-assisted work

### 28–29 October 2026: Repository consolidation, report drafting and clean-clone reproduction
- **Tool:** ChatGPT Work / OpenAI Codex.
- **Contribution:** Organised the six stage directories, preserved original ZIP archives and SHA-256 hashes, unified the L2 pipeline, drafted the initial English report structure and five composite figures, integrated figure generation into `reproduce.py` (commit `05a4352`), and added atomic PNG validation after detecting a truncated `L3_method.png` (commit `58eb990`).
- **Verification:** Clean-clone execution at `58eb990` ran all six stages and 12 regression tests, matching all 176 regular and 168 blind scientific scalars within 1e-10 relative tolerance. Detailed logs are in [REPRODUCTION_2026-10-29.md](ai_usage/REPRODUCTION_2026-10-29.md) and [validation/reproduction_2026-10-29](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/reproduction_2026-10-29/README.md).

### 10 November 2026: Final L2 comparison, independent E02 control and report editing

| Tool or method | Purpose and AI contribution | Verification |
| --- | --- | --- |
| ChatGPT with Humanizer (prose editing) | Improved English readability and sentence pacing while keeping all values, units, technical terms, figure references and uncertainty statements intact. | Checked every numeric value, unit and citation against `results.json`, `blind_results.json` and figures. |
| ChatGPT (L2 grid alignment) | Configured `reproduce.py` to use the prescribed 0.25 kBT grid for the final regular result while retaining the refined-grid check for the blind archive, and verified the 200-resample interval. | Clean-checkout run at `d53604c` regenerated both datasets and all five figure groups; all 12 tests passed. |
| ChatGPT (E02 control & packaging) | Built an independent perturbed synthetic control to trigger the legacy 15% decision error (E02), verified the corrected cone branch, and assembled signed declarations. | Confirmed legacy failure and corrected `cone` (`Eg = 0`) output in [validation/final_2026-11-10](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10/README.md). |

### 15 November 2026: Citation and package audit
- **Tool:** ChatGPT Work / OpenAI Codex.
- **Contribution:** Standardised bracketed Vancouver citations, checked figure byte-identity against the 10 November clean-checkout outputs, verified Table 1 against regular and blind JSON files, and assembled the submission ZIP.
- **Verification:** Confirmed exact agreement across all five embedded report figures, Table 1, `results.json` and archived blind records ([final_2026-11-10](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/tree/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10)).

**Repository follow-up.** ChatGPT Work / OpenAI Codex synced the 15 November report and ledger entries
from the final submission package. It prepared the individual download links, verified the three files
against the original ZIP and checked the receipt transcription. [Blind submission files](../submissions/blind/README.md)

### 19 November 2026: Rubric audit, defensive-writing strengthening and log standardisation
- **Tool:** Gemini.
- **Contribution:** Audited the report, Chapter 3 lecture slides, raw G24 data and submission ZIP against the assessment brief and report guidance; strengthened defensive wording (extraction-model theme, Chapter 3 closed-form check, thermal-smoothing resolution limit, L3 noise-degradation discussion, blind narrow-defect attenuation caveat, Table 1 grid annotation, and corrected Reference [6] to Chapter 3 slides); standardised `AI_ERROR_LEDGER.md` and `AI_USAGE.md` into consistent English written from our group's perspective.
- **Verification:** Independently recomputed L1 and L3 regular/blind metrics from raw G24 files (matching `results.json` and `blind_results.json`), verified report word counts against the 2,500 / 200 / 150–200 word limits, and confirmed unchanged byte-identity of the three historical blind submission files.

### 20 November 2026 GitHub synchronisation

ChatGPT Work / OpenAI Codex compared the revised submission archive with the repository and prepared the English AI records for publication. The final regular results, the three original blind files and the archived reproduction audit matched byte for byte. The five report figure groups matched the 10 November replay. The trajectory check also identified a small local decrease in the otherwise upward L2 trend. [Final reproduction](../validation/final_2026-11-10/README.md) · [Regular L2 trajectory](../validation/final_2026-11-10/L2_calculations.csv)

For the final publication, Codex compared the two results files, the original blind files and the reproduction audit with the final submission package. `python reproduce.py --verify-only` passed. [Result checksums](../README.md) · [Blind version record](../submissions/blind/README.md)
