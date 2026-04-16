# Squads Multisig Program

## Description

Contract package for interacting with [Squads Multisig Program](https://github.com/Squads-Protocol/v4). This contract package provides functionalities to perform transactions on `solana` via a multisig program. To make a transaction you will have to go through following steps

1. Define transaction index (`SquadsMultisig.next_tx_index`)
2. Create a transaction [PDA](https://solanacookbook.com/core-concepts/pdas.html#facts) using the index (`SquadsMultisig.get_tx_pda`)
3. Create a transaction (`SquadsMultisig.create_transaction_ix`)
4. Attach instructions (`SquadsMultisig.add_instruction_ix`)
5. Activate transaction (`SquadsMultisig.activate_transaction_ix`)
6. Approve transaction (`SquadsMultisig.approve_transaction_ix`)
7. Execute transaction (`SquadsMultisig.execute_transaction_ix`)

The steps 3,4 and 5 can be combined using `SquadsMultisig.create_new_transaction_ix` method as well.

## Functions

- `get_program_instance`: Load squads multisig program instance

- `get_account_state`: Get multisig account state

- `current_tx_index`: Get current transaction index

- `next_tx_index`: Get next transaction index

- `current_ix_index`: Get current instruction index for a transaction

- `next_ix_index`:  Get next instruction index for a transaction

- `get_tx_pda`: Get PDA for a transaction

- `get_ix_pda`: Get PDA for an instruction

- `create_transaction_ix`: Create instruction set for creating a transaction

- `add_instruction_ix`: Create instruction set for adding an instruction

- `activate_transaction_ix`: Create instruction set for activating a transaction

- `create_new_transaction_ix`: Create instruction set for creating and activating the transaction with given list of instruction

- `approve_transaction_ix`: Create instruction set for approving a transaction

- `execute_transaction_ix`: Create instruction set for executing a transaction
