"""阈值校准实验：相似度 vs 分数差散点图（回应助教 #4）。

用法:
    python scripts/calibration.py --samples-dir <samples目录>

流程:
    1. 加载 baseline 程序（从 samples_*.json 中提取 function 字段）
    2. 对每个程序运行 8 个 probe → 指纹向量
    3. 计算 C(n,2) 对的余弦相似度和分数差
    4. 输出散点图: x=余弦相似度, y=|分数差|
    5. 验证 0.98 阈值: 高相似度区域分数差应接近 0
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from itertools import combinations

import numpy as np

# 将仓库根目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.dedup.probing import compute_fingerprint, PROBING_INSTANCES


def load_samples(samples_dir: str) -> list[dict]:
    """从 samples_*.json 文件加载程序和分数。"""
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
    """从 function 字符串构建可执行的完整程序（包含 numpy import）。"""
    return f"import numpy as np\n\n{function_str}\n"


def main():
    parser = argparse.ArgumentParser(description='阈值校准实验')
    parser.add_argument(
        '--samples-dir',
        default=None,
        help='samples_*.json 文件所在目录',
    )
    parser.add_argument('--threshold', type=float, default=0.98, help='余弦相似度阈值')
    parser.add_argument('--output', default='calibration_plot.png', help='输出图片路径')
    args = parser.parse_args()

    # 未指定时，按优先级尝试常见位置
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
            print("找不到默认样本目录，请用 --samples-dir 指定")
            return

    print(f"加载样本: {args.samples_dir}")
    samples = load_samples(args.samples_dir)
    print(f"已加载 {len(samples)} 个有效样本")

    if len(samples) < 2:
        print("样本数不足，至少需要 2 个")
        return

    # 计算每个程序的行为指纹
    fingerprints = []
    valid_samples = []
    for s in samples:
        program_str = extract_program_str(s['function'])
        fp = compute_fingerprint(program_str, 'priority')
        if fp is not None:
            fingerprints.append(fp)
            valid_samples.append(s)
        else:
            print(f"  样本 {s['sample_order']} 指纹计算失败，跳过")

    print(f"成功计算指纹: {len(fingerprints)}/{len(samples)}")

    # 转为归一化向量
    vectors = []
    for fp in fingerprints:
        vec = np.array(fp, dtype=np.float64)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        vectors.append(vec)
    vectors = np.array(vectors)

    # 计算所有对的余弦相似度和分数差
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

    print(f"\n总配对数: {len(similarities)}")
    print(f"相似度范围: [{similarities.min():.4f}, {similarities.max():.4f}]")
    print(f"分数差范围: [{score_diffs.min():.2f}, {score_diffs.max():.2f}]")

    # 分析阈值效果
    above_threshold = similarities >= args.threshold
    n_above = above_threshold.sum()
    print(f"\n阈值 {args.threshold} 分析:")
    print(f"  超过阈值的配对数: {n_above}/{len(similarities)}")
    if n_above > 0:
        diffs_above = score_diffs[above_threshold]
        print(f"  这些配对的分数差: mean={diffs_above.mean():.2f}, max={diffs_above.max():.2f}")
        print(f"  分数差=0 的比例: {(diffs_above == 0).sum()}/{n_above}")

    # 尝试绘制散点图
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
        print(f"\n散点图已保存: {args.output}")
    except ImportError:
        print("\n[提示] 未安装 matplotlib，跳过散点图绘制。安装后重新运行: pip install matplotlib")


if __name__ == '__main__':
    main()
