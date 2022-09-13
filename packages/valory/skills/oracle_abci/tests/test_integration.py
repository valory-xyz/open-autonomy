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

"""Integration tests for various transaction settlement skill's failure modes."""
from collections import deque
from math import ceil
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Optional, cast
from unittest import mock

import pytest
from aea_ledger_ethereum import EthereumApi
from aea_test_autonomy.docker.base import skip_docker_tests
from web3.types import RPCEndpoint, Wei

from packages.open_aea.protocols.signing import SigningMessage
from packages.open_aea.protocols.signing.custom_types import (
    RawTransaction,
    SignedMessage,
    SignedTransaction,
)
from packages.valory.connections.ledger.tests.conftest import make_ledger_api_connection
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.protocols.ledger_api.custom_types import (
    State,
    TransactionDigest,
    TransactionReceipt,
)
from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.abstract_round_abci.test_tools.integration import (
    ExpectedContentType,
    ExpectedTypesType,
    HandlersType,
    IntegrationBaseCase,
)
from packages.valory.skills.oracle_abci.behaviours import (
    OracleAbciAppConsensusBehaviour,
)
from packages.valory.skills.oracle_deployment_abci.behaviours import (
    DeployOracleBehaviour,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    ETHER_VALUE,
    SAFE_TX_GAS,
    TransactionHashBehaviour,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    SynchronizedData as PriceEstimationSynchronizedSata,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    CheckLateTxHashesBehaviour,
    FinalizeBehaviour,
    SelectKeeperTransactionSubmissionBehaviourA,
    SelectKeeperTransactionSubmissionBehaviourB,
    SynchronizeLateMessagesBehaviour,
    TransactionSettlementBaseBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
    hash_payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TxSettlementSynchronizedSata,
)
from packages.valory.skills.transaction_settlement_abci.test_tools.integration import (
    GnosisIntegrationBaseCase,
)


PACKAGE_DIR = Path(__file__).parent.parent

DUMMY_MAX_PRIORITY_FEE_PER_GAS = 3000000000
DUMMY_MAX_FEE_PER_GAS = 4000000000
DUMMY_REPRICING_MULTIPLIER = 1.1


class OracleBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing the oracle."""

    path_to_skill = PACKAGE_DIR
    behaviour: OracleAbciAppConsensusBehaviour


class TransactionSettlementIntegrationBaseCase(
    OracleBehaviourBaseCase, GnosisIntegrationBaseCase
):
    """Base case for integration testing TransactionSettlement FSM Behaviour."""

    price_estimation_synchronized_data: PriceEstimationSynchronizedSata
    make_ledger_api_connection_callable = make_ledger_api_connection

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        keeper_initial_retries = 1
        cls.tx_settlement_synchronized_data = TxSettlementSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        safe_contract_address=cls.safe_contract_address,
                        participants=frozenset(list(cls.safe_owners.keys())),
                        keepers=keeper_initial_retries.to_bytes(32, "big").hex()
                        + cls.keeper_address,
                    )
                ),
            )
        )

        cls.price_estimation_synchronized_data = PriceEstimationSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        safe_contract_address=cls.safe_contract_address,
                        participants=frozenset(list(cls.safe_owners.keys())),
                        most_voted_keeper_address=cls.keeper_address,
                        most_voted_estimate=1,
                    )
                ),
            )
        )

    def deploy_oracle(self, mining_interval_secs: float = 0) -> None:
        """Deploy the oracle."""
        cycles_enter = 4
        handlers_enter: HandlersType = [
            self.contract_handler,
            self.signing_handler,
            self.ledger_handler,
            self.ledger_handler,
        ]
        expected_content_enter: ExpectedContentType = [
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION,
            },
            {
                "performative": SigningMessage.Performative.SIGNED_TRANSACTION,
            },
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_DIGEST,
            },
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            },
        ]
        expected_types_enter: ExpectedTypesType = [
            {
                "raw_transaction": RawTransaction,
            },
            {
                "signed_transaction": SignedTransaction,
            },
            {
                "transaction_digest": TransactionDigest,
            },
            {
                "transaction_receipt": TransactionReceipt,
            },
        ]
        _, _, _, msg4 = self.process_n_messages(
            cycles_enter,
            self.price_estimation_synchronized_data,
            DeployOracleBehaviour.behaviour_id,
            handlers_enter,
            expected_content_enter,
            expected_types_enter,
            mining_interval_secs=mining_interval_secs,
        )
        assert msg4 is not None and isinstance(msg4, LedgerApiMessage)
        oracle_contract_address = EthereumApi.get_contract_address(
            msg4.transaction_receipt.receipt
        )

        # update synchronized data with oracle contract address
        self.price_estimation_synchronized_data.update(
            oracle_contract_address=oracle_contract_address,
        )

    def gen_safe_tx_hash(self) -> None:
        """Generate safe's transaction hash."""
        cycles_enter = 3
        handlers_enter: HandlersType = [self.contract_handler] * cycles_enter
        expected_content_enter: ExpectedContentType = [
            {"performative": ContractApiMessage.Performative.RAW_TRANSACTION}
        ] * cycles_enter
        expected_types_enter: ExpectedTypesType = [
            {
                "raw_transaction": RawTransaction,
            }
        ] * cycles_enter
        _, msg_a, msg_b = self.process_n_messages(
            cycles_enter,
            self.price_estimation_synchronized_data,
            TransactionHashBehaviour.behaviour_id,
            handlers_enter,
            expected_content_enter,
            expected_types_enter,
        )

        assert msg_a is not None and isinstance(msg_a, ContractApiMessage)
        tx_data = cast(bytes, msg_a.raw_transaction.body["data"])
        assert msg_b is not None and isinstance(msg_b, ContractApiMessage)
        tx_hash = cast(str, msg_b.raw_transaction.body["tx_hash"])[2:]

        payload = hash_payload_to_hex(
            tx_hash,
            ETHER_VALUE,
            SAFE_TX_GAS,
            self.price_estimation_synchronized_data.oracle_contract_address,
            tx_data,
        )

        # update synchronized data with safe's tx hash
        self.tx_settlement_synchronized_data.update(
            most_voted_tx_hash=payload,
        )

    def clear_unmined_txs(self) -> None:
        """Clear all unmined txs. Mined txs will not be cleared, but this is not a problem."""
        for tx in self.tx_settlement_synchronized_data.tx_hashes_history:
            self.hardhat_provider.make_request(
                RPCEndpoint("hardhat_dropTransaction"), (tx,)
            )

    @staticmethod
    def dummy_try_get_gas_pricing_wrapper(
        max_priority_fee_per_gas: Wei = DUMMY_MAX_PRIORITY_FEE_PER_GAS,
        max_fee_per_gas: Wei = DUMMY_MAX_FEE_PER_GAS,
        repricing_multiplier: float = DUMMY_REPRICING_MULTIPLIER,
    ) -> Callable[
        [Optional[str], Optional[Dict], Optional[Dict[str, Wei]]], Dict[str, Wei]
    ]:
        """A dummy wrapper of `EthereumAPI`'s `try_get_gas_pricing`."""

        def dummy_try_get_gas_pricing(
            _gas_price_strategy: Optional[str] = None,
            _extra_config: Optional[Dict] = None,
            old_price: Optional[Dict[str, Wei]] = None,
            raise_on_try: bool = False,
        ) -> Dict[str, Wei]:
            """Get a dummy gas price."""
            tip = max_priority_fee_per_gas
            gas = max_fee_per_gas

            if old_price is not None:
                tip = ceil(max_priority_fee_per_gas * repricing_multiplier)
                gas = ceil(max_fee_per_gas * repricing_multiplier)
            return {"maxPriorityFeePerGas": tip, "maxFeePerGas": gas}

        return dummy_try_get_gas_pricing


@skip_docker_tests
class TestRepricing(TransactionSettlementIntegrationBaseCase):
    """Test failure modes related to repricing."""

    @pytest.mark.parametrize("should_mock_ledger_pricing_mechanism", (True, False))
    def test_same_keeper(
        self,
        should_mock_ledger_pricing_mechanism: bool,
    ) -> None:
        """Test repricing with and without mocking ledger's `try_get_gas_pricing` method."""

        try:
            if should_mock_ledger_pricing_mechanism:
                with mock.patch.object(
                    EthereumApi,
                    "try_get_gas_pricing",
                    new_callable=TransactionSettlementIntegrationBaseCase.dummy_try_get_gas_pricing_wrapper,
                ):
                    self._test_same_keeper()
            else:
                self._test_same_keeper()

        finally:
            self.clear_unmined_txs()

    def _test_same_keeper(self) -> None:
        """
        Test repricing after the first failure.

        Test that we are using the same keeper to reprice when we fail or timeout for the first time.
        Also, test that we are adjusting the gas correctly when repricing.
        """
        mining_interval_secs = 1.5
        mining_interval_msecs = mining_interval_secs * 1000

        # deploy the oracle
        self.deploy_oracle(mining_interval_secs)
        # generate tx hash
        self.gen_safe_tx_hash()
        # sign tx
        self.sign_tx()
        # stop HardHat's automatic mining
        assert self.hardhat_provider.make_request(
            RPCEndpoint("evm_setAutomine"), [False]
        ), "Disabling auto-mining failed!"
        # send tx first time, we expect it to be pending until we enable the mining back
        self.send_tx()
        # re-enable HardHat's automatic mining so that the second tx replaces the first, pending one
        assert self.hardhat_provider.make_request(
            RPCEndpoint("evm_setIntervalMining"), [mining_interval_msecs]
        ), "Re-enabling auto-mining failed!"
        """
        NOTE:
        The second gas estimation will ALWAYS fail. That is, because the
        current implementation of the plugin does not play well with Hardhat:
        https://github.com/valory-xyz/open-aea/blob/main/plugins/aea-ledger-ethereum/aea_ledger_ethereum/ethereum.py#L1113-L1118
        https://github.com/NomicFoundation/hardhat/blob/d1733f9ecfe8125111a707ff0e3dea287e584caa/packages/hardhat-core/src/internal/hardhat-network/provider/modules/eth.ts#L419-L424
        eth_estimateGas
          Contract call:       GnosisSafeProxy#<unrecognized-selector>
          From:                0xbcd4042de499d14e55001ccbb24a551f3b954096
          To:                  0x68fcdf52066cce5612827e872c45767e5a1f6551
          Value:               0 ETH

          Error: VM Exception while processing transaction: reverted with reason string 'GS026'
              at GnosisSafeL2.checkNSignatures (third_party/safe-contracts/contracts/GnosisSafe.sol:301)
              at GnosisSafeL2.checkSignatures (third_party/safe-contracts/contracts/GnosisSafe.sol:230)
              at GnosisSafeL2.execTransaction (third_party/safe-contracts/contracts/GnosisSafe.sol:145)
              at GnosisSafeL2.execTransaction (third_party/safe-contracts/contracts/GnosisSafeL2.sol:69)
              at GnosisSafeProxy.<fallback> (third_party/safe-contracts/contracts/proxies/GnosisSafeProxy.sol:36)
              at EthModule._estimateGasAction (/build/node_modules/hardhat/src/internal/hardhat-network/provider/modules/eth.ts:425:7)
              at HardhatNetworkProvider._sendWithLogging (/build/node_modules/hardhat/src/internal/hardhat-network/provider/provider.ts:131:22)
              at HardhatNetworkProvider.request (/build/node_modules/hardhat/src/internal/hardhat-network/provider/provider.ts:108:18)
              at JsonRpcHandler._handleRequest (/build/node_modules/hardhat/src/internal/hardhat-network/jsonrpc/handler.ts:188:20)
              at JsonRpcHandler._handleSingleRequest (/build/node_modules/hardhat/src/internal/hardhat-network/jsonrpc/handler.ts:167:17)
              at Server.JsonRpcHandler.handleHttp (/build/node_modules/hardhat/src/internal/hardhat-network/jsonrpc/handler.ts:52:21)

        """
        # send tx second time
        self.send_tx()
        # validate the tx
        self.validate_tx(mining_interval_secs=mining_interval_secs)


class TestKeepers(OracleBehaviourBaseCase, IntegrationBaseCase):
    """Test the keepers related functionality for the tx settlement skill."""

    make_ledger_api_connection_callable = make_ledger_api_connection

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Set up the test class."""
        super().setup()

        # init synchronized data
        cls.tx_settlement_synchronized_data = TxSettlementSynchronizedSata(
            AbciAppDB(
                setup_data=dict(
                    participants=[frozenset(list(cls.agents.keys()))],
                    most_voted_randomness=["0xabcd"],
                ),
            )
        )

    @mock.patch.object(
        TransactionSettlementBaseBehaviour,
        "serialized_keepers",
        side_effect=lambda keepers, retries: retries.to_bytes(32, "big").hex()
        + "".join(keepers),
    )
    def select_keeper(
        self,
        serialized_keepers_mock: mock.Mock,
        expected_keepers: Deque[str],
        expected_retries: int,
        first_time: bool = False,
    ) -> None:
        """Select a keeper."""

        if first_time:
            behaviour_id = SelectKeeperTransactionSubmissionBehaviourA.behaviour_id
        else:
            behaviour_id = SelectKeeperTransactionSubmissionBehaviourB.behaviour_id

        # select keeper
        self.fast_forward_to_behaviour(
            self.behaviour,
            behaviour_id,
            self.tx_settlement_synchronized_data,
        )
        assert self.behaviour.current_behaviour is not None
        assert self.behaviour.current_behaviour.behaviour_id == behaviour_id

        self.behaviour.act_wrapper()
        serialized_keepers_mock.assert_called_with(expected_keepers, expected_retries)

        # update keepers.
        self.tx_settlement_synchronized_data.update(
            # we cast to A class, because it is the top level one between A & B, and we need `serialized_keepers`
            keepers=cast(
                SelectKeeperTransactionSubmissionBehaviourA,
                self.behaviour.current_behaviour,
            ).serialized_keepers(expected_keepers, expected_retries)
        )

    def test_keepers_alternating(self) -> None:
        """Test that we are alternating the keepers when we fail or timeout more than `keeper_allowed_retries` times."""
        # set verification status
        self.tx_settlement_synchronized_data.update(
            final_verification_status=VerificationStatus.PENDING,
        )

        # select keeper a
        self.select_keeper(
            expected_keepers=deque(("0xBcd4042DE499D14e55001CcbB24a551F3b954096",)),
            expected_retries=1,
            first_time=True,
        )
        assert isinstance(
            self.behaviour.current_behaviour,
            SelectKeeperTransactionSubmissionBehaviourA,
        )

        for i in range(
            self.behaviour.current_behaviour.params.keeper_allowed_retries - 1
        ):
            # select keeper b
            # ensure that we select the same keeper until the `keeper_allowed_retries` is reached.
            # +2 because we selected once for keeperA and also index starts from 0.
            self.select_keeper(
                expected_keepers=deque(("0xBcd4042DE499D14e55001CcbB24a551F3b954096",)),
                expected_retries=i + 2,
            )

        # select keeper b after retries are reached.
        self.select_keeper(
            expected_keepers=deque(
                (
                    "0x71bE63f3384f5fb98995898A86B02Fb2426c5788",
                    "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
                )
            ),
            expected_retries=1,
        )

    def test_rotation(self) -> None:
        """Test keepers rotating when threshold reached."""
        # set more keepers than the threshold
        keepers = deque(
            (
                "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
                "0x71bE63f3384f5fb98995898A86B02Fb2426c5788",
            )
        )
        keeper_retries = 1

        self.tx_settlement_synchronized_data.update(
            keepers=int(keeper_retries).to_bytes(32, "big").hex() + "".join(keepers),
        )

        expected_keepers = keepers.copy()
        # test twice as many times as the number of participants
        for _ in range(len(self.tx_settlement_synchronized_data.participants) * 2):
            # rotate expected keepers
            expected_keepers.rotate(-1)
            # select keeper b
            self.select_keeper(expected_keepers=expected_keepers, expected_retries=1)


@skip_docker_tests
class TestSyncing(TransactionSettlementIntegrationBaseCase):
    """Test late tx hashes synchronization."""

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Set up the test class."""
        super().setup()

        # update synchronized data
        cls.tx_settlement_synchronized_data.update(missed_messages=0)

    def sync_late_messages(self) -> None:
        """Synchronize late messages."""
        params = cast(
            TransactionSettlementBaseBehaviour, self.behaviour.current_behaviour
        ).params
        late_messages_len = len(params.late_messages)
        expected_sync_result = params.tx_hash

        handlers: HandlersType = [
            self.signing_handler,
            self.ledger_handler,
        ] * late_messages_len
        expected_content: ExpectedContentType = [
            {"performative": SigningMessage.Performative.SIGNED_MESSAGE},
            {"performative": LedgerApiMessage.Performative.TRANSACTION_DIGEST},
        ] * late_messages_len
        expected_types: ExpectedTypesType = [
            {
                "signed_message": SignedMessage,
            },
            {
                "transaction_digest": TransactionDigest,
            },
        ] * late_messages_len
        msgs = self.process_n_messages(
            len(handlers),
            self.tx_settlement_synchronized_data,
            SynchronizeLateMessagesBehaviour.behaviour_id,
            handlers,
            expected_content,
            expected_types,
        )

        assert isinstance(
            self.behaviour.current_behaviour, SynchronizeLateMessagesBehaviour
        )
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == SynchronizeLateMessagesBehaviour.behaviour_id
        )
        assert self.behaviour.current_behaviour.params.tx_hash == ""
        assert self.behaviour.current_behaviour.params.late_messages == []

        tx_digest_msgs = msgs[0::2]
        for i in range(len(tx_digest_msgs)):
            current_message = tx_digest_msgs[i]
            assert current_message is not None and isinstance(
                current_message, LedgerApiMessage
            )
            tx_digest = current_message.transaction_digest.body
            assert isinstance(tx_digest, str)
            assert (
                tx_digest
            ), f"No tx digest retrieved for message {i}: {current_message}!"
            expected_sync_result += tx_digest

        assert self.behaviour.current_behaviour._tx_hashes == expected_sync_result
        self.tx_settlement_synchronized_data.update(
            late_arriving_tx_hashes=[expected_sync_result],
        )
        self.tx_settlement_synchronized_data.update(
            missed_messages=self.behaviour.current_behaviour.synchronized_data.missed_messages
            - len(
                self.behaviour.current_behaviour.synchronized_data.late_arriving_tx_hashes
            ),
        )

    def check_late_tx_hashes(self) -> None:
        """Check the late transaction hashes to see if any is validated."""
        handlers: HandlersType = [
            self.contract_handler,
        ] * len(self.tx_settlement_synchronized_data.late_arriving_tx_hashes)
        expected_content: ExpectedContentType = [
            {"performative": ContractApiMessage.Performative.STATE},
        ] * len(self.tx_settlement_synchronized_data.late_arriving_tx_hashes)
        expected_types: ExpectedTypesType = [
            {
                "state": State,
            },
        ] * len(self.tx_settlement_synchronized_data.late_arriving_tx_hashes)
        msgs = self.process_n_messages(
            len(self.tx_settlement_synchronized_data.late_arriving_tx_hashes),
            self.tx_settlement_synchronized_data,
            CheckLateTxHashesBehaviour.behaviour_id,
            handlers,
            expected_content,
            expected_types,
        )
        assert isinstance(self.behaviour.current_behaviour, CheckLateTxHashesBehaviour)
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == CheckLateTxHashesBehaviour.behaviour_id
        )

        verified_idx = -1
        verified_count = 0
        for i in range(len(msgs)):
            current_message = msgs[i]
            assert current_message is not None and isinstance(
                current_message, ContractApiMessage
            )
            if current_message.state.body["verified"]:
                verified_idx = i
                verified_count += 1
        assert verified_idx != -1, f"No message has been verified: {msgs}"
        assert verified_count == 1, "More than 1 messages have been verified!"

        self.tx_settlement_synchronized_data.update(
            final_verification_status=VerificationStatus.VERIFIED,
            final_tx_hash=self.tx_settlement_synchronized_data.late_arriving_tx_hashes[
                -verified_idx
            ],
        )

    @mock.patch.object(
        EthereumApi,
        "try_get_gas_pricing",
        side_effect=TransactionSettlementIntegrationBaseCase.dummy_try_get_gas_pricing_wrapper(),
    )
    def test_sync_local_hash(self, _: mock.Mock) -> None:
        """Test the case in which we have received a tx hash during finalization, but timed out before sharing it."""
        # deploy the oracle
        self.deploy_oracle()
        # generate tx hash
        self.gen_safe_tx_hash()
        # sign tx
        self.sign_tx()
        # send tx, but do not update the state in order to simulate a round's time out.
        self.send_tx(simulate_timeout=True)
        # check that we have increased the number of missed messages.
        assert self.tx_settlement_synchronized_data.missed_messages == 1
        # store the tx hash that we have missed.
        assert isinstance(self.behaviour.current_behaviour, FinalizeBehaviour)
        missed_hash = self.behaviour.current_behaviour.params.tx_hash
        # sync the tx hash that we missed before
        self.sync_late_messages()
        # check that we have decreased the number of missed messages.
        assert self.tx_settlement_synchronized_data.missed_messages == 0
        # check the tx hash that we missed before to see if it is verified
        self.check_late_tx_hashes()
        assert (
            self.tx_settlement_synchronized_data.final_verification_status
            == VerificationStatus.VERIFIED
        )
        assert self.tx_settlement_synchronized_data.final_tx_hash == missed_hash
