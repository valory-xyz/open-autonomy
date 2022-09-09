<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds"></a>

# packages.valory.skills.price`_`estimation`_`abci.tests.test`_`rounds

Test the rounds of the skill.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_participants"></a>

#### get`_`participants

```python
def get_participants() -> FrozenSet[str]
```

Participants

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_participant_to_randomness"></a>

#### get`_`participant`_`to`_`randomness

```python
def get_participant_to_randomness(participants: FrozenSet[str], round_id: int) -> Dict[str, RandomnessPayload]
```

participant_to_randomness

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_most_voted_randomness"></a>

#### get`_`most`_`voted`_`randomness

```python
def get_most_voted_randomness() -> str
```

most_voted_randomness

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_participant_to_selection"></a>

#### get`_`participant`_`to`_`selection

```python
def get_participant_to_selection(participants: FrozenSet[str]) -> Dict[str, SelectKeeperPayload]
```

participant_to_selection

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_most_voted_keeper_address"></a>

#### get`_`most`_`voted`_`keeper`_`address

```python
def get_most_voted_keeper_address() -> str
```

most_voted_keeper_address

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_safe_contract_address"></a>

#### get`_`safe`_`contract`_`address

```python
def get_safe_contract_address() -> str
```

safe_contract_address

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_participant_to_votes"></a>

#### get`_`participant`_`to`_`votes

```python
def get_participant_to_votes(participants: FrozenSet[str], vote: Optional[bool] = True) -> Dict[str, ValidatePayload]
```

participant_to_votes

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_participant_to_observations"></a>

#### get`_`participant`_`to`_`observations

```python
def get_participant_to_observations(participants: FrozenSet[str]) -> Dict[str, ObservationPayload]
```

participant_to_observations

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_participant_to_estimate"></a>

#### get`_`participant`_`to`_`estimate

```python
def get_participant_to_estimate(participants: FrozenSet[str]) -> Dict[str, EstimatePayload]
```

participant_to_estimate

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_estimate"></a>

#### get`_`estimate

```python
def get_estimate() -> float
```

Estimate

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_most_voted_estimate"></a>

#### get`_`most`_`voted`_`estimate

```python
def get_most_voted_estimate() -> float
```

most_voted_estimate

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_participant_to_tx_hash"></a>

#### get`_`participant`_`to`_`tx`_`hash

```python
def get_participant_to_tx_hash(participants: FrozenSet[str], hash_: Optional[str] = "tx_hash") -> Dict[str, TransactionHashPayload]
```

participant_to_tx_hash

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.get_most_voted_tx_hash"></a>

#### get`_`most`_`voted`_`tx`_`hash

```python
def get_most_voted_tx_hash() -> str
```

most_voted_tx_hash

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestRandomnessTransactionSubmissionRound"></a>

## TestRandomnessTransactionSubmissionRound Objects

```python
class TestRandomnessTransactionSubmissionRound(BaseCollectSameUntilThresholdRoundTest)
```

Test RandomnessTransactionSubmissionRound.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestRandomnessTransactionSubmissionRound.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run tests.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestCollectObservationRound"></a>

## TestCollectObservationRound Objects

```python
class TestCollectObservationRound(BaseCollectDifferentUntilThresholdRoundTest)
```

Test CollectObservationRound.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestCollectObservationRound.test_run_a"></a>

#### test`_`run`_`a

```python
def test_run_a() -> None
```

Runs tests.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestCollectObservationRound.test_run_b"></a>

#### test`_`run`_`b

```python
def test_run_b() -> None
```

Runs tests with one less observation.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestEstimateConsensusRound"></a>

## TestEstimateConsensusRound Objects

```python
class TestEstimateConsensusRound(BaseCollectSameUntilThresholdRoundTest)
```

Test EstimateConsensusRound.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestEstimateConsensusRound.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Runs test.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestTxHashRound"></a>

## TestTxHashRound Objects

```python
class TestTxHashRound(BaseCollectSameUntilThresholdRoundTest)
```

Test TxHashRound.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestTxHashRound.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Runs test.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.TestTxHashRound.test_run_none"></a>

#### test`_`run`_`none

```python
def test_run_none() -> None
```

Runs test.

<a id="packages.valory.skills.price_estimation_abci.tests.test_rounds.test_synchronized_datas"></a>

#### test`_`synchronized`_`datas

```python
def test_synchronized_datas() -> None
```

Test SynchronizedData.

