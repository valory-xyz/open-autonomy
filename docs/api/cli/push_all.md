<a id="autonomy.cli.push_all"></a>

# autonomy.cli.push`_`all

Push all available packages to a registry.

<a id="autonomy.cli.push_all.push_all"></a>

#### push`_`all

```python
@click.command("push-all")
@click.option("--packages-dir",
              type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.option(
    "--retries",
    type=int,
    default=1,
    help="Tries on package push to the network.",
)
@registry_flag()
def push_all(packages_dir: Optional[Path], retries: int,
             registry: str) -> None
```

Push all available packages to a registry.

