#!/usr/bin/env python3
"""
Conan install helper for per-preset build directories.

This script is a small wrapper around `conan install`. For each logical build
preset (e.g. `debug`, `asan`, `benchmark`) it runs `conan install` and prepares
a dedicated output folder `build/<preset>`. That folder can then be used with:

  * `conan build . -of build/<preset>`
  * `cmake --build --preset <preset>` via the auto-generated presets.

Preset ↔ profile mapping
------------------------

We keep the mapping explicit and simple:

    PRESET_PROFILE_MAP = {
        "debug":    "gcc-debug",
        "release":  "gcc-release",
        "asan":     "gcc-debug",
        "tsan":     "gcc-debug",
        "coverage": "gcc-debug",
        "benchmark": "gcc-release",
        "iwyu":     "gcc-debug",
        "ci-debug": "gcc-debug",
    }

Meaning:

  * The *build directory* is always `build/<preset>` (e.g. `build/asan`).
  * The *Conan profile* used is `conan/profiles/<profile_name>`.
  * Multiple presets can share the same profile (e.g. asan/tsan/coverage share gcc-debug).

Running the script
------------------

Examples:

    ./conan/conan_install.py debug
    ./conan/conan_install.py release
    ./conan/conan_install.py asan
    ./conan/conan_install.py all

Each call will:

  * resolve the profile from PRESET_PROFILE_MAP,
  * use that profile as both Conan **build** and (by default) **host** profile,
  * create `build/<preset>` if needed, and
  * run:

        conan install . \
          -pr:h conan/profiles/<profile> \
          -pr:b conan/profiles/<profile> \
          -of build/<preset> \
          --build=missing \
          [extra args after '--']

Cross compilation
-----------------

To use a different host profile while keeping the preset-derived build profile:

    ./conan/conan_install.py benchmark --host-profile arm-gcc

where:

  * build profile  = PRESET_PROFILE_MAP["benchmark"] (e.g. gcc-release)
  * host profile   = `conan/profiles/arm-gcc` (or a custom path)
  * build dir      = `build/benchmark`

Note: this script expects to be run from an active Python virtual environment.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# NOTE: script is expected to live in <root>/conan/
SCRIPT_DIR = Path(__file__).resolve().parent  # <root>/conan
ROOT_DIR = SCRIPT_DIR.parent  # <root>
PROFILES_DIR = SCRIPT_DIR / "profiles"  # <root>/conan/profiles

# ------------------------------------------------------------------------------
# Explicit mapping: <preset name> -> <Conan profile name>
# Adjust this dictionary to match your profiles under conan/profiles/.
# ------------------------------------------------------------------------------
PRESET_PROFILE_MAP: dict[str, str] = {
    # Base configs
    "debug": "gcc-debug",
    "release": "gcc-release",
    # Debug-derived feature presets
    "asan": "gcc-debug",
    "tsan": "gcc-debug",
    "coverage": "gcc-debug",
    "iwyu": "gcc-debug",
    "ci-debug": "gcc-debug",
    # Release-derived feature presets
    "benchmark": "gcc-release",
}


def ensure_venv_active() -> None:
    """
    Ensure a Python virtual environment is active.

    Heuristics:
      - For venv/virtualenv: VIRTUAL_ENV is set.
      - For stdlib venv: sys.prefix != sys.base_prefix.

    If no venv is detected, print a helpful error message and exit.
    """
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    in_venv = os.environ.get("VIRTUAL_ENV") is not None or sys.prefix != base_prefix

    if not in_venv:
        print("Error: no active Python virtual environment detected.\n")
        print("A venv should be available under .venv after running:")
        print("  ./setup_dev_env.sh")
        print("\nThen activate it before calling this script:")
        print("  source .venv/bin/activate\n")
        sys.exit(1)


def run(cmd: list[str]) -> None:
    """
    Run a subprocess command and abort on error.

    - The full command is echoed to stdout before execution.
    - Any non-zero exit code terminates the script with the same code.
    """
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"\nCommand failed with exit code {exc.returncode}")
        sys.exit(exc.returncode)


def resolve_host_profile_path(arg: str | None) -> Path | None:
    """
    Resolve a host profile argument to a Path.

    Rules:
      - If arg is None: return None (no override, use build profile for host).
      - If arg contains a path separator, treat it as a direct path.
      - Otherwise, treat it as a profile name under PROFILES_DIR.
    """
    if arg is None:
        return None

    candidate = Path(arg)
    if candidate.is_file():
        return candidate

    # No file at the direct path; if it looks like a bare name, resolve under PROFILES_DIR.
    if "/" not in arg and "\\" not in arg:
        candidate = PROFILES_DIR / arg
        if candidate.is_file():
            return candidate

    print(f"Error: host profile '{arg}' could not be resolved to a file.")
    print(f"Tried: {Path(arg)!s} and {PROFILES_DIR / arg}")
    sys.exit(1)


def run_conan_for_preset(
    preset: str,
    host_profile_override: Path | None,
    extra_args: list[str],
) -> None:
    """
    Execute `conan install` for a single logical preset.

    This function:
      - Resolves the Conan profile name from PRESET_PROFILE_MAP.
      - Resolves the host profile path (either override or same as build profile).
      - Uses 'build/<preset>' as the build directory.
      - Ensures the build directory exists.
      - Invokes `conan install` with:
          - `-pr:h` pointing to the host profile
          - `-pr:b` pointing to the build profile
          - `-of` pointing to 'build/<preset>'
          - `--build=missing` to build missing dependencies
          - any additional args forwarded from the CLI.
    """
    profile_name = PRESET_PROFILE_MAP.get(preset)
    if profile_name is None:
        print(
            f"Error: preset {preset!r} is not defined in PRESET_PROFILE_MAP.\n"
            f"Known presets: {', '.join(sorted(PRESET_PROFILE_MAP.keys()))}"
        )
        sys.exit(1)

    build_profile_path = PROFILES_DIR / profile_name
    if not build_profile_path.is_file():
        print(
            f"Error: Conan profile for preset {preset!r} not found:\n"
            f"  expected file: {build_profile_path}"
        )
        sys.exit(1)

    if host_profile_override is not None:
        host_profile_path = host_profile_override
    else:
        host_profile_path = build_profile_path

    build_dir_path = ROOT_DIR / "build" / preset

    print(
        f"==> Running conan install for preset '{preset}'\n"
        f"    build profile: {build_profile_path}\n"
        f"    host profile:  {host_profile_path}\n"
        f"    build dir:     {build_dir_path}"
    )

    build_dir_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        "conan",
        "install",
        ".",
        "-pr:h",
        str(host_profile_path),
        "-pr:b",
        str(build_profile_path),
        "-of",
        str(build_dir_path),
        "--build=missing",
    ]

    # Forward any extra CLI arguments directly to `conan install`.
    if extra_args:
        cmd.extend(extra_args)

    run(cmd)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the Conan preset installer.

    Positional arguments:
      preset
          Logical preset name (one of PRESET_PROFILE_MAP keys), or 'all' to
          run installation for every known preset. If omitted, the script will
          list all available presets and exit.

    Options:
      --host-profile <name-or-path>
          Optional Conan host profile override.
          If passed without a path separator, it is resolved relative to
          `conan/profiles/` next to this script.
          If omitted, the preset's build profile is also used as host profile.

    Extra arguments:
      Any arguments appearing after a standalone '--' are forwarded verbatim to
      `conan install` (e.g. `--update`, `--build=missing`, etc.).
    """
    parser = argparse.ArgumentParser(
        prog="conan_install.py",
        description=(
            "Run `conan install` for a given logical preset and populate "
            "`build/<preset>` with the Conan-generated toolchain and artifacts.\n\n"
            "Preset → profile mapping is defined explicitly in PRESET_PROFILE_MAP "
            "at the top of this script."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "preset",
        nargs="?",
        help=(
            "Preset name to configure (e.g. debug, release, asan, coverage, ...), "
            "or 'all' to configure every known preset. "
            "If omitted, available presets will be listed."
        ),
    )

    parser.add_argument(
        "--host-profile",
        dest="host_profile",
        help=(
            "Conan host profile override. If a bare name (no '/' or '\\\\'), "
            "it is resolved under 'conan/profiles/'. If omitted, the preset's "
            "build profile is reused as the host profile."
        ),
    )

    # Capture unknown arguments for forwarding into `conan install`.
    args, extra = parser.parse_known_args()

    # Strip leading `--` if present before forwarding to Conan.
    if extra and extra[0] == "--":
        extra = extra[1:]
    args.extra = extra

    return args


def main() -> None:
    # Allow users to see help without requiring an active venv.
    if not any(a in ("-h", "--help") for a in sys.argv[1:]):
        ensure_venv_active()

    args = parse_args()

    available_presets = sorted(PRESET_PROFILE_MAP.keys())

    # If no preset was given, show a friendly message with available presets.
    if args.preset is None:
        print("Error: no preset specified.\n")
        if available_presets:
            print("Available presets (from PRESET_PROFILE_MAP):")
            print("  - all (installs all presets listed below)")
            for p in available_presets:
                print(f"  - {p}")
            print("\nUsage examples:")
            print("  ./conan/conan_install.py debug")
            print("  ./conan/conan_install.py release -- --update")
            print("  ./conan/conan_install.py all")
        else:
            print("PRESET_PROFILE_MAP is empty.")
        sys.exit(1)

    # Resolve optional host profile override (for cross compilation)
    host_profile_override = resolve_host_profile_path(args.host_profile)
    extra_args = args.extra

    if args.preset == "all":
        print("Presets to install:", ", ".join(available_presets))
        for preset in available_presets:
            run_conan_for_preset(
                preset=preset,
                host_profile_override=host_profile_override,
                extra_args=extra_args,
            )
            print()
    else:
        preset = args.preset
        if preset not in PRESET_PROFILE_MAP:
            print(
                f"Error: preset {preset!r} not found in PRESET_PROFILE_MAP.\n"
                f"Available presets: {', '.join(available_presets)}"
            )
            sys.exit(1)

        run_conan_for_preset(
            preset=preset,
            host_profile_override=host_profile_override,
            extra_args=extra_args,
        )


if __name__ == "__main__":
    main()
