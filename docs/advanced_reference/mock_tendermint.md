# Mock Tendermint for Single-Agent Services

When running an autonomous service with a single agent, Tendermint consensus is pure overhead — the agent synchronises state only with itself. The **Mock Tendermint** channel replaces the real Tendermint node entirely, simulating the ABCI block lifecycle and RPC interface with zero external dependencies.

## When to Use

- **Single-agent deployments** — eliminates the Tendermint process, reducing resource usage and startup time.
- **Testing** — run e2e tests without Docker containers for Tendermint.
- **Local development** — faster iteration cycle with no Tendermint node to manage.

!!! warning
    The mock is designed exclusively for single-agent services. Multi-agent services require real Tendermint for consensus.

## Configuration

Enable the mock in your ABCI connection configuration:

```yaml
# In connection overrides or aea-config.yaml
config:
  use_mock: true
  use_tendermint: false
```

The mock RPC server listens on the address specified by `tendermint_config.rpc_laddr` (default: `tcp://127.0.0.1:26657`). Ensure `tendermint_url` and `tendermint_com_url` in the skill params point to the same address.

## What It Simulates

The mock covers both Tendermint interfaces:

**ABCI (Channel 1)** — the full block lifecycle:

- `RequestInfo` / `ResponseInfo` — startup handshake
- `RequestInitChain` / `ResponseInitChain` — genesis initialisation
- `RequestBeginBlock` / `RequestEndBlock` / `RequestCommit` — block production loop
- `RequestDeliverTx` / `ResponseDeliverTx` — transaction delivery

**RPC HTTP (Channel 2)** — endpoints the behaviours call:

| Endpoint | Purpose |
|---|---|
| `GET /broadcast_tx_sync?tx=0x...` | Submit a transaction to the mempool |
| `GET /tx?hash=0x...` | Poll transaction delivery status |
| `GET /status` | Sync check (returns current block height) |
| `GET /net_info` | Peer information (returns 0 peers) |
| `GET /hard_reset` | Reset chain state (height, mempool, delivered txs) |
| `GET /gentle_reset` | Same as hard reset |

## Behaviour

- **Tx-triggered blocks**: the mock produces a block immediately when a transaction arrives, rather than waiting for a fixed block interval. This eliminates race conditions between transaction submission and delivery polling.
- **Block interval**: when idle (no pending transactions), the mock produces empty blocks at a configurable interval (default: 1 second).
- **Reset**: `/hard_reset` and `/gentle_reset` reset the mock's internal state (height, mempool, delivered transactions), matching real Tendermint's behaviour after `unsafe-reset-all`.

## Known Limitations

- **`CheckTx` is skipped**: `broadcast_tx_sync` always returns `code: 0` without sending a `RequestCheckTx` to the handler. Skills that rely on `CheckTx`-level rejection are not faithfully tested.
- **`/tx?hash=` returns hard-coded `tx_result`**: the response always reports `code: 0` regardless of the handler's actual `ResponseDeliverTx` fields.

## Testing with `UseMockTendermint`

The `UseMockTendermint` mixin makes it trivial to add a mock variant of any single-agent e2e test:

```python
from aea_test_autonomy.fixture_helpers import UseMockTendermint

# Existing test with real Tendermint:
class TestMySkill(BaseTestEnd2EndExecution):
    agent_package = "valory/my_agent:0.1.0"
    skill_package = "valory/my_skill:0.1.0"
    ...

# Mock variant — inherits everything, replaces TM:
class TestMySkillMock(UseMockTendermint, TestMySkill):
    """Same test, mock Tendermint."""
```

The mixin overrides the Docker Tendermint fixture methods with local port allocation, so no Docker containers are needed for the Tendermint dependency.
