<a id="plugins.aea-helpers.aea_helpers.make_release"></a>

# plugins.aea-helpers.aea`_`helpers.make`_`release

Create a git tag and GitHub release.

<a id="plugins.aea-helpers.aea_helpers.make_release.make_release"></a>

#### make`_`release

```python
@click.command(name="make-release")
@click.option("--version", required=True, help="Release version (e.g. 1.0.0).")
@click.option(
    "--env",
    "environment",
    required=True,
    help="Release environment (e.g. prod, staging).",
)
@click.option("--description", required=True, help="Release description.")
def make_release(version: str, environment: str, description: str) -> None
```

Create a git tag and GitHub release.

