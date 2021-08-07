# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This module contains the behaviours for the 'abci' skill."""
from typing import Any, cast

from aea.skills.behaviours import FSMBehaviour, State
from aea_ledger_ethereum import EthereumCrypto

from packages.fetchai.protocols.signing import SigningMessage
from packages.fetchai.protocols.signing.custom_types import RawMessage, Terms
from packages.valory.skills.price_estimation_abci.behaviours_utils import (
    AsyncBehaviour,
    WaitForConditionBehaviour,
)
from packages.valory.skills.price_estimation_abci.dialogues import SigningDialogues
from packages.valory.skills.price_estimation_abci.models import (
    RegistrationPayload,
    Transaction,
)
from packages.valory.skills.price_estimation_abci.tendermint_rpc import (
    _send_broadcast_tx_commit,
)


class PriceEstimationConsensusBehaviour(FSMBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    def setup(self) -> None:
        """Set up the behaviour."""
        self.register_state(
            "wait_tendermint",
            WaitForConditionBehaviour(
                condition=self.wait_tendermint_rpc,
                event="done",
                name="wait_tendermint",
                skill_context=self.context,
            ),
            initial=True,
        )
        self.register_state(
            "register",
            RegistrationBehaviour(name="register", skill_context=self.context),
        )

        self.register_transition("wait_tendermint", "register", "done")

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def wait_tendermint_rpc(self) -> bool:
        """Wait Tendermint RPC server is up."""
        return self.context.state.info_received


class RegistrationBehaviour(AsyncBehaviour, State):
    """Register to the next round."""

    is_programmatically_defined = True

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the behaviour."""
        AsyncBehaviour.__init__(self)
        State.__init__(self, **kwargs)
        self._is_done: bool = False

    def is_done(self) -> bool:
        """Check whether the state is done."""
        return self._is_done

    def async_act(self) -> None:
        """
        Do the action.

        Send a registration transaction to the 'price-estimation' app.
        """
        payload = RegistrationPayload()
        self._send_signing_request(payload.encode())
        signature = yield from self.wait_for_message()
        if signature is None:
            self.handle_signing_failure()
            return
        signature_bytes = signature.body[2:].encode()  # remove leading 0x
        transaction = Transaction(payload, signature_bytes)
        _send_broadcast_tx_commit(self.context, transaction.encode())
        self._is_done = True

    def handle_signing_failure(self):
        """Handle signing failure."""
        self.context.logger.error("the transaction could not be signed.")

    def _send_signing_request(self, raw_message: bytes):
        """Send a signing request."""
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            raw_message=RawMessage(EthereumCrypto.identifier, raw_message),
            terms=Terms(
                ledger_id=EthereumCrypto.identifier,
                sender_address="",
                counterparty_address="",
                amount_by_currency_id={},
                quantities_by_good_id={},
                nonce="",
            ),
        )
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
