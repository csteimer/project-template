"""
Conan recipe for the project-template package.

Key points:

- settings = ("os", "arch", "compiler", "build_type")
    These describe the *binary configuration* the package depends on:
        - os:       Target operating system (Linux, Windows, macOS, ...)
        - arch:     Target architecture (x86_64, armv8, ...)
        - compiler: Compiler family + version (gcc, clang, msvc, ...)
        - build_type: Build configuration (Debug, Release, ...)

    Conan uses these settings to:
        - Select binary-compatible prebuilt packages
        - Rebuild dependencies when needed for a given configuration
        - Generate a CMake toolchain with matching flags
        - Keep binaries reproducible across profiles/presets

- exports_sources:
    Files that are exported into the recipe’s source folder. This includes
    CMakeLists, presets, source code, tests and custom cmake/conan helpers.

- requires / default_options:
    External *runtime* dependencies from ConanCenter and their options.
    These are propagated transitively to consumers of this package.

- test_requires:
    Test-only dependencies (e.g. gtest, benchmark). These are used when
    building/testing this package, but are **not** propagated to packages
    that depend on project-template.

- Versioning:
    Determined automatically from Git via set_version(), or overridden by
    PKG_VERSION.

- Package contents:
    We build via CMake (toolchain+deps) and call `cmake --install`, plus
    we copy the LICENSE and record the Git commit used to create the package.
"""

import os
import subprocess

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake
from conan.tools.files import copy, save


class Pkg(ConanFile):
    name = "project-template"
    version = None  # This is set automatically by set_version()

    # Settings describe the binary configuration this package depends on.
    settings = "os", "arch", "compiler", "build_type"

    exports_sources = (
        "CMakeLists.txt",
        "CMakePresets.json",
        "src/*",
        "tests/*",
        "cmake/*",
        "conan/*",
    )

    # Runtime Conan dependencies (propagated transitively to consumers)
    requires = (
        "spdlog/1.13.0",
        "magic_enum/0.9.5",
        "yaml-cpp/0.8.0",
    )

    # Test-only dependencies (NOT propagated to consumers)
    test_requires = (
        "gtest/1.17.0",
        "benchmark/1.9.4",
    )

    # Specify spdlog as header-only
    default_options = {
        "spdlog/*:header_only": True,
    }

    def set_version(self):
        """
        Versioning rules:
        1. If env var PKG_VERSION is set -> use that verbatim.
        2. Otherwise:
           - If HEAD is exactly on a tag -> use that tag as the version.
           - Otherwise -> use 'latest'.
        """
        # 1) Explicit override from environment
        env_version = os.getenv("PKG_VERSION")
        if env_version:
            self.version = env_version
            return

        # 2) Check whether HEAD is exactly at some tag
        try:
            exact_tag = (
                subprocess.check_output(
                    ["git", "describe", "--tags", "--exact-match"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
            # If this succeeds, we're on a tagged commit
            self.version = exact_tag
        except Exception:
            # Not exactly on any tag, or not a git repo -> generic 'latest'
            self.version = "latest"

    def layout(self):
        # Use the output folder (-of) directly as the build folder.
        # So if we call `-of build/debug`, this becomes the actual build dir.
        self.folders.build = "."
        # Put all Conan-generated files (toolchain, deps) in a subdir to keep things tidy.
        self.folders.generators = "generators"

    def generate(self):
        # Generate CMake toolchain + dependency config files.
        tc = CMakeToolchain(self)
        tc.user_presets_path = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        """
        Configure and build the project using CMake.

        This is used when running `conan create` or `conan build`.
        It relies on the Conan-generated toolchain file and the layout() above.
        """
        cm = CMake(self)
        cm.configure()
        cm.build()

    def package(self):
        """
        Install built artifacts and metadata into the package folder.

        - Uses `cmake --install` (requires proper install() rules in CMakeLists.txt)
        - Copies the license file
        - Records the Git commit used to build this package
        """
        cm = CMake(self)
        cm.install()

        # Copy license(s) into the standard location.
        copy(
            self,
            "LICENSE*",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )

        # Record the git commit used for this package for traceability.
        try:
            commit = (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
        except Exception:
            commit = "unknown"

        metadata_dir = os.path.join(self.package_folder, "metadata")
        os.makedirs(metadata_dir, exist_ok=True)
        save(self, os.path.join(metadata_dir, "git_commit.txt"), commit + "\n")

    def package_info(self):
        """
        Expose information about the packaged artifacts to consumers.

        Adjust `libs` if your CMake project generates a different library name,
        or if you ship multiple libraries.
        """
        # Assuming your CMakeLists.txt produces a library called "project_template"
        self.cpp_info.libs = ["project_template"]
