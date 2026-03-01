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
- **Stop order is reversed**: monitor-then-process vs process-then-monitor

## Safety fixes missing from Group 2

The following fixes exist in Group 1 (connection.py) but are missing from Group 2.
These should be backported, adapted to each copy's architecture.

### 1. `_stopping` race-condition guard

**Risk:** Without this flag, concurrent calls to `_stop_tm_process()` (e.g. from
the monitoring thread's restart logic and a manual `stop()` call) can race.

**Group 1 implementation:**
```python
def _stop_tm_process(self) -> None:
    if self._process is None or self._stopping:
        return
    self._stopping = True
    # ... stop logic ...
    self._stopping = False
    self._process = None
```

**Action:** Add `self._stopping = False` to `__init__` and guard `_stop_tm_process()`.

### 2. `join(timeout=10)` on monitoring thread

**Risk:** Without a timeout, `_stop_monitoring_thread()` can hang indefinitely
if the monitoring thread is blocked on `readline()`.

**Group 1 implementation:**
```python
def _stop_monitoring_thread(self) -> None:
    if self._monitoring is not None:
        self._monitoring.stop()
        self._monitoring.join(timeout=10)
```

**Action:** Add `timeout=10` to all `self._monitoring.join()` calls.

### 3. Close stdout before setting `_process = None`

**Risk:** If stdout is not closed, the monitoring thread's `readline()` blocks
forever because the pipe is never closed from our end.

**Group 1 implementation:**
```python
# In _stop_tm_process(), before self._process = None:
if self._process is not None and self._process.stdout is not None:
    self._process.stdout.close()
```

**Action:** Add stdout close to `_stop_tm_process()` in both Group 2 files.
For the slow_tendermint_server copy, only relevant when monitoring is enabled
(i.e. when stdout is piped).

### 4. Stop order consideration

Group 2 stops in monitor-then-process order. Group 1 stops process-then-monitor.
Group 1's order is correct: killing the process closes stdout, which unblocks
the monitoring thread's `readline()`, allowing clean shutdown. Stopping the
monitor first leaves it blocked on `readline()` until the process is killed.

**Action:** Consider reversing stop order in Group 2 to match Group 1:
`_stop_tm_process()` then `_stop_monitoring_thread()`.
