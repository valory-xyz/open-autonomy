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
import signal
import subprocess  # nosec
from pathlib import Path
from typing import IO, cast

import yaml
from aea.configurations.utils import PublicId


class ImageProfiles:  # pylint: disable=too-few-public-methods
    """Image build profiles."""

    CLUSTER = "cluster"
    DEVELOPMENT = "dev"
    PRODUCTION = "prod"
    DEPENDENCIES = "dependencies"
    ALL = (CLUSTER, DEVELOPMENT, PRODUCTION, DEPENDENCIES)


class ImageBuilder:
    """Class to build images using skaffold."""

    @classmethod
    def build_images(  # pylint: disable=too-many-arguments
        cls,
        profile: str,
        deployment_file_path: Path,
        package_dir: Path,
        build_dir: Path,
        skaffold_dir: Path,
        version: str,
        push: bool = False,
    ) -> None:
        """Build images using the subprocess."""

        if profile == ImageProfiles.DEVELOPMENT:
            version = "dev"

        aea_agent = cls.get_aea_agent(deployment_file_path=deployment_file_path)
        cls._copy_packages(package_dir=package_dir, build_dir=build_dir)
        cls._build(aea_agent, profile, skaffold_dir, version, push)

    @classmethod
    def _build(  # pylint: disable=too-many-arguments
        cls,
        aea_agent: str,
        profile: str,
        skaffold_dir: Path,
        version: str,
        push: bool = False,
        build_concurrency: int = 0,
    ) -> None:
        """Command to build images from for skaffold deployment."""

        agent_id = PublicId.from_str(aea_agent)
        env = os.environ.copy()
        env["AEA_AGENT"] = aea_agent
        env["VERSION"] = f"{agent_id.name}-{version}"

        if profile == ImageProfiles.CLUSTER:
            if env.get("KUBECONFIG") is None:
                raise ValueError("Please setup KUBECONFIG variable.")
        else:
            # deleting KUBECONFIG var for none cluster builds will avoid uneccessary warnings
            if env.get("KUBECONFIG") is not None:
                del env["KUBECONFIG"]

        try:
            process = (
                subprocess.Popen(  # nosec # pylint: disable=consider-using-with,W1509
                    [
                        "skaffold",
                        "build",
                        f"--build-concurrency={build_concurrency}",
                        f"--push={str(push).lower()}",
                        "-p",
                        profile,
                    ],
                    preexec_fn=os.setsid,
                    env=env,
                    stdout=subprocess.PIPE,
                    cwd=str(skaffold_dir),
                )
            )

            for line in iter(cast(IO[bytes], process.stdout).readline, ""):
                if line == b"":
                    break
                print(f"[Skaffold] {line.decode().strip()}")

        except KeyboardInterrupt:
            cast(IO[bytes], process.stdout).close()
            process.send_signal(signal.SIGTERM)

        process.wait(timeout=30)
        poll = process.poll()
        if poll is None:
            process.terminate()
            process.wait(2)

        if process.returncode != 0:
            print("Image build failed.")

    @staticmethod
    def _copy_packages(
        package_dir: Path,
        build_dir: Path,
    ) -> None:
        """Copy packages for image building."""
        build_package_dir = Path(build_dir) / "packages"

        if build_package_dir.exists():
            shutil.rmtree(build_package_dir)
        shutil.copytree(  # type: ignore # pylint: disable=E1123
            src=Path(package_dir), dst=Path(build_dir) / "packages", dirs_exist_ok=True
        )

    @staticmethod
    def get_aea_agent(deployment_file_path: Path) -> str:
        """Validate and retrieve aea agent from spec."""

        with open(deployment_file_path, "r", encoding="utf-8") as stream:
            deployment_spec, *_ = yaml.safe_load_all(stream)
            agent = deployment_spec["agent"]

        return agent
