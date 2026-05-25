# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2026 Valory AG
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

"""Test utils."""

import json
import urllib.error
import urllib.request
from json import JSONDecodeError
from typing import Dict
from unittest import mock

import pytest
from aea.configurations.data_types import PublicId
from aea.helpers.http_requests import ConnectionError as AeaHttpConnectionError

from autonomy.chain.exceptions import DependencyError, FailedToRetrieveComponentMetadata
from autonomy.chain.utils import (
    get_ipfs_hash_from_uri,
    is_service_manager_token_compatible_chain,
    parse_public_id_from_metadata,
    resolve_component_id,
)

AUTONOLAS_REGISTRIES_CONFIG_URL = (
    "https://raw.githubusercontent.com/valory-xyz/autonolas-registries/"
    "main/docs/configuration.json"
)


def get_dummy_metadata(
    name: str = "valory/package",
    description: str = "description",
    code_uri: str = "code_uri",
    nft_hash: str = "nft_hash",
    version: str = "0.1.0",
) -> Dict:
    """Get dummy metadata."""

    return {
        "name": name,
        "description": description,
        "code_uri": code_uri,
        "image": nft_hash,
        "attributes": [{"trait_type": "version", "value": version}],
    }


def test_get_ipfs_hash_from_uri() -> None:
    """Test `get_ipfs_hash_from_uri` method"""

    assert get_ipfs_hash_from_uri("ipfs://SOME_HASH") == "SOME_HASH"


@pytest.mark.parametrize(
    "public_id_string",
    [
        "author/package_name",
        "component_type/author/name",
        "skill/author/name/0.1.0",
    ],
)
def test_parse_public_id_from_metadata(public_id_string: str) -> None:
    """Test verify `parse_public_id_from_metadata` method"""

    public_id = parse_public_id_from_metadata(
        id_string=public_id_string,
    )

    assert isinstance(public_id, PublicId)


def test_parse_public_id_from_metadata_fail() -> None:
    """Test verify `parse_public_id_from_metadata` method"""

    with pytest.raises(DependencyError, match="Invalid package name found `public_id`"):
        parse_public_id_from_metadata(
            id_string="public_id",
        )


def test_parse_public_id_from_metadata_strips_token_suffix() -> None:
    """`parse_public_id_from_metadata` strips a trailing `:token_id` suffix."""

    public_id = parse_public_id_from_metadata(id_string="author/name:123")
    assert isinstance(public_id, PublicId)
    assert public_id.author == "author"
    assert public_id.name == "name"


@pytest.mark.parametrize(
    "kind, contracts_attr",
    [
        ({"is_service": True}, "service_registry"),
        ({"is_agent": True}, "agent_registry"),
        ({}, "component_registry"),
    ],
)
def test_resolve_component_id_dispatches_to_right_registry(
    kind: Dict, contracts_attr: str
) -> None:
    """`resolve_component_id` selects the registry based on is_service/is_agent."""

    ledger_api = mock.Mock()
    fake_registry = mock.Mock()
    fake_registry.get_token_uri.return_value = "ipfs://FakeURI"

    with mock.patch(
        "autonomy.chain.utils.registry_contracts", **{contracts_attr: fake_registry}
    ), mock.patch("autonomy.chain.utils.r_get") as r_get:
        r_get.return_value.json.return_value = {"ok": True}
        out = resolve_component_id(
            ledger_api=ledger_api,
            contract_address="0xabc",
            token_id=1,
            **kind,
        )

    assert out == {"ok": True}
    fake_registry.get_token_uri.assert_called_once()


def test_resolve_component_id_rpc_connection_error() -> None:
    """RPC-side ConnectionError maps to FailedToRetrieveComponentMetadata."""

    from autonomy.chain.utils import get_requests_connection_error

    with mock.patch("autonomy.chain.utils.registry_contracts") as rc:
        rc.component_registry.get_token_uri.side_effect = (
            get_requests_connection_error()("boom")
        )
        with pytest.raises(FailedToRetrieveComponentMetadata, match="Error connecting"):
            resolve_component_id(
                ledger_api=mock.Mock(),
                contract_address="0xabc",
                token_id=1,
            )


def test_resolve_component_id_ipfs_connection_error() -> None:
    """IPFS-side ConnectionError maps to FailedToRetrieveComponentMetadata."""

    with mock.patch("autonomy.chain.utils.registry_contracts") as rc, mock.patch(
        "autonomy.chain.utils.r_get"
    ) as r_get:
        rc.component_registry.get_token_uri.return_value = "ipfs://hash"
        r_get.side_effect = AeaHttpConnectionError("boom")
        with pytest.raises(
            FailedToRetrieveComponentMetadata, match="Error connecting to the IPFS"
        ):
            resolve_component_id(
                ledger_api=mock.Mock(),
                contract_address="0xabc",
                token_id=1,
            )


def test_resolve_component_id_ipfs_json_decode_error() -> None:
    """Test JSONDecodeError on IPFS response maps to FailedToRetrieveComponentMetadata."""

    with mock.patch("autonomy.chain.utils.registry_contracts") as rc, mock.patch(
        "autonomy.chain.utils.r_get"
    ) as r_get:
        rc.component_registry.get_token_uri.return_value = "ipfs://hash"
        r_get.return_value.json.side_effect = JSONDecodeError("bad", "doc", 0)
        with pytest.raises(
            FailedToRetrieveComponentMetadata, match="Error decoding json"
        ):
            resolve_component_id(
                ledger_api=mock.Mock(),
                contract_address="0xabc",
                token_id=42,
            )


def test_is_service_manager_token_compatible_chain() -> None:
    """Chain-id lookup against the known-compatible set."""

    from autonomy.chain.constants import SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS

    ledger_api = mock.Mock()
    ledger_api.api.eth.chain_id = SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS[0]
    assert is_service_manager_token_compatible_chain(ledger_api) is True

    ledger_api.api.eth.chain_id = -1
    assert is_service_manager_token_compatible_chain(ledger_api) is False


@pytest.mark.integration
def test_compatible_chains_covers_autonolas_registries_deployments() -> None:
    """Drift-check the constant against `autonolas-registries`.

    Every chain Olas has deployed `ServiceRegistryTokenUtility` to must
    appear in `SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS`. Source of truth is
    `autonolas-registries/docs/configuration.json` on `main`. Fetched live
    so a new mainnet deployment fails this test loudly instead of silently
    drifting.
    """

    from autonomy.chain.constants import SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS

    try:
        with urllib.request.urlopen(  # nosec — fixed valory-xyz URL
            AUTONOLAS_REGISTRIES_CONFIG_URL, timeout=30
        ) as response:
            raw = response.read()
        config = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, JSONDecodeError) as exc:
        pytest.skip(
            f"Could not fetch {AUTONOLAS_REGISTRIES_CONFIG_URL}: {exc}. "
            "Run with `-m 'not integration'` to skip this check offline."
        )

    upstream_chains = {
        int(chain["chainId"]): chain["name"]
        for chain in config
        if any(
            contract.get("name") == "ServiceRegistryTokenUtility"
            for contract in chain.get("contracts", [])
        )
    }
    assert upstream_chains, (
        "autonolas-registries configuration.json returned zero chains with "
        "`ServiceRegistryTokenUtility` — schema may have changed."
    )

    missing = {
        chain_id: name
        for chain_id, name in upstream_chains.items()
        if chain_id not in SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS
    }
    assert not missing, (
        "Olas has `ServiceRegistryTokenUtility` deployed on chains that are "
        "not in `SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS`. Add them to BOTH "
        "`autonomy/chain/constants.py` and "
        "`packages/valory/contracts/service_manager/contract.py` (the test "
        "below enforces parity), then re-lock packages: "
        f"{missing}. Source: {AUTONOLAS_REGISTRIES_CONFIG_URL}"
    )


def test_compatible_chains_match_across_autonomy_and_package() -> None:
    """Enforce parity of the two copies of the chain-compatibility tuple.

    `SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS` is duplicated in
    `autonomy/chain/constants.py` and
    `packages/valory/contracts/service_manager/contract.py` because the
    contract package cannot import from the framework. A chain added to
    one but not the other would silently drift, which is the regression
    that opened #2254.
    """

    from autonomy.chain.constants import (
        SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS as AUTONOMY_CHAINS,
    )

    from packages.valory.contracts.service_manager.contract import (
        SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS as PACKAGE_CHAINS,
    )

    assert set(AUTONOMY_CHAINS) == set(PACKAGE_CHAINS), (
        "`SERVICE_MANAGER_TOKEN_COMPATIBLE_CHAINS` diverges between "
        "`autonomy/chain/constants.py` and "
        "`packages/valory/contracts/service_manager/contract.py`. "
        f"autonomy-only: {sorted(set(AUTONOMY_CHAINS) - set(PACKAGE_CHAINS))}; "
        f"package-only: {sorted(set(PACKAGE_CHAINS) - set(AUTONOMY_CHAINS))}."
    )
