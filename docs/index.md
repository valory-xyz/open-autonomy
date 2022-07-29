# Open Autonomy

{{open_autonomy}} is a framework for the creation of _agent services_: off-chain services which run as a multi-agent-system (MAS) and are replicated on a consensus gadget (a sort of short-lived blockchain) while being crypto-economically secured on a public blockchain. Agent services enable complex processing, take action on their own and run continuously. Additionally, agent services are crypto-native by construction, that is, they are decentralized, trust-minimized, transparent, and robust.

The {{open_autonomy}} framework allows to define such services by means of _{{fsm_app}}s_. These dynamic, decentralized apps run inside the agents implementing the agent service, and define its business logic.

The {{open_autonomy}} framework is realized on top of the {{open_aea}} framework, and it consists of:

* A collection of command line tools to build, deploy, publish and  test agent services.
* A collection of packages with base classes to create the {{fsm_app}} that define the service business logic.


<figure markdown>
![](./images/agent_service_architecture.svg)
<figcaption>Overview of the architecture of an agent service</figcaption>
</figure>

## Why?
Decentralized ledger technologies (DLTs), such as blockchains, face several challenges, for example:

* [the blockchain trilemma](https://www.ledger.com/academy/what-is-the-blockchain-trilemma)
* [the oracle problem](https://encyclopedia.pub/entry/2959)
* [privacy issues](https://en.wikipedia.org/wiki/Privacy_and_blockchain)
* [ledger storage space](https://cointelegraph.com/news/how-can-blockchain-improve-data-storage)
* [cross chain compatibility](https://101blockchains.com/blockchain-interoperability/)
* ... and the sheer complexity of the user experience!

In contrast with the increasing growth of on-chain applications (particularly in DeFi), the off-chain design space has seen a lack of innovation. A lot of the technology is centralized, lacks fault tolerance, the code is often opaque and offers little composability.


Currently, a standardised approach for off-chain application development is missing in the blockchain space. This is where the Valory stack (i.e., the {{open_aea}} and the {{open_autonomy}} frameworks) comes in, as an open-source framework for developers to implement off-chain services which are secured on-chain and can interact with smart contracts.


<figure markdown>
![](./images/centralized_decentralized_world.svg)
<figcaption>The Valory Stack allows to develop decentralized, agent services that are run off-chain and are crypto-economically secure</figcaption>
</figure>


Agent services go beyond simple, purely
reactive applications (like smart contracts) and can show complex, proactive behaviours that contain off-chain logic without giving up on decentralization. Examples include, but are not limited to, triggering specific actions on external events, or even executing complex machine learning models.


## How It Works

{{open_aea}} is a framework for building arbitrary agent-based applications. It provides the elements to define and implement the required components of an agent, e.g., connections, protocols or skills.

On the other hand, the {{open_autonomy}} framework extends {{open_aea}} to a service architecture. That is, it allows to build applications as distributed systems (agent services) run by sets of agents.

The {{fsm_app}} that defines the service business logic is structured as a series of steps that each agent in the service must follow in order to achieve the service functionality. Agents must reach consensus on the outcome of each step. This ensures that the execution flow, its inputs and outputs are replicated across all agents, creating a distributed (and decentralized) application with shared state that is fault tolerant. The shared state is replicated across agents automatically through the consensus gadget. From an architectural point of view, the {{fsm_app}} is implemented as a particular type of agent component.

If at some point the {{fsm_app}} must execute an action involving an external service, e.g.,
settling a transaction on a blockchain, one of the agents is randomly nominated to perform that action. The nominated agent is known as a _keeper_. The nomination process is also agreed by consensus, and multi-signature protocols are used to avoid that a single, malicious agent executes an external action on its own.
For this reason, there is the requirement that a minimum number of agents approve and sign every action before it takes place, and it also must be verified once it has been processed. The threshold on the minimum number of agents is typically, but not exclusively, set at 2/3 of the total of agents.

## Agent Services Vs. Single-Agent Applications

Sometimes, there is the question whether is it best to design an application as single-agent or as an agent service. This is often a question that new developers in the field of agent systems and MAS face. We provide below a comparison table which hopefully will give you some guidance on which of the both approaches is best for your use case.

|       | Single-agent application             | Agent service |
| ----------- | ------------------------------------ | --- |
| Scope | An application designed to pursue the interests and objectives of a single entity. | An application designed to offer services that external users can benefit from. |
| Value generation model | The application is in charge of generating economic value for its owner. | Service operators might charge a fee to their users. |
| Architecture & Execution | A single agent, typically run and controlled by a single entity. | A set of agents run by a collection of independent operators. Agents have a synchronized shared state. |
| Trust model | Not applicable. The owner controls and designs and manages their own agent. | Agent services are decentralized and transparent, and can be crypto-economically secured on a public blockchain. They can be regarded as drop-in replacements of trusted entities, thus relaxing the trust requirements on them. |
| Example | Automated, personal asset management: an agent determines the best strategy to invest owners assets. | Automated asset management as a service. Users subscribe to the service, which execute elaborate investing strategies to maximize the capital gains, in exchange for a service fee. |
| Frameworks   | {{open_aea}} | {{open_autonomy}} + {{open_aea}} |

Of course, many use cases that apply for single-agent application can later be considered to be offered as an agent service. For this reason, there is also the possibility of implementing a single-agent application as an agent service with a single service operator. This approach has the benefit that whenever the developer wants to make the promotion of that application to an agent service, they will be able to do so almost effortlessly, except for some modifications to account for potentially extra configuration requirements.

## Where to Start

The [_Quick start_](./quick_start.md) section gives a general overview of the work pipeline with {{open_autonomy}} framework, as well as an example of deploying and running an already available, very basic service. The [_Hello World agent service_](./hello_world_agent_service.md) section gives a general overview about how that demonstration agent service is implemented with the stack.

Following these sections, the reader can proceed to explore the core concepts that make agent services possible, presented in the _Concepts_ section:

- [Autonomous economic agents (AEAs) and multi-agent systems (MAS)](./aea.md),
- [Finite-state machines (FSMs)](./fsm.md), and
- the [Application BlockChain Interface (ABCI)](./abci.md).

These concepts constitute the starting point before exploring more advanced parts of the documentation.
