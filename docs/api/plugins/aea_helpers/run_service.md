<a id="plugins.aea-helpers.aea_helpers.run_service"></a>

# plugins.aea-helpers.aea`_`helpers.run`_`service

Python wrapper for run_service.sh shell script.

<a id="plugins.aea-helpers.aea_helpers.run_service.run_service"></a>

#### run`_`service

```python
@click.command(name="run-service")
@click.option("--name",
              required=True,
              help="Service name (e.g. valory/trader).")
@click.option("--env-file",
              default=".env",
              help="Env file to source (default: .env).")
@click.option("--keys-file",
              default="keys.json",
              help="Keys file (default: keys.json).")
@click.option("--agents",
              type=int,
              default=4,
              help="Number of agents (default: 4).")
@click.option("--author",
              default="valory",
              help="Author for init step (default: valory).")
@click.option("--cpu-limit", type=float, default=None, help="Agent CPU limit.")
@click.option("--memory-limit",
              type=int,
              default=None,
              help="Agent memory limit (MB).")
@click.option("--memory-request",
              type=int,
              default=None,
              help="Agent memory request (MB).")
@click.option("--detach",
              is_flag=True,
              help="Run deployment in detached mode.")
@click.option("--docker-cleanup",
              is_flag=True,
              help="Clean up Docker containers before start.")
@click.option("--skip-init", is_flag=True, help="Skip the init step.")
@click.option("--pre-deploy-cmd",
              default=None,
              help="Command to run before deploy build.")
@click.option("--post-deploy-cmd",
              default=None,
              help="Command to run after deploy build.")
def run_service(**kwargs: object) -> None
```

Build and deploy an agent service.

