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
from math import ceil
from pathlib import Path
from typing import Any, Callable, Dict, Optional, cast
from unittest import mock

import pytest
from aea_ledger_ethereum import EthereumApi
from web3.types import RPCEndpoint, Wei

from packages.open_aea.protocols.signing import SigningMessage
from packages.open_aea.protocols.signing.custom_types import (
    RawTransaction,
    SignedTransaction,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.protocols.ledger_api.custom_types import (
    TransactionDigest,
    TransactionReceipt,
)
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.oracle_abci.behaviours import (
    OracleAbciAppConsensusBehaviour,
)
from packages.valory.skills.oracle_deployment_abci.behaviours import (
    DeployOracleBehaviour,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    TransactionHashBehaviour,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    PeriodState as PriceEstimationPeriodState,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    SelectKeeperTransactionSubmissionBehaviourA,
    SelectKeeperTransactionSubmissionBehaviourB,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
    hash_payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    PeriodState as TxSettlementPeriodState,
)

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase
from tests.test_skills.integration import (
    ExpectedContentType,
    ExpectedTypesType,
    GnosisIntegrationBaseCase,
    HandlersType,
    IntegrationBaseCase,
)


SAFE_TX_GAS = 120000
ETHER_VALUE = 0
DUMMY_MAX_PRIORITY_FEE_PER_GAS = 3000000000
DUMMY_MAX_FEE_PER_GAS = 4000000000
DUMMY_REPRICING_MULTIPLIER = 1.1


class OracleBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing the oracle."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "oracle_abci")
    behaviour: OracleAbciAppConsensusBehaviour


class TransactionSettlementIntegrationBaseCase(
    OracleBehaviourBaseCase, GnosisIntegrationBaseCase
):
    """Base case for integration testing TransactionSettlement FSM Behaviour."""

    price_estimation_period_state: PriceEstimationPeriodState

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        keeper_initial_retries = 1
        cls.tx_settlement_period_state = TxSettlementPeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    safe_contract_address=cls.safe_contract_address,
                    participants=frozenset(list(cls.safe_owners.keys())),
                    keepers=keeper_initial_retries.to_bytes(32, "big").hex()
                    + cls.keeper_address,
                ),
            )
        )

        cls.price_estimation_period_state = PriceEstimationPeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    safe_contract_address=cls.safe_contract_address,
                    participants=frozenset(list(cls.safe_owners.keys())),
                    most_voted_keeper_address=cls.keeper_address,
                    most_voted_estimate=1,
                ),
            )
        )

    def deploy_oracle(self) -> None:
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
            self.price_estimation_period_state,
            DeployOracleBehaviour.state_id,
            handlers_enter,
            expected_content_enter,
            expected_types_enter,
        )
        assert msg4 is not None and isinstance(msg4, LedgerApiMessage)
        oracle_contract_address = EthereumApi.get_contract_address(
            msg4.transaction_receipt.receipt
        )

        # update period state with oracle contract address
        self.price_estimation_period_state.update(
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
            self.price_estimation_period_state,
            TransactionHashBehaviour.state_id,
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
            self.price_estimation_period_state.oracle_contract_address,
            tx_data,
        )

        # update period state with safe's tx hash
        self.tx_settlement_period_state.update(
            most_voted_tx_hash=payload,
        )

    def clear_unmined_txs(self) -> None:
        """Clear all unmined txs. Mined txs will not be cleared, but this is not a problem."""
        for tx in self.tx_settlement_period_state.tx_hashes_history:
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
        ) -> Dict[str, Wei]:
            """Get a dummy gas price."""
            tip = max_priority_fee_per_gas
            gas = max_fee_per_gas

            if old_price is not None:
                tip = ceil(max_priority_fee_per_gas * repricing_multiplier)
                gas = ceil(max_fee_per_gas * repricing_multiplier)
            return {"maxPriorityFeePerGas": tip, "maxFeePerGas": gas}

        return dummy_try_get_gas_pricing


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

        # deploy the oracle
        self.deploy_oracle()
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
            RPCEndpoint("evm_setIntervalMining"), [1000]
        ), "Re-enabling auto-mining failed!"
        # send tx second time
        self.send_tx()
        # validate the tx
        self.validate_tx()


class TestKeepers(OracleBehaviourBaseCase, IntegrationBaseCase):
    """Test the keepers related functionality for the tx settlement skill."""

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Set up the test class."""
        super().setup()

        cls.tx_settlement_period_state = TxSettlementPeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    participants=frozenset(list(cls.agents.keys())),
                ),
            )
        )

    def select_keeper(self, first_time: bool = False) -> None:
        """Select a keeper."""

        if first_time:
            state_id = SelectKeeperTransactionSubmissionBehaviourA.state_id
        else:
            state_id = SelectKeeperTransactionSubmissionBehaviourB.state_id

        # select keeper
        self.fast_forward_to_state(
            self.behaviour,
            state_id,
            self.tx_settlement_period_state,
        )
        assert self.behaviour.current_state is not None
        assert self.behaviour.current_state.state_id == state_id

        self.behaviour.act_wrapper()
        # update keepers.
        self.tx_settlement_period_state.update(
            # we cast to A class, because it is the top level one between A & B, and we need `serialized_keepers`
            keepers=cast(
                SelectKeeperTransactionSubmissionBehaviourA,
                self.behaviour.current_state,
            ).serialized_keepers
        )

    def test_keepers_alternating(self) -> None:
        """Test that we are alternating the keepers when we fail or timeout more than `keeper_allowed_retries` times."""
        # set randomness
        self.tx_settlement_period_state.update(
            most_voted_randomness="0xabcd",
            final_verification_status=VerificationStatus.PENDING,
        )

        # select keeper a
        self.select_keeper(first_time=True)
        assert isinstance(
            self.behaviour.current_state, SelectKeeperTransactionSubmissionBehaviourA
        )
        assert self.tx_settlement_period_state.keeper_retries == 1
        assert self.tx_settlement_period_state.is_keeper_set
        assert (
            self.tx_settlement_period_state.most_voted_keeper_address
            == "0xBcd4042DE499D14e55001CcbB24a551F3b954096"
        )

        for i in range(self.behaviour.current_state.params.keeper_allowed_retries - 1):
            # select keeper b
            self.select_keeper()
            assert isinstance(
                self.behaviour.current_state,
                SelectKeeperTransactionSubmissionBehaviourB,
            )
            # +2 because we selected once for keeperA and also index starts from 0.
            assert self.tx_settlement_period_state.keeper_retries == i + 2
            # ensure that we select the same keeper until the `keeper_allowed_retries` is reached.
            assert (
                self.tx_settlement_period_state.most_voted_keeper_address
                == "0xBcd4042DE499D14e55001CcbB24a551F3b954096"
            )

        assert (
            self.tx_settlement_period_state.keeper_retries
            == self.behaviour.current_state.params.keeper_allowed_retries
        )
        # select keeper b after retries are reached.
        self.select_keeper()
        assert isinstance(
            self.behaviour.current_state, SelectKeeperTransactionSubmissionBehaviourB
        )
        assert self.tx_settlement_period_state.keeper_retries == 1
        # ensure that we select another keeper now that the `keeper_allowed_retries` is reached.
        assert (
            self.tx_settlement_period_state.most_voted_keeper_address
            != "0xBcd4042DE499D14e55001CcbB24a551F3b954096"
        )
        assert (
            "0xBcd4042DE499D14e55001CcbB24a551F3b954096"
            in self.tx_settlement_period_state.keepers
        )
