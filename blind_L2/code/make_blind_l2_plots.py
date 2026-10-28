#!/usr/bin/env python3
"""Create the blind-data L2 MIO fit and residual-sweep figures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import analysis_L2 as core
import analysis_L2_optimized as refined


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def residual_metrics(
    data_xy: np.ndarray,
    gaps: np.ndarray,
    hall_models: np.ndarray,
    sheet_models: np.ndarray,
) -> pd.DataFrame:
    model_xy = np.stack([hall_models, sheet_models], axis=-1)
    d2 = ((data_xy[None, :, None, :] - model_xy[:, None, :, :]) ** 2).sum(axis=3)
    nearest_d2 = np.min(d2, axis=2)
    return pd.DataFrame(
        {
            "Eg_kT": gaps,
            "rms_residual": np.sqrt(np.mean(nearest_d2, axis=1)),
            "residual_sum_of_squares": np.sum(nearest_d2, axis=1),
        }
    )


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data, meta = core.load_and_validate(args.data_dir)
    means = core.prepare_means(data)
    means = means.sort_values("measurement_index")
    mio = means["measurement_index"].to_numpy(int)
    data_xy = core.normalise_pairs(
        means["R_H_mean"].to_numpy(float),
        means["R_xx_mean"].to_numpy(float),
    )
    results = json.loads(args.results.read_text(encoding="utf-8"))
    gap = float(results["L2"]["Eg_kT"])
    temperature = float(meta["T_K"])

    _, selected_hall, selected_sheet = refined.build_gap_curves(
        temperature, np.array([gap])
    )
    _, _, _, nearest, selected_residuals = refined.fit_gap_library(
        data_xy, np.array([gap]), selected_hall, selected_sheet
    )
    selected_residual = float(selected_residuals[0])

    fig, ax = plt.subplots(figsize=(9.5, 6.7), constrained_layout=True)
    ax.plot(
        selected_hall[0],
        selected_sheet[0],
        color="#174A70",
        linewidth=3.0,
        zorder=2,
        label=(
            "Optimised hard-gap model "
            f"($E_g/k_BT={gap:.4f}$, residual={selected_residual:.5f})"
        ),
    )
    ax.plot(
        data_xy[:, 0],
        data_xy[:, 1],
        color="#E67E22",
        linewidth=2.0,
        linestyle="--",
        zorder=3,
        label="Measured trajectory (connected in MIO order)",
    )
    points = ax.scatter(
        data_xy[:, 0],
        data_xy[:, 1],
        c=mio,
        cmap="viridis",
        s=53,
        edgecolors="white",
        linewidths=0.55,
        zorder=4,
    )
    fig.colorbar(points, ax=ax, pad=0.025).set_label(
        "Measurement index order (MIO)"
    )
    ax.axvline(0.0, color="#333333", linewidth=0.9, alpha=0.55)
    ax.set_xlim(-1.10, 1.10)
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel(r"Normalised Hall coefficient, $\widetilde{R}_H$")
    ax.set_ylabel(r"Normalised sheet resistance, $\widetilde{R}_s$")
    ax.set_title("G24 blind L2 hard-gap fit and measured MIO trajectory")
    ax.grid(alpha=0.22)
    ax.legend(loc="lower center", frameon=True, framealpha=0.93)
    fig.savefig(args.output_dir / "L2_model_fit.png", dpi=260)
    plt.close(fig)

    _, library = core.build_model_library(temperature)
    cone = next(curve for curve in library if curve.model == "cone")
    cone_residual, _ = core.nearest_curve_fit(data_xy, cone)

    coarse_gaps = np.arange(0.50, 8.00 + 0.125, 0.25)
    _, coarse_hall, coarse_sheet = refined.build_gap_curves(
        temperature, coarse_gaps
    )
    coarse = residual_metrics(data_xy, coarse_gaps, coarse_hall, coarse_sheet)
    coarse.insert(0, "grid", "overview_0.25_kBT")

    fine = pd.read_csv(args.output_dir / "L2_refined_gap_sweep.csv")
    fine = fine.rename(columns={"residual": "rms_residual"})
    fine["residual_sum_of_squares"] = len(data_xy) * fine["rms_residual"] ** 2
    fine.insert(0, "grid", "final_0.0001_kBT")
    combined = pd.concat([coarse, fine], ignore_index=True)
    combined["n_measurements"] = len(data_xy)
    combined["cone_rms_residual"] = cone_residual
    combined.to_csv(args.output_dir / "L2_gap_residual_sweep.csv", index=False)

    best_row = fine.loc[fine["rms_residual"].idxmin()]
    best_gap = float(best_row["Eg_kT"])
    best_rms = float(best_row["rms_residual"])
    best_rss = float(best_row["residual_sum_of_squares"])

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(12.4, 5.4), constrained_layout=True
    )
    ax1.plot(
        coarse["Eg_kT"], coarse["rms_residual"],
        marker="o", markersize=3.8, linewidth=1.8, color="#174A70",
        label="Hard-gap RMS residual",
    )
    ax1.axhline(
        cone_residual, color="#B04A3A", linestyle="--", linewidth=1.5,
        label=f"Cone residual = {cone_residual:.5f}",
    )
    ax1.axhline(
        0.85 * cone_residual, color="#C78F18", linestyle=":", linewidth=1.6,
        label="15% selection threshold",
    )
    ax1.scatter(
        [best_gap], [best_rms], marker="*", s=150, color="#138A4B",
        edgecolors="white", linewidths=0.5, zorder=5,
        label=f"Refined optimum: {best_gap:.4f}",
    )
    ax1.set_xlabel(r"Hard gap, $E_g/k_BT$")
    ax1.set_ylabel("Nearest-curve RMS residual")
    ax1.set_title("(a) Overview of the hard-gap scan")
    ax1.grid(alpha=0.22)
    ax1.legend(frameon=False)

    line_rms = ax2.plot(
        fine["Eg_kT"], fine["rms_residual"], color="#174A70",
        linewidth=2.2, label="RMS residual",
    )[0]
    ax2.scatter(
        [best_gap], [best_rms], marker="*", s=160, color="#138A4B",
        edgecolors="white", linewidths=0.5, zorder=5,
    )
    ax2.axvline(best_gap, color="#138A4B", linestyle=":", linewidth=1.3)
    ax2.set_xlabel(r"Hard gap, $E_g/k_BT$")
    ax2.set_ylabel("RMS residual", color="#174A70")
    ax2.tick_params(axis="y", labelcolor="#174A70")
    ax2.grid(alpha=0.22)
    ax_rss = ax2.twinx()
    line_rss = ax_rss.plot(
        fine["Eg_kT"], fine["residual_sum_of_squares"], color="#E67E22",
        linewidth=1.9, linestyle="--", label="Residual sum of squares (RSS)",
    )[0]
    ax_rss.set_ylabel("Residual sum of squares (RSS)", color="#E67E22")
    ax_rss.tick_params(axis="y", labelcolor="#E67E22")
    ax2.set_title("(b) Refined scan around the minimum")
    ax2.legend(
        [line_rms, line_rss], [line_rms.get_label(), line_rss.get_label()],
        frameon=False, loc="upper right",
    )
    ax2.annotate(
        f"minimum\n$E_g/k_BT={best_gap:.4f}$\nRMS={best_rms:.8f}\nRSS={best_rss:.8f}",
        xy=(best_gap, best_rms),
        xytext=(best_gap + 0.0011, float(fine["rms_residual"].quantile(0.82))),
        arrowprops={"arrowstyle": "->", "color": "#333333", "lw": 1.0},
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "#999999"},
    )
    fig.suptitle("G24 blind L2 hard-gap residual sweep", fontsize=15)
    fig.savefig(args.output_dir / "L2_gap_residual_sweep.png", dpi=260)
    plt.close(fig)

    print(f"best_Eg_kT={best_gap:.4f}")
    print(f"best_rms_residual={best_rms:.10f}")
    print(f"best_rss={best_rss:.10f}")
    print(f"cone_residual={cone_residual:.10f}")


if __name__ == "__main__":
    main()
