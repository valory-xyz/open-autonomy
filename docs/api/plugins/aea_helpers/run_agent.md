<a id="plugins.aea-helpers.aea_helpers.run_agent"></a>

# plugins.aea-helpers.aea`_`helpers.run`_`agent

Python wrapper for run_agent.sh shell script.

<a id="plugins.aea-helpers.aea_helpers.run_agent.run_agent"></a>

#### run`_`agent

```python
@click.command(name="run-agent")
@click.option("--name", required=True, help="Agent name (e.g. valory/trader).")
@click.option("--env-file",
              default=".env",
              help="Env file to source (default: .env).")
@click.option("--agent-env-file",
              default=None,
              help="Env file passed to the agent run command.")
@click.option("--config-replace",
              is_flag=True,
              help="Run config-replace after fetch.")
@click.option("--config-mapping",
              default=None,
              help="Path to config mapping file.")
@click.option("--connection-key",
              is_flag=True,
              help="Add connection key (second add-key call).")
@click.option("--free-ports",
              is_flag=True,
              help="Auto-find free ports for tendermint/HTTP.")
@click.option("--skip-make-clean", is_flag=True, help="Skip make clean step.")
@click.option("--skip-tendermint",
              is_flag=True,
              help="Skip tendermint init and startup.")
@click.option("--abci-port",
              type=int,
              default=None,
              help="Explicit ABCI port.")
@click.option("--rpc-port", type=int, default=None, help="Explicit RPC port.")
@click.option("--p2p-port", type=int, default=None, help="Explicit P2P port.")
@click.option("--com-port", type=int, default=None, help="Explicit COM port.")
@click.option("--http-port",
              type=int,
              default=None,
              help="Explicit HTTP port.")
def run_agent(**kwargs: object) -> None
```

Fetch, configure, and run an agent locally.

