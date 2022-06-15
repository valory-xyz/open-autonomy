<a id="packages.valory.connections.abci.tendermint_encoder"></a>

# packages.valory.connections.abci.tendermint`_`encoder

Encode AEA messages into Tendermint protobuf messages.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder"></a>

## `_`TendermintProtocolEncoder Objects

```python
class _TendermintProtocolEncoder()
```

Decoder called by the server to process requests *towards* the TCP connection with Tendermint.

It translates from the AEA's ABCI protocol messages into Tendermint's ABCI Protobuf messages.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.process"></a>

#### process

```python
@classmethod
def process(cls, message: AbciMessage) -> Optional[Union[Request, Response]]
```

Encode an AbciMessage object into either Request or Response protobuf objects.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_exception"></a>

#### response`_`exception

```python
@classmethod
def response_exception(cls, message: AbciMessage) -> Response
```

Process the response exception.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_echo"></a>

#### response`_`echo

```python
@classmethod
def response_echo(cls, message: AbciMessage) -> Response
```

Process the response echo.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_set_option"></a>

#### response`_`set`_`option

```python
@classmethod
def response_set_option(cls, message: AbciMessage) -> Response
```

Process the response set_option.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_info"></a>

#### response`_`info

```python
@classmethod
def response_info(cls, message: AbciMessage) -> Response
```

Process the response info.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_flush"></a>

#### response`_`flush

```python
@classmethod
def response_flush(cls, _message: AbciMessage) -> Response
```

Process the response flush.

**Arguments**:

- `_message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_init_chain"></a>

#### response`_`init`_`chain

```python
@classmethod
def response_init_chain(cls, message: AbciMessage) -> Response
```

Process the response init_chain.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_query"></a>

#### response`_`query

```python
@classmethod
def response_query(cls, message: AbciMessage) -> Response
```

Process the response query.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_check_tx"></a>

#### response`_`check`_`tx

```python
@classmethod
def response_check_tx(cls, message: AbciMessage) -> Response
```

Process the response check_tx.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_deliver_tx"></a>

#### response`_`deliver`_`tx

```python
@classmethod
def response_deliver_tx(cls, message: AbciMessage) -> Response
```

Process the response deliver_tx.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_begin_block"></a>

#### response`_`begin`_`block

```python
@classmethod
def response_begin_block(cls, message: AbciMessage) -> Response
```

Process the response begin_block.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_end_block"></a>

#### response`_`end`_`block

```python
@classmethod
def response_end_block(cls, message: AbciMessage) -> Response
```

Process the response end_block.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_commit"></a>

#### response`_`commit

```python
@classmethod
def response_commit(cls, message: AbciMessage) -> Response
```

Process the response commit.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_list_snapshots"></a>

#### response`_`list`_`snapshots

```python
@classmethod
def response_list_snapshots(cls, message: AbciMessage) -> Response
```

Process the response list_snapshots.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_offer_snapshot"></a>

#### response`_`offer`_`snapshot

```python
@classmethod
def response_offer_snapshot(cls, message: AbciMessage) -> Response
```

Process the response offer_snapshot.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_load_snapshot_chunk"></a>

#### response`_`load`_`snapshot`_`chunk

```python
@classmethod
def response_load_snapshot_chunk(cls, message: AbciMessage) -> Response
```

Process the response load_snapshot_chunk.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.response_apply_snapshot_chunk"></a>

#### response`_`apply`_`snapshot`_`chunk

```python
@classmethod
def response_apply_snapshot_chunk(cls, message: AbciMessage) -> Response
```

Process the response apply_snapshot_chunk.

**Arguments**:

- `message`: the response.

**Returns**:

the ABCI protobuf object.

<a id="packages.valory.connections.abci.tendermint_encoder._TendermintProtocolEncoder.no_match"></a>

#### no`_`match

```python
@classmethod
def no_match(cls, _request: Request) -> None
```

No match.

