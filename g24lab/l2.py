"""Dataset-independent Hall/sheet-resistance inverse problem.

The energy and Fermi-level grids are the course grids. Refined mode searches
the complete allowed gap interval before local refinement; it never uses a
regular/blind-specific fitted-gap window. Course mode uses the 0.25-kBT grid.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import l2_core as core

GAP_MIN = 0.50
GAP_MAX = 8.00
N_BOOTSTRAP = 200
DEFAULT_SEED = 20260923


def build_curves(temperature: float, gaps: np.ndarray):
    """Exactly the 4000-energy/400-EF Fermi-window model; e=mu=c=1."""
    kT = core.KB_EV_K * temperature
    energy = np.linspace(core.EMIN_EV, core.EMAX_EV, core.N_ENERGY)
    ef = np.linspace(-8 * kT, 9 * kT, core.N_EF)
    f = 1 / (np.exp(np.clip((energy[None, :] - ef[:, None]) / kT, -60, 60)) + 1)
    weights = np.ones(len(energy)) * ((energy[-1] - energy[0]) / (len(energy) - 1))
    weights[[0, -1]] *= 0.5
    electrons = f * (energy[None, :] >= ef[:, None]) * weights
    holes = (1 - f) * (energy[None, :] <= ef[:, None]) * weights
    dos = np.maximum(np.abs(energy)[None, :] - np.asarray(gaps)[:, None] * kT / 2, 0)
    n = core.NA_CM2 * (dos @ electrons.T)
    p = core.NA_CM2 * (dos @ holes.T)
    total = p + n
    hall = (p - n) / total**2
    sheet = 1 / total
    return ef, hall / np.max(np.abs(hall), axis=1)[:, None], sheet / np.max(sheet, axis=1)[:, None]


@lru_cache(maxsize=6)
def library(temperature: float, mode: str):
    step = 0.25 if mode == "course" else 0.01
    gaps = np.round(np.arange(GAP_MIN, GAP_MAX + step / 2, step), 2)
    ef, hall, sheet = build_curves(temperature, np.r_[0.0, gaps])
    return ef, gaps, hall[0], sheet[0], hall[1:], sheet[1:]


def nearest(data_xy, hall, sheet):
    d2 = (data_xy[:, None, 0] - hall[None, :])**2 + (data_xy[:, None, 1] - sheet[None, :])**2
    indices = np.argmin(d2, axis=1)
    return float(np.sqrt(np.mean(d2[np.arange(len(data_xy)), indices]))), indices


def fit_library(data_xy, gaps, hall, sheet):
    """Bounded-memory nearest-curve RMS, preserving a common EF for both channels."""
    residuals = np.empty(len(gaps))
    for start in range(0, len(gaps), 48):
        h = hall[start:start + 48]
        s = sheet[start:start + 48]
        d2 = (h[:, None, :] - data_xy[None, :, 0, None])**2
        d2 += (s[:, None, :] - data_xy[None, :, 1, None])**2
        residuals[start:start + len(h)] = np.sqrt(np.mean(np.min(d2, axis=2), axis=1))
    best = int(np.argmin(residuals))
    _, indices = nearest(data_xy, hall[best], sheet[best])
    return best, float(residuals[best]), indices, residuals


def select_hard_gap(gap: float, gap_residual: float, cone_residual: float) -> bool:
    return bool(gap >= 1.0 and gap_residual < 0.85 * cone_residual)


def fit_central(data_xy, temperature: float, mode: str = "refined"):
    ef, gaps, cone_h, cone_s, hall, sheet = library(float(temperature), mode)
    cone_residual, cone_indices = nearest(data_xy, cone_h, cone_s)
    j, gap_residual, gap_indices, residuals = fit_library(data_xy, gaps, hall, sheet)
    scans = [pd.DataFrame({"Eg_kT": gaps, "rms_residual": residuals, "grid": "global"})]
    best_gap = float(gaps[j])
    best_h, best_s = hall[j], sheet[j]
    if mode == "refined":
        for half_width, step, digits, name in ((0.02, 0.001, 3, "local"), (0.003, 0.0001, 4, "final")):
            local = np.round(np.arange(max(GAP_MIN, best_gap - half_width), min(GAP_MAX, best_gap + half_width) + step / 2, step), digits)
            _, h, s = build_curves(temperature, local)
            j, gap_residual, gap_indices, residuals = fit_library(data_xy, local, h, s)
            best_gap = float(local[j])
            best_h, best_s = h[j], s[j]
            scans.append(pd.DataFrame({"Eg_kT": local, "rms_residual": residuals, "grid": name}))
    choose = select_hard_gap(best_gap, gap_residual, cone_residual)
    return {
        "EF_grid": ef, "model": "hard_gap" if choose else "cone",
        "selected_gap": best_gap if choose else 0.0,
        "selected_residual": gap_residual if choose else cone_residual,
        "nearest": gap_indices if choose else cone_indices,
        "hall": best_h if choose else cone_h, "sheet": best_s if choose else cone_s,
        "best_gap": best_gap, "gap_residual": gap_residual, "cone_residual": cone_residual,
        "scan": pd.concat(scans, ignore_index=True), "at_gap_domain_boundary": best_gap in (GAP_MIN, GAP_MAX),
    }


def bootstrap(data, indices, temperature, mode, seed):
    ef, gaps, cone_h, cone_s, hall, sheet = library(float(temperature), mode)
    indexed = data.set_index(["measurement_index", "repeat"])
    rh = np.column_stack([indexed.loc[(indices, r), "R_H_raw"].to_numpy() for r in (1, 2, 3)])
    rs = np.column_stack([indexed.loc[(indices, r), "R_xx_raw"].to_numpy() for r in (1, 2, 3)])
    rng = np.random.default_rng(seed)
    rows = np.arange(len(indices))
    boot_gaps = np.empty(N_BOOTSTRAP)
    trajectories = np.empty((N_BOOTSTRAP, len(indices)))
    is_gap = np.empty(N_BOOTSTRAP, dtype=bool)
    for b in range(N_BOOTSTRAP):
        repeat = rng.integers(0, 3, len(indices))
        xy = core.normalise_pairs(rh[rows, repeat], rs[rows, repeat])
        cone_r, cone_j = nearest(xy, cone_h, cone_s)
        gap_j, gap_r, nearest_j, _ = fit_library(xy, gaps, hall, sheet)
        is_gap[b] = select_hard_gap(float(gaps[gap_j]), gap_r, cone_r)
        boot_gaps[b] = gaps[gap_j] if is_gap[b] else 0.0
        trajectories[b] = ef[nearest_j if is_gap[b] else cone_j]
    return boot_gaps, trajectories, is_gap


def save_fit(xy, indices, fit, path, label):
    fig, ax = plt.subplots(figsize=(9.0, 6.4), constrained_layout=True)
    ax.plot(fit["hall"], fit["sheet"], lw=2.7, color="#174A70", label=f'{fit["model"]}: Eg/kBT={fit["selected_gap"]:.4f}, RMS={fit["selected_residual"]:.5f}')
    ax.plot(xy[:, 0], xy[:, 1], "--", lw=1.7, color="#E67E22", label="Measured trajectory (connected in MIO order)")
    points = ax.scatter(xy[:, 0], xy[:, 1], c=indices, cmap="viridis", s=40, edgecolors="white", linewidths=0.4, zorder=3)
    fig.colorbar(points, ax=ax, label="Measurement index order (MIO)")
    ax.axvline(0, color="grey", lw=0.8)
    ax.set(xlabel=r"Normalised Hall coefficient, $\widetilde{R}_H$", ylabel=r"Normalised sheet resistance, $\widetilde{R}_s$", title=f"G24 {label}: joint Hall/sheet-resistance fit")
    ax.grid(alpha=0.2)
    ax.legend(loc="lower center", fontsize=8)
    fig.savefig(path, dpi=210)
    plt.close(fig)


def save_sweep(scan, fit, path, label):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), constrained_layout=True)
    for ax, local in zip(axes, (False, True)):
        table = scan if not local else scan.loc[np.abs(scan.Eg_kT - fit["best_gap"]) <= 0.08]
        table = table.sort_values("Eg_kT").drop_duplicates("Eg_kT")
        ax.plot(table.Eg_kT, table.rms_residual, lw=1.5, color="#174A70", label="Hard-gap RMS")
        ax.scatter([fit["best_gap"]], [fit["gap_residual"]], marker="*", s=90, color="#C23C45", label=f'Best gap {fit["best_gap"]:.4f}')
        if not local:
            ax.axhline(fit["cone_residual"], color="grey", ls="--", label="Cone RMS")
            ax.axhline(0.85 * fit["cone_residual"], color="#2A7F62", ls=":", label="15% selection threshold")
        ax.set(xlabel=r"Gap $E_g/k_BT$", ylabel="Joint nearest-curve RMS", title="Full allowed interval" if not local else "Refined minimum")
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8)
    fig.suptitle(f"G24 {label}: gap-residual scan")
    fig.savefig(path, dpi=200)
    plt.close(fig)


def save_mio(xy, indices, fit, path, label):
    fig, ax = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
    for channel, color, name in ((0, "#176C9C", "Hall"), (1, "#D57B23", "Sheet resistance")):
        ax.plot(indices, xy[:, channel], "o-", ms=3, color=color, label=f"Measured {name}")
        curve = fit["hall"] if channel == 0 else fit["sheet"]
        ax.plot(indices, curve[fit["nearest"]], "--", lw=1.2, color=color, alpha=0.8, label=f"Joint-fit {name}")
    ax.axhline(0, lw=0.7, color="grey")
    ax.set(xlabel="Measurement index order (MIO)", ylabel="Independently normalised response", title=f"G24 {label}: Hall and sheet resistance by measurement index")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8, ncol=2)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def run(data_dir: Path, output_dir: Path, pipeline_commit: str, mode="refined", seed=DEFAULT_SEED):
    output_dir.mkdir(parents=True, exist_ok=True)
    data, meta = core.load_and_validate(data_dir)
    means = core.prepare_means(data)
    indices = means.measurement_index.to_numpy(int)
    xy = core.normalise_pairs(means.R_H_mean.to_numpy(), means.R_xx_mean.to_numpy())
    temperature = float(meta["T_K"])
    fit = fit_central(xy, temperature, mode)
    boot_gap, boot_ef, boot_is_gap = bootstrap(data, indices, temperature, mode, seed)
    low, median, high = np.percentile(boot_gap, [16, 50, 84])
    ef_low, ef_high = np.percentile(boot_ef, [16, 84], axis=0)
    assigned = fit["EF_grid"][fit["nearest"]]
    results_path = output_dir / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    results["pipeline_commit"] = pipeline_commit
    results["L2"] = {"model": fit["model"], "Eg_kT": fit["selected_gap"], "Eg_uncertainty_kT": [float(low), float(high)], "EF_trajectory_eV": assigned.tolist()}
    results_path.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    means["R_H_norm"], means["R_s_norm"] = xy[:, 0], xy[:, 1]
    means["EF_assigned_eV"] = assigned
    means["EF_bootstrap_p16_eV"], means["EF_bootstrap_p84_eV"] = ef_low, ef_high
    means.to_csv(output_dir / "L2_calculations.csv", index=False)
    scan = fit["scan"].copy()
    scan["residual_sum_of_squares"] = len(indices) * scan.rms_residual**2
    scan.to_csv(output_dir / "L2_gap_residual_sweep.csv", index=False)
    scan.loc[scan.grid != "global"].to_csv(output_dir / "L2_refined_gap_sweep.csv", index=False)
    pd.DataFrame({"replicate": np.arange(1, N_BOOTSTRAP + 1), "Eg_kT": boot_gap, "hard_gap": boot_is_gap}).to_csv(output_dir / "L2_bootstrap_gaps.csv", index=False)
    pd.DataFrame(boot_ef, columns=[f"MIO_{i}" for i in indices]).to_csv(output_dir / "L2_bootstrap_EF.csv", index=False)
    label = str(meta.get("dataset_set", "data"))
    save_fit(xy, indices, fit, output_dir / "L2_model_fit.png", label)
    save_sweep(scan, fit, output_dir / "L2_gap_residual_sweep.png", label)
    save_mio(xy, indices, fit, output_dir / "L2_RH_Rs_vs_measurement_index.png", label)
    core.save_raw_repeat_figure(data, core.find_sign_brackets(indices, means.R_H_mean.to_numpy()), output_dir / "L2_raw_repeats.png")
    core.save_trajectory_figure(indices, assigned, ef_low, ef_high, output_dir / "L2_EF_trajectory.png")
    note = (
        f"G24 {label}: shared L2 pipeline ({mode})\nSelected model: {fit['model']}\n"
        f"Selected Eg/kBT: {fit['selected_gap']:.4f}\nEg at {temperature:g} K: {fit['selected_gap'] * core.KB_EV_K * temperature:.8f} eV\n"
        f"Cone RMS: {fit['cone_residual']:.10f}\nBest hard-gap RMS: {fit['gap_residual']:.10f}\n"
        f"Bootstrap median / p16 / p84 kBT: {median:.6f} / {low:.6f} / {high:.6f}\n"
        f"Hard-gap selection fraction: {boot_is_gap.mean():.3f}\nBootstrap replicates: {N_BOOTSTRAP}; seed: {seed}\n"
        "Gap domain: 0.50--8.00 kBT for both datasets; no fitted-gap-specific windows.\n"
        "Refined mode scans the whole domain at 0.01 kBT, then 0.001 and 0.0001 locally.\n"
        "Course mode uses the published 0.25-kBT grid. Refined-mode permission is based on the user's earlier clarification, not an independently verified written course amendment.\n"
        "Hall signs, separate normalisation, joint nearest-EF assignment and the 15% selection rule are retained.\n"
        "This is a new replay, not a claim about the historic frozen blind-test pipeline.\n"
    )
    (output_dir / "L2_brief_note.txt").write_text(note, encoding="utf-8")
    validation = {
        "group": "G24", "dataset_set": label, "gap_mode": mode, "gap_domain_kT": [GAP_MIN, GAP_MAX],
        "energy_grid_points": core.N_ENERGY, "EF_grid_points": core.N_EF, "trajectory_length": len(indices),
        "cone_residual": fit["cone_residual"], "best_hard_gap_residual": fit["gap_residual"],
        "selected_residual": fit["selected_residual"], "selected_gap_kT": fit["selected_gap"],
        "bootstrap_replicates": N_BOOTSTRAP, "bootstrap_seed": seed, "bootstrap_gap_median_kT": float(median),
        "bootstrap_gap_p16_kT": float(low), "bootstrap_gap_p84_kT": float(high),
        "bootstrap_hard_gap_fraction": float(boot_is_gap.mean()), "gap_boundary_warning": fit["at_gap_domain_boundary"],
        "all_outputs_finite": bool(np.isfinite(assigned).all() and np.isfinite(boot_gap).all() and np.isfinite(boot_ef).all()),
    }
    (output_dir / "L2_validation.json").write_text(json.dumps(validation, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(note, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pipeline-commit", required=True)
    parser.add_argument("--gap-mode", choices=("course", "refined"), default="refined")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    run(args.data_dir, args.output_dir, args.pipeline_commit, args.gap_mode, args.seed)
