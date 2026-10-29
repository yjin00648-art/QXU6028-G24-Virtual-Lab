#!/usr/bin/env python3
"""One shared, data-driven L1/L2/L3 pipeline; preserves historical archives."""
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
from g24lab import reporting

ROOT = Path(__file__).resolve().parent


def pipeline_commit():
    top = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"], text=True).strip()
    if Path(top).resolve() != ROOT:
        raise RuntimeError("Clone this repository with Git before running.")
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=all"], text=True).strip():
        raise RuntimeError("Commit code/configuration changes first; a dirty worktree is not a reproducible source version.")
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def validate_manifest(folder):
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("group") != "G24" or manifest.get("dataset_set") not in {"regular", "blind"}:
        raise ValueError("Expected a supplied G24 regular or blind dataset.")
    for item in manifest["files"]:
        if Path(item["name"]).name != item["name"]:
            raise ValueError("Manifest filenames must not escape the input directory.")
        path = folder / item["name"]
        if path.stat().st_size != item["bytes"] or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Original input hash/length check failed: " + item["name"])
    return manifest


def run_step(command, log):
    import shlex
    line = "\n$ " + shlex.join(command) + "\n"
    print(line, end="", flush=True)
    log.write(line)
    log.flush()
    env = dict(os.environ)
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("OMP_NUM_THREADS", "1")
    env.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
    with subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace") as process:
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        code = process.wait()
    log.flush()
    if code:
        raise subprocess.CalledProcessError(code, command)


def replay(dataset, output_root, commit, config, external=None):
    out = output_root / dataset
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"Refusing to overwrite {out}; select a fresh --output-dir.")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "run_log.txt").open("w", encoding="utf-8") as log:
        header = f"G24 shared pipeline replay: {dataset}\nUTC: {datetime.now(timezone.utc).isoformat()}\nPipeline commit: {commit}\nNew replay, not the historical submission.\nConfiguration: {json.dumps(config, sort_keys=True)}\n"
        print(header, flush=True)
        log.write(header)
        with tempfile.TemporaryDirectory(prefix="g24-inputs-") as temp:
            inputs = Path(temp)
            if external:
                for source in external.iterdir():
                    if source.is_file():
                        shutil.copy2(source, inputs / source.name)
            else:
                prefix = "blind_" if dataset == "blind" else ""
                for stage in ("L1", "L2", "L3"):
                    for source in (ROOT / f"{prefix}{stage}" / "data").iterdir():
                        if source.is_file():
                            shutil.copy2(source, inputs / source.name)
            meta = validate_manifest(inputs)
            if meta["dataset_set"] != dataset:
                raise ValueError("Input dataset label does not match the selected output label.")
            log.write(f"Input manifest checks: PASS ({len(meta['files'])}/{len(meta['files'])})\n")
            if not (inputs / "results_template.json").exists():
                shutil.copy2(inputs / "blind_results.json", inputs / "results_template.json")
                log.write("Aliased the untouched blank blind template in a temporary directory.\n")
            for stage in ("l1", "l2", "l3"):
                command = [sys.executable, "-m", f"g24lab.{stage}", "--data-dir", str(inputs), "--output-dir", str(out), "--pipeline-commit", commit]
                if stage == "l2":
                    command += ["--gap-mode", config["gap_mode"], "--seed", str(config["bootstrap_seed"])]
                elif stage == "l3":
                    command += ["--base-results", str(out / "results.json"), "--seed", str(config["noise_seed"])]
                run_step(command, log)
            run_step([sys.executable, "-m", "g24lab.carrier_figures", "--data-dir", str(inputs), "--results", str(out / "results.json"), "--output-dir", str(out)], log)
            results = json.loads((out / "results.json").read_text(encoding="utf-8"))
            checks = reporting.validate(results, inputs, out)
            (out / "validation.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
            temperature = float(json.loads((inputs / "L2_meta.json").read_text())["T_K"])
            reporting.report(results, out, temperature)
            (out / "pipeline_commit.txt").write_text(commit + "\n", encoding="utf-8")
            if dataset == "blind":
                shutil.copy2(out / "results.json", out / "blind_results.json")
            reporting.checkpoints(out)
            reporting.manifest(out, ROOT, commit, config, inputs)
            log.write("All schema, finite-value, trajectory, row-major-map, figure and bootstrap checks: PASS.\nHistorical records were not overwritten.\n")
            log.flush()
    print(f"Completed {dataset}: {out}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Verify preserved submissions and results without rerunning numerical analysis.")
    parser.add_argument("--dataset", choices=("regular", "blind", "all"), default="all")
    parser.add_argument("--data-dir", type=Path, help="Optional untouched complete G24 directory; select one dataset.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "generated" / "shared")
    parser.add_argument("--config", type=Path, default=ROOT / "pipeline_config.json")
    parser.add_argument("--gap-mode", choices=("refined", "course"), help="Override the config's gap grid, using the same rule for any dataset.")
    args = parser.parse_args()
    if args.verify_only:
        from verify_submission import verify
        print(json.dumps(verify(ROOT), indent=2, ensure_ascii=False))
        return
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if set(config) != {"gap_mode", "bootstrap_seed", "noise_seed"} or config["gap_mode"] not in {"course", "refined"}:
        parser.error("Configuration must contain gap_mode, bootstrap_seed and noise_seed.")
    if args.gap_mode:
        config["gap_mode"] = args.gap_mode
    for key in ("bootstrap_seed", "noise_seed"):
        if type(config[key]) is not int or config[key] < 0:
            parser.error("Seeds must be nonnegative integers.")
    output = args.output_dir.resolve()
    protected = [ROOT / p for p in ("L1", "L2", "L3", "blind_L1", "blind_L2", "blind_L3", "evidence", "history", "g24lab", "results", "submissions", "validation", "docs", "tests")]
    if output == ROOT or output in ROOT.parents or any(output == p or p in output.parents for p in protected):
        parser.error("Output must not overwrite tracked data, history, evidence, source or published results.")
    if args.data_dir and args.dataset == "all":
        parser.error("Use --dataset regular or blind with --data-dir.")
    commit = pipeline_commit()
    for dataset in (("regular", "blind") if args.dataset == "all" else (args.dataset,)):
        replay(dataset, output, commit, config, args.data_dir.resolve() if args.data_dir else None)
    if args.dataset == "all":
        with (output / "report_figures_run_log.txt").open("w", encoding="utf-8") as log:
            run_step([sys.executable, "-m", "g24lab.report_figures", "--output-root", str(output)], log)
        print(f"Completed five report figure groups: {output / 'report_figures'}", flush=True)


if __name__ == "__main__":
    main()
