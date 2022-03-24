# ABCI: Implementation

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
At [this link](https://github.com/tendermint/abci/blob/master/types/types.proto),
you can see the Protobuf definitions of those messages.

In the following, we will review the most important interactions
between a simple user, a Tendermint node, and an ABCI-application instance,
with a focus on how the ABCI protocol comes into play.

A quick overview of the ABCI protocol is depicted in this diagram:

![](./images/abci-requests.png)

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

The ABCI application state can be queried by means of the
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
