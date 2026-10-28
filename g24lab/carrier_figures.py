#!/usr/bin/env python3
"""Generate four supplementary G24 carrier-transport figures.

The official L1 checkpoint still requires the carrier-count correction plot.
These supplementary figures use the selected L2 transport model to show the
electron-like population, hole-like population, normalised Hall coefficient,
and normalised sheet resistance as functions of Fermi level.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


KB_EV_K = 8.617333e-5
NA_CM2 = 3.816e15
EMIN_EV = -2.5
EMAX_EV = 2.5
N_ENERGY_FIT = 4_000
N_EF_FIT = 400
N_ENERGY_PLOT = 40_001
N_EF_PLOT = 600


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("regular_G24"))
    parser.add_argument("--results", type=Path, default=Path("outputs/results.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser.parse_args()


def build_transport_model(
    T_K: float,
    c_per_eV_atom: float,
    Eg_kT: float,
    n_energy: int,
    n_ef: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return EF, n, p, normalised RH and normalised Rs for a hard-gap model."""
    kT_eV = KB_EV_K * T_K
    E = np.linspace(EMIN_EV, EMAX_EV, n_energy)
    EF = np.linspace(-8.0 * kT_eV, 9.0 * kT_eV, n_ef)
    half_gap_eV = 0.5 * Eg_kT * kT_eV
    g = c_per_eV_atom * np.maximum(np.abs(E) - half_gap_eV, 0.0)
    n = np.empty_like(EF)
    p = np.empty_like(EF)
    for j, ef in enumerate(EF):
        exponent = np.clip((E - ef) / kT_eV, -60.0, 60.0)
        f = 1.0 / (np.exp(exponent) + 1.0)
        n[j] = NA_CM2 * np.trapezoid(np.where(E >= ef, g * f, 0.0), E)
        p[j] = NA_CM2 * np.trapezoid(np.where(E <= ef, g * (1.0 - f), 0.0), E)
    total = n + p
    RH = (p - n) / total**2
    Rs = 1.0 / total
    RH_norm = RH / np.max(np.abs(RH))
    Rs_norm = Rs / np.max(Rs)
    return EF, n, p, RH_norm, Rs_norm


def style_axis(ax: plt.Axes, EF_op_eV: float) -> None:
    ax.axvline(0.0, color="#6B7280", linestyle="--", linewidth=1.1, label="Charge neutrality")
    ax.axvline(
        EF_op_eV,
        color="#C83E4D",
        linestyle=":",
        linewidth=1.5,
        label=f"L1 operating point: {EF_op_eV:.4f} eV",
    )
    ax.grid(True, color="#D9E0E7", linewidth=0.8, alpha=0.75)
    ax.set_xlabel("Fermi level, $E_F$ (eV)")
    ax.legend(frameon=False, fontsize=8.5, loc="best")


def save_population_figure(
    EF: np.ndarray,
    values: np.ndarray,
    EF_op_eV: float,
    color: str,
    title: str,
    symbol: str,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.4), constrained_layout=True)
    ax.plot(EF, values, color=color, linewidth=2.4)
    y_op = float(np.interp(EF_op_eV, EF, values))
    ax.scatter(
        [EF_op_eV],
        [y_op],
        s=68,
        color="#C83E4D",
        edgecolor="white",
        linewidth=0.8,
        zorder=4,
    )
    ax.set_title(title)
    ax.set_ylabel(f"{symbol} (cm$^{{-2}}$)")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    style_axis(ax, EF_op_eV)
    fig.savefig(path, dpi=240)
    plt.close(fig)


def save_transport_figure(
    EF: np.ndarray,
    model_values: np.ndarray,
    assigned_EF: np.ndarray,
    measured_values: np.ndarray,
    measured_error: np.ndarray,
    EF_op_eV: float,
    color: str,
    title: str,
    ylabel: str,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.4), constrained_layout=True)
    ax.plot(EF, model_values, color=color, linewidth=2.4, label="Selected transport model")
    ax.errorbar(
        assigned_EF,
        measured_values,
        yerr=measured_error,
        fmt="o",
        ms=3.8,
        color="#30343B",
        ecolor="#9AA1A9",
        elinewidth=0.75,
        capsize=1.5,
        alpha=0.78,
        label="Measured means at fitted $E_F$",
    )
    ax.axhline(0.0, color="#A5ABB2", linewidth=0.8)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    style_axis(ax, EF_op_eV)
    fig.savefig(path, dpi=240)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    params = json.loads((args.data_dir / "L1_params.json").read_text(encoding="utf-8"))
    meta = json.loads((args.data_dir / "L2_meta.json").read_text(encoding="utf-8"))
    results = json.loads(args.results.read_text(encoding="utf-8"))
    data = pd.read_csv(args.data_dir / "L2_data.csv")

    if params.get("group") != "G24" or meta.get("group") != "G24":
        raise ValueError("This script expects a G24 dataset.")
    if results.get("L2", {}).get("model") not in {"hard_gap", "cone"}:
        raise ValueError("The supplied results.json must select cone or hard_gap.")

    T_K = float(meta["T_K"])
    c = float(params["c"])
    EF_op_eV = float(params["EF_op_eV"])
    Eg_kT = float(results["L2"]["Eg_kT"])
    EF_fit, _, _, RH_fit, Rs_fit = build_transport_model(
        T_K, c, Eg_kT, N_ENERGY_FIT, N_EF_FIT
    )
    EF, n, p, RH_norm, Rs_norm = build_transport_model(
        T_K, c, Eg_kT, N_ENERGY_PLOT, N_EF_PLOT
    )

    means = (
        data.groupby("measurement_index", sort=False)
        .agg(
            R_H_mean=("R_H_raw", "mean"),
            R_H_std=("R_H_raw", "std"),
            R_s_mean=("R_xx_raw", "mean"),
            R_s_std=("R_xx_raw", "std"),
        )
        .reset_index()
    )
    rh_scale = float(means["R_H_mean"].abs().max())
    rs_scale = float(means["R_s_mean"].max())
    measured_RH = means["R_H_mean"].to_numpy(float) / rh_scale
    measured_Rs = means["R_s_mean"].to_numpy(float) / rs_scale
    measured_RH_std = means["R_H_std"].to_numpy(float) / rh_scale
    measured_Rs_std = means["R_s_std"].to_numpy(float) / rs_scale

    data_xy = np.column_stack([measured_RH, measured_Rs])
    model_xy = np.column_stack([RH_fit, Rs_fit])
    d2 = ((data_xy[:, None, :] - model_xy[None, :, :]) ** 2).sum(axis=2)
    nearest = np.argmin(d2, axis=1)
    assigned_EF = EF_fit[nearest]

    save_population_figure(
        EF,
        n,
        EF_op_eV,
        "#276FBF",
        f"G24 electron-like population ($E_g/k_BT={Eg_kT:.3f}$)",
        "$n$",
        args.output_dir / "L1_electron_population.png",
    )
    save_population_figure(
        EF,
        p,
        EF_op_eV,
        "#D95D39",
        f"G24 hole-like population ($E_g/k_BT={Eg_kT:.3f}$)",
        "$p$",
        args.output_dir / "L1_hole_population.png",
    )
    save_transport_figure(
        EF,
        RH_norm,
        assigned_EF,
        measured_RH,
        measured_RH_std,
        EF_op_eV,
        "#2A9D8F",
        "G24 normalised Hall coefficient",
        "Normalised Hall coefficient, $R_H$",
        args.output_dir / "L1_hall_coefficient.png",
    )
    save_transport_figure(
        EF,
        Rs_norm,
        assigned_EF,
        measured_Rs,
        measured_Rs_std,
        EF_op_eV,
        "#6F4E7C",
        "G24 normalised sheet resistance",
        "Normalised sheet resistance, $R_s$",
        args.output_dir / "L1_sheet_resistance.png",
    )

    note = (
        "G24 supplementary carrier-transport figures\n"
        f"Model: {results['L2']['model']}, Eg/kBT = {Eg_kT:.3f}, T = {T_K:.1f} K\n"
        f"L1 operating point marked at EF = {EF_op_eV:.10f} eV\n\n"
        "The electron-like and hole-like populations use the course Fermi-window "
        "integrals with the G24 density-of-states scale. The Hall coefficient and "
        "sheet resistance follow RH=(p-n)/(p+n)^2 and Rs=1/(p+n), then each curve "
        "is normalised according to the L2 method. Measured repeat means are "
        "projected to their nearest points on the joint RH-Rs model curve.\n\n"
        "These four plots are supplementary. They do not replace the official L1 "
        "factor-sweep figure C(EF), which remains in the checkpoint.\n"
    )
    (args.output_dir / "L1_four_figures_note.txt").write_text(note, encoding="utf-8")

    audit = {
        "group": "G24",
        "model": results["L2"]["model"],
        "Eg_kT": Eg_kT,
        "temperature_K": T_K,
        "EF_op_eV": EF_op_eV,
        "measurement_count": int(len(means)),
        "fit_energy_grid_points": N_ENERGY_FIT,
        "fit_EF_grid_points": N_EF_FIT,
        "plot_energy_grid_points": N_ENERGY_PLOT,
        "plot_EF_grid_points": N_EF_PLOT,
        "files": [
            "L1_electron_population.png",
            "L1_hole_population.png",
            "L1_hall_coefficient.png",
            "L1_sheet_resistance.png",
        ],
    }
    (args.output_dir / "L1_four_figures_validation.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )

    print(note)


if __name__ == "__main__":
    main()
