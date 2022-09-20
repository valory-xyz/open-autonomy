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

"""Script to run registry contracts deployment locally."""

import click
from aea_test_autonomy.docker.registries import RegistriesDockerImage
from docker import from_env


@click.command()
def main() -> None:
    """Run a local registry deployment."""
    client = from_env()
    image = RegistriesDockerImage(
        client=client,
    )
    container = image.create()

    try:
        for line in client.api.logs(container.id, follow=True, stream=True):
            print(line.decode(), end="")
    except KeyboardInterrupt:
        print("Stopping container.")
    except Exception:  # pyline: disable=broad-except
        print("Stopping container.")
        container.stop()
        raise

    print("Stopping container.")
    container.stop()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
