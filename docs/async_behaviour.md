# `AsyncBehaviour`

!!!warning

    The content of this section is subject to change. Some parts
    might soon become obsolete (especially the API documentation).

!!!note
    
    At the time this document was written, the `aea` Python pacakge
    used was at version `1.0.1`. For later releases, some content
    of this section may not be relevant anymore.

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

## Asynchronous programming to the rescue

A well-known programming technique that turned out very useful in the
web development community is **asynchronous programming**.

Informally, a programming language that supports asynchronous 
programming features allows running blocking operations _asynchronously_:
the operation is not run in the same thread where the call happened,
but it is delegated to another executor, e.g. another thread/process,
allowing the caller function execution being "suspended" until the operation has completed.
Once the blocking operation has completed, the execution of the function
can process the result and continue as usual.
This lets the main thread to perform other tasks while the function is waiting
for the result of the operation.
 
If the reader is not familiar with asynchronous programming concepts,
we suggest reading the following resources:

- [MDN Web Docs: Asynchronous JavaScript](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous)
- [MDN Web Docs: Glossary: asynchronous](https://developer.mozilla.org/en-US/docs/Glossary/Asynchronous)
- [`asyncio` standard Python library documentation](https://docs.python.org/3/library/asyncio.html)
