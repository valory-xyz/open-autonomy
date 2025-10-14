An **AI agent** is an off-chain autonomous service which runs as a multi-agent-system (MAS) and is crypto-economically secured on a public blockchain.

AI agents enable complex processing, take action on their own and run continuously. Moreover, AI agents are crypto-native by construction, that is, they are **decentralized**, **trust-minimized**, **transparent**, and **robust**.

See [some use cases](./use_cases.md) of AI agents that can be built with the {{open_autonomy}} framework.

## Architecture

The {{open_aea}} framework provides the necessary components for building single agent blueprints. {{open_autonomy}} extends this framework to an AI agent architecture, making possible to build applications as distributed systems (that is, AI agents) that can be run by multiple, independent operators.

The internal state of an AI agent is replicated across all the agent instances in the AI agent through a **consensus gadget** (a sort of short-lived blockchain).

This is what an AI agent looks like:

<figure markdown>
![Architecture of an AI agent](../images/agent_service_architecture.svg)
</figure>

* **AI agent**: The decentralized off-chain service that implements a certain functionality. It is composed of $N$ agent instances, where $N$ is a parameter that is defined by the owner of the AI agent.

* **Operator**: An entity or individual that owns the infrastructure where an agent instance is run. Each operator manages an agent instance and a consensus gadget node.

* **Agent**: The software unit that aggregates the runtime and functionalities to execute the AI agent. Each agent blueprint is made up of a number of components that implement different functionalities, for example, what communication protocols the agent blueprint understands.

* **{{fsm_app}}**: The core component inside an agent blueprint that defines the business logic of the AI agent. {{fsm_app}} implements the underlying mechanisms for agent isntances to synchronize their internal state and run the business logic in a decentralized fashion.

* **Consensus gadget:** The infrastructure that enables agent instances to synchronize the AI agent state and reach consensus on certain important decisions. From a technical point of view, the consensus gadget implements a blockchain based on [Tendermint](https://tendermint.com/) that is pruned periodically. By consensus gadget we usually refer to the collection of consensus nodes + consensus network.

* **AI agent multisig [Safe](https://safe.global/):** Smart contract based Multisig that secures the AI agent by requiring a threshold of agent instances to sign any transaction before it is executed.

## How it works

The {{fsm_app}}, which encodes the business logic of the AI agent, is structured as a [finite-state machine](../key_concepts/fsm.md) defining a series of steps that each agent instance in the AI agent must follow in order to achieve the intended functionality.

!!! example

    This is a _toy example_ of how an {{fsm_app}} defines the business logic of an oracle AI agent that collects prices from a source and publishes it on a blockchain:

    <figure markdown>
    ![Oracle {{fsm_app}} - toy example](../images/toy_oracle_fsm_app.svg)
    </figure>

The {{fsm_app}} replicates automatically the state and transitions across agent instances using the consensus gadget. This ensures that the execution flow of the AI agent, its inputs and outputs are synchronized across all instances, creating a distributed (and decentralized) application with shared state that is fault tolerant.

!!! tip

    When developing an AI agent, the developer can focus on defining the steps of the AI agent in the {{fsm_app}} as if it were a standalone application, and get the replication mechanism "for free".

    The {{open_autonomy}} framework will provide most of the machinery to ensure that the agent instances' state is replicated as the AI agent is executed.

If at some point the AI agent needs to execute an action involving an external service, e.g., settling a transaction on a blockchain, then the following occurs:

1. The agent instances in the AI agent nominate by consensus an instance (known as **keeper**) to perform the action.
2. A threshold of agent instances has to approve and sign the transaction, using the AI agent multisig [Safe](https://safe.global/). This prevents a malicious agent instance from executing an external action on its own.
3. Furthermore, the agent instances in the AI agent verify that the transaction was executed successfully. Otherwise, a new keeper will be nominated and the transaction will be retried.

The threshold on the minimum number of agent instances required to sign is typically, but not exclusively, set at 2/3 of the total of instances.
