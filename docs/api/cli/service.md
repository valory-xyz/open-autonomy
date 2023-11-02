<a id="autonomy.cli.service"></a>

# autonomy.cli.service

Implementation of the `autonomy service` command

<a id="autonomy.cli.service.service"></a>

#### service

```python
@click.group("service")
@pass_ctx
@timeout_flag
@chain_selection_flag()
def service(ctx: Context, chain_type: str, timeout: float) -> None
```

Manage on-chain services.

