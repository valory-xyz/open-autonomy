# Eliminate Flaky Tests — Implementation Tracker

This document tracks the migration from "tests that fail intermittently"
to "tests that fail only when there is a real bug." Each entry has the
same shape: what the test was doing before, what we changed, and what
the post-change guarantee is. Tick the checkbox once the change is
landed and verified locally.

## Guiding rules

1. No `@pytest.mark.flaky(reruns=*)` markers in the final tree.
2. No static-fixture pinning of upstream data. Live data stays live.
3. Distinguish transient infra failure (skip) from real bug (fail).
4. Stop polling stdout for log substrings. Poll the actual state.
5. Tests that need a real subprocess / container live in the e2e job,
   not in the per-Python unit matrix.

## Shared infra

- [x] **Network helper.** Add `tests/utils/live_fetch.py` exposing
      `fetch_upstream_or_skip(url, timeout)` and `live_session()`.
      The helper retries `ConnectionError`, `Timeout`, and 5xx with
      exponential backoff (5 attempts, ~31s total wait), then
      `pytest.skip(...)` if still unreachable. Real HTTP errors
      (4xx, content mismatch) still fail.

## Group A — live network tests (replace bare `requests.get` with the helper)

- [x] **A1. `TestYamlSnippets::test_run_check`**
      ([tests/test_docs/test_code_blocks.py:169](../../tests/test_docs/test_code_blocks.py#L169))
  - **Before:** fetches the upstream `fsm_specification.yaml` from
    `raw.githubusercontent.com` and diffs it against the YAML embedded
    in our docs. Any DNS or network hiccup fails the test.
  - **Change:** the fetch goes through the live helper.
  - **Guarantee:** content drift between our docs and upstream is
    still caught. Transient GitHub / DNS noise becomes `SKIPPED`.

- [x] **A2. `TestAddresses::test_addresses_match`**
      ([tests/test_autonomy/test_chain/test_addresses.py:42](../../tests/test_autonomy/test_chain/test_addresses.py#L42))
  - **Before:** `setup_class` fetches `configuration.json` from GitHub.
    Each parametrized test also calls a live chain RPC to verify the
    constant address resolves to the expected contract. Both halves
    fail hard on transient network failures.
  - **Change:** both halves use the live helper.
  - **Guarantee:** constant-vs-live address drift still fails CI.
    RPC outages and DNS hiccups become `SKIPPED`.

- [x] **A3. `tests/test_docs/helper.py` (the GitHub fetcher)**
  - **Before:** `read_file_from_repository` makes two unauthenticated
    GitHub calls (api + raw); used by several doc tests.
  - **Change:** both calls go through the live helper.
  - **Guarantee:** every doc test that reaches upstream inherits the
    transient-vs-real distinction automatically.

## Group B — real Tendermint binary tests

- [x] **B1. `TestTendermintBufferWorking::test_tendermint_buffer`**
      ([tests/test_deployments/test_app.py:511](../../tests/test_deployments/test_app.py#L511))
  - **Before:** starts a real `tendermint` binary, polls
    `/status` once a second for 60s, fails on any single failed poll.
    Runs on every cell of the unit matrix; Windows and macOS runners
    have known Tendermint socket / scheduler noise.
  - **Change:** (a) skip on non-Linux (matches existing precedent at
    `test_hard_reset_dev_mode`). Linux is the production platform.
    (b) Replace per-poll asserts with monotonic block-height progress:
    poll `/status`, parse `latest_block_height`, verify it never goes
    backwards and that at least 2 blocks were produced in 60s.
    Transient socket failures get retried, not asserted-against.
  - **Guarantee:** Tendermint hanging, crashing, or rolling back during
    the 60s window still fails the test. Per-poll socket jitter does
    not.

- [~] **B2. `TestTendermintServerApp` (entire class)**
      ([tests/test_deployments/test_app.py:205](../../tests/test_deployments/test_app.py#L205))
  - **Re-scoped:** the failures previously attributed to this class were
    actually a real bug in the docker copy of the Flask app, fixed in
    `b94b2ed4e` (catches widened to parity with the localhost copy).
    Post-fix runs confirm these tests are no longer flaky.
  - The split into pure-handler vs runtime is still a nice cleanup but
    not load-bearing for de-flaking. Tracked separately; not in scope
    for this PR.
  - **Status:** no action needed for flakiness. Leaving the class as-is.

- [ ] **B3. `TestNoop`, `TestQuery` in `test_abci.py`**
      ([packages/valory/connections/abci/tests/test_abci.py:480](../../packages/valory/connections/abci/tests/test_abci.py#L480))
  - **Before:** spin up a Tendermint container, `time.sleep(5)`,
    single `/health` check, sleep again, verify it's still up.
  - **Change:** replace sleep+health-check with block-height-progress
    polling.
  - **Guarantee:** a broken ABCI integration (no blocks produced) is
    caught. Slow docker pull does not cause a phantom failure.

- [ ] **B4. `test_runtime`**
      ([tests/test_autonomy/test_images/test_runtime.py:202](../../tests/test_autonomy/test_images/test_runtime.py#L202))
  - **Before:** waits up to 30s for the log string
    `"Starting AEA 'agent' in 'async' mode..."` in the container's
    logs.
  - **Change:** poll the container's `State.Status` via
    `docker_client.api.inspect_container(...)` instead. Raise timeout
    to 180s for realistic cold-start. Dump full container logs into
    the failure message.
  - **Guarantee:** the agent failing to start is caught. The agent
    starting slowly on a busy runner is not.

## Group C — docker-third-party tests

- [ ] **C1. `TestLocalServiceRegistry`**
      ([tests/test_autonomy/test_cli/test_develop/test_local_service_registry.py:82](../../tests/test_autonomy/test_cli/test_develop/test_local_service_registry.py#L82))
  - **Before:** polls `requests.get(network_address)` 30 times × 5s
    sleeps, fails after 150s.
  - **Change:** read the hardhat subprocess's stdout for the
    `"Account #0:"` marker (block on that with a 5-minute ceiling),
    then run the HTTP probe through the live helper from Group A.
  - **Guarantee:** hardhat failing to start is caught. Hardhat taking
    90s instead of 30s on a slow runner is not.

## Group D — all e2e agent tests (10 classes, one base-class change)

The whole bucket is two race conditions in
`plugins/aea-test-autonomy/aea_test_autonomy/base_test_classes/agents.py`:

1. Agents and Tendermint containers are started in parallel, so
   Tendermint dials the agent's ABCI port before it's bound.
2. `missing_from_output(process, happy_path, timeout)` scans agent
   stdout for marker strings. Log buffering and capture timing add
   jitter.

The fix is one base-class change, but each derived test class needs
to be verified.

- [ ] **D-shared. Refactor `BaseTestEnd2EndExecution`**
      ([plugins/aea-test-autonomy/aea_test_autonomy/base_test_classes/agents.py](../../plugins/aea-test-autonomy/aea_test_autonomy/base_test_classes/agents.py))
  - **Change:** (a) start agents first, poll each agent's ABCI port
    until TCP `connect()` succeeds, then start the corresponding
    Tendermint container. (b) Replace `missing_from_output` substring
    matching with `wait_for_round_advance` that queries the agent's
    actual round state.
  - **Guarantee:** real consensus failures still fail the test. Runner
    CPU contention and slow log flushes do not.

The following tests carry `@pytest.mark.flaky(reruns=1)` today; all
markers are removed after D-shared lands and the test still passes.

- [ ] **D1.** `register_reset` — `TestTendermintStartup`,
      `TestTendermintReset`, `TestTendermintResetInterrupt`,
      `TestTendermintResetInterruptNoRejoin`, `TestTendermintResetRejoin`
- [ ] **D2.** `register_reset` — `TestHardResetRaceCondition`
- [ ] **D3.** `offend_slash` — `SlashingE2E`, `TestSlashingThresholdUnmet`,
      `TestSlashing`
- [ ] **D4.** `counter` — `TestABCICounterSkillMany`
- [ ] **D5.** `test_ipfs`
- [ ] **D6.** `registration_start_up`
- [ ] **D7.** `abstract_abci`
- [ ] **D8.** `register_reset_recovery`
- [ ] **D9.** `register_termination`
- [ ] **D10.** `solana_transfer_agent`

## Group E — workarounds that exist only because of flakiness

- [~] **E1. `BaseTendermintServerTest` shared class state.**
  Linked to **B2**. No longer in scope for de-flaking after the B2
  re-scope; tests in this class are not currently flaky.

- [ ] **E2. `_run_count` hack in `SlashingE2E`**
      ([packages/valory/agents/offend_slash/tests/test_offend_slash.py:91](../../packages/valory/agents/offend_slash/tests/test_offend_slash.py#L91))
  - **Before:** detects "am I a flaky rerun" via a class counter, then
    re-initialises the tempdir, subprocess list, and agent context.
  - **Change:** subsumed by **D3** (no more reruns, no need for the
    hack). Delete `_run_count`, the conditional `setup_method` branch,
    and the `@pytest.mark.flaky(reruns=1)` marker.
  - **Guarantee:** one code path, not two.

## Group F — non-determinism

- [x] **F1. `random.randint` in `TestABCICounterSkillMany`**
      ([packages/valory/agents/counter/tests/test_counter.py:217](../../packages/valory/agents/counter/tests/test_counter.py#L217))
  - **Before:** unseeded `random.randint(0, NB_AGENTS-1)` to pick which
    agent receives each of 15 transactions.
  - **Change:** instantiate `rng = random.Random(0)` at the top of the
    test and use `rng.randint(...)` for picks.
  - **Guarantee:** routing is exercised identically across runs.

## Post-implementation sanity check

- [ ] No `@pytest.mark.flaky` markers remain
      (`grep -rn "@pytest.mark.flaky\|@flaky" tests packages plugins`).
- [ ] No `time.sleep(N)` followed directly by `assert` in any e2e or
      integration test.
- [ ] All bare `requests.get(url)` calls in the test tree either go
      through `fetch_upstream_or_skip` or are explicitly marked as
      local-only (talking to localhost).
- [ ] Full CI matrix is green twice in a row with no reruns.
