# ABCI Counter skill

## Description

This skill implements the [ABCI `counter` application](https://docs.tendermint.com/master/app-dev/getting-started.html),
a toy example for [Tendermint](https://docs.tendermint.com/master/tendermint-core/using-tendermint.html). 

## Behaviours 

No behaviours (the skill is purely reactive).

## Handlers

* `counter`: handles `abci` messages from a Tendermint node and implements the ABCI `counter` app.
