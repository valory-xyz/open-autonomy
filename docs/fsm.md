# Finite State Machines (FSMs)

In this section we review the concept of _finite state machine_ and discuss its role in the definition
of {{fsm_app}}s, and in the operation of AEAs.

A [finite state machine](https://en.wikipedia.org/wiki/Finite-state_machine) (FSM) is a mathematical model of computation that can be
used to represent a sequential logic of state transitions.
We use FSMs to describe systems that have multiple states and can transition from one state to another due to some event or signal. In every state, we will need to perform one or more actions to trigger an event. This event will make the application to transit to a new state.


Therefore, FSMs let us define all the steps that an application of a service must follow, or in other words, the application logic.
At any given time
the FSM can be in exactly one particular state from which it can transition to
other states based on the reception of certain _events_ that it is given. The rules to transition from one state to another are governed by the so-called _transition function_. The transition function takes as input the current state and the received event and outputs the next state where the FSM will transit. A compact way of visualizing an FSM and its transition function is through a
graph with a finite number of nodes, depicting the possible states of the
system, and a finite number of labelled arcs, representing the transitions from one state to another.

As an example, consider an FSM describing a simplified vending machine with three different states:

- _Idle_: the machine is waiting for a customer to insert a coin.
- _Ready_: a coin has been inserted, and the machine is waiting for the customer to select a product, or request a refund.
- _Release_: the machine releases the selected product.

Therefore, the four self-explanatory events of this FSM are:

- COIN_INSERTED
- PRODUCT_SELECTED
- REFUND_REQUEST
- PRODUCT_RELEASED


We can represent the FSM as a graph as follows:

<figure markdown>
<div class="mermaid">
stateDiagram-v2
direction LR
  [*] --> Idle
  Idle --> Ready: COIN_INSERTED
  Ready --> Idle: REFUND_REQUEST
  Ready --> Release: PRODUCT_SELECTED
  Release --> Idle: PRODUCT_RELEASED
</div>
<figcaption>Diagram of a simplified vending machine FSM</figcaption>
</figure>
