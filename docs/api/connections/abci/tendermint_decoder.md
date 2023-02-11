<a id="packages.valory.connections.abci.tendermint_decoder"></a>

# packages.valory.connections.abci.tendermint`_`decoder

Decode AEA messages from Tendermint protobuf messages.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder"></a>

## `_`TendermintProtocolDecoder Objects

```python
class _TendermintProtocolDecoder()
```

Decoder called by the server to process requests from the TCP connection with Tendermint.

It translates from Tendermint's ABCI Protobuf messages into the AEA's ABCI protocol messages.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.process"></a>

#### process

```python
@classmethod
def process(cls, message: Request, dialogues: AbciDialogues,
            counterparty: str) -> Optional[Tuple[AbciMessage, AbciDialogue]]
```

Process an ABCI request or response.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_echo"></a>

#### request`_`echo

```python
@classmethod
def request_echo(cls, request: Request, dialogues: AbciDialogues,
                 counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode an echo request.

**Arguments**:

- `request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_flush"></a>

#### request`_`flush

```python
@classmethod
def request_flush(cls, _request: Request, dialogues: AbciDialogues,
                  counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a flush request.

**Arguments**:

- `_request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_info"></a>

#### request`_`info

```python
@classmethod
def request_info(cls, request: Request, dialogues: AbciDialogues,
                 counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a info request.

**Arguments**:

- `request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_set_option"></a>

#### request`_`set`_`option

```python
@classmethod
def request_set_option(cls, request: Request, dialogues: AbciDialogues,
                       counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a set_option request.

**Arguments**:

- `request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_init_chain"></a>

#### request`_`init`_`chain

```python
@classmethod
def request_init_chain(cls, request: Request, dialogues: AbciDialogues,
                       counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a init_chain request.

**Arguments**:

- `request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_begin_block"></a>

#### request`_`begin`_`block

```python
@classmethod
def request_begin_block(cls, request: Request, dialogues: AbciDialogues,
                        counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a begin_block request.

**Arguments**:

- `request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_check_tx"></a>

#### request`_`check`_`tx

```python
@classmethod
def request_check_tx(cls, request: Request, dialogues: AbciDialogues,
                     counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a check_tx request.

**Arguments**:

- `request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_deliver_tx"></a>

#### request`_`deliver`_`tx

```python
@classmethod
def request_deliver_tx(cls, request: Request, dialogues: AbciDialogues,
                       counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a deliver_tx request.

**Arguments**:

- `request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_query"></a>

#### request`_`query

```python
@classmethod
def request_query(cls, request: Request, dialogues: AbciDialogues,
                  counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a query request.

**Arguments**:

- `request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_commit"></a>

#### request`_`commit

```python
@classmethod
def request_commit(cls, _request: Request, dialogues: AbciDialogues,
                   counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a commit request.

**Arguments**:

- `_request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_end_block"></a>

#### request`_`end`_`block

```python
@classmethod
def request_end_block(cls, request: Request, dialogues: AbciDialogues,
                      counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode an end_block request.

**Arguments**:

- `request`: the request.
- `dialogues`: the dialogues object.
- `counterparty`: the counterparty.

**Returns**:

the AbciMessage request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_list_snapshots"></a>

#### request`_`list`_`snapshots

```python
@classmethod
def request_list_snapshots(
        cls, _request: Request, dialogues: AbciDialogues,
        counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a list_snapshots request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_offer_snapshot"></a>

#### request`_`offer`_`snapshot

```python
@classmethod
def request_offer_snapshot(
        cls, request: Request, dialogues: AbciDialogues,
        counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a offer_snapshot request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_load_snapshot_chunk"></a>

#### request`_`load`_`snapshot`_`chunk

```python
@classmethod
def request_load_snapshot_chunk(
        cls, request: Request, dialogues: AbciDialogues,
        counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a load_snapshot_chunk request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.request_apply_snapshot_chunk"></a>

#### request`_`apply`_`snapshot`_`chunk

```python
@classmethod
def request_apply_snapshot_chunk(
        cls, request: Request, dialogues: AbciDialogues,
        counterparty: str) -> Tuple[AbciMessage, AbciDialogue]
```

Decode a apply_snapshot_chunk request.

<a id="packages.valory.connections.abci.tendermint_decoder._TendermintProtocolDecoder.no_match"></a>

#### no`_`match

```python
@classmethod
def no_match(cls, _request: Request, _dialogues: AbciDialogues,
             _counterparty: str) -> None
```

Handle the case in which the request is not supported.

