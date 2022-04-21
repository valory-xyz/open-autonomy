import subprocess
from pathlib import Path
import os
import shutil
from deployments.create_deployment import validate_deployment_spec_path
from typing import Optional
import yaml
from aea.configurations.utils import PublicId

class ImageBuilder(object):
    """Class to build images using skaffold."""

    _process: None

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
            Path(package_dir), Path(build_dir) / "packages", dirs_exist_ok=True
        )

    @staticmethod
    def _get_aea_agent(deployment_file_path: str, valory_application: str) -> None:
        """validate and retrieve aea agent from spec."""
        deploy_path = Path(
            validate_deployment_spec_path(
                deployment_file_path=deployment_file_path,
                valory_application=valory_application,
            )
        )
        with open(deploy_path, "r") as stream:
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
        """"""
        aea_agent = self._get_aea_agent(deployment_file_path, valory_application)
        self._copy_packages()
        self._build(aea_agent, profile, push)
