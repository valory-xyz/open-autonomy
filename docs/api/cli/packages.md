<a id="autonomy.cli.packages"></a>

# autonomy.cli.packages

Override for packages command.

<a id="autonomy.cli.packages.lock_packages"></a>

#### lock`_`packages

```python
@package_manager.command(name="lock")
@click.option(
    "--check",
    is_flag=True,
    help="Check that fingerprints in packages.json match the local packages",
)
@pass_ctx
def lock_packages(ctx: Context, check: bool) -> None
```

Lock local packages.

