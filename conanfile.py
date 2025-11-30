import os
import subprocess

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps


class Pkg(ConanFile):
    name = "project-template"
    version = None  # This is set automatically by set_version
    settings = "os", "arch", "compiler", "build_type"
    exports_sources = (
        "CMakeLists.txt",
        "CMakePresets.json",
        "src/*",
        "tests/*",
        "cmake/*",
        "conan/*",
    )

    # Conan dependencies (ConanCenter)
    requires = (
        "gtest/1.17.0",
        "benchmark/1.9.4",
        "spdlog/1.13.0",
        "magic_enum/0.9.5",
        "yaml-cpp/0.8.0",
    )

    # Match previous behavior: spdlog as header-only
    default_options = {
        "spdlog/*:header_only": True,
    }

    def set_version(self):
        """
        Versioning rules:
        1. If env var MYLIB_VERSION is set -> use that verbatim.
        2. Otherwise:
           - If HEAD is exactly on a tag -> use that tag as the version.
           - Otherwise -> use 'latest'.
        """
        # 1) Explicit override from environment (optional but handy in CI)
        env_version = os.getenv("MYLIB_VERSION")
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
        tc = CMakeToolchain(self)
        tc.user_presets_path = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()
