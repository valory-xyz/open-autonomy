# Autonomous Economic Agents

!!!note 
    
    The snippets of code here are a simplified representation of the actual 
    implementation

It is assumed the reader has a decent understanding of the 
[open AEA framework](https://github.com/valory-xyz/open-aea).
An [introductory guide](https://valory-xyz.github.io/open-aea/) to this paradigm
is available to help you get started in case you're not yet familiar. 
The [`Behaviour`](https://valory-xyz.github.io/open-aea/skill/#behaviourspy) 
programming abstraction is of particular relevance in these next sections.

## Brief recap of core concepts

Multi-agent systems are inherently decentralized. Each of the agents pursues its
own objectives and as a result, conflicts of interest are expected to arise.
Furthermore, agents operate asynchronously and due to this decoupling and the
absence of a central moderator the resulting system becomes fundamentally 
uncertain. 

So, how then can we create a functional system in which agents can pursue their
objectives without guarantees on how other agents might behave? The answer is 
that we minimize the need to trust other agents in the system by not making 
assumptions on if and how other agent respond. 

Instead of relying on the other party to behave honestly or a third party to 
mediate transactions (e.g. via [escrow](https://en.wikipedia.org/wiki/Escrow)),
we use a shared state in which we record transactions. This shared state takes
the form of a deterministic state machine, which is 
[replicated](https://en.wikipedia.org/wiki/State_machine_replication)
by all the agents so that each has a copy of it. In order to make any changes
to this shared state, the agents need to reach consensus over the update. When 
the majority of the agents which comprise the network decide on a single state, 
consensus is achieved and the shared state is updated accordingly. More 
precisely, state machine replication with `N = 3f + 1` replicas can tolerate 
`f` simultaneous failures, and hence consensus over the new state is reached 
when `ceil((2N + 1) / 3)` of the agents agree on a particular state. Systems 
that posses this fault tolerance are referred to as being
[byzantine fault-tolerant](https://pmg.csail.mit.edu/papers/osdi99.pdf).
The result is a what is called a _trustless_ system, which refers to a system in
which the amount of trust required from any single agent is minimized.
Thus, by not trusting any single authority, this system creates trust by default.

AEAs possess [skills](https://valory-xyz.github.io/open-aea/skill/) which 
allow them to operate proactively, through the expression of 
[behaviour](https://valory-xyz.github.io/open-aea/api/skills/base/#behaviour-objects), 
as well as reactively by managing incoming messages from other agents via
[handlers](https://valory-xyz.github.io/open-aea/api/skills/base/#handler-objects). 
Since there might exist a need to share a certain context which is relevant both
to behaviors and handlers, this can be achieved via 
[models](https://valory-xyz.github.io/open-aea/api/skills/base/#model-objects).


Every skill is associated with an agent since it is registered to it. Skills 
and agents have their own respective `context` attributes, instances of 
[`SkillContext`](https://valory-xyz.github.io/open-aea/api/skills/base/) 
and 
[`AgentContext`](https://valory-xyz.github.io/open-aea/api/context/base/), 
however each of these provides access to a shared state through the `context`
attribute. This shared state is what agents can alter through the usage of 
skills.

AEAs communicate asynchronously with other agents using Envelopes that contain a
message. These messages adhere to specific messaging 
[protocols](https://valory-xyz.github.io/open-aea/protocol/). 
In order for AEAs to communicate with the outside world they need to set up 
[connections](https://valory-xyz.github.io/open-aea/connection/).


## The implementation of `AEA`


```python
class AbstractAgent(ABC):
    """This class provides an abstract base interface for an agent."""
    ...


class Agent(AbstractAgent):
    """This class provides an abstract base class for a generic agent."""
    
    def __init__(self) -> None:
        """Instantiate the agent."""
    
    def setup(self) -> None:
        """Set up the agent."""

    def start(self) -> None:
        """Start the agent."""
    
    def handle_envelope(self, envelope: Envelope) -> None:
        """Handle an envelope."""
        
    def act(self) -> None:
        """Perform actions on period."""
        
    def stop(self) -> None:
        """Stop the agent."""
        
    def teardown(self) -> None:
        """Tear down the agent."""
    
    def get_periodic_tasks(self) -> Dict[...]:
        """Get all periodic tasks for agent."""
    ...
        

class AEA(Agent):
    """This class implements an autonomous economic agent."""

    @property
    def inbox(self) -> InBox:  # pragma: nocover
        """Get the inbox."""
    
    @property
    def outbox(self) -> OutBox:  # pragma: nocover
        """Get the outbox."""

    @property
    def context(self) -> AgentContext:
        """Get (agent) context."""
    ...
```

## The implementation of `Behaviour`


```python
class SkillContext:
    """This class implements the context of a skill."""
    
    @property
    def shared_state(self) -> Dict[str, Any]:
        """Get the shared state dictionary."""
    ...

        
class SkillComponent(ABC):
    """This class defines an abstract interface for skill component classes."""

    @property
    def context(self) -> SkillContext:
        """Get the context of the skill component."""
    ...
        

class AbstractBehaviour(SkillComponent, ABC):
   
    @property
    def tick_interval(self) -> float:
        """Get the tick_interval in seconds."""
        return self._tick_interval

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


class SimpleBehaviour(Behaviour, ABC):
    """This class implements a simple behaviour."""

    def act(self) -> None:
        """Do the action."""
    ...
```

