## Definitions

??? note "What is an autonomous service?"
    An autonomous service is a decentralized service that runs off-chain and provides functionalities to objects living on-chain. Autonomous services are outside the purview and control of a single authority, and can be designed for a variety of purposes, including acting as a decentralized oracle for smart contracts, or executing complex investing strategies that cannot be easily encoded on-chain.

??? note "What is an agent service?"
    An agent service is an autonomous service which is implemented as a multi-agent system using Autonomous Economic Agents (AEAs) using the {{open_autonomy}} framework, which is built on top of {{open_aea}}.

??? note "What is an {{fsm_app}}?"
    An {{fsm_app}} is an application that implements the business logic of an agent service as a finite-state machine. The internal state of an {{fsm_app}} is replicated and synchronized across all the agents forming the agent service.

??? note "What is a keeper agent?"
    It is one of the agents for which the agents have voted to be in charge of executing a certain operation (e.g., settling a transaction on a blockchain).

??? note "What is the consensus gadget?"
    The consensus gadget is the infrastructure, local to a service, that enables the agents in that service to run a consensus algorithm to synchronize and replicate the service state. It consists of the consensus gadget nodes (one node per agent) plus the consensus gadget network (which can be the Internet or a dedicated network).

??? note "What is a period?"
    In the context of agent services, a period is the sequence of states in the {{fsm_app}} that execute the main functionality of the service. Usually, services are designed to cycle through these states, for example, an oracle service will cycle through states like "collect observations" - "compute value" - "publish value on-chain".

## How it works

??? note "Can I reuse the same {{fsm_app}} multiple times when creating a composed {{fsm_app}}?"
    No. The Open Autonomy framework currently only supports a single instance of a given {{fsm_app}} in a composition.

??? note "Composability, extensibility and reusability are advantages also present in other tech stacks. What makes Autonolas different?"
    Autonolas is not just a framework where devs can build on: it is a complete, novel ecosystem that provides an SDK, a reward system for developers and operators and a governance protocol on top, all of them decentralized.

    In the same way companies like Apple or Google offer SDKs to accelerate devs work plus an app store to monetize their work, Autonolas offers the same capabilities but in a decentralized way: developers register components, operators run services that use those components, consumers use and pay for those services so both developers and operators are compensated for their work. And all the parameters that govern the network can be voted on.

??? note "How do agents communicate with other agents?"
    Different forms of communication are used depending on the service status. Before the agents can establish a temporary blockchain (Tendermint network) that serves as consensus engine they need to exchange the necessary information with others in order to be able to do so. This information includes the network address of their Tendermint node and the associated public key. They do so by connecting to the Agent Communication Network (ACN), where they can send messages to other agents, in this case requesting their Tendermint configuration details, using their on-chain registered address. The list of registered addresses is retrieved from the service registry smart contract and can be used to filter out request coming from any party that is not registered to operate in this service as well. Once all configurations have been exchanged the Tendermint network can be established and is used as a consensus engine.

??? note "Can services use other services?"
    Yes, an agent service can be composed from other agent services, analogously to microservices. Sub-services can deliver all sorts of results which are consumed by a higher level service to create a higher level outcome.

??? note "How do services communicate with other services?"
    Services use a native message protocol based on protobuf that allows them to have arbitrary message-based communication between compatible agents in the network. The network they use for this is the Agent Communication Network (ACN), and protocols define the structure of communication flow, ranging from simple atomic request-response pairs to arbitrarily complicated dialogues (e.g. FIPA). To communicate with traditional services, agents can both make API calls and expose REST APIs.

??? note "What happens when agents are deployed?"
    Agents are able to interact with the Autonolas on-chain Protocol so they can monetize their work and connect to other services. Apart from that, "island deployments" can also be operated, which are services that run as one-off services, not anchored in the protocol.

??? note "How many composition levels does Open Autonomy offer?"
    Composition starts at the component level of the agents (multiple rounds make a skill), then continues on agent level (multiple skills make an agent) and ends at service level (multiple agents make a service).

??? note "How do agents settle a transaction?"
    1. Negotiation happens through Tendermint messages.
    2. A threshold of agents agree on a transaction hash.
    3. One of the agents is randomly selected as the keeper using a deterministic function based on a public, verifiable randomness source (currently DRAND).
    4. All agents sign the transaction using a multi-sig like Gnosis Safe.
    5. The keeper collects all the signatures and sends the transaction on-chain. If it does not do its job, another keeper will be selected.
    6. All agents wait for the transaction to be mined and validate the output.
    7. Done

??? note "Do all agent services have to be implemented as {{fsm_app}}s with Open Autonomy?"
    Certainly not. For extremely simple applications, you can consider implementing an agent service by appropriately extending the `ABCIHandler` class to handle the consensus gadget callbacks, and if required, manually implement the agent `Behaviours` that execute client calls to the consensus gadget. However, **we strongly advise against this approach**, as the complexity, maintainability and composability of the resulting service will be severely affected.

## Security

??? note "How are agent services run?"
    Agent services are composed of multiple agents that run the same code and agree on its output. These agents are executed by independent operators. Each operator can select and setup the infrastructure that best suits their needs.

??? note "What happens if my node is hacked?"
    As in any other online service, nodes are exposed to the risk of being breached. At the individual level, the framework does not provide a solution to this and it’s up to the agent operator to keep the agent safe. At the service level, on the other hand, services are secured in two ways:

    * Each agent service implements a custom protocol that expects a very narrow message flow, so a hypothetical agent running malicious code would need to express its intentions within this protocol, otherwise the other agents will ignore its messages.
    * Even in the case of an agent sending valid, malicious messages in the service, the decentralized nature of services means that the majority threshold of agents (2/3 + 1) must agree before committing a malicious transaction, so it is not enough to breach an individual agent.

## Costs

??? note "How much does it cost to run an agent service using the framework?"
    Agent services are not limited in what they do or how they are configured (e.g. number of agents in them), therefore the costs are subjective to each service. At the very minimum there will be the costs of running the agent on cloud or local infrastructure.

    On top of that, if a service sends transactions to a chain, it will incur in fee costs that will depend on the selected chain.

    As an example, for a simple service of four agents that makes a simple contract call every five minutes, a monthly cost of $3000 in Ethereum and $1.5 in Polygon is presently estimated (at gas cost of 60 wei per gas), but this number will wildly vary depending on gas costs.

    Apart from transaction costs, service operators also incur infrastructure costs. A rough, quite conservative estimation can be calculated using the following example: a simple service running on top of an AWS m5.large instance (8GB, 2vCPU) with four agents per instance. The following table shows how server costs would vary depending on the number of operators and number of instances per operator.

    <table>
    <thead>
      <tr>
        <th>Operators</th>
        <th>Instances per operator</th>
        <th>Total instances</th>
        <th>Total agents</th>
        <th>Service daily costs (USD)</th>
        <th>Daily costs per operator (USD)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td rowspan="4">1</td>
        <td>1</td>
        <td>1</td>
        <td>4</td>
        <td>2.304</td>
        <td>2.304</td>
      </tr>
      <tr>
        <td>2</td>
        <td>2</td>
        <td>8</td>
        <td>4.608</td>
        <td>4.608</td>
      </tr>
      <tr>
        <td>3</td>
        <td>3</td>
        <td>12</td>
        <td>6.912</td>
        <td>6.912</td>
      </tr>
      <tr>
        <td>4</td>
        <td>4</td>
        <td>16</td>
        <td>9.216</td>
        <td>9.216</td>
      </tr>
      <tr>
        <td rowspan="4">2</td>
        <td>1</td>
        <td>2</td>
        <td>8</td>
        <td>4.608</td>
        <td>2.304</td>
      </tr>
      <tr>
        <td>2</td>
        <td>4</td>
        <td>16</td>
        <td>9.216</td>
        <td>4.608</td>
      </tr>
      <tr>
        <td>3</td>
        <td>6</td>
        <td>24</td>
        <td>13.824</td>
        <td>6.912</td>
      </tr>
      <tr>
        <td>4</td>
        <td>8</td>
        <td>32</td>
        <td>18.432</td>
        <td>9.216</td>
      </tr>
      <tr>
        <td rowspan="4">3</td>
        <td>1</td>
        <td>3</td>
        <td>12</td>
        <td>6.912</td>
        <td>2.304</td>
      </tr>
      <tr>
        <td>2</td>
        <td>6</td>
        <td>24</td>
        <td>13.824</td>
        <td>4.608</td>
      </tr>
      <tr>
        <td>3</td>
        <td>9</td>
        <td>36</td>
        <td>20.736</td>
        <td>6.912</td>
      </tr>
      <tr>
        <td>4</td>
        <td>12</td>
        <td>48</td>
        <td>27.648</td>
        <td>9.216</td>
      </tr>
      <tr>
        <td rowspan="4">4</td>
        <td>1</td>
        <td>4</td>
        <td>16</td>
        <td>9.216</td>
        <td>2.304</td>
      </tr>
      <tr>
        <td>2</td>
        <td>8</td>
        <td>32</td>
        <td>18.432</td>
        <td>4.608</td>
      </tr>
      <tr>
        <td>3</td>
        <td>12</td>
        <td>48</td>
        <td>27.648</td>
        <td>6.912</td>
      </tr>
      <tr>
        <td>4</td>
        <td>16</td>
        <td>64</td>
        <td>36.864</td>
        <td>9.216</td>
      </tr>
    </tbody>
    </table>

## Ethereum topics

??? note "How does EIP-1559 transaction pricing mechanism work?"
    EIP-1559 has introduced significant changes in how the transaction pricing is determined. Previously, setting the `gasPrice` was sufficient; now, two new parameters have to be specified, `maxFeePerGas` and `maxPriorityFeePerGas`.

    The new pricing structure comprises three key elements:

    - **Base Fee**: This fee is determined autonomously by the network and is subsequently burned. It aims to target 50% full blocks and is adjusted based on the contents of the most recent confirmed block. Depending on block usage, the Base Fee automatically increases or decreases.
    - **Max Priority Fee Per Gas**: This fee is optional and set by the user. It is paid directly to miners. Although technically optional, most network participants estimate that transactions generally require a minimum 2.0 GWEI tip to be competitive for inclusion.
    - **Max Fee Per Gas**: This parameter is the absolute maximum amount you are willing to pay per unit of gas to have your transaction included in a block. If the sum of the Base Fee and Max Priority Fee exceeds the Max Fee, the Max Priority Fee is reduced to maintain the upper bound of the Max Fee. A heuristic formula for Max Fee calculation is: Max Fee = (2 * Base Fee) + Max Priority Fee. Doubling the Base Fee in this calculation ensures that your transaction remains marketable for six consecutive 100% full blocks.

    Transactions containing these new parameters are designated as Type 2, while legacy transactions retaining the original Gas Price field are referred to as Type 0. Notably, EIP-1559 does not alter the Gas Limit, which remains the maximum amount of gas a transaction is authorized to consume.

    For further information, please refer to the [EIP-1559 FAQ](https://notes.ethereum.org/@vbuterin/eip-1559-faq)

??? note "How does a delegate call differ from a call in the context of Safe transactions?"
    When you initiate a delegate call in a Safe transaction (i.e., with the operation set to `delegatecall`), it essentially instructs the Safe to "load the code from the specified address and run it." In other words, it retrieves the code from the contract address provided and executes it. This operation allows for dynamic code execution, enabling flexibility in Smart Contract interactions.
