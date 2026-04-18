# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2025 Valory AG
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

"""Custom exceptions for chain module."""

from typing import Type


def get_requests_connection_error() -> Type[BaseException]:
    """Return `requests.exceptions.ConnectionError`.

    web3's HTTPProvider uses `requests` internally, and `requests` is
    installed transitively with `open-aea-ledger-ethereum`. Resolved
    lazily so unrelated importers of this module work without the
    plugin; any call that actually reaches a chain-side `except` without
    the plugin raises here with a clear install hint, matching the
    `load_hwi_plugin` pattern in `autonomy.chain.config`.
    """
    try:
        from requests.exceptions import (  # pylint: disable=import-outside-toplevel
            ConnectionError as _RequestsConnectionError,
        )
    except ImportError as e:  # pragma: nocover
        raise ImportError(
            "Chain operations require the Ethereum ledger plugin, "
            "run `pip install open-aea-ledger-ethereum` to install the plugin"
        ) from e
    return _RequestsConnectionError


class ChainInteractionError(Exception):
    """Base chain interaction failure."""


class RPCError(ChainInteractionError):
    """RPC error."""


class TxBuildError(ChainInteractionError):
    """Tx build error."""


class TxSettleError(ChainInteractionError):
    """Tx settle error."""


class TxVerifyError(ChainInteractionError):
    """Tx settle error."""


class ChainTimeoutError(ChainInteractionError):
    """Timeout error for interecting with chain."""


class ComponentMintFailed(ChainInteractionError):
    """Raise when component minting fails."""


class FailedToRetrieveComponentMetadata(ChainInteractionError):
    """Raise when component metadata retrieving fails."""


class DependencyError(ChainInteractionError):
    """Raise when component dependency check fails."""


class InvalidMintParameter(ChainInteractionError):
    """Raise when the parameter provided for minting a component is invalid"""


class ServiceRegistrationFailed(ChainInteractionError):
    """Raise when service activation fails."""


class InstanceRegistrationFailed(ChainInteractionError):
    """Raise when instance registration fails."""


class ServiceDeployFailed(ChainInteractionError):
    """Raise when service activation fails."""


class TerminateServiceFailed(ChainInteractionError):
    """Raise when service termination fails."""


class RecoverServiceMultisigFailed(ChainInteractionError):
    """Raise when service multisig recovery fails."""


class UnbondServiceFailed(ChainInteractionError):
    """Raise when service unbond call fails."""
