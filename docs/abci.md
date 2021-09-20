# Application BlockChain Interface (ABCI)

This document briefly describes 
the most salient aspects of 
the Application BlockChain Interface (ABCI),
which allows for Byzantine Fault Tolerant replication of 
applications written in any programming language.

## Introduction

Blockchains are systems for multi-master state machine replication. 
**ABCI** is an interface that defines the boundary between the
**replication (or consensus) engine** 
(the blockchain), and the **state machine** (the application). 
Using a socket protocol, a consensus engine running in one process can manage 
an application state running in another.

The ABCI standard was introduced contextually with the
[Tendermint project](https://docs.tendermint.com/master/introduction/what-is-tendermint.html), 
although an ABCI-based app can work with any consensus engine
that is ABCI-compatible, e.g. see [Fantom](https://fantom.foundation/about/).
In the following, we will consider Tendermint as our state-replication layer.

## What is Tendermint

Tendermint is a software for securely and consistently replicating 
an application on many machines.
It is Byzantine fault tolerant (BFT),
i.e. it has the ability to tolerate machines failing in arbitrary ways, 
including becoming malicious.

Tendermint consists of two chief technical components: 
a **blockchain consensus engine** and a **generic application interface**.

- the consensus engine, called **Tendermint Core**, ensures that the 
  same transactions are recorded on every machine in the same order. 
- The application interface, called the **Application BlockChain Interface (ABCI)**, 
  enables the transactions to be processed in any programming language. 
  Unlike other blockchain and consensus solutions, which come pre-packaged with 
  built in state machines, developers can use Tendermint for 
  BFT state machine replication of applications written in whatever programming 
  language and development environment is right for them.

In the picture below, you can see how Tendermint
modularizes a distributed state-machine replication system
by clearly separating the business logic layer (the application)
from the consensus and networking layer (the consensus engine)
through the ABCI protocol:

![](abci-tendermint.jpg)

The interaction between the consensus node and the ABCI application
follows the client-server paradigm:
the ABCI application (the server) listens for requests coming
from the consensus node (the client), which sends requests
to the ABCI application for different purposes, e.g.
check whether a transaction is valid and therefore if it can be added
to the transaction pool, to notify the app that 
a block has been validated, or to get information from the 
application layer.

A detailed description of the consensus algorithm implemented
by Tendermint is out of the scope of this document.
Please refer to the relevant pages of the 
[Tendermint official website](https://docs.tendermint.com/master/introduction/what-is-tendermint.html)
for more details.

## The ABCI protocol

The ABCI protocol specifies the following request-response
interactions:

- `Echo`
- `Flush`
- `Info`
- `InitChain`
- `Query`
- `BeginBlock`
- `CheckTx`
- `DeliverTx`
- `EndBlock`
- `Commit`
- `ListSnapshots`
- `OfferSnapshot`
- `LoadSnapshotChunk`
- `ApplySnapshotChunk`


