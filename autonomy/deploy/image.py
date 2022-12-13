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


import json
from typing import Dict, Optional

from aea.cli.utils.config import get_default_author_from_cli_config
from aea.configurations.utils import PublicId
from docker import from_env

from autonomy.constants import AUTONOMY_IMAGE_NAME, AUTONOMY_IMAGE_VERSION, OAR_IMAGE
from autonomy.data import DATA_DIR
from autonomy.deploy.constants import DOCKERFILES


class ImageProfiles:  # pylint: disable=too-few-public-methods
    """Image build profiles."""

    CLUSTER = "cluster"
    DEVELOPMENT = "dev"
    PRODUCTION = "prod"
    ALL = (CLUSTER, DEVELOPMENT, PRODUCTION)


def build_image(
    agent: PublicId,
    pull: bool = False,
    dev: bool = False,
    version: Optional[str] = None,
) -> None:
    """Command to build images from for skaffold deployment."""

    tag: str
    path: str
    buildargs: Dict[str, str]

    docker_client = from_env()

    if dev:
        tag = OAR_IMAGE.format(agent=agent.name, version="dev")
        path = str(DATA_DIR / DOCKERFILES / "dev")
        buildargs = {
            "AUTONOMY_IMAGE_NAME": AUTONOMY_IMAGE_NAME,
            "AUTONOMY_IMAGE_VERSION": AUTONOMY_IMAGE_VERSION,
            "AEA_AGENT": str(agent),
            "AUTHOR": get_default_author_from_cli_config(),
        }

    else:
        image_version = version or agent.hash
        tag = OAR_IMAGE.format(agent=agent.name, version=image_version)
        path = str(DATA_DIR / DOCKERFILES / "agent")
        buildargs = {
            "AUTONOMY_IMAGE_NAME": AUTONOMY_IMAGE_NAME,
            "AUTONOMY_IMAGE_VERSION": AUTONOMY_IMAGE_VERSION,
            "AEA_AGENT": str(agent),
            "AUTHOR": get_default_author_from_cli_config(),
        }

    stream = docker_client.api.build(
        path=path,
        tag=tag,
        buildargs=buildargs,
        pull=pull,
    )

    for stream_obj in stream:
        for line in stream_obj.decode().split("\n"):
            line = line.strip()
            if not line:
                continue
            stream_data = json.loads(line)
            if "stream" in stream_data:
                print("[docker]" + stream_data["stream"], end="")
            elif "errorDetail" in stream_data:
                raise ImageBuildFailed(
                    "Image build failed with error "
                    + stream_data["errorDetail"]["message"]
                )
            elif "aux" in stream_data:
                print("[docker]" + stream_data["aux"]["ID"], end="")
            elif "status" in stream_data:  # pragma: no cover
                print("[docker]" + stream_data["status"], end="")


class ImageBuildFailed(Exception):
    """Raise when there's an error while building the agent image."""
