#!/usr/bin/env bash
set -euo pipefail

PROFILES=(
  gcc-debug
  gcc-debug-asan
  gcc-debug-tsan
  gcc-release
)

REMOTE="${1:-my-remote}"

for p in "${PROFILES[@]}"; do
  echo "=== Building & uploading profile: ${p} ==="
  conan create . -pr:h "profiles/${p}" -pr:b default --build=missing
  conan upload "mylib/*" -r "${REMOTE}" --confirm --skip-upload-if-immutable
done
