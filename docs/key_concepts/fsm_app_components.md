[← Back to Key Concepts](./index.md)

There are a number of important concepts that will be introduced in this section so that the developer understands how [FSM App](./fsm_app_introduction.md)s work. Namely:

Core classes that instrument the [FSM App](./fsm_app_introduction.md):

- `AbciApp` class: The base class that defines the FSM transitions in an [FSM App](./fsm_app_introduction.md).
- `AbstractRoundBehaviour` class: The base class defining the overall [FSM App](./fsm_app_introduction.md)s behaviour.

Classes that define the operations per state of the FSM:

- `AbstractRound` class: The base class to define the FSM state rounds of the [FSM App](./fsm_app_introduction.md).
- `AsyncBehaviour` class: The base class to define FSM state behaviours to be executed during each round in the [FSM App](./fsm_app_introduction.md).

Other classes related to the [FSM App](./fsm_app_introduction.md) FSM global state:

- `SynchronizedData` class: The class providing
access to the shared state.



## How [FSM App](./fsm_app_introduction.md)s work

The `AbciApp` class defines the constituent FSM of the [FSM App](./fsm_app_introduction.md). That is, it defines the set of start and final states (rounds) and the transition function.
<!-- We call _round_ a state in an ABCIApp, and _period_ an execution of the `ABCIApp`. -->

The state of the [FSM App](./fsm_app_introduction.md) is updated through
transactions committed to the temporary blockchain.
This ledger is local with respect to the `Period`, i.e., its
existence is controlled by, and only relevant in context of, the `Period`. It is
distributed and decentralized with respect to the AEAs in the system, all of
whom run a local consensus node. The underlying consensus engine (currently
CometBFT) allows decentralized state replication among different processes.

The transitions in the FSM are triggered by the delivery of blocks from the
consensus engine through the [ABCI](./abci.md). The transactions that are contained in these blocks are submitted by AEAs `Behaviours`, and can lead to updates of the shared `SynchronizedData`.

Each round has its own business logic, which specifies how the participants'
transactions are validated or the conditions that trigger a transition to
another round (e.g., enough votes received for the same value). The transitions
are triggered by means of _events_, i.e., values that are set by the round
implementation and are processed by the framework in order to compute the round
successor.

There are two kinds of events: _normal events_ and _timeout events_:

- Normal events are set by the round according to certain conditions that are checked during the execution of a round. These conditions can be defined arbitrarily according to the business logic of the [FSM App](./fsm_app_introduction.md).

- Timeout events are automatically triggered in case the timeout associated to
the event has expired. The timeout is checked against the "global clock", which
is a side effect of block validation: each block header carries the timestamp of the event of block proposal.

!!! Example
    A normal event can

    On the other hand, consider a block $B_1$ with timestamp $t_1$, and block $B_2$ with
    timestamp $t_2 = t_1 + 10$ seconds. Assume that after $B_1$ is processed, the
    [FSM App](./fsm_app_introduction.md) current state round is defined to trigger a timeout event set at  $T=5$ seconds. When $B_2$ is delivered, the timeout event had already been triggered (because $T<t_2-t_1$), and the associated transition had already happened in the FSM, regardless of the content of $B_2$.

The `ABCIHandler`, is in charge of receiving the transactions through the
[`DeliverTx`](https://docs.cometbft.com/v0.37/spec/abci/abci++_methods#delivertx)
ABCI requests, and forwards them to the current active round, which produces the
response for `DeliverTx`. The `end_block` abstract method is called on the ABCI request `EndBlock`, and determines the round successor by setting the event to
take the transition to the next state, as defined by the transition function in the `AbciApp`.

!!! warning "Important"

    We remark that the [FSM App](./fsm_app_introduction.md), which resides inside the AEA, is updated by
    the consensus engine through the [ABCI](./abci.md) requests handled by the `ABCIHandler`, and
    **NOT** by the AEA behaviours. The AEA behaviours can only send updates through
    the process of sending transactions to the consensus engine.

The `Period` class keeps track of an execution of the [FSM App](./fsm_app_introduction.md). It is
instantiated in the state of the `Skill` and accessible through the `SkillContext`.
It is a concrete class, so the developer should not need to extend it.
