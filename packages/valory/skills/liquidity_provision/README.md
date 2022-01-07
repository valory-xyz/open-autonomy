# Liquidity provision skill

## Description

This skill implements liquidity provision capacities to move into and out
of Uniswap-V2-based liquidity pools.


## Behaviours

- LiquidityProvisionBaseBehaviour
- TransactionSignatureBaseBehaviour
- TransactionSendBaseBehaviour
- TransactionValidationBaseBehaviour

- StrategyEvaluationBehaviour

- EnterPoolTransactionHashBehaviour
- EnterPoolTransactionSignatureBehaviour
- EnterPoolTransactionSendBehaviour
- EnterPoolTransactionValidationBehaviour
- EnterPoolRandomnessBehaviour
- EnterPoolSelectKeeperBehaviour

- ExitPoolTransactionHashBehaviour
- ExitPoolTransactionSignatureBehaviour
- ExitPoolTransactionSendBehaviour
- ExitPoolTransactionValidationBehaviour
- ExitPoolRandomnessBehaviour
- ExitPoolSelectKeeperBehaviour

- SwapBackTransactionHashBehaviour
- SwapBackTransactionSignatureBehaviour
- SwapBackTransactionSendBehaviour
- SwapBackTransactionValidationBehaviour
- SwapBackRandomnessBehaviour
- SwapBackSelectKeeperBehaviour

- LiquidityProvisionConsensusBehaviour


## Handlers

- ABCILiquidityProvision
- HttpHandler
- SigningHandler
- LedgerApiHandler
- ContractApiHandler
