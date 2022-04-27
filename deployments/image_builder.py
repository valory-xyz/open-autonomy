# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Image building."""

import os
import shutil
import subprocess  # nosec
from pathlib import Path
from typing import Optional

import yaml
from aea.configurations.utils import PublicId

from deployments.create_deployment import validate_deployment_spec_path


class ImageBuilder:
    """Class to build images using skaffold."""

    _process: subprocess.Popen

    def _build(
        self,
        aea_agent: str,
        profile: str,
        push: bool = False,
        build_concurrency: int = 0,
    ):
        """Command to build images from for skaffold deployment."""
        env = os.environ.copy()
        agent_id = PublicId.from_str(aea_agent)
        env["AEA_AGENT"] = aea_agent
        env["VERSION"] = f"{agent_id.name}V{env['VERSION']}"
        skaffold_profile = "prod" if profile != "dev" else profile
        cmd = f"skaffold build --build-concurrency={build_concurrency} --push={'true' if push else 'false'} -p {skaffold_profile}"
        self._process = (
            subprocess.Popen(  # nosec # pylint: disable=consider-using-with,W1509
                cmd.split(), preexec_fn=os.setsid, env=env
            )
        )
        if self._process.wait() != 0:
            raise Exception(f"Failed to build images. Check Skaffold cmd {cmd}")

    @staticmethod
    def _copy_packages(
        package_dir: str = "packages",
        build_dir: str = "deployments/Dockerfiles/open_aea",
    ) -> None:
        """Copy packages for image building."""
        shutil.copytree(
            src=Path(package_dir),
            dst=Path(build_dir) / "packages",
            dirs_exist_ok=True,  # type: ignore
        )

    @staticmethod
    def get_aea_agent(
        deployment_file_path: Optional[str], valory_application: Optional[str]
    ) -> str:
        """Validate and retrieve aea agent from spec."""
        deploy_path = Path(
            validate_deployment_spec_path(
                deployment_file_path=deployment_file_path,
                valory_application=valory_application,
            )
        )
        with open(deploy_path, "r", encoding="utf-8") as stream:
            deployment_spec = yaml.safe_load_all(stream)
            agent = list(deployment_spec)[0]["agent"]
        return agent

    def build_images(
        self,
        profile: str,
        deployment_file_path: Optional[str],
        valory_application: Optional[str],
        push: bool = False,
    ):
        """Build images using the subprocess."""
        aea_agent = self.get_aea_agent(
            deployment_file_path=deployment_file_path,
            valory_application=valory_application,
        )
        self._copy_packages()
        self._build(aea_agent, profile, push)
