<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payloads"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.tests.test`_`payloads

Test the payloads of the skill.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payloads.test_randomness_payload"></a>

#### test`_`randomness`_`payload

```python
def test_randomness_payload() -> None
```

Test `RandomnessPayload`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payloads.test_select_keeper_payload"></a>

#### test`_`select`_`keeper`_`payload

```python
def test_select_keeper_payload() -> None
```

Test `SelectKeeperPayload`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payloads.test_validate_payload"></a>

#### test`_`validate`_`payload

```python
@pytest.mark.parametrize("vote", (None, True, False))
def test_validate_payload(vote: Optional[bool]) -> None
```

Test `ValidatePayload`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payloads.test_tx_history_payload"></a>

#### test`_`tx`_`history`_`payload

```python
def test_tx_history_payload() -> None
```

Test `CheckTransactionHistoryPayload`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payloads.test_synchronize_payload"></a>

#### test`_`synchronize`_`payload

```python
def test_synchronize_payload() -> None
```

Test `SynchronizeLateMessagesPayload`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payloads.test_signature_payload"></a>

#### test`_`signature`_`payload

```python
def test_signature_payload() -> None
```

Test `SignaturePayload`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payloads.test_finalization_tx_payload"></a>

#### test`_`finalization`_`tx`_`payload

```python
def test_finalization_tx_payload() -> None
```

Test `FinalizationTxPayload`.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_payloads.test_reset_payload"></a>

#### test`_`reset`_`payload

```python
def test_reset_payload() -> None
```

Test `ResetPayload`.

