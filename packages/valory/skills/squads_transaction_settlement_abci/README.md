# Transaction settlement abci for `solana` chain

## Description

This skill package provides functionalities for making transactions on `solana` via the [Squads Multisig Program](https://github.com/Squads-Protocol/v4) and the [Squads Multisig Contract](https://github.com/valory-xyz/open-autonomy/tree/9ec25e6b7973044a63d5b0f1db3930c467c224a3/packages/valory/contracts/squads_multisig).

## Behaviours

* `CreateTxRandomnessRoundRandomnessBehaviour`

    Randomness behaviour for creating transaction

* `CreateTxSelectKeeperBehaviour`

    Behaviour for selecting keeper for creating transaction

* `CreateTxBehaviour`

    Behaviour for creating a transaction

* `ApproveTxBehaviour`

    Behaviour for approving transaction

* `ExecuteTxRandomnessRoundRandomnessBehaviour`

    Randomness behaviour for executing transaction

* `ExecuteTxSelectKeeperBehaviour`

    Behaviour for selecting keeper for executing transaction

* `ExecuteTxBehaviour`

    Behaviour for executing transaction

* `VerifyTxBehaviour`

    Behaviour for verifying transaction


This ABCI skill requires `most_voted_instruction_set` to be set on the sync `db`. Value of `most_voted_instruction_set` should be a list of serialized instructions.