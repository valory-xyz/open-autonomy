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

## How `AsyncBehaviour` works

The behaviour execution model of the AEA framework is the following. 
At the AEA startup, the framework registers a periodic task,
one for each `Behaviour` object `b`, that executes the `b.act` 
method. Such periodic execution for behaviour `b`
is scheduled in the main thread loop,
with a tick interval `b.tick_interval` and starting time `b.start_at`.
As mentioned above, the code in `act()` should not be blocking,
as otherwise it would block the main thread execution, and
therefore it would prevent the execution of the other behaviours' `act()`
and the processing of incoming messages. 

The `AsyncBehaviour` utility class allows to wrap the execution
of the `act()` method allowing its execution to be "suspended"
and resumed upon the happening of certain events 
(e.g. the receiving of a message, a sleep timeout etc.).
Currently, the crux of the implementation is the 
[Python built-in generator machinery](https://docs.python.org/3/reference/expressions.html#yield-expressions):

- from the developer perspective, the execution can be suspended by using 
  `yield` or `yield from` expressions. This will return a generator object 
  to the framework, which is opportunely stored in an object attribute; 
- from the framework perspective, the execution can be resumed by "sending" a
  value to the generator object, using the [`send()`](https://docs.python.org/3/reference/expressions.html#generator.send) 
  method of the generator object The value can be `None`, 
  or a message sent by another skill component.

The abstract methods the developer should implement are called
`async_act_wrapper` and `async_act`.

The sequence diagram below gives the idea of what happens when the
`act()` method of an `AsyncBehaviour` is called:

<div class="mermaid">
    sequenceDiagram

        participant Main loop
        participant AsyncBehaviour

        note over AsyncBehaviour: state READY
        
        loop StopIteration not raised
            Main loop->>AsyncBehaviour: act()
            alt state == READY
                note over AsyncBehaviour: self.gen = self.async_act_wrapper()<br/>self.gen.send(None)
                note over AsyncBehaviour: state RUNNING
            else state == RUNNING
                note over AsyncBehaviour: self.gen.send(None)
            else StopIteration
                note over AsyncBehaviour: state READY
            end
            AsyncBehaviour->>Main loop: (return)
        end
</div>

In words, the first time the `act()` method is called:

1. first, it creates the generator object by calling the used-defined `async_act_wrapper()`;
2. it triggers the first execution by sending the `None` value;
3. it returns the execution control at the first `yield` statement;
4. sets the state to `RUNNING`;
5. returns to the caller in the main loop.

## Blocking requests

As explained above, one of the common tasks for a behaviour is
to interact with other services and/or agents via message-based
communication. In this section, we focus on a sequence of
request-response interactions through the agent interaction protocols.

### The idiomatic approach

TODO

### Using the `AsyncBehaviour`

TODO
