# FSM Audit Report

**Scope:** `packages/valory/skills/registration_abci`
**Date:** 2026-03-04

## CLI Tool Results

| Tool | Result |
|------|--------|
| `autonomy analyse fsm-specs` | PASS |
| `autonomy analyse handlers` | PASS (error is in `counter_client`, not in scope) |
| `autonomy analyse dialogues` | PASS (error is in `counter_client`, not in scope) |
| `autonomy analyse docstrings` | FAIL — docstring for `registration_abci/rounds.py` needs updating (stale timeout reference) |

## Critical Findings

### C4: Dead Timeout — `Event.ROUND_TIMEOUT`
- **File:** `packages/valory/skills/registration_abci/rounds.py:44`
- **Issue:** `Event.ROUND_TIMEOUT` is defined in the enum but never appears in any round's `transition_function` keys. The `event_to_timeout` is empty (`{}`), yet the class docstring claims `round timeout: 30.0`. This timeout is never scheduled.
- **Code:**
  ```python
  class Event(Enum):
      DONE = "done"
      ROUND_TIMEOUT = "round_timeout"  # Dead — not in any transition
      NO_MAJORITY = "no_majority"
  ```
- **Fix:** Remove `ROUND_TIMEOUT` from the enum and update the docstring (or wire it into the transition function if a timeout is desired).

## High Findings

No findings.

## Medium Findings

### L3: Stale Docstring — "price estimation demo"
- **File:** `packages/valory/skills/registration_abci/rounds.py:41`
- **Issue:** Copy-pasted docstring references wrong skill.
- **Code:**
  ```python
  class Event(Enum):
      """Event enumeration for the price estimation demo."""
  ```
- **Fix:**
  ```python
  class Event(Enum):
      """Event enumeration for agent registration."""
  ```

### L3: Docstring Grammar — "This rounds waits"
- **File:** `packages/valory/skills/registration_abci/rounds.py:94`
- **Issue:** Subject-verb agreement error.
- **Code:**
  ```python
  """This rounds waits until the threshold..."""
  ```
- **Fix:** `"This round waits until the threshold..."`

## Low Findings

No findings.

## Test Findings

All test checks (T1-T6) passed:
- No `@classmethod @pytest.fixture` anti-pattern
- Correct base test classes used (`BaseCollectSameUntilAllRoundTest`, `BaseCollectSameUntilThresholdRoundTest`)
- All required attributes set
- `mock_a2a_transaction()` called where needed
- All round events have test coverage (DONE, NO_MAJORITY)
- No registry corruption risks

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1     |
| High     | 0     |
| Medium   | 2     |
| Low      | 0     |
| Test     | 0     |

## Notes
- The mutable class-level dicts in `RegistrationStartupBehaviour` (`local_tendermint_params = {}`, `updated_genesis_data = {}`) look suspicious but are reset explicitly in the behaviour's `async_act()` flow before use, so they are not flagged as a bug — however they are worth monitoring.
- Copyright headers on some test files are stale (fixable via `tox -e fix-copyright`).
- The `handlers`/`dialogues` CLI errors are in `counter_client`, outside audit scope.
