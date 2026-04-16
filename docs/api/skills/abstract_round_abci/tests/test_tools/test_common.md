<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`tools.test`_`common

Tests for abstract_round_abci/test_tools/common.py

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.BaseCommonBaseCaseTestSetup"></a>

## BaseCommonBaseCaseTestSetup Objects

```python
class BaseCommonBaseCaseTestSetup(FSMBehaviourTestToolSetup)
```

BaseRandomnessBehaviourTestSetup

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.BaseCommonBaseCaseTestSetup.set_done_event"></a>

#### set`_`done`_`event

```python
def set_done_event() -> None
```

Set done_event

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.BaseCommonBaseCaseTestSetup.set_next_behaviour_class"></a>

#### set`_`next`_`behaviour`_`class

```python
def set_next_behaviour_class(next_behaviour_class: Type) -> None
```

Set next_behaviour_class

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseRandomnessBehaviourTestSetup"></a>

## TestBaseRandomnessBehaviourTestSetup Objects

```python
class TestBaseRandomnessBehaviourTestSetup(BaseCommonBaseCaseTestSetup)
```

Test BaseRandomnessBehaviourTest setup.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseRandomnessBehaviourTestSetup.set_randomness_behaviour_class"></a>

#### set`_`randomness`_`behaviour`_`class

```python
def set_randomness_behaviour_class() -> None
```

Set randomness_behaviour_class

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseRandomnessBehaviourTestSetup.test_setup_randomness_behaviour_class_not_set"></a>

#### test`_`setup`_`randomness`_`behaviour`_`class`_`not`_`set

```python
def test_setup_randomness_behaviour_class_not_set() -> None
```

Test setup randomness_behaviour_class not set.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseRandomnessBehaviourTestSetup.test_setup_done_event_not_set"></a>

#### test`_`setup`_`done`_`event`_`not`_`set

```python
def test_setup_done_event_not_set() -> None
```

Test setup done_event = Event.DONE not set.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseRandomnessBehaviourTestSetup.test_setup_next_behaviour_class_not_set"></a>

#### test`_`setup`_`next`_`behaviour`_`class`_`not`_`set

```python
def test_setup_next_behaviour_class_not_set() -> None
```

Test setup next_behaviour_class not set.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseRandomnessBehaviourTestSetup.test_successful_setup_randomness_behaviour_test"></a>

#### test`_`successful`_`setup`_`randomness`_`behaviour`_`test

```python
def test_successful_setup_randomness_behaviour_test() -> None
```

Test successful setup of the test class inheriting from BaseRandomnessBehaviourTest.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseRandomnessBehaviourTestRunning"></a>

## TestBaseRandomnessBehaviourTestRunning Objects

```python
class TestBaseRandomnessBehaviourTestRunning(BaseRandomnessBehaviourTest)
```

Test TestBaseRandomnessBehaviourTestRunning running.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseSelectKeeperBehaviourTestSetup"></a>

## TestBaseSelectKeeperBehaviourTestSetup Objects

```python
class TestBaseSelectKeeperBehaviourTestSetup(BaseCommonBaseCaseTestSetup)
```

Test BaseRandomnessBehaviourTest setup.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseSelectKeeperBehaviourTestSetup.set_select_keeper_behaviour_class"></a>

#### set`_`select`_`keeper`_`behaviour`_`class

```python
def set_select_keeper_behaviour_class() -> None
```

Set select_keeper_behaviour_class

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseSelectKeeperBehaviourTestSetup.test_setup_select_keeper_behaviour_class_not_set"></a>

#### test`_`setup`_`select`_`keeper`_`behaviour`_`class`_`not`_`set

```python
def test_setup_select_keeper_behaviour_class_not_set() -> None
```

Test setup select_keeper_behaviour_class not set.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseSelectKeeperBehaviourTestSetup.test_setup_done_event_not_set"></a>

#### test`_`setup`_`done`_`event`_`not`_`set

```python
def test_setup_done_event_not_set() -> None
```

Test setup done_event = Event.DONE not set.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseSelectKeeperBehaviourTestSetup.test_setup_next_behaviour_class_not_set"></a>

#### test`_`setup`_`next`_`behaviour`_`class`_`not`_`set

```python
def test_setup_next_behaviour_class_not_set() -> None
```

Test setup next_behaviour_class not set.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseSelectKeeperBehaviourTestSetup.test_successful_setup_select_keeper_behaviour_test"></a>

#### test`_`successful`_`setup`_`select`_`keeper`_`behaviour`_`test

```python
def test_successful_setup_select_keeper_behaviour_test() -> None
```

Test successful setup of the test class inheriting from BaseSelectKeeperBehaviourTest.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_common.TestBaseSelectKeeperBehaviourTestRunning"></a>

## TestBaseSelectKeeperBehaviourTestRunning Objects

```python
class TestBaseSelectKeeperBehaviourTestRunning(BaseSelectKeeperBehaviourTest)
```

Test BaseSelectKeeperBehaviourTest running.

