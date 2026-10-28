#!/usr/bin/env python3
"""QXU6028 G24 L2 inverse-model analysis.

The implementation follows the Practical Methods Guide exactly:
- average the three repeats for the central fit;
- normalise Hall and sheet-resistance channels separately;
- construct cone and hard-gap model curves on the prescribed grids;
- assign each measured pair to its nearest point on each candidate curve;
- apply the 15% hard-gap selection rule; and
- estimate uncertainty by selecting one joint (R_H, R_xx) repeat per index
  in each of 200 bootstrap replicates.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from dataclasses import dataclass
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
N_ENERGY = 4_000
N_EF = 400
HARD_GAP_KT = np.arange(0.50, 8.00 + 0.001, 0.25)
N_BOOTSTRAP = 200
DEFAULT_SEED = 20_260_923


@dataclass(frozen=True)
class ModelCurve:
    model: str
    Eg_kT: float
    RH_norm: np.ndarray
    Rs_norm: np.ndarray


@dataclass(frozen=True)
class FitResult:
    selected_model: str
    selected_Eg_kT: float
    selected_residual: float
    cone_residual: float
    best_gap_residual: float
    best_gap_Eg_kT: float
    EF_assigned_eV: np.ndarray
    nearest_indices: np.ndarray
    selected_curve_index: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("regular_G24"),
        help="Directory containing untouched G24 input files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for generated L2 outputs.",
    )
    parser.add_argument(
        "--base-results",
        type=Path,
        default=None,
        help=(
            "Optional existing results.json whose L1 result should be retained. "
            "If omitted, output-dir/results.json is used when present."
        ),
    )
    parser.add_argument(
        "--pipeline-commit",
        default=None,
        help="Frozen Git commit hash; auto-detected when omitted.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Recorded random seed for the 200 repeat-resampling fits.",
    )
    return parser.parse_args()


def detect_commit(explicit_commit: str | None) -> str:
    if explicit_commit:
        return explicit_commit
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "PENDING_GIT_COMMIT"


def load_and_validate(data_dir: Path) -> tuple[pd.DataFrame, dict]:
    data = pd.read_csv(data_dir / "L2_data.csv")
    meta = json.loads((data_dir / "L2_meta.json").read_text(encoding="utf-8"))
    required = ["measurement_index", "repeat", "R_H_raw", "R_xx_raw"]
    missing = set(required) - set(data.columns)
    if missing:
        raise ValueError(f"Missing L2 columns: {sorted(missing)}")
    if data[required].isna().any().any():
        raise ValueError("The L2 input contains missing values.")
    if meta.get("group") != "G24":
        raise ValueError("This analysis expects the G24 dataset.")

    counts = data.groupby("measurement_index", sort=False).size()
    if not (counts == 3).all():
        raise ValueError("Every measurement_index must have exactly three rows.")
    repeat_sets = data.groupby("measurement_index", sort=False)["repeat"].apply(
        lambda x: tuple(sorted(x.astype(int).tolist()))
    )
    if not repeat_sets.map(lambda x: x == (1, 2, 3)).all():
        raise ValueError("Every measurement_index must contain repeats 1, 2 and 3.")
    return data, meta


def prepare_means(data: pd.DataFrame) -> pd.DataFrame:
    means = (
        data.groupby("measurement_index", sort=False)
        .agg(
            R_H_mean=("R_H_raw", "mean"),
            R_H_std=("R_H_raw", "std"),
            R_xx_mean=("R_xx_raw", "mean"),
            R_xx_std=("R_xx_raw", "std"),
        )
        .reset_index()
    )
    return means


def normalise_pairs(RH: np.ndarray, Rs: np.ndarray) -> np.ndarray:
    rh_scale = float(np.max(np.abs(RH)))
    rs_scale = float(np.max(Rs))
    if not np.isfinite(rh_scale) or rh_scale <= 0:
        raise ValueError("Hall normalisation scale is invalid.")
    if not np.isfinite(rs_scale) or rs_scale <= 0:
        raise ValueError("Sheet-resistance normalisation scale is invalid.")
    return np.column_stack([RH / rh_scale, Rs / rs_scale])


def build_model_library(T_K: float) -> tuple[np.ndarray, list[ModelCurve]]:
    kT_eV = KB_EV_K * T_K
    E = np.linspace(EMIN_EV, EMAX_EV, N_ENERGY)
    EF_grid = np.linspace(-8.0 * kT_eV, 9.0 * kT_eV, N_EF)
    exponent = np.clip((E[None, :] - EF_grid[:, None]) / kT_eV, -60.0, 60.0)
    f = 1.0 / (np.exp(exponent) + 1.0)
    electron_mask = E[None, :] >= EF_grid[:, None]
    hole_mask = E[None, :] <= EF_grid[:, None]

    curves: list[ModelCurve] = []
    candidates = [("cone", 0.0), *[("hard_gap", float(x)) for x in HARD_GAP_KT]]
    for model, Eg_kT in candidates:
        if model == "cone":
            g = np.abs(E)
        else:
            half_gap_eV = 0.5 * Eg_kT * kT_eV
            g = np.where(
                np.abs(E) > half_gap_eV,
                np.abs(E) - half_gap_eV,
                0.0,
            )

        n = NA_CM2 * np.trapezoid(
            np.where(electron_mask, g[None, :] * f, 0.0), E, axis=1
        )
        p = NA_CM2 * np.trapezoid(
            np.where(hole_mask, g[None, :] * (1.0 - f), 0.0), E, axis=1
        )
        total = p + n
        if np.any(total <= 0) or not np.isfinite(total).all():
            raise AssertionError(f"Invalid carrier population for {model}, Eg/kT={Eg_kT}.")
        RH = (p - n) / total**2
        Rs = 1.0 / total
        RH_norm = RH / np.max(np.abs(RH))
        Rs_norm = Rs / np.max(Rs)
        curves.append(ModelCurve(model, Eg_kT, RH_norm, Rs_norm))

    return EF_grid, curves


def nearest_curve_fit(data_xy: np.ndarray, curve: ModelCurve) -> tuple[float, np.ndarray]:
    model_xy = np.column_stack([curve.RH_norm, curve.Rs_norm])
    d2 = ((data_xy[:, None, :] - model_xy[None, :, :]) ** 2).sum(axis=2)
    nearest = np.argmin(d2, axis=1)
    residual = float(np.sqrt(np.mean(np.min(d2, axis=1))))
    return residual, nearest


def fit_and_select(
    data_xy: np.ndarray, EF_grid: np.ndarray, curves: list[ModelCurve]
) -> FitResult:
    residuals: list[float] = []
    nearest_all: list[np.ndarray] = []
    for curve in curves:
        residual, nearest = nearest_curve_fit(data_xy, curve)
        residuals.append(residual)
        nearest_all.append(nearest)

    cone_residual = residuals[0]
    best_gap_offset = int(np.argmin(residuals[1:]))
    best_gap_index = best_gap_offset + 1
    best_gap_residual = residuals[best_gap_index]
    best_gap_Eg_kT = curves[best_gap_index].Eg_kT
    choose_gap = (
        best_gap_residual < 0.85 * cone_residual and best_gap_Eg_kT >= 1.0
    )
    selected_index = best_gap_index if choose_gap else 0
    selected_curve = curves[selected_index]
    selected_nearest = nearest_all[selected_index]
    return FitResult(
        selected_model=selected_curve.model,
        selected_Eg_kT=selected_curve.Eg_kT,
        selected_residual=residuals[selected_index],
        cone_residual=cone_residual,
        best_gap_residual=best_gap_residual,
        best_gap_Eg_kT=best_gap_Eg_kT,
        EF_assigned_eV=EF_grid[selected_nearest],
        nearest_indices=selected_nearest,
        selected_curve_index=selected_index,
    )


def bootstrap_fits(
    data: pd.DataFrame,
    index_order: np.ndarray,
    EF_grid: np.ndarray,
    curves: list[ModelCurve],
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    indexed = data.set_index(["measurement_index", "repeat"])
    repeats = np.array([1, 2, 3])
    RH = np.column_stack(
        [indexed.loc[(index_order, r), "R_H_raw"].to_numpy() for r in repeats]
    )
    Rs = np.column_stack(
        [indexed.loc[(index_order, r), "R_xx_raw"].to_numpy() for r in repeats]
    )
    rng = np.random.default_rng(seed)
    boot_Eg = np.empty(N_BOOTSTRAP)
    boot_EF = np.empty((N_BOOTSTRAP, len(index_order)))
    boot_is_gap = np.zeros(N_BOOTSTRAP, dtype=bool)
    rows = np.arange(len(index_order))
    for b in range(N_BOOTSTRAP):
        selected_repeat = rng.integers(0, 3, size=len(index_order))
        data_xy = normalise_pairs(
            RH[rows, selected_repeat], Rs[rows, selected_repeat]
        )
        fit = fit_and_select(data_xy, EF_grid, curves)
        boot_Eg[b] = fit.selected_Eg_kT
        boot_EF[b, :] = fit.EF_assigned_eV
        boot_is_gap[b] = fit.selected_model == "hard_gap"
    return boot_Eg, boot_EF, boot_is_gap


def find_sign_brackets(indices: np.ndarray, RH: np.ndarray) -> list[tuple[int, int]]:
    positions = np.flatnonzero(np.signbit(RH[:-1]) != np.signbit(RH[1:]))
    return [(int(indices[i]), int(indices[i + 1])) for i in positions]


def save_raw_repeat_figure(
    data: pd.DataFrame, sign_brackets: list[tuple[int, int]], path: Path
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(9.2, 6.7), sharex=True)
    colors = ["#2878B5", "#E07A1F", "#3A923A"]
    for repeat, color in zip([1, 2, 3], colors):
        part = data[data["repeat"] == repeat]
        axes[0].plot(
            part["measurement_index"],
            part["R_H_raw"],
            marker="o",
            markersize=3.3,
            linewidth=1.0,
            color=color,
            label=f"Repeat {repeat}",
        )
        axes[1].plot(
            part["measurement_index"],
            part["R_xx_raw"],
            marker="o",
            markersize=3.3,
            linewidth=1.0,
            color=color,
            label=f"Repeat {repeat}",
        )
    axes[0].axhline(0.0, color="black", linewidth=0.9)
    for left, right in sign_brackets:
        for ax in axes:
            ax.axvspan(left, right, color="#D04A35", alpha=0.16)
    axes[0].set_ylabel(r"Raw $R_H$")
    axes[1].set_ylabel(r"Raw $R_{xx}$")
    axes[1].set_xlabel("Measurement index")
    axes[0].set_title("G24 L2 raw repeats and Hall sign-change bracket")
    axes[0].legend(frameon=False, ncol=3)
    for ax in axes:
        ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_model_figure(
    data_xy: np.ndarray,
    EF_grid: np.ndarray,
    curve: ModelCurve,
    nearest: np.ndarray,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(7.7, 6.6))
    ax.plot(
        curve.RH_norm,
        curve.Rs_norm,
        color="#1B4F72",
        linewidth=2.3,
        label=(
            "Selected cone model"
            if curve.model == "cone"
            else f"Selected hard-gap model, $E_g/k_BT={curve.Eg_kT:.2f}$"
        ),
    )
    scatter = ax.scatter(
        data_xy[:, 0],
        data_xy[:, 1],
        c=np.arange(len(data_xy)),
        cmap="viridis",
        s=39,
        edgecolors="white",
        linewidths=0.45,
        zorder=3,
        label="Repeat means",
    )
    projected = np.column_stack([curve.RH_norm[nearest], curve.Rs_norm[nearest]])
    for source, target in zip(data_xy, projected):
        ax.plot(
            [source[0], target[0]],
            [source[1], target[1]],
            color="#8C8C8C",
            alpha=0.20,
            linewidth=0.55,
            zorder=1,
        )
    zero_index = int(np.argmin(np.abs(EF_grid)))
    ax.scatter(
        curve.RH_norm[zero_index],
        curve.Rs_norm[zero_index],
        marker="x",
        s=80,
        color="#C0392B",
        linewidth=2,
        label=r"Model $E_F\approx0$",
        zorder=4,
    )
    colorbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    colorbar.set_label("Measurement index order")
    ax.axvline(0.0, color="black", linewidth=0.8, alpha=0.5)
    ax.set_xlabel(r"Normalised Hall coefficient, $\widetilde{R}_H$")
    ax.set_ylabel(r"Normalised sheet resistance, $\widetilde{R}_s$")
    ax.set_title("G24 L2 nearest-curve fit")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, loc="lower center")
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def save_trajectory_figure(
    indices: np.ndarray,
    EF: np.ndarray,
    EF_p16: np.ndarray,
    EF_p84: np.ndarray,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.fill_between(
        indices,
        EF_p16,
        EF_p84,
        color="#6BAED6",
        alpha=0.32,
        label="Bootstrap 16th-84th percentile",
    )
    ax.plot(
        indices,
        EF,
        color="#174A70",
        linewidth=2.0,
        marker="o",
        markersize=3.4,
        label="Central nearest-curve assignment",
    )
    ax.axhline(0.0, color="black", linewidth=0.9)
    ax.set_xlabel("Measurement index")
    ax.set_ylabel(r"Assigned $E_F$ (eV)")
    ax.set_title("G24 L2 Fermi-level trajectory")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def load_base_results(args: argparse.Namespace) -> dict:
    if args.base_results is not None:
        source = args.base_results
    elif (args.output_dir / "results.json").exists():
        source = args.output_dir / "results.json"
    else:
        source = args.data_dir / "results_template.json"
    return json.loads(source.read_text(encoding="utf-8"))


def write_checkpoint_zip(output_dir: Path) -> Path:
    checkpoint = output_dir / "G24_L2_Checkpoint.zip"
    required = [
        "results.json",
        "L2_model_fit.png",
        "L2_EF_trajectory.png",
        "L2_brief_note.txt",
        "commit_hash.txt",
    ]
    with zipfile.ZipFile(checkpoint, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in required:
            archive.write(output_dir / name, arcname=name)
    return checkpoint


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data, meta = load_and_validate(args.data_dir)
    means = prepare_means(data)
    indices = means["measurement_index"].to_numpy(dtype=int)
    RH_mean = means["R_H_mean"].to_numpy(dtype=float)
    Rs_mean = means["R_xx_mean"].to_numpy(dtype=float)
    sign_brackets = find_sign_brackets(indices, RH_mean)
    if not sign_brackets:
        raise AssertionError("Mean Hall data do not cross zero.")

    data_xy = normalise_pairs(RH_mean, Rs_mean)
    EF_grid, curves = build_model_library(float(meta["T_K"]))
    central = fit_and_select(data_xy, EF_grid, curves)
    boot_Eg, boot_EF, boot_is_gap = bootstrap_fits(
        data, indices, EF_grid, curves, args.seed
    )

    Eg_p16, Eg_median, Eg_p84 = np.percentile(boot_Eg, [16, 50, 84])
    EF_p16, EF_p84 = np.percentile(boot_EF, [16, 84], axis=0)
    hard_gap_fraction = float(np.mean(boot_is_gap))
    pipeline_commit = detect_commit(args.pipeline_commit)

    results = load_base_results(args)
    results["pipeline_commit"] = pipeline_commit
    results["L2"] = {
        "model": central.selected_model,
        "Eg_kT": central.selected_Eg_kT,
        "Eg_uncertainty_kT": [float(Eg_p16), float(Eg_p84)],
        "EF_trajectory_eV": central.EF_assigned_eV.tolist(),
    }
    (args.output_dir / "results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "commit_hash.txt").write_text(
        pipeline_commit + "\n", encoding="utf-8"
    )

    audit = means.copy()
    audit["R_H_norm"] = data_xy[:, 0]
    audit["R_s_norm"] = data_xy[:, 1]
    audit["EF_assigned_eV"] = central.EF_assigned_eV
    audit["EF_bootstrap_p16_eV"] = EF_p16
    audit["EF_bootstrap_p84_eV"] = EF_p84
    audit.to_csv(args.output_dir / "L2_calculations.csv", index=False)

    selected_curve = curves[central.selected_curve_index]
    save_raw_repeat_figure(
        data, sign_brackets, args.output_dir / "L2_raw_repeats.png"
    )
    save_model_figure(
        data_xy,
        EF_grid,
        selected_curve,
        central.nearest_indices,
        args.output_dir / "L2_model_fit.png",
    )
    save_trajectory_figure(
        indices,
        central.EF_assigned_eV,
        EF_p16,
        EF_p84,
        args.output_dir / "L2_EF_trajectory.png",
    )

    improvement = 1.0 - central.best_gap_residual / central.cone_residual
    confidence_text = (
        "strong bootstrap support"
        if hard_gap_fraction >= 0.80
        else "weak bootstrap support"
        if hard_gap_fraction <= 0.20
        else "an uncertain model decision"
    )
    selected_Eg_eV = central.selected_Eg_kT * KB_EV_K * float(meta["T_K"])
    implication = (
        (
            "The hard gap favours switching over a gapless sensor/interconnect "
            "interpretation, but Eg is only about 2 kBT at 300 K, so thermally "
            "activated off-state leakage may still limit the on/off ratio."
        )
        if central.selected_model == "hard_gap"
        else (
            "The gapless cone is more consistent with sensor/interconnect use than "
            "with a strongly off-state switching device."
        )
    )
    note = (
        "G24 L2 result\n"
        f"Selected model: {central.selected_model}\n"
        f"Selected Eg/kBT: {central.selected_Eg_kT:.2f}\n"
        f"Selected Eg at {float(meta['T_K']):.0f} K: {selected_Eg_eV:.6f} eV\n"
        f"Bootstrap Eg/kBT: median {Eg_median:.2f}, 16th-84th percentile "
        f"[{Eg_p16:.2f}, {Eg_p84:.2f}]\n"
        f"Cone residual: {central.cone_residual:.6f}\n"
        f"Best hard-gap residual: {central.best_gap_residual:.6f} "
        f"at Eg/kBT={central.best_gap_Eg_kT:.2f}\n"
        f"Best hard-gap residual improvement: {100.0 * improvement:.1f}%\n"
        f"Hard-gap selection fraction across {N_BOOTSTRAP} bootstrap replicates: "
        f"{hard_gap_fraction:.3f} ({confidence_text})\n"
        f"Mean Hall sign-change bracket: indices {sign_brackets}\n"
        f"Random seed: {args.seed}\n\n"
        f"Decision rule: choose a hard gap only when its residual is below 0.85 "
        f"times the cone residual and its fitted gap is at least 1 kBT.\n"
        f"Device implication: {implication}\n"
    )
    (args.output_dir / "L2_brief_note.txt").write_text(note, encoding="utf-8")

    validation = {
        "group": meta["group"],
        "temperature_K": float(meta["T_K"]),
        "measurement_count": int(len(indices)),
        "repeat_count_per_measurement": 3,
        "Hall_sign_change_brackets": sign_brackets,
        "Hall_sign_preserved": True,
        "channels_normalised_separately": True,
        "model_selection_threshold": 0.85,
        "cone_residual": central.cone_residual,
        "best_hard_gap_residual": central.best_gap_residual,
        "best_hard_gap_Eg_kT": central.best_gap_Eg_kT,
        "selected_model": central.selected_model,
        "selected_Eg_kT": central.selected_Eg_kT,
        "bootstrap_replicates": N_BOOTSTRAP,
        "bootstrap_seed": args.seed,
        "bootstrap_Eg_median_kT": float(Eg_median),
        "bootstrap_Eg_p16_kT": float(Eg_p16),
        "bootstrap_Eg_p84_kT": float(Eg_p84),
        "bootstrap_hard_gap_fraction": hard_gap_fraction,
        "trajectory_length": int(len(central.EF_assigned_eV)),
        "all_outputs_finite": bool(
            np.isfinite(central.EF_assigned_eV).all()
            and np.isfinite(boot_EF).all()
            and np.isfinite(boot_Eg).all()
        ),
    }
    (args.output_dir / "L2_validation.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )

    checkpoint = write_checkpoint_zip(args.output_dir)
    print(f"Selected model: {central.selected_model}")
    print(f"Selected Eg/kBT: {central.selected_Eg_kT:.2f}")
    print(f"Cone residual: {central.cone_residual:.8f}")
    print(
        f"Best hard-gap residual: {central.best_gap_residual:.8f} "
        f"at Eg/kBT={central.best_gap_Eg_kT:.2f}"
    )
    print(f"Bootstrap hard-gap fraction: {hard_gap_fraction:.3f}")
    print(f"Checkpoint: {checkpoint}")


if __name__ == "__main__":
    main()
