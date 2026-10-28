#!/usr/bin/env python3
"""QXU6028 G24 L1 forward carrier-count analysis.

This script reads the untouched G24 L1 inputs, validates the published gates,
calculates the exact operating-point correction, and writes the L1 checkpoint
outputs. It does not infer the operating point from the nearest CSV row.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


KB_EV_K = 8.617333e-5
NA_CM2 = 3.816e15
ELEMENTARY_CHARGE_C = 1.602176634e-19
EMAX_EV = 2.5
N_INTEGRATION_POINTS = 20_001


def fermi(E_eV: np.ndarray, EF_eV: float, T_K: float) -> np.ndarray:
    """Finite-temperature Fermi function with overflow protection."""
    x = np.clip((E_eV - EF_eV) / (KB_EV_K * T_K), -60.0, 60.0)
    return 1.0 / (np.exp(x) + 1.0)


def n_band(EF_eV: float, T_K: float, c_per_eV_atom: float) -> float:
    """Band-edge count in cm^-2, integrated from E=0 to Emax."""
    E = np.linspace(0.0, EMAX_EV, N_INTEGRATION_POINTS)
    integrand = c_per_eV_atom * E * fermi(E, EF_eV, T_K)
    return float(NA_CM2 * np.trapezoid(integrand, E))


def n_fermi(EF_eV: float, T_K: float, c_per_eV_atom: float) -> float:
    """Fermi-referenced count in cm^-2, integrated from E=EF to Emax."""
    E = np.linspace(EF_eV, EMAX_EV, N_INTEGRATION_POINTS)
    integrand = c_per_eV_atom * E * fermi(E, EF_eV, T_K)
    return float(NA_CM2 * np.trapezoid(integrand, E))


def n_fermi_closed(EF_eV: float, T_K: float, c_per_eV_atom: float) -> float:
    """Closed-form Fermi-referenced count for the ideal linear DoS."""
    kT_eV = KB_EV_K * T_K
    return float(
        NA_CM2
        * c_per_eV_atom
        * kT_eV
        * (EF_eV * np.log(2.0) + (np.pi**2 / 12.0) * kT_eV)
    )


def correction_factor(EF_eV: float, T_K: float, c_per_eV_atom: float) -> float:
    return n_band(EF_eV, T_K, c_per_eV_atom) / n_fermi(
        EF_eV, T_K, c_per_eV_atom
    )


def solve_crossing(
    target: float,
    T_K: float,
    c_per_eV_atom: float,
    lower_eV: float = 0.0,
    upper_eV: float = 0.30,
    iterations: int = 80,
) -> float:
    """Bisection solution of C(EF)=target over the positive-doping range."""
    lo, hi = lower_eV, upper_eV
    if correction_factor(lo, T_K, c_per_eV_atom) > target:
        raise ValueError("Lower crossing bracket is above the requested target.")
    if correction_factor(hi, T_K, c_per_eV_atom) < target:
        raise ValueError("Upper crossing bracket is below the requested target.")
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        if correction_factor(mid, T_K, c_per_eV_atom) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def detect_commit(explicit_commit: str | None) -> str:
    if explicit_commit:
        return explicit_commit
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "PENDING_GIT_COMMIT"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/regular_G24"),
        help="Directory containing untouched G24 input files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/L1"),
        help="Directory for generated L1 outputs.",
    )
    parser.add_argument(
        "--pipeline-commit",
        default=None,
        help="Frozen Git commit hash; auto-detected when omitted.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    params = json.loads((args.data_dir / "L1_params.json").read_text())
    data = pd.read_csv(args.data_dir / "L1_data.csv")

    if params.get("group") != "G24":
        raise ValueError("This analysis expects the G24 dataset.")
    required_columns = {"EF_eV", "n_band_cm2", "rho_ohm_sq"}
    if not required_columns.issubset(data.columns):
        raise ValueError(f"Missing L1 columns: {required_columns - set(data.columns)}")
    if data[list(required_columns)].isna().any().any():
        raise ValueError("The L1 input contains missing values.")

    c = float(params["c"])
    T_K = float(params["T"])
    EF_op_eV = float(params["EF_op_eV"])
    rho_ohm_sq = float(params["rho_ohm_sq"])

    gate_EF = np.array([0.0, 0.073, 0.100, 0.200])
    gate_expected = np.array([1.00, 2.00, 2.60, 5.10])
    gate_actual = np.array([correction_factor(x, T_K, c) for x in gate_EF])
    gate_tolerance = np.array([0.002, 0.02, 0.02, 0.03])
    if not np.all(np.abs(gate_actual - gate_expected) <= gate_tolerance):
        raise AssertionError(
            f"Published L1 gates failed: actual={gate_actual}, expected={gate_expected}"
        )

    n_band_recomputed = np.array([n_band(x, T_K, c) for x in data["EF_eV"]])
    source_n_band = data["n_band_cm2"].to_numpy(dtype=float)
    max_source_relative_error = float(
        np.max(np.abs(n_band_recomputed - source_n_band) / source_n_band)
    )
    if max_source_relative_error > 2e-6:
        raise AssertionError(
            "Recomputed band counts do not agree with the supplied L1_data.csv column."
        )

    n_fermi_sweep = np.array([n_fermi(x, T_K, c) for x in data["EF_eV"]])
    correction_sweep = source_n_band / n_fermi_sweep
    if not np.all(np.diff(correction_sweep) > 0):
        raise AssertionError("The correction factor is not monotonic over the supplied sweep.")

    n_band_op = n_band(EF_op_eV, T_K, c)
    n_fermi_op = n_fermi(EF_op_eV, T_K, c)
    n_fermi_op_closed = n_fermi_closed(EF_op_eV, T_K, c)
    closed_form_relative_error = abs(n_fermi_op - n_fermi_op_closed) / n_fermi_op_closed
    if closed_form_relative_error > 1e-5:
        raise AssertionError("Numerical and closed-form Fermi counts disagree.")

    C_op = n_band_op / n_fermi_op
    mobility_band = 1.0 / (ELEMENTARY_CHARGE_C * n_band_op * rho_ohm_sq)
    mobility_corrected = 1.0 / (
        ELEMENTARY_CHARGE_C * n_fermi_op * rho_ohm_sq
    )
    if not np.isclose(mobility_corrected / mobility_band, C_op, rtol=1e-10):
        raise AssertionError("Mobility correction does not equal the carrier correction factor.")

    C2_EF = solve_crossing(2.0, T_K, c)
    C4_EF = solve_crossing(4.0, T_K, c)
    pipeline_commit = detect_commit(args.pipeline_commit)

    template = json.loads((args.data_dir / "results_template.json").read_text())
    template["pipeline_commit"] = pipeline_commit
    template["L1"] = {
        "correction_factor": C_op,
        "n_fermi_op_cm2": n_fermi_op,
        "mobility_corrected_cm2_Vs": mobility_corrected,
    }
    (args.output_dir / "results.json").write_text(
        json.dumps(template, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "commit_hash.txt").write_text(
        pipeline_commit + "\n", encoding="utf-8"
    )

    audit = data.copy()
    audit["n_fermi_cm2"] = n_fermi_sweep
    audit["correction_factor"] = correction_sweep
    audit.to_csv(args.output_dir / "L1_calculations.csv", index=False)

    note = (
        f"G24 L1 result\n"
        f"Exact operating point: E_F = {EF_op_eV:.10f} eV\n"
        f"Band-edge carrier count: n_band = {n_band_op:.6e} cm^-2\n"
        f"Fermi-referenced carrier count: n_F = {n_fermi_op:.6e} cm^-2\n"
        f"Correction factor: C = n_band/n_F = {C_op:.6f}\n"
        f"Band-edge mobility estimate: {mobility_band:.6e} cm^2 V^-1 s^-1\n"
        f"Corrected mobility: {mobility_corrected:.6e} cm^2 V^-1 s^-1\n\n"
        f"Interpretation: the band-edge method reports {C_op:.3f} times the "
        f"Fermi-referenced carrier count, an overestimate of {(C_op - 1.0) * 100:.1f}% "
        f"relative to n_F. At fixed sheet resistivity, mobility is therefore "
        f"underestimated by the same factor. Any carrier-count-normalised sensor "
        f"sensitivity that scales as 1/n should be recalibrated upward by {C_op:.3f} times.\n"
    )
    (args.output_dir / "L1_brief_note.txt").write_text(note, encoding="utf-8")

    run_log = {
        "group": "G24",
        "EF_op_eV": EF_op_eV,
        "gate_checks": [
            {
                "EF_eV": float(x),
                "expected_ratio": float(y),
                "calculated_ratio": float(z),
                "pass": bool(abs(z - y) <= tol),
            }
            for x, y, z, tol in zip(
                gate_EF, gate_expected, gate_actual, gate_tolerance, strict=True
            )
        ],
        "max_source_n_band_relative_error": max_source_relative_error,
        "closed_form_relative_error_at_operating_point": closed_form_relative_error,
        "monotonic_over_supplied_sweep": bool(np.all(np.diff(correction_sweep) > 0)),
        "C2_crossing_EF_eV": C2_EF,
        "C4_crossing_EF_eV": C4_EF,
        "pipeline_commit": pipeline_commit,
    }
    (args.output_dir / "L1_validation.json").write_text(
        json.dumps(run_log, indent=2) + "\n", encoding="utf-8"
    )

    fig, ax = plt.subplots(figsize=(8.2, 5.4), constrained_layout=True)
    ax.plot(
        data["EF_eV"],
        correction_sweep,
        color="#173B64",
        linewidth=2.2,
        marker="o",
        markersize=5.5,
        label="G24 supplied sweep",
    )
    ax.scatter(
        [EF_op_eV],
        [C_op],
        s=85,
        color="#C83E4D",
        edgecolor="white",
        linewidth=0.8,
        zorder=5,
        label="Exact operating point",
    )
    for target, crossing, color in [
        (2.0, C2_EF, "#2A9D8F"),
        (4.0, C4_EF, "#E9A03B"),
    ]:
        ax.axhline(target, color=color, linestyle="--", linewidth=1.0, alpha=0.85)
        ax.axvline(crossing, color=color, linestyle=":", linewidth=1.2, alpha=0.9)
        ax.annotate(
            f"C={target:.0f} at {crossing:.4f} eV",
            xy=(crossing, target),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9,
            color=color,
        )
    ax.annotate(
        f"Operating point\n$E_F$={EF_op_eV:.4f} eV, C={C_op:.3f}",
        xy=(EF_op_eV, C_op),
        xytext=(18, -45),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": "#C83E4D", "lw": 1.2},
        fontsize=9,
        color="#8F2633",
    )
    ax.set_title("G24 L1 carrier-count correction")
    ax.set_xlabel("Fermi level, $E_F$ (eV)")
    ax.set_ylabel("Correction factor, $C=n_{band}/n_F$")
    ax.grid(True, color="#D9E0E7", linewidth=0.8, alpha=0.8)
    ax.legend(frameon=False, loc="upper left")
    ax.set_xlim(float(data["EF_eV"].min()) - 0.008, float(data["EF_eV"].max()) + 0.008)
    ax.set_ylim(0.8, max(6.8, float(correction_sweep.max()) + 0.35))
    fig.savefig(args.output_dir / "L1_factor_sweep.png", dpi=240)
    plt.close(fig)

    readme = (
        "G24 L1 draft outputs\n\n"
        "Run from the group repository root:\n"
        "python analysis.py --data-dir data/regular_G24 --output-dir outputs/L1\n\n"
        "Before checkpoint submission, commit the pipeline and rerun with:\n"
        "python analysis.py --data-dir data/regular_G24 --output-dir outputs/L1 "
        "--pipeline-commit <FULL_GIT_COMMIT_HASH>\n\n"
        "Then copy that hash to commit_hash.txt and confirm it matches results.json.\n"
    )
    (args.output_dir / "README_NEXT.txt").write_text(readme, encoding="utf-8")

    print(note)
    print(f"C=2 crossing: {C2_EF:.10f} eV")
    print(f"C=4 crossing: {C4_EF:.10f} eV")
    print(f"Outputs: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
