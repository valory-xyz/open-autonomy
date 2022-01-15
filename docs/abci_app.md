# ABCI Applications

In this section, we describe the ABCI-based Finite-State Machine Application
(`ABCIApp`), the Finite-State Machine Behaviour (`AbstractRoundBehaviour`),
and the interplay between the two. An understanding of the 
[Application BlockChain Interface](./abci.md) and the constituents parts of
a [Finite State Machines](./fsm.md) - the `Period` containing a sequence of 
concrete implementations of the `AbstractRound`, the implementation of 
`Behavior` to be executed during these rounds, and the `PeriodState` providing
access to the shared state throughout a `Period` - is a prerequisite to 
understanding how ABCI applications interact with the consensus engine.


## The `ABCIApp`: an ABCI-based replicated FSM

The `ABCIApp` is a finite-state machine implemented as an ABCI Application, 
that defines the finite-state machine of a period of the consensus on a 
temporary blockchain. We call _round_ a state in an ABCIApp, and _period_ an 
execution of the `ABCIApp`. The state of the `ABCIApp` is updated through 
transactions on a distributed ledger that local. 

This ledger is local with respect to the `Period`, which is to say that its 
existence is controlled by, and only relevant in context of, the Period. It is
distributed and decentralized with respect to the AEAs in the system, all of 
whom run a local node. The underlying consensus engine (at present 
Tendermint) allows decentralized state replication among different processes.
The transitions in the FSM are triggered by the delivery of blocks from the 
consensus engine. The transactions that are contained in these blocks are 
updates of the shared state.

Each round has its own business logic, that specifies how the participants'
transactions are validated or the conditions that trigger a transition to 
another round (e.g. enough votes received for the same value). The transitions 
are triggered by means of _events_, i.e. values that are set by the round 
implementation and are processed by the framework in order to compute the round 
successor.

There are two kinds of events: _normal_ events and _timeout_ events. Normal 
events are set by the round according to certain conditions, whereas timeout 
events are automatically triggered in case the timeout associated to the event 
has expired. The timeout is checked against the "global clock", which is a 
side effect of block validation: each block header carries the timestamp of the 
event of block proposal.

For example, consider a block `b_1` with timestamp `t_1`, and block `b_2` with 
timestamp `t_2 = t_1 + 10s`. Assume that after `b_1` is processed by the 
AbciApp, we are in round `r_1`, and that `r_1` can trigger a timeout event with 
timeout `T=5s`. At the time that `b_2` gets delivered, the timeout event was 
already triggered (`T<t_2`), and the associated transition is already taken in 
the FSM, regardless of the content of `b_2`.

The ABCIApp, through the `ABCIHandler`, receives transactions through the 
[`RequestDeliverTx`](https://docs.tendermint.com/master/spec/abci/abci.html#delivertx)
ABCI requests, and forwards them to the current active round, which produces the
server response. The `end_block` abstract method is called on the ABCI request 
`RequestEndBlock`, and determines the round successor by setting the event to 
take the transition to the next state.

The `Period` class keeps track of an execution of the ABCIApp. It is 
instantiated in the state of the skill and accessible through the skill context.
It is a concrete class, so the developer should not need to extend it.

We remark that the ABCIApp, which resides with the AEA process, is updated by 
the consensus engine through via ABCI requests handled by the ABCIHandler, and 
**NOT** by the AEA behaviours. The AEA behaviours can only send updates through 
the process of sending transactions to the consensus engine.


### ABCIApp diagrams

These sequence diagrams show the sequence of messages and method calls between 
the software components. 

The following diagram describes the addition of transactions to the transaction 
pool:

<div class="mermaid">
    sequenceDiagram
        participant ConsensusEngine
        participant ABCIHandler
        participant Period
        participant Round
        activate Round
        note over ConsensusEngine,ABCIHandler: client submits transaction tx
        ConsensusEngine->>ABCIHandler: RequestCheckTx(tx)
        ABCIHandler->>Period: check_tx(tx)
        Period->>Round: check_tx(tx)
        Round->>Period: OK
        Period->>ABCIHandler: OK
        ABCIHandler->>ConsensusEngine: ResponseCheckTx(tx)
        note over ConsensusEngine,ABCIHandler: tx is added to tx pool
</div>

The following diagram describes the delivery of transactions in a block:

<div class="mermaid">
    sequenceDiagram
        participant ConsensusEngine
        participant ABCIHandler
        participant Period
        participant Round1
        participant Round2
        activate Round1
        note over Round1,Round2: Round1 is the active round,<br/>Round2 is the next round
        note over ConsensusEngine,ABCIHandler: validated block ready to<br/>be submitted to the ABCI app
        ConsensusEngine->>ABCIHandler: RequestBeginBlock()
        ABCIHandler->>Period: begin_block()
        Period->>ABCIHandler: ResponseBeginBlock(OK)
        ABCIHandler->>ConsensusEngine: OK
        loop for tx_i in block
            ConsensusEngine->>ABCIHandler: RequestDeliverTx(tx_i)
            ABCIHandler->>Period: deliver_tx(tx_i)
            Period->>Round1: deliver_tx(tx_i)
            Round1->>Period: OK
            Period->>ABCIHandler: OK
            ABCIHandler->>ConsensusEngine: ResponseDeliverTx(OK)    
        end
        ConsensusEngine->>ABCIHandler: RequestEndBlock()
        ABCIHandler->>Period: end_block()
        alt if condition is true
            note over Period,Round1: replace Round1 with Round2
            deactivate Round1
            Period->>Round2: schedule
            activate Round2
        end
        Period->>ABCIHandler: OK
        ABCIHandler->>ConsensusEngine: ResponseEndBlock(OK)
        deactivate Round2
</div>


## Implementation of ABCIApp

The `ABCIApp` provides the necessary interface for implementation of ABCI-based
Finite State Machine applications. Implementation of the `AbciApp` requires the 
developer to implement the class attributes `initial_round_cls`, 
`transition_function` and `final_states` when creating concrete subclasses. The 
`_MetaRoundBehaviour` metaclass is used to enforce this during implementation
by the developer.

```python
# skills.abstract_round_behaviour.base.py


AppState = Type[AbstractRound]
AbciAppTransitionFunction = Dict[AppState, Dict[EventType, AppState]]
EventToTimeout = Dict[EventType, float]


class AbciApp(
    Generic[EventType], ABC, metaclass=_MetaAbciApp
):  
    """Base class for ABCI apps."""

    initial_round_cls: AppState
    initial_states: Set[AppState] = set()
    transition_function: AbciAppTransitionFunction
    final_states: Set[AppState] = set()
    event_to_timeout: EventToTimeout = {}

    def __init__(
        self,
        state: BasePeriodState,
        consensus_params: ConsensusParams,
    ):
        """Initialize the AbciApp."""
        
    def process_transaction(self, transaction: Transaction) -> None:
        """Process a transaction."""

    def process_event(self, event: EventType, result: Optional[Any] = None) -> None:
        """Process a round event."""

    def update_time(self, timestamp: datetime.datetime) -> None:
        """Observe timestamp from last block."""
    ...
```

Some of its methods relate to concepts discussed in the [previous section](./fsm.md):

- `process_transaction` <br/> 
  for processing the payload generated by the agents during a round.
- `process_event` <br/> 
  allows for the execution of transitions to the next round based on the output
  of the current round.
- `update_time` <br/> 
  allows for resetting of timeouts based on the timestamp from last 
  block. This is the only form of synchronization of time that exists in this 
  system of asynchronously operating AEAs, an understanding of which is 
  indispensable to a developer that needs to implement any sort of 
  [time-based](https://valory-xyz.github.io/open-aea/agent-oriented-development/#time) 
  logic as part of their agents' behaviour.


A concrete implementation of a subclass of `AbciApp` looks as follows:

```python
class MyAbciApp(AbciApp):
    """My ABCI-based Finite-State Machine Application execution behaviour"""
  
    initial_round_cls: AppState = RoundA
    initial_states: Set[AppState] = set()
    transition_function: AbciAppTransitionFunction = {
        RoundA: {
            Event.DONE: RoundB,
            Event.ROUND_TIMEOUT: RoundA,
            Event.NO_MAJORITY: RoundA,
        },
        RoundB: {
            Event.DONE: FinalRound,
            Event.ROUND_TIMEOUT: RoundA,
            Event.NO_MAJORITY: RoundA,
        },
        FinalRound: {},
    }
    final_states: Set[AppState] = {FinalRound}
    event_to_timeout: EventToTimeout = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    ...
```

The `initial_states` are optionally provided by the developer, if none are 
provided the `initial_round_cls` is inferred to be the initial state.
When we process an `Event` we schedule the next round, find the associated 
next events from the `transition_function` and set the associated timeouts, if 
any. Once the [Application BlockChain Interface](./abci.md) application is 
implemented, the application requires `AbstractRoundBehaviour` to enact the 
state transition logic contained in it.


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


## Implementation of `AbstractRoundBehaviour` `

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

