"""Reproduce two observed legacy-model failures; do not invent historical AI errors."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import pandas as pd
from g24lab import l2

ROOT = Path(__file__).resolve().parents[1]


def synthetic_pairs(gap):
    _, hall, sheet = l2.build_curves(300.0, np.array([gap]))
    selected = np.unique(np.r_[np.linspace(0, 399, 51).astype(int), np.argmin(hall[0]), np.argmax(hall[0]), np.argmax(sheet[0])])
    rows = []
    for i, j in enumerate(selected):
        for repeat in (1, 2, 3):
            rows.append((i, repeat, hall[0, j], sheet[0, j]))
    return pd.DataFrame(rows, columns=["measurement_index", "repeat", "R_H_raw", "R_xx_raw"])


def legacy_failure(data, meta):
    path = ROOT / "L2" / "code" / "analysis_L2_optimized.py"
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location("legacy_regular_optimizer", path)
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
        with tempfile.TemporaryDirectory(prefix="g24-legacy-negative-") as temporary:
            args = SimpleNamespace(data_dir=Path(temporary), output_dir=Path(temporary) / "outputs", base_results=None, pipeline_commit="NEGATIVE_CONTROL_NOT_A_SUBMISSION", seed=20260923)
            with patch.object(old, "parse_args", return_value=args), patch.object(old.core, "load_and_validate", return_value=(data, meta)):
                try:
                    old.main()
                except Exception as error:
                    return {"exception": type(error).__name__, "message": str(error), "completed": False}
                return {"exception": None, "completed": True}
    finally:
        sys.path.pop(0)


def run_controls():
    blind = pd.read_csv(ROOT / "blind_L2" / "data" / "L2_data.csv")
    blind_meta = json.loads((ROOT / "blind_L2" / "data" / "L2_meta.json").read_text())
    cone = synthetic_pairs(0.0)
    entries = []
    for name, data, meta, expected in (
        ("E01_fixed_gap_window_on_actual_blind_data", blind, blind_meta, "hard_gap"),
        ("E02_missing_cone_fallback_on_synthetic_cone", cone, {"group": "G24", "T_K": 300.0, "dataset_set": "synthetic_control"}, "cone"),
    ):
        failure = legacy_failure(data, meta)
        means = l2.core.prepare_means(data)
        xy = l2.core.normalise_pairs(means.R_H_mean.to_numpy(), means.R_xx_mean.to_numpy())
        fixed = l2.fit_central(xy, float(meta["T_K"]))
        assert not failure["completed"], f"Legacy failure was not reproduced: {name}"
        assert fixed["model"] == expected
        if expected == "cone":
            assert fixed["selected_gap"] == 0 and fixed["selected_residual"] < 1e-12
        entries.append({"id": name, "discovered_on": "2026-10-28", "data_kind": "provided blind data" if expected == "hard_gap" else "explicitly synthetic noise-free cone validation control", "legacy": failure, "repaired_model": fixed["model"], "repaired_gap_kT": fixed["selected_gap"], "repaired_RMS": fixed["selected_residual"], "passed": True})
    source = ROOT / "L2" / "code" / "analysis_L2_optimized.py"
    return {"run_utc": datetime.now(timezone.utc).isoformat(), "kind": "post-audit regression evidence, not a historical September error ledger", "legacy_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "entries": entries}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "generated" / "negative_controls.json")
    args = parser.parse_args()
    record = run_controls()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
