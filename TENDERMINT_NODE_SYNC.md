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
| `autonomy/deploy/generators/localhost/tendermint/tendermint.py` | Localhost dev deployment | Direct file I/O logging |
| `packages/valory/agents/register_reset/tests/helpers/slow_tendermint_server/tendermint.py` | Test fixture helper | Optional monitoring, conditional stdout piping |

Architectural differences (not accidental drift):
- **Monitoring is optional** via `start(start_monitoring=False)` — Group 1 always monitors
- **Subprocess piping is conditional** — only pipes stdout/stderr when monitoring is enabled
- **Logging uses direct file I/O** instead of Python's `logging` module with `RotatingFileHandler`
- **Method names differ**: `check_server_status()` vs `_monitor_tendermint_process()`, `write_line()` vs `log()`

## Safety fixes — All complete

All safety fixes are present in all 4 copies:

1. **`_stopping` race-condition guard** — `__init__`, `_stop_tm_process`, `_start_tm_process`
2. **`join(timeout=10)` on monitoring thread** — Prevents indefinite hang
3. **Close stdout before setting `_process = None`** — Unblocks monitoring thread's `readline()`
4. **Stop order: process-then-monitor** — Killing the process closes stdout, unblocking the thread
5. **EOF check in `readline()` loop** — Breaks out of monitoring loop when process exits
6. **Platform-specific process group** — `CREATE_NEW_PROCESS_GROUP` on Windows,
   `start_new_session=True` on POSIX (`start_new_session` is POSIX-only, does nothing on Windows)

## Related fix (connection.py only)

The `TcpServerChannel.disconnect()` in `connection.py` closes all active client
writers before calling `await _server.wait_closed()`. Required on Python 3.12+
where `wait_closed()` actually waits for handler tasks to finish (was a no-op before).
