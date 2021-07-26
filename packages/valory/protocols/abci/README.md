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
      consensus_params: ct:ConsensusParams
      validators: ct:ValidatorUpdates      
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
      consensus_params: ct:ConsensusParams
      validators: ct:ValidatorUpdates      
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
ct:ConsensusParams: |
  message Duration {
    int64 seconds = 1;
    int32 nanos = 2;
  }
  message BlockParams {
      int64 max_bytes = 1;
      int64 max_gas = 2;
  }
  message EvidenceParams {
    int64 max_age_num_blocks = 1;
    Duration max_age_duration = 2;
    int64 max_bytes = 3;
  }
  message ValidatorParams {
    repeated string pub_key_types = 1;
  }
  message VersionParams {
    uint64 app_version = 1;
  }
  BlockParams block = 1;
  EvidenceParams evidence = 2;
  ValidatorParams validator = 3;
  VersionParams version = 4;
ct:ValidatorUpdates: |
  message ValidatorUpdate {
    bytes pub_key = 1;
    int64 power = 2;
  }
  repeated ValidatorUpdate validators = 1;
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
