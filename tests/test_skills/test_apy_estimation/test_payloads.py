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

from packages.valory.skills.apy_estimation.payloads import (
    TransactionType,
    FetchingPayload,
    TransformationPayload,
    ResetPayload,
    PreprocessPayload,
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
    def test_transformation_payload() -> None:
        """Test `TransformationPayload`"""
        payload = TransformationPayload(sender="sender", transformation_hash='x0', id_="id")

        assert payload.transaction_type == TransactionType.TRANSFORMATION
        assert payload.transformation == "x0"
        assert payload.id_ == "id"
        assert payload.data == {"transformation": "x0"}

    @staticmethod
    def test_preprocess_payload() -> None:
        """Test `PreprocessPayload`"""
        payload = PreprocessPayload(sender="sender", train_hash='x0', test_hash='x1', pair_name='test', id_="id")

        assert payload.transaction_type == TransactionType.PREPROCESS
        assert payload.train == "x0"
        assert payload.test == "x1"
        assert payload.pair_name == "test"
        assert payload.id_ == "id"
        assert payload.data == {"train": 'x0', "test": 'x1', "pair_name": 'test'}

    @staticmethod
    def test_reset_payload() -> None:
        """Test `ResetPayload`"""
        payload = ResetPayload(sender="sender", period_count=0, id_="id")

        assert payload.transaction_type == TransactionType.RESET
        assert payload.period_count == 0
        assert payload.id_ == "id"
        assert payload.data == {"period_count": 0}
