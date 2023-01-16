# Tendermint Protocol

## Description

This is a protocol for communication between AEAs for sharing their tendermint configuration details.

## Specification

```yaml
---
name: tendermint
author: valory
version: 0.1.0
protocol_specification_id: valory/tendermint:0.1.0
description: A protocol for communication between two AEAs to share tendermint configuration details.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
speech_acts:
  get_genesis_info:
    query: pt:optional[pt:str]
  get_recovery_params:
    query: pt:optional[pt:str]
  genesis_info:
    info: pt:str
  recovery_params:
    params: pt:str
  error:
    error_code: ct:ErrorCode
    error_msg: pt:str
    error_data: pt:dict[pt:str, pt:str]
...
---
ct:ErrorCode: |
  enum ErrorCodeEnum {
      INVALID_REQUEST = 0;
    }
  ErrorCodeEnum error_code = 1;
...
---
initiation: [get_genesis_info, get_recovery_params]
reply:
  get_genesis_info: [genesis_info, error]
  get_recovery_params: [recovery_params, error]
  genesis_info: []
  recovery_params: []
  error: []
roles: {agent}
termination: [genesis_info, recovery_params, error]
end_states: [communicated, not_communicated]
keep_terminal_state_dialogues: true
...
```

## Links

