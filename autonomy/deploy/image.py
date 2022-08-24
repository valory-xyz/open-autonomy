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


def build_image(agent: PublicId) -> None:
    """Command to build images from for skaffold deployment."""

    docker_client = from_env()

    tag = OAR_IMAGE.format(agent=agent.name, version=agent.version)
    path = str(DATA_DIR / DOCKERFILES / "agent")

    stream = docker_client.api.build(
        path=path,
        tag=tag,
        buildargs={
            "AUTONOMY_IMAGE_NAME": AUTONOMY_IMAGE_NAME,
            "AUTONOMY_IMAGE_VERSION": AUTONOMY_IMAGE_VERSION,
            "AEA_AGENT": str(agent),
        },
    )

    for stream_obj in stream:
        stream_data = json.loads(stream_obj.decode())
        if "stream" in stream_data:
            print("[docker]" + stream_data["stream"], end="")
