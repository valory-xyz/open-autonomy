# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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

import binascii
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, cast

import click
from aea.configurations.base import PackageConfiguration
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.configurations.loader import load_configuration_object
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea.helpers.base import IPFSHash
from requests.exceptions import ConnectionError as RequestConnectionError
from texttable import Texttable

from autonomy.chain.base import ServiceState, UnitType
from autonomy.chain.config import (
    ChainConfigs,
    ChainType,
    ContractConfig,
    ContractConfigs,
)
from autonomy.chain.constants import (
    AGENT_REGISTRY_CONTRACT,
    COMPONENT_REGISTRY_CONTRACT,
    SERVICE_REGISTRY_CONTRACT,
    SERVICE_REGISTRY_TOKEN_UTILITY_CONTRACT,
)
from autonomy.chain.exceptions import ChainInteractionError
from autonomy.chain.metadata import NFTHashOrPath, publish_metadata
from autonomy.chain.mint import DEFAULT_NFT_IMAGE_HASH, MintManager
from autonomy.chain.service import (
    ServiceManager,
    approve_erc20_usage,
    get_activate_registration_amount,
    get_agent_instances,
    get_service_info,
    get_token_deposit_amount,
    is_service_token_secured,
)
from autonomy.chain.subgraph.client import SubgraphClient
from autonomy.chain.utils import (
    is_service_manager_token_compatible_chain,
    resolve_component_id,
)
from autonomy.configurations.base import PACKAGE_TYPE_TO_CONFIG_CLASS, Service


try:
    from aea_ledger_ethereum.ethereum import EthereumApi, EthereumCrypto

    ETHEREUM_PLUGIN_INSTALLED = True
except ImportError:  # pragma: nocover
    ETHEREUM_PLUGIN_INSTALLED = False


class OnChainHelper:  # pylint: disable=too-few-public-methods
    """On-chain interaction helper."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        sleep: Optional[float] = None,
        dry_run: bool = False,
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
        self.timeout = timeout
        self.retries = retries
        self.sleep = sleep
        self.dry_run = dry_run

    @staticmethod
    def load_hwi_plugin() -> Type[LedgerApi]:  # pragma: nocover
        """Load HWI Plugin."""
        try:
            from aea_ledger_ethereum_hwi.hwi import (  # pylint: disable=import-outside-toplevel
                EthereumHWIApi,
            )

            return EthereumHWIApi
        except ImportError as e:
            raise click.ClickException(
                "Hardware wallet plugin not installed, "
                "Run `pip3 install open-aea-ledger-ethereum-hwi` to install the plugin"
            ) from e
        except TypeError as e:
            raise click.ClickException(
                'Protobuf compatibility error; Please export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="python" '
                "to use the hardware wallet without any issues"
            ) from e

    @staticmethod
    def load_crypto(
        file: Path,
        password: Optional[str] = None,
    ) -> Crypto:
        """Load crypto object."""
        try:
            return EthereumCrypto(
                private_key_path=file,
                password=password,
            )
        except (binascii.Error, ValueError) as e:
            raise click.ClickException(
                "Cannot load private key for following possible reasons\n"
                "- Wrong key format\n"
                "- Wrong key length\n"
                "- Trailing spaces or new line characters"
            ) from e

    @classmethod
    def get_ledger_and_crypto_objects(
        cls,
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

        if hwi:
            EthereumHWIApi = cls.load_hwi_plugin()
            identifier = EthereumHWIApi.identifier

        if not hwi and not ETHEREUM_PLUGIN_INSTALLED:  # pragma: nocover
            raise click.ClickException(
                "Ethereum ledger plugin not installed, "
                "Run `pip3 install open-aea-ledger-ethereum` to install the plugin"
            )

        if key is None:
            crypto = crypto_registry.make(identifier)
        else:
            crypto = cls.load_crypto(
                file=key,
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
        except Exception as e:  # pragma: nocover
            raise click.ClickException(str(e))

        return ledger_api, crypto

    def check_required_enviroment_variables(
        self, configs: Tuple[ContractConfig, ...]
    ) -> None:
        """Check for required enviroment variables when working with the custom chain."""
        if self.chain_type != ChainType.CUSTOM:
            return
        missing = []
        for config in configs:
            if config.contracts[self.chain_type] is None:
                missing.append(config)

        if len(missing) == 0:
            return

        error = "Addresses for following contracts are None, please set them using their respective environment variables\n"
        for config in missing:
            error += f"- Set `{config.name}` address using `CUSTOM_{config.name.upper()}_ADDRESS`\n"
        raise click.ClickException(error[:-1])


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

    def __init__(  # pylint: disable=too-many-arguments
        self,
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False,
        update_token: Optional[int] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        sleep: Optional[float] = None,
        subgraph: Optional[str] = None,
        dry_run: bool = False,
    ) -> None:
        """Initialize object."""
        super().__init__(
            chain_type,
            key,
            password,
            hwi,
            timeout=timeout,
            retries=retries,
            sleep=sleep,
            dry_run=dry_run,
        )
        self.update_token = update_token
        self.manager = MintManager(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=chain_type,
            timeout=timeout,
            retries=retries,
            sleep=sleep,
            dry_run=self.dry_run,
        )
        self.subgraph = SubgraphClient(url=subgraph)

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

    def load_metadata(self) -> "MintHelper":  # pragma: nocover
        """Load metadata when updating a mint."""
        if self.update_token is None:
            return self

        if self.package_type == PackageType.SERVICE:
            is_service = True
            is_agent = False
            contract_address = ContractConfigs.get(
                SERVICE_REGISTRY_CONTRACT.name
            ).contracts[self.chain_type]
            self.check_required_enviroment_variables(
                configs=(ContractConfigs.service_registry,)
            )
        elif self.package_type == PackageType.AGENT:
            is_service = False
            is_agent = True
            contract_address = ContractConfigs.get(
                AGENT_REGISTRY_CONTRACT.name
            ).contracts[self.chain_type]
            self.check_required_enviroment_variables(
                configs=(ContractConfigs.agent_registry,)
            )
        else:
            is_service = False
            is_agent = False
            contract_address = ContractConfigs.get(
                COMPONENT_REGISTRY_CONTRACT.name
            ).contracts[self.chain_type]
            self.check_required_enviroment_variables(
                configs=(ContractConfigs.component_registry,)
            )

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

    def fetch_component_dependencies(self) -> "MintHelper":
        """Verify component dependencies."""
        if self.chain_type != ChainType.ETHEREUM:
            self.dependencies = []
            return self

        dependencies = []
        try:
            for ptype in PackageType:
                if not hasattr(self.package_configuration, ptype.to_plural()):
                    continue
                for dependency in getattr(
                    self.package_configuration, ptype.to_plural()
                ):
                    units = self.subgraph.get_record_by_package_id(
                        package_id=PackageId(package_type=ptype, public_id=dependency)
                    ).get("units", [])
                    if len(units) == 0:
                        raise click.ClickException(
                            f"Could not find on-chain token for {dependency} of type {ptype}"
                        )
                    unit, *_ = sorted(units, key=lambda x: x["tokenId"])
                    dependencies.append(unit["tokenId"])
            self.dependencies = sorted(list(map(int, dependencies)))
        except RequestConnectionError as e:
            raise click.ClickException(message=f"Error interacting with subgraph; {e}")
        return self

    def verify_service_dependencies(self, agent_id: int) -> "MintHelper":
        """Verify component dependencies."""
        self.agent_id = agent_id
        if self.chain_type in (ChainType.LOCAL, ChainType.GOERLI):
            return self

        try:
            units = self.subgraph.get_component_by_token(
                token_id=agent_id,
                package_type=PackageType.AGENT,
            ).get("units", [])
        except RequestConnectionError as e:
            raise click.ClickException(message=f"Error interacting with subgraph; {e}")
        if len(units) == 0:
            raise click.ClickException(f"No agents found with token ID {agent_id}")

        unit, *_ = sorted(units, key=lambda x: x["tokenId"])
        expected = PublicId.from_str(unit["publicId"]).to_any()
        agent = cast(Service, self.package_configuration).agent.to_any()
        if expected != agent:
            raise click.ClickException(
                f"Public ID `{expected}` for token {agent_id} does not match with the one "
                f"defained in the service package `{agent}`"
            )
        return self

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

        self.check_required_enviroment_variables(
            configs=(
                ContractConfigs.registries_manager,
                (
                    ContractConfigs.component_registry
                    if component_type == UnitType.COMPONENT
                    else ContractConfigs.agent_registry
                ),
            )
        )

        try:
            self.token_id = self.manager.mint_component(
                metadata_hash=self.metadata_hash,
                component_type=component_type,
                owner=owner,
                dependencies=self.dependencies,
            )
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(
                f"Component mint failed with following error; {e.__class__.__name__}({e})"
            ) from e

        if self.dry_run:  # pragma: nocover
            return

        click.echo("Component minted with:")
        click.echo(f"\tPublic ID: {self.package_configuration.public_id}")
        click.echo(f"\tMetadata Hash: {self.metadata_hash}")
        if self.token_id is not None:
            click.echo(f"\tToken ID: {self.token_id}")
            (Path.cwd() / f"{self.token_id}.json").write_text(self.metadata_string)
        else:  # pragma: nocover
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
        threshold: Optional[int] = None,
        token: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> None:
        """Mint service"""

        if (
            not is_service_manager_token_compatible_chain(ledger_api=self.ledger_api)
            and token is not None
        ):
            raise click.ClickException(
                "Cannot use custom token for bonding on L2 chains"
            )

        self.check_required_enviroment_variables(
            configs=(
                ContractConfigs.service_manager,
                ContractConfigs.service_registry,
            )
        )

        try:
            token_id = self.manager.mint_service(
                metadata_hash=self.metadata_hash,
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
                token=token,
                owner=owner,
            )
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(
                f"Component mint failed with following error; {e.__class__.__name__}({e})"
            ) from e

        if self.dry_run:  # pragma: nocover
            return

        click.echo("Service minted with:")
        click.echo(f"\tPublic ID: {self.package_configuration.public_id}")
        click.echo(f"\tMetadata Hash: {self.metadata_hash}")
        if token_id is not None:
            click.echo(f"\tToken ID: {token_id}")
            (Path.cwd() / f"{token_id}.json").write_text(self.metadata_string)
        else:  # pragma: nocover
            raise click.ClickException(
                "Could not verify metadata hash to retrieve the token ID"
            )

    def update_component(self, component_type: UnitType = UnitType.COMPONENT) -> None:
        """Update component."""
        self.check_required_enviroment_variables(
            configs=(
                ContractConfigs.registries_manager,
                (
                    ContractConfigs.component_registry
                    if component_type == UnitType.COMPONENT
                    else ContractConfigs.agent_registry
                ),
            )
        )
        try:
            self.token_id = self.manager.update_component(
                metadata_hash=self.metadata_hash,
                unit_id=cast(int, self.update_token),
                component_type=component_type,
            )
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(
                f"Component update failed with following error; {e.__class__.__name__}({e})"
            ) from e

        if self.dry_run:  # pragma: nocover
            return

        click.echo("Component hash updated:")
        click.echo(f"\tPublic ID: {self.package_configuration.public_id}")
        click.echo(f"\tMetadata Hash: {self.metadata_hash}")
        if self.token_id is not None:
            click.echo(f"\tToken ID: {self.token_id}")
            (Path.cwd() / f"{self.token_id}.json").write_text(self.metadata_string)
        else:  # pragma: nocover
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
        threshold: Optional[int] = None,
        token: Optional[str] = None,
    ) -> None:
        """Update service"""

        self.check_required_enviroment_variables(
            configs=(
                ContractConfigs.service_manager,
                ContractConfigs.service_registry,
            )
        )

        *_, state, _ = get_service_info(
            ledger_api=self.ledger_api,
            chain_type=self.chain_type,
            token_id=cast(int, self.update_token),
        )

        if ServiceState(state) != ServiceState.PRE_REGISTRATION:
            raise click.ClickException(
                "Cannot update service hash, service needs to be in the pre-registration state"
            )

        try:
            token_id = self.manager.update_service(
                metadata_hash=self.metadata_hash,
                service_id=cast(int, self.update_token),
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
                token=token,
            )
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(
                f"Component mint failed with following error; {e.__class__.__name__}({e})"
            ) from e

        if self.dry_run:  # pragma: nocover
            return

        click.echo("Service updated with:")
        click.echo(f"\tPublic ID: {self.package_configuration.public_id}")
        click.echo(f"\tMetadata Hash: {self.metadata_hash}")
        if token_id is not None:
            click.echo(f"\tToken ID: {token_id}")
            (Path.cwd() / f"{token_id}.json").write_text(self.metadata_string)
        else:  # pragma: nocover
            raise click.ClickException(
                "Could not verify metadata hash to retrieve the token ID"
            )


class ServiceHelper(OnChainHelper):
    """Service helper."""

    token: Optional[str]
    token_secured: bool

    def __init__(  # pylint: disable=too-many-arguments
        self,
        service_id: int,
        chain_type: ChainType,
        key: Optional[Path] = None,
        password: Optional[str] = None,
        hwi: bool = False,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        sleep: Optional[float] = None,
        dry_run: bool = False,
    ) -> None:
        """Initialize object."""
        self.service_id = service_id
        super().__init__(
            chain_type,
            key,
            password,
            hwi,
            timeout=timeout,
            retries=retries,
            sleep=sleep,
            dry_run=dry_run,
        )
        self.manager = ServiceManager(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            timeout=self.timeout,
            retries=self.retries,
            sleep=self.sleep,
            dry_run=dry_run,
        )

    def check_is_service_token_secured(
        self,
        token: Optional[str] = None,
    ) -> "ServiceHelper":
        """Check if service"""
        if not is_service_manager_token_compatible_chain(ledger_api=self.ledger_api):
            self.token = token
            self.token_secured = False
            return self

        if self.chain_type == ChainType.CUSTOM:  # pragma: nocover
            self.check_required_enviroment_variables(
                configs=(ContractConfigs.service_registry_token_utility,)
            )

        self.token = token
        self.token_secured = is_service_token_secured(
            ledger_api=self.ledger_api,
            chain_type=self.chain_type,
            service_id=self.service_id,
        )
        if self.token_secured and self.token is None:
            raise click.ClickException(
                "Service is token secured, please provice token address using `--token` flag"
            )
        ContractConfigs.erc20.contracts[self.chain_type] = cast(str, self.token)
        return self

    def approve_erc20_usage(self, amount: int, spender: str) -> "ServiceHelper":
        """Approve ERC20 usage."""

        try:
            approve_erc20_usage(
                ledger_api=self.ledger_api,
                crypto=self.crypto,
                chain_type=self.chain_type,
                spender=spender,
                amount=amount,
                sender=self.crypto.address,
                dry_run=self.dry_run,
                timeout=self.timeout,
                sleep=self.sleep,
                retries=self.retries,
            )
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(f"Error getting approval : {e}")
        return self

    def activate_service(self) -> None:
        """Activate on-chain service"""

        if self.token_secured:
            amount = get_token_deposit_amount(
                self.ledger_api,
                chain_type=self.chain_type,
                service_id=self.service_id,
            )
            spender = ContractConfigs.get(
                name=SERVICE_REGISTRY_TOKEN_UTILITY_CONTRACT.name
            ).contracts[self.chain_type]
            self.approve_erc20_usage(
                amount=amount,
                spender=spender,
            )

        self.check_required_enviroment_variables(
            configs=(
                ContractConfigs.service_manager,
                ContractConfigs.service_registry,
            )
        )

        try:
            self.manager.activate(service_id=self.service_id)
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(
                f"Service activation failed with following error; {e.__class__.__name__}({e})"
            ) from e

        if self.dry_run:  # pragma: nocover
            return
        click.echo("Service activated succesfully")

    def register_instance(self, instances: List[str], agent_ids: List[int]) -> None:
        """Register agents instances on an activated service"""

        if self.token_secured:
            amount = get_activate_registration_amount(
                ledger_api=self.ledger_api,
                chain_type=self.chain_type,
                service_id=self.service_id,
                agents=agent_ids,
            )
            spender = ContractConfigs.get(
                name=SERVICE_REGISTRY_TOKEN_UTILITY_CONTRACT.name
            ).contracts[self.chain_type]
            self.approve_erc20_usage(
                amount=amount,
                spender=spender,
            )

        self.check_required_enviroment_variables(
            configs=(
                ContractConfigs.service_manager,
                ContractConfigs.service_registry,
            )
        )

        try:
            self.manager.register_instance(
                service_id=self.service_id,
                instances=instances,
                agent_ids=agent_ids,
            )
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(
                f"Service activation failed with following error; {e.__class__.__name__}({e})"
            ) from e

        if self.dry_run:  # pragma: nocover
            return
        click.echo("Agent instance registered succesfully")

    def deploy_service(
        self,
        reuse_multisig: bool = False,
        fallback_handler: Optional[str] = None,
    ) -> None:
        """Deploy a service with registration activated"""

        self.check_required_enviroment_variables(
            configs=(
                ContractConfigs.service_manager,
                ContractConfigs.service_registry,
                ContractConfigs.gnosis_safe_proxy_factory,
                ContractConfigs.gnosis_safe_same_address_multisig,
                ContractConfigs.multisend,
            )
        )

        try:
            self.manager.deploy(
                service_id=self.service_id,
                reuse_multisig=reuse_multisig,
                fallback_handler=fallback_handler,
            )
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(
                f"Service deployment failed with following error; {e.__class__.__name__}({e})"
            ) from e

        if self.dry_run:  # pragma: nocover
            return
        click.echo("Service deployed succesfully")

    def terminate_service(self) -> None:
        """Terminate a service"""

        self.check_required_enviroment_variables(
            configs=(
                ContractConfigs.service_manager,
                ContractConfigs.service_registry,
            )
        )

        try:
            self.manager.terminate(service_id=self.service_id)
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(
                f"Service terminatation failed with following error; {e.__class__.__name__}({e})"
            ) from e
        click.echo("Service terminated succesfully")

    def unbond_service(self) -> None:
        """Unbond a service"""

        self.check_required_enviroment_variables(
            configs=(
                ContractConfigs.service_manager,
                ContractConfigs.service_registry,
            )
        )

        try:
            self.manager.unbond(service_id=self.service_id)
        except ChainInteractionError as e:  # pragma: nocover
            raise click.ClickException(
                f"Service unbonding failed with following error; {e.__class__.__name__}({e})"
            ) from e
        click.echo("Service unbonded succesfully")


def print_service_info(service_id: int, chain_type: ChainType) -> None:
    """Print service information"""
    ledger_api, _ = OnChainHelper.get_ledger_and_crypto_objects(chain_type=chain_type)
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
