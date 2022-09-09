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

"""Test the utils.py module of the skill."""
import sys
from unittest import mock

import pytest


try:
    import atheris  # type: ignore
except (ImportError, ModuleNotFoundError):
    pytestmark = pytest.mark.skip

from packages.valory.skills.abstract_round_abci.utils import MAX_UINT64, VerifyDrand


DRAND_PUBLIC_KEY: str = "868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c529eeda66c7293784a9402801af31"

DRAND_VALUE = {
    "round": 1416669,
    "randomness": "f6be4bf1fa229f22340c1a5b258f809ac4af558200775a67dacb05f0cb258a11",
    "signature": (
        "b44d00516f46da3a503f9559a634869b6dc2e5d839e46ec61a090e3032172954929a5"
        "d9bd7197d7739fe55db770543c71182562bd0ad20922eb4fe6b8a1062ed21df3b68de"
        "44694eb4f20b35262fa9d63aa80ad3f6172dd4d33a663f21179604"
    ),
    "previous_signature": (
        "903c60a4b937a804001032499a855025573040cb86017c38e2b1c3725286756ce8f33"
        "61188789c17336beaf3f9dbf84b0ad3c86add187987a9a0685bc5a303e37b008fba8c"
        "44f02a416480dd117a3ff8b8075b1b7362c58af195573623187463"
    ),
}


class TestVerifyDrand:
    """Test DrandVerify."""

    drand_check: VerifyDrand

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.drand_check = VerifyDrand()

    def test_verify(
        self,
    ) -> None:
        """Test verify method."""

        result, error = self.drand_check.verify(DRAND_VALUE, DRAND_PUBLIC_KEY)
        assert result
        assert error is None

    def test_verify_fails(
        self,
    ) -> None:
        """Test verify method."""

        drand_value = DRAND_VALUE.copy()
        del drand_value["randomness"]
        result, error = self.drand_check.verify(drand_value, DRAND_PUBLIC_KEY)
        assert not result
        assert error == "DRAND dict is missing value for 'randomness'"

        drand_value = DRAND_VALUE.copy()
        drand_value["randomness"] = "".join(
            list(drand_value["randomness"])[:-1] + ["0"]  # type: ignore
        )
        result, error = self.drand_check.verify(drand_value, DRAND_PUBLIC_KEY)
        assert not result
        assert error == "Failed randomness hash check."

        drand_value = DRAND_VALUE.copy()
        with mock.patch.object(
            self.drand_check, "_verify_signature", return_value=False
        ):
            result, error = self.drand_check.verify(drand_value, DRAND_PUBLIC_KEY)

        assert not result
        assert error == "Failed bls.Verify check."

    @pytest.mark.parametrize("value", (-1, MAX_UINT64 + 1))
    def test_negative_and_overflow(self, value: int) -> None:
        """Test verify method."""
        with pytest.raises(ValueError):
            self.drand_check._int_to_bytes_big(value)


@pytest.mark.skip
def test_fuzz_verify_drand() -> None:
    """Fuzz test for VerifyDrand. Run directly as a function, not through pytest"""

    @atheris.instrument_func
    def test_verify_int_to_bytes_big(input_bytes: bytes) -> None:
        """Test VerifyDrand."""
        fdp = atheris.FuzzedDataProvider(input_bytes)
        VerifyDrand._int_to_bytes_big(
            fdp.ConsumeInt(16)
        )  # pylint: disable=protected-access

    @atheris.instrument_func
    def test_verify_randomness_hash(input_bytes: bytes) -> None:
        """Test VerifyDrand."""
        fdp = atheris.FuzzedDataProvider(input_bytes)
        VerifyDrand._verify_randomness_hash(
            fdp.ConsumeBytes(16), fdp.ConsumeBytes(16)
        )  # pylint: disable=protected-access

    atheris.instrument_all()
    atheris.Setup(sys.argv, test_verify_int_to_bytes_big)
    atheris.Fuzz()
