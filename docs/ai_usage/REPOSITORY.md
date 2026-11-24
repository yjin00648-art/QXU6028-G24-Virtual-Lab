# Repository Consolidation and Audit AI Usage Record

- **Phase / date:** Repository creation, consolidation and verification (28–29 October 2026).
- **Tool:** ChatGPT Work / OpenAI Codex with local file, Git and GitHub tools.
- **Reviewer:** Jin Zhengyang.

## Scope and workflow

On 28 October 2026, we created our first GitHub repository (`QXU6028-G24-Virtual-Lab`) to consolidate our September L1–L3 and blind archives, publish a clean one-command `reproduce.py`, verify file hashes against our three QMplus checkpoint ZIPs, and document AI usage and error fixes transparently.

## Consolidation and corrections adopted

- Organised all six original stage directories (`L1`, `L2`, `L3`, `blind_L1`, `blind_L2`, `blind_L3`), preserving original raw inputs, checkpoint ZIPs, SHA-256 manifests and the three historical blind submission files without modifying historical hashes.
- Verified all five L1 PNGs (one factor-sweep plot plus four supplementary plots) are present in the L1 archive.
- Built the shared `g24lab/` implementation removing dataset-specific L2 search windows, alongside `--verify-only` archive-integrity checks.
- Completed reviewer attribution (Jin Zhengyang) while preserving the original September L1/L2 log snapshots verbatim.

## Verification evidence and provenance

- Verified both 9-file raw input manifests, 91 preserved-file SHA-256 hashes, all three checkpoint ZIPs, JSON schema compliance and all 21 archived PNGs, plus row-major CSV/JSON agreement for the blind L3 map.
- Verified the initial remote upload (`e4367a77`) via a fresh GitHub clone (39/39 files byte-identical).
- Preserved four older local September Git commits inside a Git bundle in `history/`; unrecovered historical hashes (such as `51814957`) remain disclosed as unavailable historical Git objects.

## Full clean-clone reproduction (29 October 2026)

On 29 October 2026, we ran a full clean-clone reproduction of both datasets and fixed every reproducibility gap encountered:
- Integrated all five report composite figure groups into `reproduce.py` (`05a4352`).
- Resolved a truncated `L3_method.png` output by implementing in-memory PNG validation and atomic file replacement with two regression tests (`58eb990`).
- Confirmed all six stages, all five report figure groups, strict numerical comparison (176 regular and 168 blind scalars within 1e-10 relative tolerance) and all 12 tests passed on a clean clone.

Sources: [master log](../AI_USAGE.md), [provenance](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/PROVENANCE.json), [archive checks](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/archive_verification.json), [legacy controls](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/final_2026-11-10/negative_controls.json), [history explanation](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/history/README.md), [29 Oct full run](https://github.com/yjin00648-art/QXU6028-G24-Virtual-Lab/blob/a1fc8bcce6bfc3cdd0c742016dd0ba02c96a0135/validation/reproduction_2026-10-29/README.md), [reproduction details](REPRODUCTION_2026-10-29.md).
