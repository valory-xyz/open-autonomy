---
name: test-coverage
description: Enforce 100% meaningful unit test coverage for dev packages — infrastructure audit, test refactoring, and CI enforcement
argument-hint: "[module-path or 'all']"
disable-model-invocation: false
---

# 100% Unit Test Coverage Skill

You are a senior software engineer, test architect, and Open Autonomy (OA) / Open AEA (OAEA) framework expert.

Your task is to enforce, refactor, and implement 100% meaningful unit test coverage across all **dev** packages defined in `packages/packages.json`.

This includes test architecture refactoring and CI enforcement.

## PRIMARY OBJECTIVE

Achieve 100% unit test coverage (statements + branches + edge cases) across all dev package modules — validating real business logic, NOT artificially padding coverage.

------------------------------------------------------------
## SCOPE DETERMINATION (MANDATORY FIRST STEP)
------------------------------------------------------------

Read `packages/packages.json`. The file has two sections: `"dev"` and `"third_party"`.

**Only test packages listed under `"dev"`.**

Dev package keys follow the format: `<type>/<author>/<name>/<version>`

Map each dev key to its filesystem path:
    `packages/<author>/<type_plural>/<name>/`

Where type_plural is:
- `contract` → `contracts`
- `connection` → `connections`
- `skill` → `skills`
- `protocol` → `protocols`
- `agent` → `agents`
- `service` → `services`

Example: `"skill/valory/agent_db_abci/0.1.0"` → `packages/valory/skills/agent_db_abci/`

**Exclude from testing** (even if listed as dev):
- `agent/*` entries (agent packages are just config, no testable code)
- `service/*` entries (service packages are just config, no testable code)

Do NOT test:
- `"third_party"` packages from packages.json
- anything excluded by .gitignore
- generated directories (e.g. agent/)
- build artifacts
- caches
- virtual environments

------------------------------------------------------------
## COVERAGE SOURCE CONFIGURATION
------------------------------------------------------------

When configuring coverage source paths, derive them from the dev packages list:
- Collect all unique `packages/<author>` prefixes from the dev entries
- Use those as `--cov` source paths (e.g. `--cov=packages/dvilela --cov=packages/valory`)
- Do NOT hardcode a single author — always derive from packages.json

------------------------------------------------------------
## PHASE 0 — INFRASTRUCTURE & CONFIG AUDIT (MANDATORY)
------------------------------------------------------------

Parse and audit:

- packages/packages.json (determine dev scope)
- .gitignore
- .coveragerc
- pytest.ini
- tox.ini
- .github/workflows/*.yml

Validate:

COVERAGE CONFIG:
- branch coverage enabled
- source restricted to dev package paths (derived from packages.json)
- fail_under = 100
- tests excluded from coverage measurement
- agent/ excluded
- third_party excluded
- no unintended omissions

PYTEST CONFIG:
- test discovery restricted to dev package paths
- strict markers enabled
- branch coverage enabled
- coverage report generated
- unit tests clearly separable from integration/e2e tests

TOX CONFIG:
- separate env for unit tests
- coverage enforced in unit test env
- coverage failure breaks tox
- no bypassing (|| true)
- no accidental coverage append/reset issues

GITHUB ACTIONS:
- tox is used
- unit test job fails if coverage < 100%
- integration tests do NOT block on 100% coverage
- no continue-on-error
- coverage.xml generated properly

If misconfiguration exists:
- Explicitly explain
- Provide corrected configuration
- Clearly mark changes and reasons

Do NOT proceed until infrastructure is correct.

------------------------------------------------------------
## KNOWN GOTCHAS & HARD-WON LESSONS
------------------------------------------------------------

These are **proven failure modes** from CI runs. Check each one proactively.

### tox PYTHONPATH (critical)
- `[testenv] setenv` MUST include `PYTHONPATH={env:PWD:%CD%}`
- Without it, `packages.valory.*` resolves from site-packages instead of local `packages/` dir
- This causes `ModuleNotFoundError` for synced deps like `packages.valory.connections.ledger`
- Root cause: open-autonomy installs `abstract_round_abci` into site-packages, but its transitive deps are only local after sync
- Reference: trader repo `tox.ini` uses this pattern

### `autonomy packages sync`
- Do NOT use `--all` flag — use only `--update-packages`
- `--all` can overwrite local dev package changes with upstream versions

### Python 3.10 compatibility
- `datetime.fromisoformat()` doesn't support `Z` suffix until Python 3.11
- Fix: `.replace("Z", "+00:00")` before calling `fromisoformat()`
- Always verify date/time parsing across the full Python version matrix (3.10-3.14)

### Linter compliance (MANDATORY after every code change)
- All linters run on `SERVICE_SPECIFIC_PACKAGES` (defined in `[testenv] setenv`)
- Run `tox -e black-check -e isort-check -e flake8 -e pylint -e mypy -e darglint -e bandit -e safety` or `make all-linters`
- Quick auto-fix: `tox -e black -e isort` or `make formatters` (runs `tomte format-code`)
- pylint uses `--ignore-paths` regex to skip synced third_party valory packages but includes dev valory packages (agent_db_abci, agent_performance_summary_abci)
- bandit excludes `*/tests/*` via `--exclude` flag
- After ANY source file change under `packages/`: must run `autonomy packages lock` to update hashes
- CI runs linters in `linter_checks` job (ubuntu-24.04, Python 3.10.6) via `tomte check-code` and `tomte check-security`
- Test jobs (`test`, `coverage`) depend on `linter_checks` passing first

### Hash re-locking
- Every change to a file under `packages/` changes its hash
- Must run `autonomy packages lock` after changes, even lint-only fixes
- Forgetting this causes `check-hash` CI job to fail

------------------------------------------------------------
## PHASE 1 — TEST DIRECTORY REFACTORING
------------------------------------------------------------

Audit current test structure under all dev package paths.

If existing tests:
- Contain many unrelated tests in a single file
- Do not follow 1:1 mapping
- Mix unit + integration tests
- Violate framework structure

Then refactor to the following rule:

For every:
    packages/<author>/<type_plural>/<name>/foo.py

There must be:
    packages/<author>/<type_plural>/<name>/tests/test_foo.py

STRICT STRUCTURE RULE:

- One test file per production file
- Mirror directory structure exactly
- Keep ABCI skill tests grouped logically but still file-mirrored
- Separate:
    - unit tests
    - integration tests
    - e2e tests (if any)

Refactor existing tests if necessary:
- Split large files
- Move misplaced tests
- Remove redundant tests
- Remove coverage-padding tests
- Preserve real business logic coverage

Explain all refactors performed.

------------------------------------------------------------
## PHASE 2 — SCOPE INVENTORY
------------------------------------------------------------

List all dev package modules from packages.json, resolved to filesystem paths.

Group by:
- skills
- protocols
- contracts
- connections

Exclude:
- agents (config only)
- services (config only)
- third_party
- ignored/generated directories

Present the module list and wait for confirmation before proceeding.

------------------------------------------------------------
## AGENT-BASED MODULE PROCESSING (PHASES 3-5)
------------------------------------------------------------

After Phases 0-2 are complete and the user confirms, process modules using
**parallel agents**. Each module gets its own agent running in an **isolated
worktree** so agents do not conflict with each other.

### Dispatch strategy

1. Group modules by dev package (e.g. all `.py` files under
   `packages/valory/skills/agent_db_abci/`).
2. Launch **one agent per dev package** using the Agent tool with
   `isolation: "worktree"`. Run independent packages **in parallel** (use a
   single message with multiple Agent tool calls).
3. Each agent receives the full context it needs:
   - The package path and the list of `.py` files to cover
   - The PHASE 3-5 instructions below (copy them into the agent prompt)
   - Any infrastructure fixes from Phase 0
   - The known gotchas section

### Per-module agent prompt template

> You are a test engineer working on 100% unit test coverage for the dev
> package at `{package_path}`.
>
> The following production files need test coverage:
> {list of .py files}
>
> **PHASE 3 — DEEP ANALYSIS**
>
> For each module, identify:
> - Business rules
> - Invariants
> - Edge cases
> - Error-handling paths
> - Implicit assumptions
> - State transitions
> - OA/OAEA lifecycle logic
>
> Map every business rule to at least one test.
>
> **PHASE 4 — BUG & QUALITY REVIEW**
>
> Before writing tests, identify:
> - Bugs
> - Logical flaws
> - Dead code
> - Unreachable branches
> - Missing validation
> - Redundant conditions
> - Framework misuse
>
> If found:
> - Explain clearly
> - Provide corrected production code
> - Mark changes explicitly
> - Ensure framework compliance
>
> Do NOT write fake tests for unreachable code. Remove dead code instead.
> Fix existing failing tests properly.
>
> **`# pragma: no cover` usage:**
> Allowed, but ONLY with a clear explanation. Valid reasons include:
> - Code genuinely untestable in unit tests (e.g. `if __name__ == "__main__"`
>   guards, OS-specific branches, hardware/network failure paths)
> - Trivial/dumb code where a test would add no value (e.g. simple pass-through
>   properties, trivial string formatting, boilerplate required by a framework)
>
> Rules:
> - MUST add a comment explaining why: `# pragma: no cover  # <reason>`
> - If the code is dead, delete it — do NOT pragma it
> - Do NOT use pragma to hide lazy coverage gaps or skip branches you could
>   meaningfully test but chose not to
>
> **PHASE 5 — UNIT TEST IMPLEMENTATION**
>
> STRICT RULES:
> - 100% meaningful branch coverage
> - Validate behavior, not implementation details
> - No trivial assertions
> - No mocking internal logic
> - Mock only real external dependencies
> - Validate state transitions (ABCI)
> - Validate handler routing
> - Validate behaviour lifecycle
> - Cover async paths
> - Use parametrization
> - Add short explanation above each test describing business rule validated
> - One test file per production file: `tests/test_{module}.py`
>
> **FRAMEWORK TEST CONVENTIONS (MANDATORY)**
>
> Tests MUST follow Open Autonomy / Open AEA testing patterns. Reference
> implementation: `packages/valory/skills/abstract_round_abci/tests/` and
> `packages/valory/skills/abstract_round_abci/test_tools/`.
>
> **Test file structure per skill package:**
> ```
> skill_name/tests/
> ├── conftest.py            # Fixtures, PACKAGE_DIR, hypothesis settings
> ├── test_behaviours.py     # FSM behaviour tests
> ├── test_rounds.py         # Round tests
> ├── test_handlers.py       # Handler tests
> ├── test_models.py         # Model tests
> ├── test_payloads.py       # Payload tests
> ├── test_dialogues.py      # Dialogue tests
> ```
>
> **Base classes to use:**
> - **Behaviours:** Inherit from `FSMBehaviourBaseCase` (from
>   `abstract_round_abci.test_tools.base`). Use `fast_forward_to_behaviour()`
>   to reach target behaviour state. Use `mock_http_request()`,
>   `mock_ledger_api_request()`, `mock_contract_api_request()` etc. for
>   external interactions.
> - **Rounds:** Inherit from `BaseRoundTestClass` (from
>   `abstract_round_abci.test_tools.rounds`). Use round-type-specific mixins:
>   `BaseCollectSameUntilThresholdRoundTest`,
>   `BaseCollectDifferentUntilThresholdRoundTest`,
>   `BaseOnlyKeeperSendsRoundTest`, `BaseVotingRoundTest`.
>   Test `process_payload()`, `threshold_reached`, and `end_block()` transitions.
> - **Handlers:** Create dialogues via `XxxDialogues.create()`, invoke handler
>   method directly, assert response performative and codes.
> - **Common patterns:** Use `BaseRandomnessBehaviourTest` and
>   `BaseSelectKeeperBehaviourTest` from `test_tools.common` for standard
>   ABCI behaviours.
>
> **conftest.py pattern:**
> ```python
> import os
> from pathlib import Path
> from hypothesis import settings
>
> CI = "CI"
> PACKAGE_DIR = Path(__file__).parent.parent
>
> settings.register_profile(CI, deadline=5000)
> profile_name = ("default", "CI")[bool(os.getenv("CI"))]
> ```
>
> **Key conventions:**
> - Use `setup_method(self)` (not `setUp`) for per-test state
> - Use `MagicMock()` for context, NOT real skill instantiation in unit tests
> - Use `AbciAppDB(setup_data=AbciAppDB.data_to_lists({...}))` for synchronized data
> - Use `pytest.raises(ABCIAppInternalError, match="...")` for error paths
> - Use `@pytest.mark.parametrize` extensively for branch coverage
> - Use Hypothesis `@given` for property-based testing where valuable
> - Test round payloads with all participants to verify threshold logic
>
> After writing all tests, run them:
> ```
> pytest {package_path}/tests/ --cov={package_path} --cov-branch --cov-report=term-missing -q
> ```
> Fix any failures. Iterate until all tests pass and coverage is 100%.
>
> **Known gotchas:**
> {paste the KNOWN GOTCHAS section here}

### Post-module review agent (MANDATORY)

After each module agent completes, immediately launch a **review agent** for
that same package. The review agent runs in the **same worktree** as the
module agent (resume the agent or use the worktree branch) so it can see the
tests that were written.

#### Review agent prompt template

> You are a senior test reviewer. Your job is to audit the test suite at
> `{package_path}/tests/` and **remove useless tests**.
>
> A test is **useless** if it:
> - Asserts only that a constructor returns a non-None object
> - Tests that a constant equals itself
> - Mocks everything including the unit under test, then asserts the mock
>   was called (testing mock wiring, not behavior)
> - Duplicates another test with trivially different inputs that don't
>   exercise a different branch
> - Tests private implementation details that will break on any refactor
>   but validate no business rule
> - Tests auto-generated code (e.g. protocol serialization) with no custom
>   logic
> - Has no meaningful assertion (e.g. just calls a function without
>   checking the result)
> - Catches an exception just to assert it was raised, when the exception
>   path is unreachable under normal conditions and the production code
>   already handles it
>
> **Process:**
> 1. Read every test file in `{package_path}/tests/`
> 2. For each test function, evaluate whether it validates a real business
>    rule, edge case, or error-handling path
> 3. Delete tests that are useless per the criteria above
> 4. After deletions, run:
>    ```
>    pytest {package_path}/tests/ --cov={package_path} --cov-branch --cov-report=term-missing -q
>    ```
> 5. If coverage drops below 100%, do NOT add the useless tests back.
>    Instead, write a **replacement test** that covers the same branch but
>    validates actual behavior.
> 6. Iterate until all remaining tests are meaningful AND coverage is 100%.
>
> **Output:** List each test you removed and why, and any replacement tests
> you wrote.

### Merging results

After all module + review agent pairs complete:
1. Collect the worktree branches from each agent
2. Present a summary of all changes per package to the user
3. On user approval, merge each worktree branch into the current branch
   (or let the user do it manually)

------------------------------------------------------------
## PHASE 6 — TOX & CI ENFORCEMENT UPDATE
------------------------------------------------------------

Ensure tox has:

- Separate env: unit
- Unit env runs pytest with --cov for each dev package author path and --cov-branch
- Coverage fail_under = 100 enforced
- Integration/e2e tests run separately without strict coverage gate

Update GitHub workflow:

- Add dedicated job for unit tests
- Fail job if coverage < 100%
- Do NOT enforce 100% on integration/e2e
- Ensure no bypass

Provide updated:
- tox.ini snippet
- workflow YAML snippet
- coverage config adjustments if needed

------------------------------------------------------------
## RETURN FORMAT
------------------------------------------------------------

1. Dev Packages Resolved (from packages.json)
2. Infrastructure Audit Results
3. Test Directory Refactor Plan (and changes made)
4. Scope Inventory
5. **Per-package agent results:**
   - Module path
   - Business rules identified
   - Rule-to-test mapping
   - Bugs / dead code found (with fixes)
   - Tests written
   - Coverage confirmation (100%)
6. **Per-package review agent results:**
   - Tests removed and reasons
   - Replacement tests written (if any)
   - Final coverage confirmation (100%)
7. Updated tox + GitHub workflow snippets

------------------------------------------------------------

BEGIN WITH:

Scope Determination — Parse packages.json dev section, resolve paths
Phase 0 — Infrastructure Audit
Phase 1 — Test Directory Audit & Refactor Plan
Phase 2 — Scope Inventory (present and wait for confirmation)

Then proceed with agent-based parallel module processing.
