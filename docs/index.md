# Consensus algorithms

Consensus algorithms implements the {{valory_stack}}, which allows for the creation of _{{valory_app}}s_: autonomous applications that can be operated in a robust, transparent and decentralized way. The stack is realized on top of the
{{open_aea}} framework, and it facilitates the creation of dynamic, decentralized applications that run off-chain.

As opposed to traditional smart contracts, {{valory_app}}s go beyond simple, purely
reactive applications and can show complex, proactive behaviors that contain
off-chain logic without giving up on decentralization.

## How it works

{{open_aea}} is a multi-agent system (MAS) framework for building
arbitrary agent-based apps. The {{valory_stack}} extends this framework to a service architecture, where applications are implemented
as sets of agents. A {{valory_app}} defines a series of steps that each agent
in the service must agree upon. At the end of every step, the agents must reach consensus on its outputs. This ensures that the execution flow, its
inputs and its outputs are replicated across all agents, creating a distributed and
decentralized application with shared state that is fault tolerant.

If at some point the application must execute an action involving an external service, e.g.,
settling a transaction on a blockchain, one of the agents is randomly nominated to perform that action. The nominated agent is known as a _keeper_. The nomination process is also agreed by consensus, and multi-signature protocols are used to avoid that a single, malicious agent executes an external action on its own.
For this reason, there is the requirement that a minimum number of agents approve and sign every action before it takes place, and it also must be verified once it has been processed. The threshold on the minimum number of agents is typically set at 2/3 of the total of agents.

There are some core concepts that make {{valory_app}}s possible, and we will be discussing them in the following sections. Namely:

- _Autonomous economic agent (AEA)_ and _multi-agent sytem (MAS)_,
- _Finite-state machine (FSM)_,
- _Application BlockChain Interface (ABCI)_.
