<a id="autonomy.test_tools.docker.base"></a>

# autonomy.test`_`tools.docker.base

This module contains testing utilities.

<a id="autonomy.test_tools.docker.base.DockerImage"></a>

## DockerImage Objects

```python
class DockerImage(ABC)
```

A class to wrap interaction with a Docker image.

<a id="autonomy.test_tools.docker.base.DockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: docker.DockerClient)
```

Initialize.

<a id="autonomy.test_tools.docker.base.DockerImage.check_skip"></a>

#### check`_`skip

```python
def check_skip() -> None
```

Check whether the test should be skipped.

By default, nothing happens.

<a id="autonomy.test_tools.docker.base.DockerImage.tag"></a>

#### tag

```python
@property
@abstractmethod
def tag() -> str
```

Return the tag of the image.

<a id="autonomy.test_tools.docker.base.DockerImage.stop_if_already_running"></a>

#### stop`_`if`_`already`_`running

```python
def stop_if_already_running() -> None
```

Stop the running images with the same tag, if any.

<a id="autonomy.test_tools.docker.base.DockerImage.create"></a>

#### create

```python
@abstractmethod
def create() -> Container
```

Instantiate the image in a container.

<a id="autonomy.test_tools.docker.base.DockerImage.create_many"></a>

#### create`_`many

```python
@abstractmethod
def create_many(nb_containers: int) -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="autonomy.test_tools.docker.base.DockerImage.wait"></a>

#### wait

```python
@abstractmethod
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is running.

**Arguments**:

- `max_attempts`: max number of attempts.
- `sleep_rate`: the amount of time to sleep between different requests.

**Returns**:

True if the wait was successful, False otherwise.

<a id="autonomy.test_tools.docker.base.launch_image"></a>

#### launch`_`image

```python
def launch_image(image: DockerImage, timeout: float = 2.0, max_attempts: int = 10) -> Generator[DockerImage, None, None]
```

Launch a single container.

**Arguments**:

:yield: image
- `image`: an instance of Docker image.
- `timeout`: timeout to launch
- `max_attempts`: max launch attempts

<a id="autonomy.test_tools.docker.base.launch_many_containers"></a>

#### launch`_`many`_`containers

```python
def launch_many_containers(image: DockerImage, nb_containers: int, timeout: float = 2.0, max_attempts: int = 10) -> Generator[DockerImage, None, None]
```

Launch many containers from an image.

**Arguments**:

:yield: image
- `image`: an instance of Docker image.
- `nb_containers`: the number of containers to launch from the image.
- `timeout`: timeout to launch
- `max_attempts`: max launch attempts

<a id="autonomy.test_tools.docker.base.DockerBaseTest"></a>

## DockerBaseTest Objects

```python
@skip_docker_tests
class DockerBaseTest(ABC)
```

Base pytest class for setting up Docker images.

<a id="autonomy.test_tools.docker.base.DockerBaseTest.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls) -> None
```

Setup up the test class.

<a id="autonomy.test_tools.docker.base.DockerBaseTest.teardown_class"></a>

#### teardown`_`class

```python
@classmethod
def teardown_class(cls) -> None
```

Tear down the test.

<a id="autonomy.test_tools.docker.base.DockerBaseTest.setup_class_kwargs"></a>

#### setup`_`class`_`kwargs

```python
@classmethod
@abstractmethod
def setup_class_kwargs(cls) -> Dict[str, Any]
```

Get kwargs for _setup_class call.

