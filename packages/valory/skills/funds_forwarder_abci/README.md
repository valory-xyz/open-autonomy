# Funds Forwarder ABCI

## Description

Transfers excess token balances from the service safe to the resolved service owner. Supports both native tokens and ERC20 tokens with per-token configurable thresholds. Designed to run after `identify_service_owner_abci`.

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `expected_service_owner_address` | `str` | Expected owner address. Transfers only proceed if resolved owner matches this value. |
| `funds_forwarder_token_config` | `dict` | Per-token transfer configuration. See below. |

### Token Config Format

```json
{
  "0xTokenAddress": {
    "retain_balance": 300000000000000000000,
    "min_transfer": 100000000000000000,
    "max_transfer": 100000000000000000
  }
}
```

| Field | Description |
|-------|-------------|
| `retain_balance` | Minimum balance to keep in the safe |
| `min_transfer` | Minimum excess required before a transfer is triggered. Optional, defaults to `0`. |
| `max_transfer` | Maximum amount to transfer per cycle |

Use `0x0000000000000000000000000000000000000000` as the token address for native tokens (e.g. xDAI).

## Safety Guards

1. **Expected owner enforcement** - Resolved owner must match `expected_service_owner_address`. Prevents funds going to an unexpected address.
2. **Zero address guard** - Rejects empty or zero-address owners.
3. **Empty config guard** - Skips forwarding when no token config is set.
4. **Minimum transfer threshold** - Only transfers when `balance >= retain_balance + min_transfer`, avoiding dust transactions.
5. **Startup validation** - Raises `ValueError` at agent startup if `min_transfer > max_transfer`.

## Behaviours

* `FundsForwarderBehaviour`

   Checks token balances, builds transfer transactions (single or multisend), and submits for consensus.

## Handlers

ABCIHandler, ContractApiHandler, HttpHandler, IpfsHandler, LedgerApiHandler, SigningHandler, TendermintHandler (standard ABCI skill handlers).
