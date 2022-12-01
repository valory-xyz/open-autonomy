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
# pylint: disable=import-error

"""Autonomous Fund Contracts Docker image."""

from aea_test_autonomy.docker.tendermint import FlaskTendermintDockerImage


class SlowFlaskTendermintDockerImage(FlaskTendermintDockerImage):
    """A tendermint server that is slow to respond."""

    @property
    def image(self) -> str:
        """Get the image."""
        return "valory/slow-tendermint-server:0.1.0"
