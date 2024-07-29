import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class BuildFrontend(BuildHookInterface):
    PLUGIN_NAME = "build_frontend"
    FRONTEND_DIR_PATH = Path(__file__).parents[1] / "viz"

    def initialize(self, version, build_data):
        subprocess.run(
            args=["npm", "run", "build"],
            cwd=self.FRONTEND_DIR_PATH,
            check=True,
        )

        return super().initialize(version, build_data)
