In this section, we describe more closely the 
ABCI-based Finite-State Machine App (ABCIApp), 
the Finite-State Machine Behaviour (FSMBehaviour),
and the interplay between the two in the [price estimation demo](./price_estimation_demo.md).

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

Concrete subclasses of `AbstractRound` specify a round (i.e. a state), of the ABCIApp.
A round can validate, store and aggregate data coming from different participant by means of
transactions. The actual meaning of the data depends on the round and the specific
use case, e.g. measurement of a quantity from different data sources,
votes for reaching distributed consensus on a certain value.
The ABCI server receives transactions through the 
[`RequestDeliverTx`](https://docs.tendermint.com/master/spec/abci/abci.html#delivertx)
ABCI requests, and forwards them to the current active round,
which produces the server response. 
The `end_block` abstract method is called on the ABCI request 
`RequestEndBlock`, and determines the round successor according to
the business logic of the ABCIApp.

The `Period` class keeps track of an execution of the ABCIApp.
It is instantiated in the state of the skill and accessible
through the skill context.
It is already a concrete class, so the developer should not need
to extend it.


### ABCIApp sequence diagram

This sequence diagram shows the sequence of messages
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


### FSMBehaviour in the Price Estimation demo

TODO

## ABCIApp-FSMBehaviour interaction

TODO

### ABCIApp-FSMBehaviour interaction in the Price Estimation demo

TODO