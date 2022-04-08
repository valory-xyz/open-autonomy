# Autonomous Economic Agents (AEAs)

!!!note
    It is assumed the reader has some familiarity with the
    {{open_aea}} framework.
    We refer new developers to the {{open_aea_doc}} to get started.

An [intelligent agent](https://en.wikipedia.org/wiki/Intelligent_agent) is a computer program that observes its environment, processes the perceived information, and executes actions in order to achieve some predefined goals. Intelligent agents can be designed to work autonomously by gathering data on a regular, pre-programmed schedule, or when a user prompts them in real time.



A [multi-agent system (MAS)](https://en.wikipedia.org/wiki/Multi-agent_system), also known as a self-organized system, is a computer system composed of multiple, intelligent agents that coordinate to solve a problem. Such systems are inherently decentralized: each of the agents pursues its
own objectives and as a result, conflicts of interest are expected to arise.
Furthermore, agents operate asynchronously, and due to this decoupling and the
absence of a central moderator the resulting system becomes fundamentally
uncertain.

So, how then can we create a functional system in which agents can pursue their
objectives without guarantees on how other agents might behave? The answer lies
in minimizing the need to trust other agents in the system by not making
assumptions on how, or even if, they will respond.

Instead of relying on the other agents to behave honestly or a third party to
mediate transactions (e.g., via [escrow](https://en.wikipedia.org/wiki/Escrow)), in a MAS
there is a _distributed shared state_ in which transactions are recorded. This
shared state takes the form of a deterministic finite-state machine,
which is [replicated](https://en.wikipedia.org/wiki/State_machine_replication)
by all the agents so that each has a copy of it. In order to make any changes
to the shared state, the agents in the MAS need to reach consensus over the update. When
a majority of agents comprising the network decides on a single state,
consensus is achieved and the shared state is updated accordingly. More
precisely, state machine replication with $N = 3f + 1$ replicas can tolerate up to
$f$ simultaneous failures, and hence consensus over the new state is reached
when $\geq\lceil(2N + 1) / 3\rceil$ of the replicated agents agree on a particular state. Systems
that possess this fault tolerance are referred to as being
[Byzantine fault-tolerant](https://pmg.csail.mit.edu/papers/osdi99.pdf).
The result is what is called a _trustless system_, which refers to a system in
which the amount of trust required from any single agent is minimized.
That is, "by not trusting any single authority, this system creates trust by default."

An [autonomous economic agent (AEA)](https://valory-xyz.github.io/open-aea/agent-vs-aea/) is a specific type of agent
that is concerned with the generation of economic wealth on its owners' behalf in an autonomous way. Every Valory app is a MAS composed of several AEAs that interact between them to achieve the application's goals.

Below, we provide a brief summary, showing some aspects of the
implementation that are relevant for developers, and providing easy access to
sections in the guide and API documentation related to the concepts discussed. See the {{open_aea_doc}} for the complete details.


## Main Components of an AEA

Every AEA is composed of a number of components that work together to achieve the pre-defined goals of the agent:

- The [`DecisionMaker`](https://valory-xyz.github.io/open-aea/decision-maker/)
is the "economic brain" of the AEA, where the developers' or users' goals, preferences, message handling and wallet
control reside. It is composed of a number of components:
    - The [`Wallet`](https://valory-xyz.github.io/open-aea/api/crypto/wallet/),
    containing access to crypto addresses, public and private_keys.
    [`Crypto`](https://valory-xyz.github.io/open-aea/api/crypto/base/) objects
    are used to load and encrypt private keys stored in an agents' environment.
    - A [`Resources`](https://valory-xyz.github.io/open-aea/api/registries/resources/) object,
    giving access to various
    [`Registries`](https://valory-xyz.github.io/open-aea/api/registries/base/)
    and allowing for the remote registration of various components such as
    [`Protocols`](https://valory-xyz.github.io/open-aea/api/protocols/base/#protocol-objects),
    [`Skills`](https://valory-xyz.github.io/open-aea/api/skills/base/),
    [`Contracts`](https://valory-xyz.github.io/open-aea/api/contracts/base/) and
    [`Connections`](https://valory-xyz.github.io/open-aea/api/connections/base/).
    - The [`AgentContext`](https://valory-xyz.github.io/open-aea/api/context/base/), which
    allows access to various objects that are relevant to the agents'
    [`Skills`](https://valory-xyz.github.io/open-aea/api/skills/base/).
    - A [`Preferences`](https://valory-xyz.github.io/open-aea/api/decision_maker/base/#preferences-objects) object,
    used to check whether a proposed [`Transaction`](https://valory-xyz.github.io/open-aea/api/helpers/transaction/base/)
    satisfies the AEA's goals. This is done through the computation of a marginal
    utility score based on the
    [`Terms`](https://valory-xyz.github.io/open-aea/api/helpers/transaction/base/#terms-objects)
    of the transaction and the AEA's current
    [`OwnershipState`](https://valory-xyz.github.io/open-aea/api/decision_maker/base/#ownershipstate-objects).





- [`Skills`](https://valory-xyz.github.io/open-aea/skill/), which
allow AEAs to operate proactively, through the expression of
[`Behaviour`](https://valory-xyz.github.io/open-aea/api/skills/base/#behaviour-objects),
as well as reactively by managing incoming messages from other agents via a
[`Handler`](https://valory-xyz.github.io/open-aea/api/skills/base/#handler-objects). Every [`Skill`](https://valory-xyz.github.io/open-aea/skill/) has access to its
[`SkillContext`](https://valory-xyz.github.io/open-aea/api/skills/base/).
- Since there might exist a need to share a certain context which is relevant both
to behaviors and handlers, this can be achieved via a
[`Model`](https://valory-xyz.github.io/open-aea/api/skills/base/#model-objects).

![Simplified AEA](./images/simplified-aea.jpg)


We remark that [`SkillContext`](https://valory-xyz.github.io/open-aea/api/skills/base/)
and
[`AgentContext`](https://valory-xyz.github.io/open-aea/api/context/base/), besides
allowing [`Skills`](https://valory-xyz.github.io/open-aea/skill/) and AEAs, respectively, have their own [`Context`](https://valory-xyz.github.io/open-aea/api/context/base/) attributes, they also
provide access to a shared state.
This shared state is what AEAs can alter through the usage of [`Skills`](https://valory-xyz.github.io/open-aea/skill/).

![Skill components](./images/skill-components.jpg)

## AEA Communication

AEAs interact with other agents, either within the same {{valory_app}}, and/or with agents in the outside world, via
[interaction protocols](https://valory-xyz.github.io/open-aea/interaction-protocol/).
In order to locate other agents, they connect to the
[Agent Communication Network (ACN)](https://valory-xyz.github.io/open-aea/acn/).
More specifically, AEAs communicate asynchronously with other agents by exchanging
[`Envelopes`](https://valory-xyz.github.io/open-aea/api/mail/base/#envelope-objects), each one
containing a [`Message`](https://valory-xyz.github.io/open-aea/api/protocols/base/).
These messages adhere to specific messaging
[protocols](https://valory-xyz.github.io/open-aea/protocol/).
In order to make the communication possible, each AEA needs to
set up a [connection](https://valory-xyz.github.io/open-aea/connection/), which
is managed by the
[`Mutliplexer`](https://valory-xyz.github.io/open-aea/api/multiplexer/).
A [connection](https://valory-xyz.github.io/open-aea/connection/) wraps an SDK or API and provides an interface to networks, ledgers or other services, in addition to make possible the communication between AEAs through the ACN.
For example, The logic related to the execution of a smart
[`Contract`](https://valory-xyz.github.io/open-aea/contract/)
requires a connection to provide the agent with the
necessary blockchain network access.
Connection is responsible for translating between the framework-specific Envelope with its Message and the external service or third-party protocol (e.g. HTTP).

The AEAs [`Identity`](https://valory-xyz.github.io/open-aea/api/identity/base/)
provides access to any associated addresses and public keys.
A list with [`Connections`](https://valory-xyz.github.io/open-aea/api/connections/base/)
allows agent-to-agent communication.



## Implementation Details of AEA Skills
!!!note
    For clarity, the snippets of code presented here are a simplified version of the actual
    implementation. We refer the reader to the {{open_aea_api}} for the complete details.

The [`AbstractAgent`](https://valory-xyz.github.io/open-aea/api/abstract_agent/) class
simply defines all the strictly necessary methods and properties required to
implement a concrete [`Agent`](https://valory-xyz.github.io/open-aea/api/agent/).
The [`AEA`](https://valory-xyz.github.io/open-aea/api/aea/) class inherits from the
[`Agent`](https://valory-xyz.github.io/open-aea/api/agent/) and extends it with
additional functionality.



The abstract class [`SkillComponent`](https://valory-xyz.github.io/open-aea/api/skills/base/#skillcomponent-objects)
serves as the base class for the implementation of all the internal components of the AEA [`Skills`](https://valory-xyz.github.io/open-aea/skill/). Upon instantiation, it receives a [`SkillContext`](https://valory-xyz.github.io/open-aea/api/skills/base/#skillcontext-objects) object, which
provides access to the `shared_state`.

```python
class SkillContext:
    """This class implements the context of a skill."""

    @property
    def shared_state(self) -> Dict[str, Any]:
        """Get the shared state dictionary."""
    ...


class SkillComponent(ABC):
    """This class defines an abstract interface for skill component classes."""

    def __init__(
        self,
        skill_context: SkillContext,
        ...
    ):
        """Initialize a skill component."""

    @abstractmethod
    def setup(self) -> None:
        """Implement the setup."""

    @property
    def context(self) -> SkillContext:
        """Get the context of the skill component."""

    @abstractmethod
    def teardown(self) -> None:
        """Implement the teardown."""
    ...

```

Then, the classes
[`Model`](https://valory-xyz.github.io/open-aea/api/skills/base/#model-objects),
[`Handler`](https://valory-xyz.github.io/open-aea/api/skills/base/#handler-objects), and
[`Behaviour`](https://valory-xyz.github.io/open-aea/api/skills/base/#behaviour-objects) implement the class [`SkillComponent`](https://valory-xyz.github.io/open-aea/api/skills/base/#skillcomponent-objects). Note that the abstract methods `setup()` and `teardown()` force the developer to
ensure these methods are implemented on any concrete subclass implementation.

```python
class Model(SkillComponent, ABC):
    """This class implements an abstract model."""
    ...


class Handler(SkillComponent, ABC):
    """This class implements an abstract behaviour."""

    @abstractmethod
    def handle(self, message: Message) -> None:
        """Implement the reaction to a message."""

    def handle_wrapper(self, message: Message) -> None:
        """Wrap the call of the handler. This method must be called only by the framework."""
    ...


class AbstractBehaviour(SkillComponent, ABC):

    @property
    def tick_interval(self) -> float:
        """Get the tick_interval in seconds."""

    @property
    def start_at(self) -> Optional[datetime.datetime]:
        """Get the start time of the behaviour."""
    ...


class Behaviour(AbstractBehaviour, ABC):

    @abstractmethod
    def act(self) -> None:
        """Implement the behaviour."""

    def act_wrapper(self) -> None:
        """Wrap the call of the action. This method must be called only by the framework."""
    ...
```

Also, note that the
[`Behaviour`](https://valory-xyz.github.io/open-aea/api/skills/base/#behaviour-objects) class
has access to two additional properties, `tick_interval` and `start_at`, which
allow that the [`Behaviour`](https://valory-xyz.github.io/open-aea/api/skills/base/#behaviour-objects), or more concretely, the `act()` method, be invoked periodically,
starting from the designated time. A simple concrete implementation of [`Behaviour`](https://valory-xyz.github.io/open-aea/api/skills/base/#behaviour-objects),
one which we will return to in the next section, looks as follows:

```python
class SimpleBehaviour(Behaviour, ABC):
    """This class implements a simple behaviour."""

    def setup(self) -> None:
        """Set the behaviour up."""

    def act(self) -> None:
        """Do the action."""

    def teardown(self) -> None:
        """Tear the behaviour down."""
```
The following diagram summarizes the relationship between the classes presented above:
<div class="mermaid">
classDiagram
    SkillComponent <|-- Model
    SkillComponent <|-- Handler
    SkillComponent <|-- AbstractBehaviour
    AbstractBehaviour <|-- Behaviour
    Behaviour <|-- SimpleBehaviour
    class SkillComponent {
        +skill_context: SkillContext
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
    class SimpleBehaviour {
        +setup(self)
        +act(self)
        +teardown(self)
    }
</div>




<!--
## The implementation `Skill`

A [`Skill`](https://valory-xyz.github.io/open-aea/api/skills/base/#skill-objects)
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
