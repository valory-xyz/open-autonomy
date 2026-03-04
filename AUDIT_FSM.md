# FSM Core Audit — Chainable Skill Architecture

**Date:** 2026-03-03
**Branch:** `fix/audit-round-2` (based on `fix/critical-audit-issues`)
**Scope:** The core FSM app pattern — rounds, behaviours, chaining, ABCI integration

---

## Critical

### F1. Shared list references in `bg_apps_prioritized` break background app prioritization
- **File:** `packages/valory/skills/abstract_round_abci/base.py:2542`
- **Issue:** `([],) * n_correct_types` creates `n` references to the **same list object**. Every `.append()` on any index appends to all indices. All background apps end up in every priority group.
- **Impact:** Background app prioritization is completely non-functional. Execution order of background rounds is undefined.
- **Fix:** Replace with `tuple([] for _ in range(n_correct_types))`.

---

## High

### F2. Operator precedence bug unconditionally skips `PendingOffencesBehaviour`
- **File:** `packages/valory/skills/abstract_round_abci/behaviours.py:324-332`
- **Issue:** The condition:
  ```python
  if (
      not params.use_termination
      and background_cls.auto_behaviour_id() == TERMINATION_BACKGROUND_BEHAVIOUR_ID
  ) or (
      not params.use_slashing
      and background_cls.auto_behaviour_id() == SLASHING_BACKGROUND_BEHAVIOUR_ID
      or background_cls == PendingOffencesBehaviour  # <-- outside the `and`
  ):
  ```
  Due to `and` binding tighter than `or`, this evaluates as:
  ```
  (not use_termination AND id == TERMINATION_ID)
  OR (not use_slashing AND id == SLASHING_ID)
  OR (cls == PendingOffencesBehaviour)          # always true when cls matches
  ```
  `PendingOffencesBehaviour` is **always** skipped regardless of `use_slashing`.
- **Impact:** Pending offences checking is non-functional even when slashing is enabled.
- **Fix:** Add parentheses:
  ```python
  ) or (
      not params.use_slashing
      and (
          background_cls.auto_behaviour_id() == SLASHING_BACKGROUND_BEHAVIOUR_ID
          or background_cls == PendingOffencesBehaviour
      )
  ):
  ```

### F3. `sys.getsizeof()` used for transaction size validation instead of `len()`
- **File:** `packages/valory/skills/abstract_round_abci/base.py:246, 269`
- **Issue:** `sys.getsizeof(encoded_data)` returns the Python object's memory footprint (data + ~49 bytes overhead), not the byte length of the encoded data. While deterministic on CPython, it is semantically incorrect and could differ across Python implementations.
- **Impact:** Size limit is effectively ~49 bytes lower than intended. Heterogeneous deployments (different Python implementations) could disagree on validity, breaking consensus.
- **Fix:** Use `len(encoded_data)`.

### F4. `commit()` handler re-raises exception instead of returning ABCI response
- **File:** `packages/valory/skills/abstract_round_abci/handlers.py:295-297`
- **Issue:** `AddBlockError` is caught, logged, then re-raised. Tendermint expects an ABCI response for every request. An unhandled exception breaks the ABCI protocol state machine.
- **Impact:** Commit failures crash the ABCI connection instead of returning an error response. Tendermint hangs waiting for a reply.
- **Assessment:** Needs investigation into what the correct ABCI error response should be. The current re-raise may be intentional as a fail-fast mechanism (forcing the agent to restart), but it violates the ABCI contract.

---

## Medium

### F5. Missing `IndexError` guard in `AbciAppDB.sync()`
- **File:** `packages/valory/skills/abstract_round_abci/base.py:790`
- **Issue:** `tuple(db_data.values())[0]` raises `IndexError` if `db_data` is an empty dict. Other validation errors in this method raise `ABCIAppInternalError`; this one would surface as an unexpected `IndexError`.
- **Impact:** Inconsistent error handling during state synchronization with malformed data.

### F6. Dead `ROUND_TIMEOUT` config in registration and reset-pause skills
- **Files:** `packages/valory/skills/registration_abci/rounds.py:169`, `packages/valory/skills/reset_pause_abci/rounds.py:109`
- **Issue:** `Event.ROUND_TIMEOUT` is declared in `event_to_timeout` but no round's `transition_function` includes it. The framework only schedules timeouts for events present in a round's transitions (see `base.py:2639-2641`), so this config is silently ignored.
- **Impact:** No runtime effect, but misleading — suggests timeout handling exists when it doesn't.

### F7. Unused `_next_behaviour_cls` instance variable
- **File:** `packages/valory/skills/abstract_round_abci/behaviours.py:272`
- **Issue:** Initialized in `__init__` but never read or written anywhere in the codebase. Likely a remnant of planned deferred behaviour transitions.
- **Impact:** Dead code.

---

## Low

### F8. Payload registry not thread-safe
- **File:** `packages/valory/skills/abstract_round_abci/base.py:171-186`
- **Issue:** `_MetaPayload.registry` is a class-level dict mutated during metaclass `__new__`. Safe under CPython's GIL for simple attribute writes, but not formally thread-safe.
- **Impact:** Theoretical only — class creation is single-threaded in practice.

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

### T7. `mock_a2a_transaction()` uses stub signature and empty body
- **File:** `packages/valory/skills/abstract_round_abci/test_tools/base.py:336-386`
- **Issue:** Transaction mock uses `body="stub_signature"` and empty transaction body `b""`. These don't match real transaction formats, so tests don't validate serialization/deserialization or signature verification.
- **Impact:** Transaction submission bugs may not be caught by unit tests.

### T8. Integration test event loop thread joined without timeout safety
- **File:** `packages/valory/skills/abstract_round_abci/test_tools/integration.py:136-137`
- **Issue:** `cls.thread_loop.join()` is called without a timeout. If the event loop thread hangs, the test suite blocks indefinitely.
- **Impact:** CI hangs on integration test failures.

### T9. `ganache_scope_function` fixture is dead code
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/fixture_helpers.py:241-256`
- **Issue:** Marked with `# TODO: remove as not used`. Dead code that creates Ganache containers unnecessarily if accidentally referenced.
- **Impact:** Code quality; maintenance burden.

---

## Low

### T10. Dialogue reference uses arbitrary `"stub"` string
- **File:** `packages/valory/skills/abstract_round_abci/test_tools/base.py:218, 263, 300, 326`
- **Issue:** Mock response messages use `dialogue_reference=(ref[0], "stub")`. While this works for dialogue matching, it doesn't validate that real dialogue references follow protocol conventions.
- **Impact:** Minor — dialogue matching works by reference tuple, and "stub" is valid for test responses.

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
