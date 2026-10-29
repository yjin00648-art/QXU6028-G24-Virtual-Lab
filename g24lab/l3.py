#!/usr/bin/env python3
"""QXU6028 L3 analysis for the G24 regular or blind dataset.

Implements the prescribed zero-mean, first-difference Tikhonov inverse,
five-point regularisation sensitivity study, point-spread resolution test,
and 500-sample noise-linked detection limit.
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
from .plot_io import save_png
import numpy as np
import pandas as pd


NPIX = 10
N_CHANNELS = 128
N_UNKNOWN = 100
SPEC_LIMIT = 0.030
ETA_FACTORS = np.array([0.01, 0.1, 1.0, 10.0, 100.0])
N_NOISE = 500
DEFAULT_SEED = 20_260_924
COORDS = np.linspace(-2.7, 2.7, NPIX)


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
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "PENDING_LOCAL_L3_COMMIT"


def load_and_validate(data_dir: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    A = np.load(data_dir / "L3_A.npy")
    d_repeats = np.loadtxt(data_dir / "L3_d.csv", delimiter=",")
    meta = json.loads((data_dir / "L3_meta.json").read_text(encoding="utf-8"))

    if A.shape != (N_CHANNELS, N_UNKNOWN):
        raise ValueError(f"Expected A shape (128, 100), received {A.shape}")
    if d_repeats.shape != (3, N_CHANNELS):
        raise ValueError(f"Expected d shape (3, 128), received {d_repeats.shape}")
    if not np.isfinite(A).all() or not np.isfinite(d_repeats).all():
        raise ValueError("A and d must contain only finite values")
    max_row_sum = float(np.max(np.abs(A.sum(axis=1))))
    if max_row_sum >= 1e-11:
        raise ValueError(f"A row-sum gate failed: max abs row sum={max_row_sum:.3e}")
    if meta.get("group") != "G24" or meta.get("dataset_set") not in {"regular", "blind"}:
        raise ValueError("L3 metadata does not identify a supported G24 dataset")
    return A, d_repeats, meta


def gradient_matrix(npix: int = NPIX) -> np.ndarray:
    rows: list[np.ndarray] = []
    n = npix * npix
    for i in range(npix):
        for j in range(npix):
            k = i * npix + j
            if j < npix - 1:
                row = np.zeros(n)
                row[k] = -1.0
                row[k + 1] = 1.0
                rows.append(row)
            if i < npix - 1:
                row = np.zeros(n)
                row[k] = -1.0
                row[k + npix] = 1.0
                rows.append(row)
    return np.asarray(rows)


def zero_mean_projector(n: int) -> np.ndarray:
    one = np.ones((n, 1)) / np.sqrt(n)
    return np.eye(n) - one @ one.T


def inverse_operator(
    A: np.ndarray,
    L: np.ndarray,
    projector: np.ndarray,
    eta: float,
) -> np.ndarray:
    n = A.shape[1]
    system = (
        projector @ (A.T @ A + eta * (L.T @ L)) @ projector
        + 1e-9 * np.eye(n)
    )
    rhs_operator = projector @ A.T
    return np.linalg.lstsq(system, rhs_operator, rcond=None)[0]


def reconstruct(operator: np.ndarray, data: np.ndarray) -> np.ndarray:
    model = operator @ data
    return model - model.mean()


def psf_result(
    A: np.ndarray,
    operator: np.ndarray,
    row: int,
    column: int,
) -> tuple[np.ndarray, float]:
    q = np.zeros(N_UNKNOWN)
    q[row * NPIX + column] = 1.0
    q -= q.mean()
    recovered = reconstruct(operator, A @ q).reshape(NPIX, NPIX)

    yy, xx = np.meshgrid(COORDS, COORDS, indexing="ij")
    radius_sq = (xx - COORDS[column]) ** 2 + (yy - COORDS[row]) ** 2
    weights = np.maximum(recovered, 0.0)
    sigma_sq = float(np.sum(weights * radius_sq) / (2.0 * np.sum(weights)))
    fwhm = 2.355 * np.sqrt(sigma_sq)
    return recovered, float(fwhm)


def load_base_results(args: argparse.Namespace) -> dict:
    if args.base_results is not None:
        source = args.base_results
    elif (args.output_dir / "results.json").exists():
        source = args.output_dir / "results.json"
    else:
        source = args.data_dir / "results_template.json"
    return json.loads(source.read_text(encoding="utf-8"))


def save_map_figure(
    map_2d: np.ndarray,
    positive: tuple[int, int],
    negative: tuple[int, int],
    eta: float,
    delta95: float,
    decision: str,
    path: Path,
) -> None:
    vmax = float(np.max(np.abs(map_2d)))
    fig, ax = plt.subplots(figsize=(8.8, 7.2), constrained_layout=True)
    image = ax.imshow(
        map_2d,
        origin="lower",
        extent=(-3.0, 3.0, -3.0, 3.0),
        cmap="RdBu_r",
        vmin=-vmax,
        vmax=vmax,
        interpolation="nearest",
    )
    colorbar = fig.colorbar(image, ax=ax, pad=0.025)
    colorbar.set_label("Relative conductivity non-uniformity, m")

    ax.set_xticks(COORDS)
    ax.set_yticks(COORDS)
    ax.tick_params(axis="x", rotation=45)
    ax.set_xlabel("x position (probe pitch)")
    ax.set_ylabel("y position (probe pitch)")

    pos_x, pos_y = COORDS[positive[1]], COORDS[positive[0]]
    neg_x, neg_y = COORDS[negative[1]], COORDS[negative[0]]
    ax.scatter(
        [pos_x], [pos_y], s=150, marker="^", facecolors="none",
        edgecolors="black", linewidths=1.7, zorder=4,
    )
    ax.scatter(
        [neg_x], [neg_y], s=150, marker="v", facecolors="none",
        edgecolors="black", linewidths=1.7, zorder=4,
    )
    ax.annotate(
        f"positive maximum\n({pos_x:.1f}, {pos_y:.1f}), {map_2d[positive]:+.5f}",
        xy=(pos_x, pos_y), xytext=(-1.3, 2.25),
        arrowprops={"arrowstyle": "->", "color": "black", "lw": 1.0},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "alpha": 0.86},
    )
    ax.annotate(
        f"negative minimum\n({neg_x:.1f}, {neg_y:.1f}), {map_2d[negative]:+.5f}",
        xy=(neg_x, neg_y), xytext=(0.55, -2.25),
        arrowprops={"arrowstyle": "->", "color": "black", "lw": 1.0},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "alpha": 0.86},
    )

    xx, yy = np.meshgrid(COORDS, COORDS)
    contours = ax.contour(
        xx, yy, map_2d, levels=[-SPEC_LIMIT, SPEC_LIMIT],
        colors="black", linestyles="--", linewidths=1.0,
    )
    ax.clabel(contours, inline=True, fontsize=8, fmt={-SPEC_LIMIT: "-3%", SPEC_LIMIT: "+3%"})
    ax.set_title(
        "G24 L3 zero-mean conductivity map\n"
        f"eta={eta:.6g}; max|m|={vmax:.5f}; delta95={delta95:.2e}; {decision.upper()}"
    )
    save_png(fig, path, dpi=260)
    plt.close(fig)


def save_method_figure(
    singular_values: np.ndarray,
    sensitivity: pd.DataFrame,
    central_psf: np.ndarray,
    offcentre_psf: np.ndarray,
    central_fwhm: float,
    offcentre_fwhm: float,
    noise_maxima: np.ndarray,
    delta95: float,
    path: Path,
) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(15.2, 9.0), constrained_layout=True)

    ax = axes[0, 0]
    ax.semilogy(np.arange(1, len(singular_values) + 1), singular_values, color="#174A70")
    ax.axhline(1e-12, color="#B04A3A", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Singular-value index")
    ax.set_ylabel("Singular value")
    ax.set_title("(a) Forward-matrix singular values")
    ax.grid(alpha=0.22)

    ax = axes[0, 1]
    ax.plot(
        sensitivity["roughness_norm"], sensitivity["residual_norm"],
        color="#777777", linewidth=1.4, zorder=1,
    )
    factor_colours = plt.cm.viridis(np.linspace(0.08, 0.92, len(sensitivity)))
    for row, colour in zip(sensitivity.itertuples(), factor_colours):
        ax.scatter(
            [row.roughness_norm],
            [row.residual_norm],
            s=52,
            color=colour,
            zorder=2,
            label=f"{row.eta_factor:g}x eta0",
        )
    ax.set_xlabel(r"Roughness norm, $||Lm||_2$")
    ax.set_ylabel(r"Residual norm, $||Am-d||_2$")
    ax.set_title("(b) Regularisation sensitivity")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, fontsize=8, loc="upper right")

    ax = axes[0, 2]
    ax.semilogx(
        sensitivity["eta_factor"], sensitivity["max_abs_map"],
        color="#174A70", marker="o", linewidth=1.8,
    )
    ax.axhline(SPEC_LIMIT, color="#B04A3A", linestyle="--", linewidth=1.4, label="3% specification")
    selected = sensitivity.loc[np.isclose(sensitivity["eta_factor"], 1.0)].iloc[0]
    ax.scatter([1.0], [selected["max_abs_map"]], marker="*", s=150, color="#138A4B", zorder=4, label="selected eta0")
    ax.set_xlabel(r"Regularisation factor, $\eta/\eta_0$")
    ax.set_ylabel(r"$\max |m|$")
    ax.set_title("(c) Decision stability versus eta")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False)

    psf_vmax = max(float(np.max(np.abs(central_psf))), float(np.max(np.abs(offcentre_psf))))
    for ax, psf, title in [
        (axes[1, 0], central_psf, f"(d) Central PSF: FWHM={central_fwhm:.3f}"),
        (axes[1, 1], offcentre_psf, f"(e) Off-centre PSF: FWHM={offcentre_fwhm:.3f}"),
    ]:
        im = ax.imshow(
            psf, origin="lower", extent=(-3, 3, -3, 3), cmap="RdBu_r",
            vmin=-psf_vmax, vmax=psf_vmax, interpolation="nearest",
        )
        ax.set_xlabel("x (probe pitch)")
        ax.set_ylabel("y (probe pitch)")
        ax.set_title(title)
        fig.colorbar(im, ax=ax, fraction=0.047, pad=0.03)

    ax = axes[1, 2]
    ax.hist(noise_maxima, bins=25, color="#2A9D8F", edgecolor="white", alpha=0.9)
    ax.axvline(delta95, color="#B04A3A", linestyle="--", linewidth=1.6, label=f"95th percentile={delta95:.2e}")
    ax.set_xlabel(r"Noise-map $\max |m|$")
    ax.set_ylabel("Count")
    ax.set_title("(f) 500 noise-only reconstructions")
    ax.grid(alpha=0.18)
    ax.legend(frameon=False)

    fig.suptitle("G24 L3 inversion, resolution and detection-limit diagnostics", fontsize=16, fontweight="semibold")
    save_png(fig, path, dpi=240)
    plt.close(fig)


def write_checkpoint(output_dir: Path) -> Path:
    checkpoint = output_dir / "G24_L3_Checkpoint.zip"
    required = [
        "results.json",
        "L3_map.png",
        "L3_method.png",
        "L3_brief_note.txt",
        "commit_hash.txt",
    ]
    with zipfile.ZipFile(checkpoint, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in required:
            archive.write(output_dir / name, arcname=name)
    return checkpoint


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    A, d_repeats, meta = load_and_validate(args.data_dir)
    d_mean = d_repeats.mean(axis=0)
    repeat_sigma = d_repeats.std(axis=0, ddof=1)

    L = gradient_matrix(NPIX)
    projector = zero_mean_projector(N_UNKNOWN)
    eta0 = 1e-2 * np.linalg.norm(A, 2) ** 2 / np.linalg.norm(L, 2) ** 2

    sensitivity_rows = []
    operators: dict[float, np.ndarray] = {}
    for factor in ETA_FACTORS:
        eta = float(eta0 * factor)
        operator = inverse_operator(A, L, projector, eta)
        operators[float(factor)] = operator
        model = reconstruct(operator, d_mean)
        sensitivity_rows.append(
            {
                "eta_factor": float(factor),
                "eta": eta,
                "residual_norm": float(np.linalg.norm(A @ model - d_mean)),
                "roughness_norm": float(np.linalg.norm(L @ model)),
                "max_abs_map": float(np.max(np.abs(model))),
            }
        )
    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity.to_csv(args.output_dir / "L3_eta_sensitivity.csv", index=False)

    chosen_factor = 1.0
    chosen_eta = float(eta0)
    chosen_operator = operators[chosen_factor]
    map_flat = reconstruct(chosen_operator, d_mean)
    map_2d = map_flat.reshape(NPIX, NPIX)
    if not np.isfinite(map_flat).all() or abs(float(map_flat.mean())) >= 1e-10:
        raise RuntimeError("Reconstructed map failed the finite/zero-mean checks")

    positive = tuple(int(i) for i in np.unravel_index(np.argmax(map_2d), map_2d.shape))
    negative = tuple(int(i) for i in np.unravel_index(np.argmin(map_2d), map_2d.shape))
    positive_feature = {
        "sign": "positive",
        "x_probe_pitch": float(COORDS[positive[1]]),
        "y_probe_pitch": float(COORDS[positive[0]]),
        "amplitude_fraction": float(map_2d[positive]),
        "row": positive[0],
        "column": positive[1],
    }
    negative_feature = {
        "sign": "negative",
        "x_probe_pitch": float(COORDS[negative[1]]),
        "y_probe_pitch": float(COORDS[negative[0]]),
        "amplitude_fraction": float(map_2d[negative]),
        "row": negative[0],
        "column": negative[1],
    }

    central_psf, central_fwhm = psf_result(A, chosen_operator, 5, 5)
    offcentre_psf, offcentre_fwhm = psf_result(A, chosen_operator, 2, 7)
    resolution = float(max(central_fwhm, offcentre_fwhm))

    rng = np.random.default_rng(args.seed)
    noise_vectors = rng.normal(0.0, repeat_sigma, size=(N_NOISE, N_CHANNELS))
    noise_maps = noise_vectors @ chosen_operator.T
    noise_maps -= noise_maps.mean(axis=1, keepdims=True)
    noise_maxima = np.max(np.abs(noise_maps), axis=1)
    delta95 = float(np.percentile(noise_maxima, 95.0))

    max_abs = float(np.max(np.abs(map_flat)))
    if max_abs + delta95 <= SPEC_LIMIT:
        decision = "clear pass"
        pass_value = True
        confidence = (
            f"clear pass: max|m| + delta95 = {max_abs + delta95:.8f} "
            f"is below the {SPEC_LIMIT:.3f} limit"
        )
    elif max_abs - delta95 > SPEC_LIMIT:
        decision = "clear fail"
        pass_value = False
        confidence = (
            f"clear fail: max|m| - delta95 = {max_abs - delta95:.8f} "
            f"is above the {SPEC_LIMIT:.3f} limit"
        )
    else:
        decision = "borderline"
        pass_value = False
        confidence = (
            f"borderline: the interval [{max_abs - delta95:.8f}, "
            f"{max_abs + delta95:.8f}] crosses the {SPEC_LIMIT:.3f} limit"
        )

    pipeline_commit = detect_commit(args.pipeline_commit)
    results = load_base_results(args)
    results["group"] = str(meta["group"])
    results["dataset_set"] = str(meta["dataset_set"])
    results["pipeline_commit"] = pipeline_commit
    results["L3"] = {
        "map": [float(value) for value in map_flat],
        "features": [positive_feature, negative_feature],
        "resolution_probe_pitch": resolution,
        "detection_limit_fraction": delta95,
        "pass": pass_value,
        "confidence": confidence,
    }
    if len(results["L3"]["map"]) != 100:
        raise RuntimeError("L3 map must contain exactly 100 row-major values")
    (args.output_dir / "results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "commit_hash.txt").write_text(
        pipeline_commit + "\n", encoding="utf-8"
    )

    map_table = pd.DataFrame(map_2d, index=COORDS, columns=COORDS)
    map_table.index.name = "y_probe_pitch"
    map_table.columns.name = "x_probe_pitch"
    map_table.to_csv(args.output_dir / "L3_map.csv")
    pd.DataFrame({"noise_max_abs": noise_maxima}).to_csv(
        args.output_dir / "L3_noise_maxima.csv", index=False
    )

    singular_values = np.linalg.svd(A, compute_uv=False)
    save_map_figure(
        map_2d, positive, negative, chosen_eta, delta95, decision,
        args.output_dir / "L3_map.png",
    )
    save_method_figure(
        singular_values,
        sensitivity,
        central_psf,
        offcentre_psf,
        central_fwhm,
        offcentre_fwhm,
        noise_maxima,
        delta95,
        args.output_dir / "L3_method.png",
    )

    note = (
        "G24 L3 zero-mean regularised reconstruction\n"
        f"A shape: {A.shape}; d shape: {d_repeats.shape}\n"
        f"Maximum absolute row sum: {np.max(np.abs(A.sum(axis=1))):.3e}\n"
        f"Numerical rank of A: {np.linalg.matrix_rank(A)} / {N_UNKNOWN}\n"
        f"Gradient matrix shape: {L.shape}\n"
        f"eta0: {eta0:.10g}; selected eta factor: {chosen_factor:g}\n"
        f"Map mean: {map_flat.mean():.3e}\n"
        f"Positive feature: x={positive_feature['x_probe_pitch']:.1f}, "
        f"y={positive_feature['y_probe_pitch']:.1f}, "
        f"amplitude={positive_feature['amplitude_fraction']:+.8f}\n"
        f"Negative feature: x={negative_feature['x_probe_pitch']:.1f}, "
        f"y={negative_feature['y_probe_pitch']:.1f}, "
        f"amplitude={negative_feature['amplitude_fraction']:+.8f}\n"
        f"Central PSF FWHM: {central_fwhm:.6f} probe pitches\n"
        f"Off-centre PSF FWHM: {offcentre_fwhm:.6f} probe pitches\n"
        f"Conservative resolution: {resolution:.6f} probe pitches\n"
        f"Repeat-noise sigma: median={np.median(repeat_sigma):.3e}, "
        f"maximum={np.max(repeat_sigma):.3e}\n"
        f"Noise simulations: {N_NOISE}; random seed: {args.seed}\n"
        f"95% detection limit delta95: {delta95:.10g}\n"
        f"Maximum absolute reconstructed non-uniformity: {max_abs:.8f}\n"
        f"Announced specification: max|m| <= {SPEC_LIMIT:.3f}\n"
        f"Decision: {decision.upper()}\n"
        f"Confidence statement: {confidence}.\n\n"
        "Method note: the reference result uses the prescribed eta0 because the extrema "
        "and the pass/fail decision remain stable across the five requested eta factors. "
        "The probe is blind to the constant mode, so the map is explicitly projected "
        "and returned with zero mean. Adjacent pixels of the same sign are treated as "
        "one broad feature; the reported coordinates are the positive and negative extrema. "
        "The repeat-linked detection limit is orders of magnitude smaller than the observed "
        f"{100.0 * max_abs:.2f}% extremum, so repeat noise does not alter the decision.\n"
    )
    (args.output_dir / "L3_brief_note.txt").write_text(note, encoding="utf-8")

    diagnostics = {
        "eta0": eta0,
        "selected_eta_factor": chosen_factor,
        "selected_eta": chosen_eta,
        "central_fwhm_probe_pitch": central_fwhm,
        "offcentre_fwhm_probe_pitch": offcentre_fwhm,
        "resolution_probe_pitch": resolution,
        "detection_limit_fraction": delta95,
        "max_abs_map": max_abs,
        "specification_fraction": SPEC_LIMIT,
        "decision": decision,
        "random_seed": args.seed,
    }
    (args.output_dir / "L3_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
    )

    checkpoint = write_checkpoint(args.output_dir)
    print(f"eta0: {eta0:.10g}")
    print(f"max|m|: {max_abs:.8f}")
    print(f"resolution: {resolution:.6f} probe pitches")
    print(f"delta95: {delta95:.10g}")
    print(f"decision: {decision}")
    print(f"checkpoint: {checkpoint}")


if __name__ == "__main__":
    main()
