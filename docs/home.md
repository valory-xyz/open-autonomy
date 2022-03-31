# Consensus algorithms

Consensus algorithms implements the [Valory](https://www.valory.xyz/) stack, which allows for the creation of **Valory apps**: autonomous applications that can be operated in a robust, transparent and decentralised way. The stack is realised on top of the
[open AEA framework](https://github.com/valory-xyz/open-aea), and it facilitates the creation of dynamic, decentralised applications that run off-chain.

As opposed to traditional smart contracts, Valory apps go beyond simple, purely
reactive applications and can show complex, proactive behaviours that contain
off-chain logic without giving up on decentralization.

## How it works

Open AEA is a multi-agent system (MAS) framework for building
arbitrary agent-based apps. The Valory stack extends this framework to a service architecture, where applications are implemented
as sets of agents. A Valory app defines a series of steps that every agent
in the service must agree upon. At the end of every step, the agents must reach consensus on its outputs. This ensures that the execution flow, its
inputs and outputs are replicated across all agents, creating a distributed and
decentralized application with shared state that is fault tolerant.

If at some point the application must execute an action involving an external service, e.g.,
settling a transaction on a blockchain, one of the agents is randomly nominated to perform that action. The nominated agent is known as a keeper. Multi-signature protocols are used to avoid that a single, malicious agent executes an action on its own.
For this reason, a threshold of agents must approve and sign every action before it takes place, and it also must be
verified once it has been processed.

There are some core concepts that make Valory apps possible, and we will be discussing them in the following sections. Namely:

- **Autonomous Economic Agent (AEA)** and **Multi-agent sytems (MAS)**,
- **Finite-State Machine (FSM)**,
- **Application BlockChain Interface (ABCI)**.
