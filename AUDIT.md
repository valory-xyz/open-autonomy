# Open-Autonomy Codebase Audit

**Date:** 2026-03-01
**Branch:** `chore/review_audit` (based on `feat/python3.14-compat`)
**Scope:** Architecture, bugs/reliability, security, developer experience

---

## Critical (Functional Bugs)

### C1. ~~`OfferSnapshot` gRPC handler returns wrong protobuf field~~ **RESOLVED**
- **File:** `packages/valory/connections/abci/connection.py:715`
- **Resolution:** Changed `response.list_snapshots` to `response.offer_snapshot`. Copy-paste error from `ListSnapshots` handler above.

### C2. ~~`read_until()` infinite loop on TCP peer disconnect~~ **RESOLVED**
- **File:** `packages/valory/connections/abci/connection.py:250-258`
- **Resolution:** Already fixed in `b70663046`. `read_until()` now raises `EOFError` when the connection is closed mid-read.

### C3. `shutil.rmtree(onerror=...)` deprecated in Python 3.12
- **Files:** `deployments/Dockerfiles/tendermint/app.py:160`, `autonomy/deploy/generators/localhost/tendermint/app.py:179`, `packages/valory/agents/register_reset/tests/helpers/slow_tendermint_server/app.py:99`
- **Impact:** `onerror=` parameter was deprecated in 3.12 in favor of `onexc=`. Still functional on Python 3.14. Low urgency — can migrate when `onerror=` is actually removed.

### C4. ~~`writer.write()` without `await writer.drain()` in TCP channel~~ **RESOLVED**
- **File:** `packages/valory/connections/abci/connection.py:1045`
- **Resolution:** Added `await writer.drain()` after `writer.write(data)` to apply back-pressure.

---

## High (Security / Reliability)

### H1. All Docker containers run as root — **NOT APPLICABLE**
- **Files:** All Dockerfiles under `deployments/Dockerfiles/` and `autonomy/data/Dockerfiles/`
- **Assessment:** By design for the current deployment model. Agents need to install packages and manage Tendermint. Containers run on operator-controlled infrastructure, not as multi-tenant services.

### H2. Flask Tendermint management server — no authentication, bound to `0.0.0.0` — **NOT APPLICABLE**
- **Files:** `deployments/Dockerfiles/tendermint/app.py`, `autonomy/deploy/generators/localhost/tendermint/app.py`
- **Assessment:** The server is internal to the Docker network (Docker Compose) or localhost. Only reachable by other containers on the same network. Access to the Docker network already implies full access.

### H3. ~~TendermintNode copied to 4 locations, already diverged~~ **RESOLVED**
- **Files:** `packages/valory/connections/abci/connection.py:1041-1334`, `deployments/Dockerfiles/tendermint/tendermint.py`, `autonomy/deploy/generators/localhost/tendermint/tendermint.py`, `packages/valory/agents/register_reset/tests/helpers/slow_tendermint_server/tendermint.py`
- **Resolution:** All 4 copies now have safety fixes applied. Group 1 (connection.py + Docker copy) is enforced identical by `test_deployment_class_identical`. Group 2 (localhost + slow_tendermint_server) has intentional architectural differences but all safety backports applied. See `TENDERMINT_NODE_SYNC.md`.

### H4. Race condition: monitoring thread vs `_stop_tm_process` (no lock) — **LOW PRIORITY**
- **Files:** All 4 TendermintNode copies (see H3)
- **Assessment:** The `_stopping` flag is a plain bool without synchronization. However, simple attribute reads/writes are GIL-atomic in CPython. The TOCTOU on `self._process is not None` is swallowed by `except Exception`. Code smell but not a practical bug under CPython.

### H5. Private keys written to disk without restrictive permissions
- **Files:** `autonomy/deploy/generators/localhost/base.py:120`, `autonomy/deploy/generators/docker_compose/base.py:519-520`
- **Impact:** Key files written with default 0o644 (world-readable). No `os.chmod(path, 0o600)` applied. On shared systems, any local user can read agent private keys. Valid hardening but low urgency — build directories are typically in temp dirs or project-local dirs.

### H6. `PRE_INSTALL_COMMAND` shell injection in Docker build — **NOT APPLICABLE**
- **Files:** `autonomy/deploy/image.py:111`, `autonomy/data/Dockerfiles/agent/Dockerfile:10`
- **Assessment:** This is a Docker build arg supplied by the operator building their own image — same trust model as writing a Dockerfile `RUN` directive. The operator controls the input.

### H7. ~~`preexec_fn=os.setsid` — unsafe in threaded programs, deprecated~~ **RESOLVED**
- **Files:** `connection.py:1145`, `deployments/.../tendermint.py:139`, `localhost/.../tendermint.py:137`, `slow_tendermint_server/tendermint.py:136`
- **Resolution:** All 4 files now use `start_new_session=True`.

### H8. HTTP 200 returned on error from all Flask endpoints — **NOT APPLICABLE**
- **Files:** `deployments/Dockerfiles/tendermint/app.py:268-292`, `autonomy/deploy/generators/localhost/tendermint/app.py:295-337`
- **Assessment:** The callers (ABCI connection) check the JSON body (`"status"` field), not the HTTP status code. Changing to 500 would break existing callers without benefit.

---

## Medium (Architecture / Code Quality)

### M1. `base.py` is a 3,924-line god-file with 40+ classes spanning 6 domains — **ACKNOWLEDGED**
- **File:** `packages/valory/skills/abstract_round_abci/base.py`
- **Assessment:** Architecture concern. Refactoring would be a major effort with high risk of breaking downstream packages. Not actionable now.

### M2. Skill imports constant from connection module — **ACKNOWLEDGED**
- **File:** `packages/valory/skills/abstract_round_abci/base.py:63`
- **Assessment:** Valid coupling concern but the import is declared in `skill.yaml` and works correctly. Moving the constant would change package hashes for no functional benefit.

### M3. `ABCIApplicationServicer` — 15 near-identical gRPC handler methods — **ACKNOWLEDGED**
- **File:** `packages/valory/connections/abci/connection.py:261-775`
- **Assessment:** Boilerplate but explicit. A dispatch table would reduce lines but risk breaking the protobuf/gRPC contract and make handler-specific logic (e.g. C1 fix) harder to trace.

### M4. `_MetaAbciApp` metaclass injects background round at import time — **ACKNOWLEDGED**
- **File:** `packages/valory/skills/abstract_round_abci/base.py:2042-2247`
- **Assessment:** By design. The metaclass injects background rounds on first concrete `AbciApp`. Import order is deterministic in production. Worth documenting but not a bug.

### M5. `deplopyment_type` typo baked into public API
- **Files:** `autonomy/deploy/base.py:158,474,618,634`, `autonomy/deploy/build.py:81`, test files
- **Impact:** Propagated across 8+ references. Renaming is a breaking change. Should be fixed with an alias for backward compat.

### M6. `COMPONENT_CONFIGS` dict defined independently in 3 modules — **ACKNOWLEDGED**
- **Files:** `autonomy/configurations/base.py:55`, `autonomy/configurations/loader.py:39`, `autonomy/deploy/base.py:88`
- **Assessment:** Duplication concern. Consolidation risks import cycles between configuration and deploy modules. Low priority.

### M7. Flask server `create_server()` discards TendermintNode reference — **NOT APPLICABLE**
- **Files:** `autonomy/deploy/generators/localhost/tendermint/app.py:354-357`, `deployments/Dockerfiles/tendermint/app.py:333-336`
- **Assessment:** The TendermintNode lives as a closure variable referenced by route handlers — it won't be GC'd. Flask doesn't have a clean shutdown lifecycle; the process exits when the container stops.

### M8. `docker.from_env()` clients created without closing — **ACKNOWLEDGED**
- **Files:** `plugins/aea-test-autonomy/aea_test_autonomy/docker/base.py:97`, `fixture_helpers.py` (15+ instances)
- **Assessment:** Test infrastructure only. Pytest processes exit after each suite, closing all connections. Low priority.

### M9. `asyncio.create_task()` task reference not stored — **ACKNOWLEDGED**
- **File:** `packages/valory/connections/abci/connection.py:844`
- **Assessment:** The task runs `_start_server()` which awaits the gRPC server. `disconnect()` stops the server, which completes the task. Not ideal but functional.

### M10. 11 suppressed `safety` CVEs without documentation — **ACKNOWLEDGED**
- **File:** `tox.ini:546`
- **Assessment:** Documentation gap. Each suppression should have a comment explaining why the CVE is safe to ignore.

### M11. `curl | sh` and unchecked binary downloads in Dockerfiles — **ACKNOWLEDGED**
- **Files:** `deployments/Dockerfiles/autonomy/Dockerfile:10`, `autonomy-user/Dockerfile:21`, `tendermint/install.sh`
- **Assessment:** Standard Docker practice. Images are built in CI from pinned URLs. Adding checksums would be good hardening but low urgency.

### M12. Node.js 16 EOL base image — **ACKNOWLEDGED**
- **File:** `deployments/Dockerfiles/hardhat/Dockerfile:1`
- **Assessment:** Only used for Hardhat (Ethereum dev tooling for testing). Not in production images. Low priority.

---

## Low (Developer Experience / Cleanup)

### L1. Inverted `svn` check in Makefile breaks `make new_env`
- **File:** `Makefile:161-163`
- **Impact:** `if [ ! -z "$(which svn)" ]; then echo "requires SVN, exit"; exit 1; fi` exits if svn IS found (inverted logic). Developers with svn installed cannot run `make new_env`.

### L2. `--fsm` flag declared as both `is_flag=True` and `type=str`
- **File:** `autonomy/cli/analyse.py:233-237`
- **Impact:** Contradictory Click option declaration. A flag cannot carry a string value.

### L3. "of of the service" typo in user-facing error messages
- **File:** `autonomy/cli/analyse.py:446,451`

### L4. CI uses `actions/checkout@v2` and `actions/setup-python@master`
- **File:** `.github/workflows/main_workflow.yml` (multiple lines)
- **Impact:** v2 is outdated (v4 current). `@master` is unpinned — any commit to the action immediately affects all builds. Security and reproducibility risk.

### L5. Wrong docstrings on `tendermint` and `acn_node` fixtures
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/fixture_helpers.py:97,383`
- **Impact:** Both say "Launch the Ganache image" — copy-paste error.

### L6. `pytest` listed as production dependency
- **File:** `setup.py:58`
- **Impact:** `pytest==8.4.2` in `base_deps` forces pytest into any `pip install open-autonomy`.

### L7. `tox.ini` is 1,004 lines with ~30 repetitive `[testenv]` blocks
- **File:** `tox.ini`
- **Impact:** Could be collapsed to ~200 lines using tox generative syntax. Hard for new developers to navigate.

### L8. `pytz==2022.2.1` — unnecessary on Python 3.14
- **Files:** `Pipfile:42`, `tox.ini:52`
- **Impact:** Only used for UTC timestamps. Python 3.9+ has `zoneinfo` and `datetime.timezone.utc`.

### L9. `hypothesis==6.21.6` pinned to 2022 release
- **Files:** `Pipfile:38`, `tox.ini:49`
- **Impact:** Current series is 6.100+. Old pin may conflict with consumer packages.

### L10. `filterwarnings("ignore")` at module scope
- **File:** `autonomy/cli/analyse.py:60`
- **Impact:** Suppresses all Python warnings globally when any `analyse` subcommand runs. Hides real deprecation warnings from dependencies.

### L11. Deprecated CLI commands not using Click's `deprecated=True`
- **Files:** `autonomy/cli/scaffold_fsm.py:91`, `autonomy/cli/deploy.py:491`, `autonomy/cli/hash.py:52`
- **Impact:** Users only discover deprecation at runtime, not in `--help`.

### L12. `ganache_scope_function` fixture marked `# TODO: remove as not used`
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/fixture_helpers.py:241`

### L13. Multiple dependency specification files with drifting version pins
- **Files:** `pyproject.toml`, `setup.py`, `tox.ini`, `Pipfile`, `setup.cfg`
- **Impact:** `jsonschema` range differs between `pyproject.toml` (`<4.4.0`) and `setup.py`/`tox.ini` (`<4.24.0`). `typing_extensions` upper bound also drifts.

### L14. `BaseBehaviour` bypasses MRO with explicit `__init__` calls
- **File:** `packages/valory/skills/abstract_round_abci/behaviour_utils.py:566`
- **Impact:** `# pylint: disable=super-init-not-called`. Diamond inheritance managed manually. Fragile if bases gain a common ancestor.

### L15. `$(PYTHON_VERSION)` used but never defined in Makefile
- **File:** `Makefile:171`
- **Impact:** `make new_env` silently uses pipenv's default Python resolution.

### L16. Linter CI job runs 15 checks sequentially
- **File:** `.github/workflows/main_workflow.yml`
- **Impact:** First failure aborts all subsequent linters. Developers must re-run CI to see the next error. Could be parallelized.

### L17. `e.args` destructuring can raise `IndexError`
- **File:** `autonomy/cli/helpers/analyse.py:256-257`
- **Impact:** `message, *_ = e.args` crashes if exception has empty args.

### L18. "Usefule" typo in module docstring
- **File:** `autonomy/cli/utils/click_utils.py:20`

### L19. Tendermint v0.34.19 — unmaintained, superseded by CometBFT
- **Impact:** No security patches upstream.

---

## Quick Wins (fixable in < 1 hour each)

| # | Fix | Effort |
|---|-----|--------|
| C1 | Change `response.list_snapshots` to `response.offer_snapshot` | 1 line |
| C3 | Migrate `onerror=` to `onexc=` (3 files) | 15 min |
| H7 | Replace `preexec_fn=os.setsid` with `start_new_session=True` (4 files) | 10 min |
| H8 | Return HTTP 500 on error in Flask endpoints | 15 min |
| L1 | Fix inverted svn check in Makefile | 1 line |
| L2 | Remove `is_flag=True` from `--fsm` option | 1 line |
| L3 | Fix "of of" typo | 1 line |
| L5 | Fix copy-paste docstrings | 2 lines |
| L10 | Narrow `filterwarnings` to specific warnings | 5 min |
| L12 | Remove dead `ganache_scope_function` | 5 min |
| L18 | Fix "Usefule" typo | 1 line |
| M5 | Add `deployment_type` property aliasing `deplopyment_type` | 5 min |
