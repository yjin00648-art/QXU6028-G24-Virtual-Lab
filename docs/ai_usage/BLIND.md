# Blind-Test AI Usage Record

- **Phase:** G24 blind analysis (preserved run log dated 24 September 2026).
- **Record review.** I reviewed the retrospective record compiled on 28 October 2026. Reviewer Jin Zhengyang, G24.
- **Tool:** ChatGPT Work / OpenAI Codex (exact historical model sub-version not recorded).

## Purpose and instruction summary

G24 used AI assistance to run the blind G24 dataset through L1 carrier counting, L2 transport-model fitting and uncertainty estimation, and L3 mean-zero reconstruction and noise-confidence testing, populate the blind result schema, verify array dimensions and finite values, and package `blind_results.json`, `run_log.txt` and `pipeline_commit.txt` for submission.

This retrospective summary draws on G24’s preserved files.

## Retained outputs and disclosed script differences

G24’s submitted QMplus archive (`G24_Blind_Submission.zip`) contains `blind_results.json`, `run_log.txt` and `pipeline_commit.txt` together with an L3 working-pack preview. All three blind submission files are preserved byte-for-byte with their original values and recorded commit hash.

The archived September regular and blind L2 scripts used different fixed search windows (1.90–2.20 vs 3.20–3.80 kBT) and dataset labels. G24 subsequently implemented a shared 0.50–8.00 kBT search in `g24lab/l2.py`.

## Checks and recorded blind results

- Raw manifest: 9 supplied blind input files verified for group G24.
- L1: C = 3.1581735677159646, nF = 4.460862731430169e11 cm^-2, corrected mobility = 33659.06777367225 cm^2 V^-1 s^-1.
- L2: `hard_gap`, Eg/kBT = 3.5306, 50 finite Fermi levels, 200 bootstrap replicates (seed 20260923), hard-gap fraction 1.000, p16–p84 [3.43, 3.6516] kBT; cone RMS ~ 0.10326635 vs hard-gap RMS ~ 0.01379014.
- L3: 100 finite zero-mean row-major values matching the retained CSV; resolution = 1.444295 probe pitches; 500 noise simulations (seed 20260924) give delta95 = 6.4205e-6; max|m| + delta95 = 0.02076858 < 0.030 (`clear pass`).
- Archive integrity: the three submitted blind files match all retained copies byte-for-byte.

## Timing and version provenance

### Session timeline (24 September 2026)

I completed the regular L1–L3 code and figures by **11:15 Singapore time (UTC+8)** and ran the blind analysis from **11:15 to 12:10 Singapore time** (55 minutes). On 24 September 2026, UK local time was BST (UTC+1, seven hours behind Singapore, verified against [GOV.UK](https://www.gov.uk/when-do-the-clocks-change) using Python `zoneinfo`).

| Event | Singapore (UTC+8) | UK (BST, UTC+1) |
| --- | --- | --- |
| Regular code and figures ready (reported) | 11:15 | 04:15 |
| Blind analysis work (reported) | 11:15–12:10 | 04:15–05:10 |
| QMplus due time | 16:00 | 09:00 |
| Combined L3 and blind submission last modified in QMplus | 17:42 | 10:42 |

### Preserved platform receipt and recorded commit hash

The regular L3 checkpoint and blind test were submitted together in `G24_Blind_Submission.zip` through the `Blind test L3` activity. The retained QMplus screenshot shows Attempt 1, `Submitted for grading`, last modified 24 September 2026 at 10:42 AM UK BST (1 h 42 min after the 9:00 AM due time). The original display and normalised timestamps are recorded in `blind_receipt.json` without assuming any extension or penalty adjustment.

The recorded blind commit hash is `51814957ddcb8d34d4153c386cf2194f7be0b541`. I created the repository on 28 October 2026. The retained September materials record the hash text for `51814957`, and its Git object is unavailable. The clean-checkout run at `d53604c` verifies reproducibility of the blind scientific fields. [Individual blind files and receipt](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/bf51beb8cbee64ffc3105f35d0bc2fcfd0ac17ec/submissions/blind/README.md)

Sources: [submitted ZIP](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/evidence/submitted_archives/G24_Blind_Submission.zip), [original result](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/submissions/blind/blind_results.json), [original log](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/submissions/blind/run_log.txt), [original hash](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/submissions/blind/pipeline_commit.txt), [L2 validation](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/blind_L2/recorded/validation/L2_validation.json), [L3 note](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/blind_L3/recorded/notes/L3_brief_note.txt), [receipt](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/evidence/blind_receipt.json), [archive checks](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/archive_verification.json).
