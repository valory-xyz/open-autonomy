<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.tests.test`_`payload`_`tools

Tests for valory/transaction settlement skill's payload tools.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools.TestTxHistPayloadEncodingDecoding"></a>

## TestTxHistPayloadEncodingDecoding Objects

```python
class TestTxHistPayloadEncodingDecoding()
```

Tests for the transaction history's payload encoding - decoding.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools.TestTxHistPayloadEncodingDecoding.test_tx_hist_payload_to_hex_and_back"></a>

#### test`_`tx`_`hist`_`payload`_`to`_`hex`_`and`_`back

```python
@staticmethod
@pytest.mark.parametrize(
        "verification_status, tx_hash",
        (
            (
                VerificationStatus.VERIFIED,
                "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
            ),
            (VerificationStatus.ERROR, None),
        ),
    )
def test_tx_hist_payload_to_hex_and_back(verification_status: VerificationStatus, tx_hash: str) -> None
```

Test `tx_hist_payload_to_hex` and `tx_hist_hex_to_payload` functions.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools.TestTxHistPayloadEncodingDecoding.test_invalid_tx_hash_during_serialization"></a>

#### test`_`invalid`_`tx`_`hash`_`during`_`serialization

```python
@staticmethod
def test_invalid_tx_hash_during_serialization() -> None
```

Test encoding when transaction hash is invalid.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools.TestTxHistPayloadEncodingDecoding.test_invalid_payloads_during_deserialization"></a>

#### test`_`invalid`_`payloads`_`during`_`deserialization

```python
@staticmethod
@pytest.mark.parametrize(
        "payload",
        ("0000000000000000000000000000000000000000000000000000000000000007", ""),
    )
def test_invalid_payloads_during_deserialization(payload: str) -> None
```

Test decoding payload is invalid.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools.test_payload_to_hex_and_back"></a>

#### test`_`payload`_`to`_`hex`_`and`_`back

```python
def test_payload_to_hex_and_back() -> None
```

Test `payload_to_hex` function.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools.test_fuzz_tx_hist_payload_to_hex"></a>

#### test`_`fuzz`_`tx`_`hist`_`payload`_`to`_`hex

```python
@pytest.mark.skip
def test_fuzz_tx_hist_payload_to_hex() -> None
```

Test fuzz tx_hist_payload_to_hex.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools.test_fuzz_tx_hist_hex_to_payload"></a>

#### test`_`fuzz`_`tx`_`hist`_`hex`_`to`_`payload

```python
@pytest.mark.skip
def test_fuzz_tx_hist_hex_to_payload() -> None
```

Test fuzz tx_hist_hex_to_payload.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools.test_fuzz_hash_payload_to_hex"></a>

#### test`_`fuzz`_`hash`_`payload`_`to`_`hex

```python
@pytest.mark.skip
def test_fuzz_hash_payload_to_hex() -> None
```

Test fuzz hash_payload_to_hex.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payload_tools.test_fuzz_skill_input_hex_to_payload"></a>

#### test`_`fuzz`_`skill`_`input`_`hex`_`to`_`payload

```python
@pytest.mark.skip
def test_fuzz_skill_input_hex_to_payload() -> None
```

Test fuzz skill_input_hex_to_payload.

