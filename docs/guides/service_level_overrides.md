This guide will walk you through the process of defining the service level overrides. If you don't know about what are component overrides refer to [component overrides](https://open-aea.docs.autonolas.tech/overrides/) to learn about component overrides before moving ahead.

### Defining service level overrides.

You can define the service level overrides in the `service.yaml` file which will be used to generate the deployment environment for agents

```yaml
name: hello_world
author: valory
version: 0.1.0
description: A simple demonstration of a simple ABCI application
aea_version: '>=1.0.0, <2.0.0'
license: Apache-2.0
fingerprint:
  README.md: bafybeiapubcoersqnsnh3acia5hd7otzt7kjxekr6gkbrlumv6tkajl6jm
fingerprint_ignore_patterns: []
agent: valory/hello_world:0.1.0:bafybeiaotnukv7oq2sknot73a4zssrrnjezh6nd2fwptrznxtnovy2rusm
number_of_agents: 4
---
public_id: valory/hello_world_abci:0.1.0
type: skill
models:
  params:
    args:
      hello_world_message: Hello, World!
```

When generating the deployment environment this override will be used to create a environment variable, which later will be picked by the agent in the runtime. 

> The environment variable for the above override should look this `SKILL_HELLO_WORLD_ABCI_MODELS_PARAMS_ARGS_HELLO_WORLD_MESSAGE` since they are generated from the `json` path to the value.

### Multiple overrides

The service component allows you to define different override values for different agents using the multiple overrides.

```yaml
...
---
public_id: valory/hello_world_abci:0.1.0
type: skill
{agent_number}:
  {overrides}
```

For example, using the example above the multiple overrides should be defined like this

```yaml
...
---
public_id: valory/hello_world_abci:0.1.0
type: skill
public_id: valory/hello_world_abci:0.1.0
type: skill
0:
  models:
    params:
      args:
        hello_world_message: Hello, from agent 0
1:
  models:
    params:
      args:
        hello_world_message: Hello, from agent 1
2:
  models:
    params:
      args:
        hello_world_message: Hello, from agent 2
3:
  models:
    params:
      args:
        hello_world_message: Hello, from agent 3
```

If you choose to go with the multiple overrides you'll have to define overrides for every single agent.

If you have overrides values which are repetitive you can define them under extra section and reference them when defining overrides for different agents.

```yaml
...
---
extra:
  benchmark_tool:
    args: &id001
      log_dir: /benchmarks
public_id: valory/hello_world_abci:0.1.0
type: skill
public_id: valory/hello_world_abci:0.1.0
type: skill
0:
  models:
    params:
      args:
        hello_world_message: Hello, from agent 0
    benchmark_tool:
      args: *id001
1:
  models:
    params:
      args:
        hello_world_message: Hello, from agent 1
    benchmark_tool:
      args: *id001
2:
  models:
    params:
      args:
        hello_world_message: Hello, from agent 2
    benchmark_tool:
      args: *id001
3:
  models:
    params:
      args:
        hello_world_message: Hello, from agent 3
    benchmark_tool:
      args: *id001
```