# ABCI Protocol

## Description

This is a protocol for interacting with an ABCI client/server requests and responses.

## Specification

The specification is inspired from
[the Protobuf file `types.proto` for the ABCI protocol](https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto).

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
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L42
  request_echo:
    message: pt:str
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L46
  request_flush: {}
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L48
  request_info:
    version: pt:str
    block_version: pt:int
    p2p_version: pt:int
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L55
  request_set_option:
    option_key: pt:str
    option_value: pt:str
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L60
  request_init_chain:
    time: ct:Timestamp
    chain_id: pt:str
    consensus_params: pt:optional[ct:ConsensusParams]
    validators: ct:ValidatorUpdates      
    app_state_bytes: pt:bytes
    initial_height: pt:int
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L70
  request_query:
    query_data: pt:bytes
    path: pt:str
    height: pt:int
    prove: pt:bool
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L77
  request_begin_block:
    hash: pt:bytes
    header: ct:Header
    last_commit_info: ct:LastCommitInfo
    byzantine_validators: ct:Evidences
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L89
  request_check_tx:
    tx: pt:bytes
    type: ct:CheckTxType   
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L94
  request_deliver_tx:
    tx: pt:bytes
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L98
  request_end_block:
    height: pt:int
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L102
  request_commit: {}
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L105
  request_list_snapshots: {}
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L109
  request_offer_snapshot:
    snapshot: ct:Snapshot  # snapshot offered by peers
    app_hash: pt:bytes     # light client-verified app hash for snapshot height
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L115
  request_load_snapshot_chunk:
    height: pt:int
    format: pt:int
    chunk_index: pt:int
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L115
  request_apply_snapshot_chunk:
    index: pt:int
    chunk: pt:bytes
    chunk_sender: pt:str  # 'sender' conflicts with the attribute of 'Message'
  # responses
  response_exception: {
    error: pt:str
  }
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L157
  response_echo:
    message: pt:str
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L161
  response_flush: {}
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L163
  response_info:
    info_data: pt:str
    version: pt:str
    app_version: pt:int
    last_block_height: pt:int
    last_block_app_hash: pt:bytes
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L174
  response_set_option:
    code: pt:int
    log: pt:str
    info: pt:str
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L181
  response_init_chain:
    consensus_params: pt:optional[ct:ConsensusParams]
    validators: ct:ValidatorUpdates      
    app_hash: pt:bytes
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L187
  response_query:
    code: pt:int
    log: pt:str
    info: pt:str
    index: pt:int
    key: pt:bytes
    value: pt:bytes
    proof_ops: ct:ProofOps
    height: pt:int
    codespace: pt:str
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L200
  response_begin_block:
    events: ct:Events
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L205
  response_check_tx:
    code: pt:int
    data: pt:bytes
    log: pt:str
    info: pt:str
    gas_wanted: pt:int
    gas_used: pt:int
    events: ct:Events
    codespace: pt:str
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L217
  response_deliver_tx:
    code: pt:int
    data: pt:bytes
    log: pt:str
    info: pt:str
    gas_wanted: pt:int
    gas_used: pt:int
    events: ct:Events
    codespace: pt:str
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L229
  response_end_block:
    validator_updates: ct:ValidatorUpdates
    consensus_param_updates: pt:optional[ct:ConsensusParams]
    events: ct:Events
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L237
  response_commit:
    data: pt:bytes
    retain_height: pt:int
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L243
  response_list_snapshots:
    snapshots: ct:SnapShots
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L247
  response_offer_snapshot:
    result: ct:Result
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L260
  response_load_snapshot_chunk:
    chunk: pt:bytes
  # https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L264
  response_apply_snapshot_chunk:
    result: ct:Result
    refetch_chunks: pt:list[pt:int]  # Chunks to refetch and reapply
    reject_senders: pt:list[pt:str]  # Chunk senders to reject and ban
  # dummy performative to make custom types used at least once
  dummy: 
    dummy_consensus_params: ct:ConsensusParams
...
---
# https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L284
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
# https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L343
ct:ValidatorUpdates: |
  message PublicKey {
    oneof sum {
      bytes ed25519   = 1;
      bytes secp256k1 = 2;
    }
  }
  message ValidatorUpdate {
    PublicKey pub_key = 1;
    int64 power = 2;
  }
  repeated ValidatorUpdate validators = 1;
# google.protobuf.Timestamp
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
# https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/crypto/proof.proto#L39
ct:ProofOps: |
  message ProofOp {
    string type = 1;
    bytes  key  = 2;
    bytes  data = 3;
  }
  repeated ProofOp ops = 1;
# https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/types/types.proto#L58
ct:Header: |
  message ConsensusVersion {
    uint64 block = 1;
    uint64 app   = 2;
  }
  message BlockID {
    bytes         hash            = 1;
    PartSetHeader part_set_header = 2;
  }
  message PartSetHeader {
    uint32 total = 1;
    bytes  hash  = 2;
  }
  ConsensusVersion             version  = 1;
  string                       chain_id = 2;
  int64                        height   = 3;
  Timestamp                    time     = 4;

  // prev block info
  BlockID last_block_id = 5;

  // hashes of block data
  bytes last_commit_hash = 6;  // commit from validators from the last block
  bytes data_hash        = 7;  // transactions

  // hashes from the app output from the prev block
  bytes validators_hash      = 8;   // validators for the current block
  bytes next_validators_hash = 9;   // validators for the next block
  bytes consensus_hash       = 10;  // consensus params for current block
  bytes app_hash             = 11;  // state after txs from the previous block
  bytes last_results_hash    = 12;  // root hash of all results from the txs from the previous block

  // consensus info
  bytes evidence_hash    = 13;  // evidence included in the block
  bytes proposer_address = 14;  // original proposer of the block
# https://github.com/tendermint/tendermint/blob/v0.34.19/proto/tendermint/abci/types.proto#L299
ct:LastCommitInfo: |
  message Validator {
    bytes address = 1;  // The first 20 bytes of SHA256(public key)
    // PubKey pub_key = 2 [(gogoproto.nullable)=false];
    int64 power = 3;  // The voting power
  }
  message VoteInfo {
    Validator validator         = 1;
    bool      signed_last_block = 2;
  }
  int32             round = 1;
  repeated VoteInfo votes = 2;
# https://github.com/tendermint/tendermint/blob/2f231ceb952a2426cf3c0abaf0b455aadd11e5b2/proto/tendermint/abci/types.proto#L360
ct:Evidences: |
  message Evidence {
    enum EvidenceType {
      UNKNOWN             = 0;
      DUPLICATE_VOTE      = 1;
      LIGHT_CLIENT_ATTACK = 2;
    }
    EvidenceType type = 1;
    // The offending validator
    LastCommitInfo.Validator validator = 2;
    // The height when the offense occurred
    int64 height = 3;
    // The corresponding time where the offense occurred
    Timestamp time = 4;
    // Total voting power of the validator set in case the ABCI application does
    // not store historical validators.
    // https://github.com/tendermint/tendermint/issues/4581
    int64 total_voting_power = 5;
  }
  repeated Evidence byzantine_validators = 1;
ct:CheckTxType: |
  enum _CheckTxType {
    NEW            = 0;
    RECHECK        = 1;
  }
  _CheckTxType type = 1;
# https://github.com/tendermint/tendermint/blob/2f231ceb952a2426cf3c0abaf0b455aadd11e5b2/proto/tendermint/abci/types.proto#L307
ct:Events: |
  message EventAttribute {
    bytes key   = 1;
    bytes value = 2;
    bool  index = 3;  // nondeterministic
  }
  message Event {
    string                  type       = 1;
    repeated EventAttribute attributes = 2;
  }
  repeated Event events = 1;
ct:Result: |
  enum ResultType {
    UNKNOWN       = 0;  // Unknown result, abort all snapshot restoration
    ACCEPT        = 1;  // Snapshot accepted, apply chunks
    ABORT         = 2;  // Abort all snapshot restoration
    REJECT        = 3;  // Reject this specific snapshot, try others
    REJECT_FORMAT = 4;  // Reject all snapshots of this format, try others
    REJECT_SENDER = 5;  // Reject all snapshots from the sender(s), try others
  }
  ResultType result_type = 1;
ct:Snapshot: |
  // State Sync Types
  uint64 height   = 1;  // The height at which the snapshot was taken
  uint32 format   = 2;  // The application-specific snapshot format
  uint32 chunks   = 3;  // Number of chunks in the snapshot
  bytes  hash     = 4;  // Arbitrary snapshot hash, equal only if identical
  bytes  metadata = 5;  // Arbitrary application metadata
ct:SnapShots: |
  repeated Snapshot snapshots = 1;
...
---
initiation:
- request_echo
- request_flush
- request_info
- request_set_option
- request_init_chain
- request_query
- request_begin_block
- request_check_tx
- request_deliver_tx
- request_end_block
- request_commit
- request_list_snapshots
- request_offer_snapshot
- request_apply_snapshot_chunk
- request_load_snapshot_chunk
- dummy
reply:
  request_echo: [response_echo, response_exception]
  response_echo: []
  response_exception: []
  request_flush: [response_flush, response_exception]
  response_flush: []
  request_info: [response_info, response_exception]
  response_info: []
  request_set_option: [response_set_option, response_exception]
  response_set_option: []
  request_init_chain: [response_init_chain, response_exception]
  response_init_chain: []
  request_query: [response_query, response_exception]
  response_query: []
  request_begin_block: [response_begin_block, response_exception]
  response_begin_block: []
  request_check_tx: [response_check_tx, response_exception]
  response_check_tx: []
  request_deliver_tx: [response_deliver_tx, response_exception]
  response_deliver_tx: []
  request_end_block: [response_end_block, response_exception]
  response_end_block: []
  request_commit: [response_commit, response_exception]
  response_commit: []
  request_list_snapshots: [response_list_snapshots, response_exception]
  response_list_snapshots: []
  request_offer_snapshot: [response_offer_snapshot, response_exception]
  response_offer_snapshot: []
  request_apply_snapshot_chunk: [response_apply_snapshot_chunk, response_exception]
  response_apply_snapshot_chunk: []
  request_load_snapshot_chunk: [response_load_snapshot_chunk, response_exception]
  response_load_snapshot_chunk: []
  dummy: []
termination:
  - response_exception
  - response_echo
  - response_flush
  - response_info
  - response_set_option
  - response_init_chain
  - response_query
  - response_begin_block
  - response_check_tx
  - response_deliver_tx
  - response_end_block
  - response_commit
  - response_list_snapshots
  - response_offer_snapshot
  - response_apply_snapshot_chunk
  - response_load_snapshot_chunk
  - dummy
roles: {client, server}
end_states: [successful]
keep_terminal_state_dialogues: false
...
```

## Links

* <a href="https://www.w3.org/Protocols/rfc2616/rfc2616.html" target="_blank">HTTP Specification</a>
