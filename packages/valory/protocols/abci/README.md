# ABCI Protocol

## Description

This is a protocol for interacting with an ABCI client/server requests and responses.

## Specification

The specification is inspired from
[the Protobuf file `types.proto` for the ABCI protocol](https://github.com/tendermint/tendermint/blob/v0.34.11/proto/tendermint/abci/types.proto).

```yaml
---
name: abci
author: valory
version: 0.1.0
description: A protocol for ABCI requests and responses.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: valory/abci:0.1.0
speech_acts:
#  requests
    request_echo:
      message: pt:str
    request_flush: {}
    request_info:
      version: pt:str
      block_version: pt:int
      p2p_version: pt:int
    request_init_chain:
      time: ct:Timestamp
      chain_id: pt:str
      # begin ConsensusParams
      # BlocksParams
      # https://github.com/tendermint/tendermint/blob/v0.34.11/proto/tendermint/abci/types.proto#L291
      # Note, must be greater than 0
      block_max_bytes: pt:int
      # Note, must be greater or equal to -1
      block_max_gas: pt:int
      # EvidenceParams
      evidence_max_age_num_blocks: pt:int
      evidence_max_age_duration_seconds: pt:int
      evidence_max_age_duration_nanos: pt:int
      evidence_max_bytes: pt:int
      # ValidatorParams
      validator_pub_key_types: pt:list[pt:str]
      # VersionParams
      version_app_version: pt:int
      # end ConsensusParams
      # ValidatorUpdates
      # https://github.com/tendermint/tendermint/blob/v0.34.11/proto/tendermint/abci/types.proto#L342
      validators_updates_pub_key: pt:list[pt:bytes]
      validators_power: pt:list[pt:int]
      
      app_state_bytes: pt:bytes
      initial_height: pt:str
#    request_query: {}
#    request_begin_block: {}
#    request_check_tx: {}
#    request_deliver_tx: {}
#    request_end_block: {}
#    request_commit: {}
#    request_list_snapshots: {}
#    request_offer_snapshot: {}
#    request_load_snapshot_chunk: {}
#    request_apply_snapshot_chunk: {}
# responses
    response_exception: {}
    response_echo:
      message: pt:str
    response_flush: {}
    response_info:
      data: pt:str
      version: pt:str
      app_version: pt:int
      last_block_height: pt:int
      last_block_app_hash: pt:bytes
    response_init_chain:
      # begin ConsensusParams
      # BlocksParams
      # https://github.com/tendermint/tendermint/blob/v0.34.11/proto/tendermint/abci/types.proto#L291
      # Note, must be greater than 0
      block_max_bytes: pt:int
      # Note, must be greater or equal to -1
      block_max_gas: pt:int
      # EvidenceParams
      evidence_max_age_num_blocks: pt:int
      evidence_max_age_duration_seconds: pt:int
      evidence_max_age_duration_nanos: pt:int
      evidence_max_bytes: pt:int
      # ValidatorParams
      validator_pub_key_types: pt:list[pt:str]
      # VersionParams
      version_app_version: pt:int
      # end ConsensusParams
      # ValidatorUpdates
      # https://github.com/tendermint/tendermint/blob/v0.34.11/proto/tendermint/abci/types.proto#L342
      validators_updates_pub_key: pt:list[pt:bytes]
      validators_power: pt:list[pt:int]

      app_hash: pt:bytes
    #    response_query: {}
    #    response_begin_block: {}
    #    response_check_tx: {}
    #    response_deliver_tx: {}
    #    response_end_block: {}
    #    response_commit: {}
    #    response_list_snapshots: {}
    #    response_offer_snapshot: {}
    #    response_load_snapshot_chunk: {}
    #    response_apply_snapshot_chunk: {}
...
---
ct:Timestamp: |
  // Represents seconds of UTC time since Unix epoch
  // 1970-01-01T00:00:00Z. Must be from 0001-01-01T00:00:00Z to
  // 9999-12-31T23:59:59Z inclusive.
  int64 seconds = 1;
  // Non-negative fractions of a second at nanosecond resolution. Negative
  // second values with fractions must still have non-negative nanos values
  // that count forward in time. Must be from 0 to 999,999,999
  // inclusive.
  int32 nanos = 2;
...
---
initiation: [request_echo, request_flush]
reply:
  request_echo: [response_echo, response_exception]
  response_echo: []
  response_exception: []
  request_flush: [response_flush, response_exception]
  response_flush: []
  request_info: [response_info, response_exception]
  response_info: []
  request_init_chain: [response_init_chain, response_exception]
  response_init_chain: []
termination: [response_exception, response_echo, response_flush, response_info, response_init_chain]
roles: {client, server}
end_states: [successful]
keep_terminal_state_dialogues: false
...
```

## Links

* <a href="https://www.w3.org/Protocols/rfc2616/rfc2616.html" target="_blank">HTTP Specification</a>
