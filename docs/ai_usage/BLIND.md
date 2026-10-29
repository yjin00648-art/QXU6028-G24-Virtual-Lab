# Blind-test AI usage record

- Phase: G24 blind analysis; the preserved run log is dated 24 September 2026.
- Record completed retrospectively: 28 October 2026.
- Tool/model: ChatGPT Work / OpenAI Codex, used in this analysis workflow; exact historical model version not recorded.
- Checked by: **Jin Zhengyang**. Reviewer identity supplied on the record-completion date; no original human review timestamp is inferred.

## Purpose and instruction summary

Process the supplied blind G24 files through L1 carrier counting, L2 transport-model fitting and uncertainty, and L3 mean-zero reconstruction and confidence testing. Populate the blind result schema, retain supporting figures/tables, check dimensions and finite values, and organise the result, run log and pipeline-hash files for submission.

This is a retrospective description supported by the retained files, not a recovered verbatim prompt. It does not assert that only a data path was changed during the original workflow.

## Output retained and changes disclosed

The actual user-confirmed QMplus ZIP contains blind_results.json, run_log.txt and pipeline_commit.txt inside its G24_Blind_Submission folder, together with a separate L3 working-pack ZIP. The three blind files were retained without numerical or hash edits. The working pack's preview outputs were not used to replace the submitted blind result.

The archived regular and blind refined L2 scripts use different fixed search windows: 1.90-2.20 and 3.20-3.80 kBT respectively; the blind L3 script also accepts the blind dataset label. These differences are disclosed. The later shared implementation removes the dataset-specific gap windows, but it is a subsequent improvement, not evidence that the historical submission used unchanged frozen code.

## Checks and recorded results

- Original manifests: nine supplied input files verified for the blind dataset; group G24.
- L1 correction factor=3.1581735677159646, nF=446086273143.0169 cm^-2 and corrected mobility=33659.06777367225 cm^2 V^-1 s^-1.
- L2 hard_gap, Eg/kBT=3.5306; 50 finite Fermi levels; 200 bootstrap replicates with seed 20260923, hard-gap fraction=1.000 and interval [3.43,3.6516] kBT. The archived validation records cone/hard-gap RMS approximately 0.10326635/0.01379014.
- L3 map: 100 finite row-major values, effectively zero mean; its archived CSV agrees with JSON in row-major order. Resolution=1.444295 probe pitches; 500 noise simulations, seed 20260924; delta95=6.420532374154724e-06.
- L3 confidence: max|m|+delta95=0.02076858 is below 0.030, giving clear pass.
- Current file checks confirm the actual submission's three blind files match all three historical blind/recorded copies. The archived log is preserved as a source record, not replaced with a newly captured terminal log.

## Timing and source-version evidence

### User-reported operating timeline, added 29 October 2026

Jin Zhengyang stated that all regular L1/L2/L3 code and run figures were complete at **11:15**, and that blind work took place from **11:15 to 12:10**. This is 55 minutes if the same day and clock apply. The statement is retained verbatim in [user_reported_timeline.json](../../evidence/user_reported_timeline.json).

The user subsequently clarified that the operating times should be treated as **Singapore time (UTC+8)** and the screenshot as **UK local time**. The conversion uses the associated 24 September 2026 session date from the screenshot and preserved run log; the clarification did not separately restate the date. On that date the UK was on BST (UTC+1), so Singapore was seven hours ahead. The government clock-change dates were checked at [GOV.UK](https://www.gov.uk/when-do-the-clocks-change), with conversions calculated using Python zoneinfo.

| Event | Singapore (UTC+8) | UK (BST, UTC+1) |
| --- | --- | --- |
| Regular code and figures ready, as reported | 11:15 | 04:15 |
| Blind work, as reported | 11:15-12:10 | 04:15-05:10 |
| Platform due time | 16:00 | 09:00 |
| Platform last modified/submission time | 17:42 | 10:42 |

The reported computational work lasted 55 minutes; the platform submission was recorded five hours and 32 minutes after the reported blind-work end. These are distinct events, and no reason for the interval is inferred. This account does not independently verify the code snapshot, the historical Git object, or an unchanged algorithm.

### Preserved platform receipt and recorded hash

The user-supplied QMplus screenshot shows Attempt 1, Submitted for grading, Not graded, and last modified 24 September 2026 at 10:42 AM. It shows a 9:00 AM due time and states submission was 1 hour 42 minutes late. Although the timezone is not printed in the image, the user has identified it as UK local time. The original display is retained alongside the timezone interpretation and normalized values in the receipt JSON; no penalty or extension decision is inferred.

The recorded pipeline hash is 51814957ddcb8d34d4153c386cf2194f7be0b541. Its underlying Git object has not been recovered from the supplied materials. The timing screenshot and preserved hash text do not independently establish that source object or prove compliance with the original frozen-code condition. The user has confirmed this October repository is their first GitHub repository.

Sources: [actual submission ZIP](../../evidence/submitted_archives/G24_Blind_Submission.zip), [original result](../../submissions/blind/blind_results.json), [original log](../../submissions/blind/run_log.txt), [original hash](../../submissions/blind/pipeline_commit.txt), [L2 validation](../../blind_L2/recorded/validation/L2_validation.json), [L3 note](../../blind_L3/recorded/notes/L3_brief_note.txt), [receipt](../../evidence/blind_receipt.json) and [current archive checks](../../validation/archive_verification.json).
