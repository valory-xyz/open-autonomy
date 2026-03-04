# FSM Core Audit — Chainable Skill Architecture

**Date:** 2026-03-03
**Branch:** `fix/audit-round-2` (based on `fix/critical-audit-issues`)
**Scope:** The core FSM app pattern — rounds, behaviours, chaining, ABCI integration

---

## Critical

### F1. ~~Shared list references in `bg_apps_prioritized` break background app prioritization~~ **RESOLVED**
- **File:** `packages/valory/skills/abstract_round_abci/base.py:2542`
- **Issue:** `([],) * n_correct_types` creates `n` references to the **same list object**. Every `.append()` on any index appends to all indices. All background apps end up in every priority group.
- **Impact:** Background app prioritization is non-functional. In practice limited severity since compositions have at most 2 bg apps and the consumer returns early, but priority ordering is lost.
- **Resolution:** Replaced with `tuple([] for _ in range(n_correct_types))`. Added test.

---

## High

### F2. ~~Operator precedence bug unconditionally skips `PendingOffencesBehaviour`~~ **RESOLVED**
- **File:** `packages/valory/skills/abstract_round_abci/behaviours.py:324-332`
- **Issue:** Due to `and` binding tighter than `or`, `PendingOffencesBehaviour` is always skipped regardless of `use_slashing`.
- **Impact:** Pending offences checking is non-functional even when slashing is enabled.
- **Resolution:** Added parentheses to group the `or` condition under the `not params.use_slashing` guard. Added test.

---

## Medium

### F6. ~~Dead `ROUND_TIMEOUT` config in registration and reset-pause skills~~ **RESOLVED**
- **Files:** `packages/valory/skills/registration_abci/rounds.py`, `packages/valory/skills/reset_pause_abci/rounds.py`, `packages/valory/skills/reset_pause_abci/models.py`
- **Issue:** `Event.ROUND_TIMEOUT` is in `event_to_timeout` but absent from any round's `transition_function`. The framework only schedules timeouts for events present in transitions (`base.py:2641`), so these entries are never used. For registration, a timeout makes no sense — agents wait indefinitely for peers to join. For reset_pause, timeout handling is already covered by `RESET_AND_PAUSE_TIMEOUT` which is properly wired to `FinishedResetAndPauseErrorRound`.
- **Resolution:** Removed dead `ROUND_TIMEOUT` entries from `event_to_timeout` in both skills and the corresponding dead config update in `reset_pause_abci/models.py`. Kept `ROUND_TIMEOUT` enum members for downstream compatibility.

### F7. ~~Unused `_next_behaviour_cls` instance variable~~ **RESOLVED**
- **File:** `packages/valory/skills/abstract_round_abci/behaviours.py:269-272`
- **Issue:** Initialized in `__init__` but never read or written anywhere in the codebase. The comment described deferred behaviour transitions ("remembers the actual next transition when we cannot preemptively interrupt the current behaviour"), but the framework uses immediate interruption instead — when a round changes, the current behaviour is immediately cleaned up and replaced (`_process_current_round`). Deferred transitions would add complexity with no benefit since behaviours are generator-based and interruption is clean.
- **Resolution:** Removed the unused variable and its comment.

---

## Investigated and Confirmed Not Bugs

These were flagged during the audit but confirmed as correct after manual verification:

### Slashing `update()` result not captured
- **File:** `packages/valory/skills/slashing_abci/rounds.py:164`
- **Analysis:** `BaseSynchronizedData.update()` calls `self.db.update()` which mutates the underlying `AbciAppDB` **in-place** before returning a new wrapper. The database is updated regardless of whether the return value is captured. Not a bug.

### `CollectNonEmptyUntilThresholdRound` returning wrong state
- **File:** `packages/valory/skills/abstract_round_abci/base.py:1960-1962`
- **Analysis:** `done_event` correctly returns the new `synchronized_data`; `none_event` correctly returns the old `self.synchronized_data`. Both share the same mutated DB, but the distinction matters for `synchronized_data_class` propagation. Correct as written.

### `_is_healthy = False` after successful Tendermint reset
- **File:** `packages/valory/skills/abstract_round_abci/behaviour_utils.py:2025`
- **Analysis:** `_end_reset()` (line 1883-1886) already set `_is_healthy = True` and `_check_started = None` earlier in the same call. Setting `_is_healthy = False` at the end resets the per-cycle state so the next call to `_start_reset()` can begin a new health check cycle. The method returns `True` to signal success to the caller. Intentional design.

### `check_tx` vs `deliver_tx` offence tracking asymmetry
- **File:** `packages/valory/skills/abstract_round_abci/handlers.py:156-269`
- **Analysis:** By design. `check_tx` runs during mempool admission (non-deterministic, per-node). `deliver_tx` runs during block execution (deterministic, consensus). Offence tracking must be deterministic to maintain consensus, so it correctly belongs only in `deliver_tx`.

### Unhandled `ROUND_TIMEOUT` transitions
- **Files:** `registration_abci/rounds.py`, `reset_pause_abci/rounds.py`
- **Analysis:** The framework only schedules timeout events that appear in a round's `transition_function` (see `base.py:2639`). Events in `event_to_timeout` but not in any transition are dead config — they never fire. Reclassified from "High" to "Medium" (F6) as a code quality issue.

---
---

# Test Infrastructure Audit

**Scope:** Test base classes, helpers, fixtures, and Docker infrastructure for FSM apps

---

## Critical

### T1. ~~`teardown_method` calls `self.loop.start()` instead of `self.loop.stop()`~~ **RESOLVED**
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/helpers/async_utils.py:174`
- **Issue:** `BaseThreadedAsyncLoop.teardown_method()` calls `self.loop.start()` — an exact duplicate of `setup_method()`. The async event loop thread is never stopped.
- **Impact:** Thread and event loop leak after every test method. Leads to port conflicts, resource exhaustion, and flaky tests in CI.
- **Resolution:** Changed `self.loop.start()` to `self.loop.stop()`. Added test.

### T2. ~~Fragile set mutation pattern in ACN node `wait()`~~ **RESOLVED**
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/docker/acn_node.py:102-109`
- **Issue:** `to_be_connected.remove(uri)` is called inside `for uri in to_be_connected:`. The `break` on the next line prevents a `RuntimeError` in practice, but the pattern is fragile and the `break` also limits throughput to one URI check per outer loop iteration.
- **Resolution:** Iterate over `list(to_be_connected)`, use `discard()`, remove the `break` so all ready URIs are checked per pass. Added test.

---

## High

### T3. ~~Socket resource leak in ACN node `wait()` exception path~~ **RESOLVED**
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/docker/acn_node.py:104-116`
- **Issue:** `sock = socket.socket(...)` is created at line 104, but if an exception occurs before `sock.close()` at line 107, the socket leaks. The broad `except Exception` on line 112 catches and swallows the error.
- **Impact:** File descriptor exhaustion during retry loops.
- **Resolution:** Replaced with `with socket.socket(...) as sock:` context manager. Added test.

### T6. ~~Agent process `terminate()` without `wait()` before cleanup~~ **RESOLVED**
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/base_test_classes/agents.py:489-490`
- **Issue:** `self.processes[i].terminate()` is called immediately followed by `self.processes.pop(i)` without waiting for the process to exit. The comment on line 486 says "don't pop before termination" but doesn't address waiting.
- **Impact:** Orphaned processes, race conditions on process state, and potential port conflicts when restarting agents.
- **Resolution:** Added `self.processes[i].wait()` between `terminate()` and `pop()`, matching the parent class `terminate_agents()` pattern.

---

## Medium

### T8. ~~Integration test event loop thread joined without timeout safety~~ **RESOLVED**
- **File:** `packages/valory/skills/abstract_round_abci/test_tools/integration.py:136-137`
- **Issue:** `cls.thread_loop.join()` is called without a timeout. If the event loop thread hangs, the test suite blocks indefinitely.
- **Impact:** CI hangs on integration test failures.
- **Resolution:** Added `timeout=30.0` to `cls.thread_loop.join()`.

---

## Investigated and Confirmed Not Issues

### Shallow copy of `_MetaPayload.registry`
- **File:** `packages/valory/skills/abstract_round_abci/test_tools/base.py:91`
- **Analysis:** The registry values are `Type["BaseTxPayload"]` — immutable class references. Shallow copy is sufficient since there are no mutable nested containers. The dict itself is replaced (not mutated) via `_MetaPayload.registry = {}`, so the saved copy remains intact.

### Process dict modified during iteration in agent termination
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/base_test_classes/agents.py:487-490`
- **Analysis:** The loop iterates `range(self.n_terminal)` (integers), not `self.processes.keys()`. Popping `self.processes[0]` doesn't affect iteration over the pre-computed range. Not a dict-during-iteration bug.

### `end_round()` test helper directly manipulates round state (T4)
- **File:** `packages/valory/skills/abstract_round_abci/test_tools/base.py:394-401`
- **Analysis:** Intentional separation of concerns. Behaviour unit tests need to simulate "the round ended with event X" without running the full ABCI consensus flow (multi-agent payload collection). The helper still uses the real `transition_function` to determine the next round class, so FSM wiring is validated. Round transition internals (timeout scheduling, height tracking) are tested separately in round tests.

### `mock_contract_api_request()` uses hardcoded `contract_id` in response (T5)
- **File:** `packages/valory/skills/abstract_round_abci/test_tools/base.py:270`
- **Analysis:** Dialogue matching in the AEA framework routes on `dialogue_reference` + `target`/`message_id`, not on `contract_id`. The request validation (line 252) correctly checks the real `contract_id` — confirming the behaviour sent the request to the right contract. The response `contract_id` is just a required protocol field with no effect on routing or handler logic.

### Dialogue reference uses arbitrary `"stub"` string (T10)
- **File:** `packages/valory/skills/abstract_round_abci/test_tools/base.py:218, 263, 300, 326`
- **Analysis:** Standard AEA test pattern. `(ref[0], "stub")` provides the initiator's reference for dialogue matching plus a valid placeholder for the responder's reference. The dialogue protocol matches on the tuple; `"stub"` is a legitimate value for test response messages.

### `mock_a2a_transaction()` uses stub signature and empty body (T7)
- **File:** `packages/valory/skills/abstract_round_abci/test_tools/base.py:336-386`
- **Analysis:** Same pattern as T4/T5. The helper tests that behaviours handle the signing → HTTP submit → HTTP confirm flow correctly and transition state. Validating real transaction serialization and signature verification is the concern of integration/e2e tests, not behaviour unit tests.

### `ganache_scope_function` fixture kept for downstream compatibility (T9)
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/fixture_helpers.py:241-256`
- **Analysis:** Marked `# TODO: remove as not used` by original authors, but `aea-test-autonomy` is a public plugin used by downstream projects. Removing it could break consumers who import the fixture. Safe to leave as-is.

### `sys.getsizeof()` used for transaction size validation (F3)
- **File:** `packages/valory/skills/abstract_round_abci/base.py:246, 269`
- **Analysis:** `sys.getsizeof(encoded_data)` measures the Python object's in-memory size, which is slightly larger than the raw byte length (~33 bytes overhead). The check guards against exceeding the ABCI connection's `MAX_READ_IN_BYTES` (1 MiB) read buffer. The overhead is constant and negligible vs the 1 MiB limit, deterministic across identical Docker deployments, and provides a conservative bound. Not a bug.

### `commit()` handler re-raises `AddBlockError` (F4)
- **File:** `packages/valory/skills/abstract_round_abci/handlers.py:295-297`
- **Analysis:** Intentional fail-fast design. An `AddBlockError` during commit means the ABCI app state is inconsistent. Returning an error response would let Tendermint continue with corrupted state. Crashing forces the agent to restart and resync from a known-good state. The AEA framework catches unhandled handler exceptions at a higher level.

### Missing `IndexError` guard in `AbciAppDB.sync()` (F5)
- **File:** `packages/valory/skills/abstract_round_abci/base.py:790`
- **Analysis:** `tuple(db_data.values())[0]` would raise `IndexError` if `db_data` is empty. However, `sync()` receives serialized state from the framework's own `AbciAppDB.serialize()`, which always includes at least index 0 (the initial round's data). An empty `db_data` would require a fundamentally corrupted sync payload that bypassed JSON structure validation. The `IndexError` would still surface the problem (just with a less descriptive message than `ABCIAppInternalError`). Defensive improvement at best, not a functional bug.

### Payload registry not thread-safe (F8)
- **File:** `packages/valory/skills/abstract_round_abci/base.py:171-186`
- **Analysis:** `_MetaPayload.registry` is a class-level dict mutated during metaclass `__new__`, which runs at class definition time (module import). Class creation is single-threaded in Python — it happens sequentially during import. The GIL also protects simple dict writes. No scenario exists where two metaclass `__new__` calls race in this codebase.
