# Finite State Machines (FSMs)

In this section we introduce the concept of _finite state machine_ and discuss its role in the construction
of {{valory_app}}s, and in the operation of AEAs.

A [finite state machine](https://en.wikipedia.org/wiki/Finite-state_machine) (FSM) is a mathematical model of computation that can be
used to represent a sequential logic of state transitions.
We use FSMs to describe systems that have multiple states and can transition from one state to another due to some event or signal. In every state, we will need to perform one or more actions to trigger an event. This event will make the application to transit to a new state.


Therefore, FSMs let us define all the steps that an application of a service must follow, or in other words, the application logic.
At any given time
the FSM can be in exactly one particular state from which it can transition to
other states based on the reception of certain _events_ that it is given. The rules to transition from one state to another are governed by the so-called _transition function_. The transition function takes as input the current state and the received event and outputs the next state where the FSM will transit. A compact way of visualizing an FSM and its transition function is through a
graph with a finite number of nodes, depicting the possible states of the
system, and a finite number of labelled arcs, representing the transitions from one state to another.

As an example, consider an FSM describing a simplified vending machine with three different states:

- _Idle_: the machine is waiting for a customer to insert a coin.
- _Ready_: a coin has been inserted, and the machine is waiting for the customer to select a product, or request a refund.
- _Release_: the machine releases the selected product.

Therefore, the four self-explanatory events of this FSM are:

- COIN_INSERTED
- PRODUCT_SELECTED
- REFUND_REQUEST
- PRODUCT_RELEASED


We can represent the FSM as a graph as follows:

<figure markdown>
<div class="mermaid">
stateDiagram-v2
direction LR
  [*] --> Idle
  Idle --> Ready: COIN_INSERTED
  Ready --> Idle: REFUND_REQUEST
  Ready --> Release: PRODUCT_SELECTED
  Release --> Idle: PRODUCT_RELEASED
</div>
<figcaption>Diagram of a simplified vending machine FSM</figcaption>
</figure>




## How Valory Apps use FSMs

Departing from this basic notion of FSM, we are now in position to describe in more detail the particularities of the FSMs in the {{valory_stack}}. Namely, what are the key components to take into account when the FSM transitions from one state to another.

<figure markdown>
  ![](./images/fsm.svg){align=center}
  <figcaption>Diagram of a Valory stack FSM</figcaption>
</figure>


The figure above depicts the main components of an FSM implemented with the {{valory_stack}}, composed of six states (A-F) and six events (1-6).


It is important to note that in the {{valory_stack}} the responsibility of a state in an FSM is distributed across two components, as it can be seen in the "zoomed" State C above:

- A _round_ is the component that defines the rules to transition across different
  states. It is a concrete implementation of the `AbstractRound` class. It usually involves
  interactions between participants, although this is not enforced
  at this level of abstraction. A round can validate, store and aggregate data
  coming from different agents by means of transactions. The actual meaning of
  the data depends on the implementation of the specific round. This component
  produces the `Events` that will enable the FSM transit from one state to another, that is, capturing the role of the transition function.

- A _behaviour_ is the component that defines the actions to be executed at
  a particular state. It is a concrete implementation of the `BaseState` class, and contains the application logic for each state. It is scheduled for
  execution by the agents. Every behaviour is associated with a specific round.

We will sometimes use indistinctly the terms "state" or "round" in the context of the {{valory_stack}}.  We also define the following concepts that are particular to the stack:

- A _period_ is a sequence of states that is semantically meaningful. See a more elaborate definition below.
- The _period state_ is the component that contains shared information
  across sates. It provides access to the state data that is shared by the agents throughout a period (see below), and gets updated at the end of each round. Therefore, it is not tied to any specific state, rather each state can update its contents. It is a concrete implementation of the `BasePeriodState` class.



!!! example

    A round/state might just be a stage in
    the overall flow of the application (e.g., waiting that a sufficient number of participants commit their
    observations to a temporary blockchain), or a voting round (e.g.,
    waiting until at least an observed value has reached $\lceil(2N + 1) / 3\rceil$ of the votes).

    A period, on the other hand, consists of a sequence of such stages in the FSM state flow that achieve a specific objective defined by the {{valory_app}}. Consider the price oracle demo, which aggregates asset prices from different data sources and submits the aggregated result to an L1/L2 blockchain. In this example a period is defined as follows:

    1. Collect observations from external APIs or prior rounds.
    2. Reach consensus on the set of collected observations (i.e., 2/3 of the agents must agree).
    3. Compute a function (e.g., mean) on the set of collected observations, and reach consensus on the computed result.
    4. Construct a transaction that contains the aggregated result.
    5. Sign the transaction (2/3 of the agents must agree to sign).
    6. A single agent, randomly nominated as the keeper, sends the transaction to the chain. If it does not do this before a
    timeout event occurs, another agent is selected to be the
    keeper.
    7. Go to Step 1.



In order to define more formally a period, two sets of special states are defined for the FSM, namely _start states_ and _final states_. Every FSM has a set of start states, but it might not have a set of final states. Therefore, a period is defined as a sequence of states that begin at a start state and finishes either:

  - at a final state, if the set of final states is defined, or
  - at a start state, otherwise.

## Composition of FSMs

In order to facilitate rapid development of complex applications, the {{valory_stack}} offers a mechanism to extend and reuse already developed components known as _FSM composition_.

Departing from a collection of FSMs, say FSM1, FSM2, ..., FSM$n$, a composed FSM can be constructed with a composition mechanism that follows certain rules. Most importantly, an FSM$i$ can transit from a final state to a start state of another FSM$j$. If such a inter-FSM transition is defined, the composition mechanism will enforce that all the transitions ending in the final state of FSM$i$ be re-arranged to point to the corresponding start state of FSM$j$. The collection of transitions between FSMs are described in what we call the _FSM transition mapping_.

<figure markdown>
  ![](./images/fsm_composition.svg){align=center}
  <figcaption>How the FSM composition process works</figcaption>
</figure>

The figure above depicts a excerpt of a composition stage of three FSMs. Note how the finish states of FSM1 are linked to start states of FSM2 and FSM3. We remark that the transitions indicated by the FSM transition mapping are not regular transitions that respond to events, rather they are merely a construct to indicate how the states in the aggregated FSM must be connected.

## Implementation Details of FSMs

!!!note
    For clarity, the snippets of code presented here are a simplified version of the actual
    implementation. We refer the reader to the {{valory_stack_api}} for the complete details.

Now, we discuss the main components of the {{valory_stack}} FSMs presented above. Namely,
`Round`, `Behaviour`, `Period`, `PeriodState`, and `Event`. The `abstract_round_abci` skill implements the abstract classes for
implementation of these components.


### Period State

The `BasePeriodState` provides access to state variables stored in a `StateDB`
shared by the agents throughout the entire period, and which can be updated
at each state. It provides access to information such as the participants and
their votes in various types of voting rounds. This class is typically derived
during the implementation of a skill by the developer, in order to provide additional
functionality that is relevant for the execution of that skill.

```python
# skills.abstract_round_abci.base.py

class BasePeriodState:
    """Class to represent a period state."""

    @property
    def db(self) -> StateDB:
        """Get DB."""

    @property
    def participants(self) -> FrozenSet[str]:
        """Get the participants."""

    @property
    def participant_to_votes(self) -> Mapping:
        """Check whether keeper is set."""
    ...
```

An example of a concrete implementation of a `PeriodState` might look something
as follows, where access to contract addresses is provided to the agents.
In a typical skill implementation such addresses are selected during an earlier
round of the period in which consensus achieved over it.

```python
# skills.abstract_round_abci.base.py

class PeriodState(BasePeriodState):
    """Class to represent a period state."""

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""

    @property
    def oracle_contract_address(self) -> str:
        """Get the oracle contract address."""
    ...
```

### Round

A round can be viewed as a state of a period. It usually involves interactions between agents in the form of `Transactions`,
although this is not enforced at this level of abstraction.
`round_id` and `allowed_tx_type` must be provided by the developer that
implements a concrete subclass.

A `Transaction` is a class that is composed of:

- a _payload_ and
- a _signature_ of the payload.

The payload is an instance of a subclass of the abstract class `BaseTxPayload`.
Concrete subclasses of `BaseTxPayload` specify the allowed transaction payloads
and depend on the actual use case. The signature contains a binary encoding of
the payload during that round.

The `BasePeriodState` is passed on initialization of any concrete implementation,
of the `AbstractRound`, allowing agents to access period state information
during a particular round.
`ConsensusParams` are also passed upon initialization, which registers the
number of participants and computes the consensus threshold,
$\lceil(2N + 1) / 3\rceil$, which is used to determine whether there is sufficient
agreement among the agents regarding the result of the behaviour that was
executed during that round.


```python
# skills.abstract_round_abci.base.py

class AbstractRound(Generic[EventType, TransactionType], ABC):
    """This class represents an abstract round."""

    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def __init__(
        self, state: BasePeriodState, consensus_params: ConsensusParams
    ) -> None:
        """Initialize the round."""

    @property
    def period_state(self) -> BasePeriodState:
        """Get the period state."""

    def process_transaction(self, transaction: Transaction) -> None:
        """Process a transaction."""
        ... # check allowed transaction type
        self.process_payload(transaction.payload)

    @abstractmethod
    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""

    @abstractmethod
    def end_block(self) -> Optional[Tuple[BasePeriodState, Enum]]:
        """Process the end of the block."""
    ...
```

An example of a concrete implementation is a `CollectionRound` in which
data is collected, for example from a voting round or a price estimation round.

```python
# skills.abstract_round_abci.base.py

class CollectionRound(AbstractRound):
    """CollectionRound."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""

        sender = payload.sender
        self.collection[sender] = payload
    ...
```

Note that apart from the method for processing a particular payload, the
developer also needs to implement a method for processing the end of a block.
It needs to be implemented in a way that it can be used to check whether and how
a round was ended by returning both the `BasePeriodState` and an `Event`.


### Behaviour

The abstract base class used for any concrete implementation of behaviour is the
`BaseState`. It inherits directly from the `AsyncBehaviour` class and the same execution logic applies that leads to the periodic
execution of the `act()` and `async_act()` methods.

The `state_id` and `matching_round` both need to be provided by any class implementing
this base class, ensuring that a concrete implementation of the `AbstractRound`
is associated during which this behaviour will be executed.

```python
# skills.abstract_round_abci.behaviour_utils.py

class BaseState(AsyncBehaviour, SimpleBehaviour, ABC):
    """Base class for FSM states."""

    state_id = ""
    matching_round: Optional[Type[AbstractRound]] = None
    ...

    def set_done(self) -> None:
        """Set the behaviour to done."""

    def is_done(self) -> bool:
        """Check whether the state is done."""
    ...
```

The `is_done()` method is available on all concrete implementations of behaviour
and is used to signal the completion of execution. Whether the execution of a
behaviour was completed successfully or not results, as well as the actual
result hereof (e.g., consensus reached or not) in reported as an output which is
translated into an `Event`.


### Event

Events are provided as class attributes of any concrete implementation of
`AbstractRound` by the developer to define the possible outcomes of a round.

```python
from enum import Enum

class Event(Enum):
    """Event enumeration"""

    DONE = "done"
    NONE = "none"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
```

These events are provided as class attributes in a concrete implementation of
`AbstractRound` and are used to decide what the next round in the `Period` is
that the system needs to transition to. An implementation might look as follows:

```python
# skills.abstract_round_abci.base.py

class CollectSameUntilThresholdRound(CollectionRound):
    """CollectSameUntilThresholdRound"""

    done_event: Event.DONE
    no_majority_event: Event.NO_MAJORITY
    ...
```


### Period

The implementation of a period is used to set up the
local consensus engine and the [ABCI application](./abci_app_intro.md), and facilitates
the interaction between these two.

```python
# skills.abstract_round_abci.base.py

class Period:
    """This class represents a period (i.e. a sequence of rounds)"""
    def __init__(self, abci_app_cls: Type[AbciApp]):
        """Initialize the round."""
        self._blockchain = Blockchain()
    ...
```

The actual round transition logic is implemented as part of the
[Application BlockChain Interface Application](./abci_app_intro.md) and the
`AbstractRoundBehaviour` is in control of its execution.
