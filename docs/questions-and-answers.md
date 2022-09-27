## Definitions

<details><summary>What is an autonomous service?</summary>
An autonomous service is a decentralized service that runs off-chain and provides functionalities to objects living on-chain. Autonomous services are outside the purview and control of a single authority, and can be designed for a variety of purposes, including acting as a decentralized oracle for smart contracts, or executing complex investing strategies that cannot be easily encoded on-chain.
</details>

<details><summary>What is an agent service?</summary>
An agent service is an autonomous service which is implemented as a multi-agent system using Autonomous Economic Agents (AEAs) using the <a href="https://github.com/valory-xyz/open-autonomy">Open Autonomy</a> framework, which is built on top of <a href="https://github.com/valory-xyz/open-aea">Open AEA</a>.
</details>

<details><summary>What is an FSM App?</summary>
An FSM App is an application that implements the business logic of an agent service as a finite-state machine. The internal state of an FSM App is replicated and synchronized across all the agents forming the agent service.
</details>

<details><summary>What is a keeper agent?</summary>
It is one of the agents for which the agents have voted to be in charge of executing a certain operation (e.g., settling a transaction on a blockchain).
</details>

## How it works

<details><summary>Can I reuse the same FSM App multiple times when creating a composed FSM App?</summary>
No. The Open Autonomy framework currently only supports a single instance of a given FSM App in a composition.
</details>

<details><summary>Composability, extensibility and reusability are advantages also present in other tech stacks. What makes Autonolas different?</summary>
Autonolas is not just a framework where devs can build on: it is a complete, novel ecosystem that provides an SDK, a reward system for developers and operators and a governance protocol on top, all of them decentralized.</p>
In the same way companies like Apple or Google offer SDKs to accelerate devs work plus an app store to monetize their work, Autonolas offers the same capabilities but in a decentralized way: developers register components, operators run services that use those components, consumers use and pay for those services so both developers and operators are compensated for their work. And all the parameters that govern the network can be voted on.</details>

<details><summary>How do agents communicate with other agents?</summary>
Different forms of communication are used depending on the service status. Before the agents can establish a temporary blockchain (Tendermint network) that serves as consensus engine they need to exchange the necessary information with others in order to be able to do so. This information includes the network address of their Tendermint node and the associated public key. They do so by connecting to the Agent Communication Network (ACN), where they can send messages to other agents, in this case requesting their Tendermint configuration details, using their on-chain registered address. The list of registered addresses is retrieved from the the service registry smart contract and can be used to filter out request coming from any party that is not registered to operate in this service as well. Once all configurations have been exchanged the Tendermint network can be established and is used as a consensus engine.
</details>

<details><summary>Can services use other services?</summary>
Yes, an agent service can be composed from other agent services, analogously to microservices. Sub-services can deliver all sorts of results which are consumed by a higher level service to create a higher level outcome.
</details>

<details><summary>How do services communicate with other services?</summary>
Services use a native message protocol based on protobuf that allows them to have arbitrary message based communication between compatible agents in the network. This network is called Agent Communication Network (ACN). When a service needs a more complicated message flow than request-response (e.g. some extended dialogue like FIPA) they can express it as a protocol and deliver the messages via the ACN. To communicate with traditional services, agents can both make API calls and expose REST APIs.
</details>

<details><summary>What happens when agents are deployed?</summary>
Agents are be able to interact with the Autonolas on-chain Protocol so they can monetize their work and connect to other services. Apart from that, "island deployments" can also be operated, which are services that run as one-off services, not anchored in the protocol.
</details>

<details><summary>How many composition levels does Open Autonomy offer?</summary>
Composition starts at the component level of the agents (multiple rounds make a skill), then continues on agent level (multiple skills make an agent) and ends at service level (multiple agents make a service).
</details>

<details><summary>How do agents settle a transaction?</summary>

<ol>
<li>Negotiation happens through Tendermint messages.</li>
<li>A threshold of agents agree on a transaction hash.</li>
<li>One of the agents is randomly selected as the keeper using a deterministic function based on a public, verifiable randomness source (currently DRAND).</li>
<li>All agents sign the transaction using a multi-sig like Gnosis Safe.</li>
<li>The keeper collects all the signatures and sends the transaction on-chain. If it does not do its job, another keeper will be selected.</li>
<li>All agents wait for the transaction to be mined and validate the output.</li>
<li>Done</li>
</ol>
</details>

<details><summary>Do all agent services have to be implemented as {{fsm_app}}s with Open Autonomy?</summary>
Certainly not. We have provided an example in the <a href=/counter_example>counter demo</a>. That is, for extremely simple applications, you can consider implementing an agent service by appropriately extending the <code>ABCIHandler</code> class to handle the consensus gadget callbacks, and if required, manually implement the agent <code>Behaviours</code> that execute client calls to the consensus gadget. However, <b>we strongly advise against this approach</b>, as the complexity, maintainability and composability of the resulting service will be severely affected.
</details>

## Security

<details><summary>How are agent services run?</summary>

Agent services are composed of multiple agents that run the same code and agree on its output. These agents are executed by independent operators. Each operator can select and setup the infrastructure that best suits their needs.</details>

<details><summary>What happens if my node is hacked?</summary>

As in any other online service, nodes are exposed to the risk of being breached. At the individual level, the framework does not provide a solution to this and it’s up to the agent operator to keep the agent safe. At the service level, on the other hand, services are secured in two ways:</p>

<ul>
<li>Each agent service implements a custom protocol that expects a very narrow message flow, so a hypothetical agent running malicious code would need to express its intentions within this protocol, otherwise the other agents will ignore its messages.</li>

<li>Even in the case of an agent sending valid, malicious messages in the service, the decentralized nature of services means that the majority threshold of agents (2/3 + 1) must agree before committing a malicious transaction, so it is not enough to breach an individual agent.</li>
</ul>
</details>

## Costs

<details><summary>How much does it cost to run an agent service using the framework?</summary>
Agent services are not limited in what they do or how they are configured (e.g. number of agents in them), therefore the costs are subjective to each service. At the very minimum there will be the costs of running the agent on cloud or local infrastructure.
On top of that, if a service sends transactions to a chain, it will incur in fee costs that will depend on the selected chain.</p>As an example, for a simple service of four agents that makes a simple contract call every five minutes, a monthly cost of $3000 in Ethereum and $1.5 in Polygon is presently estimated (at gas cost of 60 wei per gas), but this number will wildly vary depending on gas costs.

Apart from transaction costs, service operators also incur in infrastructure costs. A rough, quite conservative estimation can be calculated using the following example: a simple service running on
top of AWS m5.large instances (8GB, 2vCPU) with four agents per instance. The following table shows how server costs would vary depending on the number of operators and number of instances per operator.

<table>
<thead>
  <tr>
    <th>Operators</th>
    <th>Instances per operator</th>
    <th>Total instances</th>
    <th>Total agents</th>
    <th>Service daily costs ($)</th>
    <th>Daily costs per operator ($)</th>
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

</details>
