# Consensus algorithms

Consensus algorithms implements the [Valory](https://www.valory.xyz/) stack, a set of
distributed consensus technologies built on top of the
[open AEA framework](https://github.com/valory-xyz/open-aea) to facilitate the
creation of dynamic, decentralised applications that depend on off-chain components.

As opposed to traditional smart contracts, Valory apps go beyond simple, purely
reactive applications and can show complex, proactive behaviours that contain
off-chain logic without giving up on decentralization.

## How it works

The Valory stack extends open AEA, a multi-agent system (MAS) framework for building
arbitrary agent-based apps, to a service architecture where apps are implemented
as sets of agents. A Valory app can be thought of as a series of steps that every agent
that makes up the service must agree upon. At the end of evey step, consensus must
be reached on its outputs. This way, the execution flow as well as its
inputs and outputs are replicated across all agents, creating a distributed and
decentralized application with shared state that is fault tolerant.

If at some point the application must take some action over an external service, i.e.
settle a transaction on a blockchain, one of the agents can be randomly nominated as a keeper
to perform that action. Multi-signature software can be used to avoid unilateral actions
being taken, so all of the agents must approve and sign every action before it takes place and
verify it once it has been processed.

There are some core concepts that make Valory apps possible. In the following sections
you'll find more information to help you understand how all of them interplay, but here's some
short definitions that can serve as appetizer:

- **Autonomous Economic Agents (AEAs)**: intelligent agents acting on an owner's behalf, with limited or no interference, and whose goal is to generate economic value for its owner. Every Valory app is composed of several AEAs that interact to achieve the application's goal.
- **Finite State Machines (FSMs)**: mathematical models of computation that can be used to represent the sequential logic of state transitions. This lets us define all the steps that an application of service must follow, or in other words: the application's logic.
- **Application Blockchain Interface (ABCI)**: an interface that defines the boundary between the replication/consensus engine and the state machine. It lets the application logic communicate with the consensus engine so every agent's state is on the same page.
