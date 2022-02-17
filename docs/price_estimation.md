# Price estimation internals

Documentation of the price estimation demo.

## Introduction

The estimate is an average of a set of observations
on the Bitcoin price coming from different sources,
e.g. CoinMarketCap, CoinGecko, Binance and Coinbase.
Each AEA shares an observation from one of the sources above
by committing it to a temporary blockchain made with Tendermint.
Once all the observation are settled, each AEA
runs a script to aggregate the observations to compute an estimate,
and we say that the consensus is reached when one estimate
reaches `ceil((2n + 1) / 3)` of the total voting power committed
on the temporary blockchain.
Once the consensus on an estimate has been reached, a multi-signature transaction 
with `ceil((2n + 1) / 3)` of the participants' signature is settled on the 
Ethereum chain (in the POC this is the hardhat node).

Alongside the finite-state machine behaviour, the AEAs runs
an ABCI application instance which receives all the updates from the
underlying Tendermint network.


## Setup

The network is composed of:

- A [HardHat](https://hardhat.org/) node (the local blockchain)
- A set of $n$ Tendermint nodes
- A set of $n$ AEAs, in one-to-one connection with one Tendermint node.

![](./images/agent-to-node_connections.svg)

Agents communicate directly to their local tendermint node, whereas the `ABCIApp` 
is used to handle requests they receive (e.g. in response to their behaviour).

The AEAs have the following custom components:

- Protocol `valory/abci:0.1.0`: it allows representing
    ABCI request and response messages.
- Connection `valory/abci:0.1.0`: it accepts ABCI requests
    from a consensus engine module, e.g. the Tendermint node;
- Skill `valory/abstract_abci:0.1.0`: it provides a
    scaffold handler for ABCI requests. It is an abstract skill.
- Skill `valory/abstract_round_abci:0.1.0`: it
    implements an ABCI handler and provides
    useful code abstractions for creating round-based
    replicated state machines, based on the ABCI protocol
    (e.g. `Period`, `AbstractRound`). It is an abstract skill.

Moreover, it has the following demo-specific components:

- `valory/price_estimation_abci`: it implements the round-based
    ABCI application for price estimation of a cryptocurrency,
    with a finalization step over an Ethereum chain.


## Price estimation as a proof of concept

The ABCI-based replicated FSM (`ABCIApp`) used for price estimation consists 
of several smaller modules, each of which is an `ABCIApp` of its own. Each of 
them is a `Skill`, which implies that they operate independently of each other,
however they can be combined to create a larger `ABCIApp`, provided that the 
developer specifies the required transition mapping to connect these FSMs.
This modularity allows a developer to use a subset of these skills in different 
contexts, potentially in combination with skills they themselves define, to 
create another composite `ABCIApp` that performs according to their particular 
needs. Specifically, the `PriceEstimationAbciApp` is created by combining the 
following parts:

- `AgentRegistrationAbciApp`
- `SafeDeploymentAbciApp`
- `OracleDeploymentAbciApp`
- `PriceAggregationAbciApp`
- `TransactionSubmissionAbciApp`


### The `AgentRegistrationAbciApp`

This `AbciApp` implements the registration of agents to partake in the behaviour
scheduled in subsequent rounds. 

0. `RegistrationStartupRound` <br/>

1. `RegistrationRound` <br/>
   In this round registrations from AEAs to join the period are accepted, up to 
   a configured maximum number of participants (in the demo, this limit is 4); 
   once this threshold is hit ("registration threshold"), the round is finished.

2. `FinishedRegistrationRound` <br/>
   A round that signals agent registration was successful.

3. `FinishedRegistrationFFWRound` <br/>
   A round that signals agent registration was successful.


### The `SafeDeploymentAbciApp`

This `AbciApp` implements the deployments of a Gnosis safe contract, which is
a multisig smart contract wallet that requires a minimum number of people to 
approve a transaction before it can occur. This assures that no single agent 
can compromise the funds contained in it.

0. `RandomnessSafeRound` <br/>
   Some randomness is retrieved to be used in a keeper agent selection. In 
   particular, agents individually request the latest random number from
   [DRAND](https://drand.love), establish consensus on it and then use 
   it as a seed for computations requiring randomness (e.g. keeper selection).

1. `SelectKeeperSafeRound` <br/>
   The agents agree on a new keeper that will be in charge of sending deploying 
   the multisig wallet and settling transactions.

2. `DeploySafeRound` <br/>
   A designated sender among the participants of the current period deploys a
   <a href="https://gnosis-safe.io/">Gnosis Safe contract</a> with all the 
   participants as owners and with `ceil((2n + 1) / 3)` as threshold. If the 
   safe deployment has not been completed after some time, a new keeper will be 
   selected and the safe deployment will be re-run.
    
3. `ValidateSafeRound` <br/>
   All agents validate the previous deployment to ensure that the correct 
   contract with the correct settings has been deployed. If the safe deployment 
   could not be verified, the process will start again from the registration 
   round.

4. `FinishedSafeRound` <br/>
   A round that signals the safe contract was deployed successfully.


### The `OracleDeploymentAbciApp`

This `AbciApp` implements the deployments of an Oracle contract, a Gnosis safe 
multisig smart contract wallet that was forked from [Chainlink](https://chain.link/)
and subsequently stripped from unnecessary data structures and behaviours.

0. `RandomnessOracleRound` <br/>
   Similar as to the `RandomnessSafeRound`, randomness is retrieved here, this 
   time for the selection of an agent to become the oracle keeper.

1. `SelectKeeperOracleRound` <br/>
   The agents select a new keeper that will be in charge of sending deploying 
   the multisig wallet and settling transactions.

2. `DeployOracleRound` <br/>
   The designated keeper deploys a Gnosis safe contract. If a timeout occurs
   before oracle deployment was completed, a new keeper will be selected and
   the oracle deployment will be re-run.

3. `ValidateOracleRound` <br/>
   all agents verify that the Oracle contract has been  deployed using the 
   expected settings. If that's not the case, agents will restart the period.

4. `FinishedOracleRound`
   A round that signals the oracle contract was deployed successfully.


### The `PriceAggregationAbciApp`

This `AbciApp` implements off-chain aggregation of observations by the agents.
Once the majority of agents has submitted their observation these are shared 
with all agents as they move to the price estimation round. In this next round  
each of the agents performs off-chain a computation on the data set, which could
be a simple summary statistic or an estimate derived from a complex model - 
either way this is something that cannot be done on-chain. Once consensus is
reached on this estimate, the aggregate value is submitted and recorded 
on-chain in the next block that is mined.

0. `CollectObservationRound` <br/>
   Observational data is collected by the AEAs on the target quantity to 
   estimate. Once the agents reach consensus over this data, that is to say at 
   least 2/3rd of them agree on the set of single observations collected by 
   agents (not on individual observations), the shared state gets updated and
   the agents enter the next round.

1. `EstimateConsensusRound` <br/>
   Based on the collected data the actual price of the asset is estimated, which
   could be a simple summary statistic such as the median or the geometric mean.
   Once the same estimate receives a number of votes greater or equal than
   2/3 of the total voting power, consensus is reached and the period moves 
   forward.

2. `TxHashRound` <br/>
   A designated sender composes the transaction and puts it on the temporary 
   Tendermint-based chain. Signing of the transaction for the multisig smart
   contract requires consensus among the agents on the transaction hash to use.  

3. `FinishedPriceAggregationRound` <br/>
   A round that signals price aggregation was completed successfully.


### The `TransactionSubmissionAbciApp`

0. `RandomnessTransactionSubmissionRound` <br/>
   Randomness is retrieved for keeper selection. 

1. `SelectKeeperTransactionSubmissionRoundA` <br/>
   The agents select a keeper that will be in charge of sending the transaction.
    
2. `CollectSignatureRound` <br/>
   Agents sign the transaction to be submitted.

3. `FinalizationRound` <br/>
   The keeper sends off the transaction to be incorporated in the next block.
   A transaction hash is returned. This round takes care of submitting 
   with the right amount of gas, i.e., if resubmitting, then the "tip" for the miners
   is also increased by 10%.

4. `ValidateTransactionRound` <br/>
   Agents validate whether the transaction has been incorporated in the 
   blockchain.

5. `CheckTransactionHistoryRound` <br/>
   This round is triggered if the `ValidateTransactionRound` returns with
   a `NEGATIVE` `Event`, which means that the transaction has not been validated. 
   During the round, the agents check the transaction history upt to this point again
   in order to specify the cause of the problem, e.g., a transaction of a keeper 
   was settled before another keeper managed to do so, a payload is invalid, etc.

6. `SelectKeeperTransactionSubmissionRoundB` <br/>
   The agents select a keeper that will be in charge of sending the transaction, 
   in case that the first keeper has failed.    

7. `ResetRound` <br/>
   In case that a failure such as round timeout or no majority reached, the period 
   is reset.

8. `ResetAndPauseRound` <br/>
   A round that updates some period state data before going to the 
   `FinishedTransactionSubmissionRound`.

9. `FinishedTransactionSubmissionRound` <br/>
   A round that signals transaction submission was completed successfully.

10. `FailedRound` <br/>
    A round that signals transaction submission has failed. Occurs if the 
    `CheckTransactionHistoryRound` does not manage to find a validated transaction
    in the history, or if a Reset round fails.


### Implementation of the `PriceEstimationAbciApp`

In the final implementation the `PriceEstimationAbciApp` is then assembled from
its constituent parts. However, in order to combine the various FSMs previously
discussed, a transition mapping between states of these FSMs also needs to be 
provided. In order to combine the different FSMs we need to connect them by
providing the necessary transition mapping. As per the code implemented in the
[demo](./price_estimation_demo.md), the implementation looks as follows:

```python

abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedRegistrationRound: RandomnessSafeRound,
    FinishedSafeRound: RandomnessOracleRound,
    FinishedOracleRound: CollectObservationRound,
    FinishedRegistrationFFWRound: CollectObservationRound,
    FinishedPriceAggregationRound: RandomnessTransactionSubmissionRound,
    FinishedTransactionSubmissionRound: CollectObservationRound,
    FailedRound: RegistrationRound,
}

PriceEstimationAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        SafeDeploymentAbciApp,
        OracleDeploymentAbciApp,
        PriceAggregationAbciApp,
        TransactionSubmissionAbciApp,
    ),
    abci_app_transition_mapping,
)
```

!!! note

    The execution logic of the AbstractRoundBehaviour implemented below
    still requires documention here


```python
class PriceEstimationConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = PriceEstimationAbciApp
    behaviour_states: Set[Type[BaseState]] = {
        TendermintHealthcheckBehaviour,
        RegistrationBehaviour,
        RegistrationStartupBehaviour,
        RandomnessSafeBehaviour,
        RandomnessOracleBehaviour,
        SelectKeeperSafeBehaviour,
        DeploySafeBehaviour,
        ValidateSafeBehaviour,
        SelectKeeperOracleBehaviour,
        DeployOracleBehaviour,
        ValidateOracleBehaviour,
        RandomnessTransactionSubmissionBehaviour,
        ObserveBehaviour,
        EstimateBehaviour,
        TransactionHashBehaviour,
        SignatureBehaviour,
        FinalizeBehaviour,
        ValidateTransactionBehaviour,
        SelectKeeperTransactionSubmissionBehaviourA,
        SelectKeeperTransactionSubmissionBehaviourB,
        ResetBehaviour,
        ResetAndPauseBehaviour,
    }

```

Have a look at the [FSM diagram](./fsm_diagram.md) of the application in order 
to see what the encoded state transitions in the final composite FSM look like.

!!! warning

    A sequence diagram that shows how AEAs communicate with their environment
    throughout the execution can be found [here](poc-diagram.md). However,
    it is not fully up-to-date with the implementation discussed here.

### Appendix: High-level description of the constituent FSMs.
For reference, we provide a high-level descritpion of the automata that constitute
the five FSMs of this proof of concept using a simplified "Pythonic" syntax.
The syntax should be easy to understand for a reader familiar with conventional
automata textbook notation.

The aim of this syntax is to be used as a starting point in the design and
reasoning of an ABCI application without delving into the internals of the library
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

The summary of the FSMs is as follows:

| FSM                     | States  | Start states  | Final states  | Events  | Non-trivial transitions (*)   |
|-----------------------  |-------: |-------------: |-------------: |-------: |------------------------:  |
| AgentRegistration       |      4  |            2  |            2  |      3  |                       3   |
| SafeDeployment          |      5  |            1  |            1  |      8  |                      14   |
| OracleDeployment        |      5  |            1  |            1  |      8  |                      14   |
| PriceAggregation        |      9  |            1  |            1  |      4  |                       9   |
| TransactionSubmission   |     10  |            1  |            2  |      9  |                      26   |
| **PriceEstimation**     | **21**  |        **2**  |        **0**  | **12**  |                  **66**   |

(*) Transitions to a different state, i.e., not self-transitions.

#### `AgentRegistrationAbciApp` FSM
```python
AgentRegistrationAbciApp = DFA(
    label =
        'AgentRegistrationAbciApp',        
    states = {
        'RegistrationStartupRound',
        'RegistrationRound',
        'FinishedRegistrationRound',
        'FinishedRegistrationFFWRound'        
        },
    defaultStartState =
        'RegistrationStartupRound',
    startStates = {
        'RegistrationStartupRound',
        'RegistrationRound'
        },
    finalStates = {
        'FinishedRegistrationRound',
        'FinishedRegistrationFFWRound'        
        },
    alphabetIn = {
        'DONE',
        'FAST_FORWARD',
        'TIMEOUT'
        },
    transitionFunc = {
        ('RegistrationStartupRound', 'DONE'): 'FinishedRegistrationRound',
        ('RegistrationStartupRound', 'FAST_FORWARD'): 'FinishedRegistrationFFWRound',
        ('RegistrationRound', 'DONE'): 'FinishedRegistrationFFWRound',                
        }
    )
```

#### `SafeDeploymentAbciApp` FSM
```python
SafeDeploymentAbciApp = DFA(
    label =
        'SafeDeploymentAbciApp',        
    states = {
        'RandomnessSafeRound',
        'SelectKeeperSafeRound',
        'DeploySafeRound',
        'ValidateSafeRound',
        'FinishedSafeRound'        
        },
    defaultStartState =
        'RandomnessSafeRound',
    startStates = {
        'RandomnessSafeRound'
        },
    finalStates = {
        'FinishedSafeRound',
        },
    alphabetIn = {
        'DONE',
        'NO_MAJORITY',
        'ROUND_TIMEOUT',
        'DEPLOY_TIMEOUT',
        'VALIDATE_TIMEOUT',
        'FAILED',
        'NEGATIVE',
        'NONE'
        },
    transitionFunc = {
        ('RandomnessSafeRound', 'DONE'): 'SelectKeeperSafeRound',
        ('RandomnessSafeRound', 'ROUND_TIMEOUT'): 'RandomnessSafeRound',
        ('RandomnessSafeRound', 'NO_MAJORITY'): 'RandomnessSafeRound',                
        ('SelectKeeperSafeRound', 'DONE'): 'DeploySafeRound',
        ('SelectKeeperSafeRound', 'ROUND_TIMEOUT'): 'RandomnessSafeRound',
        ('SelectKeeperSafeRound', 'NO_MAJORITY'): 'RandomnessSafeRound',
        ('DeploySafeRound', 'DONE'): 'ValidateSafeRound',
        ('DeploySafeRound', 'DEPLOY_TIMEOUT'): 'SelectKeeperSafeRound',
        ('DeploySafeRound', 'FAILED'): 'SelectKeeperSafeRound',                
        ('ValidateSafeRound', 'DONE'): 'FinishedSafeRound',
        ('ValidateSafeRound', 'NEGATIVE'): 'RandomnessSafeRound',
        ('ValidateSafeRound', 'NONE'): 'RandomnessSafeRound',
        ('ValidateSafeRound', 'VALIDATE_TIMEOUT'): 'RandomnessSafeRound',
        ('ValidateSafeRound', 'NO_MAJORITY'): 'RandomnessSafeRound'               
        }
    )
```

#### `OracleDeploymentAbciApp` FSM
```python
OracleDeploymentAbciApp = DFA(
    label =
        'OracleDeploymentAbciApp',        
    states = {
        'RandomnessOracleRound',
        'SelectKeeperOracleRound',
        'DeployOracleRound',
        'ValidateOracleRound',
        'FinishedOracleRound'  
        },
    defaultStartState =
        'RandomnessOracleRound',
    startStates = {
        'RandomnessOracleRound'
        },        
    finalStates = {
        'FinishedOracleRound'
        },
    alphabetIn = {
        'DONE',
        'ROUND_TIMEOUT',
        'DEPLOY_TIMEOUT',
        'VALIDATE_TIMEOUT',
        'FAILED',
        'NEGATIVE',
        'NONE',
        'NO_MAJORITY'
        },
    transitionFunc = {
        ('RandomnessOracleRound', 'DONE'): 'SelectKeeperOracleRound',
        ('RandomnessOracleRound', 'ROUND_TIMEOUT'): 'RandomnessOracleRound',
        ('RandomnessOracleRound', 'NO_MAJORITY'): 'RandomnessOracleRound',                
        ('SelectKeeperOracleRound', 'DONE'): 'DeployOracleRound',
        ('SelectKeeperOracleRound', 'ROUND_TIMEOUT'): 'RandomnessOracleRound',
        ('SelectKeeperOracleRound', 'NO_MAJORITY'): 'RandomnessOracleRound',
        ('DeployOracleRound', 'DONE'): 'ValidateOracleRound',
        ('DeployOracleRound', 'DEPLOY_TIMEOUT'): 'SelectKeeperOracleRound',
        ('DeployOracleRound', 'FAILED'): 'SelectKeeperOracleRound',
        ('ValidateOracleRound', 'DONE'): 'FinishedOracleRound',
        ('ValidateOracleRound', 'NEGATIVE'): 'RandomnessOracleRound',
        ('ValidateOracleRound', 'NONE'): 'RandomnessOracleRound',
        ('ValidateOracleRound', 'VALIDATE_TIMEOUT'): 'RandomnessOracleRound',
        ('ValidateOracleRound', 'NO_MAJORITY'): 'RandomnessOracleRound'
        }
    )
```

#### `PriceAggregationAbciApp` FSM
```python
PriceAggregationAbciApp = DFA(
    label =
        'PriceAggregationAbciApp',        
    states = {
        'CollectObservationRound',
        'EstimateConsensusRound',
        'TxHashRound',
        'FinishedPriceAggregationRound'        
        },
    defaultStartState =
        'CollectObservationRound',
    startStates = {
        'CollectObservationRound'
        },
    finalStates = {
        'FinishedPriceAggregationRound'  
        },
    alphabetIn = {
        'DONE',
        'ROUND_TIMEOUT',
        'NO_MAJORITY',
        'NONE'
        },
    transitionFunc = {
        ('CollectObservationRound', 'DONE'): 'EstimateConsensusRound',
        ('CollectObservationRound', 'ROUND_TIMEOUT'): 'CollectObservationRound',
        ('EstimateConsensusRound', 'DONE'): 'TxHashRound',
        ('EstimateConsensusRound', 'ROUND_TIMEOUT'): 'CollectObservationRound',
        ('EstimateConsensusRound', 'NO_MAJORITY'): 'CollectObservationRound',
        ('TxHashRound', 'DONE'): 'FinishedPriceAggregationRound',
        ('TxHashRound', 'NONE'): 'CollectObservationRound',
        ('TxHashRound', 'ROUND_TIMEOUT'): 'CollectObservationRound',                            
        ('TxHashRound', 'NO_MAJORITY'): 'CollectObservationRound'
        }
    )
```

#### `TransactionSubmissionAbciApp` FSM
```python
TransactionSubmissionAbciApp = DFA(
    label =
        'TransactionSubmissionAbciApp',        
    states = {
        'RandomnessTransactionSubmissionRound',
        'SelectKeeperTransactionSubmissionRoundA',
        'CollectSignatureRound',
        'FinalizationRound',
        'ValidateTransactionRound',
        'SelectKeeperTransactionSubmissionRoundB',
        'ResetRound',
        'ResetAndPauseRound',
        'FinishedTransactionSubmissionRound',
        'FailedRound'
        },
    defaultStartState =
        'RandomnessTransactionSubmissionRound',
    startStates = {
        'RandomnessTransactionSubmissionRound'
        },        
    finalStates = {
        'FinishedTransactionSubmissionRound',
        'FailedRound'        
        },
    alphabetIn = {
        'DONE',
        'ROUND_TIMEOUT',
        'NO_MAJORITY',
        'FAILED',
        'NEGATIVE',
        'NONE',
        'VALIDATE_TIMEOUT',
        'RESET_TIMEOUT',        
        'NO_MAJORITY',
        'RESET_AND_PAUSE_TIMEOUT'
        },
    transitionFunc = {
        ('RandomnessTransactionSubmissionRound', 'DONE'): 'SelectKeeperTransactionSubmissionRoundA',
        ('RandomnessTransactionSubmissionRound', 'ROUND_TIMEOUT'): 'ResetRound',
        ('RandomnessTransactionSubmissionRound', 'NO_MAJORITY'): 'RandomnessTransactionSubmissionRound',                
        ('SelectKeeperTransactionSubmissionRoundA', 'DONE'): 'CollectSignatureRound',
        ('SelectKeeperTransactionSubmissionRoundA', 'ROUND_TIMEOUT'): 'ResetRound',
        ('SelectKeeperTransactionSubmissionRoundA', 'NO_MAJORITY'): 'ResetRound',
        ('CollectSignatureRound', 'DONE'): 'FinalizationRound',
        ('CollectSignatureRound', 'ROUND_TIMEOUT'): 'ResetRound',
        ('CollectSignatureRound', 'NO_MAJORITY'): 'ResetRound',
        ('FinalizationRound', 'DONE'): 'ValidateTransactionRound',
        ('FinalizationRound', 'ROUND_TIMEOUT'): 'SelectKeeperTransactionSubmissionRoundB',
        ('FinalizationRound', 'FAILED'): 'SelectKeeperTransactionSubmissionRoundB',
        ('ValidateTransactionRound', 'DONE'): 'ResetAndPauseRound',
        ('ValidateTransactionRound', 'NEGATIVE'): 'ResetRound',
        ('ValidateTransactionRound', 'NONE'): 'ResetRound',
        ('ValidateTransactionRound', 'VALIDATE_TIMEOUT'): 'FinalizationRound',
        ('ValidateTransactionRound', 'NO_MAJORITY'): 'ValidateTransactionRound',
        ('SelectKeeperTransactionSubmissionRoundB', 'DONE'): 'FinalizationRound',
        ('SelectKeeperTransactionSubmissionRoundB', 'ROUND_TIMEOUT'): 'ResetRound',
        ('SelectKeeperTransactionSubmissionRoundB', 'NO_MAJORITY'): 'ResetRound',
        ('ResetRound', 'DONE'): 'RandomnessTransactionSubmissionRound',        
        ('ResetRound', 'RESET_TIMEOUT'): 'FailedRound',
        ('ResetRound', 'NO_MAJORITY'): 'FailedRound',
        ('ResetAndPauseRound', 'DONE'): 'FinishedTransactionSubmissionRound',                      
        ('ResetAndPauseRound', 'RESET_AND_PAUSE_TIMEOUT'): 'FailedRound',
        ('ResetAndPauseRound', 'NO_MAJORITY'): 'FailedRound'
        }
    )
```

#### `PriceEstimationAbciApp` FSM
As described above, the `PriceEstimationAbciApp` FSM is the composition of the
FSMs defined above using an FSM transition mapping that establishes the relationship
between the final states of a certain FSM with the start states of another FSM, that is,

```python
PriceEstimationAbciApp = compose_dfa(
    (
        AgentRegistrationAbciApp,
        SafeDeploymentAbciApp,
        OracleDeploymentAbciApp,
        PriceAggregationAbciApp,
        TransactionSubmissionAbciApp    
    ),
    PriceEstimationAbciAppTransitionMapping
)
```
The transition mapping for this FSM is defined as

```python
PriceEstimationAbciAppTransitionMapping = {
    'FinishedRegistrationRound': 'RandomnessSafeRound',
    'FinishedSafeRound': 'RandomnessOracleRound',
    'FinishedOracleRound': 'CollectObservationRound',
    'FinishedRegistrationFFWRound': 'CollectObservationRound',
    'FinishedPriceAggregationRound': 'RandomnessTransactionSubmissionRound',
    'FinishedTransactionSubmissionRound': 'CollectObservationRound',
    'FailedRound': 'RegistrationRound',    
    }
```
