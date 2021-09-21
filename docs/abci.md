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

<div style="text-align: center;"> 
  <img src="../abci-tendermint.jpg" alt="ABCI and Tendermint" />
</div>

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
interactions between the consensus node and the ABCI application:

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

Some requests like `Info` and `InitChain` are proactively 
made by the consensus node upon genesis; most of the requests
instead depend on the transactions stored in the mempool.
The transaction are submitted by a third entity, 
the _User_, that uses the ABCI app
by interacting with a Tendermint node
through the [Tendermint RPC protocol](https://docs.tendermint.com/master/rpc/).
At [this link](https://github.com/tendermint/tendermint/blob/master/proto/tendermint/abci/types.proto), 
you can see the Protobuf definitions of those messages.

In the following, we will review the most important interactions
between an user, a Tendermint node, and an ABCI-application instance,
with a focus on how the ABCI protocol comes into play.

A quick overview of the ABCI protocol is depicted in this diagram:

![](abci-requests.png)

### Send a transaction

The user can send a transaction by using the following three
Tendermint RPC methods:

- [`broadcast_tx_sync`](https://docs.tendermint.com/master/rpc/#/Tx/broadcast_tx_sync),
  which is blocking until the transaction is considered valid and added to the mempool;
- [`broadcast_tx_async`](https://docs.tendermint.com/master/rpc/#/Tx/broadcast_tx_async),
  which does not wait until the transaction is considered valid and added to the mempool;
- [`broadcast_tx_commit`](https://docs.tendermint.com/master/rpc/#/Tx/broadcast_tx_commit),
  which waits until the transaction is committed into a block and processed by the ABCI app.

Note that the above methods take in input a transaction, i.e. a sequence of bytes.
The consensus node does not know the meaning of the content of the transaction,
as its meaning resides in the ABCI application logic. This is a key feature
that makes the application layer and the consensus layer highly decoupled.

#### The `broadcast_tx_sync` method


<div class="mermaid">
    sequenceDiagram

        participant User
        participant Tendermint node
        participant ABCI app

        User->>Tendermint node: broadcast_tx_sync(tx=0x1234...)
        activate User
        note over User: wait until the transaction<br/>is added to the mempool
        
        Tendermint node->>ABCI app: RequestCheckTx(tx)
        alt tx is not valid
          ABCI app->>Tendermint node: ResponseCheckTx(ERROR)
          Tendermint node->>User: ERROR
        else tx is valid
          ABCI app->>Tendermint node: ResponseCheckTx(OK)
          Tendermint node->>Tendermint node: add tx to mempool
          Tendermint node->>User: OK
        end

        deactivate User

</div>

#### The `broadcast_tx_async` method


<div class="mermaid">
    sequenceDiagram

        participant User
        participant Tendermint node
        participant ABCI app

        User->>Tendermint node: broadcast_tx_sync(tx=0x1234...)
        activate User
        note over User: user does not wait...
        deactivate User

</div>


#### The `broadcast_tx_commit` method

<div class="mermaid">
    sequenceDiagram

        participant User
        participant Tendermint node
        participant ABCI app

        User->>Tendermint node: broadcast_tx_commit(tx=0x1234...)
        activate User
        note over User: wait until the transaction<br/>is committed to the chain
        
        Tendermint node->>ABCI app: RequestCheckTx(tx)
        alt tx is not valid
          ABCI app->>Tendermint node: ResponseCheckTx(ERROR)
          Tendermint node->>User: ERROR
          note over User: STOP
        end
        note over User, ABCI app: tx passed the mempool check
        ABCI app->>Tendermint node: ResponseCheckTx(OK)
        Tendermint node->>Tendermint node: add tx to mempool
        note over Tendermint node: eventually, the tx gets<br/>added to a committed block 
        note over Tendermint node: on receipt of such block:
        Tendermint node->>ABCI app: RequestBeginBlock(...)
        ABCI app->>Tendermint node: ResponseBeginBlock(...)
        loop for tx_i in block
          Tendermint node->>ABCI app: RequestDeliverTx(tx_i)
          ABCI app->>Tendermint node: ResponseDeliverTx(tx_i)
        end
        Tendermint node->>ABCI app: RequestEndBlock(...)
        ABCI app->>Tendermint node: ResponseEndBlock(...)
        
        alt if ResponseDeliverTx(tx) == OK
          Tendermint node->>User: ERROR
        else
          Tendermint node->>User: OK
        end
        deactivate User

</div>

### Query the state

The ABCI appplication state can be queried by means of the 
[`abci_query`](https://docs.tendermint.com/master/rpc/#/ABCI/abci_query)
request.
The sender has to provide the `path` parameter (a string) and the `data`
parameter (a string). The actual content will depend on the queries the ABCI application
supports.

The consensus node forwards the query through the `Query` request.

#### `abci_query`

<div class="mermaid">
    sequenceDiagram

        participant User
        participant Tendermint node
        participant ABCI app

        User->>Tendermint node: query(path="/a/b/c", data=0x123...)
        activate User
        Tendermint node->>ABCI app: RequestQuery(...)
        ABCI app->>Tendermint node: ResponseQuery(...)
        Tendermint node->>User: response(...)
        deactivate User

</div>
