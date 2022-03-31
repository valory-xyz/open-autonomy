# FSM Implementation

!!!note
    The snippets of code presented here are a simplified representation of the actual
    implementation. We refer the reader to the corresponding API documentation for the complete details.

Here, we explain the
implementation of and relationship among the Valory stack FSMs core components, as discussed in the previous section. Namely,
`Round`, `Behaviour`, `Period`, `PeriodState`, and `Event`. The `abstract_round_abci` skill implements the abstract classes for
implementation of these components.


### Period State

The `BasePeriodState` provides access to state variables stored in a `StateDB`
shared by the agents throughout the entire period, and which can be updated
during rounds. It provides access to information such as the participants and
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

A round is a state of a period. It usually involves interactions between agents in the form of `Transactions`,
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
`ceil((2*N + 1) / 3)`, which is used to determine whether there is sufficient
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
result hereof (e.g. consensus reached or not) in reported as an output which is
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

A Period is a sequence of rounds that is semantically meaningful. Its implementation is used to set up the
local consensus engine and [ABCI application](./abci_app.md), and facilitates
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
[Application BlockChain Interface Application](./abci_app.md) and the
`AbstractRoundBehaviour` in control of its execution.
