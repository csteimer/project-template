#!/usr/bin/env python3
"""
Benchmark helper tool for project_template.

Subcommands:

  run
    Configure (if needed), build, and run the benchmarks for the current
    working tree using:
      - CMake preset: 'benchmark'
      - Build dir:    'build/benchmark'
      - Target:       'run-benchmark'

    Example:
      ./tools/benchmark_runner.py run

  compare-json
    Compare two sets of Google Benchmark JSON outputs and print a table of
    speedup and percentage change per benchmark.

    You can pass either:
      - two JSON files, or
      - two directories that contain multiple JSON files (e.g. *_bench.json)

    Examples:
      ./tools/benchmark_runner.py compare-json --baseline base.json --current curr.json
      ./tools/benchmark_runner.py compare-json --baseline build/base/benchmark \
                                               --current  build/curr/benchmark

  compare-commits
    For each of two commits:
      - create (or reuse) a git worktree under build/benchmark/benchmark_worktrees/
      - configure, build, and run the 'benchmark' preset
      - collect JSON benchmark results from build/benchmark
    Then compare their performance and print a table.

    Example:
      ./tools/benchmark_runner.py compare-commits <baseline-commit> <current-commit>

Use -h/--help after the main command or any subcommand for detailed options:

  ./tools/benchmark_runner.py --help
  ./tools/benchmark_runner.py run --help
  ./tools/benchmark_runner.py compare-json --help
  ./tools/benchmark_runner.py compare-commits --help
"""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple

# Fixed configuration for this project
BUILD_SUBDIR = Path("build/benchmark")
CMAKE_PRESET = "benchmark"
BENCH_TARGET = "run-benchmark"
BENCH_WORKTREES_DIR_NAME = "benchmark_worktrees"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def run_cmd(cmd, *, cwd: Path | None = None) -> None:
    """Run a shell command, raising on failure, and echo it to stdout."""
    print(f"[bench] $ {' '.join(cmd)} (cwd={cwd or Path.cwd()})")
    subprocess.run(cmd, check=True, cwd=str(cwd) if cwd else None)


def ensure_repo_root() -> Path:
    """Return the Git repository root directory."""
    out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True)
    return Path(out.strip())


def short_ref(ref: str) -> str:
    """Return a short, filesystem-friendly representation of a Git ref."""
    out = subprocess.check_output(
        ["git", "rev-parse", "--short", ref],
        text=True,
    )
    return out.strip()


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def run_benchmarks(project_root: Path) -> None:
    build_dir = project_root / BUILD_SUBDIR
    print(f"[bench:run] Project root: {project_root}")
    print(f"[bench:run] Build dir:    {build_dir}")
    print(f"[bench:run] Preset:       {CMAKE_PRESET}")
    print(f"[bench:run] Target:       {BENCH_TARGET}")

    # 1) Run Conan install for this preset inside the given tree
    conan_install = project_root / "conan" / "conan_install.py"
    if not conan_install.is_file():
        raise SystemExit(
            f"Conan install script not found at '{conan_install}'. "
            "Make sure you run benchmark_runner.py from a repo that contains 'conan/conan_install.py'."
        )

    print(f"[bench:run] Running Conan install for preset '{CMAKE_PRESET}'...")
    run_cmd([str(conan_install), CMAKE_PRESET], cwd=project_root)

    # 2) Configure with the benchmark preset
    print(f"[bench:run] Configuring with preset '{CMAKE_PRESET}'...")
    run_cmd(["cmake", "--preset", CMAKE_PRESET], cwd=project_root)

    # 3) Build the preset
    print("[bench:run] Building benchmarks...")
    run_cmd(["cmake", "--build", "--preset", CMAKE_PRESET], cwd=project_root)

    # 4) Run the aggregate benchmark target
    print(f"[bench:run] Running aggregate benchmark target '{BENCH_TARGET}'...")
    run_cmd(
        ["cmake", "--build", str(build_dir), "--target", BENCH_TARGET],
        cwd=project_root,
    )

    print(
        f"[bench:run] Done. JSON outputs should be in '{build_dir}' (e.g. *_bench.json)."
    )


# ---------------------------------------------------------------------------
# Benchmark loading and comparison
# ---------------------------------------------------------------------------


def load_benchmarks_from_file(path: Path, time_key: str) -> Dict[str, float]:
    """
    Load Google Benchmark results from a single JSON file and return:

        benchmark_name -> time (float)

    Only entries that contain the requested time_key are included.
    Files that do not look like Google Benchmark JSON are ignored.
    """
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        print(
            f"[bench:load] Skipping {path}: JSON root is {type(data).__name__}, expected object."
        )
        return {}

    # Some versions use "benchmarks", some "benchmark"
    bench_key = None
    if "benchmark" in data:
        bench_key = "benchmark"
    elif "benchmarks" in data:
        bench_key = "benchmarks"

    if bench_key is None:
        print(
            f"[bench:load] Skipping {path}: no 'benchmark' or 'benchmarks' key found."
        )
        return {}

    result: Dict[str, float] = {}
    for entry in data.get(bench_key, []):
        name = entry.get("name")
        if not name:
            continue
        if time_key not in entry:
            continue
        result[name] = float(entry[time_key])

    return result


def load_benchmarks_from_dir(directory: Path, time_key: str) -> Dict[str, float]:
    """
    Load benchmark results from all *_bench.json files under a directory, recursively.

    Results are merged into a single mapping:

        benchmark_name -> time (float)

    Later files override earlier ones for duplicate names.
    """
    if not directory.is_dir():
        raise SystemExit(f"'{directory}' is not a directory.")

    # Search recursively for benchmark result files.
    json_paths = sorted(directory.rglob("*_bench.json"))

    if not json_paths:
        raise SystemExit(
            f"No benchmark JSON files matching '*_bench.json' found under '{directory}'."
        )

    merged: Dict[str, float] = {}
    for p in json_paths:
        print(f"[bench:load] Loading benchmarks from {p}")
        merged.update(load_benchmarks_from_file(p, time_key=time_key))

    if not merged:
        raise SystemExit(
            f"No benchmark entries found in JSON files under '{directory}'."
        )

    return merged


def compare_results(
    baseline: Dict[str, float],
    current: Dict[str, float],
) -> Dict[str, Tuple[float, float, float, float]]:
    """
    Compare two benchmark mappings.

    Returns a dict:
        name -> (baseline_time, current_time, speedup, percent_change)

    where:
        speedup        = baseline_time / current_time   ( >1 => faster )
        percent_change = (current_time - baseline_time) / baseline_time * 100
                         (negative => faster)
    """
    common = sorted(set(baseline.keys()) & set(current.keys()))
    if not common:
        raise SystemExit(
            "No common benchmark names found between baseline and current."
        )

    result: Dict[str, Tuple[float, float, float, float]] = {}
    for name in common:
        base_t = baseline[name]
        cur_t = current[name]
        if cur_t == 0:
            speedup = float("inf")
        else:
            speedup = base_t / cur_t

        if base_t == 0:
            percent = float("inf")
        else:
            percent = (cur_t - base_t) / base_t * 100.0

        result[name] = (base_t, cur_t, speedup, percent)

    return result


def print_comparison_table(
    comparison: Dict[str, Tuple[float, float, float, float]],
    time_key: str,
) -> None:
    """
    Pretty-print a comparison table to the terminal.

    Times are printed in the original units from the JSON (usually ns).
    """
    print()
    print(f"Comparison (time key: {time_key}, units as in JSON, typically ns)")
    print("=" * 80)
    header = (
        f"{'Benchmark':40} {'baseline':>14} {'current':>14} {'speedup':>10} {'Δ %':>10}"
    )
    print(header)
    print("-" * 80)

    speedups = []

    for name, (base_t, cur_t, speedup, percent) in comparison.items():
        speedups.append(speedup if speedup != float("inf") else 0.0)
        percent_str = " inf" if percent == float("inf") else f"{percent:+.2f}"
        speedup_str = "  inf" if speedup == float("inf") else f"{speedup:.3f}"
        print(
            f"{name:40} "
            f"{base_t:14.3f} "
            f"{cur_t:14.3f} "
            f"{speedup_str:>10} "
            f"{percent_str:>10}"
        )

    print("-" * 80)
    if speedups:
        finite = [s for s in speedups if s not in (0.0, float("inf"))]
        if finite:
            avg_speedup = sum(finite) / len(finite)
            avg_percent = (1.0 / avg_speedup - 1.0) * -100.0  # derived for info
            print(
                f"{'Average (over common benchmarks)':40} "
                f"{'':14} {'':14} {avg_speedup:>10.3f} {avg_percent:>10.2f}"
            )
    print("=" * 80)
    print()


# ---------------------------------------------------------------------------
# compare-json subcommand
# ---------------------------------------------------------------------------


def handle_compare_json(args: argparse.Namespace) -> None:
    """
    Compare benchmarks from two JSON files or directories and print a table.
    """
    time_key = args.time_key

    base_path: Path = args.baseline
    curr_path: Path = args.current

    if base_path.is_dir():
        baseline = load_benchmarks_from_dir(base_path, time_key=time_key)
    else:
        baseline = load_benchmarks_from_file(base_path, time_key=time_key)

    if curr_path.is_dir():
        current = load_benchmarks_from_dir(curr_path, time_key=time_key)
    else:
        current = load_benchmarks_from_file(curr_path, time_key=time_key)

    comparison = compare_results(baseline, current)
    print_comparison_table(comparison, time_key=time_key)


# ---------------------------------------------------------------------------
# compare-commits subcommand
# ---------------------------------------------------------------------------


def run_benchmarks_for_commit(ref: str, time_key: str) -> Dict[str, float]:
    """
    Create or reuse a git worktree for a given ref, run benchmarks there,
    and return the loaded benchmark results from build/benchmark.
    """
    repo_root = ensure_repo_root()
    short = short_ref(ref)

    # Worktrees live under: build/benchmark/benchmark_worktrees/<short-ref>
    worktrees_root = repo_root / BUILD_SUBDIR / BENCH_WORKTREES_DIR_NAME
    worktrees_root.mkdir(parents=True, exist_ok=True)

    worktree_dir = worktrees_root / short

    if not worktree_dir.exists():
        print(f"[bench:commits] Creating worktree for '{ref}' at '{worktree_dir}'...")
        run_cmd(
            ["git", "worktree", "add", "--detach", str(worktree_dir), ref],
            cwd=repo_root,
        )
    else:
        print(
            f"[bench:commits] Reusing existing worktree '{worktree_dir}' for ref '{ref}'."
        )

    run_benchmarks(worktree_dir)

    results_dir = worktree_dir / BUILD_SUBDIR
    return load_benchmarks_from_dir(results_dir, time_key=time_key)


def handle_compare_commits(args: argparse.Namespace) -> None:
    """
    Run benchmarks for two commits (via git worktrees) and compare the results.
    """
    baseline_ref = args.baseline_commit
    current_ref = args.current_commit
    time_key = args.time_key

    print(f"[bench:commits] Baseline commit: {baseline_ref}")
    print(f"[bench:commits] Current  commit: {current_ref}")
    print(f"[bench:commits] Time key:        {time_key}")

    baseline = run_benchmarks_for_commit(baseline_ref, time_key=time_key)
    current = run_benchmarks_for_commit(current_ref, time_key=time_key)

    comparison = compare_results(baseline, current)
    print_comparison_table(comparison, time_key=time_key)


# ---------------------------------------------------------------------------
# CLI setup
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark helper for project_template.\n\n"
            "Subcommands:\n"
            "  run             Configure, build, and run benchmarks for current tree.\n"
            "  compare-json    Compare benchmark JSON outputs (files or directories).\n"
            "  compare-commits Run benchmarks for two Git commits and compare results.\n\n"
            "Use 'benchmark_runner.py <command> -h' for details on each subcommand."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Subcommand to execute. Use '<command> -h' for detailed help.",
    )

    # run
    subparsers.add_parser(
        "run",
        help="Configure, build, and run benchmarks for the current working tree.",
        description=(
            "Configure (if needed), build, and run benchmarks for the current Git checkout.\n\n"
            "Uses CMake preset 'benchmark', build directory 'build/benchmark', and target 'run-benchmark'."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # compare-json
    compare_json_parser = subparsers.add_parser(
        "compare-json",
        help="Compare two sets of benchmark JSON outputs (files or directories).",
        description=(
            "Compare benchmark performance between two JSON sources.\n\n"
            "Each source can be either a single JSON file or a directory containing multiple JSON files "
            "(e.g. '*_bench.json'). Only benchmarks present in both sets are compared.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    compare_json_parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Baseline JSON file or directory containing benchmark JSON files.",
    )
    compare_json_parser.add_argument(
        "--current",
        type=Path,
        required=True,
        help="Current JSON file or directory containing benchmark JSON files.",
    )
    compare_json_parser.add_argument(
        "--time-key",
        default="real_time",
        choices=["real_time", "cpu_time"],
        help=(
            "JSON time field to use for comparison. "
            "Use 'real_time' for wall-clock time or 'cpu_time' for CPU time. "
            "Default: 'real_time'."
        ),
    )

    # compare-commits
    compare_commits_parser = subparsers.add_parser(
        "compare-commits",
        help="Run benchmarks for two Git commits and compare results.",
        description=(
            "Run benchmarks for two Git commits and compare their performance.\n\n"
            "For each commit, a git worktree is created (or reused) under "
            "'build/benchmark/benchmark_worktrees/<short-ref>'. "
            "Benchmarks are built and executed there using the 'benchmark' preset. "
            "JSON outputs are loaded from 'build/benchmark'.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    compare_commits_parser.add_argument(
        "baseline_commit",
        help="Baseline Git commit (hash, tag, or branch name).",
    )
    compare_commits_parser.add_argument(
        "current_commit",
        help="Current Git commit (hash, tag, or branch name) to compare against the baseline.",
    )
    compare_commits_parser.add_argument(
        "--time-key",
        default="real_time",
        choices=["real_time", "cpu_time"],
        help=(
            "JSON time field to use for comparison. "
            "Use 'real_time' for wall-clock time or 'cpu_time' for CPU time. "
            "Default: 'real_time'."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "run":
        project_root = ensure_repo_root()
        run_benchmarks(project_root)
    elif args.command == "compare-json":
        handle_compare_json(args)
    elif args.command == "compare-commits":
        handle_compare_commits(args)
    else:
        raise SystemExit(f"Unknown command: {args.command!r}")


if __name__ == "__main__":
    main()
