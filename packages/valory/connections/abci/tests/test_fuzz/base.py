# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
"""Defines the base of the fuzzy tests"""

# pylint: skip-file

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type

import numpy as np
from aea.exceptions import enforce
from aea.test_tools.test_cases import AEATestCaseMany
from hypothesis import given
from hypothesis.strategies import binary, booleans, integers, lists, text, tuples

from packages.valory.connections.abci.tests.test_fuzz.mock_node.channels.base import (
    BaseChannel,
)
from packages.valory.connections.abci.tests.test_fuzz.mock_node.node import MockNode


class BaseFuzzyTests(AEATestCaseMany):
    """
    Base class for the Fuzzy Tests
    """

    package_registry_src_rel = Path(__file__).parents[5]

    UINT_64_MAX_VALUE = np.iinfo(np.uint64).max
    UINT_64_MIN_VALUE = 0
    INT_64_MAX_VALUE = np.iinfo(np.int64).max
    INT_64_MIN_VALUE = np.iinfo(np.int64).min

    UINT_32_MAX_VALUE = np.iinfo(np.uint32).max
    UINT_32_MIN_VALUE = 0
    INT_32_MAX_VALUE = np.iinfo(np.int32).max
    INT_32_MIN_VALUE = np.iinfo(np.int32).min

    CHANNEL_TYPE: Type[BaseChannel] = BaseChannel
    CHANNEL_ARGS: Dict[str, Any] = dict()
    IS_LOCAL = True
    USE_GRPC = False

    channel: BaseChannel
    mock_node: MockNode
    agent_package = "valory/test_abci:0.1.0"
    agent_name = "test_abci"
    agent_process = None
    cli_log_options = ["-v", "INFO"]

    AGENT_TIMEOUT_SECONDS = 10

    @classmethod
    def setup_class(cls) -> None:
        """Sets up the environment for the tests."""

        super().setup_class()
        cls.fetch_agent(cls.agent_package, cls.agent_name, is_local=cls.IS_LOCAL)
        cls.set_agent_context(cls.agent_name)
        cls.generate_private_key("ethereum", "ethereum_private_key.txt")
        cls.add_private_key("ethereum", "ethereum_private_key.txt")
        # issue certificates for libp2p proof of representation
        cls.generate_private_key("cosmos", "cosmos_private_key.txt")
        cls.add_private_key("cosmos", "cosmos_private_key.txt")
        cls.run_cli_command("issue-certificates", cwd=cls._get_cwd())

        # we are mocking a tendermint node
        cls.set_config("vendor.valory.connections.abci.config.use_tendermint", False)

        cls.set_config("vendor.valory.connections.abci.config.use_grpc", cls.USE_GRPC)

        cls.run_install()
        cls.agent_process = cls.run_agent()

        enforce(
            cls.is_running(cls.agent_process, cls.AGENT_TIMEOUT_SECONDS),
            f"The agent was not started in the defined timeout ({cls.AGENT_TIMEOUT_SECONDS}s)",
        )

        enforce(cls.CHANNEL_TYPE is not None, "A channel type must be provided")

        cls.channel = cls.CHANNEL_TYPE(**cls.CHANNEL_ARGS)
        cls.mock_node = MockNode(cls.channel)
        cls.mock_node.connect()
        logging.disable(logging.INFO)

    @classmethod
    def teardown_class(cls) -> None:
        """Tear down the testing environment."""
        logging.disable(logging.NOTSET)
        cls.mock_node.disconnect()
        super().teardown_class()

    # flake8: noqa:D102
    @given(message=text())
    def test_echo(self, message: str) -> None:
        assert self.mock_node.echo(message)

    @given(
        version=text().filter(lambda x: x != ""),
        block_version=integers(0, UINT_64_MAX_VALUE),
        p2p_version=integers(0, UINT_64_MAX_VALUE),
    )
    def test_info(self, version: str, block_version: int, p2p_version: int) -> None:
        assert self.mock_node.info(version, block_version, p2p_version)

    def test_flush(self) -> None:
        assert self.mock_node.flush()

    @given(key=text(), value=text())
    def test_set_option(self, key: str, value: str) -> None:
        assert self.mock_node.set_option(key, value)

    @given(tx=binary())
    def test_deliver_tx(self, tx: bytes) -> None:
        assert self.mock_node.deliver_tx(tx)

    @given(tx=binary(), is_new_check=booleans())
    def test_check_tx(self, tx: bytes, is_new_check: bool) -> None:
        assert self.mock_node.check_tx(tx, is_new_check)

    @given(
        data=binary(),
        path=text(),
        height=integers(-INT_64_MAX_VALUE, INT_64_MAX_VALUE),
        prove=booleans(),
    )
    def test_query(self, data: bytes, path: str, height: int, prove: bool) -> None:
        assert self.mock_node.query(data, path, height, prove)

    def test_commit(self) -> None:
        assert self.mock_node.commit()

    @given(
        time_seconds=integers(0, INT_64_MAX_VALUE),
        time_nanos=integers(0, 10 ** 9),
        chain_id=text(),
        block_max_bytes=integers(1, INT_64_MAX_VALUE),
        block_max_gas=integers(-1, INT_32_MAX_VALUE),
        evidence_max_age_num_blocks=integers(INT_64_MIN_VALUE, INT_64_MAX_VALUE),
        evidence_max_age_seconds=integers(0, INT_64_MAX_VALUE),
        evidence_max_age_nanos=integers(0, 10 ** 9),
        evidence_max_bytes=integers(1, INT_64_MAX_VALUE),
        pub_key_types=lists(booleans()),
        app_version=integers(0, INT_32_MAX_VALUE),
        validator_pub_keys=lists(tuples(binary(), booleans())),
        validator_power=lists(integers(0, INT_32_MAX_VALUE)),
        app_state_bytes=binary(),
        initial_height=integers(0, INT_32_MAX_VALUE),
    )
    def test_init_chain(
        self,
        time_seconds: int,
        time_nanos: int,
        chain_id: str,
        block_max_bytes: int,
        block_max_gas: int,
        evidence_max_age_num_blocks: int,
        evidence_max_age_seconds: int,
        evidence_max_age_nanos: int,
        evidence_max_bytes: int,
        pub_key_types: List[str],
        app_version: int,
        validator_pub_keys: List[Tuple[bytes, bool]],
        validator_power: List[int],
        app_state_bytes: bytes,
        initial_height: int,
    ) -> None:
        min_validator_length = min(
            validator_power.__len__(),
            validator_pub_keys.__len__(),
            pub_key_types.__len__(),
        )

        assert self.mock_node.init_chain(
            time_seconds,
            time_nanos,
            chain_id,
            block_max_bytes,
            block_max_gas,
            evidence_max_age_num_blocks,
            evidence_max_age_seconds,
            evidence_max_age_nanos,
            evidence_max_bytes,
            ["ed25519" if pk else "secp256k1" for pk in pub_key_types][
                :min_validator_length
            ],
            app_version,
            [
                (pk, "ed25519") if tp else (pk, "secp256k1")
                for pk, tp in validator_pub_keys
            ][:min_validator_length],
            validator_power[:min_validator_length],
            app_state_bytes,
            initial_height,
        )

    @given(
        hash_=binary(),
        consen_ver_block=integers(0, UINT_64_MAX_VALUE),
        consen_ver_app=integers(0, UINT_64_MAX_VALUE),
        chain_id=text(),
        height=integers(-INT_64_MAX_VALUE, INT_64_MAX_VALUE),
        time_seconds=integers(1, INT_64_MAX_VALUE),
        time_nanos=integers(0, 10 ** 9),
        last_block_id_hash=binary(),
        last_commit_hash=binary(),
        data_hash=binary(),
        validators_hash=binary(),
        next_validators_hash=binary(),
        next_validators_part_header_total=integers(0, UINT_32_MAX_VALUE),
        next_validators_part_header_hash=binary(),
        header_consensus_hash=binary(),
        header_app_hash=binary(),
        header_last_results_hash=binary(),
        header_evidence_hash=binary(),
        header_proposer_address=binary(),
        last_commit_round=integers(INT_32_MIN_VALUE, INT_32_MAX_VALUE),
        last_commit_info_votes=lists(
            tuples(binary(), integers(INT_64_MIN_VALUE, INT_64_MAX_VALUE))
        ),
        last_commit_info_signed_last_block=lists(booleans()),
        evidence_type=lists(integers()),
        evidence_validator_address=lists(binary()),
        evidence_validator_power=lists(integers(INT_64_MIN_VALUE, INT_64_MAX_VALUE)),
        evidence_height=lists(integers(INT_64_MIN_VALUE, INT_64_MAX_VALUE)),
        evidence_time_seconds=lists(integers(1, INT_64_MAX_VALUE)),
        evidence_time_nanos=lists(integers(0, 10 ** 9)),
        evidence_total_voting_power=lists(integers(0, INT_64_MAX_VALUE)),
    )
    def test_begin_block(
        self,
        hash_: bytes,
        consen_ver_block: int,
        consen_ver_app: int,
        chain_id: str,
        height: int,
        time_seconds: int,
        time_nanos: int,
        last_block_id_hash: bytes,
        last_commit_hash: bytes,
        data_hash: bytes,
        validators_hash: bytes,
        next_validators_hash: bytes,
        next_validators_part_header_total: int,
        next_validators_part_header_hash: bytes,
        header_consensus_hash: bytes,
        header_app_hash: bytes,
        header_last_results_hash: bytes,
        header_evidence_hash: bytes,
        header_proposer_address: bytes,
        last_commit_round: int,
        last_commit_info_votes: List[Tuple[bytes, int]],
        last_commit_info_signed_last_block: List[bool],
        evidence_type: List[int],
        evidence_validator_address: List[bytes],
        evidence_validator_power: List[int],
        evidence_height: List[int],
        evidence_time_seconds: List[int],
        evidence_time_nanos: List[int],
        evidence_total_voting_power: List[int],
    ) -> None:
        last_commit_len = min(
            last_commit_info_votes.__len__(),
            last_commit_info_signed_last_block.__len__(),
        )
        evidence_len = min(
            evidence_type.__len__(),
            evidence_validator_address.__len__(),
            evidence_validator_power.__len__(),
            evidence_height.__len__(),
            evidence_time_seconds.__len__(),
            evidence_time_nanos.__len__(),
            evidence_total_voting_power.__len__(),
        )
        self.mock_node.begin_block(
            hash_,
            consen_ver_block,
            consen_ver_app,
            chain_id,
            height,
            time_seconds,
            time_nanos,
            last_block_id_hash,
            last_commit_hash,
            data_hash,
            validators_hash,
            next_validators_hash,
            next_validators_part_header_total,
            next_validators_part_header_hash,
            header_consensus_hash,
            header_app_hash,
            header_last_results_hash,
            header_evidence_hash,
            header_proposer_address,
            last_commit_round,
            last_commit_info_votes[:last_commit_len],
            last_commit_info_signed_last_block[:last_commit_len],
            evidence_type[:evidence_len],
            evidence_validator_address[:evidence_len],
            evidence_validator_power[:evidence_len],
            evidence_height[:evidence_len],
            evidence_time_seconds[:evidence_len],
            evidence_time_nanos[:evidence_len],
            evidence_total_voting_power[:evidence_len],
        )

    @given(height=integers(INT_64_MIN_VALUE, INT_64_MAX_VALUE))
    def test_end_block(self, height: int) -> None:
        assert self.mock_node.end_block(height)

    def test_list_snapshots(self) -> None:
        assert self.mock_node.list_snapshots()

    @given(
        height=integers(UINT_64_MIN_VALUE, UINT_64_MAX_VALUE),
        format_=integers(UINT_32_MIN_VALUE, UINT_32_MAX_VALUE),
        chunks=integers(UINT_32_MIN_VALUE, UINT_32_MAX_VALUE),
        hash_=binary(),
        metadata=binary(),
        app_hash=binary(),
    )
    def test_offer_snapshot(
        self,
        height: int,
        format_: int,
        chunks: int,
        hash_: bytes,
        metadata: bytes,
        app_hash: bytes,
    ) -> None:
        assert self.mock_node.offer_snapshot(
            height, format_, chunks, hash_, metadata, app_hash
        )

    @given(
        height=integers(UINT_64_MIN_VALUE, UINT_64_MAX_VALUE),
        format_=integers(UINT_32_MIN_VALUE, UINT_32_MAX_VALUE),
        chunk=integers(UINT_32_MIN_VALUE, UINT_32_MAX_VALUE),
    )
    def test_load_snapshot_chunk(self, height: int, format_: int, chunk: int) -> None:
        assert self.mock_node.load_snapshot_chunk(height, format_, chunk)

    @given(
        index=integers(UINT_32_MIN_VALUE, UINT_32_MAX_VALUE),
        chunk=binary(),
        sender=text(),
    )
    def test_apply_snapshot_chunk(self, index: int, chunk: bytes, sender: str) -> None:
        assert self.mock_node.apply_snapshot_chunk(index, chunk, sender)
