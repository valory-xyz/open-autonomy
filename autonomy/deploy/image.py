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
import signal
import subprocess  # nosec
from pathlib import Path
from typing import IO, cast

from aea.configurations.utils import PublicId


def check_kubeconfig_vars() -> bool:
    """Check if kubeconfig variables are set properly."""

    env_vars = (
        "KUBERNETES_SERVICE_PORT_HTTPS",
        "KUBERNETES_SERVICE_PORT",
        "KUBERNETES_PORT_443_TCP",
        "KUBERNETES_PORT_443_TCP_PROTO",
        "KUBERNETES_PORT_443_TCP_ADDR",
        "KUBERNETES_SERVICE_HOST",
        "KUBERNETES_PORT",
        "KUBERNETES_PORT_443_TCP_PORT",
    )

    return any(map(os.environ.get, env_vars))


class ImageProfiles:  # pylint: disable=too-few-public-methods
    """Image build profiles."""

    CLUSTER = "cluster"
    DEVELOPMENT = "dev"
    PRODUCTION = "prod"
    DEPENDENCIES = "dependencies"
    ALL = (CLUSTER, DEVELOPMENT, PRODUCTION, DEPENDENCIES)


def build_image(  # pylint: disable=too-many-arguments
    agent: PublicId,
    profile: str,
    skaffold_dir: Path,
    version: str,
    push: bool = False,
    build_concurrency: int = 0,
) -> None:
    """Command to build images from for skaffold deployment."""

    env = os.environ.copy()
    env["AEA_AGENT"] = str(agent)

    if profile == ImageProfiles.DEPENDENCIES:
        env["VERSION"] = version
    elif profile == ImageProfiles.DEVELOPMENT:
        env["VERSION"] = f"{agent.name}-dev"
    else:
        env["VERSION"] = f"{agent.name}-{version}"

    kubeconfig = env.get("KUBECONFIG")
    if profile == ImageProfiles.CLUSTER:
        if kubeconfig is None and not check_kubeconfig_vars():
            raise ValueError("Please setup kubernetes environment variables.")
    else:
        if kubeconfig is not None:  # pragma: nocover
            del env["KUBECONFIG"]
    try:
        process = subprocess.Popen(  # nosec # pylint: disable=consider-using-with,W1509
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

        for line in iter(cast(IO[bytes], process.stdout).readline, ""):
            if line == b"":
                break
            print(f"[Skaffold] {line.decode().strip()}")

    except KeyboardInterrupt:  # pragma: nocover
        cast(IO[bytes], process.stdout).close()
        process.send_signal(signal.SIGTERM)

    process.wait(timeout=30)
    poll = process.poll()
    if poll is None:  # pragma: nocover
        process.terminate()
        process.wait(2)

    if process.returncode != 0:  # pragma: nocover
        print("Image build failed.")
