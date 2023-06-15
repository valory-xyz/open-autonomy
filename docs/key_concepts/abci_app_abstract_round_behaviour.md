!!!note
    For clarity, the snippets of code presented here are a simplified version of the actual
    implementation. We refer the reader to the {{open_autonomy_api}} for the complete details.

Whereas the `AbciApp` class defines the model of the FSM for the {{fsm_app}}, the `AbstractRoundBehaviour` is a [`Behaviour`](https://open-aea.docs.autonolas.tech/api/skills/base/#behaviour-objects) that takes care of the processing of the current round
and transition to the subsequent round, implementation of which resides in the
`act()` method. Whenever the {{fsm_app}} detects a round change, the
`AbstractRoundBehaviour` schedules the state behaviour associated with the
current round, ensuring that a transition to the new state cannot occur without first invoking the
associated state Behaviour.

Below we present a sketch of this class:

```python
# skills.abstract_round_abci.behaviours.py

class AbstractRoundBehaviour(
    Behaviour, ABC, Generic[EventType], metaclass=_MetaRoundBehaviour
):
    """This behaviour implements an abstract round behaviour."""

    abci_app_cls: Type[AbciApp[EventType]]
    behaviours: AbstractSet[BehaviourType]
    initial_behaviour_cls: BehaviourType

    def instantiate_behaviour_cls(self, behaviour_cls: BehaviourType) -> BaseBehaviour:
        return behaviour_cls(
            name=behaviour_cls.auto_behaviour_id(), skill_context=self.context
        )

    def setup(self) -> None:
        self.current_behaviour = self.instantiate_behaviour_cls(
            self.initial_behaviour_cls
        )

    def act(self) -> None:
        """Implement the behaviour."""
        self._process_current_round()
    # (...)
```

A concrete implementation of `AbstractRoundBehaviour` requires that the developer provide the corresponding
`AbciApp`, a set of `BaseBehaviours` encoding the different types of Behaviour at each FSM state, and
the initial Behaviour. The`_MetaRoundBehaviour` metaclass provided enforces correctness on the
logic of the `AbstractRoundBehaviour` ensuring that:

- `abci_app_cls`, `behaviour_states` and   `initial_state_cls` are set,
- each `state_id` is unique,
- `initial_state_cls` is part of `behaviour_states`,
- rounds are unique across behavioural states, and
- all of behavioural states are covered during rounds.

A concrete implementation of the `AbstractRoundBehaviour` class looks as follows:

```python
class MyAbstractRoundBehaviour(AbstractRoundBehaviour):
    """My ABCI-based Finite-State Machine Application execution behaviour"""

    abci_app_cls: ABCIApp = MyAbciApp
    initial_state_cls: StateType = RoundA
    behaviour_states = {
      RoundA,
      RoundB,
      FinalRound,
    }
    # (...)
```
