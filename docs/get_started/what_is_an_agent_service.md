An **agent service** is an off-chain service which runs as a multi-agent-system (MAS) and is replicated on a **consensus gadget** (a sort of short-lived blockchain) while being crypto-economically secured on a public blockchain. Agent services enable complex processing, take action on their own and run continuously. Moreover, agent services are crypto-native by construction, that is, they are **decentralized**, **trust-minimized**, **transparent**, and **robust**.


The {{open_autonomy}} framework allows to define such services by means of a special component called **{{fsm_app}}**. These dynamic, decentralized apps run inside the agents defining the agent service, and implementing the underlying mechanisms that allow agents to synchronize their internal state.




## How it works

There are a number of concepts that are required to have an initial idea on how an agent service works. In summary,

* Each agent service is composed of a number of $N$ **agents**. This number is determined upon definition of the concrete agent service.

* Each agent is made up of a number of **components** defined by the {{open_aea}} framework. These components define, for example, what protocols the agent is able to process.

* A special component called **{{fsm_app}}** defines the business logic of the agent service. Thus, each agent in the service has a copy of the {{fsm_app}}. The {{fsm_app}} is defined through the {{open_autonomy}} framework.

* **Agent operators** are the entities or individuals that own the infrastructure where the agents run. Each operator executes an agent instance and a **consensus gadget node**.

* The **consensus gadget** (i.e., the consensus gadget nodes + the consensus gadget network) is the agent service component that enables the agents to maintain the service state and reach consensus on certain important decisions. From a technical point of view, the consensus gadget implements a blockchain based on [Tendermint](https://tendermint.com/).


<figure markdown>
![](../images/agent_service_architecture.svg)
<figcaption>Overview of the architecture of an agent service</figcaption>
</figure>

Recall that the business logic of the service (encoded in the {{fsm_app}}) can define anything, from a price oracle to a complex investment strategy using machine learning algorithms. The {{fsm_app}} is structured as a series of steps that each agent in the service must follow in order to achieve the service functionality. Using the consensus gadget, agents must reach consensus on the outcome of each step. This ensures that the execution flow of the service, its inputs and outputs are replicated across all agents, creating a distributed (and decentralized) application with shared state that is fault tolerant. The {{open_autonomy}} framework provides most of the machinery so that the shared state is replicated across agents automatically through the consensus gadget. From an architectural point of view, the {{fsm_app}} is implemented as a particular type of agent component.

If at some point the agent service must execute an action involving an external service, e.g.,
settling a transaction on a blockchain, one of the agents is randomly nominated to perform that action. The nominated agent is known as a **keeper**. The nomination process is also agreed by consensus, and multi-signature protocols are used to avoid that a single, malicious agent executes an external action on its own.
For this reason, there is the requirement that a minimum number of agents approve and sign every action before it takes place, and it also must be verified once it has been processed. The threshold on the minimum number of agents is typically, but not exclusively, set at 2/3 of the total of agents.
