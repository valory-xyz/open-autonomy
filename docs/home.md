# Consensus algorithms

Consensus algorithms implements the [Valory](https://www.valory.xyz/) stack, which allows for the creation of autonomous applications that can be operated in a robust, transparent and decentralised way. The stack is realised on top of the
[open AEA framework](https://github.com/valory-xyz/open-aea). It facilitates the creation of dynamic, decentralised applications that run off-chain.

As opposed to traditional smart contracts, Valory apps go beyond simple, purely
reactive applications and can show complex, proactive behaviours that contain
off-chain logic without giving up on decentralization.

## How it works

The Valory stack extends open AEA, a multi-agent system (MAS) framework for building
arbitrary agent-based apps, to a service architecture where apps are implemented
as sets of agents. A Valory app defines a series of steps that every agent
that makes up the service must agree upon. At the end of every step, consensus must
be reached on its outputs. This ensures that the execution flow as well as its
inputs and outputs are replicated across all agents, creating a distributed and
decentralized application with shared state that is fault tolerant.

If at some point the application must execute an action involving an external service, e.g.,
settle a transaction on a blockchain, one of the agents is randomly nominated to perform that action. The nominated agent is known as a keeper. Multi-signature protocols are used to avoid that a single, malicious agent executes an action on its own.
For this reason, a threshold of agents must approve and sign every action before it takes place and
verify it once it has been processed.

There are some core concepts that make Valory apps possible. In the following sections
you'll find more information to help you understand how all of them interplay, but here's some
short definitions that can serve as appetizer:

- **Autonomous Economic Agent (AEA)**: intelligent agent acting on behalf of its owner, with limited or no interference, and whose goal is to generate economic value for its owner. Every Valory app is composed of several AEAs that interact between them to achieve the application's goals.
- **Finite State Machine (FSM)**: mathematical model of computation that can be used to represent the sequential logic of state transitions. This lets us define all the steps that an application of service must follow, or in other words: the application's logic.
- **Application Blockchain Interface (ABCI)**: an interface that defines the boundary between the replication/consensus engine and an FSM-based app. It lets the application logic communicate with the consensus engine so that every agent's state is on the same page.
