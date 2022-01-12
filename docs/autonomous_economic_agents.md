# Autonomous Economic Agents

It is assumed the reader has a decent understanding of the 
[open AEA framework](https://valory-xyz.github.io/open-aea/).
An introductory guide can be found [here](https://valory-xyz.github.io/open-aea/), 
and the `Behaviour` programming abstraction is of particular relevance in
these next sections.
(see [here](https://valory-xyz.github.io/open-aea/skill/#behaviourspy)).


## Brief recap of key concepts

- Multi agent systems are inherently decentralized
- As a result, conflicts of interest are the norm rather than the exception
- Agents operate asynchronously and due to this decoupling even time keeping is 


- AEA communicate asynchrously using Enveloppes that 
contain a message that adheres to a specific messaging protocol.
- 

Every skill, that is to say both behaviours and handlers, is associated with an 
agent since it is registered to it. Skills and agents have their own respective
`context` attributes, instances of `SkillContext` and `AgentContext`, however
both of these allow access to a ```shared state```. This shared state is what 
skills can alter, either through the expression of behaviour or by the handling 
of messages.


## 


## 





