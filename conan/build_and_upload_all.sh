#!/usr/bin/env bash
# Exit immediately on errors, undefined vars, or failed pipeline parts.
set -euo pipefail

# List of Conan *host profiles* for which we want to build and upload packages.
# These correspond to the configurations your project supports.
PROFILES=(
  gcc-debug
  gcc-debug-asan
  gcc-debug-msan
  gcc-debug-tsan
  gcc-release
)

# First argument = name of the Conan remote to upload to.
# If none is provided, use "my-remote" as default.
REMOTE="${1:-my-remote}"

# Loop through each profile and build/upload a package for it.
for p in "${PROFILES[@]}"; do
  echo "=== Building & uploading profile: ${p} ==="

  #
  # 1. Build the package using `conan create`
  #
  # `conan create` performs the full lifecycle:
  #   export -> install -> build -> package -> (optional) test_package
  #
  # -pr:h : host profile
  #         Defines the configuration of the *final* binary:
  #         (compiler, version, build_type, sanitizers, coverage, system libs)
  #
  # -pr:b : build profile
  #         Defines the environment used to *build* the package itself.
  #         This matters for cross-compilation, but in our case host = build
  #         so we reuse the same profile for deterministic builds.
  #
  # --build=missing :
  #         Build dependencies only when no compatible binary exists.
  #         Ensures reproducibility while keeping builds reasonably fast.
  #
  # This step:
  # -> Exports the recipe
  # -> Installs dependencies
  # -> Configures + builds via CMakeToolchain
  # -> Packages artifacts into the local Conan cache
  #
  conan create . \
    -pr:h "profiles/${p}" \
    -pr:b "profiles/${p}" \
    --build=missing

  #
  # 2. Upload the resulting package to the given remote
  #
  # -r REMOTE : upload destination
  # --confirm : skip interactive confirmations
  # --skip-upload-if-immutable : avoids re-uploading unchanged packages
  #
  # Note: "project-template/*" must match the package name/version namespace in the recipe.
  #
  conan upload "project-template/*" \
    -r "${REMOTE}" \
    --confirm \
    --skip-upload-if-immutable
done
