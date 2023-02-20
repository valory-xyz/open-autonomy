# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Tools for testing docker images"""

import contextlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import docker
from docker.errors import APIError
from docker.models.containers import Container


class BaseImageBuildTest:
    """Test image build and run."""

    client: docker
    path: Path
    tag: str
    agent: str

    running_containers: List[Container]

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""

        cls.client = docker.from_env()

    def setup(self) -> None:
        """Setup test."""
        self.running_containers = []

    def build_image(
        self,
        path: Path,
        tag: str,
        buildargs: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, str]:
        """Build docker image."""

        stream = self.client.api.build(
            path=str(path),
            tag=tag,
            nocache=True,
            buildargs=(buildargs or {}),
        )
        output = ""
        for stream_obj in stream:
            for line in stream_obj.decode().split("\n"):
                line = line.strip()
                if not line:
                    continue
                stream_data = json.loads(line)
                if "stream" in stream_data:
                    output += stream_data["stream"]
                elif "errorDetail" in stream_data:
                    return False, stream_data["errorDetail"]["message"]
                elif "aux" in stream_data:
                    output += stream_data["aux"]["ID"]
                elif "status" in stream_data:
                    output += stream_data["status"]

        return True, output

    def teardown(self) -> None:
        """Teardown test."""

        for container in self.running_containers:
            with contextlib.suppress(APIError):
                container.kill()
                container.wait(timeout=30)
