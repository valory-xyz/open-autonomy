<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Still incomplete!</p>
</div>

The Simple ABCI is a demonstration of a simple {{valory_app}}.

It's specification is relatively simple:

```yaml
alphabet_in:
- DONE
- NO_MAJORITY
- RESET_TIMEOUT
- ROUND_TIMEOUT
default_start_state: RegistrationRound
final_states: []
label: packages.valory.skills.simple_abci.rounds.SimpleAbciApp
start_states:
- RegistrationRound
states:
- RandomnessStartupRound
- RegistrationRound
- ResetAndPauseRound
- SelectKeeperAtStartupRound
transition_func:
    (RandomnessStartupRound, DONE): SelectKeeperAtStartupRound
    (RandomnessStartupRound, NO_MAJORITY): RandomnessStartupRound
    (RandomnessStartupRound, ROUND_TIMEOUT): RandomnessStartupRound
    (RegistrationRound, DONE): RandomnessStartupRound
    (ResetAndPauseRound, DONE): RandomnessStartupRound
    (ResetAndPauseRound, NO_MAJORITY): RegistrationRound
    (ResetAndPauseRound, RESET_TIMEOUT): RegistrationRound
    (SelectKeeperAtStartupRound, DONE): ResetAndPauseRound
    (SelectKeeperAtStartupRound, NO_MAJORITY): RegistrationRound
    (SelectKeeperAtStartupRound, ROUND_TIMEOUT): RegistrationRound
```

And visualised here:

<figure markdown>
<div class="mermaid">
stateDiagram-v2
    RegistrationRound --> RandomnessStartupRound: <center>DONE</center>
    RandomnessStartupRound --> SelectKeeperAtStartupRound: <center>DONE</center>
    RandomnessStartupRound --> RandomnessStartupRound: <center>NO_MAJORITY<br />ROUND_TIMEOUT</center>
    ResetAndPauseRound --> RandomnessStartupRound: <center>DONE</center>
    ResetAndPauseRound --> RegistrationRound: <center>NO_MAJORITY<br />RESET_TIMEOUT</center>
    SelectKeeperAtStartupRound --> ResetAndPauseRound: <center>DONE</center>
    SelectKeeperAtStartupRound --> RegistrationRound: <center>NO_MAJORITY<br />ROUND_TIMEOUT</center>
</div>
<figcaption>SimpleAbciApp FSM</figcaption>
</figure>

It can be ran as an end-to-end test:
```bash
pytest tests/test_agents/test_simple_abci.py
```
The tests nicely demonstrate how the same code can be run as a single agent app or as a multi-agent service.

We recommend using the simple abci as a starting point for development of your own {{valory_app}}.
