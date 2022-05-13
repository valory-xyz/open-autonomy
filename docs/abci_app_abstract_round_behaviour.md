
# The `AbstractRoundBehaviour` Class

!!!note
    For clarity, the snippets of code presented here are a simplified version of the actual
    implementation. We refer the reader to the {{valory_stack_api}} for the complete details.

Whereas the `AbciApp` class defines the model of the FSM for the {{abci_app}}, the `AbstractRoundBehaviour` is a [`Behaviour`](https://valory-xyz.github.io/open-aea/api/skills/base/#behaviour-objects) that takes care of the processing of the current round
and transition to the subsequent round, implementation of which resides in the
`act()` method. Whenever the {{abci_app}} detects a round change, the
`AbstractRoundBehaviour` schedules the state behaviour associated with the
current round, ensuring that a transition to the new state cannot occur without first invoking the
associated state Behaviour.

Below we present a sketch of this class:

```python
# skills.abstract_round_abci.behaviours.py

StateType = Type[BaseState]

class AbstractRoundBehaviour(
    Behaviour, ABC, Generic[EventType], metaclass=_MetaRoundBehaviour
):
    """This behaviour implements an abstract round behaviour."""

    abci_app_cls: Type[AbciApp[EventType]]
    behaviour_states: AbstractSet[StateType]
    initial_state_cls: StateType

    def instantiate_state_cls(self, state_cls: StateType) -> BaseState:
        return state_cls(name=state_cls.state_id, skill_context=self.context)

    def setup(self) -> None:
        self.current_state = self.instantiate_state_cls(self.initial_state_cls)

    def act(self) -> None:
        """Implement the behaviour."""
        self._process_current_round()
        self.current_state = self.instantiate_state_cls(self._next_state_cls)
    ...
```

A concrete implementation of `AbstractRoundBehaviour` requires that the developer provide the corresponding
`AbciApp`, a set of `BaseStates` encoding the different types of Behaviour at each FSM state, and
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
    ...
```
