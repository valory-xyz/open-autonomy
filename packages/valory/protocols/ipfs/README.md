# IPFS Protocol

## Description

This is a protocol for interacting with IPFS.

## Specification

```yaml
---
name: ipfs
author: valory
version: 0.1.0
description: A protocol specification for IPFS requests and responses.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: valory/ipfs:0.1.0
speech_acts:
 store_files:
   files: pt:dict[pt:str, pt:str]
   timeout: pt:optional[pt:float]
 ipfs_hash:
   ipfs_hash: pt:str
 get_files:
   ipfs_hash: pt:str
   timeout: pt:optional[pt:float]
 files:
   files: pt:dict[pt:str, pt:str]
 error:
   reason: pt:str
---
initiation: [get_files, store_files]
reply:
 store_files: [ipfs_hash, error]
 ipfs_hash: []
 get_files: [files, error]
 files: []
 error: []
termination: [ipfs_hash, files, error]
roles: {skill, connection}
end_states: [ok, error]
keep_terminal_state_dialogues: false
...
```

## Links

