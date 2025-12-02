#!/usr/bin/env python3
"""
Conan install helper for per-preset build directories.

This script is a small wrapper around `conan install`. For each logical build
preset (e.g. `debug`, `asan`, `benchmark`) it runs `conan install` and prepares
a dedicated output folder `build/<preset>`. That folder can then be used with:

  * `conan build . -of build/<preset>`
  * `cmake --build --preset <preset>` via the auto-generated `CMakeUserPresets.json`.

Preset ↔ profile mapping
------------------------

A "preset" is a logical build configuration name such as:

  - debug, release, asan, tsan, coverage, benchmark, iwyu, ci-debug, ...

Profiles are discovered from the local `profiles/` directory. For each profile
file, the script:

  * parses the `[options]` section,
  * looks for any key ending in `:cmake_presets_name`
    (e.g. `somepkg/*:cmake_presets_name`), or
  * falls back to the global key `cmake_presets_name`.

From this it builds a mapping:

    <preset_name> -> <profile_path>

Running the script
------------------

Example:

    ./conan_install.py debug

This will:

  * find the profile whose options set `cmake_presets_name=debug`,
  * use that profile as both Conan **build** and (by default) **host** profile,
  * create `build/debug` if needed, and
  * run:

        conan install . \
          -pr:h <profile_path> \
          -pr:b <profile_path> \
          -of build/debug \
          --build=missing \
          [extra args after '--']

As a result, `build/debug` becomes a self-contained Conan output folder for
`conan build` and CMake presets.

Cross compilation
-----------------

To use a different host profile while keeping the preset-derived build profile:

    ./conan_install.py benchmark --host-profile arm-gcc

where:

  * build profile  = profile with `cmake_presets_name=benchmark`
  * host profile   = `profiles/arm-gcc` (or a custom path)
  * build dir      = `build/benchmark`

Summary
-------

All actual build behavior (CMAKE_BUILD_TYPE, sanitizers, coverage, IWYU,
benchmark, CI flags, etc.) is defined in the Conan recipe and profiles.

This script only:

  1. Discovers participating profiles via their `cmake_presets_name` option.
  2. Maps each preset name to a profile file.
  3. Creates `build/<preset>` for the chosen (or all) presets.
  4. Runs `conan install` into that folder with suitable `-pr:h`, `-pr:b` and
     `-of` settings so `conan build` and CMake presets can be used consistently.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# NOTE: script is expected to live in <root>/conan/
SCRIPT_DIR = Path(__file__).resolve().parent  # <root>/conan
ROOT_DIR = SCRIPT_DIR.parent  # <root>
PROFILES_DIR = SCRIPT_DIR / "profiles"  # <root>/conan/profiles


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


def _parse_profile_options(profile_path: Path) -> dict[str, str]:
    """
    Parse the [options] section of a Conan profile file into a dict.

    The parser is intentionally simple and only understands lines like:

        key=value

    inside the [options] section. Comments (# or ;) and blank lines are ignored.
    """
    options: dict[str, str] = {}
    in_options = False

    try:
        text = profile_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Warning: could not read profile {profile_path}: {exc}")
        return options

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or line.startswith(";"):
            continue

        if line.startswith("[") and line.endswith("]"):
            in_options = line == "[options]"
            continue

        if not in_options:
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        options[key.strip()] = value.strip()

    return options


def discover_preset_profile_map() -> dict[str, Path]:
    """
    Scan all profiles in PROFILES_DIR and build a mapping:

        cmake_presets_name -> profile_path

    using either:
      - any key that ends with ':cmake_presets_name' (e.g. 'pkg/*:cmake_presets_name')
      - or the global key 'cmake_presets_name'

    If a profile defines multiple different cmake_presets_name values, this
    function will error out, as the mapping would be ambiguous.
    """
    if not PROFILES_DIR.is_dir():
        print(f"Profiles directory does not exist: {PROFILES_DIR}")
        sys.exit(1)

    mapping: dict[str, Path] = {}

    for profile_path in sorted(PROFILES_DIR.iterdir()):
        if not profile_path.is_file():
            continue

        options = _parse_profile_options(profile_path)

        # Collect all keys that look like *:cmake_presets_name
        pkg_keys = [k for k in options if k.endswith(":cmake_presets_name")]
        has_global = "cmake_presets_name" in options

        preset_value_raw = None

        if pkg_keys:
            # Prefer package-scoped form; error if multiple different ones exist
            if len(pkg_keys) > 1:
                values = {k: options[k] for k in pkg_keys}
                print(
                    "Error: profile defines multiple package-scoped "
                    "cmake_presets_name options:\n"
                    f"  profile: {profile_path}\n"
                    f"  values: {values}"
                )
                sys.exit(1)

            preset_value_raw = options[pkg_keys[0]]
        elif has_global:
            preset_value_raw = options["cmake_presets_name"]

        if not preset_value_raw:
            continue

        # Strip optional quotes: cmake_presets_name="benchmark"
        preset_name = preset_value_raw.strip().strip('"').strip("'")

        if not preset_name:
            continue

        if preset_name in mapping and mapping[preset_name] != profile_path:
            print(
                "Error: multiple profiles define the same "
                f"cmake_presets_name='{preset_name}':\n"
                f"  {mapping[preset_name]}\n"
                f"  {profile_path}"
            )
            sys.exit(1)

        mapping[preset_name] = profile_path

    if not mapping:
        print(
            "Error: no profiles with a cmake_presets_name option found "
            f"in {PROFILES_DIR}"
        )
    return mapping


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
    preset_to_profile: dict[str, Path],
    host_profile_override: Path | None,
    extra_args: list[str],
) -> None:
    """
    Execute `conan install` for a single logical preset.

    This function:
      - Resolves the build profile path from preset_to_profile.
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
    build_profile_path = preset_to_profile.get(preset)
    if build_profile_path is None:
        print(
            f"Error: no profile found that defines "
            f"cmake_presets_name={preset!r} in {PROFILES_DIR}"
        )
        sys.exit(1)

    if host_profile_override is not None:
        host_profile_path = host_profile_override
    else:
        host_profile_path = build_profile_path

    build_dir_path = ROOT_DIR / "build" / preset

    print(
        f"==> Running conan install for preset '{preset}'\n"
        f"    host profile:  {host_profile_path}\n"
        f"    build profile: {build_profile_path}\n"
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
          Logical preset name (as defined by `cmake_presets_name` in profiles),
          or 'all' to run installation for every discovered preset.

    Options:
      --host-profile <name-or-path>
          Optional Conan host profile override.
          If passed without a path separator, it is resolved relative to
          `profiles/` next to this script.
          If omitted, the preset's build profile is also used as host profile.

    Extra arguments:
      Any arguments appearing after a standalone '--' are forwarded verbatim to
      `conan install` (e.g. `--update`, `--build=missing`, etc.).

    Examples:
      conan_install.py debug
      conan_install.py release -- --update
      conan_install.py all
      conan_install.py benchmark --host-profile arm-gcc
    """
    parser = argparse.ArgumentParser(
        prog="conan_install.py",
        description=(
            "Run `conan install` for a given logical preset and populate "
            "`build/<preset>` with the Conan-generated toolchain and artifacts.\n\n"
            "Conan profiles are matched to CMake presets via their custom `cmake_presets_name` "
            "option. For each preset, the script executes:\n\n"
            "  conan install . -pr:h <host> -pr:b <build> -of build/<preset>\n\n"
            "This keeps Conan profiles, CMake presets and build folders aligned "
            "so you can later run `conan build` or `cmake --preset <preset>` "
            "without manual folder/profile management."
        ),
        epilog=(
            "Examples:\n"
            "  ./conan/conan_install.py debug\n"
            "  ./conan/conan_install.py release -- --update\n"
            "  ./conan/conan_install.py all\n"
            "  ./conan/conan_install.py benchmark --host-profile arm-gcc\n\n"
            "Preset discovery:\n"
            "  Profiles in 'profiles/' participate if their [options] section defines either:\n"
            "      somepkg/*:cmake_presets_name=<preset>\n"
            "  or:\n"
            "      cmake_presets_name=<preset>\n"
            "  The preset names used on the CLI should correspond exactly to these values."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "preset",
        help=(
            "Preset name to configure (e.g. debug, release, asan, benchmark, ...), "
            "or 'all' to configure every discovered preset."
        ),
    )

    parser.add_argument(
        "--host-profile",
        dest="host_profile",
        help=(
            "Conan host profile override. If a bare name (no '/' or '\\\\'), "
            "it is resolved under 'profiles/'. If omitted, the preset's build "
            "profile is reused as the host profile."
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
    args = parse_args()

    # Discover mapping from cmake_presets_name -> build profile path
    preset_to_profile = discover_preset_profile_map()
    available_presets = sorted(preset_to_profile.keys())

    # Resolve optional host profile override (for cross compilation)
    host_profile_override = resolve_host_profile_path(args.host_profile)

    # Extra args already cleaned in parse_args()
    extra_args = args.extra

    if args.preset == "all":
        print("Discovered presets:", ", ".join(available_presets))
        for preset in available_presets:
            run_conan_for_preset(
                preset,
                preset_to_profile,
                host_profile_override,
                extra_args,
            )
            print()
    else:
        preset = args.preset
        if preset not in preset_to_profile:
            print(
                f"Error: preset {preset!r} not found.\n"
                f"Available presets (from cmake_presets_name): "
                f"{', '.join(available_presets)}"
            )
            sys.exit(1)

        run_conan_for_preset(
            preset,
            preset_to_profile,
            host_profile_override,
            extra_args,
        )


if __name__ == "__main__":
    main()
