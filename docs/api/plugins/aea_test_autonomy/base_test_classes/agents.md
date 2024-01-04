<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents"></a>

# plugins.aea-test-autonomy.aea`_`test`_`autonomy.base`_`test`_`classes.agents

End2end tests base class.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.RoundChecks"></a>

## RoundChecks Objects

```python
@dataclass
class RoundChecks()
```

Class for the necessary checks of a round during the tests.

name: is the name of the round for which the checks should be performed.
event: is the name of the event that is considered as successful.
n_periods: is the number of periods this event should appear for the check to be considered successful.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End"></a>

## BaseTestEnd2End Objects

```python
@pytest.mark.e2e

@pytest.mark.integration
class BaseTestEnd2End(AEATestCaseMany, UseFlaskTendermintNode, UseLocalIpfs)
```

Base class for end-to-end tests of agents with a skill extending the abstract_abci_round skill.

The setup test function of this class will configure a set of 'n'
agents with the configured (agent_package) agent, and a Tendermint network
of 'n' nodes, one for each agent.

Test subclasses must set `agent_package`, `wait_to_finish` and `check_strings`.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls) -> None
```

Setup class

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End.set_config"></a>

#### set`_`config

```python
@classmethod
def set_config(cls,
               dotted_path: str,
               value: Any,
               type_: Optional[str] = None,
               aev: bool = True) -> Result
```

Set config value.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End.prepare"></a>

#### prepare

```python
def prepare(nb_nodes: int) -> None
```

Set up the agents.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End.prepare_and_launch"></a>

#### prepare`_`and`_`launch

```python
def prepare_and_launch(nb_nodes: int) -> None
```

Prepare and launch the agents.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End.missing_from_output"></a>

#### missing`_`from`_`output

```python
@classmethod
def missing_from_output(cls,
                        happy_path: Tuple[RoundChecks, ...] = (),
                        strict_check_strings: Tuple[str, ...] = (),
                        period: int = 1,
                        is_terminating: bool = True,
                        **kwargs: Any) -> Tuple[List[str], List[str]]
```

Check if strings are present in process output.

Read process stdout in thread and terminate when all strings are present or timeout expired.

**Arguments**:

- `happy_path`: the happy path of the testing FSM.
- `strict_check_strings`: tuple of strings expected to appear in output as is.
- `period`: period of checking.
- `is_terminating`: whether the agents are terminated if any of the check strings do not appear in the logs.
- `kwargs`: the kwargs of the overridden method.

**Returns**:

tuple with two lists of missed strings, the strict and the round respectively.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2End.check_aea_messages"></a>

#### check`_`aea`_`messages

```python
def check_aea_messages() -> None
```

Check that *each* AEA prints these messages.

First failing check will cause assertion error and test tear down.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution"></a>

## BaseTestEnd2EndExecution Objects

```python
class BaseTestEnd2EndExecution(BaseTestEnd2End)
```

Test that an agent that is launched later can synchronize with the rest of the network

- each agent starts, and sets up the ABCI connection, which in turn spawns both an ABCI
  server and a local Tendermint node (using the configuration folders we set up previously).
  The Tendermint node is unique for each agent
- when we will stop one agent, also the ABCI server created by the ABCI connection will
  stop, and in turn the Tendermint node will stop. In particular, it does not keep polling
  the endpoint until it is up again, it just stops.
- when we will restart the previously stopped agent, the ABCI connection will set up again
  both the server and the Tendermint node. The node will automatically connect to the rest
  of the Tendermint network, loads the entire blockchain bulit so far by the others, and
  starts sending ABCI requests to the agent (begin_block; deliver_tx*; end_block), plus
  other auxiliary requests like info , flush etc. The agent which is already processing
  incoming messages, forwards the ABCI requests to the ABCIHandler, which produces ABCI
  responses that are forwarded again via the ABCI connection such that the Tendermint
  node can receive the responses

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution.nb_nodes"></a>

#### nb`_`nodes

number of agents with tendermint nodes

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution.stop_string"></a>

#### stop`_`string

mandatory argument if n_terminal > 0

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution.n_terminal"></a>

#### n`_`terminal

number of agents to be restarted

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution.wait_to_kill"></a>

#### wait`_`to`_`kill

delay the termination event

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution.restart_after"></a>

#### restart`_`after

how long to wait before restart

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution.wait_before_stop"></a>

#### wait`_`before`_`stop

how long to check logs for `stop_string`

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution.check"></a>

#### check

```python
def check() -> None
```

Check pre-conditions of the test

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution.test_run"></a>

#### test`_`run

```python
def test_run(nb_nodes: int) -> None
```

Run the test.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.agents.BaseTestEnd2EndExecution.teardown_class"></a>

#### teardown`_`class

```python
@classmethod
def teardown_class(cls) -> None
```

Teardown the test.

