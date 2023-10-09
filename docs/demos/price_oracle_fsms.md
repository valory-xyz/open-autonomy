# Price Oracle - Description of the FSMs

For reference, we provide a high-level description of the FSMs that constitute
the Price Oracle demo using a simplified syntax.
The syntax should be easy to understand for a reader familiar with conventional
automata textbook notation.

The aim of this syntax is to be used as a starting point in the design and
reasoning of an {{fsm_app}} without delving into the internals of the {{open_autonomy}} framework
itself. Hence, the usage of objects is minimized, and only strings are
used as identifiers. It can be used as a description language to translate a
specification into code, e.g., for agent development, or for conducting some
formal analysis using a model checker like SPIN.

Each FSM object is defined by a collection of seven input parameters:

* label (optional),
* states,
* default start state,
* allowed start states (e.g., when re-routing a transition from another FSM),
* final states,
* input alphabet (i.e., received events),
* transition function, expressed as a function that maps tuples of the form (S, E) to the resulting state S'. That is, upon receiving event E being at state S, the FSM will transit to state S'.

The summary of the constituent FSMs is as follows:


| FSM                     | States  | Start states  | Final states  | Events  | Non-trivial transitions (*)   |
|-----------------------  |-------: |-------------: |-------------: |-------: |------------------------:  |
| AgentRegistration       |      4  |            2  |            2  |      3  |                       3   |
| OracleDeployment        |      5  |            1  |            1  |      8  |                      14   |
| PriceAggregation        |      9  |            1  |            1  |      4  |                       9   |
| TransactionSubmission   |     10  |            1  |            2  |      9  |                      26   |
| ResetPauseAbciApp       |      3  |            1  |            2  |      3  |                       3   |
| **OracleAbciApp**       | **21**  |        **2**  |        **0**  | **12**  |                  **66**   |


(`*`) Transitions to a different state, i.e., not self-transitions.

#### `AgentRegistrationAbciApp` FSM

```yaml title="fsm_specification.yaml"
alphabet_in:
- DONE
- NO_MAJORITY
default_start_state: RegistrationStartupRound
final_states:
- FinishedRegistrationRound
label: AgentRegistrationAbciApp
start_states:
- RegistrationRound
- RegistrationStartupRound
states:
- FinishedRegistrationRound
- RegistrationRound
- RegistrationStartupRound
transition_func:
    (RegistrationRound, DONE): FinishedRegistrationRound
    (RegistrationRound, NO_MAJORITY): RegistrationRound
    (RegistrationStartupRound, DONE): FinishedRegistrationRound
```

<figure markdown>
<div class="mermaid">
stateDiagram-v2
    RegistrationRound --> FinishedRegistrationFFWRound: <center>DONE</center>
    RegistrationStartupRound --> FinishedRegistrationRound: <center>DONE</center>
    RegistrationStartupRound --> FinishedRegistrationFFWRound: <center>FAST_FORWARD</center>
</div>
<figcaption>AgentRegistrationAbciApp FSM</figcaption>
</figure>


#### `OracleDeploymentAbciApp` FSM
```yaml title="fsm_specification.yaml"
alphabet_in:
- DEPLOY_TIMEOUT
- DONE
- FAILED
- NEGATIVE
- NONE
- NO_MAJORITY
- ROUND_TIMEOUT
- VALIDATE_TIMEOUT
default_start_state: RandomnessOracleRound
final_states:
- FinishedOracleRound
label: packages.valory.skills.oracle_deployment_abci.rounds.OracleDeploymentAbciApp
start_states:
- RandomnessOracleRound
states:
- DeployOracleRound
- FinishedOracleRound
- RandomnessOracleRound
- SelectKeeperOracleRound
- ValidateOracleRound
transition_func:
    (DeployOracleRound, DEPLOY_TIMEOUT): SelectKeeperOracleRound
    (DeployOracleRound, DONE): ValidateOracleRound
    (DeployOracleRound, FAILED): SelectKeeperOracleRound
    (RandomnessOracleRound, DONE): SelectKeeperOracleRound
    (RandomnessOracleRound, NO_MAJORITY): RandomnessOracleRound
    (RandomnessOracleRound, ROUND_TIMEOUT): RandomnessOracleRound
    (SelectKeeperOracleRound, DONE): DeployOracleRound
    (SelectKeeperOracleRound, NO_MAJORITY): RandomnessOracleRound
    (SelectKeeperOracleRound, ROUND_TIMEOUT): RandomnessOracleRound
    (ValidateOracleRound, DONE): FinishedOracleRound
    (ValidateOracleRound, NEGATIVE): RandomnessOracleRound
    (ValidateOracleRound, NONE): RandomnessOracleRound
    (ValidateOracleRound, NO_MAJORITY): RandomnessOracleRound
    (ValidateOracleRound, VALIDATE_TIMEOUT): RandomnessOracleRound
```

<figure markdown>
<div class="mermaid">
stateDiagram-v2
    RandomnessOracleRound --> SelectKeeperOracleRound: <center>DONE</center>
    RandomnessOracleRound --> RandomnessOracleRound: <center>NO_MAJORITY<br />ROUND_TIMEOUT</center>
    DeployOracleRound --> SelectKeeperOracleRound: <center>FAILED<br />DEPLOY_TIMEOUT</center>
    DeployOracleRound --> ValidateOracleRound: <center>DONE</center>
    SelectKeeperOracleRound --> DeployOracleRound: <center>DONE</center>
    SelectKeeperOracleRound --> RandomnessOracleRound: <center>NO_MAJORITY<br />ROUND_TIMEOUT</center>
    ValidateOracleRound --> FinishedOracleRound: <center>DONE</center>
    ValidateOracleRound --> RandomnessOracleRound: <center>NO_MAJORITY<br />NONE<br />NEGATIVE<br />VALIDATE_TIMEOUT</center>
</div>
<figcaption>OracleDeploymentAbciApp FSM</figcaption>
</figure>

#### `PriceAggregationAbciApp` FSM
```yaml title="fsm_specification.yaml"
alphabet_in:
- DONE
- NONE
- NO_MAJORITY
- ROUND_TIMEOUT
default_start_state: CollectObservationRound
final_states:
- FinishedPriceAggregationRound
label: packages.valory.skills.price_estimation_abci.rounds.PriceAggregationAbciApp
start_states:
- CollectObservationRound
states:
- CollectObservationRound
- EstimateConsensusRound
- FinishedPriceAggregationRound
- TxHashRound
transition_func:
    (CollectObservationRound, DONE): EstimateConsensusRound
    (CollectObservationRound, NO_MAJORITY): CollectObservationRound
    (CollectObservationRound, ROUND_TIMEOUT): CollectObservationRound
    (EstimateConsensusRound, DONE): TxHashRound
    (EstimateConsensusRound, NONE): CollectObservationRound
    (EstimateConsensusRound, NO_MAJORITY): CollectObservationRound
    (EstimateConsensusRound, ROUND_TIMEOUT): CollectObservationRound
    (TxHashRound, DONE): FinishedPriceAggregationRound
    (TxHashRound, NONE): CollectObservationRound
    (TxHashRound, NO_MAJORITY): CollectObservationRound
    (TxHashRound, ROUND_TIMEOUT): CollectObservationRound
```

<figure markdown>
<div class="mermaid">
stateDiagram-v2
    CollectObservationRound --> EstimateConsensusRound: <center>DONE</center>
    CollectObservationRound --> CollectObservationRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    EstimateConsensusRound --> TxHashRound: <center>DONE</center>
    EstimateConsensusRound --> CollectObservationRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    TxHashRound --> FinishedPriceAggregationRound: <center>DONE</center>
    TxHashRound --> CollectObservationRound: <center>ROUND_TIMEOUT<br />NONE<br />NO_MAJORITY</center>
</div>
<figcaption>PriceAggregationAbciApp FSM</figcaption>
</figure>

#### `TransactionSubmissionAbciApp` FSM
```yaml title="fsm_specification.yaml"
alphabet_in:
- CHECK_HISTORY
- CHECK_LATE_ARRIVING_MESSAGE
- CHECK_TIMEOUT
- DONE
- FINALIZATION_FAILED
- FINALIZE_TIMEOUT
- INCORRECT_SERIALIZATION
- INSUFFICIENT_FUNDS
- MISSED_AND_LATE_MESSAGES_MISMATCH
- NEGATIVE
- NONE
- NO_MAJORITY
- RESET_TIMEOUT
- ROUND_TIMEOUT
- VALIDATE_TIMEOUT
default_start_state: RandomnessTransactionSubmissionRound
final_states:
- FailedRound
- FinishedTransactionSubmissionRound
label: TransactionSubmissionAbciApp
start_states:
- RandomnessTransactionSubmissionRound
states:
- CheckLateTxHashesRound
- CheckTransactionHistoryRound
- CollectSignatureRound
- FailedRound
- FinalizationRound
- FinishedTransactionSubmissionRound
- RandomnessTransactionSubmissionRound
- ResetRound
- SelectKeeperTransactionSubmissionARound
- SelectKeeperTransactionSubmissionBRound
- SelectKeeperTransactionSubmissionBRoundAfterTimeout
- SynchronizeLateMessagesRound
- ValidateTransactionRound
transition_func:
    (CheckLateTxHashesRound, CHECK_LATE_ARRIVING_MESSAGE): SynchronizeLateMessagesRound
    (CheckLateTxHashesRound, CHECK_TIMEOUT): CheckLateTxHashesRound
    (CheckLateTxHashesRound, DONE): FinishedTransactionSubmissionRound
    (CheckLateTxHashesRound, NEGATIVE): FailedRound
    (CheckLateTxHashesRound, NONE): FailedRound
    (CheckLateTxHashesRound, NO_MAJORITY): FailedRound
    (CheckTransactionHistoryRound, CHECK_LATE_ARRIVING_MESSAGE): SynchronizeLateMessagesRound
    (CheckTransactionHistoryRound, CHECK_TIMEOUT): CheckTransactionHistoryRound
    (CheckTransactionHistoryRound, DONE): FinishedTransactionSubmissionRound
    (CheckTransactionHistoryRound, NEGATIVE): SelectKeeperTransactionSubmissionBRound
    (CheckTransactionHistoryRound, NONE): FailedRound
    (CheckTransactionHistoryRound, NO_MAJORITY): CheckTransactionHistoryRound
    (CollectSignatureRound, DONE): FinalizationRound
    (CollectSignatureRound, NO_MAJORITY): ResetRound
    (CollectSignatureRound, ROUND_TIMEOUT): CollectSignatureRound
    (FinalizationRound, CHECK_HISTORY): CheckTransactionHistoryRound
    (FinalizationRound, CHECK_LATE_ARRIVING_MESSAGE): SynchronizeLateMessagesRound
    (FinalizationRound, DONE): ValidateTransactionRound
    (FinalizationRound, FINALIZATION_FAILED): SelectKeeperTransactionSubmissionBRound
    (FinalizationRound, FINALIZE_TIMEOUT): SelectKeeperTransactionSubmissionBRoundAfterTimeout
    (FinalizationRound, INSUFFICIENT_FUNDS): SelectKeeperTransactionSubmissionBRound
    (RandomnessTransactionSubmissionRound, DONE): SelectKeeperTransactionSubmissionARound
    (RandomnessTransactionSubmissionRound, NO_MAJORITY): RandomnessTransactionSubmissionRound
    (RandomnessTransactionSubmissionRound, ROUND_TIMEOUT): RandomnessTransactionSubmissionRound
    (ResetRound, DONE): RandomnessTransactionSubmissionRound
    (ResetRound, NO_MAJORITY): FailedRound
    (ResetRound, RESET_TIMEOUT): FailedRound
    (SelectKeeperTransactionSubmissionARound, DONE): CollectSignatureRound
    (SelectKeeperTransactionSubmissionARound, INCORRECT_SERIALIZATION): FailedRound
    (SelectKeeperTransactionSubmissionARound, NO_MAJORITY): ResetRound
    (SelectKeeperTransactionSubmissionARound, ROUND_TIMEOUT): SelectKeeperTransactionSubmissionARound
    (SelectKeeperTransactionSubmissionBRound, DONE): FinalizationRound
    (SelectKeeperTransactionSubmissionBRound, INCORRECT_SERIALIZATION): FailedRound
    (SelectKeeperTransactionSubmissionBRound, NO_MAJORITY): ResetRound
    (SelectKeeperTransactionSubmissionBRound, ROUND_TIMEOUT): SelectKeeperTransactionSubmissionBRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, CHECK_HISTORY): CheckTransactionHistoryRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, CHECK_LATE_ARRIVING_MESSAGE): SynchronizeLateMessagesRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, DONE): FinalizationRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, INCORRECT_SERIALIZATION): FailedRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, NO_MAJORITY): ResetRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, ROUND_TIMEOUT): SelectKeeperTransactionSubmissionBRoundAfterTimeout
    (SynchronizeLateMessagesRound, DONE): CheckLateTxHashesRound
    (SynchronizeLateMessagesRound, MISSED_AND_LATE_MESSAGES_MISMATCH): FailedRound
    (SynchronizeLateMessagesRound, NONE): SelectKeeperTransactionSubmissionBRound
    (SynchronizeLateMessagesRound, NO_MAJORITY): SynchronizeLateMessagesRound
    (SynchronizeLateMessagesRound, ROUND_TIMEOUT): SynchronizeLateMessagesRound
    (ValidateTransactionRound, DONE): FinishedTransactionSubmissionRound
    (ValidateTransactionRound, NEGATIVE): CheckTransactionHistoryRound
    (ValidateTransactionRound, NONE): SelectKeeperTransactionSubmissionBRound
    (ValidateTransactionRound, NO_MAJORITY): ValidateTransactionRound
    (ValidateTransactionRound, VALIDATE_TIMEOUT): SelectKeeperTransactionSubmissionBRound
```

<figure markdown>
<div class="mermaid">
stateDiagram-v2
    RandomnessTransactionSubmissionRound --> SelectKeeperTransactionSubmissionARound: <center>DONE</center>
    RandomnessTransactionSubmissionRound --> RandomnessTransactionSubmissionRound: <center>NO_MAJORITY</center>
    RandomnessTransactionSubmissionRound --> ResetRound: <center>ROUND_TIMEOUT</center>
    CheckLateTxHashesRound --> FinishedTransactionSubmissionRound: <center>DONE</center>
    CheckLateTxHashesRound --> FailedRound: <center>NONE<br />NEGATIVE<br />NO_MAJORITY</center>
    CheckLateTxHashesRound --> CheckLateTxHashesRound: <center>ROUND_TIMEOUT</center>
    CheckTransactionHistoryRound --> SynchronizeLateMessagesRound: <center>CHECK_LATE_ARRIVING_MESSAGE</center>
    CheckTransactionHistoryRound --> FinishedTransactionSubmissionRound: <center>DONE</center>
    CheckTransactionHistoryRound --> FailedRound: <center>NONE<br />NEGATIVE<br />NO_MAJORITY</center>
    CheckTransactionHistoryRound --> CheckTransactionHistoryRound: <center>ROUND_TIMEOUT</center>
    CollectSignatureRound --> FinalizationRound: <center>DONE</center>
    CollectSignatureRound --> ResetRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    FinalizationRound --> CheckTransactionHistoryRound: <center>CHECK_HISTORY</center>
    FinalizationRound --> SynchronizeLateMessagesRound: <center>CHECK_LATE_ARRIVING_MESSAGE</center>
    FinalizationRound --> ValidateTransactionRound: <center>DONE</center>
    FinalizationRound --> SelectKeeperTransactionSubmissionBRound: <center>FINALIZATION_FAILED</center>
    FinalizationRound --> SelectKeeperTransactionSubmissionBRoundAfterTimeout: <center>ROUND_TIMEOUT</center>
    ResetRound --> RandomnessTransactionSubmissionRound: <center>DONE</center>
    ResetRound --> FailedRound: <center>NO_MAJORITY<br />RESET_TIMEOUT</center>
    SelectKeeperTransactionSubmissionARound --> CollectSignatureRound: <center>DONE</center>
    SelectKeeperTransactionSubmissionARound --> ResetRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    SelectKeeperTransactionSubmissionBRound --> FinalizationRound: <center>DONE</center>
    SelectKeeperTransactionSubmissionBRound --> ResetRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    SelectKeeperTransactionSubmissionBRoundAfterTimeout --> CheckTransactionHistoryRound: <center>CHECK_HISTORY</center>
    SelectKeeperTransactionSubmissionBRoundAfterTimeout --> FinalizationRound: <center>DONE</center>
    SelectKeeperTransactionSubmissionBRoundAfterTimeout --> ResetRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    SynchronizeLateMessagesRound --> CheckLateTxHashesRound: <center>DONE</center>
    SynchronizeLateMessagesRound --> FailedRound: <center>NONE<br />MISSED_AND_LATE_MESSAGES_MISMATCH</center>
    SynchronizeLateMessagesRound --> SynchronizeLateMessagesRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    ValidateTransactionRound --> FinishedTransactionSubmissionRound: <center>DONE</center>
    ValidateTransactionRound --> CheckTransactionHistoryRound: <center>NEGATIVE</center>
    ValidateTransactionRound --> FinalizationRound: <center>VALIDATE_TIMEOUT<br />NONE</center>
    ValidateTransactionRound --> ValidateTransactionRound: <center>NO_MAJORITY</center>
</div>
<figcaption>TransactionSubmissionAbciApp FSM</figcaption>
</figure>

#### `ResetPauseAbciApp` FSM

```yaml title="fsm_specification.yaml"
alphabet_in:
- DONE
- NO_MAJORITY
- RESET_AND_PAUSE_TIMEOUT
default_start_state: ResetAndPauseRound
final_states:
- FinishedResetAndPauseErrorRound
- FinishedResetAndPauseRound
label: ResetPauseAbciApp
start_states:
- ResetAndPauseRound
states:
- FinishedResetAndPauseErrorRound
- FinishedResetAndPauseRound
- ResetAndPauseRound
transition_func:
    (ResetAndPauseRound, DONE): FinishedResetAndPauseRound
    (ResetAndPauseRound, NO_MAJORITY): FinishedResetAndPauseErrorRound
    (ResetAndPauseRound, RESET_AND_PAUSE_TIMEOUT): FinishedResetAndPauseErrorRound
```

<figure markdown>
<div class="mermaid">
stateDiagram-v2
    ResetAndPauseRound --> FinishedResetAndPauseRound: <center>DONE</center>
    ResetAndPauseRound --> FinishedResetAndPauseErrorRound: <center>NO_MAJORITY<br />RESET_AND_PAUSE_TIMEOUT</center>
</div>
<figcaption>ResetPauseAbciApp FSM</figcaption>
</figure>


#### `OracleAbciApp` FSM
As described above, the `OracleAbciApp` FSM is the composition of the
FSMs defined above using an FSM transition mapping that establishes the relationship
between the final states of a certain FSM with the start states of another FSM, that is,

```python
OracleAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        SafeDeploymentAbciApp,
        OracleDeploymentAbciApp,
        PriceAggregationAbciApp,
        TransactionSubmissionAbciApp,
        ResetPauseAbciApp,
    ),
    abci_app_transition_mapping,
)
```
The transition mapping for this FSM is defined as

```python
abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedRegistrationRound: RandomnessSafeRound,
    FinishedSafeRound: RandomnessOracleRound,
    FinishedOracleRound: CollectObservationRound,
    FinishedRegistrationFFWRound: CollectObservationRound,
    FinishedPriceAggregationRound: RandomnessTransactionSubmissionRound,
    FailedRound: ResetAndPauseRound,
    FinishedTransactionSubmissionRound: ResetAndPauseRound,
    FinishedResetAndPauseRound: CollectObservationRound,
    FinishedResetAndPauseErrorRound: RegistrationRound,
}
```



The complete specification of the composed FSM is therefore:

```yaml title="fsm_specification.yaml"
alphabet_in:
- CHECK_HISTORY
- CHECK_LATE_ARRIVING_MESSAGE
- CHECK_TIMEOUT
- DEPLOY_TIMEOUT
- DONE
- FAILED
- FAST_FORWARD
- FINALIZATION_FAILED
- FINALIZE_TIMEOUT
- INCORRECT_SERIALIZATION
- INSUFFICIENT_FUNDS
- MISSED_AND_LATE_MESSAGES_MISMATCH
- NEGATIVE
- NONE
- NO_MAJORITY
- RESET_AND_PAUSE_TIMEOUT
- RESET_TIMEOUT
- ROUND_TIMEOUT
- VALIDATE_TIMEOUT
default_start_state: RegistrationStartupRound
final_states: []
label: packages.valory.skills.oracle_abci.composition.OracleAbciApp
start_states:
- RegistrationStartupRound
states:
- CheckLateTxHashesRound
- CheckTransactionHistoryRound
- CollectObservationRound
- CollectSignatureRound
- DeployOracleRound
- DeploySafeRound
- EstimateConsensusRound
- FinalizationRound
- RandomnessOracleRound
- RandomnessSafeRound
- RandomnessTransactionSubmissionRound
- RegistrationRound
- RegistrationStartupRound
- ResetAndPauseRound
- ResetRound
- SelectKeeperOracleRound
- SelectKeeperSafeRound
- SelectKeeperTransactionSubmissionARound
- SelectKeeperTransactionSubmissionBRound
- SelectKeeperTransactionSubmissionBRoundAfterTimeout
- SynchronizeLateMessagesRound
- TxHashRound
- ValidateOracleRound
- ValidateSafeRound
- ValidateTransactionRound
transition_func:
    (CheckLateTxHashesRound, CHECK_LATE_ARRIVING_MESSAGE): SynchronizeLateMessagesRound
    (CheckLateTxHashesRound, CHECK_TIMEOUT): CheckLateTxHashesRound
    (CheckLateTxHashesRound, DONE): ResetAndPauseRound
    (CheckLateTxHashesRound, NEGATIVE): ResetAndPauseRound
    (CheckLateTxHashesRound, NONE): ResetAndPauseRound
    (CheckLateTxHashesRound, NO_MAJORITY): ResetAndPauseRound
    (CheckTransactionHistoryRound, CHECK_LATE_ARRIVING_MESSAGE): SynchronizeLateMessagesRound
    (CheckTransactionHistoryRound, CHECK_TIMEOUT): CheckTransactionHistoryRound
    (CheckTransactionHistoryRound, DONE): ResetAndPauseRound
    (CheckTransactionHistoryRound, NEGATIVE): SelectKeeperTransactionSubmissionBRound
    (CheckTransactionHistoryRound, NONE): ResetAndPauseRound
    (CheckTransactionHistoryRound, NO_MAJORITY): CheckTransactionHistoryRound
    (CollectObservationRound, DONE): EstimateConsensusRound
    (CollectObservationRound, NO_MAJORITY): CollectObservationRound
    (CollectObservationRound, ROUND_TIMEOUT): CollectObservationRound
    (CollectSignatureRound, DONE): FinalizationRound
    (CollectSignatureRound, NO_MAJORITY): ResetRound
    (CollectSignatureRound, ROUND_TIMEOUT): CollectSignatureRound
    (DeployOracleRound, DEPLOY_TIMEOUT): SelectKeeperOracleRound
    (DeployOracleRound, DONE): ValidateOracleRound
    (DeployOracleRound, FAILED): SelectKeeperOracleRound
    (DeploySafeRound, DEPLOY_TIMEOUT): SelectKeeperSafeRound
    (DeploySafeRound, DONE): ValidateSafeRound
    (DeploySafeRound, FAILED): SelectKeeperSafeRound
    (EstimateConsensusRound, DONE): TxHashRound
    (EstimateConsensusRound, NONE): CollectObservationRound
    (EstimateConsensusRound, NO_MAJORITY): CollectObservationRound
    (EstimateConsensusRound, ROUND_TIMEOUT): CollectObservationRound
    (FinalizationRound, CHECK_HISTORY): CheckTransactionHistoryRound
    (FinalizationRound, CHECK_LATE_ARRIVING_MESSAGE): SynchronizeLateMessagesRound
    (FinalizationRound, DONE): ValidateTransactionRound
    (FinalizationRound, FINALIZATION_FAILED): SelectKeeperTransactionSubmissionBRound
    (FinalizationRound, FINALIZE_TIMEOUT): SelectKeeperTransactionSubmissionBRoundAfterTimeout
    (FinalizationRound, INSUFFICIENT_FUNDS): SelectKeeperTransactionSubmissionBRound
    (RandomnessOracleRound, DONE): SelectKeeperOracleRound
    (RandomnessOracleRound, NO_MAJORITY): RandomnessOracleRound
    (RandomnessOracleRound, ROUND_TIMEOUT): RandomnessOracleRound
    (RandomnessSafeRound, DONE): SelectKeeperSafeRound
    (RandomnessSafeRound, NO_MAJORITY): RandomnessSafeRound
    (RandomnessSafeRound, ROUND_TIMEOUT): RandomnessSafeRound
    (RandomnessTransactionSubmissionRound, DONE): SelectKeeperTransactionSubmissionARound
    (RandomnessTransactionSubmissionRound, NO_MAJORITY): RandomnessTransactionSubmissionRound
    (RandomnessTransactionSubmissionRound, ROUND_TIMEOUT): RandomnessTransactionSubmissionRound
    (RegistrationRound, DONE): CollectObservationRound
    (RegistrationRound, NO_MAJORITY): RegistrationRound
    (RegistrationStartupRound, DONE): RandomnessSafeRound
    (RegistrationStartupRound, FAST_FORWARD): CollectObservationRound
    (ResetAndPauseRound, DONE): CollectObservationRound
    (ResetAndPauseRound, NO_MAJORITY): RegistrationRound
    (ResetAndPauseRound, RESET_AND_PAUSE_TIMEOUT): RegistrationRound
    (ResetRound, DONE): RandomnessTransactionSubmissionRound
    (ResetRound, NO_MAJORITY): ResetAndPauseRound
    (ResetRound, RESET_TIMEOUT): ResetAndPauseRound
    (SelectKeeperOracleRound, DONE): DeployOracleRound
    (SelectKeeperOracleRound, NO_MAJORITY): RandomnessOracleRound
    (SelectKeeperOracleRound, ROUND_TIMEOUT): RandomnessOracleRound
    (SelectKeeperSafeRound, DONE): DeploySafeRound
    (SelectKeeperSafeRound, NO_MAJORITY): RandomnessSafeRound
    (SelectKeeperSafeRound, ROUND_TIMEOUT): RandomnessSafeRound
    (SelectKeeperTransactionSubmissionARound, DONE): CollectSignatureRound
    (SelectKeeperTransactionSubmissionARound, INCORRECT_SERIALIZATION): ResetAndPauseRound
    (SelectKeeperTransactionSubmissionARound, NO_MAJORITY): ResetRound
    (SelectKeeperTransactionSubmissionARound, ROUND_TIMEOUT): SelectKeeperTransactionSubmissionARound
    (SelectKeeperTransactionSubmissionBRound, DONE): FinalizationRound
    (SelectKeeperTransactionSubmissionBRound, INCORRECT_SERIALIZATION): ResetAndPauseRound
    (SelectKeeperTransactionSubmissionBRound, NO_MAJORITY): ResetRound
    (SelectKeeperTransactionSubmissionBRound, ROUND_TIMEOUT): SelectKeeperTransactionSubmissionBRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, CHECK_HISTORY): CheckTransactionHistoryRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, CHECK_LATE_ARRIVING_MESSAGE): SynchronizeLateMessagesRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, DONE): FinalizationRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, INCORRECT_SERIALIZATION): ResetAndPauseRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, NO_MAJORITY): ResetRound
    (SelectKeeperTransactionSubmissionBRoundAfterTimeout, ROUND_TIMEOUT): SelectKeeperTransactionSubmissionBRoundAfterTimeout
    (SynchronizeLateMessagesRound, DONE): CheckLateTxHashesRound
    (SynchronizeLateMessagesRound, MISSED_AND_LATE_MESSAGES_MISMATCH): ResetAndPauseRound
    (SynchronizeLateMessagesRound, NONE): SelectKeeperTransactionSubmissionBRound
    (SynchronizeLateMessagesRound, NO_MAJORITY): SynchronizeLateMessagesRound
    (SynchronizeLateMessagesRound, ROUND_TIMEOUT): SynchronizeLateMessagesRound
    (TxHashRound, DONE): RandomnessTransactionSubmissionRound
    (TxHashRound, NONE): CollectObservationRound
    (TxHashRound, NO_MAJORITY): CollectObservationRound
    (TxHashRound, ROUND_TIMEOUT): CollectObservationRound
    (ValidateOracleRound, DONE): CollectObservationRound
    (ValidateOracleRound, NEGATIVE): RandomnessOracleRound
    (ValidateOracleRound, NONE): RandomnessOracleRound
    (ValidateOracleRound, NO_MAJORITY): RandomnessOracleRound
    (ValidateOracleRound, VALIDATE_TIMEOUT): RandomnessOracleRound
    (ValidateSafeRound, DONE): RandomnessOracleRound
    (ValidateSafeRound, NEGATIVE): RandomnessSafeRound
    (ValidateSafeRound, NONE): RandomnessSafeRound
    (ValidateSafeRound, NO_MAJORITY): RandomnessSafeRound
    (ValidateSafeRound, VALIDATE_TIMEOUT): RandomnessSafeRound
    (ValidateTransactionRound, DONE): ResetAndPauseRound
    (ValidateTransactionRound, NEGATIVE): CheckTransactionHistoryRound
    (ValidateTransactionRound, NONE): SelectKeeperTransactionSubmissionBRound
    (ValidateTransactionRound, NO_MAJORITY): ValidateTransactionRound
    (ValidateTransactionRound, VALIDATE_TIMEOUT): SelectKeeperTransactionSubmissionBRound
```

<figure markdown>
<div class="mermaid">
stateDiagram-v2
    RegistrationStartupRound --> RandomnessSafeRound: <center>DONE</center>
    RegistrationStartupRound --> CollectObservationRound: <center>FAST_FORWARD</center>
    CheckLateTxHashesRound --> ResetAndPauseRound: <center>DONE</center>
    CheckLateTxHashesRound --> RegistrationRound: <center>NEGATIVE<br />NONE<br />NO_MAJORITY</center>
    CheckLateTxHashesRound --> CheckLateTxHashesRound: <center>ROUND_TIMEOUT</center>
    CheckTransactionHistoryRound --> SynchronizeLateMessagesRound: <center>CHECK_LATE_ARRIVING_MESSAGE</center>
    CheckTransactionHistoryRound --> ResetAndPauseRound: <center>DONE</center>
    CheckTransactionHistoryRound --> RegistrationRound: <center>NEGATIVE<br />NONE<br />NO_MAJORITY</center>
    CheckTransactionHistoryRound --> CheckTransactionHistoryRound: <center>ROUND_TIMEOUT</center>
    CollectObservationRound --> EstimateConsensusRound: <center>DONE</center>
    CollectObservationRound --> CollectObservationRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    CollectSignatureRound --> FinalizationRound: <center>DONE</center>
    CollectSignatureRound --> ResetRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    DeployOracleRound --> SelectKeeperOracleRound: <center>DEPLOY_TIMEOUT<br />FAILED</center>
    DeployOracleRound --> ValidateOracleRound: <center>DONE</center>
    DeploySafeRound --> SelectKeeperSafeRound: <center>DEPLOY_TIMEOUT<br />FAILED</center>
    DeploySafeRound --> ValidateSafeRound: <center>DONE</center>
    EstimateConsensusRound --> TxHashRound: <center>DONE</center>
    EstimateConsensusRound --> CollectObservationRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    FinalizationRound --> CheckTransactionHistoryRound: <center>CHECK_HISTORY</center>
    FinalizationRound --> SynchronizeLateMessagesRound: <center>CHECK_LATE_ARRIVING_MESSAGE</center>
    FinalizationRound --> ValidateTransactionRound: <center>DONE</center>
    FinalizationRound --> SelectKeeperTransactionSubmissionBRound: <center>FINALIZATION_FAILED</center>
    FinalizationRound --> SelectKeeperTransactionSubmissionBRoundAfterTimeout: <center>ROUND_TIMEOUT</center>
    RandomnessOracleRound --> SelectKeeperOracleRound: <center>DONE</center>
    RandomnessOracleRound --> RandomnessOracleRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    RandomnessSafeRound --> SelectKeeperSafeRound: <center>DONE</center>
    RandomnessSafeRound --> RandomnessSafeRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    RandomnessTransactionSubmissionRound --> SelectKeeperTransactionSubmissionARound: <center>DONE</center>
    RandomnessTransactionSubmissionRound --> RandomnessTransactionSubmissionRound: <center>NO_MAJORITY</center>
    RandomnessTransactionSubmissionRound --> ResetRound: <center>ROUND_TIMEOUT</center>
    RegistrationRound --> CollectObservationRound: <center>DONE</center>
    ResetAndPauseRound --> CollectObservationRound: <center>DONE</center>
    ResetAndPauseRound --> RegistrationRound: <center>RESET_AND_PAUSE_TIMEOUT<br />NO_MAJORITY</center>
    ResetRound --> RandomnessTransactionSubmissionRound: <center>DONE</center>
    ResetRound --> RegistrationRound: <center>RESET_TIMEOUT<br />NO_MAJORITY</center>
    SelectKeeperOracleRound --> DeployOracleRound: <center>DONE</center>
    SelectKeeperOracleRound --> RandomnessOracleRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    SelectKeeperSafeRound --> DeploySafeRound: <center>DONE</center>
    SelectKeeperSafeRound --> RandomnessSafeRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    SelectKeeperTransactionSubmissionARound --> CollectSignatureRound: <center>DONE</center>
    SelectKeeperTransactionSubmissionARound --> ResetRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    SelectKeeperTransactionSubmissionBRound --> FinalizationRound: <center>DONE</center>
    SelectKeeperTransactionSubmissionBRound --> ResetRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    SelectKeeperTransactionSubmissionBRoundAfterTimeout --> CheckTransactionHistoryRound: <center>CHECK_HISTORY</center>
    SelectKeeperTransactionSubmissionBRoundAfterTimeout --> FinalizationRound: <center>DONE</center>
    SelectKeeperTransactionSubmissionBRoundAfterTimeout --> ResetRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    SynchronizeLateMessagesRound --> CheckLateTxHashesRound: <center>DONE</center>
    SynchronizeLateMessagesRound --> RegistrationRound: <center>NONE<br />MISSED_AND_LATE_MESSAGES_MISMATCH</center>
    SynchronizeLateMessagesRound --> SynchronizeLateMessagesRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    TxHashRound --> RandomnessTransactionSubmissionRound: <center>DONE</center>
    TxHashRound --> CollectObservationRound: <center>ROUND_TIMEOUT<br />NONE<br />NO_MAJORITY</center>
    ValidateOracleRound --> CollectObservationRound: <center>DONE</center>
    ValidateOracleRound --> RandomnessOracleRound: <center>NEGATIVE<br />NONE<br />VALIDATE_TIMEOUT<br />NO_MAJORITY</center>
    ValidateSafeRound --> RandomnessOracleRound: <center>DONE</center>
    ValidateSafeRound --> RandomnessSafeRound: <center>NEGATIVE<br />NONE<br />VALIDATE_TIMEOUT<br />NO_MAJORITY</center>
    ValidateTransactionRound --> ResetAndPauseRound: <center>DONE</center>
    ValidateTransactionRound --> CheckTransactionHistoryRound: <center>NEGATIVE</center>
    ValidateTransactionRound --> FinalizationRound: <center>NONE<br />VALIDATE_TIMEOUT</center>
    ValidateTransactionRound --> ValidateTransactionRound: <center>NO_MAJORITY</center>
</div>
<figcaption>OracleAbciApp FSM</figcaption>
</figure>
