# AEA: Autonomous Economic Agents

!!!note

    It is assumed the reader has a decent understanding of the
    [open AEA framework](https://github.com/valory-xyz/open-aea).
    An __[introductory guide to this paradigm](https://valory-xyz.github.io/open-aea/)__
    is available to help you get started in case you're not yet familiar.

[Multi-agent systems](https://en.wikipedia.org/wiki/Multi-agent_system), also known as self-organized systems are computer systems composed of multiple, intelligent agents that coordinate to solve a problem. Such systems are inherently decentralized: each of the agents pursues its
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
that possess this fault tolerance are referred to as being
[Byzantine fault-tolerant](https://pmg.csail.mit.edu/papers/osdi99.pdf).
The result is a what is called a _trustless_ system, which refers to a system in
which the amount of trust required from any single agent is minimized.
Thus, _by not trusting any single authority, this system creates trust by default_.

An Autonomous Economic Agent (AEA) is a
[specific type of agent](https://valory-xyz.github.io/open-aea/agent-vs-aea/)
that is concerned with the generation of economic wealth on its owners' behalf
in an autonomous way.