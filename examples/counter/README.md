# ABCI Counter with AEAs

This demo shows how to run an ABCI counter application
over Tendermint.
It is an example on how to replicate an application state-machine
across different AEAs using the Tendermint consensus engine.

## Preliminaries

Make sure you have installed on your machine:

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Run

To set up the network:

```
make localnet-start
```

The network is made of:
- 4 Tendermint nodes, `node0`, `node1`, `node2`, and `node3`,
which are listening at ports `26657`, `26667`, `26677`, `26687`
for RCP requests, respectively, and
- 4 AEAs, `abci0`, `abci1`, `abci2`, and `abci3`,
  each of them connected to one and only one Tendermint node `nodeX`. 
 
Each AEA has the ABCI skill `counter`, and the Tendermint network
manages the consensus for incoming transactions.

## Query

Once the network is up, you can interact with it.
For example, to query the state of the ABCI application
from one Tendermint node, say `node0`:

```
curl http://localhost:26657/abci_query
```

What will happen behind the scenes is that the Tendermint node `node0`
will send a `request_query` ABCI request to the ABCI app `abci0`
(in our case an AEA skill handler). The skill will reply 
with an `response_query` ABCI response,
containing the current state of the ABCI application.

The response to the HTTP request above is:
```
{
  "jsonrpc": "2.0",
  "id": -1,
  "result": {
    "response": {
      "code": 0,
      "log": "value: 0",
      "info": "",
      "index": "0",
      "key": null,
      "value": "AAAAAA==",
      "proofOps": {
        "ops": []
      },
      "height": "0",
      "codespace": ""
    }
  }
}
```

As you can see from the `log` field, the counter is initializes at `0`.
`value` contains the `base64` encoding of the bytes of the data,
representing the app state. 

You can verify that runnning the same query against the other
nodes will give you the same response, e.g.

```
curl http://localhost:26667/abci_query
```

## Transaction

To send a transaction and update the ABCI application state:

```
curl http://localhost:26657/broadcast_tx_commit\?tx\=0x01
```

where `0x01` is the new value for the distributed counter.

Once the request is received, the Tendermint node will 
first check that the transaction is indeed valid against
the current state of the application by sending
a `check_tx` request to the ABCI application.
If so, the transaction will be added to the mempool
of pending transactions. 

In our case, since the state before the transaction was `0x00`, 
and since `0x01` is a unitary increment of the counter,
the transaction is valid.

After the Tendermint network managed to reach a consensus,
the command above receives this HTTP response:

```
{
  "jsonrpc": "2.0",
  "id": -1,
  "result": {
    "check_tx": {
      "code": 0,
      "data": null,
      "log": "valid transaction.",
      "info": "OK: the next count is a unitary increment.",
      "gas_wanted": "0",
      "gas_used": "0",
      "events": [],
      "codespace": ""
    },
    "deliver_tx": {
      "code": 0,
      "data": null,
      "log": "",
      "info": "",
      "gas_wanted": "0",
      "gas_used": "0",
      "events": [],
      "codespace": ""
    },
    "hash": "4BF5122F344554C53BDE2EBB8CD2B7E3D1600AD631C385A5D7CCE23C7785459A",
    "height": "3"
  }
}
```

The `check_tx` part is the response of the ABCI app when the
transaction was received and checked,
and `deliver_tx` is the response of the ABCI app after the transaction was applied
to the state.
The `info` field of the `check_tx` response:
```
OK: the next count is a unitary increment.
```
describes
the reason why the transaction is considered valid by the ABCI application.

Note that we would have obtained the same result
by interacting with another available Tendermint node;
you can try by replacing the port `26657`
with one of `26667`, `26677` and `26687`.

If, say, we had sent the transaction `0x02` instead of the
only legal one `0x01`, we would have got the following response: 

```
{
  "jsonrpc": "2.0",
  "id": -1,
  "result": {
    "check_tx": {
      "code": 1,
      "data": null,
      "log": "invalid transaction.",
      "info": "ERROR: the next count must be a unitary increment.",
      "gas_wanted": "0",
      "gas_used": "0",
      "events": [],
      "codespace": ""
    },
    "deliver_tx": {
      "code": 0,
      "data": null,
      "log": "",
      "info": "",
      "gas_wanted": "0",
      "gas_used": "0",
      "events": [],
      "codespace": ""
    },
    "hash": "DBC1B4C900FFE48D575B5DA5C638040125F65DB0FE3E24494B76EA986457D986",
    "height": "0"
  }
```
The `info` field of the `check_tx` response:
```
ERROR: the next count must be a unitary increment.
```
describes  the reason why the transaction has been rejected.

Now, the query request
```
curl http://localhost:26667/abci_query
```

returns the updated counter value:
```
{
  "jsonrpc": "2.0",
  "id": -1,
  "result": {
    "response": {
      "code": 0,
      "log": "value: 1",
      "info": "",
      "index": "0",
      "key": null,
      "value": "AAAAAQ==",
      "proofOps": {
        "ops": []
      },
      "height": "0",
      "codespace": ""
    }
  }
}
```
