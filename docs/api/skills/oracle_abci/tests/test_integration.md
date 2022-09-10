<a id="packages.valory.skills.oracle_abci.tests.test_integration"></a>

# packages.valory.skills.oracle`_`abci.tests.test`_`integration

Integration tests for various transaction settlement skill's failure modes.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.OracleBehaviourBaseCase"></a>

## OracleBehaviourBaseCase Objects

```python
class OracleBehaviourBaseCase(FSMBehaviourBaseCase)
```

Base case for testing the oracle.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TransactionSettlementIntegrationBaseCase"></a>

## TransactionSettlementIntegrationBaseCase Objects

```python
class TransactionSettlementIntegrationBaseCase(
    OracleBehaviourBaseCase,  GnosisIntegrationBaseCase)
```

Base case for integration testing TransactionSettlement FSM Behaviour.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TransactionSettlementIntegrationBaseCase.setup"></a>

#### setup

```python
@classmethod
def setup(cls, **kwargs: Any) -> None
```

Setup.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TransactionSettlementIntegrationBaseCase.deploy_oracle"></a>

#### deploy`_`oracle

```python
def deploy_oracle(mining_interval_secs: float = 0) -> None
```

Deploy the oracle.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TransactionSettlementIntegrationBaseCase.gen_safe_tx_hash"></a>

#### gen`_`safe`_`tx`_`hash

```python
def gen_safe_tx_hash() -> None
```

Generate safe's transaction hash.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TransactionSettlementIntegrationBaseCase.clear_unmined_txs"></a>

#### clear`_`unmined`_`txs

```python
def clear_unmined_txs() -> None
```

Clear all unmined txs. Mined txs will not be cleared, but this is not a problem.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TransactionSettlementIntegrationBaseCase.dummy_try_get_gas_pricing_wrapper"></a>

#### dummy`_`try`_`get`_`gas`_`pricing`_`wrapper

```python
@staticmethod
def dummy_try_get_gas_pricing_wrapper(max_priority_fee_per_gas: Wei = DUMMY_MAX_PRIORITY_FEE_PER_GAS, max_fee_per_gas: Wei = DUMMY_MAX_FEE_PER_GAS, repricing_multiplier: float = DUMMY_REPRICING_MULTIPLIER) -> Callable[
        [Optional[str], Optional[Dict], Optional[Dict[str, Wei]]], Dict[str, Wei]
    ]
```

A dummy wrapper of `EthereumAPI`'s `try_get_gas_pricing`.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestRepricing"></a>

## TestRepricing Objects

```python
@skip_docker_tests
class TestRepricing(TransactionSettlementIntegrationBaseCase)
```

Test failure modes related to repricing.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestRepricing.test_same_keeper"></a>

#### test`_`same`_`keeper

```python
@pytest.mark.parametrize("should_mock_ledger_pricing_mechanism", (True, False))
def test_same_keeper(should_mock_ledger_pricing_mechanism: bool) -> None
```

Test repricing with and without mocking ledger's `try_get_gas_pricing` method.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestKeepers"></a>

## TestKeepers Objects

```python
class TestKeepers(OracleBehaviourBaseCase,  IntegrationBaseCase)
```

Test the keepers related functionality for the tx settlement skill.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestKeepers.setup"></a>

#### setup

```python
@classmethod
def setup(cls, **kwargs: Any) -> None
```

Set up the test class.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestKeepers.select_keeper"></a>

#### select`_`keeper

```python
@mock.patch.object(
        TransactionSettlementBaseBehaviour,
        "serialized_keepers",
        side_effect=lambda keepers, retries: retries.to_bytes(32, "big").hex()
        + "".join(keepers),
    )
def select_keeper(serialized_keepers_mock: mock.Mock, expected_keepers: Deque[str], expected_retries: int, first_time: bool = False) -> None
```

Select a keeper.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestKeepers.test_keepers_alternating"></a>

#### test`_`keepers`_`alternating

```python
def test_keepers_alternating() -> None
```

Test that we are alternating the keepers when we fail or timeout more than `keeper_allowed_retries` times.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestKeepers.test_rotation"></a>

#### test`_`rotation

```python
def test_rotation() -> None
```

Test keepers rotating when threshold reached.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestSyncing"></a>

## TestSyncing Objects

```python
@skip_docker_tests
class TestSyncing(TransactionSettlementIntegrationBaseCase)
```

Test late tx hashes synchronization.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestSyncing.setup"></a>

#### setup

```python
@classmethod
def setup(cls, **kwargs: Any) -> None
```

Set up the test class.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestSyncing.sync_late_messages"></a>

#### sync`_`late`_`messages

```python
def sync_late_messages() -> None
```

Synchronize late messages.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestSyncing.check_late_tx_hashes"></a>

#### check`_`late`_`tx`_`hashes

```python
def check_late_tx_hashes() -> None
```

Check the late transaction hashes to see if any is validated.

<a id="packages.valory.skills.oracle_abci.tests.test_integration.TestSyncing.test_sync_local_hash"></a>

#### test`_`sync`_`local`_`hash

```python
@mock.patch.object(
        EthereumApi,
        "try_get_gas_pricing",
        side_effect=TransactionSettlementIntegrationBaseCase.dummy_try_get_gas_pricing_wrapper(),
    )
def test_sync_local_hash(_: mock.Mock) -> None
```

Test the case in which we have received a tx hash during finalization, but timed out before sharing it.

