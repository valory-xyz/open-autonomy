# Price estimation abci

## Description

This module contains the ABCI cryptocurrency price estimation skill for an AEA
through aggregation of observations from different sources.

## Behaviours

* `EstimateBehaviour`

   Estimate price.

* `ObserveBehaviour`

   Observe price estimate.

* `PriceEstimationBaseState`

   Base state behaviour for the common apps' skill.

* `PriceEstimationConsensusBehaviour`

   This behaviour manages the consensus stages for the price estimation.

* `TransactionHashBehaviour`

   Share the transaction hash for the signature round.


## Handlers

* `ABCIPriceEstimationHandler`
* `HttpHandler`
* `SigningHandler`
* `LedgerApiHandler`
* `ContractApiHandler`

