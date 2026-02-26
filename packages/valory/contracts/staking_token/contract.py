# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2025 Valory AG
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

"""This module contains the class to connect to the `StakingToken` contract."""

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


class StakingTokenContract(Contract):
    """The Staking Token contract."""

    contract_id = PublicId.from_str("valory/staking_token:0.1.0")

    @classmethod
    def get_service_staking_state(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> JSONLike:
        """Check whether the service is staked."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        res = contract_instance.functions.getStakingState(service_id).call()
        return dict(data=res)

    @classmethod
    def build_stake_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> JSONLike:
        """Build stake tx."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        data = contract_instance.encode_abi("stake", args=[service_id])
        return dict(data=bytes.fromhex(data[2:]))

    @classmethod
    def build_checkpoint_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Build checkpoint tx."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        data = contract_instance.encode_abi("checkpoint")
        return dict(data=bytes.fromhex(data[2:]))

    @classmethod
    def build_unstake_tx(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> JSONLike:
        """Build unstake tx."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        data = contract_instance.encode_abi("unstake", args=[service_id])
        return dict(data=bytes.fromhex(data[2:]))

    @classmethod
    def available_rewards(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Get the available rewards."""
        contract_instance = cls.get_instance(ledger_api, contract_address)
        res = contract_instance.functions.availableRewards().call()
        return dict(data=res)

    @classmethod
    def get_staking_rewards(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> JSONLike:
        """Get the service's staking rewards."""
        contract = cls.get_instance(ledger_api, contract_address)
        reward = contract.functions.calculateStakingReward(service_id).call()
        return dict(data=reward)

    @classmethod
    def get_next_checkpoint_ts(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Get the next checkpoint's timestamp."""
        contract = cls.get_instance(ledger_api, contract_address)
        ts = contract.functions.getNextRewardCheckpointTimestamp().call()
        return dict(data=ts)

    @classmethod
    def ts_checkpoint(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Retrieve the checkpoint's timestamp."""
        contract = cls.get_instance(ledger_api, contract_address)
        ts_checkpoint = contract.functions.tsCheckpoint().call()
        return dict(data=ts_checkpoint)

    @classmethod
    def liveness_ratio(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Retrieve the liveness ratio."""
        contract = cls.get_instance(ledger_api, contract_address)
        liveness_ratio = contract.functions.livenessRatio().call()
        return dict(data=liveness_ratio)

    @classmethod
    def get_liveness_period(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Retrieve the liveness period."""
        contract = cls.get_instance(ledger_api, contract_address)
        liveness_period = contract.functions.livenessPeriod().call()
        return dict(data=liveness_period)

    @classmethod
    def get_service_info(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        service_id: int,
    ) -> JSONLike:
        """Retrieve the service info for a service."""
        contract = cls.get_instance(ledger_api, contract_address)
        info = contract.functions.getServiceInfo(service_id).call()
        return dict(data=info)

    @classmethod
    def max_num_services(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Retrieve the max number of services."""
        contract = cls.get_instance(ledger_api, contract_address)
        max_num_services = contract.functions.maxNumServices().call()
        return dict(data=max_num_services)

    @classmethod
    def get_service_ids(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Retrieve the service IDs."""
        contract = cls.get_instance(ledger_api, contract_address)
        service_ids = contract.functions.getServiceIds().call()
        return dict(data=service_ids)

    @classmethod
    def get_min_staking_duration(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Retrieve the service IDs."""
        contract = cls.get_instance(ledger_api, contract_address)
        duration = contract.functions.minStakingDuration().call()
        return dict(data=duration)

    @classmethod
    def get_agent_ids(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Retrieve the agent IDs."""
        contract = cls.get_instance(ledger_api, contract_address)
        agent_ids = contract.functions.getAgentIds().call()
        return dict(data=agent_ids)
