A [finite-state machine](https://en.wikipedia.org/wiki/Finite-state_machine) (FSM) is a mathematical model of computation that can be
used to represent a sequential logic of state transitions.
We use FSMs to describe systems that have a finite number of _states_ and can transition from one state to another due to some _event_. At any given time the FSM can be in exactly one particular state, and the reception of this event will make the application to transit to a new state. FSMs will be a central part to define the {{fsm_app}} in an agent service (because we express the business logic of such services as FSMs).

The rules to transition from one state of the FSM to another are governed by the so-called _transition function_. The transition function takes as input the current state and the received event and outputs the next state where the FSM will transit. A compact way of visualizing an FSM and its transition function is through a multi
digraph with a finite number of nodes, depicting the possible states of the system, and a finite number of labelled arcs, representing the transitions from one state to another.

!!! note "Example"
    Consider an FSM describing a simplified vending machine with three different states:

    - _Idle_: the machine is waiting for a customer to insert a coin.
    - _Ready_: a coin has been inserted, and the machine is waiting for the customer to select a product, or request a refund.
    - _Release_: the machine releases the selected product.

    Therefore, the four self-explanatory events of this FSM are:

    - COIN_INSERTED
    - PRODUCT_SELECTED
    - REFUND_REQUEST
    - PRODUCT_RELEASED


    We can represent the FSM as a multi digraph as follows:

    <div class="mermaid">
    stateDiagram-v2
    direction LR
      [*] --> Idle
      Idle --> Ready: COIN_INSERTED
      Ready --> Idle: REFUND_REQUEST
      Ready --> Release: PRODUCT_SELECTED
      Release --> Idle: PRODUCT_RELEASED
    </div>

    Or alternatively, using its transition function:

    | Input                       | Output  |
    |-----------------------------|---------|
    | (Idle, COIN_INSERTED)       | Ready   |
    | (Ready, REFUND_REQUESTED)   | Idle    |
    | (Ready, PRODUCT_SELECTED)   | Release |
    | (Release, PRODUCT_RELEASED) | Idle    |


FSMs let us define all the steps that an application of a service must follow, or in other words, the application logic. Roughly speaking, the {{fsm_app}} defining an agent service is essentially an FSM replicated across the number of AEAs that compose the service, including additional proactive functionalities. Although it is not stritly necessary to understand how {{fsm_app}}s work, you can read more about FSM replication [here](https://en.wikipedia.org/wiki/State_machine_replication).
