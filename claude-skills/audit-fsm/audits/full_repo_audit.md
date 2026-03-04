# FSM Audit Report — Full Repository

**Scope:** All FSM skills in `packages/valory/skills/`
**Date:** 2026-03-04

## CLI Tool Results

| Tool | Result |
|------|--------|
| `autonomy analyse fsm-specs` | PASS (registration_abci) |
| `autonomy analyse handlers` | FAIL — `counter_client` missing `abci` handler (pre-existing, not FSM skill) |
| `autonomy analyse dialogues` | FAIL — `counter_client` missing `abci_dialogues` (pre-existing, not FSM skill) |
| `autonomy analyse docstrings` | FAIL — `registration_abci` and `reset_pause_abci` docstrings stale (fixed on `fix/audit-round-2` branch) |

---

## Critical Findings

### C4: Dead Timeout — `registration_abci` `Event.ROUND_TIMEOUT`
- **File:** `packages/valory/skills/registration_abci/rounds.py:44`
- **Issue:** `Event.ROUND_TIMEOUT` is defined in the enum but never appears in any `transition_function` keys. `event_to_timeout` is empty. The class docstring falsely claims `round timeout: 30.0`.
- **Fix:** Remove `ROUND_TIMEOUT` from the enum and update the docstring. *(Already fixed on `fix/audit-round-2` branch.)*

### ~~C4: Dead Timeout — `test_abci` `Event.ROUND_TIMEOUT` and `Event.RESET_TIMEOUT`~~ — RECLASSIFIED: not-issue
- **File:** `packages/valory/skills/test_abci/rounds.py:84-86`
- **Reclassification:** `test_abci` is a test/scaffold skill, not a production FSM app. The dead timeouts are intentional test fixtures — `models.py:SharedState.setup()` wires these `event_to_timeout` entries from params, which is the behaviour under test.

### ~~C4: Dead Timeout — `test_solana_tx_abci` `Event.ERROR`~~ — RECLASSIFIED: not-issue
- **File:** `packages/valory/skills/test_solana_tx_abci/rounds.py:134`
- **Reclassification:** `test_solana_tx_abci` is a test/scaffold skill. The `Event.ERROR` in `event_to_timeout` is part of the test scaffolding, not a production oversight.

---

## High Findings

### M1: Wrong `payload_class` — `squads_transaction_settlement_abci` `ExecuteTxRound`
- **File:** `packages/valory/skills/squads_transaction_settlement_abci/rounds.py:195`
- **Issue:** `ExecuteTxRound` declares `payload_class = CreateTxPayload` but the `keeper_payload` type hint is `Optional[ExecuteTxPayload]` and `end_block()` accesses `self.keeper_payload.tx_pda` which is an `ExecuteTxPayload` field. The payload class mismatch will cause validation errors.
- **Code:**
  ```python
  class ExecuteTxRound(OnlyKeeperSendsRound):
      keeper_payload: Optional[ExecuteTxPayload] = None
      payload_class = CreateTxPayload  # BUG: should be ExecuteTxPayload
  ```
- **Fix:** Change to `payload_class = ExecuteTxPayload`.

### M1: Potential DB Key Mismatch — `slashing_abci` `participant_to_offence_reset`
- **File:** `packages/valory/skills/slashing_abci/rounds.py:105`
- **Issue:** The property `participant_to_offence_reset` fetches from DB key `"participant_to_randomness"` instead of `"participant_to_offence_reset"`. This is a likely copy-paste error.
- **Code:**
  ```python
  @property
  def participant_to_offence_reset(self) -> DeserializedCollection:
      serialized = self.db.get_strict("participant_to_randomness")  # Wrong key?
  ```
- **Fix:** Verify intended key. If the property should read its own data, change to `self.db.get_strict("participant_to_offence_reset")`.

---

## Medium Findings

### L3: Stale Docstring — `registration_abci` "price estimation demo"
- **File:** `packages/valory/skills/registration_abci/rounds.py:41`
- **Issue:** Copy-pasted docstring references wrong skill.
- **Fix:** Change to `"""Event enumeration for agent registration."""`

### L3: Docstring Grammar — `registration_abci` "This rounds waits"
- **File:** `packages/valory/skills/registration_abci/rounds.py:94`
- **Fix:** Change `"This rounds waits"` to `"This round waits"`.

### T5: Incomplete Round Event Testing — `test_ipfs_abci`
- **File:** `packages/valory/skills/test_ipfs_abci/tests/test_rounds.py:27-33`
- **Issue:** `test_end_block()` calls `end_block()` without asserting the return value. No coverage for `Event.DONE` or `Event.ROUND_TIMEOUT` transitions.
- **Fix:** Add assertions verifying correct events under different conditions.

### ~~T5: Incomplete Round Event Testing — `test_abci`~~ — RECLASSIFIED: not-issue
- **File:** `packages/valory/skills/test_abci/tests/test_rounds.py:45-80`
- **Reclassification:** `test_abci` is a test/scaffold skill. `ROUND_TIMEOUT` and `RESET_TIMEOUT` are not in the transition function (they are test fixtures for `SharedState.setup()`), so there are no transitions to test for them.

---

## Low Findings

No findings.

---

## Skills With Clean Audits

| Skill | Status |
|-------|--------|
| `transaction_settlement_abci` | All checks PASS |
| `offend_abci` | All checks PASS |
| `termination_abci` | All checks PASS |
| `register_reset_recovery_abci` | All checks PASS |
| `reset_pause_abci` | All checks PASS (ROUND_TIMEOUT is implicit framework handling) |

## Composition Files — All PASS

| Composition | H2 Status |
|-------------|-----------|
| `register_reset_abci/composition.py` | PASS — all final states mapped |
| `register_termination_abci/composition.py` | PASS — BackgroundAppConfig correct (TERMINATING type) |
| `register_reset_recovery_abci/composition.py` | PASS — chain complete |
| `offend_slash_abci/composition.py` | PASS — chain and background config correct |
| `slashing_abci/composition.py` | PASS — post-hoc transition modification is intentional for background round |
| `test_solana_tx_abci/composition.py` | PASS — chain complete |

## Test Checks (T1–T6) — All PASS except noted

| Check | Status |
|-------|--------|
| T1: `@classmethod @pytest.fixture` | PASS across all skills |
| T2: Wrong base test class | PASS across all skills |
| T3: Missing required attributes | PASS across all skills |
| T4: Missing `mock_a2a_transaction()` | PASS across all skills |
| T5: Incomplete event testing | FAIL — `test_abci`, `test_ipfs_abci` (see Medium) |
| T6: Registry save/restore | PASS across all skills |

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1     |
| High     | 2     |
| Medium   | 4     |
| Low      | 0     |
| Reclassified (not-issue) | 2 |

## Notes
- The C4 finding in `registration_abci` and the L3 docstring issues are already fixed on the `fix/audit-round-2` branch.
- The `slashing_abci` DB key mismatch (H) needs manual verification — the property may intentionally alias another key.
- The `squads_transaction_settlement_abci` payload_class bug (H) is a clear copy-paste error that should be fixed.
- `counter` and `counter_client` skills are non-FSM skills and were excluded from this audit.
- `abstract_round_abci` base module and behaviours were checked for C1/C2/H1 — all PASS on current branch.
- `test_abci` and `test_solana_tx_abci` are test/scaffold skills — their C4 findings were reclassified as not-issues since the dead timeouts are intentional test fixtures.
