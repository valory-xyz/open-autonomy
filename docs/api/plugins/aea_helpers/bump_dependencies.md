<a id="plugins.aea-helpers.aea_helpers.bump_dependencies"></a>

# plugins.aea-helpers.aea`_`helpers.bump`_`dependencies

Bump core dependencies.

Fetches the latest core dependency versions from GitHub, updates
tox.ini, packages and Pipfile/pyproject.toml files, and optionally
performs a packages sync.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.load_git_cache"></a>

#### load`_`git`_`cache

```python
def load_git_cache() -> None
```

Load versions cache.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.dump_git_cache"></a>

#### dump`_`git`_`cache

```python
def dump_git_cache() -> None
```

Dump versions cache.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.make_git_request"></a>

#### make`_`git`_`request

```python
def make_git_request(url: str) -> http_requests.HTTPResponse
```

Make git request.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.get_latest_tag"></a>

#### get`_`latest`_`tag

```python
def get_latest_tag(repo: str) -> str
```

Fetch latest git tag.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.get_dependency_version"></a>

#### get`_`dependency`_`version

```python
def get_dependency_version(repo: str, file: str) -> str
```

Get version spec.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.get_dependencies"></a>

#### get`_`dependencies

```python
def get_dependencies() -> t.Dict
```

Get dependency->version mapping.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.bump_pipfile_or_pyproject"></a>

#### bump`_`pipfile`_`or`_`pyproject

```python
def bump_pipfile_or_pyproject(file: Path, dependencies: t.Dict[str,
                                                               str]) -> None
```

Bump Pipfile or pyproject.toml.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.bump_tox"></a>

#### bump`_`tox

```python
def bump_tox(dependencies: t.Dict[str, str]) -> None
```

Bump tox file.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.bump_packages"></a>

#### bump`_`packages

```python
def bump_packages(dependencies: t.Dict[str, str]) -> None
```

Bump packages.

<a id="plugins.aea-helpers.aea_helpers.bump_dependencies.bump_dependencies"></a>

#### bump`_`dependencies

```python
@click.command(name="bump-dependencies")
@click.option(
    "-d",
    "--dependency",
    "extra",
    type=PyPiDependency(),
    multiple=True,
    help="Specify extra dependency.",
)
@click.option(
    "-s",
    "--source",
    "sources",
    type=PackagesSource(),
    multiple=True,
    help="Specify extra sources.",
)
@click.option("--sync", is_flag=True, help="Perform sync.")
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Avoid using cache to bump.",
)
def bump_dependencies(extra: t.Tuple[Dependency, ...], sources: t.Tuple[str,
                                                                        ...],
                      sync: bool, no_cache: bool) -> None
```

Bump core dependency versions from GitHub.

