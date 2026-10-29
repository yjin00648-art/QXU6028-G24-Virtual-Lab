#!/usr/bin/env python3
"""Check a completed replay against preserved results and source/output hashes."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
from verify_submission import verify as verify_archives

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare_results(old, new):
    numeric_count = 0
    differences = []

    def inspect(a, b, path="root"):
        nonlocal numeric_count
        if path == "root.pipeline_commit":
            return
        if isinstance(a, dict):
            if not isinstance(b, dict) or set(a) != set(b):
                differences.append({"field": path, "reason": "different keys"})
                return
            for key in a:
                inspect(a[key], b[key], path + "." + key)
        elif isinstance(a, list):
            if not isinstance(b, list) or len(a) != len(b):
                differences.append({"field": path, "reason": "different length"})
                return
            for i, (x, y) in enumerate(zip(a, b)):
                inspect(x, y, path + f"[{i}]")
        elif isinstance(a, (int, float)) and not isinstance(a, bool):
            numeric_count += 1
            if isinstance(b, bool) or not isinstance(b, (int, float)) or not math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12):
                differences.append({"field": path, "archived": a, "recomputed": b})
        elif type(a) is not type(b) or a != b:
            differences.append({"field": path, "archived": a, "recomputed": b})

    inspect(old, new)
    return {"all_scientific_fields_match": not differences,
            "numeric_scalars_compared": numeric_count,
            "relative_tolerance": 1e-10, "absolute_tolerance": 1e-12,
            "excluded_field": "pipeline_commit (new run records its real source commit)",
            "differences": differences}


def verify(output_root):
    output_root = Path(output_root).resolve()
    archive_checks = verify_archives(ROOT)
    record = {"kind": "post-audit-reproduction-not-historical-blind-test",
              "checked_utc": datetime.now(timezone.utc).isoformat(),
              "command": "python reproduce.py --dataset all",
              "archive_checks": archive_checks, "datasets": {}}
    commits = set()
    for dataset, name in (("regular", "results.json"), ("blind", "blind_results.json")):
        folder = output_root / dataset
        old = json.loads((ROOT / name).read_text())
        new = json.loads((folder / "results.json").read_text())
        comparison = compare_results(old, new)
        if not comparison["all_scientific_fields_match"]:
            raise ValueError(f"{dataset} differs from retained scientific results: {comparison['differences']}")
        manifest = json.loads((folder / "run_manifest.json").read_text())
        commit = new["pipeline_commit"]
        assert commit == manifest["pipeline_commit"]
        subprocess.run(["git", "cat-file", "-e", commit + "^{commit}"], cwd=ROOT, check=True)
        for path, expected in manifest["source_sha256"].items():
            if digest(ROOT / path) != expected:
                raise ValueError("Source changed since replay: " + path)
        for path, expected in manifest["output_sha256"].items():
            if digest(folder / path) != expected:
                raise ValueError("Output hash mismatch: " + path)
        commits.add(commit)
        record["datasets"][dataset] = {
            **comparison, "source_commit": commit, "environment": manifest["environment"],
            "source_hashes_verified": True, "output_hashes_verified": True,
            "output_file_count": len(manifest["output_sha256"]),
            "validation": json.loads((folder / "validation.json").read_text()),
            "L2_validation": json.loads((folder / "L2_validation.json").read_text()),
            "historical_result_sha256": digest(ROOT / name),
            "new_result_sha256": digest(folder / "results.json"),
        }
    assert len(commits) == 1
    figures = output_root / "report_figures"
    figure_validation = json.loads((figures / "validation.json").read_text())
    assert figure_validation["pipeline_commit"] in commits
    assert figure_validation["figure_count"] == 5
    for path, expected in figure_validation["input_sha256"].items():
        assert digest(output_root / path) == expected
    for path, expected in figure_validation["output_sha256"].items():
        assert digest(figures / path) == expected
    record["source_commit"] = commits.pop()
    record["report_figure_groups"] = 5
    record["report_figure_hashes_verified"] = True
    record["historical_blind_records_sha256"] = {
        path: digest(ROOT / path) for path in (
            "submissions/blind/blind_results.json", "submissions/blind/run_log.txt",
            "submissions/blind/pipeline_commit.txt")}
    record["status"] = "PASS"
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / "generated/shared")
    args = parser.parse_args()
    result = verify(args.output_root)
    (args.output_root / "reproduction_audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
