# FSM Audit Report — Full Repository (Rounds 1–4)

**Scope:** All FSM skills in `packages/valory/skills/`
**Date:** 2026-03-04
**Branch:** `fix/audit-round-3`

## CLI Tool Results

| Tool | Result |
|------|--------|
| `autonomy analyse fsm-specs` | PASS |
| `autonomy analyse handlers` | PASS (error in `counter_client` — non-FSM, out of scope) |
| `autonomy analyse dialogues` | PASS (error in `counter_client` — non-FSM, out of scope) |
| `autonomy analyse docstrings` | PASS |

---

## All Findings (cumulative across rounds 1–4)

### Critical — FIXED

#### C4: Dead Timeout — `registration_abci` `Event.ROUND_TIMEOUT`
- **File:** `packages/valory/skills/registration_abci/rounds.py:44`
- **Issue:** `Event.ROUND_TIMEOUT` in enum but never in `transition_function` or `event_to_timeout`. Docstring falsely claimed `round timeout: 30.0`.
- **Status:** FIXED on `fix/audit-round-2`. ROUND_TIMEOUT kept as library skill convention; docstring corrected.

### High — FIXED

#### M1→Critical: Wrong `payload_class` — `squads_transaction_settlement_abci` `ExecuteTxRound`
- **File:** `packages/valory/skills/squads_transaction_settlement_abci/rounds.py:195`
- **Issue:** `payload_class = CreateTxPayload` but `keeper_payload` type hint is `ExecuteTxPayload` and behaviour sends `ExecuteTxPayload`.
- **Status:** FIXED on `fix/audit-round-3`. Changed to `payload_class = ExecuteTxPayload`.

#### M5: DB key mismatch — `slashing_abci` `participant_to_offence_reset`
- **File:** `packages/valory/skills/slashing_abci/rounds.py:105`
- **Issue:** Property read from `"participant_to_randomness"` instead of `"participant_to_offence_reset"`. Copy-paste error.
- **Status:** FIXED on `fix/audit-round-3`. Changed to `self.db.get_strict("participant_to_offence_reset")`.

#### M5: DB key mismatch — `transaction_settlement_abci` `participant_to_late_messages`
- **File:** `packages/valory/skills/transaction_settlement_abci/rounds.py:246`
- **Issue:** Property read from `"participant_to_late_message"` (singular) but `collection_key` resolves to `"participant_to_late_messages"` (plural). Latent bug — property was never called at runtime (`# pragma: no cover`).
- **Status:** FIXED on `fix/audit-round-3`. Changed to `self.db.get_strict("participant_to_late_messages")`.

### Medium — FIXED

#### L3: Stale docstrings — `registration_abci`
- **Issue:** "price estimation demo" and "This rounds waits" copy-paste errors.
- **Status:** FIXED on `fix/audit-round-3`.

#### L3: Stale docstring — `slashing_abci` `StatusResetRound`
- **Issue:** Docstring said "slashing check background round" instead of "status reset round".
- **Status:** FIXED on `fix/audit-round-3`.

#### L3: Stale docstring — `test_abci` `DummyRound`
- **Issue:** Docstring said "This class represents the registration round" — stale copy-paste.
- **Status:** FIXED on `fix/audit-round-3`.

#### L3: Misleading test class name — `register_reset_recovery_abci`
- **Issue:** `TestTerminationRound` class actually tests `RoundCountRound`.
- **Status:** FIXED on `fix/audit-round-3`. Renamed to `TestRoundCountRound`.

#### T5: Missing `NO_MAJORITY` test — `reset_pause_abci`
- **Issue:** Only `Event.DONE` tested.
- **Status:** FIXED on `fix/audit-round-3`. Added `test_no_majority_event()`.

### Reclassified as not-issue

| Finding | Reason |
|---------|--------|
| C4: Dead timeouts in `test_abci` | Test/scaffold skill — intentional test fixtures |
| C4: Dead timeout `Event.ERROR` in `test_solana_tx_abci` | Test/scaffold skill — intentional test fixture |
| T5: Incomplete event testing in `test_abci` | Test/scaffold skill — no transitions to test for dead events |
| M2: Unused `ROUND_TIMEOUT` in `registration_abci` | Library skill convention for extensibility |
| M2: Unused `ROUND_TIMEOUT` in `reset_pause_abci` | Library skill convention for extensibility |

---

## Skills With Clean Audits

| Skill | Status |
|-------|--------|
| `registration_abci` | All checks PASS (after fixes) |
| `reset_pause_abci` | All checks PASS (after fixes) |
| `offend_abci` | All checks PASS |
| `slashing_abci` | All checks PASS (after fixes) |
| `squads_transaction_settlement_abci` | All checks PASS (after fixes) |
| `transaction_settlement_abci` | All checks PASS (after fix) |
| `termination_abci` | All checks PASS |
| `register_reset_recovery_abci` | All checks PASS (after fixes) |

## Test/Scaffold Skills

| Skill | Notes |
|-------|-------|
| `test_abci` | All checks PASS. Dead timeouts are intentional test fixtures. |
| `test_solana_tx_abci` | All checks PASS. Dead `Event.ERROR` is intentional. |
| `test_ipfs_abci` | All checks PASS |

## Composition Chain Checks (H2) — All PASS

| Composition | Status |
|-------------|--------|
| `register_reset_abci` | PASS |
| `register_termination_abci` | PASS (reset loop is intentional periodic pattern) |
| `offend_slash_abci` | PASS (reset loop is intentional periodic pattern) |
| `slashing_abci` | PASS |
| `register_reset_recovery_abci` | PASS |
| `test_solana_tx_abci` | PASS |

---

## Summary

| Severity | Found | Fixed | Reclassified |
|----------|-------|-------|--------------|
| Critical | 1 | 1 | 2 |
| High | 3 | 3 | 0 |
| Medium | 5 | 5 | 2 |
| Low | 0 | 0 | 0 |

**All findings resolved. No open issues.**

## Notes
- `counter` and `counter_client` are non-FSM skills, excluded from audit.
- C1 (shared mutable references) grep across all skills: no matches found.
- `ROUND_TIMEOUT` enum members in library skills are a framework convention for extensibility, not dead code.
- `test_*` skills reported under separate section per false-positive guidance.
- The `transaction_settlement_abci` M5 bug was latent — the property was never called at runtime (`# pragma: no cover`), so it never crashed in production.
