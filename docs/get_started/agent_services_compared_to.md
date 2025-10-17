One of the best ways to understand how autonomous [AI agents](./what_is_an_agent_service.md) fit into
the wider ecosystem of crypto services and applications is to compare them with existing solutions.

Recall that an **autonomous AI agents** is a decentralized service that runs off-chain and provides functionalities to objects living on-chain. Autonomous AI agents are outside the purview and control of a single authority, and can be designed for a variety of purposes, including acting as a decentralized oracle for smart contracts, or executing complex investing strategies that cannot be easily encoded on-chain. An **AI agents** is a particular type of autonomous AI agent which is implemented as a multi-agent system.

## AI agents vs. other software solutions

The table below highlights the main differences between AI agents and other software solutions.

|                          |   Smart contracts  |    Web services    | Custom decentralized services (e.g., Oracles) | **Autonomous AI agents**                 |
|--------------------------|:------------------:|:------------------:|:---------------------------------------------:|:----------------------------------------:|
| **Location**             |      On-chain      |      Off-chain     |                   Off-chain                   |                 Off-chain                |
| **Decentralized**        | :heavy_check_mark: |         :x:        |               :heavy_check_mark:              |            :heavy_check_mark:            |
| **Robust**               | :heavy_check_mark: |         :x:        |               :heavy_check_mark:              |            :heavy_check_mark:            |
| **Transparent**          | :heavy_check_mark: |         :x:        |               :heavy_check_mark:              |            :heavy_check_mark:            |
| **Complex processing**   |         :x:        | :heavy_check_mark: |               :heavy_check_mark:              |            :heavy_check_mark:            |
| **Cross-chain**          |         :x:        | :heavy_check_mark: |               :heavy_check_mark:              |            :heavy_check_mark:            |
| **Continuous/always-on** |         :x:        | :heavy_check_mark: |               :heavy_check_mark:              |            :heavy_check_mark:            |
| **Flexible**             | :heavy_check_mark: | :heavy_check_mark: |                      :x:                      |            :heavy_check_mark:            |
| **Composable**           | :heavy_check_mark: |         :x:        |                      :x:                      |            :heavy_check_mark:            |
| **DAO-owned**            | :heavy_check_mark: |         :x:        |                      :x:                      |            :heavy_check_mark:            |
| **Full-stack**           |         :x:        | :heavy_check_mark: |                      :x:                      |            :heavy_check_mark:            |

**Smart contracts** are computer programs that live on-chain. They are crypto-native, can be audited and can use any functionality already available in the blockchain. Their security relies
on the security of the underlying blockchain. However, due to their nature, they have a number of limitations, including the inability of doing complex operations, talking to other APIs or interact with other blockchains.

**Web services** are a popular off-chain solution to complement the limitations of smart contracts. They are very flexible, but they usually lack the crypto-native features of smart contracts.

**Custom decentralized services** are services like oracles, bridges or keepers which are run off-chain by a group of operators, thus providing the required level of trust and security. These services run off-chain, which enables them to do complex processing. The main drawback of this approach is that there is no standardized approach to build and compose such services. This severely limits the growth of the ecosystem of applications in the off-chain space.

This is where **AI agents** (implemented with the {{open_autonomy}} framework) comes into play in the broader ecosystem of crypto software. AI agents are composable, crypto-native services that can execute complex processing, take action on their own and run continuously.

For a more detailed discussion, take a look at the [Autonolas Education](https://www.olas.network/education-articles) article series.


## AI agents vs. single-agent-instance applications

Having understood how AI agents fit into the wider crypto ecosystem, sometimes there is the question whether is it best to design a certain application as single-agent-instance or as an AI agents.
This is often a question that new developers in the field of agent systems and multi-agent systems face. We provide below a comparison table which hopefully will give you some guidance on which of the both approaches is best for your use case.

|       | Single-agent-instance applications             | Autonomous AI agents |
| ----------- | ------------------------------------ | --- |
| Scope | An application designed to pursue the interests and objectives of a single entity. | An application designed to offer services that external users can benefit from. |
| Value generation model | The application is in charge of generating economic value for its owner. | AI agent operators might charge a fee to their users. |
| Architecture & Execution | A single agent instance, typically run and controlled by a single entity. | A set of agent instances run by a collection of independent operators. Agent instances have a synchronized shared state. |
| Trust model | Not applicable. The owner controls and designs and manages their own agent instance. | AI agents are decentralized and transparent, and can be crypto-economically secured on a public blockchain. They can be regarded as drop-in replacements of trusted entities (on complex service infrastructures), thus relaxing the trust requirements on them. |
| Example | Automated, personal asset management: an agent instance determines the best strategy to invest owners assets. | Automated asset management as a service. Users subscribe to AI agents, which execute elaborate investing strategies to maximize the capital gains, in exchange for a service fee. |
| Frameworks   | {{open_aea}} | {{open_autonomy}} + {{open_aea}} |

## Progressive decentralization

Of course, many use cases that apply for single-agent-instance application can later be considered to be offered as an AI agent. For this reason, it is often advisable to implement a single-agent-instance application as an AI agent with a single instance operator. This approach has the benefit that whenever the developer wants to make the promotion of that application to an AI agent, they will be able to do so almost effortlessly, except for some modifications to account for potentially extra configuration requirements.
