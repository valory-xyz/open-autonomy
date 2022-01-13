# Finite State Machine


A finite state machine (FSM) is a mathematical model of computation that can be
used to represent the sequential logic of state transitions. At any given time 
the FSM can be in exactly one particular state from which it can transition to
other states based on the inputs it is given. An FSM can be represented by a 
graph, with a finite number of nodes describing the possible states of the 
system, and a finite number of arcs representing the transitions from one state
to another.


## How Finite State Machines work

A transition function ...
- introduce rounds and periods here
- how behaviour is scheduled and executed during a round

## Implementation

The abstract base class used for any concrete implementation of states is the
`BaseState`. It inherits directly from the `AsyncBehaviour` we discussed in the
previous section and the same execution logic applies. The `state_id` and
`matching_round` both need to be provided by any class using this base class, 
ensuring that a `Round` is associated.


```python
class BaseState(AsyncBehaviour, SimpleBehaviour, ABC):
    """Base class for FSM states."""
    
    state_id = ""
    matching_round: Optional[Type[AbstractRound]] = None
    ...
```


```python
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
        
    def act(self):
        """process the round"""
    ...
```

One of the primary purpose of the `_MetaRoundBehaviour` is to ensure that the
`initial_state_cls` is provided. 


```python
class AbstractRound(Generic[EventType, TransactionType], ABC):
    """This class represents an abstract round."""

    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str
```


A round is a state of a period. It usually involves
interactions between participants in the period,
although this is not enforced at this level of abstraction.


----
---- WIP notes


- `abci_app_cls`, `behaviour_states` and `initial_state_cls` are set
- that the `state_id` is unique
- that the `initial_state_cls` is part of the `behaviour_states`



`BaseState` base class to:
- all behaviour that is part of `behaviour_states` 

`AbstractRoundBehaviour` base class to
- PriceEstimationConsensusBehaviour
- LiquidityProvisionConsensusBehaviour



When the round instantiates the initial state the 
[`skill_context`](https://valory-xyz.github.io/open-aea/api/skills/base/)
is passed which provides access to the shared state via the `context` attribute.


