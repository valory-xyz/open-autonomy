<a id="autonomy.cli.replay"></a>

# autonomy.cli.replay

Develop CLI module.

<a id="autonomy.cli.replay.replay_group"></a>

#### replay`_`group

```python
@click.group(name="replay")
def replay_group() -> None
```

Replay tools for agent services.

<a id="autonomy.cli.replay.run_agent"></a>

#### run`_`agent

```python
@replay_group.command(name="agent")
@click.argument("agent", type=int, required=True)
@click.option(
    "--build",
    "build_path",
    type=click.Path(exists=True, dir_okay=True),
    default=BUILD_DIR,
    help="Path to build dir.",
)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=True),
    default=REGISTRY_PATH,
    help="Path to registry folder.",
)
def run_agent(agent: int, build_path: Path, registry_path: Path) -> None
```

Agent runner.

<a id="autonomy.cli.replay.run_tendermint"></a>

#### run`_`tendermint

```python
@replay_group.command(name="tendermint")
@click.option(
    "--build",
    "build_dir",
    type=click.Path(dir_okay=True, exists=True),
    default=BUILD_DIR,
    help="Path to build directory.",
)
def run_tendermint(build_dir: Path) -> None
```

Tendermint runner.

