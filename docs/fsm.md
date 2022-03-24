# FSM: Finite State Machines

A finite state machine (FSM) is a mathematical model of computation that can be
used to represent the sequential logic of state transitions. At any given time
the FSM can be in exactly one particular state from which it can transition to
other states based on the inputs it is given. An FSM can be represented by a
graph, with a finite number of nodes describing the possible states of the
system, and a finite number of arcs representing the transitions from one state
to another. In this section we discuss the role FSMs play in the construction
of ABCI applications and the operation of AEAs.


## How FSMs come into play

Accepting this is sufficient as a notion on the FSM we may start to think of
what it is that is changing when we transition from one state to another.
States consists of:

- a round: some concrete implementation of `AbstractRound`. It usually involves
  interactions between participants in the period, although this is not enforced
  at this level of abstraction. A round can validate, store and aggregate data
  coming from different agents by means of transactions. The actual meaning of
  the data depends on the implementation of the specific round.
- a behaviour: some concrete implementation of `BaseState`. It is scheduled for
  execution by the agents. Every behaviour is associated with a specific round.
- a period state: some concrete implementation of `BasePeriodState`. It provides
  access to the state data that is shared by the agents throughout the period
  and gets updated each round.


![](./images/fsm.svg)


We define _period_ as a sequence of rounds. A _round_ might just be a stage in
the consensus (e.g. waiting that a sufficient number of participants commit their
observations to the temporary tendermint blockchain), or a voting round (e.g.
waiting till at least one estimate has reached `ceil((2n + 1) / 3)` of the votes).

The data flow in a period can be summarized as follows:
>
    Period with n agents
        1. k rounds of each 3 steps
            a. collect observations from external APIs or prior rounds
            b. share observations untill threshold of 2/3rd is reached
            c. compute on observations, reach consensus on the result
        2. finalization
            after k rounds run a final round for constructions of the
            on-chain transaction submission
        3. sign the transactions, again need 2/3rd majority
        4. a single agent, the keeper, sends the transaction to the
           chain. If the keeper does not do this before a timeout
           event occurs, another agent is selected to be the keeper.
>