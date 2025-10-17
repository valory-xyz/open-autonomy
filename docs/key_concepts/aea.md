!!!note
    This page presents a brief overview of the {{open_aea}} framework. We refer the reader to the {{open_aea_doc}} for the complete details.


An [intelligent agent](https://en.wikipedia.org/wiki/Intelligent_agent) is a computer program that observes its environment, processes the perceived information, and executes actions in order to achieve some predefined goals. Intelligent agents can be designed to work autonomously by gathering data on a regular, pre-programmed schedule, or when a user prompts them in real time.



An [autonomous economic agent (AEA)](https://stack.olas.network/open-aea/agent-vs-aea/) is a specific type of agent
that is concerned with the generation of economic wealth on its owners' behalf in an autonomous way.



A [multi-agent system (MAS)](https://en.wikipedia.org/wiki/Multi-agent_system), also known as a self-organized system, is a computer system composed of multiple, intelligent agents that coordinate to solve a problem. Such systems are inherently decentralized: each of the agents pursues its
own objectives and as a result, conflicts of interest are expected to arise.
Furthermore, agents operate asynchronously, and due to this decoupling and the
absence of a central moderator the resulting system becomes fundamentally
uncertain.


!!! warning "Important"
    Every AI agent built with the {{open_autonomy}} framework is a MAS composed of several AEAs that interact between them to achieve the goals of the AI agent.


## How AI Agents Are Secured

So, how can we create a functional system in which agent instances can pursue their
objectives without guarantees on how other agent instances might behave? The answer lies
in minimizing the need to trust other agent instances in the system by not making
assumptions on how, or even if, they will respond.

Instead of relying on the other agent instances to behave honestly or a third party to
mediate transactions (e.g., via [escrow](https://en.wikipedia.org/wiki/Escrow)), in a MAS
there is a _distributed shared state_ in which transactions are recorded. This
shared state takes the form of a deterministic finite-state machine (FSM),
which is [replicated](https://en.wikipedia.org/wiki/State_machine_replication)
by all the agent instances so that each one has a copy of it. The mechanism that is in charge of managing the replication is called the _state-minimized consensus gadget_ (SGC).

In order to make any changes
to the shared state, the agent instances in the MAS need to reach consensus over the update. For example, let us consider the case where the shared state is the current exchange rate between two cryptocurrencies. When
a majority of agent instances that comprise the AI agent decides on a single state,
the shared state is updated accordingly provided that consensus is achieved. More
precisely, FSM replication with $N = 3f + 1$ agent instances can tolerate up to
$f$ simultaneous failures, and hence consensus over the new state is reached
when $\geq\lceil(2N + 1) / 3\rceil$ of the agent instances agree on a particular state. Systems
that possess this fault tolerance level are referred to as being
[Byzantine fault-tolerant](http://pmg.csail.mit.edu/papers/osdi99.pdf).
The result is what is called a _trust-minimized system_, which refers to a system in
which the amount of trust required from any single agent instance is minimized.
That is, "by not trusting any single authority, this system creates trust by default."


## Main Components of an AEA

Every AEA is composed of a number of components that work together to achieve the pre-defined goals of the agent blueprint. The image below offers a high-level view of such internal components.


<figure markdown>
![](../images/simplified-aea.svg)
<figcaption>Main components of an AEA</figcaption>
</figure>

As it can be seen, there are quite a few elements that make up an AEA. We briefly review the most relevant ones that play a role in the creation of an AI agent:

### DecisionMaker
The [`DecisionMaker`](https://stack.olas.network/open-aea/decision-maker/)
is the "economic brain" of the AEA, where the developers' or users' goals, preferences, message handling and wallet
control reside. It comprises:

- The [`Wallet`](https://stack.olas.network/open-aea/api/crypto/wallet/),
containing access to crypto addresses, public and private keys.
[`Crypto`](https://stack.olas.network/open-aea/api/crypto/base/) objects
are used to load and encrypt private keys stored in an agent's local environment.
- A [`Resources`](https://stack.olas.network/open-aea/api/registries/resources/) object,
giving access to various
[`Registries`](https://stack.olas.network/open-aea/api/registries/base/),
and allowing for the remote registration of various components such as
[`Protocols`](https://stack.olas.network/open-aea/api/protocols/base/#protocol-objects),
[`Skills`](https://stack.olas.network/open-aea/api/skills/base/),
[`Contracts`](https://stack.olas.network/open-aea/api/contracts/base/) and
[`Connections`](https://stack.olas.network/open-aea/api/connections/base/).
- The [`AgentContext`](https://stack.olas.network/open-aea/api/context/base/), which
allows access to various objects that are relevant to the agent's
[`Skills`](https://stack.olas.network/open-aea/api/skills/base/).
- A [`Preferences`](https://stack.olas.network/open-aea/api/decision_maker/base/#preferences-objects) object,
used to check whether a proposed [`Transaction`](https://stack.olas.network/open-aea/api/helpers/transaction/base/)
satisfies the AEA's goals. This is done through the computation of a marginal
utility score based on the
[`Terms`](https://stack.olas.network/open-aea/api/helpers/transaction/base/#terms-objects)
of the transaction and the AEA's current
[`OwnershipState`](https://stack.olas.network/open-aea/api/decision_maker/base/#ownershipstate-objects).



### Skills
[`Skills`](https://stack.olas.network/open-aea/skill/) are the core focus of the {{open_aea}} framework's extensibility, as they implement business logic to deliver economic value for the AEA.  They represent the AEAs knowledge, that is, self-contained capabilities that AEAs can dynamically take on board, in order to expand their effectiveness in different situations. Skills exhibit both reactive and proactive actions as follows:

- [`Handlers`](https://stack.olas.network/open-aea/api/skills/base/#handler-objects) implement AEAs' reactive behaviour. Each [`Skill`](https://stack.olas.network/open-aea/skill/) has zero, one or more handler objects. There is a one-to-one correspondence between [`Handlers`](https://stack.olas.network/open-aea/api/skills/base/#handler-objects) and [`Protocols`](https://stack.olas.network/open-aea/api/protocols/base/#protocol-objects) in an AEA (also known as registered protocols). If an AEA understands a [`Protocol`](https://stack.olas.network/open-aea/api/protocols/base/#protocol-objects) referenced in a received [`Envelope`](https://stack.olas.network/open-aea/api/mail/base/#envelope-objects) (i.e., the protocol is registered in this AEA), this envelope is sent to the corresponding [`Handler`](https://stack.olas.network/open-aea/api/skills/base/#handler-objects) which executes the AEA's reaction to this [`Message`](https://stack.olas.network/open-aea/api/protocols/base/).

- [`Behaviours`](https://stack.olas.network/open-aea/api/skills/base/#behaviour-objects) encapsulate actions which further the AEAs goal and are initiated by internals of the AEA rather than external events. [`Behaviours`](https://stack.olas.network/open-aea/api/skills/base/#behaviour-objects) implement AEAs' proactiveness. The {{open_aea}} framework provides a number of abstract base classes implementing different types of simple and composite [`Behaviours`](https://stack.olas.network/open-aea/api/skills/base/#behaviour-objects) (e.g., cyclic, one-shot, finite-state-machine, etc), and these define how often and in what order a behaviour and its sub-behaviours must be executed. [`Behaviours`](https://stack.olas.network/open-aea/api/skills/base/#behaviour-objects) act as a user in a traditional blockchain.


- Since there might exist a need to share a certain context which is relevant both
to behaviours and handlers, this can be achieved via a
[`Model`](https://stack.olas.network/open-aea/api/skills/base/#model-objects).

Every [`Skill`](https://stack.olas.network/open-aea/skill/) has a
[`SkillContext`](https://stack.olas.network/open-aea/api/skills/base/).
This object is shared by all [`Handler`](https://stack.olas.network/open-aea/api/skills/base/#handler-objects), [`Behaviour`](https://stack.olas.network/open-aea/api/skills/base/#behaviour-objects), and [`Model`](https://stack.olas.network/open-aea/api/skills/base/#model-objects) objects. The [`SkillContext`](https://stack.olas.network/open-aea/api/skills/base/) also has a link to the [`AgentContext`](https://stack.olas.network/open-aea/api/context/base/), which provides read access to AEA specific information like the public key and address of the AEA, its preferences and ownership state.

<figure markdown>
![Skill components](../images/skill-components.svg)
<figcaption>Skill components have access to the SkillContext</figcaption>
</figure>

!!! note "Example"
    In the `ErrorHandler(Handler)` class, the code often grabs a reference to its context and by doing so can access initialised and running framework objects such as an `OutBox` for putting messages into:

    ```python
    self.context.outbox.put_message(message=reply)
    ```

    Moreover, the programmer can read/write to the agent instance context namespace by accessing the attribute SkillContext.namespace.

    Importantly, however, a [`Skill`](https://stack.olas.network/open-aea/skill/) does not have access to the context of another skill or protected AEA components like the [`DecisionMaker`](https://stack.olas.network/open-aea/decision-maker/).



## Overview of AEA Skills Implementation


Note that [`Skills`](https://stack.olas.network/open-aea/skill/) are one of the parts where the developer will need to invest more time, as it is where the concrete business logic is developed. This will be also the case when developing AI agents, because a special type of [`Skill`](https://stack.olas.network/open-aea/skill/) is what will define the AI agent business logic.

Therefore, we briefly provide a general overview on how an AEA [`Skill`](https://stack.olas.network/open-aea/skill/) is implemented in the {{open_aea}} framework. See also the {{open_aea_doc}} for the complete details.


The [`AbstractAgent`](https://stack.olas.network/open-aea/api/abstract_agent/) class
simply defines all the strictly necessary methods and properties required to
implement a concrete [`Agent`](https://stack.olas.network/open-aea/api/agent/).
The [`AEA`](https://stack.olas.network/open-aea/api/aea/) class inherits from the
[`Agent`](https://stack.olas.network/open-aea/api/agent/) and extends it with
additional functionality.



<figure markdown>
<div class="mermaid">
classDiagram
    SkillComponent o--> SkillContext
    SkillComponent <|-- Model
    SkillComponent <|-- Handler
    SkillComponent <|-- AbstractBehaviour
    AbstractBehaviour <|-- Behaviour
    Behaviour <|-- ConcreteBehaviour
    class SkillComponent {
        +skill_context: SkillContext
        +context(self)
        +init(self, skill_context)
        +setup(self)*
        +teardown(self)*
    }
    class Model {
    }
    class Handler {
        +handle(self, message)*
        +handle_wrapper(self, message)
    }
    class AbstractBehaviour{
      +tick_interval(self)
      +start_at(self)
    }
    class Behaviour {
        +act(self)*
        +act_wrapper(self)
    }
    class ConcreteBehaviour {
        +setup(self)
        +act(self)
        +teardown(self)
    }
    class SkillContext {
        +shared_state
    }
</div>
<figcaption>Overview of the classes associated to an AEA Skill</figcaption>
</figure>



*  The abstract class [`SkillComponent`](https://stack.olas.network/open-aea/api/skills/base/#skillcomponent-objects)
serves as the base class for the implementation of all the internal components of the AEA [`Skills`](https://stack.olas.network/open-aea/skill/). Upon instantiation, it receives a [`SkillContext`](https://stack.olas.network/open-aea/api/skills/base/#skillcontext-objects) object, which
provides access to the `shared_state`.



*  Then, the classes
[`Model`](https://stack.olas.network/open-aea/api/skills/base/#model-objects),
[`Handler`](https://stack.olas.network/open-aea/api/skills/base/#handler-objects), and
[`Behaviour`](https://stack.olas.network/open-aea/api/skills/base/#behaviour-objects) implement the class [`SkillComponent`](https://stack.olas.network/open-aea/api/skills/base/#skillcomponent-objects). Note that the inherited abstract methods `setup()` and `teardown()` force the developer to
ensure these methods are implemented on any concrete subclass.


*  Also, note that the
[`Behaviour`](https://stack.olas.network/open-aea/api/skills/base/#behaviour-objects) class
has access to two additional properties, `tick_interval` and `start_at`, which
allow that the [`Behaviour`](https://stack.olas.network/open-aea/api/skills/base/#behaviour-objects), or more concretely, the `act()` method, be invoked periodically,
starting from the designated time. A simple concrete implementation of [`Behaviour`](https://stack.olas.network/open-aea/api/skills/base/#behaviour-objects),
one which we will return to in the next section, looks as follows:

*  A `ConcreteBehaviour`, therefore must implement the corresponding methods to initialize, execute the action, and finalize the `Behaviour`.



## AEA Communication

AEAs interact with other agent instances, either within the same AI agent, and/or with agent instances in the outside world, via
[interaction protocols](https://stack.olas.network/open-aea/interaction-protocol/).
In order to locate other agent instances, they connect to the
[Agent Communication Network (ACN)](https://stack.olas.network/open-aea/acn/).

More specifically, AEAs communicate asynchronously with other agent instances by exchanging
[`Envelopes`](https://stack.olas.network/open-aea/api/mail/base/#envelope-objects), each one
containing a [`Message`](https://stack.olas.network/open-aea/api/protocols/base/).
These messages adhere to specific messaging
[`Protocols`](https://stack.olas.network/open-aea/protocol/).
In order to make the communication possible, each AEA needs to
set up a [`Connection`](https://stack.olas.network/open-aea/connection/), which
is managed by the
[`Mutliplexer`](https://stack.olas.network/open-aea/api/multiplexer/).
A [`Connection`](https://stack.olas.network/open-aea/connection/) wraps an SDK or API and provides an interface to networks, ledgers or other services, in addition to make possible the communication between AEAs through the ACN.
For example, the logic related to the execution of a smart
[`Contract`](https://stack.olas.network/open-aea/contract/)
requires a connection to provide the agent instance with the
necessary blockchain network access.
Connection is responsible for translating between the framework-specific [`Envelope`](https://stack.olas.network/open-aea/api/mail/base/#envelope-objects) with its [`Message`](https://stack.olas.network/open-aea/api/protocols/base/) and the external service or third-party protocol (e.g. HTTP).

The AEAs [`Identity`](https://stack.olas.network/open-aea/api/identity/base/)
provides access to any associated addresses and public keys.
A list with [`Connections`](https://stack.olas.network/open-aea/api/connections/base/)
allows agent-to-agent communication.


<!--
## The implementation `Skill`

A [`Skill`](https://stack.olas.network/open-aea/api/skills/base/#skill-objects)
encapsulates abstractions of `Behaviour`, `Handler` and `Model`.

```python
class Skill(Component):
    """This class implements a skill."""
    @property
    def handlers(self) -> Dict[str, Handler]:
        """Get the handlers."""

    @property
    def behaviours(self) -> Dict[str, Behaviour]:
        """Get the behaviours."""

    @property
    def models(self) -> Dict[str, Model]:
        """Get the models."""
```
-->
