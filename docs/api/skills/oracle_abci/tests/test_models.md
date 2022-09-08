<a id="packages.valory.skills.oracle_abci.tests.test_models"></a>

# packages.valory.skills.oracle`_`abci.tests.test`_`models

Test the models.py module of the skill.

<a id="packages.valory.skills.oracle_abci.tests.test_models.shared_state"></a>

#### shared`_`state

```python
@pytest.fixture
def shared_state() -> SharedState
```

Initialize a test shared state.

<a id="packages.valory.skills.oracle_abci.tests.test_models.TestSharedState"></a>

## TestSharedState Objects

```python
class TestSharedState()
```

Test SharedState(Model) class.

<a id="packages.valory.skills.oracle_abci.tests.test_models.TestSharedState.test_initialization"></a>

#### test`_`initialization

```python
def test_initialization() -> None
```

Test initialization.

<a id="packages.valory.skills.oracle_abci.tests.test_models.TestSharedState.test_setup"></a>

#### test`_`setup

```python
def test_setup(shared_state: SharedState) -> None
```

Test setup.

