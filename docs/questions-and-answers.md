## Definitions

<details><summary>What is an Autonomous Service?</summary>
An Autonomous Service is a decentralized service that runs off-chain and provides functionalities to objects living on-chain. Autonomous Services are outside the purview and control of a single authority, and can be be designed for a variety of purposes, including acting as a decentralized oracle for smart contracts, or executing complex investing strategies that cannot be easily encoded on-chain.
</details>

<details><summary>What is an Agent Service?</summary>
An Agent Service is an Autonomous Service which is implemented as a multi-agent system using Autonomous Economic Agents through the <a href="https://github.com/valory-xyz/open-aea">Open AEA</a> framework.
</details>

<details><summary>What is an FSM App?</summary>
An FSM App is an application that implements the business logic of an Agent Service as a finite-state machine. The internal state of an FSM App is replicated and synchronized across all the agents forming the Agent Service.
</details>

<details><summary>What is a keeper agent?</summary>
It is a normal agent for which other agents have voted to be in charge of executing a certain operation (e.g., settling a transaction on a blockchain).
</details>

## How it works

<details><summary>Can I reuse the same FSM App multiple times when creating a composed FSM App?</summary>
No. The Open Autonomy framework currently only supports a single instance of a given FSM App in a composition.
</details>

<details><summary>Composability, extensibility and reusability are advantages also present in other tech stacks. What makes Autonolas different?</summary>
Autonolas it’s not just a framework where devs can build on: it is a complete, novel ecosystem that provides an SDK, a reward system for developers and operators and a governance protocol on top, all of them decentralized.</p>
In the same way companies like Apple or Google offer SDKs to accelerate devs work plus an app store to monetize their work, Autonolas offers the same capabilities but in a decentralized way: developers register components, operators run services that use those components, consumers use and pay for those services so both developers and operators are compensated for their work. And all the parameters that govern the network can be voted on.</details>

<details><summary>Can services use other services?</summary>
Yes, agent services can be composed from other agent services eventually, analogously to microservices. Sub-services could deliver all sorts of results which are consumed by a higher level service to create a higher level outcome.
</details>

<details><summary>How do services communicate with other services?</summary>
Services can expose REST APIs and they also have a native message protocol that uses protobuf that allows them to have arbitrary message based communication between compatible agents in the network. This network is called agent communication network (ACN). When a service need a more complicated message flow than request-response (e.g. some extended dialogue like FIPA) they can express it as a protocol and deliver the messages via ACN.</p>
Under the hood ACN is a DHT that keeps track of live agents mapping their crypto address to IP address. So agents can communicate with other agents without knowing their network location assuming they’re online or offline but registered in the ACN.
</details>

<details><summary>What happens when agents are deployed now?</summary>
Currently we're only operating what we call "island deployments", which are services that run as one-off services, not anchored in the protocol, because the protocol isn't live (more on that here). Once the protocol is live, agents will be able to interact with it so they can monetize their work and connect to other services.
</details>

<details><summary>How many composition levels does Autonolas stack offer?</summary>
Composition starts at the component level of the agents (multiple rounds make a skill), then continues on agent level (multiple skills make an agent) and ends at service level (multiple agents make a service).
</details>

<details><summary>How do agents settle a transaction?</summary>

<ol>
<li>Negotiation happens through ACN (or alternatively another connection like ABCI connection).</li>
<li> A threshold of agents agree on a transaction hash.</li>
<li>One of the agents is randomly selected as the keeper using a verifiable randomness function (currently DRAND).</li>
<li>All agents sign the transaction using a multi-sig like Gnosis Safe.</li>
<li>The keeper collects all the signatures and sends the transaction onchain.</li>
<li>All agents wait for the transaction to be mined and validate the output.</li>
<li>Done</li>
</ol>
</details>

## Security

<details><summary>How are Autonolas services run?</summary>

Autonolas services are composed of multiple agents that run the same code and agree on its output. These agents are executed in different nodes that are run by independent operators. In order to avoid centralizing this power, Autonolas does not play a role here so it does not offer a cloud platform. Each operator must select and setup the infrastructure that best suits their needs.</details>

<details><summary>What happens if my node is hacked?</summary>

As in any other online service, Autonolas nodes are exposed to the risk of being breached. At the individual level, Autonolas does not provide a solution to this and it’s up to the node operator to keep the node safe. At the service level, on the other hand, services are secured in three ways:</p>

<ul>
<li>Each agent service implements a custom protocol that expects very narrow message flow, so a hypothetical malicious node running malicious code would need to express its intentions within this protocol, otherwise the other agents will ignore its messages.</li>

<li>Even in the case of an agent sending valid, malicious messages to the service, the decentralized nature of Autonolas services means that the majority threshold of agents (⅔ + 1) should agree before committing a malicious transaction, so it is not enough to breach a bunch of nodes.</li>

<li>Services are crypto-economically secured: agents are incentivised to behave honestly by the fact that certain misbehavior can be detected and punished, so it is economically not profitable to cheat.</li>
</ul>
</details>

<details><summary>For critical operations, like sending a transaction to a blockchain, it is not enough with trusting that the agents will behave honestly, and further security and cryptographic mechanisms are required. Does the framework provide those mechanisms?</summary>
For sending transactions to a chain, for example, we use a multisig approach (currently Gnosis Safe) so a threshold of agents must always approve and validate operations.
</details>

## Costs

<details><summary>How much does it cost to run an autonomous service using the framework?</summary>
We don’t define what an agent service does and how it is configured (e.g. number of agents in it), so the costs are subjective to the service. At the very minimum you’ll have the infrastructure costs.
On top of that, if the server you’re participating in sends transactions to a chain, you’ll incur in fee costs that will depend on the selected chain. As an example, for a simple service of four agents that make a simple contract call every five minutes, we estimate a monthly cost of $3000 in Ethereum and $1.5 in Polygon, but this number will wildly vary depending on gas costs.
</details>