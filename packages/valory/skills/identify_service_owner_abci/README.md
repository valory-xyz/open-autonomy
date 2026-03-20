# Identify Service Owner ABCI

## Description

Resolves the real service owner from the on-chain service registry, handling staking contract indirection. When a service is staked, `ServiceRegistry.ownerOf()` returns the staking contract address instead of the real owner. This skill detects that case and reads the original owner from `StakingContract.getServiceInfo()`.

The resolved owner is stored in `SynchronizedData.service_owner` for use by downstream skills.

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `on_chain_service_id` | `int` | On-chain service ID (inherited from `BaseParams`) |
| `service_registry_address` | `str` | Address of the ServiceRegistry contract |

## Safety Guards

1. **Safe registration check** - Verifies the agent's safe matches `ServiceRegistry.getAgentInstances()` before proceeding.
2. **Staking-aware resolution** - Detects staking contracts via `getServiceInfo()` call. Works regardless of staking state (active, inactive, evicted).
3. **Graceful degradation** - On any error (missing config, contract call failure), emits `Event.ERROR` and the FSM skips to the next skill without blocking.

## Behaviours

* `IdentifyServiceOwnerBehaviour`

   Queries the service registry, resolves the real owner, and submits a consensus payload with the result.

## Handlers

ABCIHandler, ContractApiHandler, HttpHandler, IpfsHandler, LedgerApiHandler, SigningHandler, TendermintHandler (standard ABCI skill handlers).
