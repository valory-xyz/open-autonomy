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
transactions committed to a temporary blockchain.

This ledger is local with respect to the `Period`, which is to say that its
existence is controlled by, and only relevant in context of, the Period. It is
distributed and decentralized with respect to the AEAs in the system, all of
whom run a local node. The underlying consensus engine (at present
Tendermint) allows decentralized state replication among different processes.
The transitions in the FSM are triggered by the delivery of blocks from the
consensus engine. The transactions that are  contained in these blocks are submitted by the agents, and can lead to updates of the shared state.

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
the consensus engine through ABCI requests handled by the ABCIHandler, and
**NOT** by the AEA behaviours. The AEA behaviours can only send updates through
the process of sending transactions to the consensus engine.