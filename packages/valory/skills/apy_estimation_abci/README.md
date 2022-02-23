# Apy estimation abci

## Description

This module contains the APY estimation skill for an AEA.

## Behaviours

* `APYEstimationBaseState`

   Base state behaviour for the APY estimation skill.

* `APYEstimationConsensusBehaviour`

   This behaviour manages the consensus stages for the APY estimation.

* `BaseResetBehaviour`

   Reset state.

* `CycleResetBehaviour`

   Cycle reset state.

* `EmptyResponseError`

   Exception for empty response.

* `EstimateBehaviour`

   Estimate APY.

* `FetchBehaviour`

   Observe historical data.

* `OptimizeBehaviour`

   Run an optimization study based on the training data.

* `PreprocessBehaviour`

   Preprocess historical data (train-test split).

* `RandomnessBehaviour`

   Get randomness value from `drnand`.

* `RegistrationBehaviour`

   Register to the next periods.

* `ResetBehaviour`

   Reset state.

* `TestBehaviour`

   Test an estimator.

* `TrainBehaviour`

   Train an estimator.

* `TransformBehaviour`

   Transform historical data, i.e., convert them to a dataframe and calculate useful metrics, such as the APY.


## Handlers

* `ABCIAPYEstimationHandler`
* `HttpHandler`
* `SigningHandler`
* `LedgerApiHandler`
* `ContractApiHandler`

