
Departing from the notions of [AEA](./aea.md), [FSM](./fsm.md), and [ABCI](./abci.md), we are now in position to describe in more detail what an {{fsm_app}} is.


## Definition of an {{fsm_app}}
An {{fsm_app}} is a replicated appliation which uses
an underlying consensus engine implementing the [ABCI](./abci.md).
Its internal state takes the form of an FSM, and it exhibits proactive behaviours in each of such states.
{{fsm_app}}s constitute a core part in the {{valory_stack}} to implement multi-agent based services.

The figure below depicts an sketch of the internal workings of an {{fsm_app}}, composed of six states (A-F) and six events (1-6):

<figure markdown>
  ![](./images/fsm.svg){align=center}
  <figcaption>Diagram of a Valory stack FSM</figcaption>
</figure>

Note that in an {{fsm_app}}, the responsibility of a state is distributed across two components, as it can be seen in the "zoomed" State C above:

- A _round_ is the component that defines the rules to transition across different
  states. It is a concrete implementation of the `AbstractRound` class. It usually involves
  interactions between participants, although this is not enforced
  at this level of abstraction. A round can validate, store and aggregate data
  coming from different agents by means of transactions. The actual meaning of
  the data depends on the implementation of the specific round. This component
  produces the `Events` that will enable the FSM transit from one state to another, that is, capturing the role of the transition function.

- Each round has an associated _Behaviour_, which is the component that defines the proactive actions to be executed at
  a particular state. It is a concrete implementation of the `BaseState` class, and contains the application logic for each state. It is scheduled for
  execution by the agents.

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

## Composition of {{fsm_app}}s
One of the key features of the {{valory_stack}} is the generation of {{fsm_app}}s whose internal FSM is a composition of different FSMs. The composition mechanism facilitates
rapid development of complex applications, by reusing FSMs already developed for other {{fsm_app}}s, obtaining the aggregated functionality.

Departing from a collection of FSMs, say FSM1, FSM2, ..., FSM$n$, a composed FSM can be constructed following certain rules:

1. when composing FSMs, an FSM$i$ can only transit from a final state to a start state of another FSM$j$, and
2. a given FSM can only be used once in a composition.

We call _FSM composition mapping_ the mapping that indicates how to move from one FSM to another.
For every entry in the FSM composition mapping, e.g., from a final state $Z$ from FSM1 to a start state $A$ from FSM2, the composition mechanism will enforce that all the transitions ending in the final state $Z$ of FSM1 be redirected to the start state $A$ of FSM2. See an example below.

<figure markdown>
  ![](./images/fsm_composition.svg){align=center}
  <figcaption>How the FSM composition process works</figcaption>
</figure>

The figure above depicts an excerpt of a composition of three FSMs into a single one. Note how the finish states of FSM1 are linked to start states of FSM2 and FSM3. We remark that the transitions indicated by the FSM composition mapping are not regular transitions that respond to events, rather they are merely a construct to indicate how the states in the composed FSM are connected.

!!! warning "Important"

    The result of a composition of a collection of FSMs is an FSM whose set of spaces is a subset of the union of state spaces of the constituent FSMs. For this reason is it not possible to "reuse" a given FSM twice in a composition. All the final states of the constituent FSMs that are defined in the transition mapping will be removed, as exemplified in the figure above.

    Therefore, althought it might be useful and intuitive thinking of a composed FSM in terms of its constituent FSMs, the structure is not retained internally by the {{fsm_app}}. For example, consider the following setting:

    <figure markdown>
      ![](./images/fsm_composition_2.svg){align=center}
      <figcaption>FSM composition with two sources</figcaption>
    </figure>

    Note that in the composed FSM, when transitioning to A3, the FSM loses track of what was the FSM from which it transitioned (either FSM1 or FSM2). Nevertheless, if the business logic in state A3 requires knowledge of what was the history of visited states before reaching it (e.g., in order to execute a different action), the developer has access to that history through the field `_previous_rounds` from the class [`AbciApp`](./abci_app_class.md) which will be discussed in a separate section.
