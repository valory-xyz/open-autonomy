# Simple abci

## Description

This module contains the ABCI simple skill for an AEA. It implements an ABCI
application for a simple demonstration.

## Behaviours

* `BaseResetBehaviour`

   Reset state.

* `RandomnessAtStartupBehaviour`

   Retrieve randomness at startup.

* `RandomnessBehaviour`

   Check whether Tendermint nodes are running.

* `RegistrationBehaviour`

   Register to the next round.

* `ResetAndPauseBehaviour`

   Reset state.

* `SelectKeeperAAtStartupBehaviour`

   Select the keeper agent at startup.

* `SelectKeeperBehaviour`

   Select the keeper agent.

* `SimpleABCIBaseState`

   Base state behaviour for the simple abci skill.

* `SimpleAbciConsensusBehaviour`

   This behaviour manages the consensus stages for the simple abci app.


## Handlers

* `SimpleABCIHandler`
* `HttpHandler`
* `SigningHandler`
* `LedgerApiHandler`
* `ContractApiHandler`

