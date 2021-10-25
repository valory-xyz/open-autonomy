In this section, we describe more closely the 
ABCI-based Finite-State Machine App (ABCIApp), 
the Finite-State Machine Behaviour (AbstractRoundBehaviour),
and the interplay between the two.

It is recommended to read [this page](./abci.md)
in order to have a good understanding of what
is a generic ABCI application, and how it interacts with 
a consensus engine. 

## ABCIApp: ABCI-based replicated FSM

The `ABCIApp` is a finite-state machine 
implemented as an ABCI Application, 
that defines the finite-state machine 
of a period of the consensus on a temporary blockchain.
We call _round_ a state in an ABCIApp, and _period_ an execution of 
the ABCIApp. The state of the ABCIApp is updated through transactions
in the blockchain.
The underlying consensus engine (at present Tendermint) allows decentralized 
state replication among different processes.
The transitions of such FSM are triggered by the delivery of blocks
from the consensus engine. 
The transactions, sent by the agents' FSMBehaviour, 
perform state updates and eventually trigger the transitions of the
ABCIApp.

Each round has its own business logic,
that specifies how the participants' transactions are validated
or the conditions that trigger a transition to another round 
(e.g. enough votes received for the same value).
The transitions are triggered by means of _events_, i.e. values
that are set by the round implementation and 
are processed by the framework in order to compute the round successor.

There are two kinds of events: _normal_ events and _timeout_ events.
Normal events are set by the round according to certain conditions,
whereas timeout events are automatically triggered in case the
timeout associated to the event has expired. The timeout
is checked against the "global clock", which is a side-effect
of block validation: each block header carries the timestamp 
of the event of block proposal.

For example, consider a block $b_1$ with timestamp $t_1$, 
and block $b_2$ with timestamp $t_2 = t_1 + 10s$.
Assume that after $b_1$ is processed by the AbciApp, we are 
in round $r_1$, and that $r_1$ can trigger a timeout event
with timeout $T=5s$. At the time that $b_2$ gets delivered,
the timeout event was already triggered ($T<t_2$), and the associated
transition is already taken in the FSM, regardless of the 
content of $b_2$.


### ABCIApp in the `valory/abstract_round_abci` skill

The `valory/abstract_round_abci` skill provides several code abstractions
in order to make it easier for developers to implement ABCIApps.

The `Transaction` is a class that represents an ABCIApp transaction.
It is composed of:

- a _payload_ and 
- a _signature_ of the payload.

The payload is an instance of a subclass of the abstract class `BaseTxPayload`. 
Concrete subclasses of `BaseTxPayload` specify the allowed transaction payloads
and depend on the actual use case. The signature is an
Ethereum digital signature of the binary encoding of the payload.

In our code, the core abstraction that represents the ABCIApp is the `AbciApp` base class.
It relies on the `AbstractRound` building block (more below).
Concrete classes of `AbciApp` must specify:

- `initial_round_cls`: a concrete class of `AbstractRound` that determines the initial round of the FSM;
- `transition_function`: a nested mapping from state to another mapping from events to successor states; 
- `event_to_timeout`: a mapping from event to its associated timeout; it implicitly defines the set of normal events and timeout events.

Concrete subclasses of `AbstractRound` specify a round (i.e. a state), of the ABCIApp.
A round can validate, store and aggregate data coming from different participant by means of
transactions. The actual meaning of the data depends on the round and the specific
use case, e.g. measurement of a quantity from different data sources,
votes for reaching distributed consensus on a certain value.
ABCI requests are received through the `ABCIConnection` and handled
by the `ABCIHandler`. Therefore, the `ABCIHandler` handler, together with the `ABCIConnection`,
acts as an ABCI server.
The ABCIApp, through the `ABCIHandler`, receives transactions through the 
[`RequestDeliverTx`](https://docs.tendermint.com/master/spec/abci/abci.html#delivertx)
ABCI requests, and forwards them to the current active round,
which produces the server response. 
The `end_block` abstract method is called on the ABCI request 
`RequestEndBlock`, and determines the round successor
by setting the event to take the transition to the next state.

The `Period` class keeps track of an execution of the ABCIApp.
It is instantiated in the state of the skill and accessible
through the skill context.
It is already a concrete class, so the developer should not need
to extend it.

We remark that the ABCIApp, which resides into the AEA process,
is updated by the consensus engine
through the ABCI requests handled by the ABCIHandler, and **NOT** by the AEA behaviours.
The AEA behaviours can only send updates through the process of sending transactions
to the consensus engine.

### ABCIApp diagrams

These sequence diagrams show the sequence of messages
and method calls between the software components. 

The following diagram describes the addition of transactions to the transaction pool:
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

## FSMBehaviour

The FSMBehaviour is an AEA Behaviour that is closely related
to an ABCIApp. It utilizes the ABCIApp as state-replication
layer among different AEA participants. Notably, the ABCIApp changes states only
by means of transaction committed by the AEAs to the temporary blockchain,
and in this sense is "purely reactive";
instead, the FSMBehaviour execution also shows "proactive logic".
For example, the FSMBehaviour of each AEA can observe the price value of BTC
from an external source, AEAs can use the ABCIApp to replicate the observations, and then reach the consensus on an estimate,
and submit the estimate on the Ethereum blockchain
(as done in the 
[price estimation demo](./price_estimation_demo.md));
each step represents a 'state' of the FSMBehaviour.

The FSMBehaviour can be seen as a _client_ of the ABCIApp (in that sense it encapsulates the "user" of a normal blockchain),
although the ultimate goal is to provide services to external
users or other systems. Continuing the example above, the FSMBehaviour that periodically
submits the average BTC price on the Ethereum blockchain can be 
seen as a BTC price [oracle service](https://ethereum.org/en/developers/docs/oracles/).


### FSMBehaviour in the `valory/abstract_round_abci` skill

The FSMBehaviour abstraction is represented
in the code by the `AbstractRoundBehaviour` abstract class,
which implements the [`Behaviour` interface](https://fetchai.github.io/agents-aea/api/skills/behaviours).

The states of the `AbstractRoundBehaviour` behaviour are of type `BaseState`,
a base class with several utility methods to make developer's life easier.
In particular, it inherits from [`AsyncBehaviour`](./async_behaviour.md),
and so the methods can use the asynchronous programming paradigm.

Concrete classes of the `BaseState` class must specify the 
`matching_round` class attribute, which indicates the `AbstractRoundBehaviour`
the ABCIApp round associated with the state behaviour. This is 
useful to check whether the state behaviour should be changed
according to the current ABCIApp round. 

A concrete class of `AbstractRoundBehaviour` looks like:

```python
class MyFSMBehaviour(AbstractRoundBehaviour):
    abci_app_cls = MyAbciApp
    behaviour_states = {
      StateA,
      StateB,
      ...
    }
    initial_state_cls: StateA

```

Where:

- `abci_app_cls` is the `AbciApp` concrete class associated to this behaviour
- `initial_state_cls` is the class of the initial state of the FSM;
- `behaviour_states` is the set of `BaseState` concrete classes that constitute
  the FSMBehaviour.

The transitions are not set by the developer; rather, the execution
of the FSMBehaviour slavishly follows the underlying AbciApp.
Whenever a round change in the AbciApp is detected, the `AbstractRoundBehaviour`
promptly schedules the state behaviour associated to the current round,
by preemptively replacing the current state behaviour.
In this way, the FSMBehaviour is always in the correct state behaviour
according to the current period.

### FSMBehaviour diagrams

The following diagram shows how the FSM behaviour works
together with the AEA event loop.

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

## ABCIApp-FSMBehaviour interaction

The interaction between the FSMBehaviour 
(i.e. the `AbstractRoundBehaviour` in the code)
and the ABCIApp
(i.e. executions of the `AbciAbstractRound` in the code)
happens through the consensus engine and 
the shared state among the concrete skill of 
the `valory/abstract_abci_round` abstract skill.

In particular, the usual workflow looks like this:

1. At setup time, the consensus engine node creates connections
  with the associated AEA and sync together. 
  In the AEA process, the ABCIApp starts from the first round, 
  waiting for transactions to update its state. 
  The FSMBehaviour schedules the initial state behaviour 
  for execution of the `act` method.
2. The current state behaviour sends transactions to update
  the state of the ABCIApp, and once its job is done waits until
  the ABCIApp changes round, by checking read-only attributes of the ABCIApp,
  accessible through the AEA's skill context. Observe that it is crucial
  that the behaviour cannot update the ABCIApp state as it should only 
  be updated by the consensus engine node.
  The state behaviour may eventually repeat the job, 
  according to the business logic and error handling.
3. Once the transaction gets added
  into a block accepted by the consensus engine, the consensus engine node
  delivers the block and its transaction(s) to the ABCIApp, through the AEA's ABCIConnection
  and ABCIHandler. The ABCIApp processes the transaction and, if the business
  logic implemented by the ABCIApp satisfies the conditions to make a transition,
  the ABCIApp changes round.
4. The round change of the ABCIApp is detected by the state behaviour, which
  stops the waiting loop. The FSMBehaviour, according to the current
  ABCIApp, schedules the next state behaviour.
5. Repeat the steps above from (2) until a final state is reached.