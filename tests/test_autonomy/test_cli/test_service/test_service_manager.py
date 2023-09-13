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

"""Test service management."""

import binascii
from typing import List, Optional
from unittest import mock

from aea.components.base import load_aea_package
from aea.configurations.data_types import PackageType
from aea.configurations.loader import load_configuration_object
from aea.contracts.base import Contract
from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto
from aea_test_autonomy.configurations import ETHEREUM_KEY_PATH_5
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401
from click.testing import Result
from hexbytes import HexBytes
from web3 import HTTPProvider, Web3

from autonomy.chain.base import ServiceState, registry_contracts
from autonomy.chain.config import ChainType
from autonomy.chain.constants import ERC20_TOKEN_ADDRESS_LOCAL, HardhatAddresses
from autonomy.chain.service import (
    activate_service,
    deploy_service,
    get_service_info,
    register_instance,
    terminate_service,
    unbond_service,
)
from autonomy.cli.helpers.chain import ServiceHelper

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_chain.base import (
    AGENT_ID,
    BaseChainInteractionTest,
    COST_OF_BOND_FOR_AGENT,
    DUMMY_SERVICE,
    NUMBER_OF_SLOTS_PER_AGENT,
    THRESHOLD,
)


DEFAULT_AGENT_INSTANCE_ADDRESS = (
    "0x976EA74026E726554dB657fA54763abd0C3a0aa9"  # a key from default hardhat keys
)
MAX_DEPLOY_ATTEMPTS = 5


class BaseServiceManagerTest(BaseChainInteractionTest):
    """Test service manager."""

    cli_options = ("service",)
    key_file = ETHEREUM_KEY_PATH_5

    def mint_service(
        self,
        number_of_slots_per_agent: int = NUMBER_OF_SLOTS_PER_AGENT,
        threshold: int = THRESHOLD,
    ) -> int:
        """Mint service component"""
        with mock.patch("autonomy.cli.helpers.chain.verify_service_dependencies"):
            service_id = self.mint_component(
                package_id=DUMMY_SERVICE,
                service_mint_parameters=dict(
                    agent_ids=[AGENT_ID],
                    number_of_slots_per_agent=[number_of_slots_per_agent],
                    cost_of_bond_per_agent=[COST_OF_BOND_FOR_AGENT],
                    threshold=threshold,
                ),
            )

        assert isinstance(service_id, int)
        return service_id

    def activate_service(self, service_id: int) -> None:
        """Activate service"""
        activate_service(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            service_id=service_id,
        )

    def register_instances(
        self, service_id: int, agent_instance: Optional[str] = None
    ) -> None:
        """Register agent instance."""

        register_instance(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            service_id=service_id,
            instances=[(agent_instance or make_crypto("ethereum").address)],
            agent_ids=[AGENT_ID],
        )

    def deploy_service(
        self,
        service_id: int,
        deployment_payload: Optional[str] = None,
        reuse_multisig: bool = False,
    ) -> None:
        """Deploy service."""

        deploy_service(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            service_id=service_id,
            deployment_payload=deployment_payload,
            reuse_multisig=reuse_multisig,
        )

    def terminate_service(self, service_id: int) -> None:
        """Terminate service."""

        terminate_service(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            service_id=service_id,
        )

    def unbond_service(self, service_id: int) -> None:
        """Unbond service."""

        unbond_service(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            service_id=service_id,
        )


class TestServiceManager(BaseServiceManagerTest):
    """Test service manager."""

    def test_activate_service(self) -> None:
        """Test activate service."""

        def _run_command(service_id: str) -> Result:
            """Run command and return result"""
            return self.run_cli(
                commands=(
                    "activate",
                    service_id,
                    "--key",
                    str(self.key_file),
                )
            )

        result = _run_command("100")
        # This should fail since the service is not there yet
        assert result.exit_code == 1, result.output
        assert "Service does not exist" in result.stderr

        service_id = self.mint_service()

        result = _run_command(str(service_id))
        # first attempt should be succesfull
        assert result.exit_code == 0, result.output
        assert "Service activated succesfully" in result.output

        result = _run_command(str(service_id))
        # first attempt should fail since the service already active
        assert result.exit_code == 1, service_id
        assert "Service must be inactive" in result.stderr

    def test_register_instances(
        self,
    ) -> None:
        """Test register instance on a service"""

        agent_instance = make_crypto("ethereum")

        def _run_command(service_id: str) -> Result:
            """Run command and return result"""
            return self.run_cli(
                commands=(
                    "register",
                    service_id,
                    "--key",
                    str(self.key_file),
                    "-a",
                    "1",
                    "-i",
                    agent_instance.address,
                )
            )

        result = _run_command("100")
        assert result.exit_code == 1, result.output
        assert "Service does not exist" in result.stderr

        service_id = self.mint_service()
        result = _run_command(str(service_id))
        assert result.exit_code == 1, result.output
        assert "Service needs to be in active state" in result.stderr

        self.activate_service(
            service_id=service_id,
        )

        result = _run_command(str(service_id))
        assert result.exit_code == 0, result.stderr
        assert "Agent instance registered succesfully" in result.output

        result = _run_command(str(service_id))
        # Will fail becaue the agent instance is already registered
        assert result.exit_code == 1, result.stdout
        assert "Instance registration failed" in result.stderr
        assert "AgentInstanceRegistered" in result.stderr

    def test_deploy(
        self,
    ) -> None:
        """Test register instance on a service"""

        def _run_command(service_id: str) -> Result:
            """Run command and return result"""
            return self.run_cli(
                commands=(
                    "deploy",
                    service_id,
                    "--key",
                    str(self.key_file),
                )
            )

        service_id = self.mint_service()
        self.activate_service(
            service_id=service_id,
        )

        result = _run_command(str(service_id))
        assert result.exit_code == 1, result.output
        assert "Service needs to be in finished registration state" in result.stderr

        for _ in range(NUMBER_OF_SLOTS_PER_AGENT):
            self.register_instances(
                service_id=service_id,
            )

        result = _run_command(str(service_id))

        assert result.exit_code == 0, result.stderr
        assert "Service deployed succesfully" in result.output

        result = self.run_cli(
            commands=(
                "deploy",
                str(service_id),
                "--key",
                str(self.key_file),
            )
        )

        # Will fail becaue the service is already deployed
        assert result.exit_code == 1, result.stdout
        assert "Service needs to be in finished registration state" in result.stderr

    def test_terminate(
        self,
    ) -> None:
        """Test terminate service."""

        def _run_command(service_id: str) -> Result:
            """Run command and return result"""
            return self.run_cli(
                commands=(
                    "terminate",
                    service_id,
                    "--key",
                    str(self.key_file),
                )
            )

        result = _run_command("100")
        assert result.exit_code == 1, result.output
        assert "Service does not exist" in result.stderr

        service_id = self.mint_service()

        result = _run_command(str(service_id))
        assert result.exit_code == 1, result.output
        assert "Service not active" in result.stderr

        self.activate_service(
            service_id=service_id,
        )
        for _ in range(NUMBER_OF_SLOTS_PER_AGENT):
            self.register_instances(
                service_id=service_id,
            )
        self.deploy_service(service_id=service_id)

        result = _run_command(str(service_id))

        assert result.exit_code == 0, result.stderr
        assert "Service terminated succesfully" in result.output

        result = _run_command(str(service_id))

        # Will fail becaue the service is already deployed
        assert result.exit_code == 1, result.stdout
        assert "Service already terminated" in result.stderr

    def test_unbond(
        self,
    ) -> None:
        """Test unbond service."""

        def _run_command(service_id: str) -> Result:
            """Run command and return result"""
            return self.run_cli(
                commands=(
                    "unbond",
                    service_id,
                    "--key",
                    str(self.key_file),
                )
            )

        result = _run_command("100")
        assert result.exit_code == 1, result.output
        assert "Service does not exist" in result.stderr

        service_id = self.mint_service()

        self.activate_service(
            service_id=service_id,
        )
        for _ in range(NUMBER_OF_SLOTS_PER_AGENT):
            self.register_instances(
                service_id=service_id,
            )
        self.deploy_service(service_id=service_id)

        result = _run_command(str(service_id))
        assert result.exit_code == 1, result.output
        assert "Service needs to be in terminated-bonded state" in result.stderr

        self.terminate_service(service_id=service_id)

        result = _run_command(str(service_id))

        assert result.exit_code == 0, result.stderr
        assert "Service unbonded succesfully" in result.output

        result = _run_command(str(service_id))

        # Will fail becaue the service is already deployed
        assert result.exit_code == 1, result.stdout
        assert "Service needs to be in terminated-bonded state" in result.stderr

    def test_info(
        self,
    ) -> None:
        """Test service info."""

        def _run_check(service_id: str, message: str) -> Result:
            """Run command and return result"""
            result = self.run_cli(commands=("info", service_id))
            assert result.exit_code == 0
            assert message in result.output

        _run_check("100", message=ServiceState.NON_EXISTENT.name)

        service_id = self.mint_service()
        _run_check(
            service_id=str(service_id), message=ServiceState.PRE_REGISTRATION.name
        )

        self.activate_service(service_id=service_id)
        _run_check(
            service_id=str(service_id), message=ServiceState.ACTIVE_REGISTRATION.name
        )

        for _ in range(NUMBER_OF_SLOTS_PER_AGENT):
            self.register_instances(
                service_id=service_id,
            )
        _run_check(
            service_id=str(service_id), message=ServiceState.FINISHED_REGISTRATION.name
        )

        self.deploy_service(service_id=service_id)
        _run_check(service_id=str(service_id), message=ServiceState.DEPLOYED.name)

        self.terminate_service(service_id=service_id)
        _run_check(
            service_id=str(service_id), message=ServiceState.TERMINATED_BONDED.name
        )

        self.unbond_service(service_id=service_id)
        _run_check(
            service_id=str(service_id), message=ServiceState.PRE_REGISTRATION.name
        )


class TestERC20AsBond(BaseServiceManagerTest):
    """Test ERC20 token as bond."""

    def setup(self) -> None:
        """Setup test."""
        super().setup()
        erc20_instance = Contract.from_dir(
            ROOT_DIR / "packages" / "valory" / "contracts" / "erc20"
        ).get_instance(
            ledger_api=self.ledger_api,
            contract_address=ERC20_TOKEN_ADDRESS_LOCAL,
        )
        tx = erc20_instance.functions.mint(
            self.crypto.address, int(1e18)
        ).build_transaction(
            {
                "from": self.crypto.address,
                "gas": 200001,
                "gasPrice": 30000,
                "nonce": self.ledger_api.api.eth.get_transaction_count(
                    self.crypto.address
                ),
            }
        )
        stx = self.crypto.entity.sign_transaction(tx)
        tx_digext = self.ledger_api.api.eth.send_raw_transaction(stx.rawTransaction)
        while True:
            try:
                return self.ledger_api.api.eth.get_transaction_receipt(tx_digext)
            except Exception:  # nosec
                continue

    def mint(self) -> int:
        """Mint service with token"""
        with mock.patch("autonomy.cli.helpers.chain.verify_service_dependencies"):
            service_id = self.mint_component(
                package_id=DUMMY_SERVICE,
                service_mint_parameters=dict(
                    agent_ids=[AGENT_ID],
                    number_of_slots_per_agent=[NUMBER_OF_SLOTS_PER_AGENT],
                    cost_of_bond_per_agent=[COST_OF_BOND_FOR_AGENT],
                    threshold=THRESHOLD,
                    token=ERC20_TOKEN_ADDRESS_LOCAL,
                ),
            )
        assert isinstance(service_id, int)
        return service_id

    def test_mint(self) -> None:
        """Test mint with ERC20 token as bond."""
        service_id = self.mint()
        assert (
            ServiceHelper(
                service_id=service_id,
                chain_type=ChainType.LOCAL,
                key=self.key_file,
            )
            .check_is_service_token_secured(token=ERC20_TOKEN_ADDRESS_LOCAL)
            .token_secured
            is True
        )

    def test_activate(self) -> None:
        """Test activate with token."""
        service_id = self.mint()
        result = self.run_cli(
            commands=(
                "activate",
                str(service_id),
                "--key",
                str(self.key_file),
                "--token",
                ERC20_TOKEN_ADDRESS_LOCAL,
            )
        )
        assert result.exit_code == 0, result.output

    def test_activate_failure(self) -> None:
        """Test activate with token."""
        service_id = self.mint()
        result = self.run_cli(
            commands=(
                "activate",
                str(service_id),
                "--key",
                str(self.key_file),
            )
        )

        assert result.exit_code == 1, result.output
        assert (
            "Service is token secured, please provice token address using `--token` flag"
            in result.stderr
        )

    def test_register_instances(self) -> None:
        """Test register instances with token."""
        service_id = self.mint()
        result = self.run_cli(
            commands=(
                "activate",
                str(service_id),
                "--key",
                str(self.key_file),
                "--token",
                ERC20_TOKEN_ADDRESS_LOCAL,
            )
        )
        assert result.exit_code == 0, result.output

        agent = make_crypto("ethereum")
        result = self.run_cli(
            commands=(
                "register",
                str(service_id),
                "--key",
                str(self.key_file),
                "-a",
                str(AGENT_ID),
                "-i",
                agent.address,
                "--token",
                ERC20_TOKEN_ADDRESS_LOCAL,
            )
        )
        assert result.exit_code == 0, result.output

    def test_register_instances_failure(self) -> None:
        """Test register instances with token."""
        service_id = self.mint()
        result = self.run_cli(
            commands=(
                "activate",
                str(service_id),
                "--key",
                str(self.key_file),
                "--token",
                ERC20_TOKEN_ADDRESS_LOCAL,
            )
        )
        assert result.exit_code == 0, result.output

        agent = make_crypto("ethereum")
        result = self.run_cli(
            commands=(
                "register",
                str(service_id),
                "--key",
                str(self.key_file),
                "-a",
                str(AGENT_ID),
                "-i",
                agent.address,
            )
        )
        assert result.exit_code == 1, result.output
        assert (
            "Service is token secured, please provice token address using `--token` flag"
            in result.stderr
        )


class TestServiceRedeploymentWithSameMultisig(BaseServiceManagerTest):
    """Test service deployment with same multisig."""

    def setup(self) -> None:
        """Setup class."""
        super().setup()
        self.ledger_api._api = Web3(
            HTTPProvider(
                endpoint_uri="http://127.0.0.1:8545",
                request_kwargs={
                    "timeout": 120,
                },
            ),
        )
        self.ledger_api.api.eth.default_account = self.crypto.address

    def fund(self, address: str, amount: int = 1) -> None:
        """Fund an address."""
        raw_tx = {
            "to": address,
            "from": self.crypto.address,
            "value": self.ledger_api.api.to_wei(amount, "ether"),
            "gas": 100000,
            "chainId": self.ledger_api.api.eth.chain_id,
            "gasPrice": self.ledger_api.api.eth.gas_price,
            "nonce": self.ledger_api.api.eth.get_transaction_count(self.crypto.address),
        }
        signed_tx = self.crypto.entity.sign_transaction(raw_tx)
        self.ledger_api.api.eth.send_raw_transaction(signed_tx.rawTransaction)

    def generate_and_fund_keys(self, n: int = 4) -> List[Crypto]:
        """Generate and fund keys."""
        keys = []
        for _ in range(n):
            crypto = make_crypto("ethereum")
            keys.append(crypto)
        self.fund(address=keys[0].address)
        return keys

    def remove_owners(self, multisig_address: str, owners: List[Crypto]) -> None:
        """Remove owners."""

        # Load packages in the memory.
        packages_dir = ROOT_DIR / "packages" / "valory"
        for package_type, package_path in (
            (
                PackageType.CONTRACT,
                packages_dir / "contracts" / "gnosis_safe_proxy_factory",
            ),
            (PackageType.CONTRACT, packages_dir / "contracts" / "gnosis_safe"),
            (PackageType.CONTRACT, packages_dir / "contracts" / "multisend"),
            (
                PackageType.SKILL,
                packages_dir / "skills" / "transaction_settlement_abci",
            ),
        ):
            config_obj = load_configuration_object(
                package_type=package_type, directory=package_path
            )
            config_obj.directory = package_path
            load_aea_package(configuration=config_obj)

        from packages.valory.contracts.gnosis_safe.contract import SafeOperation
        from packages.valory.contracts.multisend.contract import MultiSendOperation
        from packages.valory.skills.transaction_settlement_abci.payload_tools import (
            hash_payload_to_hex,
            skill_input_hex_to_payload,
        )

        multisend_address = HardhatAddresses.multisend
        threshold = 1
        owner_to_swap = owners[0].address
        owners_to_remove = reversed(owners[1:])
        multisend_txs = []

        for owner in owners_to_remove:
            txd = registry_contracts.gnosis_safe.get_remove_owner_data(
                ledger_api=self.ledger_api,
                contract_address=multisig_address,
                owner=owner.address,
                threshold=threshold,
            ).get("data")
            multisend_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": multisig_address,
                    "value": 0,
                    "data": HexBytes(bytes.fromhex(txd[2:])),
                }
            )
        txd = registry_contracts.gnosis_safe.get_swap_owner_data(
            ledger_api=self.ledger_api,
            contract_address=multisig_address,
            old_owner=self.ledger_api.api.to_checksum_address(owner_to_swap),
            new_owner=self.ledger_api.api.to_checksum_address(self.crypto.address),
        ).get("data")
        multisend_txs.append(
            {
                "operation": MultiSendOperation.CALL,
                "to": multisig_address,
                "value": 0,
                "data": HexBytes(txd[2:]),
            }
        )

        multisend_txd = registry_contracts.multisend.get_tx_data(
            ledger_api=self.ledger_api,
            contract_address=multisend_address,
            multi_send_txs=multisend_txs,
        ).get("data")
        multisend_data = bytes.fromhex(multisend_txd[2:])

        safe_tx_hash = registry_contracts.gnosis_safe.get_raw_safe_transaction_hash(
            ledger_api=self.ledger_api,
            contract_address=multisig_address,
            to_address=multisend_address,
            value=0,
            data=multisend_data,
            safe_tx_gas=0,
            operation=SafeOperation.DELEGATE_CALL.value,
        ).get("tx_hash")[2:]

        payload_data = hash_payload_to_hex(
            safe_tx_hash=safe_tx_hash,
            ether_value=0,
            safe_tx_gas=0,
            to_address=multisend_address,
            data=multisend_data,
        )

        tx_params = skill_input_hex_to_payload(payload=payload_data)
        safe_tx_bytes = binascii.unhexlify(tx_params["safe_tx_hash"])
        owner_to_signature = {}
        for owner_crypto in owners:
            signature = owner_crypto.sign_message(
                message=safe_tx_bytes,
                is_deprecated_mode=True,
            )
            owner_to_signature[
                self.ledger_api.api.to_checksum_address(owner_crypto.address)
            ] = signature[2:]

        tx = registry_contracts.gnosis_safe.get_raw_safe_transaction(
            ledger_api=self.ledger_api,
            contract_address=multisig_address,
            sender_address=owners[0].address,
            owners=tuple([owner.address for owner in owners]),
            to_address=tx_params["to_address"],
            value=tx_params["ether_value"],
            data=tx_params["data"],
            safe_tx_gas=tx_params["safe_tx_gas"],
            signatures_by_owner=owner_to_signature,
            operation=SafeOperation.DELEGATE_CALL.value,
        )
        stx = owners[0].sign_transaction(tx)
        tx_digest = self.ledger_api.send_signed_transaction(stx)
        self.ledger_api.get_transaction_receipt(tx_digest)

    def test_redeploy(self) -> None:
        """Test redeploy service with same multisig."""
        n = 2
        instances = self.generate_and_fund_keys(n=n)
        service_id = self.mint_service(number_of_slots_per_agent=n, threshold=n)
        self.activate_service(service_id=service_id)
        for instance in instances:
            self.register_instances(
                service_id=service_id, agent_instance=instance.address
            )
        self.deploy_service(service_id=service_id)
        self.terminate_service(service_id=service_id)
        self.unbond_service(service_id=service_id)
        _, multisig_address, *_ = get_service_info(
            ledger_api=self.ledger_api,
            chain_type=ChainType.LOCAL,
            token_id=service_id,
        )
        self.remove_owners(multisig_address=multisig_address, owners=instances)

        new_instances = self.generate_and_fund_keys(n=n)
        self.activate_service(service_id=service_id)
        for instance in new_instances:
            self.register_instances(
                service_id=service_id, agent_instance=instance.address
            )

        self.deploy_service(service_id=service_id, reuse_multisig=True)
        _, multisig_address_redeployed, *_ = get_service_info(
            ledger_api=self.ledger_api,
            chain_type=ChainType.LOCAL,
            token_id=service_id,
        )
        assert multisig_address_redeployed == multisig_address
        safe_owners = registry_contracts.gnosis_safe.get_owners(
            ledger_api=self.ledger_api,
            contract_address=multisig_address,
        ).get("owners")
        assert set(safe_owners) == set([instance.address for instance in new_instances])
