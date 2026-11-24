# Group G24 AI Usage Log

- **Group:** G24
- **Prepared by.** Jin Zhengyang, G24 coordinator and primary reviewer.
- **Primary tools used:** ChatGPT Work / OpenAI Codex (exact historical model sub-versions from September 2026 were not recorded and are not inferred); Gemini (used on 19 November 2026 for final rubric review, defensive-writing refinement and log standardisation).

## Phase-by-phase summary

| Phase | Purpose and AI-assisted output | Detailed record |
| --- | --- | --- |
| L1 | Finite-temperature carrier counting, exact operating point, mobility correction, factor-sweep and supplementary plots | [L1 record](ai_usage/L1.md) |
| L2 | Signed Hall/sheet-resistance joint fit, gap refinement, Fermi trajectory and 200-replicate repeat-resampling uncertainty | [L2 record](ai_usage/L2.md) |
| L3 | Mean-zero regularised conductivity map, eta sensitivity, point-spread resolution, 500-run noise detection limit and pass/fail decision | [L3 record](ai_usage/L3.md) |
| Blind | L1/L2/L3 blind-dataset processing, schema validation and packaging of the three submitted blind files | [Blind record](ai_usage/BLIND.md) |
| Repository & Audit | GitHub repository setup (28 Oct), clean-clone replay (29 Oct) and negative-control verification (10 Nov) | [Repository record](ai_usage/REPOSITORY.md) |

## Preparation of the records

The September logs provide the basis for the L1 and L2 instruction summaries. I checked the L1 log against the preserved record. The L3 and blind instruction summaries were compiled retrospectively on 28 October 2026 from the retained scripts, notes and outputs. [Checked L1 log](../AI_usage_log_L1_checked.txt) · [Original L1 snapshot](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/44144c7f6164270c0923fe70d1693fc913cd3dae/AI_usage_log_L1_original.txt) · [Original L2 log](../AI_usage_log_L2_original.txt)

The records distinguish the September submissions, the October repository consolidation and the later clean-clone verification. The archived September regular and blind L2 scripts used different fixed search windows. The shared pipeline in `g24lab/l2.py` subsequently introduced a common global search.

## Verification and corrections

- **L1:** Verified neutrality limit (C = 1.00 at EF = 0), reference sweep ratios (~2.00 at 0.073 eV, 2.60 at 0.100 eV, 5.10 at 0.200 eV), exact operating point (C = 3.58528, nF = 5.0737e11 cm^-2, mu = 2.0727e4 cm^2 V^-1 s^-1), and agreement with the Chapter 3 closed-form expression.
- **L2:** Verified signed independent normalisation (zero-crossing preserved between indices 28 and 29), 200 paired resamples, 58 regular / 50 blind Fermi-level assignments, and both the prescribed 0.25 kBT grid (2.00 kBT) and refined checkpoint (2.0730 kBT) fits.
- **L3:** Verified A = (128, 100) with numerical rank 92 and max row-sum ~1.67e-16, zero-mean reconstruction at eta0, 5-point eta sweep, central/off-centre PSF FWHMs (1.4443 / 1.3035 probe pitches), and 500 noise-only maps (delta95 = 4.0517e-6 regular; 6.4205e-6 blind).
- **Model-implementation error checks:** Two L2 physics-model implementation errors (E01 fixed narrow gap window; E02 missing cone return path when the 15% rule fails) were identified and independently verified with reproducible negative controls on 10 November 2026; see [AI_ERROR_LEDGER.md](AI_ERROR_LEDGER.md) and [negative_controls.json](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10/negative_controls.json).

## Timeline and GitHub provenance

- **Timeline for 24 September 2026.** I completed the regular L1–L3 code and figures by 11:15 Singapore time (UTC+8, 04:15 UK BST) and ran the blind analysis from 11:15 to 12:10 Singapore time (04:15–05:10 UK BST). QMplus displays 10:42 UK BST (17:42 Singapore time) as the last-modified time for the combined L3 and blind submission `G24_Blind_Submission.zip`, 1 h 42 min after the 09:00 UK BST deadline. [G24 work timeline](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/44144c7f6164270c0923fe70d1693fc913cd3dae/evidence/blind_work_timeline.json) · [QMplus receipt](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/44144c7f6164270c0923fe70d1693fc913cd3dae/evidence/blind_receipt.json) · [Blind record](ai_usage/BLIND.md)
- **GitHub history.** I created the G24 coursework repository on 28 October 2026. The repository’s `history/` directory contains a bundle of four local Git commits from September. For the September blind commit `51814957`, the retained evidence is the hash text from the original submission.

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
against the original ZIP and checked the receipt transcription. [Blind submission files](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/bf51beb8cbee64ffc3105f35d0bc2fcfd0ac17ec/submissions/blind/README.md)

### 19 November 2026: Rubric audit, defensive-writing strengthening and log standardisation
- **Tool:** Gemini.
- **Contribution:** Audited the report, Chapter 3 lecture slides, raw G24 data and submission ZIP against the assessment brief and report guidance; strengthened defensive wording (extraction-model theme, Chapter 3 closed-form check, thermal-smoothing resolution limit, L3 noise-degradation discussion, blind narrow-defect attenuation caveat, Table 1 grid annotation, and corrected Reference [6] to Chapter 3 slides); standardised `AI_ERROR_LEDGER.md` and `AI_USAGE.md` into consistent English for Group G24.
- **Verification:** Independently recomputed L1 and L3 regular/blind metrics from raw G24 files (matching `results.json` and `blind_results.json`), verified report word counts against the 2,500 / 200 / 150–200 word limits, and confirmed unchanged byte-identity of the three historical blind submission files.

### 20 November 2026 GitHub synchronisation

ChatGPT Work / OpenAI Codex compared the revised submission archive with the repository and prepared the English AI records for publication. The final regular results, the three original blind files and the archived reproduction audit matched byte for byte. The five report figure groups matched the 10 November replay. The trajectory check also identified a small local decrease in the otherwise upward L2 trend. [Final reproduction](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10/README.md) · [Regular L2 trajectory](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10/L2_calculations.csv)

For the final publication, Codex compared the two results files, the original blind files and the reproduction audit with the final submission package. `python reproduce.py --verify-only` passed. [Result checksums](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/README.md) · [Blind version record](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/bf51beb8cbee64ffc3105f35d0bc2fcfd0ac17ec/submissions/blind/README.md)

### Final report and submission package check on 24 November 2026

- **Tool.** ChatGPT Work / OpenAI Codex.
- **Contribution.** I provided the details of each member’s role and confirmed the L1 reviewer attribution. ChatGPT Work / OpenAI Codex reviewed the report against the coursework brief and guidance, checked the word count and numerical consistency, and aligned the wording of the AI records and report. Codex rebuilt the submission archive and prepared the standalone PDF extracts from the Word report.
- **Verification.** Checked Table 1 against the final regular and archived blind JSON files and matched the five embedded figures to the recorded replay. The three original blind files were checked against the preserved QMplus archive. See the [reproduction audit](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10/reproduction_audit.json) and [blind archive record](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/bf51beb8cbee64ffc3105f35d0bc2fcfd0ac17ec/submissions/blind/README.md).
- **Repository wording.** I used Codex to revise the repository documentation and the explanatory sentence in the displayed October replay logs to reflect my account of the work. The original October logs are available in the [replay record](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/44144c7f6164270c0923fe70d1693fc913cd3dae/validation/reproduction_2026-10-29/README.md).

### Working records formatting on 24 November 2026

- **Tool.** ChatGPT Work / OpenAI Codex.
- **Contribution.** Arranged the archived checkpoint checks, AI records, signed contribution details and final self-assessment under the fields in the coursework template.
- **Verification.** Compared the table headings with the coursework template, checked the signatures and self-assessment against the supplied records, and verified the final ZIP. The working records are included in the QMplus submission package.

### Caption and time record check on 24 November 2026

- **Tool.** ChatGPT Work / OpenAI Codex.
- **Contribution.** I confirmed that L3 and the blind test were submitted together. Codex corrected the checkpoint time entry and shortened the five figure captions.
- **Verification.** Checked the combined submission against the [QMplus receipt](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/44144c7f6164270c0923fe70d1693fc913cd3dae/evidence/blind_receipt.json) and counted 2,497 words in Sections 1–8 including captions. Compared the report body, tables and figures with the preceding version.

### Final Figure 1 and submission check on 24 November 2026

- **Tool.** ChatGPT Work / OpenAI Codex.
- **Contribution.** I supplied our archived L1 sweep plot for the revision of Figure 1(b). The updated panel combines the continuous model from charge neutrality with 12 ratios calculated using the original CSV band counts. It labels the operating point and the crossings at C = 2 and C = 4.
- **Verification.** Codex checked the sampled ratios against the original inputs and confirmed the operating-point ratio against the final regular result. Figure 1(a) matches the archived panel. The report has 2,492 words across Sections 1–8 including the captions.

### Final repository synchronisation on 24 November 2026

- **Tool.** ChatGPT Work / OpenAI Codex.
- **Contribution.** I used Codex to integrate the final Figure 1(b) plot into the shared one-command run and synchronise the AI usage records with the QMplus submission package. The panel draws the CSV-derived ratios from the regular L1 replay table. The four signed contributions, report and self-assessment are included in the course submission package.
- **Verification.** The shared run matched 176 regular and 168 blind numerical fields within the documented tolerances. All five output PNGs matched the report images byte for byte under the pinned dependencies and Nimbus Roman font. The archive integrity checks and 12 unit tests passed.
