# Counter

## Description

This module contains an example of the counter ABCI skill for an AEA.
It implements the [ABCI `counter` application](https://docs.tendermint.com/v0.34/app-dev/getting-started.html),
a toy example for [Tendermint](https://docs.tendermint.com/v0.34/tendermint-core/using-tendermint.html).

## Behaviours

No behaviours (the skill is purely reactive).

## Handlers

* `ABCICounterHandler`

   Handles ABCI messages from a Tendermint node and implements the ABCI
    Counter app.


