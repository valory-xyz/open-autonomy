## Fetch

```
Usage: autonomy fetch [OPTIONS] PUBLIC_ID_OR_HASH

  Fetch an agent from the registry.

Options:
  --remote      To use a remote registry.
  --local       To use a local registry.
  --alias TEXT  Provide a local alias for the agent.
  --agent       Provide a local alias for the agent.
  --service     Provide a local alias for the agent.
  --help        Show this message and exit.
```

#### Example


```
autonomy fetch --local --alias oracle valory/oracle:0.1.0
```
