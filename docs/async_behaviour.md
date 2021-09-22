# `AsyncBehaviour`

!!!warning

    The content of this section is subject to change. Some parts
    might soon become obsolete (especially the API documentation).

The `AsyncBehaviour` class, introduced in the `valory/abstract_round_abci`
skill, is a mixin class that allows the AEA developer to use
asynchronous programming patterns in a `Behaviour` implementation.

It is assumed the reader has basic knowledge of the 
[AEA framework](https://fetchai.github.io/agents-aea/),
in particular of the `Behaviour` programming abstraction
(see [here](https://fetchai.github.io/agents-aea/skill-guide/#step-2-develop-a-behaviour) 
and [here](https://fetchai.github.io/agents-aea/skill/#behaviourspy)
).

## Why?

The main motivation behind the `AsyncBehaviour` utility class
is that in idiomatic AEA behaviour development, the `act` method
cannot contain blocking code or long-running tasks, as otherwise 
the AEA thread that executes all the behaviours would get stuck.
For example, in order to interact with an external component through
a request-response pattern (e.g. sending requests to an HTTP server, 
request the Decision Maker to sign a transaction), the usual approach
is to:

- send the message from the `act` method and update the state
    into "waiting for the response" (e.g. by updating an attribute in 
    the shared state or in the behaviour instance, or by using the 
    ["State pattern"](https://gameprogrammingpatterns.com/state.html)),
    such that the next call to `act` can be intercepted and controlled by the developer;
- receive the response in a concrete `Handler` object that is registered 
    to process messages of the response protocol;
- handle the response in the handler's `handle()` method according to the 
    skill business logic and the current state behaviour, and notify 
    the behaviour about the change of state (e.g. by updating an attribute 
    in the shared state such that the next `act` call can read it and take 
    a different execution path).

For large and complex skills, this development approach is quite expensive 
in terms of maintainability, as the business logic does not reside in a single 
skill component (in a behaviour class), but in many skill components 
(in the handler classes, one for each interaction protocol required by the behaviour).


