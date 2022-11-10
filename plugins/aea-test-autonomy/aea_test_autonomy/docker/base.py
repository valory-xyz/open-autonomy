# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This module contains testing utilities."""
import logging
import platform
import re
import shutil
import subprocess  # nosec
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List

import docker
import pytest
from docker.errors import ImageNotFound, NotFound
from docker.models.containers import Container


SEPARATOR = ("\n" + "*" * 40) * 3 + "\n"
logger = logging.getLogger(__name__)


skip_docker_tests = pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Docker daemon is not available in Windows and macOS CI containers.",
)


class DockerImage(ABC):
    """A class to wrap interaction with a Docker image."""

    MINIMUM_DOCKER_VERSION = (19, 0, 0)

    def __init__(self, client: docker.DockerClient):
        """Initialize."""
        self._client = client

    def check_skip(self) -> None:
        """
        Check whether the test should be skipped.

        By default, nothing happens.
        """
        self._check_docker_binary_available()

    def _check_docker_binary_available(self) -> None:
        """Check the 'Docker' CLI tool is in the OS PATH."""
        result = shutil.which("docker")
        if result is None:
            pytest.skip("Docker not in the OS Path; skipping the test")

        result_ = subprocess.run(  # nosec   # pylint: disable=subprocess-run-check
            ["docker", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result_.returncode != 0:
            pytest.skip(
                f"'docker --version' failed with exit code {result_.returncode}"
            )

        match = re.search(
            r"Docker version ([0-9]+)\.([0-9]+)\.([0-9]+)",
            result_.stdout.decode("utf-8"),
        )
        if match is None:
            pytest.skip("cannot read version from the output of 'docker --version'")
            return
        version = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if version < self.MINIMUM_DOCKER_VERSION:
            pytest.skip(
                f"expected Docker version to be at least {'.'.join(*[str(el) for el in self.MINIMUM_DOCKER_VERSION])}, found {'.'.join(*[str(el) for el in version])}"
            )

    @property
    @abstractmethod
    def image(self) -> str:
        """Return the image name."""

    def stop_if_already_running(self) -> None:
        """Stop the running images with the same tag, if any."""
        client = docker.from_env()
        for container in client.containers.list():
            if self.image in container.image.tags:
                logger.info(f"Stopping image {self.image}...")
                container.stop()

    @abstractmethod
    def create(self) -> Container:
        """Instantiate the image in a container."""

    @abstractmethod
    def create_many(self, nb_containers: int) -> List[Container]:
        """Instantiate the image in many containers, parametrized."""

    @abstractmethod
    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """
        Wait until the image is running.

        :param max_attempts: max number of attempts.
        :param sleep_rate: the amount of time to sleep between different requests.
        :return: True if the wait was successful, False otherwise.
        """


def _pre_launch(image: DockerImage) -> None:
    """Run pre-launch checks."""
    image.check_skip()
    image.stop_if_already_running()


def _start_container(
    image: DockerImage, container: Container, timeout: float, max_attempts: int
) -> None:
    """
    Start a container.

    :param image: an instance of Docker image.
    :param container: the container to start, created from the image.
    :param timeout: timeout to launch
    :param max_attempts: max launch attempts
    """
    container.start()
    logger.info(f"Setting up image {image.image}...")
    success = image.wait(max_attempts, timeout)
    if not success:
        container.stop()
        logger.error(
            f"{SEPARATOR}Logs from container {container.name}:\n{container.logs().decode()}"
        )
        container.remove()
        pytest.fail(f"{image.image} doesn't work. Exiting...")
    else:
        logger.info("Done!")
        time.sleep(timeout)


def _stop_container(container: Container, tag: str) -> None:
    """Stop a container."""
    logger.info(f"Stopping container {container.name} from image {tag}...")
    container.stop()
    try:
        logger.info(
            f"{SEPARATOR}Logs from container {container.name}:\n{container.logs().decode()}"
        )
        if str(container.name).startswith("node"):
            logger.info(f"{SEPARATOR}Logs from container log file {container.name}:\n")
            bits, _ = container.get_archive(f"/logs/{container.name}.txt")
            for chunk in bits:
                logger.info(chunk.decode())
    except (ImageNotFound, NotFound) as e:
        logger.error(e)
    finally:
        container.remove()


def launch_image(
    image: DockerImage, timeout: float = 2.0, max_attempts: int = 10
) -> Generator[DockerImage, None, None]:
    """
    Launch a single container.

    :param image: an instance of Docker image.
    :param timeout: timeout to launch
    :param max_attempts: max launch attempts
    :yield: image
    """
    _pre_launch(image)
    container = image.create()
    _start_container(image, container, timeout, max_attempts)
    yield image
    _stop_container(container, image.image)


def launch_many_containers(
    image: DockerImage, nb_containers: int, timeout: float = 2.0, max_attempts: int = 10
) -> Generator[DockerImage, None, None]:
    """
    Launch many containers from an image.

    :param image: an instance of Docker image.
    :param nb_containers: the number of containers to launch from the image.
    :param timeout: timeout to launch
    :param max_attempts: max launch attempts
    :yield: image
    """
    _pre_launch(image)
    containers = image.create_many(nb_containers)
    for container in containers:
        _start_container(image, container, timeout, max_attempts)
    yield image
    for container in containers:
        _stop_container(container, image.image)


class DockerBaseTest(ABC):
    """Base pytest class for setting up Docker images."""

    timeout: float = 3.0
    max_attempts: int = 60
    addr: str
    port: int

    _image: DockerImage
    _container: Container

    @classmethod
    def setup_class(cls) -> None:
        """Setup up the test class."""
        cls._image = cls._build_image()
        cls._image.check_skip()
        cls._image.stop_if_already_running()
        cls._container = cls._image.create()
        cls._container.start()
        logger.info(f"Setting up image {cls._image.image}...")
        success = cls._image.wait(cls.max_attempts, cls.timeout)
        if not success:
            cls._container.stop()
            logger.error(
                f"{SEPARATOR}Logs from container {cls._container.name}:\n{cls._container.logs().decode()}"
            )
            cls._container.remove()
            pytest.fail(f"{cls._image.image} doesn't work. Exiting...")
        else:
            logger.info("Done!")
            time.sleep(cls.timeout)
        cls._setup_class(**cls.setup_class_kwargs())

    @classmethod
    def teardown_class(cls) -> None:
        """Tear down the test."""
        logger.info(f"Stopping the image {cls._image.image}...")
        cls._container.stop()
        logger.info(
            f"{SEPARATOR}Logs from container {cls._container.name}:\n{cls._container.logs().decode()}"
        )
        cls._container.remove()

    @classmethod
    @abstractmethod
    def _build_image(cls) -> DockerImage:
        """Instantiate the Docker image."""

    @classmethod
    @abstractmethod
    def _setup_class(cls, **setup_class_kwargs: Any) -> None:
        """Continue setting up the class."""

    @classmethod
    @abstractmethod
    def setup_class_kwargs(cls) -> Dict[str, Any]:
        """Get kwargs for _setup_class call."""
