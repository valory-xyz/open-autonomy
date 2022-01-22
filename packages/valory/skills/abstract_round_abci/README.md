# Abstract round abci

## Description

This module contains an abstract round ABCI skill template for an AEA.

## Behaviours

* `AbstractRoundBehaviour`

   This behaviour implements an abstract round behaviour.

* `_MetaRoundBehaviour`

   A metaclass that validates AbstractRoundBehaviour's attributes.


## Handlers

* `ABCIRoundHandler`

   ABCI handler.

* `AbstractResponseHandler`

   The concrete classes must set the `allowed_response_performatives`
    class attribute to the (frozen)set of performative the developer
    wants the handler to handle.

* `ContractApiHandler`

   Implement the contract api handler.

* `HttpHandler`

   The HTTP response handler.

* `LedgerApiHandler`

   Implement the ledger handler.

* `SigningHandler`

   Implement the transaction handler.


