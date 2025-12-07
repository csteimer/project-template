#!/usr/bin/env python3
"""
Conan release automation script.

This script:

  - Detects available Conan profile files under `conan/profiles/`
  - Detects the package name from the local Conan recipe via `conan inspect`
  - Builds the Conan package for one or more *build profiles*
  - Optionally uploads the resulting packages to a configured remote
  - Uses the same profile for host and build by default
  - Optionally supports cross-compilation:
      * build profile: toolchain/environment building the package
      * host profile:  system where the package will finally run

Usage examples (from the project root):

  # Build and upload for all profiles under conan/profiles/ (host == build)
  ./conan/release_conan_packages.py --remote local-test

  # Build only for one profile (host == build)
  ./conan/release_conan_packages.py --remote local-test --profile gcc-release

  # Build for multiple build profiles (host == build)
  ./conan/release_conan_packages.py --remote local-test -p gcc-debug -p gcc-release

  # Build only (no upload), host == build (remote not needed)
  ./conan/release_conan_packages.py --disable-upload

  # Cross-compilation: build with gcc-debug, target host profile gcc-release
  ./conan/release_conan_packages.py --remote local-test --profile gcc-debug --host-profile gcc-release
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional


def run(cmd: List[str], stage: str) -> None:
    """
    Run a subprocess command for a specific stage.

    - stage: short label describing where we are (e.g. "create: gcc-debug").
    - The full command is printed before execution.
    - Any non-zero exit code terminates the script with a clear, stage-specific message.
    """
    print(f"[{stage}] Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print("")
        print(
            f"ERROR during stage '{stage}': command failed with exit code {exc.returncode}"
        )
        print("Command was:")
        print(" ", " ".join(cmd))
        print("")
        print("Please check the command output above for details.")
        sys.exit(exc.returncode)


def run_capture(cmd: List[str], stage: str) -> str:
    """
    Run a subprocess command for a specific stage and capture stdout.

    If the command fails, print a stage-specific error and exit.
    """
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as exc:
        print("")
        print(
            f"ERROR during stage '{stage}': command failed with exit code {exc.returncode}"
        )
        print("Command was:")
        print(" ", " ".join(cmd))
        print("")
        print("Command stdout:")
        print(exc.stdout or "(empty)")
        print("")
        print("Command stderr:")
        print(exc.stderr or "(empty)")
        sys.exit(exc.returncode)


def ensure_path_exists(path: Path, description: str) -> None:
    """
    Ensure a path exists.

    - description: short description of what we expected (e.g. "profile directory").

    If the path does not exist:
      - prints a clear error including the missing path and description,
      - suggests running the script from the project root,
      - and exits.
    """
    if not path.exists():
        print("ERROR:", description, "not found.")
        print("Missing path:", path)
        print("")
        print("This script expects to be run from the project root directory.")
        print("Example:")
        print("  ./conan/release_conan_packages.py [--remote <remote-name>] [options]")
        sys.exit(1)


def detect_package_name() -> str:
    """
    Detect the Conan package name from the local recipe via `conan inspect`.

    Uses (Conan 2 syntax):
      conan inspect . --format=json

    Fails if:
      - conan is not installed or not in PATH, or
      - the current directory is not a valid Conan recipe, or
      - the 'name' attribute cannot be read.
    """
    stage = "detect-package-name"
    cmd = ["conan", "inspect", ".", "--format=json"]
    stdout = run_capture(cmd, stage=stage)

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        print("")
        print(
            f"ERROR during stage '{stage}': failed to parse JSON from 'conan inspect'."
        )
        print("Raw output was:")
        print(stdout)
        print("")
        print("JSON error:", exc)
        sys.exit(1)

    name = data.get("name")
    if not name:
        print("")
        print(
            f"ERROR during stage '{stage}': 'name' attribute not found in 'conan inspect' output."
        )
        print("Inspect output keys were:", ", ".join(sorted(data.keys())))
        sys.exit(1)

    print(f"[{stage}] Detected package name:", name)
    return name


def detect_profiles() -> List[str]:
    """
    Detect available Conan profiles in ./conan/profiles/.

    Returns:
        A sorted list of profile file names.

    Fails if:
      - the directory does not exist, or
      - no profile files are found.
    """
    profiles_dir = Path("conan") / "profiles"

    ensure_path_exists(profiles_dir, "profile directory")

    profiles = [
        p.name
        for p in profiles_dir.iterdir()
        if p.is_file() and not p.name.startswith(".")
    ]

    if not profiles:
        print("ERROR during profile detection: no profile files found.")
        print("Checked directory:", profiles_dir)
        print("Expected one or more files like 'gcc-debug', 'gcc-release', etc.")
        sys.exit(1)

    return sorted(profiles)


def detect_remotes() -> Tuple[List[str], str]:
    """
    Detect available Conan remotes using `conan remote list`.

    Returns:
        - list of remote names
        - raw text output from `conan remote list`
    """
    stage = "detect-remotes"
    stdout = run_capture(["conan", "remote", "list"], stage=stage)

    names: List[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        name = line.split(":", 1)[0].strip()
        if name:
            names.append(name)

    return names, stdout


def build_and_upload(
    remote: Optional[str],
    package_name: str,
    build_profiles: List[str],
    do_upload: bool,
    host_profile_name: Optional[str],
) -> None:
    """
    Build and (optionally) upload the package for each selected build profile.

    Profiles:
      - build profile: environment/toolchain used to compile the package
      - host profile:  system where the package will run
                       (if host_profile_name is None, host == build)
    """
    print("")
    print("Package name:", package_name)
    print("Build profiles:", ", ".join(build_profiles))
    if host_profile_name is None:
        print("Host profile: same as build profile for each entry.")
    else:
        print("Host profile (target system):", host_profile_name)
    if do_upload:
        print("Target remote:", remote)
        print("Upload enabled.")
    else:
        print("Upload disabled (build-only run).")
    print("")

    for build_profile in build_profiles:
        print("------------------------------------------------------------")
        print("Processing build profile:", build_profile)
        print("------------------------------------------------------------")

        build_profile_path = Path("conan") / "profiles" / build_profile
        ensure_path_exists(
            build_profile_path, f"build profile file for '{build_profile}'"
        )

        # Determine host profile (for the target system)
        if host_profile_name is None:
            host_profile_path = build_profile_path
            host_profile_effective = build_profile
        else:
            host_profile_path = Path("conan") / "profiles" / host_profile_name
            host_profile_effective = host_profile_name
            ensure_path_exists(
                host_profile_path, f"host profile file for '{host_profile_name}'"
            )

        print(
            "Using build profile:",
            build_profile_path,
            "and host profile:",
            host_profile_path,
            "(build:",
            build_profile,
            "-> host:",
            host_profile_effective,
            ")",
        )

        build_profile_str = str(build_profile_path)
        host_profile_str = str(host_profile_path)

        # Stage: build (conan create)
        create_stage = f"create: build={build_profile}, host={host_profile_effective}"
        run(
            [
                "conan",
                "create",
                ".",
                "-pr:h",
                host_profile_str,
                "-pr:b",
                build_profile_str,
                "--build=missing",
            ],
            stage=create_stage,
        )

        if do_upload:
            # Stage: upload
            upload_stage = (
                f"upload: build={build_profile}, host={host_profile_effective}"
            )
            run(
                [
                    "conan",
                    "upload",
                    package_name + "/*",
                    "-r",
                    remote,  # type: ignore[arg-type]
                    "--confirm",
                    "--skip-upload-if-immutable",
                ],
                stage=upload_stage,
            )
        else:
            print(
                f"[skip-upload] Skipping upload for build profile '{build_profile}' "
                f"(host profile '{host_profile_effective}'; upload disabled)."
            )

    print("")
    print("All packages were built.")
    if do_upload:
        print("Upload commands were executed for remote:", remote)
    else:
        print("Upload was disabled by command line option.")
    print("Build profiles processed:", ", ".join(build_profiles))
    if host_profile_name is None:
        print("Host profile mapping: host == build for all entries.")
    else:
        print("Host profile used for all builds:", host_profile_name)


def build_parser() -> argparse.ArgumentParser:
    """
    Create and return the top-level argument parser.
    Separated so we can attach argcomplete to the same parser instance.
    """
    parser = argparse.ArgumentParser(
        description="Build and upload Conan packages for selected profiles."
    )

    parser.add_argument(
        "-r",
        "--remote",
        required=False,
        help="Conan remote to upload to (for example: local-test, conancenter, ...). "
        "Required unless --disable-upload is given.",
    )

    parser.add_argument(
        "-p",
        "--profile",
        dest="profiles",
        action="append",
        help=(
            "Conan build profile name under 'conan/profiles/'. "
            "May be specified multiple times. "
            "If omitted, all available profiles are used as build profiles."
        ),
    )

    parser.add_argument(
        "--host-profile",
        dest="host_profile",
        help=(
            "Conan host profile name under 'conan/profiles/'. "
            "Defines the target system where the package will run. "
            "If omitted, host profile == build profile (no cross-compilation)."
        ),
    )

    parser.add_argument(
        "--disable-upload",
        action="store_true",
        help="Disable the upload step. Only 'conan create' will be executed for each build profile.",
    )

    return parser


# Build the global parser once so argcomplete can hook into it
parser = build_parser()

# Optional: enable shell auto-completion via argcomplete, if installed.
try:
    import argcomplete  # type: ignore[import]

    argcomplete.autocomplete(parser)
except ImportError:
    pass


def parse_args() -> argparse.Namespace:
    """Thin wrapper around the global parser to keep main() unchanged."""
    return parser.parse_args()


def main() -> None:
    # Stage: argument parsing
    args = parse_args()

    # Determine whether we intend to upload
    do_upload = not args.disable_upload

    # If we intend to upload, a remote must be provided
    if do_upload and not args.remote:
        print("ERROR: --remote is required unless --disable-upload is specified.")
        sys.exit(1)

    # Stage: detect package name
    package_name = detect_package_name()

    # Stage: profile detection
    available_profiles = detect_profiles()

    # Stage: build profile selection
    if args.profiles is None:
        print("No build profiles specified on CLI.")
        print("Using all detected profiles from:", Path("conan") / "profiles")
        for p in available_profiles:
            print(" ", p)
        selected_build_profiles = available_profiles
    else:
        missing = [p for p in args.profiles if p not in available_profiles]
        if missing:
            print("ERROR during profile selection: requested build profiles not found:")
            for m in missing:
                print(" ", m)
            print("")
            print("Available profiles are:")
            for ap in available_profiles:
                print(" ", ap)
            sys.exit(1)

        selected_build_profiles = args.profiles

    # Stage: host profile validation (if provided)
    host_profile_name: Optional[str] = None
    if args.host_profile is not None:
        if args.host_profile not in available_profiles:
            print("ERROR: Requested host profile not found:", args.host_profile)
            print("")
            print("Available profiles are:")
            for ap in available_profiles:
                print(" ", ap)
            sys.exit(1)
        host_profile_name = args.host_profile

    # Stage: remote validation (only relevant if we intend to upload)
    if do_upload:
        remote_names, raw_remote_list = detect_remotes()
        if args.remote not in remote_names:
            print("")
            print(f"ERROR: Conan remote '{args.remote}' not found.")
            print("Available remotes are:")
            for rn in remote_names:
                print(" ", rn)
            print("")
            print("Full output of 'conan remote list':")
            print(raw_remote_list)
            sys.exit(1)

    # Stage: build + (optional) upload for selected profiles
    build_and_upload(
        args.remote, package_name, selected_build_profiles, do_upload, host_profile_name
    )


if __name__ == "__main__":
    main()
