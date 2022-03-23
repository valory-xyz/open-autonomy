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
as sets of agents. A Valory app can be thought as a series of steps that every agent
that makes up the service must agree upon. At the end of evey step, consensus must
be reached on its outputs. This way, the execution flow as well as its
inputs and outputs are replicated across all agents, creating a distributed and
decentralized application with shared state that is fault tolerant.

Even if at some point the application must take some action over an external service, i.e.
settle a transaction on a blockchain, one of the agents can be randomly nominated as a keeper
to perform that action. Multi-signature software can be used to avoid unilateral actions
being taken, so all of the agents must approve and sign every action before it takes place and verify it once it has been processed.


