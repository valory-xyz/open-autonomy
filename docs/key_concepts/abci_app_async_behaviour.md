!!!note
    For clarity, the snippets of code presented here are a simplified version of the actual
    implementation. We refer the reader to the {{open_autonomy_api}} for the complete details.

The `AsyncBehaviour` class, introduced in the `valory/abstract_round_abci`
Skill, is a mixin class that allows the AEA developer to use
asynchronous programming patterns in a `Behaviour` implementation. Since it is usual that many of the tasks to be carried by the state behaviours are long-running, this is the base class from which FSM Behaviours will be typically derived from.

## The Need for Asynchronous Behaviours

The main motivation behind the `AsyncBehaviour` utility class
is that in idiomatic AEA behaviour development, the `act` method
cannot contain blocking code or long-running tasks, as otherwise
the AEA main thread that executes all the behaviours would get stuck.
For example, in order to interact with an external component through
a request-response pattern, e.g., sending a request to an HTTP server and waiting for its response, or
request the [Decision Maker](https://open-aea.docs.autonolas.tech/decision-maker/) to sign a transaction. The usual approach in this case is to:

1. Send the message from the `act()` method and update the state
  into "waiting for the response" (e.g., by updating an attribute in
  the shared state or in the behaviour instance, or by using the
  [state pattern](https://gameprogrammingpatterns.com/state.html)),
  such that the next call to `act()` can be intercepted and controlled by the developer.
2. Receive the response in a concrete `Handler` object that is registered
  to process messages of the response protocol.
3. Handle the response in the handler's `handle()` method according to the
  skill business logic and the current state behaviour, and notify
  the behaviour about the change of state (e.g. by updating an attribute
  in the shared state such that the next `act` call can read it and take
  a different execution path).

For large and complex skills, this development approach is quite error-prone and expensive
in terms of maintainability, as the business logic does not reside in a single
skill component (i.e., in a behaviour class), but also in several other skill components (i.e., in the handler classes, one for each interaction protocol required by the behaviour).

## Asynchronous Programming to the Rescue

A well-known programming technique that turned out very useful in the
web development community is [asynchronous programming](https://en.wikipedia.org/wiki/Asynchrony_(computer_programming)).

Informally, a programming language that supports asynchronous
programming allows running blocking operations _asynchronously_:
the operation is not run in the same thread where the call happened,
but it is delegated to another executor, e.g., another thread/process,
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
At the AEA startup, the framework registers a periodic task, one for each
`Behaviour` object `b`, that executes the `b.act` method. Such periodic
execution for behaviour `b` is scheduled in the main thread loop,
with a tick interval `b.tick_interval` and starting time `b.start_at`.
As mentioned above, the code in `act()` should not be blocking,
as otherwise it would block the main thread execution, and
therefore it would prevent the execution of the other behaviours' `act()`
and the processing of incoming messages.

```python
class SimpleBehaviour(Behaviour, ABC):
    """This class implements a simple behaviour."""

    def act(self) -> None:
        """Do the action."""
    # (...)
```

The `AsyncBehaviour` utility class allows to wrap the execution
of the `act()` method allowing its execution to be "suspended"
and resumed upon the happening of certain events
(e.g. the receiving of a message, a sleep timeout etc.).
Currently, the crux of the implementation is the
[Python built-in generator machinery](https://docs.python.org/3/reference/expressions.html#yield-expressions):

- from the developer perspective, the execution can be suspended by using
  `yield` or `yield from` expressions. This will return a generator object
  to the framework, which can opportunely be stored in an object attribute;
- from the framework perspective, the execution can be resumed by "sending" a
  value to the generator object, using the [`send()`](https://docs.python.org/3/reference/expressions.html#generator.send)
  method of the generator object. The value can be `None`,
  or a message sent by another skill component.

```python
class AsyncBehaviour(ABC):

    @abstractmethod
    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

    @abstractmethod
    def async_act_wrapper(self) -> Generator:
        """Do the act, supporting asynchronous execution."""
    # (...)
```

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

Any subsequent calls to the ```act()``` method are redirected to the generator
whose execution was triggered by the first call, which invokes ```async_act()```.


## A simple example

Consider a [(one-shot) behaviour](https://open-aea.docs.autonolas.tech/skill/#behaviourspy)
whose logic is to print a sequence of messages separated by a sleep interval:

```python

class PrintBehaviour(OneShotBehaviour, AsyncBehaviour):

    def async_act_wrapper(self):
        yield from self.async_act()

    def async_act(self):
        print("First message")
        yield from self.sleep(1.0)
        print("Second message")
        yield from self.sleep(1.0)
        print("Third message")
```

Without `AsyncBehaviour`, one should take care of:

- remembering the "state" of the behaviour (i.e. what is the last message printed)
- handling the sleep interval by hand

This is a naive implementation
```python
import datetime
from aea.skills.behaviours import SimpleBehaviour


class PrintBehaviour(SimpleBehaviour):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = 0

        # remember time of last printed message
        self.last_time = None
        # timedelta of 0 days, 1 second
        self.timedelta = datetime.timedelta(0, 1)

    def act(self):
        now = datetime.datetime.now()
        if self.state == 0:
            print("First message")
            self.state += 1
            self.last_time = now
            return
        if self.state == 1 and now > (self.last_time + self.timedelta):
            print("Second message")
            self.state += 1
            self.last_time = now
            return
        if self.state == 2 and now > (self.last_time + self.timedelta):
            print("Third message")
            self.state += 1
            self.last_time = now
            return
        # do nothing
```


## Blocking requests

As explained above, one of the common tasks for a behaviour is
to interact with other services and/or agents via message-based
communication. In this section, we focus on a sequence of
request-response interactions through agent interaction protocols.
We consider the `fetchai/generic_buyer` skill as an example ([link to code](https://github.com/valory-xyz/open-aea/tree/v1.37.0/packages/fetchai/skills/generic_buyer)).

### The idiomatic approach

The idiomatic approach, implemented in the skill `fetchai/generic_buyer`,
is outlined in the sequence diagram below. The suffix `B` is a shorthand
for `Behaviour`, and `H` is a shorthand for `Handler`.

<div class="mermaid">
    sequenceDiagram

        participant SearchB
        participant SearchH
        participant TransactionB
        participant SigningH
        participant LedgerH
        participant DecisionMaker
        participant FipaH
        participant OEF
        participant Seller
        participant Ledger

        SearchB->>ADS: "search for sellers"
        ADS->>SearchH: listOfAgents
        SearchH->>Seller: call for proposals
        Seller->>FipaH: proposals
        note over FipaH, Seller: buyer and seller negotiate...
        note over FipaH, Seller: buyer is ready to pay the seller
        FipaH->>TransactionB: transaction tx
        TransactionB->>DecisionMaker: signingRequest(tx)
        DecisionMaker->>SigningH: signed_tx
        SigningH->>Ledger: signed_tx
        Ledger->>LedgerH: tx_hash
        LedgerH->>Seller: tx_hash
        Seller->>FipaH: bought data
</div>

The participants `SearchB`, `SearchH`, `TransactionB`, `SigningH`, `LedgerH`, `FipaH`
and `DecisionMaker` are **internal components** of the buyer AEA,
whereas `ADS`, `Seller`, and `Ledger` are **external actors**.

Follows the breakdown of each message exchange:

- The buyer starts by searching for seller of the desired data,
  and the search behaviour (`SearchB`) sends a search request to an
  agent discovery service (ADS);
- The search result of the ADS gets routed to the search handler (`SearchH`),
  which selects one of the sellers, and sends a "call for proposal" (CFP) message to him.
  The CFP is the first message of a
  [FIPA protocol interaction](http://www.fipa.org/repository/ips.php3).
  See the AEA documentation on the
  [AEA FIPA-like protocol](https://open-aea.docs.autonolas.tech/protocol/#fetchaifipa100-protocol).
- The seller replies with a "FIPA proposal" to the buyer. Such message
  is handled by the `FipaH` handler;
- Once the negotiation has completed (only the `FipaH` is involved in the negotiation),
  the `FipaH` handler sends the payment transaction to the `TransactionB` behaviour
  such that it can be processed;
- The `TransactionB`, which was periodically listening for new transaction to process,
  reads the new transaction and sends a signing requests to the
  [DecisionMaker](https://open-aea.docs.autonolas.tech/api/decision_maker/base/).
  Note that a skill component does not have access to the crypto identity of
  an AEA, and it has to rely on the
  [DecisionMaker](https://open-aea.docs.autonolas.tech/api/decision_maker/base/)
  for certain operations, such as the signing of transactions.
- The [`DecisionMaker`](https://open-aea.docs.autonolas.tech/decision-maker/)
  sends the response to the dedicated handler, the `SigningH`.
  The `SigningH` submit the transactions to the `Ledger` (through the `ledger_api` connection);
- The `Ledger`'s response (the transaction hash) is handled by the `LedgerH` handler,
  which in turn sends the transaction hash to the `Seller`
- The `Seller`, once the transaction has been validated, will send the
  bought data to the buyer with an FIPA "inform" message, which is handled
  by the `FipaH` handler.

The business logic is spread across different skill components, behaviours and handlers,
due to the "forced callback" mechanism that forces the developer to handle the message
of an interaction protocol in the handler registered for that protocol.


### Using the `AsyncBehaviour`

The above example can be reimplemented in an `AsyncBehaviour` in
the following way (Python-pseudocode):

```python


class GenericBuyerBehaviour(OneShotBehaviour, AsyncBehaviour):

    def async_act_wrapper(self):
        yield from self.async_act()

    def async_act(self):
        search_request = build_search_request(...)
        # send search request to the ADS
        # and (asynchronously) wait for the response
        response = yield from send(search_request)
        agents = response.result
        # pick the first agent in the result list
        seller = agents[0]

        # send CFP to the seller
        # and (asynchronously) wait for the response
        cfp = build_cfp(...)
        response = yield from send(cfp, to=seller)

        # here there should be the buyer strategy
        # for the negotiation with the seller...
        # (...)

        # in case both parties accept the negotiation outcome:
        tx = build_tx(...)

        # send transaction to the decision maker
        # and (asynchronously) wait for the response
        signed_tx = yield from send(tx)

        # send transaction to the distributed ledger
        # and (asynchronously) wait for the response
        tx_hash = yield from send(signed_tx)

        # send transaction hash to the seller
        send(tx_hash, to=seller)

        # wait until the seller sends the data
        inform_message = yield from self.wait_for_message()
        print(inform_message.data)

        # done!
```

As you can see, the core business logic of the buyer resides in the `async_act`
method. Many details of the implementation are omitted, like
the utility functions like `build_*` and `send`,
but they are conceptually similar to what is done in the handlers of the
`fetchai/generic_buyer` skill.

The `wait_for_message` method, uses the `send(...)` method to wait for the
response, allowing it to wait for specific events triggered
by other components. In this case, each of the handlers will
dispatch the response to the requester component, whose request
is identified by the [(dialogue) identifier](https://open-aea.docs.autonolas.tech/protocol/#dialogue-rules)
of the interaction.
However, note that the handler code in this case is _skill-independent_,
which means that they do not contribute to the business logic.
