#!/usr/bin/env python3
"""
Offline BCR (Behavioral Coverage Rate) computation.

Fits k-means ONCE on all fingerprints from all conditions combined,
then replays each condition's history to produce:
  BCR(t) = explored behavioral clusters / K

This avoids cluster drift and relabeling issues that arise from online k-means.
Fully reproducible: same random seed, same fit, deterministic curves.

Usage:
  python scripts/compute_bcr_offline.py \
    --log_dirs logs/layer1_baseline_150_r1 logs/layer1_dedup_150_r1 logs/layer2_dedup_div_150_r1 \
    --labels baseline dedup "dedup+diversity" \
    --n_clusters 8 \
    --output docs/figures/bcr_curves.pdf

Notes:
  - fingerprints.csv format: sample_num,v1,v2,...,v62  (comma-separated integers)
  - Only dedup/dedup+div runs produce fingerprints (baseline has no dedup_filter).
  - Run with EXPORT_FINGERPRINTS=1 to generate fingerprints.csv during experiments.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # non-interactive backend, safe for scripts
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans


# ── Fingerprint loading ────────────────────────────────────────────────────────

def load_fingerprints(log_dir: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Load fingerprints.csv from log_dir.

    Returns:
        sample_indices: shape (N,), int — the global_sample_nums value per row
        vectors:        shape (N, D), float — the fingerprint vectors
    """
    fp_path = os.path.join(log_dir, 'fingerprints.csv')
    if not os.path.exists(fp_path):
        raise FileNotFoundError(
            f"fingerprints.csv not found in {log_dir}\n"
            "Re-run that experiment with EXPORT_FINGERPRINTS=1 to generate it."
        )

    df = pd.read_csv(fp_path, header=None)
    # Column 0: sample index; columns 1..D: fingerprint integer values
    sample_indices = df.iloc[:, 0].to_numpy(dtype=int)
    vectors = df.iloc[:, 1:].to_numpy(dtype=float)
    return sample_indices, vectors


# ── BCR curve computation ──────────────────────────────────────────────────────

def compute_bcr_curve(
    sample_indices: np.ndarray,
    vectors: np.ndarray,
    kmeans: KMeans,
) -> list[tuple[int, float]]:
    """
    Assign fingerprints to clusters using a pre-fitted k-means model,
    then replay history to build the BCR(t) curve.

    Args:
        sample_indices: (N,) — sample numbers in chronological order
        vectors:        (N, D) — fingerprint vectors
        kmeans:         pre-fitted KMeans model (K clusters)

    Returns:
        List of (sample_num, bcr) pairs, monotonically non-decreasing BCR.
    """
    K = kmeans.n_clusters
    labels = kmeans.predict(vectors)

    explored: set[int] = set()
    curve: list[tuple[int, float]] = []
    for idx, label in zip(sample_indices, labels):
        explored.add(int(label))
        curve.append((int(idx), len(explored) / K))
    return curve


# ── Plotting ───────────────────────────────────────────────────────────────────

COLORS = ['#888888', '#2196F3', '#FF9800', '#E91E63', '#4CAF50', '#9C27B0']
LINESTYLES = ['-', '-', '-', '--', '--', '--']


def plot_bcr_curves(
    curves: dict[str, list[tuple[int, float]]],
    output_path: str,
    n_clusters: int,
) -> None:
    """
    Plot BCR(t) curves for all conditions and save to PDF.

    Args:
        curves:      {label: [(sample_num, bcr), ...]}
        output_path: path to save the PDF
        n_clusters:  K value used (for annotation)
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))

    for i, (label, curve) in enumerate(curves.items()):
        xs = [pt[0] for pt in curve]
        ys = [pt[1] for pt in curve]
        color = COLORS[i % len(COLORS)]
        ls = LINESTYLES[i % len(LINESTYLES)]
        ax.plot(xs, ys, label=label, color=color, linestyle=ls, linewidth=2)

        # Annotate final BCR value at the end of each curve
        if xs:
            ax.annotate(
                f'{ys[-1]:.2f}',
                xy=(xs[-1], ys[-1]),
                xytext=(4, 2),
                textcoords='offset points',
                fontsize=8,
                color=color,
            )

    ax.set_xlabel('Sample number', fontsize=12)
    ax.set_ylabel(f'BCR(t)  [explored / K={n_clusters}]', fontsize=12)
    ax.set_title('Behavioral Coverage Rate over Search Progress', fontsize=13)
    ax.set_ylim(-0.05, 1.1)
    ax.axhline(y=1.0, color='gray', linestyle=':', linewidth=1, alpha=0.6)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    fig.savefig(output_path, dpi=150)
    print(f"[BCR] Saved plot → {output_path}")
    plt.close(fig)


# ── CSV export (for Colab) ─────────────────────────────────────────────────────

def save_bcr_csv(
    curves: dict[str, list[tuple[int, float]]],
    output_path: str,
) -> None:
    """
    Save BCR curves as a tidy CSV for loading in the Colab notebook.

    Columns: condition, sample_num, bcr
    """
    rows = []
    for label, curve in curves.items():
        for sample_num, bcr in curve:
            rows.append({'condition': label, 'sample_num': sample_num, 'bcr': bcr})
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[BCR] Saved CSV  → {output_path}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Offline BCR curve computation via k-means on behavioral fingerprints.'
    )
    parser.add_argument(
        '--log_dirs', nargs='+', required=True,
        help='Log directories containing fingerprints.csv (one per condition).'
    )
    parser.add_argument(
        '--labels', nargs='+',
        help='Human-readable label for each log_dir (same order). '
             'Defaults to directory names.'
    )
    parser.add_argument(
        '--n_clusters', type=int, default=8,
        help='K for k-means (default: 8).'
    )
    parser.add_argument(
        '--output', default='docs/figures/bcr_curves.pdf',
        help='Output path for the BCR plot PDF.'
    )
    parser.add_argument(
        '--csv_output', default='docs/figures/bcr_data.csv',
        help='Output path for tidy BCR CSV (for Colab).'
    )
    args = parser.parse_args()

    # Validate label count
    labels = args.labels or args.log_dirs
    if len(labels) != len(args.log_dirs):
        print(
            f"[Error] --labels count ({len(labels)}) != --log_dirs count ({len(args.log_dirs)})",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Step 1: Load all fingerprints ──────────────────────────────────────────
    all_data: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for log_dir, label in zip(args.log_dirs, labels):
        print(f"[BCR] Loading fingerprints from {log_dir} ({label}) ...")
        indices, vecs = load_fingerprints(log_dir)
        all_data[label] = (indices, vecs)
        print(f"      {len(indices)} fingerprints, dim={vecs.shape[1]}")

    # ── Step 2: Fit k-means ONCE on all fingerprints combined ─────────────────
    all_vecs = np.vstack([v for _, v in all_data.values()])
    print(f"\n[BCR] Fitting k-means (K={args.n_clusters}) on {len(all_vecs)} total fingerprints ...")
    kmeans = KMeans(n_clusters=args.n_clusters, random_state=42, n_init=10)
    kmeans.fit(all_vecs)
    print(f"[BCR] Inertia: {kmeans.inertia_:.2f}")

    # ── Step 3: Compute per-condition BCR curves ───────────────────────────────
    curves: dict[str, list[tuple[int, float]]] = {}
    print()
    for label, (indices, vecs) in all_data.items():
        curve = compute_bcr_curve(indices, vecs, kmeans)
        curves[label] = curve
        final_bcr = curve[-1][1] if curve else 0.0
        print(f"[BCR] {label:<25}  final BCR = {final_bcr:.3f}  (n={len(curve)})")

    # ── Step 4: Save outputs ───────────────────────────────────────────────────
    print()
    plot_bcr_curves(curves, args.output, args.n_clusters)
    save_bcr_csv(curves, args.csv_output)

    print("\n[BCR] Done.")


if __name__ == '__main__':
    main()
