# G24 AI usage log

Record completed: **28 October 2026**. **Checked by: Jin Zhengyang.**

Timeline addendum, **29 October 2026**: Jin Zhengyang reported completion of all regular L1/L2/L3 code and run figures at 11:15, followed by blind work from 11:15 to 12:10. The event date and timezone were not explicitly supplied. The original statement is preserved in [user_reported_timeline.json](../evidence/user_reported_timeline.json) and discussed in the [blind record](ai_usage/BLIND.md). It is recorded as a user account, separately from the platform receipt and historical source-version verification.

Tool: ChatGPT Work / OpenAI Codex, as identified in the existing L1/L2 records and current work session. An exact historical model version was not recorded and is not inferred.

The user supplied the reviewer name and requested completion of the remaining log fields. Reviewer attribution is recorded on the completion date; it does not assign an invented review date or claim that every automated check was personally executed by the reviewer during the original lab.

## Phase records

| Phase | Purpose and AI-assisted output | Instruction and checking record |
| --- | --- | --- |
| L1 | Finite-temperature carrier counting, exact operating point, mobility correction, factor-sweep and supplementary plots | [L1 record](ai_usage/L1.md) |
| L2 | Signed Hall/sheet-resistance joint fit, gap refinement, Fermi trajectory and repeat-resampling uncertainty | [L2 record](ai_usage/L2.md) |
| L3 | Mean-zero regularised map, eta sensitivity, point-spread resolution, noise detection limit and specification decision | [L3 record](ai_usage/L3.md) |
| Blind | L1/L2/L3 blind outputs, schema checks, three submitted files and package organisation | [Blind record](ai_usage/BLIND.md) |
| Repository | First GitHub repository, source and evidence organisation, later code fixes and read-only verification | [Repository record](ai_usage/REPOSITORY.md) |

## How the records were completed

The L1 and L2 instruction summaries are grounded in the preserved original AI logs. The L3 and blind entries are retrospective summaries of the task, implemented methods and retained outputs. The historical verbatim prompts and full transcripts were not recovered, so these summaries are not presented as exact quotations or complete chat histories.

For each phase, the record separates outputs retained in the historical archive from changes made during repository consolidation. Numeric values are taken from the existing JSON, notes and validation files, rather than recalculated for this log update. In particular, the blind record discloses the differences between the archived regular and blind L2 scripts; it does not describe them as a proven unchanged frozen pipeline.

## Checking and corrections

- L1: the archived numerical gates, exact operating point and mobility relation are documented in the phase record. The user-confirmed reviewer name completes the current L1 attribution.
- L2: the original log records the refined gap, signed independent normalisation, 200 repeat-resampling fits and the 58-point trajectory. Blind uncertainty and its 50-point trajectory are recorded separately.
- L3: archived notes document the input dimensions, constant-mode limitation, selected eta, two PSFs and 500 noise simulations. The recorded regular decision is clear fail; the blind decision is clear pass.
- Repository checking: the latest read-only review verified 91 preserved-file hashes, both nine-file raw manifests, the three user-confirmed submission ZIPs, JSON structure and all 21 archived PNGs. These checks verify archived-file consistency; they are not a fresh numerical reproduction of the revised shared pipeline.
- Corrections to the legacy L2 model implementation are described in [AI_ERROR_LEDGER.md](AI_ERROR_LEDGER.md), with the existing evidence in [negative_controls.json](../validation/negative_controls.json). The controls were executed during the 28 October audit, not during this documentation update. Both preserved legacy controls stop at the preliminary search-boundary assertion; a separately isolated cone-fallback failure was not recorded. These records therefore do not by themselves demonstrate two independent historical physics-concept errors.

The original L1/L2 logs are preserved byte-for-byte as [L1 original](../AI_usage_log_L1_original.txt) and [L2 original](../AI_usage_log_L2_original.txt). The placeholder in the historical L1 snapshot is superseded by **Jin Zhengyang** in the completed current record. Keeping the snapshot does not leave the current attribution unfilled.

## First GitHub repository and version provenance

The user confirmed: **this is their first GitHub repository; they had not created a GitHub repository before this one.** The repository was created on 28 October 2026. Its actual GitHub history starts with the 28 October initialisation and import commits; later work is recorded in subsequent real commits.

Four older local Git commits are present in the supplied project archive and preserved in a bundle. A local Git object does not establish a pre-existing GitHub repository, who personally operated Git, or a student's contribution. Missing objects referenced by historical result hashes are therefore described as unavailable source-version evidence, not as a missing earlier GitHub repository. The original hashes are retained without replacement. See [history/README.md](../history/README.md).

## Scope of this update

This update writes AI-use records and clarifies provenance. It does not change raw data, numerical results, original submission ZIPs or original blind files. No six-stage numerical rerun or QMplus resubmission was performed. The formal report, signed contribution statement and self-assessment remain outside the user's requested repository update.
