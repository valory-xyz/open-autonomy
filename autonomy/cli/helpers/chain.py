# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""On-chain interaction helpers."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

import click
from aea.configurations.base import PackageConfiguration
from aea.configurations.data_types import PackageType
from aea.configurations.loader import load_configuration_object
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea.helpers.base import IPFSHash
from texttable import Texttable

from autonomy.chain.base import ServiceState, UnitType
from autonomy.chain.config import ChainConfigs, ChainType, ContractConfigs
from autonomy.chain.constants import (
    AGENT_REGISTRY_CONTRACT,
    COMPONENT_REGISTRY_CONTRACT,
    SERVICE_REGISTRY_CONTRACT,
)
from autonomy.chain.exceptions import (
    ComponentMintFailed,
    DependencyError,
    FailedToRetrieveComponentMetadata,
    FailedToRetrieveTokenId,
    InstanceRegistrationFailed,
    InvalidMintParameter,
    ServiceDeployFailed,
    ServiceRegistrationFailed,
    TerminateServiceFailed,
    UnbondServiceFailed,
)
from autonomy.chain.metadata import NFTHashOrPath, publish_metadata
from autonomy.chain.mint import DEFAULT_NFT_IMAGE_HASH
from autonomy.chain.mint import mint_component as _mint_component
from autonomy.chain.mint import mint_service as _mint_service
from autonomy.chain.mint import update_component as _update_component
from autonomy.chain.mint import update_service as _update_service
from autonomy.chain.service import activate_service as _activate_service
from autonomy.chain.service import deploy_service as _deploy_service
from autonomy.chain.service import get_agent_instances, get_service_info
from autonomy.chain.service import register_instance as _register_instance
from autonomy.chain.service import terminate_service as _terminate_service
from autonomy.chain.service import unbond_service as _unbond_service
from autonomy.chain.utils import (
    resolve_component_id,
    verify_component_dependencies,
    verify_service_dependencies,
)
from autonomy.configurations.base import PACKAGE_TYPE_TO_CONFIG_CLASS, Service


try:
    from aea_ledger_ethereum.ethereum import EthereumApi, EthereumCrypto

    ETHEREUM_PLUGIN_INSTALLED = True
except ImportError:  # pragma: nocover
    ETHEREUM_PLUGIN_INSTALLED = False

try:
    from aea_ledger_ethereum_hwi.exceptions import HWIError
    from aea_ledger_ethereum_hwi.hwi import EthereumHWIApi

    HWI_PLUGIN_INSTALLED = True
except ImportError:  # pragma: nocover
    HWI_PLUGIN_INSTALLED = False


def get_ledger_and_crypto_objects(
    chain_type: ChainType,
    key: Optional[Path] = None,
    password: Optional[str] = None,
    hwi: bool = False,
) -> Tuple[LedgerApi, Crypto]:
    """Create ledger_api and crypto objects"""

    chain_config = ChainConfigs.get(chain_type=chain_type)
    identifier = EthereumApi.identifier

    if chain_config.rpc is None:
        raise click.ClickException(
            f"RPC URL cannot be `None`, "
            f"Please set the environment variable for {chain_type.value} chain "
            f"using `{ChainConfigs.get_rpc_env_var(chain_type)}` environment variable"
        )

    if hwi and not HWI_PLUGIN_INSTALLED:
        raise click.ClickException(
            "Hardware wallet plugin not installed, "
            "Run `pip3 install open-aea-ledger-ethereum-hwi` to install the plugin"
        )

    if hwi:
        identifier = EthereumHWIApi.identifier

    if not hwi and not ETHEREUM_PLUGIN_INSTALLED:
        raise click.ClickException(
            "Ethereum ledger plugin not installed, "
            "Run `pip3 install open-aea-ledger-ethereum` to install the plugin"
        )

    if key is None:
        crypto = crypto_registry.make(identifier)
    else:
        crypto = EthereumCrypto(
            private_key_path=key,
            password=password,
        )

    ledger_api = ledger_apis_registry.make(
        identifier,
        **{
            "address": chain_config.rpc,
            "chain_id": chain_config.chain_id,
            "is_gas_estimation_enabled": True,
        },
    )

    if hwi:
        # Setting the `LedgerApi.identifier` to `ethereum` for both ledger and
        # hardware plugin to interact with the contract. If we use `ethereum_hwi`
        # as the ledger identifier the contracts will need ABI configuration for
        # the `ethereum_hwi` identifier which means we will have to define hardware
        # wallet as the dependency for contract but the hardware wallet plugin
        # is meant to be used for CLI tools only so we set the identifier to
        # `ethereum` for both ledger and hardware wallet plugin
        ledger_api.identifier = EthereumApi.identifier

    try:
        ledger_api.api.eth.default_account = crypto.address
    except HWIError as e:
        raise click.ClickException(e.message)

    return ledger_api, crypto


def activate_service(  # pylint: disable=too-many-arguments
    service_id: int,
    key: Path,
    chain_type: ChainType,
    password: Optional[str] = None,
    timeout: Optional[float] = None,
    hwi: bool = False,
) -> None:
    """Activate on-chain service"""

    if key is None and not hwi:  # pragma: nocover
        raise click.ClickException(
            "Please provide key path using `--key` or use `--hwi` if you want to use a hardware wallet"
        )

    ledger_api, crypto = get_ledger_and_crypto_objects(
        chain_type=chain_type,
        key=key,
        password=password,
        hwi=hwi,
    )

    try:
        _activate_service(
            ledger_api=ledger_api,
            crypto=crypto,
            chain_type=chain_type,
            service_id=service_id,
            timeout=timeout,
        )
    except ServiceRegistrationFailed as e:
        raise click.ClickException(str(e)) from e

    click.echo("Service activated succesfully")


def register_instance(  # pylint: disable=too-many-arguments
    service_id: int,
    instances: List[str],
    agent_ids: List[int],
    key: Path,
    chain_type: ChainType,
    password: Optional[str] = None,
    timeout: Optional[float] = None,
    hwi: bool = False,
) -> None:
    """Register agents instances on an activated service"""

    if key is None and not hwi:  # pragma: nocover
        raise click.ClickException(
            "Please provide key path using `--key` or use `--hwi` if you want to use a hardware wallet"
        )

    ledger_api, crypto = get_ledger_and_crypto_objects(
        chain_type=chain_type,
        key=key,
        password=password,
        hwi=hwi,
    )

    try:
        _register_instance(
            ledger_api=ledger_api,
            crypto=crypto,
            chain_type=chain_type,
            service_id=service_id,
            instances=instances,
            agent_ids=agent_ids,
            timeout=timeout,
        )
    except InstanceRegistrationFailed as e:
        raise click.ClickException(str(e)) from e

    click.echo("Agent instance registered succesfully")


def deploy_service(  # pylint: disable=too-many-arguments
    service_id: int,
    key: Path,
    chain_type: ChainType,
    deployment_payload: Optional[str] = None,
    password: Optional[str] = None,
    timeout: Optional[float] = None,
    hwi: bool = False,
) -> None:
    """Deploy a service with registration activated"""

    if key is None and not hwi:  # pragma: nocover
        raise click.ClickException(
            "Please provide key path using `--key` or use `--hwi` if you want to use a hardware wallet"
        )

    ledger_api, crypto = get_ledger_and_crypto_objects(
        chain_type=chain_type,
        key=key,
        password=password,
        hwi=hwi,
    )

    try:
        _deploy_service(
            ledger_api=ledger_api,
            crypto=crypto,
            chain_type=chain_type,
            service_id=service_id,
            deployment_payload=deployment_payload,
            timeout=timeout,
        )
    except ServiceDeployFailed as e:
        raise click.ClickException(str(e)) from e

    click.echo("Service deployed succesfully")


def terminate_service(
    service_id: int,
    key: Path,
    chain_type: ChainType,
    password: Optional[str] = None,
    hwi: bool = False,
) -> None:
    """Terminate a service"""

    if key is None and not hwi:  # pragma: nocover
        raise click.ClickException(
            "Please provide key path using `--key` or use `--hwi` if you want to use a hardware wallet"
        )

    ledger_api, crypto = get_ledger_and_crypto_objects(
        chain_type=chain_type,
        key=key,
        password=password,
        hwi=hwi,
    )

    try:
        _terminate_service(
            ledger_api=ledger_api,
            crypto=crypto,
            chain_type=chain_type,
            service_id=service_id,
        )
    except TerminateServiceFailed as e:
        raise click.ClickException(str(e)) from e

    click.echo("Service terminated succesfully")


def unbond_service(
    service_id: int,
    key: Path,
    chain_type: ChainType,
    password: Optional[str] = None,
    hwi: bool = False,
) -> None:
    """Terminate a service"""

    if key is None and not hwi:  # pragma: nocover
        raise click.ClickException(
            "Please provide key path using `--key` or use `--hwi` if you want to use a hardware wallet"
        )

    ledger_api, crypto = get_ledger_and_crypto_objects(
        chain_type=chain_type,
        key=key,
        password=password,
        hwi=hwi,
    )

    try:
        _unbond_service(
            ledger_api=ledger_api,
            crypto=crypto,
            chain_type=chain_type,
            service_id=service_id,
        )
    except UnbondServiceFailed as e:
        raise click.ClickException(str(e)) from e

    click.echo("Service unbonded succesfully")


def print_service_info(
    service_id: int,
    chain_type: ChainType,
) -> None:
    """Terminate a service"""

    ledger_api, _ = get_ledger_and_crypto_objects(
        chain_type=chain_type,
    )
    (
        security_deposit,
        multisig_address,
        _,
        threshold,
        max_agents,
        number_of_agent_instances,
        _service_state,
        cannonical_agents,
    ) = get_service_info(
        ledger_api=ledger_api,
        chain_type=chain_type,
        token_id=service_id,
    )
    service_state = ServiceState(_service_state)
    rows = [
        ("Property", "Value"),
        ("Service State", service_state.name),
        ("Security Deposit", security_deposit),
        ("Multisig Address", multisig_address),
        ("Cannonical Agents", ", ".join(map(str, cannonical_agents))),
        ("Max Agents", max_agents),
        ("Threshold", threshold),
        ("Number Of Agent Instances", number_of_agent_instances),
    ]

    if service_state.value >= ServiceState.ACTIVE_REGISTRATION.value:
        rows.append(
            (
                "Registered Instances",
                "\n".join(
                    map(
                        lambda x: f"- {x}",
                        get_agent_instances(
                            ledger_api=ledger_api,
                            chain_type=chain_type,
                            token_id=service_id,
                        ).get("agentInstances", []),
                    ),
                ),
            ),
        )
    click.echo(Texttable().add_rows(rows=rows).draw())


class OnChainHelper:  # pylint: disable=too-few-public-methods
    """On-chain interaction helper."""

    def __init__(
        self,
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False,
    ) -> None:
        """Initialize object."""
        if key is None and not hwi:
            raise click.ClickException(
                "Please provide key path using `--key` or use `--hwi` if you want to use a hardware wallet"
            )

        self.chain_type = chain_type
        self.ledger_api, self.crypto = self.get_ledger_and_crypto_objects(
            chain_type=chain_type,
            key=key,
            password=password,
            hwi=hwi,
        )

    @staticmethod
    def get_ledger_and_crypto_objects(
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False,
    ) -> Tuple[LedgerApi, Crypto]:
        """Create ledger_api and crypto objects"""
        chain_config = ChainConfigs.get(chain_type=chain_type)
        identifier = EthereumApi.identifier

        if chain_config.rpc is None:
            raise click.ClickException(
                f"RPC URL cannot be `None`, "
                f"Please set the environment variable for {chain_type.value} chain "
                f"using `{ChainConfigs.get_rpc_env_var(chain_type)}` environment variable"
            )

        if hwi and not HWI_PLUGIN_INSTALLED:
            raise click.ClickException(
                "Hardware wallet plugin not installed, "
                "Run `pip3 install open-aea-ledger-ethereum-hwi` to install the plugin"
            )

        if hwi:
            identifier = EthereumHWIApi.identifier

        if not hwi and not ETHEREUM_PLUGIN_INSTALLED:
            raise click.ClickException(
                "Ethereum ledger plugin not installed, "
                "Run `pip3 install open-aea-ledger-ethereum` to install the plugin"
            )

        if key is None:
            crypto = crypto_registry.make(identifier)
        else:
            crypto = EthereumCrypto(
                private_key_path=key,
                password=password,
            )

        ledger_api = ledger_apis_registry.make(
            identifier,
            **{
                "address": chain_config.rpc,
                "chain_id": chain_config.chain_id,
                "is_gas_estimation_enabled": True,
            },
        )

        if hwi:
            # Setting the `LedgerApi.identifier` to `ethereum` for both ledger and
            # hardware plugin to interact with the contract. If we use `ethereum_hwi`
            # as the ledger identifier the contracts will need ABI configuration for
            # the `ethereum_hwi` identifier which means we will have to define hardware
            # wallet as the dependency for contract but the hardware wallet plugin
            # is meant to be used for CLI tools only so we set the identifier to
            # `ethereum` for both ledger and hardware wallet plugin
            ledger_api.identifier = EthereumApi.identifier

        try:
            ledger_api.api.eth.default_account = crypto.address
        except HWIError as e:
            raise click.ClickException(e.message)

        return ledger_api, crypto


class MintHelper(OnChainHelper):  # pylint: disable=too-many-instance-attributes
    """Mint helper."""

    package_path: Path
    package_type: PackageType
    package_configuration: PackageConfiguration
    old_metadata: Dict[str, Any]
    nft: NFTHashOrPath
    dependencies: List[int]
    agent_id: int
    metadata_hash: str
    metadata_string: str
    token_id: Optional[int]

    def __init__(
        self,
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False,
        update_token: Optional[int] = None,
    ) -> None:
        """Initialize object."""
        super().__init__(chain_type, key, password, hwi)
        self.update_token = update_token

    def load_package_configuration(
        self,
        package_path: Path,
        package_type: PackageType,
    ) -> "MintHelper":
        """Load package configuration."""
        try:
            self.package_path = package_path
            self.package_type = package_type
            self.package_configuration = load_configuration_object(
                package_type=package_type,
                directory=package_path,
                package_type_config_class=PACKAGE_TYPE_TO_CONFIG_CLASS,
            )
            return self
        except FileNotFoundError as e:  # pragma: nocover
            raise click.ClickException(
                f"Cannot find configuration file for {package_type}"
            ) from e

    def load_metadata(self) -> "MintHelper":
        """Load metadata when updating a mint."""
        if self.update_token is None:
            return self

        if self.package_type == PackageType.SERVICE:
            is_service = True
            is_agent = False
            contract_address = ContractConfigs.get(
                SERVICE_REGISTRY_CONTRACT.name
            ).contracts[self.chain_type]
        elif self.package_type == PackageType.AGENT:
            is_service = False
            is_agent = True
            contract_address = ContractConfigs.get(
                AGENT_REGISTRY_CONTRACT.name
            ).contracts[self.chain_type]
        else:
            is_service = False
            is_agent = False
            contract_address = ContractConfigs.get(
                COMPONENT_REGISTRY_CONTRACT.name
            ).contracts[self.chain_type]

        self.old_metadata = resolve_component_id(
            ledger_api=self.ledger_api,
            contract_address=contract_address,
            is_agent=is_agent,
            is_service=is_service,
            token_id=self.update_token,
        )

        return self

    def verify_nft(self, nft: Optional[NFTHashOrPath] = None) -> "MintHelper":
        """Verify NFT image."""

        # If new NFT hash is not provided, check previous mint for NFT hash
        if self.update_token is not None and nft is None:
            image_uri = self.old_metadata.get("image", None)
            if image_uri is not None:
                nft = IPFSHash(image_uri.replace("ipfs://", ""))

        # NFTs are required for minting components on a local chain deployement
        if self.chain_type == ChainType.LOCAL and nft is None:
            nft = IPFSHash(DEFAULT_NFT_IMAGE_HASH)

        if self.chain_type != ChainType.LOCAL and nft is None:
            raise click.ClickException(
                f"Please provide hash for NFT image to mint component on `{self.chain_type.value}` chain"
            )

        self.nft = nft
        return self

    def verify_component_dependencies(
        self,
        dependencies: Tuple[str],
        skip_dependencies_check: bool = False,
        skip_hash_check: bool = False,
    ) -> "MintHelper":
        """Verify component dependencies."""
        self.dependencies = list(map(int, dependencies))
        if skip_dependencies_check:
            return self
        if self.chain_type != ChainType.ETHEREUM:
            return self
        try:
            verify_component_dependencies(
                ledger_api=self.ledger_api,
                contract_address=ContractConfigs.get(
                    COMPONENT_REGISTRY_CONTRACT.name
                ).contracts[self.chain_type],
                dependencies=self.dependencies,
                package_configuration=self.package_configuration,
                skip_hash_check=skip_hash_check,
            )
            return self
        except (FailedToRetrieveComponentMetadata, DependencyError) as e:
            raise click.ClickException(f"Dependency verification failed; {e}") from e

    def verify_service_dependencies(
        self,
        agent_id: int,
        skip_dependencies_check: bool = False,
        skip_hash_check: bool = False,
    ) -> "MintHelper":
        """Verify component dependencies."""
        self.agent_id = agent_id
        if skip_dependencies_check:
            return self
        if self.chain_type != ChainType.ETHEREUM:
            return self
        try:
            verify_service_dependencies(
                ledger_api=self.ledger_api,
                contract_address=ContractConfigs.get(
                    AGENT_REGISTRY_CONTRACT.name
                ).contracts[self.chain_type],
                agent_id=self.agent_id,
                service_configuration=cast(Service, self.package_configuration),
                skip_hash_check=skip_hash_check,
            )
            return self
        except FailedToRetrieveComponentMetadata as e:
            raise click.ClickException(f"Dependency verification failed; {e}") from e
        except DependencyError as e:
            raise click.ClickException(f"Dependency verification failed; {e}") from e

    def publish_metadata(self) -> "MintHelper":
        """Publish metadata."""
        self.metadata_hash, self.metadata_string = publish_metadata(
            package_id=self.package_configuration.package_id,
            package_path=self.package_path,
            nft=cast(str, self.nft),
            description=self.package_configuration.description,
        )
        return self

    def mint_component(
        self,
        owner: Optional[str] = None,
        component_type: UnitType = UnitType.COMPONENT,
    ) -> None:
        """Mint component."""
        try:
            self.token_id = _mint_component(
                ledger_api=self.ledger_api,
                crypto=self.crypto,
                metadata_hash=self.metadata_hash,
                owner=owner,
                component_type=component_type,
                chain_type=self.chain_type,
                dependencies=self.dependencies,
            )
        except InvalidMintParameter as e:
            raise click.ClickException(f"Invalid parameters provided; {e}") from e
        except ComponentMintFailed as e:
            raise click.ClickException(
                f"Component mint failed with following error; {e}"
            ) from e
        except FailedToRetrieveTokenId as e:
            raise click.ClickException(
                f"Component mint was successful but token ID retrieving failed with following error; {e}"
            ) from e

        click.echo("Component minted with:")
        click.echo(f"\tPublic ID: {self.package_configuration.public_id}")
        click.echo(f"\tMetadata Hash: {self.metadata_hash}")
        if self.token_id is not None:
            click.echo(f"\tToken ID: {self.token_id}")
            (Path.cwd() / f"{self.token_id}.json").write_text(self.metadata_string)
        else:
            raise click.ClickException(
                "Could not verify metadata hash to retrieve the token ID"
            )

    def mint_agent(
        self,
        owner: Optional[str] = None,
    ) -> None:
        """Mint agent."""
        self.mint_component(
            owner=owner,
            component_type=UnitType.AGENT,
        )

    def mint_service(
        self,
        number_of_slots: int,
        cost_of_bond: int,
        threshold: int,
        owner: Optional[str] = None,
    ) -> None:
        """Mint service"""

        try:
            token_id = _mint_service(
                ledger_api=self.ledger_api,
                crypto=self.crypto,
                metadata_hash=self.metadata_hash,
                chain_type=self.chain_type,
                agent_ids=[
                    self.agent_id,
                ],
                number_of_slots_per_agent=[
                    number_of_slots,
                ],
                cost_of_bond_per_agent=[
                    cost_of_bond,
                ],
                threshold=threshold,
                owner=owner,
            )
        except ComponentMintFailed as e:
            raise click.ClickException(
                f"Service mint failed with following error; {e}"
            ) from e
        except FailedToRetrieveTokenId as e:
            raise click.ClickException(
                f"Service mint was successful but token ID retrieving failed with following error; {e}"
            ) from e

        click.echo("Service minted with:")
        click.echo(f"\tPublic ID: {self.package_configuration.public_id}")
        click.echo(f"\tMetadata Hash: {self.metadata_hash}")
        if token_id is not None:
            click.echo(f"\tToken ID: {token_id}")
            (Path.cwd() / f"{token_id}.json").write_text(self.metadata_string)
        else:
            raise click.ClickException(
                "Could not verify metadata hash to retrieve the token ID"
            )

    def update_component(self, component_type: UnitType = UnitType.COMPONENT) -> None:
        """Update component."""
        try:
            self.token_id = _update_component(
                ledger_api=self.ledger_api,
                crypto=self.crypto,
                unit_id=cast(int, self.update_token),
                metadata_hash=self.metadata_hash,
                component_type=component_type,
                chain_type=self.chain_type,
            )
        except InvalidMintParameter as e:
            raise click.ClickException(f"Invalid parameters provided; {e}") from e
        except ComponentMintFailed as e:
            raise click.ClickException(
                f"Component mint failed with following error; {e}"
            ) from e
        except FailedToRetrieveTokenId as e:
            raise click.ClickException(
                f"Component mint was successful but token ID retrieving failed with following error; {e}"
            ) from e

        click.echo("Component hash updated:")
        click.echo(f"\tPublic ID: {self.package_configuration.public_id}")
        click.echo(f"\tMetadata Hash: {self.metadata_hash}")
        if self.token_id is not None:
            click.echo(f"\tToken ID: {self.token_id}")
            (Path.cwd() / f"{self.token_id}.json").write_text(self.metadata_string)
        else:
            raise click.ClickException(
                "Could not verify metadata hash to retrieve the token ID"
            )

    def update_agent(self) -> None:
        """Update agent."""
        self.update_component(component_type=UnitType.AGENT)

    def update_service(
        self,
        number_of_slots: int,
        cost_of_bond: int,
        threshold: int,
    ) -> None:
        """Update service"""

        try:
            token_id = _update_service(
                ledger_api=self.ledger_api,
                crypto=self.crypto,
                metadata_hash=self.metadata_hash,
                service_id=cast(int, self.update_token),
                chain_type=self.chain_type,
                agent_ids=[
                    self.agent_id,
                ],
                number_of_slots_per_agent=[
                    number_of_slots,
                ],
                cost_of_bond_per_agent=[
                    cost_of_bond,
                ],
                threshold=threshold,
            )
        except ComponentMintFailed as e:
            raise click.ClickException(
                f"Service mint failed with following error; {e}"
            ) from e
        except FailedToRetrieveTokenId as e:
            raise click.ClickException(
                f"Service mint was successful but token ID retrieving failed with following error; {e}"
            ) from e

        click.echo("Service updated with:")
        click.echo(f"\tPublic ID: {self.package_configuration.public_id}")
        click.echo(f"\tMetadata Hash: {self.metadata_hash}")
        if token_id is not None:
            click.echo(f"\tToken ID: {token_id}")
            (Path.cwd() / f"{token_id}.json").write_text(self.metadata_string)
        else:
            raise click.ClickException(
                "Could not verify metadata hash to retrieve the token ID"
            )
