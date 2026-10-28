#!/usr/bin/env python3
"""Read-only checks of the preserved G24 submissions; no numerical re-analysis."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_results(result, template, dataset, count):
    require(set(result) == set(template), "Root JSON schema keys differ")
    for stage in ("L1", "L2", "L3"):
        require(set(result[stage]) == set(template[stage]), f"Schema keys differ: {stage}")
    def finite(value):
        require(value is not None, "Unfilled required result")
        if isinstance(value, dict):
            for item in value.values():
                finite(item)
        elif isinstance(value, list):
            for item in value:
                finite(item)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            require(math.isfinite(value), "Nonfinite result")
    finite(result)
    require(result["schema_version"] == "QXU6028-results-v1", "Schema version differs")
    require(result["group"] == "G24" and result["dataset_set"] == dataset, "Dataset identity differs")
    commit = result["pipeline_commit"]
    require(len(commit) == 40 and all(c in "0123456789abcdef" for c in commit), "Invalid recorded hash")
    require(len(result["L2"]["EF_trajectory_eV"]) == count, "Fermi trajectory length differs")
    require(result["L2"]["model"] in {"cone", "hard_gap"}, "Unknown model")
    interval = result["L2"]["Eg_uncertainty_kT"]
    require(len(interval) == 2 and interval[0] <= interval[1], "Invalid gap uncertainty interval")
    model = result["L3"]["map"]
    require(len(model) == 100 and abs(sum(model) / 100) < 1e-10, "Map must have 100 zero-mean values")
    require(type(result["L3"]["pass"]) is bool, "L3 pass must be Boolean")
    require(bool(result["L3"]["confidence"]), "Missing confidence statement")
    for feature in result["L3"]["features"]:
        index = 10 * feature["row"] + feature["column"]
        require(0 <= index < 100, "Feature index outside map")
        require(math.isclose(model[index], feature["amplitude_fraction"], abs_tol=1e-12), "Feature and row-major map differ")


def verify(root=ROOT):
    root = Path(root).resolve()
    record = {"kind": "archive-consistency-check-without-numerical-rerun", "group": "G24"}
    counts = {}
    for dataset, prefix in (("regular", ""), ("blind", "blind_")):
        paths = {p.name: p for stage in ("L1", "L2", "L3") for p in (root / f"{prefix}{stage}" / "data").iterdir() if p.is_file()}
        manifest = json.loads(paths["manifest.json"].read_text(encoding="utf-8"))
        require(manifest["group"] == "G24" and manifest["dataset_set"] == dataset, "Manifest identity differs")
        for item in manifest["files"]:
            require(Path(item["name"]).name == item["name"], "Invalid manifest path")
            p = paths[item["name"]]
            require(p.stat().st_size == item["bytes"] and digest(p) == item["sha256"], "Raw input differs: " + p.name)
        with paths["L2_data.csv"].open(newline="", encoding="utf-8-sig") as stream:
            count = len({row["measurement_index"] for row in csv.DictReader(stream)})
        result = json.loads((root / ("blind_results.json" if dataset == "blind" else "results.json")).read_text(encoding="utf-8"))
        template = json.loads(paths["blind_results.json" if dataset == "blind" else "results_template.json"].read_text(encoding="utf-8"))
        check_results(result, template, dataset, count)
        counts[dataset] = {"raw_manifest_files_verified": len(manifest["files"]), "EF_trajectory_length": count, "map_length": 100, "recorded_pipeline_commit": result["pipeline_commit"]}
    record["datasets"] = counts
    regular_bytes = (root / "results.json").read_bytes()
    require(regular_bytes == (root / "L3/recorded/results.json").read_bytes(), "Regular final result differs from its recorded source")
    final = json.loads(regular_bytes)
    evidence = json.loads((root / "evidence/INDEX.json").read_text(encoding="utf-8"))
    for item in evidence["items"]:
        file = root / item["repository_path"]
        require(file.stat().st_size == item["bytes"] and digest(file) == item["sha256"], "Evidence changed: " + item["repository_path"])
    archives = root / "evidence/submitted_archives"
    for name, prefix, stage in (("G24_L1_4figures.zip", "", "L1"), ("G24_L2_Checkpoint.zip", "G24_L2_Checkpoint/", "L2")):
        with zipfile.ZipFile(archives / name) as archive:
            require(archive.testzip() is None, "ZIP integrity failed: " + name)
            stage_result = json.loads(archive.read(prefix + "results.json"))
            require(stage_result["L1"] == final["L1"], "Submitted L1 differs from final result")
            if stage == "L2":
                require(stage_result["L2"] == final["L2"], "Submitted L2 differs from final result")
            for member in archive.infolist():
                if member.is_dir():
                    continue
                file_name = Path(member.filename).name
                destination = root / stage / "recorded" / file_name
                require(destination.read_bytes() == archive.read(member.filename), "Submitted checkpoint member differs: " + member.filename)
            if stage == "L1":
                figures = {Path(f).name for f in archive.namelist() if f.lower().endswith(".png")}
                require(figures == {"L1_factor_sweep.png", "L1_electron_population.png", "L1_hole_population.png", "L1_hall_coefficient.png", "L1_sheet_resistance.png"}, "Expected one correction-factor figure plus four supplementary figures")
    with zipfile.ZipFile(archives / "G24_Blind_Submission.zip") as archive:
        require(archive.testzip() is None, "Blind ZIP integrity failed")
        for name in ("blind_results.json", "run_log.txt", "pipeline_commit.txt"):
            original = archive.read("G24_Blind_Submission/" + name)
            require((root / "submissions/blind" / name).read_bytes() == original, "Extracted blind file differs: " + name)
            for stage in ("blind_L1", "blind_L2", "blind_L3"):
                require((root / stage / "recorded" / name).read_bytes() == original, "Existing blind record differs: " + stage + "/" + name)
        require((root / "blind_results.json").read_bytes() == archive.read("G24_Blind_Submission/blind_results.json"), "Root blind result differs from submitted ZIP")
    receipt = json.loads((root / "evidence/blind_receipt.json").read_text(encoding="utf-8"))
    require(receipt == evidence["blind_receipt"], "Receipt metadata differs")
    record.update({"evidence_files_verified": len(evidence["items"]), "submitted_ZIPs_verified": 3, "L1_submitted_PNGs": 5,
        "regular_final_source": "L3/recorded/results.json (byte-identical)", "blind_final_source": "G24_Blind_Submission.zip (byte-identical)",
        "L1_and_L2_fields_match_submitted_checkpoints": True, "historical_blind_files_match_all_three_recorded_directories": True,
        "blind_submission_status": receipt["submission_status"], "blind_last_modified_as_displayed": receipt["last_modified_as_displayed"],
        "blind_timing_as_displayed": receipt["time_remaining_as_displayed"], "numerical_analysis_rerun": False,
        "historical_commit_objects_verified": False, "historical_hashes_preserved_without_replacement": True})
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(verify(), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
