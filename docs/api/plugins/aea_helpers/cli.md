<a id="plugins.aea-helpers.aea_helpers.cli"></a>

# plugins.aea-helpers.aea`_`helpers.cli

CLI entry point for aea-helpers.

<a id="plugins.aea-helpers.aea_helpers.cli.cli"></a>

#### cli

```python
@click.group()
@click.version_option()
def cli() -> None
```

AEA helper utilities for CI, dependency management, and deployment.

<a id="plugins.aea-helpers.aea_helpers.cli.generate_api_docs_cmd"></a>

#### generate`_`api`_`docs`_`cmd

```python
@click.command(name="generate-api-docs")
@click.option("--check",
              "check_clean",
              is_flag=True,
              help="Check docs are up to date.")
def generate_api_docs_cmd(check_clean: bool) -> None
```

Generate API documentation from source.

