# Liquidity provision

## Description

This module contains the liquidity provision skill for an AEA.

## Behaviours

* `EnterPoolRandomnessBehaviour`

   Get randomness.

* `EnterPoolSelectKeeperBehaviour`

   'exit pool' select keeper.

* `EnterPoolTransactionHashBehaviour`

   Prepare the transaction hash for entering the liquidity pool

* `EnterPoolTransactionSendBehaviour`

   Send the transaction for entering the liquidity pool

* `EnterPoolTransactionSignatureBehaviour`

   Sign the transaction for entering the liquidity pool

* `EnterPoolTransactionValidationBehaviour`

   Validate the transaction for entering the liquidity pool

* `ExitPoolRandomnessBehaviour`

   Get randomness.

* `ExitPoolSelectKeeperBehaviour`

   'exit pool' select keeper.

* `ExitPoolTransactionHashBehaviour`

   Prepare the transaction hash for exiting the liquidity pool

* `ExitPoolTransactionSendBehaviour`

   Send the transaction hash for exiting the liquidity pool

* `ExitPoolTransactionSignatureBehaviour`

   Sign the transaction hash for exiting the liquidity pool

* `ExitPoolTransactionValidationBehaviour`

   Validate the transaction hash for exiting the liquidity pool

* `LiquidityProvisionBaseBehaviour`

   Base state behaviour for the liquidity provision skill.

* `LiquidityProvisionConsensusBehaviour`

   Managing of consensus stages for liquidity provision.

* `StrategyEvaluationBehaviour`

   Evaluate the financial strategy.

* `SwapBackRandomnessBehaviour`

   Get randomness.

* `SwapBackSelectKeeperBehaviour`

   'swap back' select keeper.

* `SwapBackTransactionHashBehaviour`

   Prepare the transaction hash for swapping back assets

* `SwapBackTransactionSendBehaviour`

   Send the transaction hash for swapping back assets

* `SwapBackTransactionSignatureBehaviour`

   Sign the transaction hash for swapping back assets

* `SwapBackTransactionValidationBehaviour`

   Validate the transaction hash for swapping back assets

* `TransactionSendBaseBehaviour`

   Finalize state.

* `TransactionSignatureBaseBehaviour`

   Signature base behaviour.

* `TransactionValidationBaseBehaviour`

   Validate a transaction.


## Handlers

* `ABCILiquidityProvision`
* `HttpHandler`
* `SigningHandler`
* `LedgerApiHandler`
* `ContractApiHandler`

