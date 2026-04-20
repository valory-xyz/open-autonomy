# ACN Data share protocol

## Description

This protocol provides support for sharing raw data using ACN

## Specification

```yaml
---
name: acn_data_share
author: valory
version: 0.1.0
description: A protocol for sharing raw data using ACN.
license: Apache-2.0
aea_version: '>=2.0.0, <3.0.0'
protocol_specification_id: valory/acn_data_share:0.1.0
speech_acts:
  data:
    request_id: pt:str
    content: pt:str
...
---
initiation: [data]
reply:
  data: []
termination: [data]
roles: {agent,skill}
end_states: [successful, failed]
keep_terminal_state_dialogues: false
...
```
