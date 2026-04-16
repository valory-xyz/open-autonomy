<a id="packages.valory.skills.abstract_round_abci.handlers"></a>

# packages.valory.skills.abstract`_`round`_`abci.handlers

This module contains the handler for the 'abstract_round_abci' skill.

<a id="packages.valory.skills.abstract_round_abci.handlers.exception_to_info_msg"></a>

#### exception`_`to`_`info`_`msg

```python
def exception_to_info_msg(exception: Exception) -> str
```

Transform an exception to an info string message.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler"></a>

## ABCIRoundHandler Objects

```python
class ABCIRoundHandler(ABCIHandler)
```

ABCI handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.info"></a>

#### info

```python
def info(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'info' request.

As per Tendermint spec (https://github.com/tendermint/spec/blob/038f3e025a19fed9dc96e718b9834ab1b545f136/spec/abci/abci.md#info):

- Return information about the application state.
- Used to sync Tendermint with the application during a handshake that happens on startup.
- The returned app_version will be included in the Header of every block.
- Tendermint expects last_block_app_hash and last_block_height to be updated during Commit, ensuring that Commit is never called twice for the same block height.

**Arguments**:

- `message`: the ABCI request.
- `dialogue`: the ABCI dialogue.

**Returns**:

the response.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.init_chain"></a>

#### init`_`chain

```python
def init_chain(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle a message of REQUEST_INIT_CHAIN performative.

As per Tendermint spec (https://github.com/tendermint/spec/blob/038f3e025a19fed9dc96e718b9834ab1b545f136/spec/abci/abci.md#initchain):

- Called once upon genesis.
- If ResponseInitChain.Validators is empty, the initial validator set will be the RequestInitChain.Validators.
- If ResponseInitChain.Validators is not empty, it will be the initial validator set (regardless of what is in RequestInitChain.Validators).
- This allows the app to decide if it wants to accept the initial validator set proposed by tendermint (ie. in the genesis file), or if it wants to use a different one (perhaps computed based on some application specific information in the genesis file).

**Arguments**:

- `message`: the ABCI request.
- `dialogue`: the ABCI dialogue.

**Returns**:

the response.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.begin_block"></a>

#### begin`_`block

```python
def begin_block(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'begin_block' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.check_tx"></a>

#### check`_`tx

```python
def check_tx(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'check_tx' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.settle_pending_offence"></a>

#### settle`_`pending`_`offence

```python
def settle_pending_offence(accused_agent_address: Optional[str],
                           invalid: bool) -> None
```

Add an invalid pending offence or a no-offence for the given accused agent address, if possible.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.deliver_tx"></a>

#### deliver`_`tx

```python
def deliver_tx(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'deliver_tx' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.end_block"></a>

#### end`_`block

```python
def end_block(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'end_block' request.

<a id="packages.valory.skills.abstract_round_abci.handlers.ABCIRoundHandler.commit"></a>

#### commit

```python
def commit(message: AbciMessage, dialogue: AbciDialogue) -> AbciMessage
```

Handle the 'commit' request.

As per Tendermint spec (https://github.com/tendermint/spec/blob/038f3e025a19fed9dc96e718b9834ab1b545f136/spec/abci/abci.md#commit):

Empty request meant to signal to the app it can write state transitions to state.

- Persist the application state.
- Return a Merkle root hash of the application state.
- It's critical that all application instances return the same hash. If not, they will not be able to agree on the next block, because the hash is included in the next block!

**Arguments**:

- `message`: the ABCI request.
- `dialogue`: the ABCI dialogue.

**Returns**:

the response.

<a id="packages.valory.skills.abstract_round_abci.handlers.AbstractResponseHandler"></a>

## AbstractResponseHandler Objects

```python
class AbstractResponseHandler(Handler, ABC)
```

Abstract response Handler.

This abstract handler works in tandem with the 'Requests' model.
Whenever a message of 'response' type arrives, the handler
tries to dispatch it to a pending request previously registered
in 'Requests' by some other code in the same skill.

The concrete classes must set the 'allowed_response_performatives'
class attribute to the (frozen)set of performative the developer
wants the handler to handle.

<a id="packages.valory.skills.abstract_round_abci.handlers.AbstractResponseHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.AbstractResponseHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear down the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.AbstractResponseHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Handle the response message.

Steps:
1. Try to recover the 'dialogues' instance, for the protocol
   of this handler, from the skill context. The attribute name used to
   read the attribute is computed by '_get_dialogues_attribute_name()'
   method. If no dialogues instance is found, log a message and return.
2. Try to recover the dialogue; if no dialogue is present, log a message
   and return.
3. Check whether the performative is in the set of allowed performative;
   if not, log a message and return.
4. Try to recover the callback of the request associated to the response
   from the 'Requests' model; if no callback is present, log a message
   and return.
5. If the above check have passed, then call the callback with the
   received message.

**Arguments**:

- `message`: the message to handle.

<a id="packages.valory.skills.abstract_round_abci.handlers.HttpHandler"></a>

## HttpHandler Objects

```python
class HttpHandler(AbstractResponseHandler)
```

The HTTP response handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.SigningHandler"></a>

## SigningHandler Objects

```python
class SigningHandler(AbstractResponseHandler)
```

Implement the transaction handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.LedgerApiHandler"></a>

## LedgerApiHandler Objects

```python
class LedgerApiHandler(AbstractResponseHandler)
```

Implement the ledger handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.ContractApiHandler"></a>

## ContractApiHandler Objects

```python
class ContractApiHandler(AbstractResponseHandler)
```

Implement the contract api handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.TendermintHandler"></a>

## TendermintHandler Objects

```python
class TendermintHandler(Handler)
```

The Tendermint config-sharing request / response handler.

This handler is used to share the information necessary
to set up the Tendermint network. The agents use it during
the RegistrationStartupBehaviour, and communicate with
each other over the Agent Communication Network using a
p2p_libp2p or p2p_libp2p_client connection.

This handler does NOT use the ABCI connection.

<a id="packages.valory.skills.abstract_round_abci.handlers.TendermintHandler.LogMessages"></a>

## LogMessages Objects

```python
class LogMessages(Enum)
```

Log messages used in the TendermintHandler

<a id="packages.valory.skills.abstract_round_abci.handlers.TendermintHandler.LogMessages.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

For ease of use in formatted string literals

<a id="packages.valory.skills.abstract_round_abci.handlers.TendermintHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.TendermintHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear down the handler.

<a id="packages.valory.skills.abstract_round_abci.handlers.TendermintHandler.initial_tm_configs"></a>

#### initial`_`tm`_`configs

```python
@property
def initial_tm_configs() -> Dict[str, Dict[str, Any]]
```

A mapping of the other agents' addresses to their initial Tendermint configuration.

<a id="packages.valory.skills.abstract_round_abci.handlers.TendermintHandler.initial_tm_configs"></a>

#### initial`_`tm`_`configs

```python
@initial_tm_configs.setter
def initial_tm_configs(configs: Dict[str, Dict[str, Any]]) -> None
```

A mapping of the other agents' addresses to their initial Tendermint configuration.

<a id="packages.valory.skills.abstract_round_abci.handlers.TendermintHandler.dialogues"></a>

#### dialogues

```python
@property
def dialogues() -> Optional[TendermintDialogues]
```

Tendermint config-sharing request / response protocol dialogues

<a id="packages.valory.skills.abstract_round_abci.handlers.TendermintHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Handle incoming Tendermint config-sharing messages

<a id="packages.valory.skills.abstract_round_abci.handlers.IpfsHandler"></a>

## IpfsHandler Objects

```python
class IpfsHandler(AbstractResponseHandler)
```

A class for handling IPFS messages.

