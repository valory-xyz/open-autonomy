# AEA: Autonomous Economic Agents

!!!note

    It is assumed the reader has a decent understanding of the
    [open AEA framework](https://github.com/valory-xyz/open-aea).
    An __[introductory guide to this paradigm](https://valory-xyz.github.io/open-aea/)__
    is available to help you get started in case you're not yet familiar.

Multi-agent systems are inherently decentralized. Each of the agents pursues its
own objectives and as a result, conflicts of interest are expected to arise.
Furthermore, agents operate asynchronously and due to this decoupling and the
absence of a central moderator the resulting system becomes fundamentally
uncertain.

So, how then can we create a functional system in which agents can pursue their
objectives without guarantees on how other agents might behave? The answer lies
in minimizing the need to trust other agents in the system by not making
assumptions on how, or even if, other agent will respond.

Instead of relying on the other party to behave honestly or a third party to
mediate transactions (e.g. via [escrow](https://en.wikipedia.org/wiki/Escrow)),
we use a _distributed shared state_ in which transactions are recorded. This
_distributed shared state_ takes the form of a deterministic state machine,
which is [replicated](https://en.wikipedia.org/wiki/State_machine_replication)
by all the agents so that each has a copy of it. In order to make any changes
to this shared state, the agents need to reach consensus over the update. When
a majority of agents comprising the network decides on a single state,
consensus is achieved and the shared state is updated accordingly. More
precisely, state machine replication with `N = 3f + 1` replicas can tolerate
`f` simultaneous failures, and hence consensus over the new state is reached
when `ceil((2N + 1) / 3)` of the agents agree on a particular state. Systems
that posses this fault tolerance are referred to as being
[Byzantine fault-tolerant](https://pmg.csail.mit.edu/papers/osdi99.pdf).
The result is a what is called a _trustless_ system, which refers to a system in
which the amount of trust required from any single agent is minimized.
Thus, by not trusting any single authority, this system creates trust by default.

An Autonomous Economic Agent (AEA) is a
[specific type of agent](https://valory-xyz.github.io/open-aea/agent-vs-aea/)
that is concerned with the generation of economic wealth on its owners' behalf.
The [DecisionMaker](https://valory-xyz.github.io/open-aea/decision-maker/)
is where a developers' or users' goals, preferences, message handling and wallet
control reside.
AEAs possess [skills](https://valory-xyz.github.io/open-aea/skill/) which
allow them to operate proactively, through the expression of
[`Behaviour`](https://valory-xyz.github.io/open-aea/api/skills/base/#behaviour-objects),
as well as reactively by managing incoming messages from other agents via a
[`Handler`](https://valory-xyz.github.io/open-aea/api/skills/base/#handler-objects).
Since there might exist a need to share a certain context which is relevant both
to behaviors and handlers, this can be achieved via a
[`Model`](https://valory-xyz.github.io/open-aea/api/skills/base/#model-objects).

Every skill is associated with an agent since it is registered to it. Skills
and agents have their own respective `context` attributes, instances of
[`SkillContext`](https://valory-xyz.github.io/open-aea/api/skills/base/)
and
[`AgentContext`](https://valory-xyz.github.io/open-aea/api/context/base/),
however each of these provides access to a shared state.
This shared state is what agents can alter through the usage of skills.

AEAs interact with other agents, both AEAs and those in the outside world, via
[interaction protocols](https://valory-xyz.github.io/open-aea/interaction-protocol/).
In order to locate other agents they connect to the
[Agent Communication Network (ACN)](https://valory-xyz.github.io/open-aea/acn/).
More specifically, AEAs communicate asynchronously with other agents using
[`Envelopes`](https://valory-xyz.github.io/open-aea/api/mail/base/#envelope-objects)
that contain a [`Message`](https://valory-xyz.github.io/open-aea/api/protocols/base/).
These messages adhere to specific messaging
[protocols](https://valory-xyz.github.io/open-aea/protocol/).
In order for AEAs to communicate with agents in the outside world they need to
set up a [connection](https://valory-xyz.github.io/open-aea/connection/), which
are managed by the
[`Mutliplexer`](https://valory-xyz.github.io/open-aea/api/multiplexer/).
The execution of smart
[contract](https://valory-xyz.github.io/open-aea/contract/)
related logic, for example, requires a connection to provide the agent with the
necessary network access.
