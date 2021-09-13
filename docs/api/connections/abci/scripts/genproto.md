<a id="packages.valory.connections.abci.scripts.genproto"></a>

# packages.valory.connections.abci.scripts.genproto

Update Python modules from Tendermint Protobuf files.

NOTE: This code is adapted from the google protobuf Python library. Specifically from the setup.py file.

<a id="packages.valory.connections.abci.scripts.genproto.generate_proto"></a>

#### generate`_`proto

```python
def generate_proto(source: str) -> None
```

Generate a protobuf file.

Invokes the Protocol Compiler to generate a _pb2.py from the given
.proto file.  Does nothing if the output already exists and is newer than
the input.

**Arguments**:

- `source`: path to the source.

