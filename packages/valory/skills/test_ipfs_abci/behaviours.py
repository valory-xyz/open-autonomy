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

"""This module contains the behaviours for the 'test_ipfs_behaviour' skill."""
import sys
from abc import ABC
from typing import Generator, Set, Type, cast

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.io_.store import SupportedFiletype
from packages.valory.skills.test_ipfs_abci.rounds import IpfsRound, IpfsTestAbciApp


class DummyIpfsBehaviour(BaseBehaviour, ABC):
    """A dummy behaviour that stores and retrieves data from IPFS."""

    matching_round = IpfsRound

    def async_act(self) -> Generator:
        """Do the action."""
        dummy_object = {
            "dummy_k1": "dummy_v1",
            "dummy_k2": "dummy_v2",
            "dummy_k3": "dummy_v3",
        }

        filename = "testfile.json"
        ipfs_hash = yield from self.send_to_ipfs(
            filename,
            {filename: dummy_object},
            filetype=SupportedFiletype.JSON,
            multiple=True,
        )
        ipfs_hash = cast(str, ipfs_hash)
        received_object = yield from self.get_from_ipfs(
            ipfs_hash=ipfs_hash, filetype=SupportedFiletype.JSON
        )
        if received_object == dummy_object:
            self.context.logger.info("Single object uploading & downloading works.")

        multiple_objects = {
            "test1.json": dummy_object,
            "test2.json": dummy_object,
            "test3.json": dummy_object,
        }
        dir_name = "test_dir"
        ipfs_hash = yield from self.send_to_ipfs(
            dir_name,
            multiple_objects,
            filetype=SupportedFiletype.JSON,
            multiple=True,
        )
        ipfs_hash = cast(str, ipfs_hash)
        received_object = yield from self.get_from_ipfs(
            ipfs_hash=ipfs_hash, filetype=SupportedFiletype.JSON
        )
        if received_object == multiple_objects:
            self.context.logger.info("Multiple object uploading & downloading works.")
        else:
            self.context.logger.info(received_object)
            self.context.logger.info(multiple_objects)
        # give some time to
        yield from self.sleep(10)
        sys.exit()


class TestAbciConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the ipfs test abci app."""

    initial_behaviour_cls = DummyIpfsBehaviour
    abci_app_cls = IpfsTestAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        DummyIpfsBehaviour,  # type: ignore
    }
