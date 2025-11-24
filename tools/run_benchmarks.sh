#!/usr/bin/env bash
set -euo pipefail

# Simple helper script to configure, build, and run all benchmarks via the
# "run-benchmarks" target created by add_benchmark_aggregate_target().

# You can override these via environment variables:
#   BUILD_DIR=build/benchmark PRESET=benchmark ./tools/run_benchmarks.sh

BUILD_DIR="${BUILD_DIR:-build/benchmark}"
PRESET="${PRESET:-benchmark}"

echo "[run_benchmarks] Using BUILD_DIR='${BUILD_DIR}', PRESET='${PRESET}'"

# Configure if needed (if no CMake cache exists for that build dir)
if [[ ! -f "${BUILD_DIR}/CMakeCache.txt" ]]; then
    echo "[run_benchmarks] Configuring CMake with preset '${PRESET}'..."
    cmake --preset "${PRESET}"
fi

echo "[run_benchmarks] Building benchmarks..."
cmake --build --preset "${PRESET}"

echo "[run_benchmarks] Running 'run-benchmarks' target..."
cmake --build "${BUILD_DIR}" --target run-benchmarks

echo "[run_benchmarks] Done. JSON outputs should be in '${BUILD_DIR}' (e.g. *_bench.json)."
