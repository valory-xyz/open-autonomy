<details><summary>What is an Autonomous Service?</summary>
An Autonomous Service is a decentralized service that runs off-chain and provides functionalities to objects living on-chain. Autonomous Services are outside the purview and control of a single authority, and can be be designed for a variety of purposes, including acting as a decentralized oracle for smart contracts, or executing complex investing strategies that cannot be easily encoded on-chain.
</details>

<details><summary>What is an Agent Service?</summary>
An Agent Service is an Autonomous Service which is implemented as a multi-agent system using Autonomous Economic Agents through the <a href="https://github.com/valory-xyz/open-aea">Open AEA</a> framework.
</details>

<details><summary>What is an FSM App?</summary>
An FSM App is an application that implements the business logic of an Agent Service as a finite-state machine. The internal state of an FSM App is replicated and synchronized across all the agents forming the Agent Service.
</details>

<details><summary>Can I reuse the same FSM App multiple times when creating a composed FSM App?</summary>
No. The Open Autonomy framework currently only supports a single instance of a given FSM App in a composition.
</details>

<details><summary>What is a keeper agent?</summary>
It is a normal agent for which other agents have voted to be in charge of executing a certain operation (e.g., settling a transaction on a blockchain).
</details>
