<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`behaviours

Test the behaviours.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.test_skill_public_id"></a>

#### test`_`skill`_`public`_`id

```python
def test_skill_public_id() -> None
```

Test skill module public ID

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteBackgroundRound"></a>

## ConcreteBackgroundRound Objects

```python
class ConcreteBackgroundRound(AbstractRound)
```

Concrete Background Round.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteBackgroundRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, EventType]]
```

End block.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteBackgroundRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check payload.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteBackgroundRound.process_payload"></a>

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.BehaviourC"></a>

## BehaviourC Objects

```python
class BehaviourC(BaseBehaviour, ABC)
```

Dummy behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.test_auto_behaviour_id"></a>

#### test`_`auto`_`behaviour`_`id

```python
def test_auto_behaviour_id() -> None
```

Test that the 'auto_behaviour_id()' method works as expected.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteBackgroundBehaviour"></a>

## ConcreteBackgroundBehaviour Objects

```python
class ConcreteBackgroundBehaviour(BaseBehaviour)
```

Dummy behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteBackgroundBehaviour.async_act"></a>

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteRoundBehaviour.behaviours"></a>

#### behaviours

type: ignore

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.ConcreteRoundBehaviour.background_behaviours_cls"></a>

#### background`_`behaviours`_`cls

type: ignore

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour"></a>

## TestAbstractRoundBehaviour Objects

```python
class TestAbstractRoundBehaviour()
```

Test 'AbstractRoundBehaviour' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Set up the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_setup"></a>

#### test`_`setup

```python
@pytest.mark.parametrize("use_termination", (True, False))
def test_setup(use_termination: bool) -> None
```

Test 'setup' method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_setup_pending_offences_included_when_slashing_enabled"></a>

#### test`_`setup`_`pending`_`offences`_`included`_`when`_`slashing`_`enabled

```python
def test_setup_pending_offences_included_when_slashing_enabled() -> None
```

Test that PendingOffencesBehaviour is included when use_slashing=True.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_check_matching_round_consistency_no_behaviour"></a>

#### test`_`check`_`matching`_`round`_`consistency`_`no`_`behaviour

```python
@pytest.mark.parametrize(
    "no_round, error",
    (
        (
            True,
            "Behaviour 'behaviour_without_round' specifies unknown 'unknown' as a matching round. "
            "Please make sure that the round is implemented and belongs to the FSM. "
            "If 'behaviour_without_round' is a background behaviour, please make sure that it is set correctly, "
            "by overriding the corresponding attribute of the chained skill's behaviour.",
        ),
        (False, "round round_1 is not a matching round of any behaviour"),
    ),
)
def test_check_matching_round_consistency_no_behaviour(no_round: bool,
                                                       error: str) -> None
```

Test classmethod '_check_matching_round_consistency', when no behaviour or round is specified.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_check_matching_round_consistency"></a>

#### test`_`check`_`matching`_`round`_`consistency

```python
def test_check_matching_round_consistency() -> None
```

Test classmethod '_check_matching_round_consistency', negative case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_check_matching_round_consistency_with_bg_rounds"></a>

#### test`_`check`_`matching`_`round`_`consistency`_`with`_`bg`_`rounds

```python
@pytest.mark.parametrize("behaviour_cls", (set(), {MagicMock()}))
def test_check_matching_round_consistency_with_bg_rounds(
        behaviour_cls: set) -> None
```

Test classmethod '_check_matching_round_consistency' when a background behaviour class is set.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_termination_behaviour_acting"></a>

#### test`_`termination`_`behaviour`_`acting

```python
@mock.patch.object(
    AbstractRoundBehaviour,
    "_process_current_round",
)
@mock.patch.object(
    TmManager,
    "tm_communication_unhealthy",
    new_callable=mock.PropertyMock,
    return_value=False,
)
@mock.patch.object(
    TmManager,
    "is_acting",
    new_callable=mock.PropertyMock,
    return_value=False,
)
@pytest.mark.parametrize("expected_termination_acting", (True, False))
def test_termination_behaviour_acting(
        _: mock._patch, __: mock._patch, ___: mock._patch,
        expected_termination_acting: bool) -> None
```

Test if the termination background behaviour is acting only when it should.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestAbstractRoundBehaviour.test_try_fix_call"></a>

#### test`_`try`_`fix`_`call

```python
@mock.patch.object(
    AbstractRoundBehaviour,
    "_process_current_round",
)
@pytest.mark.parametrize(
    ("mock_tm_communication_unhealthy", "mock_is_acting", "expected_fix"),
    [
        (True, True, True),
        (False, True, True),
        (True, False, True),
        (False, False, False),
    ],
)
def test_try_fix_call(_: mock._patch, mock_tm_communication_unhealthy: bool,
                      mock_is_acting: bool, expected_fix: bool) -> None
```

Test that `try_fix` is called when necessary.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.test_meta_round_behaviour_when_instance_not_subclass_of_abstract_round_behaviour"></a>

#### test`_`meta`_`round`_`behaviour`_`when`_`instance`_`not`_`subclass`_`of`_`abstract`_`round`_`behaviour

```python
def test_meta_round_behaviour_when_instance_not_subclass_of_abstract_round_behaviour(
) -> (None)
```

Test instantiation of meta class when instance not a subclass of abstract round behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.test_abstract_round_behaviour_instantiation_without_attributes_raises_error"></a>

#### test`_`abstract`_`round`_`behaviour`_`instantiation`_`without`_`attributes`_`raises`_`error

```python
def test_abstract_round_behaviour_instantiation_without_attributes_raises_error(
) -> (None)
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
def test_self_loops_in_abci_app_reinstantiate_behaviour(
        _: mock._patch) -> None
```

Test that a self-loop transition in the AbciApp will trigger a transition in the round behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.LongRunningBehaviour"></a>

## LongRunningBehaviour Objects

```python
class LongRunningBehaviour(BaseBehaviour)
```

A behaviour that runs forevever.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.LongRunningBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

An act method that simply cycles forever.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.test_reset_should_be_performed_when_tm_unhealthy"></a>

#### test`_`reset`_`should`_`be`_`performed`_`when`_`tm`_`unhealthy

```python
def test_reset_should_be_performed_when_tm_unhealthy() -> None
```

Test that hard reset is performed while a behaviour is running, and tendermint communication is unhealthy.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestPendingOffencesBehaviour"></a>

## TestPendingOffencesBehaviour Objects

```python
class TestPendingOffencesBehaviour()
```

Tests for `PendingOffencesBehaviour`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestPendingOffencesBehaviour.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls) -> None
```

Setup the test class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_behaviours.TestPendingOffencesBehaviour.test_pending_offences_act"></a>

#### test`_`pending`_`offences`_`act

```python
@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="`timegm` behaves differently on Windows. "
    "As a result, the generation of `last_transition_timestamp` is invalid.",
)
@given(
    offence=st.builds(
        PendingOffense,
        accused_agent_address=st.text(),
        round_count=st.integers(min_value=0),
        offense_type=st.sampled_from(OffenseType),
        last_transition_timestamp=st.floats(
            min_value=timegm(datetime(1971, 1, 1).utctimetuple()),
            max_value=timegm(datetime(8000, 1, 1).utctimetuple()) - 2000,
        ),
        time_to_live=st.floats(min_value=1, max_value=2000),
    ),
    wait_ticks=st.integers(min_value=0, max_value=1000),
    expired=st.booleans(),
)
def test_pending_offences_act(offence: PendingOffense, wait_ticks: int,
                              expired: bool) -> None
```

Test `PendingOffencesBehaviour`.

