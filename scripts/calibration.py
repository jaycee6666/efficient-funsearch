"""Threshold calibration experiment: similarity vs score difference scatter plot (addressing TA feedback #4).

Usage:
    python scripts/calibration.py --samples-dir <samples_directory>

Workflow:
    1. Load baseline programs (extract the function field from samples_*.json)
    2. Run 8 probes on each program -> fingerprint vector
    3. Compute cosine similarity and score difference for all C(n,2) pairs
    4. Output scatter plot: x=cosine similarity, y=|score difference|
    5. Validate 0.98 threshold: score differences in the high similarity region should be near 0
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from itertools import combinations

import numpy as np

# Add repository root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.dedup.probing import compute_fingerprint, PROBING_INSTANCES


def load_samples(samples_dir: str) -> list[dict]:
    """Load programs and scores from samples_*.json files."""
    pattern = os.path.join(samples_dir, 'samples_*.json')
    files = sorted(glob.glob(pattern))
    samples = []
    for f in files:
        with open(f) as fp:
            data = json.load(fp)
        if data.get('function') and data.get('score') is not None:
            samples.append({
                'function': data['function'],
                'score': data['score'],
                'sample_order': data.get('sample_order', 0),
            })
    return samples


def extract_program_str(function_str: str) -> str:
    """Build an executable program from a function string (including numpy import)."""
    return f"import numpy as np\n\n{function_str}\n"


def main():
    parser = argparse.ArgumentParser(description='Threshold calibration experiment')
    parser.add_argument(
        '--samples-dir',
        default=None,
        help='Directory containing samples_*.json files',
    )
    parser.add_argument('--threshold', type=float, default=0.98, help='Cosine similarity threshold')
    parser.add_argument('--output', default='calibration_plot.png', help='Output image path')
    args = parser.parse_args()

    # If not specified, try common locations in priority order
    if args.samples_dir is None:
        candidates = [
            os.path.join(os.path.dirname(__file__), '..',
                         'funsearch-baseline', 'logs', 'baseline_50samples', 'samples'),
            os.path.join(os.path.dirname(__file__), '..', '..',
                         'resources', 'repos', 'funsearch-course', 'logs', 'baseline_50samples', 'samples'),
        ]
        for c in candidates:
            if os.path.isdir(c):
                args.samples_dir = c
                break
        if args.samples_dir is None:
            print("Cannot find default samples directory, please specify with --samples-dir")
            return

    print(f"Loading samples: {args.samples_dir}")
    samples = load_samples(args.samples_dir)
    print(f"Loaded {len(samples)} valid samples")

    if len(samples) < 2:
        print("Insufficient samples, at least 2 are required")
        return

    # Compute behavioral fingerprint for each program
    fingerprints = []
    valid_samples = []
    for s in samples:
        program_str = extract_program_str(s['function'])
        fp = compute_fingerprint(program_str, 'priority')
        if fp is not None:
            fingerprints.append(fp)
            valid_samples.append(s)
        else:
            print(f"  Sample {s['sample_order']} fingerprint computation failed, skipping")

    print(f"Successfully computed fingerprints: {len(fingerprints)}/{len(samples)}")

    # Convert to normalized vectors
    vectors = []
    for fp in fingerprints:
        vec = np.array(fp, dtype=np.float64)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        vectors.append(vec)
    vectors = np.array(vectors)

    # Compute cosine similarity and score difference for all pairs
    n = len(valid_samples)
    similarities = []
    score_diffs = []
    for i, j in combinations(range(n), 2):
        sim = float(np.dot(vectors[i], vectors[j]))
        diff = abs(valid_samples[i]['score'] - valid_samples[j]['score'])
        similarities.append(sim)
        score_diffs.append(diff)

    similarities = np.array(similarities)
    score_diffs = np.array(score_diffs)

    print(f"\nTotal pairs: {len(similarities)}")
    print(f"Similarity range: [{similarities.min():.4f}, {similarities.max():.4f}]")
    print(f"Score diff range: [{score_diffs.min():.2f}, {score_diffs.max():.2f}]")

    # Analyze threshold effectiveness
    above_threshold = similarities >= args.threshold
    n_above = above_threshold.sum()
    print(f"\nThreshold {args.threshold} analysis:")
    print(f"  Pairs above threshold: {n_above}/{len(similarities)}")
    if n_above > 0:
        diffs_above = score_diffs[above_threshold]
        print(f"  Score diffs for these pairs: mean={diffs_above.mean():.2f}, max={diffs_above.max():.2f}")
        print(f"  Proportion with score diff=0: {(diffs_above == 0).sum()}/{n_above}")

    # Try to plot scatter chart
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(similarities, score_diffs, alpha=0.5, s=10)
        ax.axvline(x=args.threshold, color='r', linestyle='--',
                   label=f'threshold={args.threshold}')
        ax.set_xlabel('Cosine Similarity')
        ax.set_ylabel('|Score Difference|')
        ax.set_title(f'Behavioral Fingerprint Similarity vs Score Difference (n={n})')
        ax.legend()
        plt.tight_layout()
        plt.savefig(args.output, dpi=150)
        print(f"\nScatter plot saved: {args.output}")
    except ImportError:
        print("\n[Note] matplotlib is not installed, skipping scatter plot. Install and re-run: pip install matplotlib")


if __name__ == '__main__':
    main()
