# Error handling

Errors that arise during the execution of an autonomous agent system are categorized in two different classes: `AppExceptions` and `AppErrors`. The main difference between the two is the need of handling them, so we use this language so that developers know what must be handled by the application and what not.

## AppExceptions
AppExceptions are runtime errors that arise from faulty or malicious agent-to-agent interactions and need to be caught and handled. Examples of this are transaction signature errors (`SignatureNotValidError`), unexpected content being sent by a faulty agent (`TransactionNotValidError`) or problems that happen while committing a new block to the blockchain (`AddBlockError`).

In this scenario, an error code different from 0 will be returned to the Tendermint node while the agent tries to recover from the error. If this is not possible, and the agent is not able to progress with the round, the `FAIL` flag will be set by calling `set_fail()` and the agent will transition into a `WaitBehaviour` state. In the case the round cannot be finished without this agent (for example, due to not meeting the minimum quorum requirements), all agents will try to agree to restart the round from the beginning.


## AppErrors
AppErrors errors are basically inconsistencies in the application logic and are not handled. These are usually problems within the ABCI app implementation, that should not be caught, for instance missing `None` or initialization checks that lead to an application crash so the developers can trace it and solve it.

