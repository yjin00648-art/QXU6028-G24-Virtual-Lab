"""Output checks, computed report and provenance (no hand-entered results)."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import platform
import zipfile
import numpy as np
import pandas as pd
import matplotlib
from PIL import Image

FIGURES = [
    "L1_factor_sweep.png", "L1_electron_population.png", "L1_hole_population.png",
    "L1_hall_coefficient.png", "L1_sheet_resistance.png", "L2_model_fit.png",
    "L2_EF_trajectory.png", "L2_gap_residual_sweep.png", "L2_RH_Rs_vs_measurement_index.png",
    "L2_raw_repeats.png", "L3_map.png", "L3_method.png",
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(results, data_dir, output_dir):
    template = json.loads((data_dir / "results_template.json").read_text(encoding="utf-8"))
    def inspect(a, b, name="root"):
        if isinstance(a, dict):
            if not isinstance(b, dict) or set(a) != set(b):
                raise ValueError(f"Template keys differ: {name}")
        if isinstance(b, dict):
            for key in b:
                inspect(a.get(key) if isinstance(a, dict) else None, b[key], name + "." + key)
        elif b is None:
            raise ValueError(f"Unfilled required value: {name}")
        elif isinstance(b, (int, float)) and not isinstance(b, bool) and not math.isfinite(b):
            raise ValueError(f"Nonfinite value: {name}")
        elif isinstance(b, list):
            for i, item in enumerate(b):
                inspect(None, item, name + f"[{i}]")
    inspect(template, results)
    n = pd.read_csv(data_dir / "L2_data.csv").measurement_index.nunique()
    ef = np.asarray(results["L2"]["EF_trajectory_eV"])
    m = np.asarray(results["L3"]["map"])
    assert results["group"] == "G24" and results["schema_version"] == "QXU6028-results-v1"
    assert len(results["pipeline_commit"]) == 40 and all(c in "0123456789abcdef" for c in results["pipeline_commit"])
    assert ef.shape == (n,) and np.isfinite(ef).all()
    assert m.shape == (100,) and np.isfinite(m).all() and abs(m.mean()) < 1e-10
    assert results["L2"]["model"] in {"cone", "hard_gap"}
    assert len(results["L2"]["Eg_uncertainty_kT"]) == 2
    assert type(results["L3"]["pass"]) is bool and results["L3"]["confidence"]
    table = pd.read_csv(output_dir / "L3_map.csv", index_col=0).to_numpy()
    assert np.allclose(m, table.ravel(order="C"), atol=1e-12, rtol=1e-10)
    for feature in results["L3"]["features"]:
        assert np.isclose(m[10 * feature["row"] + feature["column"]], feature["amplitude_fraction"])
    for name in FIGURES:
        with Image.open(output_dir / name) as image:
            image.verify()
    boot = pd.read_csv(output_dir / "L2_bootstrap_gaps.csv")
    assert len(boot) == 200
    assert np.allclose(np.percentile(boot.Eg_kT, [16, 84]), results["L2"]["Eg_uncertainty_kT"])
    return {"schema_keys_match": True, "required_values_filled_and_finite": True,
            "EF_length": int(n), "map_length": 100, "map_order": "row-major",
            "map_zero_mean": True, "map_matches_csv": True, "PNG_count_verified": len(FIGURES),
            "bootstrap_replicates": 200, "bootstrap_interval_verified": True}


def report(results, output_dir, temperature):
    l1, l2, l3 = (results[k] for k in ("L1", "L2", "L3"))
    v2 = json.loads((output_dir / "L2_validation.json").read_text())
    lines = [f"# G24 {results['dataset_set']} — computed results", "",
        "Automatically generated from untouched group data. This is a new replay, not the historical submission or a student contribution statement.", "",
        f"Source pipeline commit: {results['pipeline_commit']}", "",
        "## L1", "", "| Quantity | Computed value |", "| --- | ---: |",
        f"| Correction factor | {l1['correction_factor']:.10f} |",
        f"| Fermi-referenced density (cm⁻²) | {l1['n_fermi_op_cm2']:.10e} |",
        f"| Corrected mobility (cm² V⁻¹ s⁻¹) | {l1['mobility_corrected_cm2_Vs']:.10f} |", "",
        "The operating point is evaluated exactly. No additional factor of 10⁴ is inserted in mobility.", "",
        "## L2", "", "| Quantity | Computed value |", "| --- | ---: |",
        f"| Selected model | {l2['model']} |", f"| Gap / kBT | {l2['Eg_kT']:.4f} |",
        f"| Gap at {temperature:g} K (eV) | {l2['Eg_kT'] * 8.617333e-5 * temperature:.8f} |",
        f"| Gap bootstrap p16 / p84 (kBT) | {l2['Eg_uncertainty_kT'][0]:.6f} / {l2['Eg_uncertainty_kT'][1]:.6f} |",
        f"| Cone RMS | {v2['cone_residual']:.10f} |",
        f"| Best hard-gap RMS | {v2['best_hard_gap_residual']:.10f} |",
        f"| Hard-gap bootstrap fraction | {v2['bootstrap_hard_gap_fraction']:.3f} |",
        f"| Fermi trajectory points | {len(l2['EF_trajectory_eV'])} |", "",
        "Hall signs are retained; Hall and sheet resistance are normalised separately and assigned one common nearest-model Fermi level per observation. The 15% improvement and gap ≥ 1 kBT selection rules are applied.", "",
        "## L3", "", "| Quantity | Computed value |", "| --- | ---: |",
        f"| Maximum absolute non-uniformity (fraction) | {max(abs(x) for x in l3['map']):.10f} |",
        f"| Detection limit δ95 (fraction) | {l3['detection_limit_fraction']:.10e} |",
        f"| Conservative resolution (probe pitches) | {l3['resolution_probe_pitch']:.8f} |",
        f"| Pass | {str(l3['pass']).lower()} |", "", l3['confidence'], "",
        "The flat map contains 100 row-major values with zero mean. Fractional values are multiplied by 100 only when expressed as percentages, not inside the inverse calculation.", "",
        "## Figures", ""]
    for name in FIGURES:
        lines += [f"### {name}", "", f"![{name}]({name})", ""]
    lines += ["## Machine-readable evidence", "", "See results.json, L2_calculations.csv, L2_bootstrap_gaps.csv, L2_bootstrap_EF.csv, L3_map.csv, L3_eta_sensitivity.csv, validation.json and run_manifest.json.", ""]
    (output_dir / "COMPUTED_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def checkpoints(output_dir):
    groups = {
        "L1": ["L1_factor_sweep.png", "L1_electron_population.png", "L1_hole_population.png", "L1_hall_coefficient.png", "L1_sheet_resistance.png", "L1_brief_note.txt", "L1_four_figures_note.txt"],
        "L2": ["L2_model_fit.png", "L2_EF_trajectory.png", "L2_brief_note.txt"],
        "L3": ["L3_map.png", "L3_method.png", "L3_brief_note.txt"],
    }
    for stage, names in groups.items():
        with zipfile.ZipFile(output_dir / f"G24_{stage}_Checkpoint.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for name in ["results.json", *names, "commit_hash.txt"]:
                archive.write(output_dir / name, arcname=name)


def manifest(output_dir, root, commit, config, inputs):
    code = [root / "reproduce.py", root / "pipeline_config.json", root / "requirements.txt", *sorted((root / "g24lab").glob("*.py"))]
    original_manifest = json.loads((inputs / "manifest.json").read_text(encoding="utf-8"))
    original_inputs = [inputs / item["name"] for item in original_manifest["files"]] + [inputs / "manifest.json"]
    record = {
        "kind": "post-audit-replay-not-historical-blind-test", "pipeline_commit": commit,
        "configuration": config,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "matplotlib": matplotlib.__version__},
        "source_sha256": {str(f.relative_to(root)): sha256(f) for f in code},
        "input_sha256": {f.name: sha256(f) for f in original_inputs},
        "output_sha256": {f.name: sha256(f) for f in sorted(output_dir.iterdir()) if f.is_file() and f.name not in {"run_manifest.json", "run_log.txt"}},
    }
    (output_dir / "run_manifest.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")

