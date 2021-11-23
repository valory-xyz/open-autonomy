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

"""Test the payloads.py module of the skill."""
import pandas as pd

from packages.valory.skills.apy_estimation.payloads import (
    TransactionType,
    FetchingPayload,
    TransformationPayload,
    ResetPayload,
)


class TestTransactionType:
    def test__str__(self):
        for transaction_type in TransactionType:
            assert transaction_type.value == str(transaction_type)


class TestPayloads:
    @staticmethod
    def test_fetching_payload() -> None:
        """Test `FetchingPayload`"""
        payload = FetchingPayload(sender="sender", history_hash='x0', id_="id")

        assert payload.transaction_type == TransactionType.FETCHING
        assert payload.history == "x0"
        assert payload.id_ == "id"
        assert payload.data == {"history": "x0"}

    @staticmethod
    def test_transformation_payload(transformation) -> None:
        """Test `TransformationPayload`"""
        payload = TransformationPayload(sender="sender", transformation=transformation, id_="id")

        assert payload.transaction_type == TransactionType.TRANSFORMATION
        pd.testing.assert_frame_equal(payload.transformation, transformation)
        assert payload.id_ == "id"
        pd.testing.assert_frame_equal(payload.data['transformation'], transformation)

    @staticmethod
    def test_reset_payload() -> None:
        """Test `ResetPayload`"""
        payload = ResetPayload(sender="sender", period_count=0, id_="id")

        assert payload.transaction_type == TransactionType.RESET
        assert payload.period_count == 0
        assert payload.id_ == "id"
        assert payload.data == {"period_count": 0}
