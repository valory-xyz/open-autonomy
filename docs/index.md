# Consensus Algorithms

Consensus algorithms implements the {{valory_stack}}, which allows for the creation of _{{valory_app}}s_: autonomous applications that can be operated in a robust, transparent and decentralized way. The stack is realized on top of the
{{open_aea}} framework, and it facilitates the creation of dynamic, decentralized applications that run off-chain.

As opposed to traditional smart contracts, {{valory_app}}s go beyond simple, purely
reactive applications and can show complex, proactive behaviours that contain
off-chain logic without giving up on decentralization.

## How it Works

{{open_aea}} is a multi-agent system (MAS) framework for building
arbitrary agent-based apps. The {{valory_stack}} extends this framework to a service architecture, where applications are implemented
as sets of agents. A {{valory_app}} defines a series of steps that each agent
in the service must agree upon. At the end of every step, the agents must reach consensus on its outputs. This ensures that the execution flow, its
inputs and its outputs are replicated across all agents, creating a distributed and
decentralized application with shared state that is fault tolerant.

If at some point the application must execute an action involving an external service, e.g.,
settling a transaction on a blockchain, one of the agents is randomly nominated to perform that action. The nominated agent is known as a _keeper_. The nomination process is also agreed by consensus, and multi-signature protocols are used to avoid that a single, malicious agent executes an external action on its own.
For this reason, there is the requirement that a minimum number of agents approve and sign every action before it takes place, and it also must be verified once it has been processed. The threshold on the minimum number of agents is typically set at 2/3 of the total of agents.

## Where to Start

We recommend that new users of the {{valory_stack}} start reading the the [_Get Started_](./get_started.md) section, which should give a general overview about how {{agent_service}}s are implemented with the stack.

Following that introduction, the reader can proceed to explore the core concepts that make {{valory_app}}s possible, presented in the _Preliminaries_ section:

- _Autonomous economic agent (AEA)_ and _multi-agent system (MAS)_,
- _Finite-state machine (FSM)_,
- _Application BlockChain Interface (ABCI)_.

These concepts will be the starting point before exploring more advanced parts of the documentation.
