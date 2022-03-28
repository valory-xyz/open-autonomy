
# AbstractRoundBehaviour implementation

The `AbstractRoundBehaviour` takes care of the processing of the current round
and transition to the subsequent round, implementation of which resides in the
`act()` method. Whenever a round change in the AbciApp is detected, the
`AbstractRoundBehaviour` schedules the state behaviour associated with the
current round, ensuring state transition cannot occur without first invoking the
associated behavioral change.

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

The concrete implementation of which requires the developer to provide the
`AbciApp`, a set of `BaseStates` encoding the different types of behaviour and
the initial behaviour. Similar to the role of `_MetaAbciApp` in the case of the
`AbciApp`, the`_MetaRoundBehaviour` metaclass provided here check the
logic of the `AbstractRoundBehaviour` implementation, ensuring that:

    - abci_app_cls, behaviour_states and initial_state_cls are set
    - that each `state_id` is unique
    - that the `initial_state_cls` is part of the `behaviour_states`
    - rounds are unique across behavioural states
    - that all of behavioural states are covered during rounds

A concrete implementation of a subclass of `AbstractRoundBehaviour` looks
as follows:

```python
class MyFSMBehaviour(AbstractRoundBehaviour):
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


## The `ABCIApp` - `AbstractRoundBehaviour` interaction

The interaction between `AbstractRoundBehaviour` and the `ABCIApp` occurs via
the consensus engine, the setup of which proceeds on the `Period`.
and the shared state among the skills. A typical workflow
looks as follows:

1. At setup time, the consensus engine node creates connections with the
   associated AEA and sync together. In the AEA process, the ABCIApp starts from
   the first round, waiting for transactions to update its state. The
   `AbstractRoundBehaviour` schedules the initial state behaviour for execution
   of the `act()` method.

2. The current state behaviour sends transactions to update the state of the
   `ABCIApp`, and once its job is done waits until it transitions to the next
   round, by checking read-only attributes of the `ABCIApp` accessible through
   the AEAs' skill context. Concrete implementations of `AbstractRoundBehaviour`
   cannot update the state the of ABCIApp directly, only through an agreed
   upon update with other agents via the consensus engine node.

3. Once the transaction gets added to a block accepted by the consensus engine,
   the consensus engine node delivers the block and transactions contained in
   it to the `ABCIApp` using the AEAs `ABCIConnection` and `ABCIHandler`. The
   `ABCIApp` processes the transaction and enacts the encoded state transition
   logic.

4. The transition to the next round is detected and all scheduled behaviour and
   other tasks get cancelled before transitioning to the next round.

5. Cycles of such rounds may, either entirely or in part, be repeated until a
   final state is reached, implemented as a


The [price estimation demo](./price_estimation_demo.md)
showcases deployment and operation of AEAs using an ABCIApp.

## AbstractRoundBehaviour:

Concrete implementations of `AbstractRoundBehaviour` can be seen as a _client_
of the `ABCIApp` (in that sense it encapsulates the "user" of a normal blockchain).


### AbstractRoundBehaviour diagrams

The following diagram shows how the FSM behaviour operates in concert with the
AEA event loop.

<div class="mermaid">
    sequenceDiagram
        participant EventLoop
        participant AbsRoundBehaviour
        participant State1
        participant State2
        participant Period
        note over AbsRoundBehaviour,State2: Let the FSMBehaviour start with State1<br/>it will schedule State2 on event e
        loop while round does not change
          EventLoop->>AbsRoundBehaviour: act()
          AbsRoundBehaviour->>State1: act()
          activate State1
          note over State1: during the execution, <br/> the current round may<br/>(or may not) change
          State1->>AbsRoundBehaviour: return
          deactivate State1
          note over EventLoop: the loop now executes other routines
        end
        note over AbsRoundBehaviour: read current AbciApp round and pick matching state<br/>in this example, State2
        EventLoop->>AbsRoundBehaviour: act()
        note over AbsRoundBehaviour: now State2.act is called
        AbsRoundBehaviour->>State2: act()
        activate State2
        State2->>AbsRoundBehaviour: return
        deactivate State2
</div>