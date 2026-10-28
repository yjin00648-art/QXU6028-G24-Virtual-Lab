#!/usr/bin/env python3
"""Replay archived stage scripts, preserving original data and recorded outputs.

This is a new archival wrapper, not evidence of a historically frozen pipeline.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def pipeline_commit() -> str:
    try:
        top = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if Path(top).resolve() != ROOT:
            return "PENDING_ARCHIVAL_REPLAY"
        dirty = subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=all"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if dirty:
            raise RuntimeError("Commit the repository changes before replaying; refusing to record a stale HEAD.")
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "PENDING_ARCHIVAL_REPLAY"


def validate_manifest(folder: Path) -> None:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("group") != "G24":
        raise ValueError("Only G24 data are expected.")
    for item in manifest["files"]:
        path = folder / item["name"]
        if path.stat().st_size != item["bytes"]:
            raise ValueError(f"Input length differs: {path.name}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            raise ValueError(f"Input hash differs: {path.name}")


def run_step(command: list[str], log) -> None:
    import shlex
    line = "\n$ " + shlex.join(command) + "\n"
    print(line, end="", flush=True)
    log.write(line)
    log.flush()
    env = dict(os.environ)
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("OMP_NUM_THREADS", "1")
    env["PYTHONUTF8"] = "1"
    env["MPLBACKEND"] = "Agg"
    with subprocess.Popen(
        command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
    ) as process:
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        code = process.wait()
    log.flush()
    if code:
        raise subprocess.CalledProcessError(code, command)


def replay(dataset: str, output_root: Path) -> None:
    prefix = "blind_" if dataset == "blind" else ""
    out = output_root / dataset
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"Use a fresh --output-dir; refusing to overwrite {out}")
    out.mkdir(parents=True, exist_ok=True)
    commit = pipeline_commit()
    with (out / "run_log.txt").open("w", encoding="utf-8") as log:
        header = (
            f"G24 archival replay: {dataset}\n"
            f"UTC: {datetime.now(timezone.utc).isoformat()}\n"
            f"Current repository commit: {commit}\n"
            "This is a new replay, not the historical blind-test log.\n"
        )
        print(header, flush=True)
        log.write(header)
        with tempfile.TemporaryDirectory(prefix="g24-inputs-") as temp:
            inputs = Path(temp)
            for stage in ("L1", "L2", "L3"):
                for source in (ROOT / f"{prefix}{stage}" / "data").iterdir():
                    if source.is_file():
                        shutil.copy2(source, inputs / source.name)
            validate_manifest(inputs)
            log.write("Original manifest SHA-256: PASS (9/9 files)\n")
            if dataset == "blind":
                shutil.copy2(inputs / "blind_results.json", inputs / "results_template.json")
                log.write("Aliased untouched blank blind_results.json as temporary results_template.json.\n")
            for stage, script in (("L1", "analysis.py"), ("L2", "analysis_L2_optimized.py"), ("L3", "analysis_L3.py")):
                command = [
                    sys.executable, str(ROOT / f"{prefix}{stage}" / "code" / script),
                    "--data-dir", str(inputs), "--output-dir", str(out),
                    "--pipeline-commit", commit,
                ]
                if stage != "L1":
                    command += ["--base-results", str(out / "results.json")]
                run_step(command, log)
            run_step([
                sys.executable, str(ROOT / f"{prefix}L1" / "code" / "analysis_L1_four_figures.py"),
                "--data-dir", str(inputs), "--results", str(out / "results.json"),
                "--output-dir", str(out),
            ], log)
            if dataset == "blind":
                run_step([
                    sys.executable, str(ROOT / "blind_L2" / "code" / "make_blind_l2_plots.py"),
                    "--data-dir", str(inputs), "--results", str(out / "results.json"),
                    "--output-dir", str(out),
                ], log)
                shutil.copy2(out / "results.json", out / "blind_results.json")
            (out / "pipeline_commit.txt").write_text(commit + "\n", encoding="utf-8")
            log.write("Archival replay completed. Historical recorded files were not overwritten.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("regular", "blind", "all"), default="all")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "generated")
    args = parser.parse_args()
    output_root = args.output_dir.resolve()
    if output_root == ROOT or output_root in ROOT.parents or any(
        output_root == ROOT / stage or ROOT / stage in output_root.parents
        for stage in ("L1", "L2", "L3", "blind_L1", "blind_L2", "blind_L3")
    ):
        parser.error("Output must not overwrite archived stage directories.")
    for dataset in (("regular", "blind") if args.dataset == "all" else (args.dataset,)):
        replay(dataset, output_root)


if __name__ == "__main__":
    main()
