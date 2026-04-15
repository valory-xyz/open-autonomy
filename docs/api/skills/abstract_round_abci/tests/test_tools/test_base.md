<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_base"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`tools.test`_`base

Tests for abstract_round_abci/test_tools/base.py

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_base.TestFSMBehaviourBaseCaseSetup"></a>

## TestFSMBehaviourBaseCaseSetup Objects

```python
class TestFSMBehaviourBaseCaseSetup(FSMBehaviourTestToolSetup)
```

test TestFSMBehaviourBaseCaseSetup setup

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_base.TestFSMBehaviourBaseCaseSetup.test_setup_fails_without_path"></a>

#### test`_`setup`_`fails`_`without`_`path

```python
@pytest.mark.parametrize("kwargs", [{}])
def test_setup_fails_without_path(kwargs: Dict[str, Dict[str, Any]]) -> None
```

Test setup

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_base.TestFSMBehaviourBaseCaseSetup.test_setup"></a>

#### test`_`setup

```python
@pytest.mark.parametrize("kwargs", [{}, {"param_overrides": {"new_p": None}}])
def test_setup(kwargs: Dict[str, Dict[str, Any]]) -> None
```

Test setup

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_base.TestFSMBehaviourBaseCaseSetup.test_fast_forward_to_behaviour"></a>

#### test`_`fast`_`forward`_`to`_`behaviour

```python
@pytest.mark.parametrize("behaviour", DummyRoundBehaviour.behaviours)
def test_fast_forward_to_behaviour(behaviour: BaseBehaviour) -> None
```

Test fast_forward_to_behaviour

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_base.TestFSMBehaviourBaseCaseSetup.test_end_round"></a>

#### test`_`end`_`round

```python
@pytest.mark.parametrize("event", Event)
@pytest.mark.parametrize("set_none", [False, True])
def test_end_round(event: Enum, set_none: bool) -> None
```

Test end_round

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_base.TestFSMBehaviourBaseCaseSetup.test_mock_ledger_api_request"></a>

#### test`_`mock`_`ledger`_`api`_`request

```python
def test_mock_ledger_api_request() -> None
```

Test mock_ledger_api_request

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_base.TestFSMBehaviourBaseCaseSetup.test_mock_contract_api_request"></a>

#### test`_`mock`_`contract`_`api`_`request

```python
def test_mock_contract_api_request() -> None
```

Test mock_contract_api_request

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_base.test_dummy_context_is_abstract_component"></a>

#### test`_`dummy`_`context`_`is`_`abstract`_`component

```python
def test_dummy_context_is_abstract_component() -> None
```

Test dummy context is abstract component

