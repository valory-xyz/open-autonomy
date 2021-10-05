In this section, we describe more closely the 
ABCI-based Finite-State Machine App (ABCIApp), 
the Finite-State Machine Behaviour (FSMBehaviour),
and the interplay between the two in the [price estimation demo](./price_estimation_demo.md).

## ABCIApp: ABCI-based replicated FSM

The `ABCIApp` is a finite-state machine 
implemented as an ABCI Application, 
that defines the finite-state machine 
of a period of the consensus on a temporary blockchain.
The underlying consensus engine (at present Tendermint) allows decentralized 
state replication among different processes.
The transitions of such FSM are triggered by the delivery of blocks
from the consensus engine. 
The transactions, sent by the agents' FSMBehaviour, 
perform state updates and eventually trigger the transitions of the
ABCIApp.

### ABCIApp in the Price Estimation demo

TODO

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
seen as a BTC price oracle service.


### FSMBehaviour in the Price Estimation demo

TODO

## ABCIApp-FSMBehaviour interaction

TODO

### ABCIApp-FSMBehaviour interaction in the Price Estimation demo

TODO