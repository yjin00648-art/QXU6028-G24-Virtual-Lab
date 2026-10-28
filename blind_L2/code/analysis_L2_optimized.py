#!/usr/bin/env python3
"""G24 L2 fit with a refined hard-gap parameter search.

This variant keeps the published carrier equations, independent channel
normalisation, 400-point EF grid, nearest-point residual and 15% model rule.
Only the hard-gap parameter grid is refined, following the teacher's updated
instruction to vary Eg to minimise the residual.

Place this file beside analysis_L2.py and run it from the project root.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import analysis_L2 as core


# The broad 0.25-kBT course scan gives 3.50 for the blind dataset.  Keep the
# same two-stage refinement used for the regular data, but centre its local
# window on that blind coarse result.
CENTRAL_GAP_MIN_KT = 3.20
CENTRAL_GAP_MAX_KT = 3.80
CENTRAL_GAP_STEP_KT = 0.001
FINAL_GAP_HALF_WIDTH_KT = 0.003
FINAL_GAP_STEP_KT = 0.0001
BOOTSTRAP_GAP_MIN_KT = 2.50
BOOTSTRAP_GAP_MAX_KT = 4.50
BOOTSTRAP_GAP_STEP_KT = 0.01
N_BOOTSTRAP = 200
DEFAULT_SEED = 20_260_923


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("regular_G24"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--base-results", type=Path, default=None)
    parser.add_argument("--pipeline-commit", default=None)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
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


def build_gap_curves(
    T_K: float, gap_values: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return EF grid and normalised RH/Rs curves for many gap values."""
    kT = core.KB_EV_K * T_K
    E = np.linspace(core.EMIN_EV, core.EMAX_EV, core.N_ENERGY)
    EF = np.linspace(-8.0 * kT, 9.0 * kT, core.N_EF)
    exponent = np.clip((E[None, :] - EF[:, None]) / kT, -60.0, 60.0)
    f = 1.0 / (np.exp(exponent) + 1.0)
    electron_mask = E[None, :] >= EF[:, None]
    hole_mask = E[None, :] <= EF[:, None]

    weights = np.ones_like(E)
    weights[[0, -1]] = 0.5
    weights *= (E[-1] - E[0]) / (len(E) - 1)
    electron_window = f * electron_mask * weights[None, :]
    hole_window = (1.0 - f) * hole_mask * weights[None, :]

    abs_E = np.abs(E)
    half_gaps = 0.5 * gap_values * kT
    dos = np.maximum(abs_E[None, :] - half_gaps[:, None], 0.0)
    n = core.NA_CM2 * (dos @ electron_window.T)
    p = core.NA_CM2 * (dos @ hole_window.T)
    total = p + n
    RH = (p - n) / total**2
    Rs = 1.0 / total
    RH_norm = RH / np.max(np.abs(RH), axis=1)[:, None]
    Rs_norm = Rs / np.max(Rs, axis=1)[:, None]
    return EF, RH_norm, Rs_norm


def fit_gap_library(
    data_xy: np.ndarray,
    gap_values: np.ndarray,
    RH_models: np.ndarray,
    Rs_models: np.ndarray,
) -> tuple[float, float, int, np.ndarray, np.ndarray]:
    """Fit every gap curve and return the best gap, residual and assignments."""
    model_xy = np.stack([RH_models, Rs_models], axis=-1)
    d2 = ((data_xy[None, :, None, :] - model_xy[:, None, :, :]) ** 2).sum(axis=3)
    min_d2 = np.min(d2, axis=2)
    residuals = np.sqrt(np.mean(min_d2, axis=1))
    best_model = int(np.argmin(residuals))
    nearest = np.argmin(d2[best_model], axis=1)
    return (
        float(gap_values[best_model]),
        float(residuals[best_model]),
        best_model,
        nearest,
        residuals,
    )


def load_base_results(args: argparse.Namespace) -> dict:
    if args.base_results is not None:
        source = args.base_results
    elif (args.output_dir / "results.json").exists():
        source = args.output_dir / "results.json"
    else:
        source = args.data_dir / "results_template.json"
    return json.loads(source.read_text(encoding="utf-8"))


def bootstrap(
    data: pd.DataFrame,
    indices: np.ndarray,
    EF_grid: np.ndarray,
    cone_curve: core.ModelCurve,
    gap_values: np.ndarray,
    RH_models: np.ndarray,
    Rs_models: np.ndarray,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    indexed = data.set_index(["measurement_index", "repeat"])
    repeats = np.array([1, 2, 3])
    RH = np.column_stack(
        [indexed.loc[(indices, r), "R_H_raw"].to_numpy() for r in repeats]
    )
    Rs = np.column_stack(
        [indexed.loc[(indices, r), "R_xx_raw"].to_numpy() for r in repeats]
    )
    model_xy = np.stack([RH_models, Rs_models], axis=-1)
    cone_xy = np.column_stack([cone_curve.RH_norm, cone_curve.Rs_norm])
    rng = np.random.default_rng(seed)
    rows = np.arange(len(indices))
    boot_gap = np.empty(N_BOOTSTRAP)
    boot_EF = np.empty((N_BOOTSTRAP, len(indices)))
    boot_is_gap = np.zeros(N_BOOTSTRAP, dtype=bool)

    for b in range(N_BOOTSTRAP):
        selected_repeat = rng.integers(0, 3, size=len(indices))
        data_xy = core.normalise_pairs(
            RH[rows, selected_repeat], Rs[rows, selected_repeat]
        )

        cone_d2 = ((data_xy[:, None, :] - cone_xy[None, :, :]) ** 2).sum(axis=2)
        cone_residual = float(np.sqrt(np.mean(np.min(cone_d2, axis=1))))
        cone_nearest = np.argmin(cone_d2, axis=1)

        d2 = ((data_xy[None, :, None, :] - model_xy[:, None, :, :]) ** 2).sum(axis=3)
        min_d2 = np.min(d2, axis=2)
        residuals = np.sqrt(np.mean(min_d2, axis=1))
        j_gap = int(np.argmin(residuals))
        gap_residual = float(residuals[j_gap])
        choose_gap = gap_residual < 0.85 * cone_residual and gap_values[j_gap] >= 1.0
        boot_is_gap[b] = choose_gap
        if choose_gap:
            boot_gap[b] = gap_values[j_gap]
            nearest = np.argmin(d2[j_gap], axis=1)
        else:
            boot_gap[b] = 0.0
            nearest = cone_nearest
        boot_EF[b] = EF_grid[nearest]

    return boot_gap, boot_EF, boot_is_gap


def save_refined_model_figure(
    data_xy: np.ndarray,
    RH_model: np.ndarray,
    Rs_model: np.ndarray,
    nearest: np.ndarray,
    gap_kT: float,
    residual: float,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 6.6))
    ax.plot(
        RH_model,
        Rs_model,
        color="#174A70",
        linewidth=2.4,
        label=f"Optimised hard gap: Eg/kBT={gap_kT:.4f}, r={residual:.5f}",
    )
    scatter = ax.scatter(
        data_xy[:, 0],
        data_xy[:, 1],
        c=np.arange(len(data_xy)),
        cmap="viridis",
        s=42,
        edgecolors="white",
        linewidths=0.45,
        zorder=3,
    )
    projected = np.column_stack([RH_model[nearest], Rs_model[nearest]])
    for source, target in zip(data_xy, projected):
        ax.plot(
            [source[0], target[0]],
            [source[1], target[1]],
            color="#888888",
            linewidth=0.55,
            alpha=0.20,
            zorder=1,
        )
    cbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label("Measurement index order")
    ax.axvline(0.0, color="black", linewidth=0.8, alpha=0.5)
    ax.set_xlabel(r"Normalised Hall coefficient, $\widetilde{R}_H$")
    ax.set_ylabel(r"Normalised sheet resistance, $\widetilde{R}_s$")
    ax.set_title("G24 L2 refined hard-gap fit")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, loc="lower center")
    fig.tight_layout()
    fig.savefig(path, dpi=240)
    plt.close(fig)


def write_checkpoint(output_dir: Path) -> Path:
    checkpoint = output_dir / "G24_L2_Checkpoint.zip"
    required = [
        "results.json",
        "L2_model_fit.png",
        "L2_EF_trajectory.png",
        "L2_brief_note.txt",
        "commit_hash.txt",
    ]
    with zipfile.ZipFile(checkpoint, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in required:
            zf.write(output_dir / name, arcname=name)
    return checkpoint


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data, meta = core.load_and_validate(args.data_dir)
    means = core.prepare_means(data)
    indices = means["measurement_index"].to_numpy(int)
    RH_mean = means["R_H_mean"].to_numpy(float)
    Rs_mean = means["R_xx_mean"].to_numpy(float)
    data_xy = core.normalise_pairs(RH_mean, Rs_mean)

    T_K = float(meta["T_K"])
    coarse_EF, coarse_curves = core.build_model_library(T_K)
    cone_curve = coarse_curves[0]
    cone_residual, _ = core.nearest_curve_fit(data_xy, cone_curve)

    preliminary_gaps = np.round(
        np.arange(
            CENTRAL_GAP_MIN_KT,
            CENTRAL_GAP_MAX_KT + 0.5 * CENTRAL_GAP_STEP_KT,
            CENTRAL_GAP_STEP_KT,
        ),
        3,
    )
    EF_grid, preliminary_RH, preliminary_Rs = build_gap_curves(
        T_K, preliminary_gaps
    )
    preliminary_gap, _, preliminary_j, _, _ = fit_gap_library(
        data_xy, preliminary_gaps, preliminary_RH, preliminary_Rs
    )
    if preliminary_j in (0, len(preliminary_gaps) - 1):
        raise AssertionError("Preliminary gap optimum lies on the search boundary.")

    central_gaps = np.round(
        np.arange(
            preliminary_gap - FINAL_GAP_HALF_WIDTH_KT,
            preliminary_gap + FINAL_GAP_HALF_WIDTH_KT + 0.5 * FINAL_GAP_STEP_KT,
            FINAL_GAP_STEP_KT,
        ),
        4,
    )
    EF_grid, RH_models, Rs_models = build_gap_curves(T_K, central_gaps)
    gap_kT, gap_residual, best_j, nearest, residuals = fit_gap_library(
        data_xy, central_gaps, RH_models, Rs_models
    )
    if best_j in (0, len(central_gaps) - 1):
        raise AssertionError("Refined central optimum lies on the search boundary.")
    choose_gap = gap_residual < 0.85 * cone_residual and gap_kT >= 1.0
    if not choose_gap:
        raise AssertionError("The refined hard-gap model did not pass the 15% rule.")

    bootstrap_gaps = np.round(
        np.arange(
            BOOTSTRAP_GAP_MIN_KT,
            BOOTSTRAP_GAP_MAX_KT + 0.5 * BOOTSTRAP_GAP_STEP_KT,
            BOOTSTRAP_GAP_STEP_KT,
        ),
        2,
    )
    _, RH_boot_models, Rs_boot_models = build_gap_curves(T_K, bootstrap_gaps)
    boot_gap, boot_EF, boot_is_gap = bootstrap(
        data,
        indices,
        EF_grid,
        cone_curve,
        bootstrap_gaps,
        RH_boot_models,
        Rs_boot_models,
        args.seed,
    )
    if np.any(np.isin(boot_gap[boot_is_gap], [bootstrap_gaps[0], bootstrap_gaps[-1]])):
        raise AssertionError("A bootstrap gap optimum reached the local search boundary.")

    Eg_p16, Eg_median, Eg_p84 = np.percentile(boot_gap, [16, 50, 84])
    EF_p16, EF_p84 = np.percentile(boot_EF, [16, 84], axis=0)
    hard_gap_fraction = float(np.mean(boot_is_gap))
    EF_assigned = EF_grid[nearest]
    pipeline_commit = detect_commit(args.pipeline_commit)

    results = load_base_results(args)
    results["pipeline_commit"] = pipeline_commit
    results["L2"] = {
        "model": "hard_gap",
        "Eg_kT": gap_kT,
        "Eg_uncertainty_kT": [float(Eg_p16), float(Eg_p84)],
        "EF_trajectory_eV": EF_assigned.tolist(),
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
    audit["EF_assigned_eV"] = EF_assigned
    audit["EF_bootstrap_p16_eV"] = EF_p16
    audit["EF_bootstrap_p84_eV"] = EF_p84
    audit.to_csv(args.output_dir / "L2_calculations.csv", index=False)
    pd.DataFrame({"Eg_kT": central_gaps, "residual": residuals}).to_csv(
        args.output_dir / "L2_refined_gap_sweep.csv", index=False
    )

    sign_brackets = core.find_sign_brackets(indices, RH_mean)
    core.save_raw_repeat_figure(
        data, sign_brackets, args.output_dir / "L2_raw_repeats.png"
    )
    save_refined_model_figure(
        data_xy,
        RH_models[best_j],
        Rs_models[best_j],
        nearest,
        gap_kT,
        gap_residual,
        args.output_dir / "L2_model_fit.png",
    )
    core.save_trajectory_figure(
        indices,
        EF_assigned,
        EF_p16,
        EF_p84,
        args.output_dir / "L2_EF_trajectory.png",
    )

    Eg_eV = gap_kT * core.KB_EV_K * T_K
    note = (
        "G24 L2 refined-gap result\n"
        f"Selected model: hard_gap\n"
        f"Optimised Eg/kBT: {gap_kT:.4f}\n"
        f"Optimised Eg at {T_K:.0f} K: {Eg_eV:.6f} eV\n"
        f"Bootstrap Eg/kBT: median {Eg_median:.2f}, 16th-84th percentile "
        f"[{Eg_p16:.2f}, {Eg_p84:.2f}]\n"
        f"Cone residual: {cone_residual:.8f}\n"
        f"Optimised hard-gap residual: {gap_residual:.8f}\n"
        f"Residual improvement versus cone: "
        f"{100.0 * (1.0 - gap_residual / cone_residual):.2f}%\n"
        f"Hard-gap bootstrap selection fraction: {hard_gap_fraction:.3f}\n"
        f"Random seed: {args.seed}\n\n"
        "Method note: the carrier equations, independent normalisation, 400-point "
        "EF grid, nearest-point residual and 15% model rule were retained. Only Eg "
        "was refined first in 0.001-kBT steps and then in 0.0001-kBT steps for "
        "the central fit, following the updated instruction to vary the gap for "
        "the smallest residual.\n"
    )
    (args.output_dir / "L2_brief_note.txt").write_text(note, encoding="utf-8")

    validation = {
        "group": meta["group"],
        "temperature_K": T_K,
        "measurement_count": int(len(indices)),
        "EF_grid_points": core.N_EF,
        "central_gap_search_kT": [
            CENTRAL_GAP_MIN_KT,
            CENTRAL_GAP_MAX_KT,
            CENTRAL_GAP_STEP_KT,
        ],
        "final_gap_search_half_width_kT": FINAL_GAP_HALF_WIDTH_KT,
        "final_gap_step_kT": FINAL_GAP_STEP_KT,
        "bootstrap_gap_step_kT": BOOTSTRAP_GAP_STEP_KT,
        "cone_residual": cone_residual,
        "optimised_gap_Eg_kT": gap_kT,
        "optimised_gap_Eg_eV": Eg_eV,
        "optimised_gap_residual": gap_residual,
        "bootstrap_replicates": N_BOOTSTRAP,
        "bootstrap_seed": args.seed,
        "bootstrap_gap_median_kT": float(Eg_median),
        "bootstrap_gap_p16_kT": float(Eg_p16),
        "bootstrap_gap_p84_kT": float(Eg_p84),
        "bootstrap_hard_gap_fraction": hard_gap_fraction,
        "trajectory_length": int(len(EF_assigned)),
        "all_outputs_finite": bool(
            np.isfinite(EF_assigned).all()
            and np.isfinite(boot_EF).all()
            and np.isfinite(boot_gap).all()
        ),
    }
    (args.output_dir / "L2_validation.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )

    checkpoint = write_checkpoint(args.output_dir)
    print(f"Optimised Eg/kBT: {gap_kT:.4f}")
    print(f"Optimised Eg: {Eg_eV:.6f} eV")
    print(f"Cone residual: {cone_residual:.8f}")
    print(f"Optimised hard-gap residual: {gap_residual:.8f}")
    print(f"Bootstrap Eg/kBT 16-84%: [{Eg_p16:.2f}, {Eg_p84:.2f}]")
    print(f"Bootstrap hard-gap fraction: {hard_gap_fraction:.3f}")
    print(f"Checkpoint: {checkpoint}")


if __name__ == "__main__":
    main()
