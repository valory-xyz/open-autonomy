<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds"></a>

# packages.valory.skills.oracle`_`deployment`_`abci.tests.test`_`rounds

Tests for valory/registration_abci skill's rounds.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.get_participants"></a>

#### get`_`participants

```python
def get_participants() -> FrozenSet[str]
```

Participants

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.get_participant_to_randomness"></a>

#### get`_`participant`_`to`_`randomness

```python
def get_participant_to_randomness(participants: FrozenSet[str], round_id: int) -> Dict[str, RandomnessPayload]
```

participant_to_randomness

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.get_most_voted_randomness"></a>

#### get`_`most`_`voted`_`randomness

```python
def get_most_voted_randomness() -> str
```

most_voted_randomness

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.get_participant_to_selection"></a>

#### get`_`participant`_`to`_`selection

```python
def get_participant_to_selection(participants: FrozenSet[str], keeper: str = "keeper") -> Dict[str, SelectKeeperPayload]
```

participant_to_selection

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.get_most_voted_keeper_address"></a>

#### get`_`most`_`voted`_`keeper`_`address

```python
def get_most_voted_keeper_address() -> str
```

most_voted_keeper_address

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.get_safe_contract_address"></a>

#### get`_`safe`_`contract`_`address

```python
def get_safe_contract_address() -> str
```

safe_contract_address

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.get_participant_to_votes"></a>

#### get`_`participant`_`to`_`votes

```python
def get_participant_to_votes(participants: FrozenSet[str], vote: Optional[bool] = True) -> Dict[str, ValidateOraclePayload]
```

participant_to_votes

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.BaseDeployTestClass"></a>

## BaseDeployTestClass Objects

```python
class BaseDeployTestClass(BaseOnlyKeeperSendsRoundTest)
```

Test DeploySafeRound.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.BaseDeployTestClass.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run tests.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.TestDeployOracleRound"></a>

## TestDeployOracleRound Objects

```python
class TestDeployOracleRound(BaseDeployTestClass)
```

Test DeployOracleRound.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.BaseValidateRoundTest"></a>

## BaseValidateRoundTest Objects

```python
class BaseValidateRoundTest(BaseVotingRoundTest)
```

Test BaseValidateRound.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.BaseValidateRoundTest.test_positive_votes"></a>

#### test`_`positive`_`votes

```python
def test_positive_votes() -> None
```

Test ValidateRound.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.BaseValidateRoundTest.test_negative_votes"></a>

#### test`_`negative`_`votes

```python
def test_negative_votes() -> None
```

Test ValidateRound.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.BaseValidateRoundTest.test_none_votes"></a>

#### test`_`none`_`votes

```python
def test_none_votes() -> None
```

Test ValidateRound.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.TestValidateOracleRound"></a>

## TestValidateOracleRound Objects

```python
class TestValidateOracleRound(BaseValidateRoundTest)
```

Test ValidateSafeRound.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.BaseSelectKeeperRoundTest"></a>

## BaseSelectKeeperRoundTest Objects

```python
class BaseSelectKeeperRoundTest(BaseCollectSameUntilThresholdRoundTest)
```

Test SelectKeeperTransactionSubmissionRoundA

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.BaseSelectKeeperRoundTest.test_run"></a>

#### test`_`run

```python
def test_run(most_voted_payload: str = "keeper", keepers: str = "", exit_event: Optional[Any] = None) -> None
```

Run tests.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.TestSelectKeeperOracleRound"></a>

## TestSelectKeeperOracleRound Objects

```python
class TestSelectKeeperOracleRound(BaseSelectKeeperRoundTest)
```

Test SelectKeeperTransactionSubmissionRoundB.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_rounds.test_synchronized_datas"></a>

#### test`_`synchronized`_`datas

```python
def test_synchronized_datas() -> None
```

Test SynchronizedData.

