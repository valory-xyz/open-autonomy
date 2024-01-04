<a id="autonomy.cli.helpers.registry"></a>

# autonomy.cli.helpers.registry

Component registry helpers.

<a id="autonomy.cli.helpers.registry.fetch_service"></a>

#### fetch`_`service

```python
def fetch_service(ctx: Context,
                  public_id: PublicId,
                  alias: Optional[str] = None) -> Path
```

Fetch service.

<a id="autonomy.cli.helpers.registry.fetch_service_mixed"></a>

#### fetch`_`service`_`mixed

```python
def fetch_service_mixed(ctx: Context,
                        public_id: PublicId,
                        alias: Optional[str] = None) -> Path
```

Fetch service in mixed mode.

<a id="autonomy.cli.helpers.registry.fetch_service_remote"></a>

#### fetch`_`service`_`remote

```python
def fetch_service_remote(public_id: PublicId,
                         alias: Optional[str] = None) -> Path
```

Fetch service in remote mode.

<a id="autonomy.cli.helpers.registry.fetch_service_ipfs"></a>

#### fetch`_`service`_`ipfs

```python
def fetch_service_ipfs(public_id: PublicId,
                       alias: Optional[str] = None) -> Path
```

Fetch service from IPFS node.

<a id="autonomy.cli.helpers.registry.fetch_service_local"></a>

#### fetch`_`service`_`local

```python
def fetch_service_local(ctx: Context,
                        public_id: PublicId,
                        alias: Optional[str] = None) -> Path
```

Fetch service from local directory.

<a id="autonomy.cli.helpers.registry.publish_service_package"></a>

#### publish`_`service`_`package

```python
def publish_service_package(click_context: click.Context,
                            registry: str) -> None
```

Publish a service package.

<a id="autonomy.cli.helpers.registry.publish_service_ipfs"></a>

#### publish`_`service`_`ipfs

```python
def publish_service_ipfs(public_id: PublicId, package_path: Path) -> None
```

Publish a service package on the IPFS registry.

<a id="autonomy.cli.helpers.registry.publish_service_local"></a>

#### publish`_`service`_`local

```python
def publish_service_local(ctx: Context, public_id: PublicId) -> None
```

Publish a service package on the local packages directory.

