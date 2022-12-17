## Run

```
Usage: autonomy run [OPTIONS]

  Run the agent. Available for docker compose deployments only, not for kubernetes deployments.

Options:
  -p                          Ask for password interactively
  --password PASSWORD         Set password for key encryption/decryption
  --connections TEXT          The connection names to use for running the
                              agent. Must be declared in the agent's
                              configuration file.
  --env PATH                  Specify an environment file (default: .env)
  --install-deps              Install all the dependencies before running the
                              agent.
  --profiling INTEGER         Enable profiling, print profiling every amount
                              of seconds
  --memray                    Enable memray tracing, create a bin file with
                              the memory dump
  --exclude-connections TEXT  The connection names to disable for running the
                              agent. Must be declared in the agent's
                              configuration file.
  --aev                       Populate Agent configs from Environment
                              variables.
  --help                      Show this message and exit.
```

#### Example


```
autonomy run --aev
```
