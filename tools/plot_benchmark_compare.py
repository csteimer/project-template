#!/usr/bin/env python3
"""
Compare two Google Benchmark JSON outputs and generate a speedup plot.

Usage:
    ./tools/plot_benchmark_compare.py \
        --baseline build/benchmark/example_benchmark_baseline.json \
        --current  build/benchmark/example_benchmark_bench.json \
        --output   benchmark_compare.png
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def load_benchmarks(path: Path, time_key: str = "real_time") -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    result = {}
    for entry in data.get("benchmarks", []):
        name = entry.get("name")
        if name is None:
            continue
        if time_key not in entry:
            continue
        result[name] = float(entry[time_key])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare Google Benchmark results and plot speedup."
    )
    parser.add_argument(
        "--baseline", type=Path, required=True, help="Baseline benchmark JSON file"
    )
    parser.add_argument(
        "--current", type=Path, required=True, help="Current benchmark JSON file"
    )
    parser.add_argument("--output", type=Path, required=True, help="Output PNG file")
    parser.add_argument(
        "--time-key",
        default="real_time",
        choices=["real_time", "cpu_time"],
        help="Which time field to use for comparison",
    )
    args = parser.parse_args()

    baseline = load_benchmarks(args.baseline, time_key=args.time_key)
    current = load_benchmarks(args.current, time_key=args.time_key)

    # intersection of names that exist in both runs
    common_names = sorted(set(baseline.keys()) & set(current.keys()))
    if not common_names:
        raise SystemExit(
            "No common benchmark names found between baseline and current."
        )

    ratios = []
    for name in common_names:
        base_t = baseline[name]
        cur_t = current[name]
        ratio = base_t / cur_t if cur_t != 0 else 0.0  # >1 => faster than baseline
        ratios.append(ratio)

    # Simple bar chart: x-axis = benchmark names, y = speedup factor
    fig, ax = plt.subplots(figsize=(max(6, len(common_names) * 0.6), 4))

    x_positions = range(len(common_names))
    ax.bar(x_positions, ratios)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(common_names, rotation=45, ha="right")

    ax.set_ylabel(f"Speedup vs baseline ({args.time_key})")
    ax.set_xlabel("Benchmark")
    ax.axhline(1.0, linestyle="--")
    ax.set_title("Benchmark comparison (baseline vs current)")

    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)


if __name__ == "__main__":
    main()
