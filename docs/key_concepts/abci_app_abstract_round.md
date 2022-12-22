!!!note
    For clarity, the snippets of code presented here are a simplified version of the actual
    implementation. We refer the reader to the {{open_autonomy_api}} for the complete details.

The `AbstractRound` class is the parent class of all the `Round` subclasses of an {{fsm_app}}. It is in charge of processing the requests coming from the ABCI Handler, and it defines a number of abstract methods that must be implemented by its subclasses, namely:
  - `end_block()`
  - `check_payload()`
  - `process_payload()`

For convenience, the {{open_autonomy}} framework provides a collection of helper classes that derive from the `AbstractRound` class that represent common situations when defining custom rounds. This way the developer is freed from having to implement the `check_payload()` and `process_payload()` methods above. These classes are:

  - `CollectDifferentUntilAllRound`: This class represents logic for rounds where a round needs to collect different payloads from each agent.
  - `CollectSameUntilAllRound`:     This class represents logic for when a round needs to collect the same payload from all the agents.
  - `CollectSameUntilThresholdRound`:     This class represents logic for rounds where a round needs to collect same payload from $k$ of $n$ agents.
  - `OnlyKeeperSendsRound`: This class represents logic for rounds where only one agent sends a payload.
  - `VotingRound`: This class represents logic for rounds where a round needs votes from agents, pass if $k$ same votes of $n$ agents.
  - `CollectDifferentUntilThresholdRound`: This class represents logic for rounds where a round needs to collect different payloads from $k$ of $n$ agents
  - `CollectNonEmptyUntilThresholdRound`:     This class represents logic for rounds where we need to collect payloads from each agent which will contain optional, different data and only keep the non-empty. This round may be used for cases that we want to collect all the agent's data, such as late-arriving messages.


Thus, an example on how these classes are used is as follows:


```python
class MyFsmAppAbstractRound(AbstractRound[Event, TransactionType], ABC):

    @property
    def synchronized_data(self) -> SynchronizedData:
        return cast(SynchronizedData, self._synchronized_data)

    def _return_no_majority_event(self) -> Tuple[SynchronizedData, Event]:
        return self.synchronized_data, Event.NO_MAJORITY


class RegistrationRound(CollectDifferentUntilAllRound, MyFsmAppAbstractRound):

    round_id = "registration"
    allowed_tx_type = RegistrationPayload.transaction_type
    payload_attribute = "sender"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:

        if self.collection_threshold_reached:
            synchronized_data = self.synchronized_data.update(
                participants=self.collection,
                synchronized_data_class=SynchronizedData,
            )
            return synchronized_data, Event.DONE
        return None
```

The developer needs, therefore, to implement the `end_block()` method, which requires to return the updated `SynchronizedData` object, together with the event generated after evaluating the received data in that round.
