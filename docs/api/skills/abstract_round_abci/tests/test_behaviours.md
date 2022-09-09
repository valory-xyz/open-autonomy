<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`behaviours

Test the behaviours.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.RoundA"></a>

## RoundA Objects

```python
class RoundA(AbstractRound)
```

Round A.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.RoundA.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, EventType]]
```

End block.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.RoundA.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check payload.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.RoundA.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payload.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.RoundB"></a>

## RoundB Objects

```python
class RoundB(AbstractRound)
```

Round B.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.RoundB.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, EventType]]
```

End block.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.RoundB.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check payload.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.RoundB.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payload.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.BehaviourA"></a>

## BehaviourA Objects

```python
class BehaviourA(BaseBehaviour)
```

Dummy behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.BehaviourA.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.BehaviourA.setup"></a>

#### setup

```python
def setup() -> None
```

Setup behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.BehaviourA.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Dummy act method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.BehaviourB"></a>

## BehaviourB Objects

```python
class BehaviourB(BaseBehaviour)
```

Dummy behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.BehaviourB.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Dummy act method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteAbciApp"></a>

## ConcreteAbciApp Objects

```python
class ConcreteAbciApp(AbciApp)
```

Concrete ABCI App.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteRoundBehaviour"></a>

## ConcreteRoundBehaviour Objects

```python
class ConcreteRoundBehaviour(AbstractRoundBehaviour)
```

Concrete round behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour"></a>

## TestAbstractRoundBehaviour Objects

```python
class TestAbstractRoundBehaviour()
```

Test 'AbstractRoundBehaviour' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_setup"></a>

#### test`_`setup

```python
def test_setup() -> None
```

Test 'setup' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_teardown"></a>

#### test`_`teardown

```python
def test_teardown() -> None
```

Test 'teardown' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_current_behaviour_return_none"></a>

#### test`_`current`_`behaviour`_`return`_`none

```python
def test_current_behaviour_return_none() -> None
```

Test 'current_behaviour' property return None.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_act_current_behaviour_name_is_none"></a>

#### test`_`act`_`current`_`behaviour`_`name`_`is`_`none

```python
def test_act_current_behaviour_name_is_none() -> None
```

Test 'act' with current behaviour None.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_check_matching_round_consistency"></a>

#### test`_`check`_`matching`_`round`_`consistency

```python
def test_check_matching_round_consistency() -> None
```

Test classmethod '_get_behaviour_id_to_behaviour_mapping', negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_get_behaviour_id_to_behaviour_mapping_negative"></a>

#### test`_`get`_`behaviour`_`id`_`to`_`behaviour`_`mapping`_`negative

```python
def test_get_behaviour_id_to_behaviour_mapping_negative() -> None
```

Test classmethod '_get_behaviour_id_to_behaviour_mapping', negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_get_round_to_behaviour_mapping_two_behaviours_same_round"></a>

#### test`_`get`_`round`_`to`_`behaviour`_`mapping`_`two`_`behaviours`_`same`_`round

```python
def test_get_round_to_behaviour_mapping_two_behaviours_same_round() -> None
```

Test classmethod '_get_round_to_behaviour_mapping' when two different behaviours point to the same round.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_get_round_to_behaviour_mapping_with_final_rounds"></a>

#### test`_`get`_`round`_`to`_`behaviour`_`mapping`_`with`_`final`_`rounds

```python
def test_get_round_to_behaviour_mapping_with_final_rounds() -> None
```

Test classmethod '_get_round_to_behaviour_mapping' with final rounds.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_check_behaviour_id_uniqueness_negative"></a>

#### test`_`check`_`behaviour`_`id`_`uniqueness`_`negative

```python
def test_check_behaviour_id_uniqueness_negative() -> None
```

Test metaclass method '_check_consistency', negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_check_consistency_two_behaviours_same_round"></a>

#### test`_`check`_`consistency`_`two`_`behaviours`_`same`_`round

```python
def test_check_consistency_two_behaviours_same_round() -> None
```

Test metaclass method '_check_consistency' when two different behaviours point to the same round.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_check_initial_behaviour_in_set_of_behaviours_negative_case"></a>

#### test`_`check`_`initial`_`behaviour`_`in`_`set`_`of`_`behaviours`_`negative`_`case

```python
def test_check_initial_behaviour_in_set_of_behaviours_negative_case() -> None
```

Test classmethod '_check_initial_behaviour_in_set_of_behaviours' when initial behaviour is NOT in the set.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_act_no_round_change"></a>

#### test`_`act`_`no`_`round`_`change

```python
def test_act_no_round_change() -> None
```

Test the 'act' method of the behaviour, with no round change.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_act_behaviour_setup"></a>

#### test`_`act`_`behaviour`_`setup

```python
def test_act_behaviour_setup() -> None
```

Test the 'act' method of the FSM behaviour triggers setup() of the behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_act_with_round_change"></a>

#### test`_`act`_`with`_`round`_`change

```python
def test_act_with_round_change() -> None
```

Test the 'act' method of the behaviour, with round change.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_act_with_round_change_after_current_behaviour_is_none"></a>

#### test`_`act`_`with`_`round`_`change`_`after`_`current`_`behaviour`_`is`_`none

```python
def test_act_with_round_change_after_current_behaviour_is_none() -> None
```

Test the 'act' method of the behaviour, with round change, after cur behaviour is none.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.test_meta_round_behaviour_when_instance_not_subclass_of_abstract_round"></a>

#### test`_`meta`_`round`_`behaviour`_`when`_`instance`_`not`_`subclass`_`of`_`abstract`_`round

```python
def test_meta_round_behaviour_when_instance_not_subclass_of_abstract_round() -> None
```

Test instantiation of meta class when instance not a subclass of abstract round.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.test_abstract_round_behaviour_instantiation_without_attributes_raises_error"></a>

#### test`_`abstract`_`round`_`behaviour`_`instantiation`_`without`_`attributes`_`raises`_`error

```python
def test_abstract_round_behaviour_instantiation_without_attributes_raises_error() -> None
```

Test that definition of concrete subclass of AbstractRoundBehavior without attributes raises error.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.test_abstract_round_behaviour_matching_rounds_not_covered"></a>

#### test`_`abstract`_`round`_`behaviour`_`matching`_`rounds`_`not`_`covered

```python
def test_abstract_round_behaviour_matching_rounds_not_covered() -> None
```

Test that definition of concrete subclass of AbstractRoundBehavior when matching round not covered.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.test_self_loops_in_abci_app_reinstantiate_behaviour"></a>

#### test`_`self`_`loops`_`in`_`abci`_`app`_`reinstantiate`_`behaviour

```python
@mock.patch.object(
    BaseBehaviour,
    "tm_communication_unhealthy",
    new_callable=mock.PropertyMock,
    return_value=False,
)
def test_self_loops_in_abci_app_reinstantiate_behaviour(_: mock._patch) -> None
```

Test that a self-loop transition in the AbciApp will trigger a transition in the round behaviour.

