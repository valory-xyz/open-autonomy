# FSM Audit Report — Round 3

**Scope:** All 11 FSM skills under `packages/valory/skills/`
**Date:** 2026-03-04
**Branch:** `fix/audit-round-3` (after applying fixes from rounds 1–2)

## CLI Tool Results

| Tool | Result |
|------|--------|
| `autonomy analyse fsm-specs` | PASS |
| `autonomy analyse handlers` | PASS (error in `counter_client` — non-FSM, out of scope) |
| `autonomy analyse dialogues` | PASS (error in `counter_client` — non-FSM, out of scope) |
| `autonomy analyse docstrings` | PASS — no updates needed |

## Critical Findings

No findings.

## High Findings

No findings.

## Medium Findings

### ~~M2: Unused Event `ROUND_TIMEOUT` — `registration_abci`~~ — RECLASSIFIED: not-issue
- **File:** `packages/valory/skills/registration_abci/rounds.py:44`
- **Reclassification:** `registration_abci` is a library skill. `ROUND_TIMEOUT = "round_timeout"` is a framework convention for extensibility — downstream services composing this skill may add timeout transitions. Not dead code.

### ~~M2: Unused Event `ROUND_TIMEOUT` — `reset_pause_abci`~~ — RECLASSIFIED: not-issue
- **File:** `packages/valory/skills/reset_pause_abci/rounds.py:40`
- **Reclassification:** Same as above — library skill convention.

### T5: Missing `NO_MAJORITY` test — `reset_pause_abci`
- **File:** `packages/valory/skills/reset_pause_abci/tests/test_rounds.py`
- **Issue:** Only `Event.DONE` tested, no explicit `NO_MAJORITY` event test coverage

## Low Findings

### L3: Stale docstring — `slashing_abci` `StatusResetRound`
- **File:** `packages/valory/skills/slashing_abci/rounds.py:188`
- **Issue:** Docstring says "slashing check background round" but this is the status reset round

### L3: Stale docstring — `test_abci` `DummyRound`
- **File:** `packages/valory/skills/test_abci/rounds.py:44`
- **Issue:** Docstring says "This class represents the registration round" — stale copy-paste

### L3: Misleading test class name — `register_reset_recovery_abci`
- **File:** `packages/valory/skills/register_reset_recovery_abci/tests/test_rounds.py:47`
- **Issue:** `TestTerminationRound` class actually tests `RoundCountRound`

## Test/Scaffold Skills

| Skill | Notes |
|-------|-------|
| `test_abci` | Dead timeouts intentional (testing SharedState.setup()). Stale DummyRound docstring (L3). |
| `test_solana_tx_abci` | Dead `Event.ERROR` timeout intentional. `synchronized_data_class = BaseSynchronizedData` while `end_block()` uses `SynchronizedData` — benign since `update()` explicitly passes the correct class. |
| `test_ipfs_abci` | Clean |

## Skills With Clean Audits

| Skill | Status |
|-------|--------|
| `transaction_settlement_abci` | All checks PASS |
| `squads_transaction_settlement_abci` | All checks PASS (after payload_class fix) |
| `slashing_abci` | All checks PASS (after DB key fix). Minor docstring issue (L3). |
| `offend_abci` | All checks PASS |
| `termination_abci` | All checks PASS |
| `register_reset_recovery_abci` | All checks PASS. Minor test naming issue (L3). |

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 3 |
| Reclassified (not-issue) | 2 |

## Notes
- All previous Critical/High findings (payload_class mismatch, DB key mismatch, stale docstrings) have been fixed on this branch.
- `counter` and `counter_client` are non-FSM skills, excluded from audit.
- `test_*` skills reported under separate section per false-positive guidance.
- C1 (shared mutable references) grep across all skills: no matches found.
- `ROUND_TIMEOUT` enum members in library skills (`registration_abci`, `reset_pause_abci`) are a framework convention for extensibility, not dead code. Reclassified as not-issues.
