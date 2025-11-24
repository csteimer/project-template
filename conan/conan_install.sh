#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <profile> [extra conan args...]"
    echo "Known profiles: debug, release, asan, tsan, coverage, benchmark, ci-debug, all"
    exit 1
fi

PRESET="$1"
shift || true  # remaining args passed to conan install
EXTRA_ARGS=("$@")

run_conan_for_profile() {
    local profile="$1"
    shift || true  # remaining args: extra conan args

    local PROFILE_HOST
    local BUILD_DIR

    case "${profile}" in
      debug)
        PROFILE_HOST="gcc-debug"
        BUILD_DIR="build/debug"
        ;;

      release)
        PROFILE_HOST="gcc-release"
        BUILD_DIR="build/release"
        ;;

      asan)
        PROFILE_HOST="gcc-debug-asan"
        BUILD_DIR="build/asan"
        ;;

      tsan)
        PROFILE_HOST="gcc-debug-tsan"
        BUILD_DIR="build/tsan"
        ;;

      coverage)
        PROFILE_HOST="gcc-debug-coverage"
        BUILD_DIR="build/coverage"
        ;;

      benchmark)
        PROFILE_HOST="gcc-release"
        BUILD_DIR="build/benchmark"
        ;;

      ci-debug)
        PROFILE_HOST="gcc-debug"
        BUILD_DIR="build/ci-debug"
        ;;

      *)
        echo "Unknown profile: ${profile}"
        return 1
        ;;
    esac

    echo "==> Running conan install for profile '${profile}' (profile: ${PROFILE_HOST}, build dir: ${BUILD_DIR})"

    mkdir -p "${BUILD_DIR}"

    conan install . \
      -pr:h "conan/profiles/${PROFILE_HOST}" \
      -pr:b "conan/profiles/${PROFILE_HOST}" \
      -of "${BUILD_DIR}" \
      --build=missing \
      "$@"
}

if [[ "${PRESET}" == "all" ]]; then
    # List of all supported profiles (except "all" itself)
    PRESETS=(debug release asan tsan coverage benchmark ci-debug)
    for p in "${PRESETS[@]}"; do
        run_conan_for_profile "${p}" "${EXTRA_ARGS[@]}"
        echo
    done
else
    run_conan_for_profile "${PRESET}" "${EXTRA_ARGS[@]}"
fi
