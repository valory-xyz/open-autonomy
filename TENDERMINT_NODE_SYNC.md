# TendermintNode Copies — Sync Status & Safety Backlog

## Overview

`TendermintNode` (and `TendermintParams`, `StoppableThread`) exist in 4 locations.
Two are enforced-identical; two are intentionally different.

## Group 1 — Must be identical

Enforced by `test_deployment_class_identical` (character-for-character comparison).

| File | Purpose |
|------|---------|
| `packages/valory/connections/abci/connection.py` | Production runtime (ABCI connection) |
| `deployments/Dockerfiles/tendermint/tendermint.py` | Docker container (literal copy, embedded in Alpine) |

These are currently in sync. Any change to one must be mirrored in the other,
and the test will catch drift.

## Group 2 — Intentionally different

| File | Purpose | Key differences |
|------|---------|-----------------|
| `autonomy/deploy/generators/localhost/tendermint/tendermint.py` | Localhost dev deployment | Direct file I/O logging, optional monitoring param on `start()` |
| `packages/valory/agents/register_reset/tests/helpers/slow_tendermint_server/tendermint.py` | Test fixture helper | Optional monitoring, conditional stdout piping, simplified logging |

Architectural differences (not accidental drift):
- **Monitoring is optional** via `start(start_monitoring=False)` — Group 1 always monitors
- **Subprocess piping is conditional** — only pipes stdout/stderr when monitoring is enabled
- **Logging uses direct file I/O** instead of Python's `logging` module with `RotatingFileHandler`
- **Method names differ**: `check_server_status()` vs `_monitor_tendermint_process()`, `write_line()` vs `log()`

## Safety fixes — All backported

All safety fixes from Group 1 have been backported to Group 2:

1. **`_stopping` race-condition guard** — Prevents concurrent `_stop_tm_process()` calls from racing.
2. **`join(timeout=10)` on monitoring thread** — Prevents indefinite hang if thread is blocked.
3. **Close stdout before setting `_process = None`** — Unblocks monitoring thread's `readline()`.
4. **Stop order: process-then-monitor** — Killing the process closes stdout, which unblocks the monitoring thread for clean shutdown.
5. **EOF check in `readline()` loop** — Breaks out of monitoring loop when process exits.
