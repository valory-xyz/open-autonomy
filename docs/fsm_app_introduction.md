
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

    A period, on the other hand, consists of a sequence of such stages in the FSM state flow that achieve a specific objective defined by the {{fsm_app}}. Consider the price oracle demo, which aggregates asset prices from different data sources and submits the aggregated result to an L1/L2 blockchain. In this example a period is defined as follows:

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
