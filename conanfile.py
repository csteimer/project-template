import os
import subprocess

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, cmake_layout


class Pkg(ConanFile):
    name = "project-template"
    version = None
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
           - Use the latest reachable tag as base version.
           - If HEAD is not exactly on that tag, append '.latest'.
        3. If no tags exist at all -> use '0.0.0.latest'.
        """
        # 1) Explicit override from environment (optional but handy in CI)
        env_version = os.getenv("MYLIB_VERSION")
        if env_version:
            self.version = env_version
            return

        # 2) Try to get the latest reachable tag
        try:
            latest_tag = (
                subprocess.check_output(
                    ["git", "describe", "--tags", "--abbrev=0"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
        except Exception:
            # No tags or not a git repo
            self.version = "0.0.0.latest"
            return

        # 3) Check whether HEAD is exactly at that tag
        try:
            exact_tag = (
                subprocess.check_output(
                    ["git", "describe", "--tags", "--exact-match"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
            on_tag = exact_tag == latest_tag
        except Exception:
            # Not exactly on any tag
            on_tag = False

        if on_tag:
            # Tagged commit -> plain tag as version
            self.version = latest_tag
        else:
            # Non-tag commit -> latest tag + '.latest'
            self.version = f"{latest_tag}.latest"

    def layout(self):
        # Use the output folder (-of) directly as the build folder.
        # So if we call `-of build/debug`, this becomes the actual build dir.
        self.folders.build = "."
        # Put all Conan-generated files (toolchain, deps) in a subdir to keep things tidy.
        self.folders.generators = "generators"

    def generate(self):
        # Toolchain (presets etc.)
        tc = CMakeToolchain(self)
        # Generate a Conan-specific presets file that you can include from your main CMakePresets.json
        tc.user_presets_path = "ConanPresets.json"
        tc.generate()

        # Dependency config files for find_package()
        deps = CMakeDeps(self)
        deps.generate()
