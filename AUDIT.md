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

### H1. All Docker containers run as root
- **Files:** All Dockerfiles under `deployments/Dockerfiles/` and `autonomy/data/Dockerfiles/`
- **Impact:** No `USER` directive. Container compromise gives root access. Combined with `chmod 777` on `/app`, `/tendermint`, `/tm_state`, `/home` — any process can overwrite config, genesis, and key files.

### H2. Flask Tendermint management server — no authentication, bound to `0.0.0.0`
- **Files:** `deployments/Dockerfiles/tendermint/app.py`, `autonomy/deploy/generators/localhost/tendermint/app.py`
- **Impact:** Unauthenticated endpoints `/hard_reset`, `/gentle_reset`, `/params` (POST) allow any network-reachable peer to reset consensus state, reconfigure genesis, or read node parameters. Returns full Python tracebacks on error (information leakage).

### H3. ~~TendermintNode copied to 4 locations, already diverged~~ **RESOLVED**
- **Files:** `packages/valory/connections/abci/connection.py:1041-1334`, `deployments/Dockerfiles/tendermint/tendermint.py`, `autonomy/deploy/generators/localhost/tendermint/tendermint.py`, `packages/valory/agents/register_reset/tests/helpers/slow_tendermint_server/tendermint.py`
- **Resolution:** All 4 copies now have safety fixes applied. Group 1 (connection.py + Docker copy) is enforced identical by `test_deployment_class_identical`. Group 2 (localhost + slow_tendermint_server) has intentional architectural differences but all safety backports applied. See `TENDERMINT_NODE_SYNC.md`.

### H4. Race condition: monitoring thread vs `_stop_tm_process` (no lock)
- **Files:** All 4 TendermintNode copies (see H3)
- **Impact:** `_stopping` flag and `_process` reference mutated by both monitoring thread and main thread without synchronization. TOCTOU on `self._process is not None` check → `readline()` call. Swallowed by `except Exception` but produces undefined behavior. The localhost copy also lacks stdout close and `join(timeout=)`, creating potential hangs.

### H5. Private keys written to disk without restrictive permissions
- **Files:** `autonomy/deploy/generators/localhost/base.py:120`, `autonomy/deploy/generators/docker_compose/base.py:519-520`
- **Impact:** Key files written with default 0o644 (world-readable). No `os.chmod(path, 0o600)` applied. On shared systems, any local user can read agent private keys.

### H6. `PRE_INSTALL_COMMAND` shell injection in Docker build
- **Files:** `autonomy/deploy/image.py:111`, `autonomy/data/Dockerfiles/agent/Dockerfile:10`
- **Impact:** User-supplied string passed verbatim to `RUN /bin/sh -c "${PRE_INSTALL_COMMAND}"`. No sanitization.

### H7. `preexec_fn=os.setsid` — unsafe in threaded programs, deprecated
- **Files:** `connection.py:1137`, `deployments/.../tendermint.py:139`, `localhost/.../tendermint.py:137`, `slow_tendermint_server/tendermint.py:136`
- **Impact:** `preexec_fn` runs between `fork()` and `exec()` in child process where only async-signal-safe functions are allowed. Replace with `start_new_session=True`.

### H8. HTTP 200 returned on error from all Flask endpoints
- **Files:** `deployments/Dockerfiles/tendermint/app.py:288-316`, `autonomy/deploy/generators/localhost/tendermint/app.py:295-337`
- **Impact:** `/app_hash`, `/gentle_reset`, `/hard_reset` all return HTTP 200 with an error body on failure. Callers checking HTTP status codes cannot distinguish success from failure.

---

## Medium (Architecture / Code Quality)

### M1. `base.py` is a 3,924-line god-file with 40+ classes spanning 6 domains
- **File:** `packages/valory/skills/abstract_round_abci/base.py`
- **Impact:** Contains transaction/payload layer, blockchain model, synchronized state, consensus rounds, FSM orchestration, and slashing/offences. The slashing subsystem alone (lines 2945-3924) is a large secondary concern that could be its own module. `BaseSynchronizedData` contains application-specific properties (`safe_contract_address`, `keeper_randomness`) that belong in `transaction_settlement_abci`.

### M2. Skill imports constant from connection module
- **File:** `packages/valory/skills/abstract_round_abci/base.py:63`
- **Impact:** `from packages.valory.connections.abci.connection import MAX_READ_IN_BYTES`. Skills can depend on connections (declared in `skill.yaml`), so this is not a layering violation per se. However, importing a transport-level buffer size constant creates tight coupling to a specific connection's implementation detail. If `MAX_READ_IN_BYTES` were defined in the protocol or a shared constants module, the skill would be decoupled from the connection's internals.

### M3. `ABCIApplicationServicer` — 15 near-identical gRPC handler methods (~450 lines of boilerplate)
- **File:** `packages/valory/connections/abci/connection.py:261-775`
- **Impact:** Every handler follows the exact same pattern. Could be reduced to ~30 lines with a dispatch table.

### M4. `_MetaAbciApp` metaclass injects background round at import time, order-sensitive
- **File:** `packages/valory/skills/abstract_round_abci/base.py:2042-2247`
- **Impact:** `_add_pending_offences_bg_round` fires on the *first* concrete `AbciApp` encountered. Import order determines which class gets modified. In tests, classes defined before production ones may behave differently.

### M5. `deplopyment_type` typo baked into public API
- **Files:** `autonomy/deploy/base.py:158,474,618,634`, `autonomy/deploy/build.py:81`, test files
- **Impact:** Propagated across 8+ references. Renaming is a breaking change. Should be fixed with an alias for backward compat.

### M6. `COMPONENT_CONFIGS` dict defined independently in 3 modules
- **Files:** `autonomy/configurations/base.py:55`, `autonomy/configurations/loader.py:39`, `autonomy/deploy/base.py:88`
- **Impact:** Adding a new component type requires 3 coordinated edits.

### M7. Flask server `create_server()` discards TendermintNode reference
- **Files:** `autonomy/deploy/generators/localhost/tendermint/app.py:354-357`, `deployments/Dockerfiles/tendermint/app.py:333-336`
- **Impact:** `tendermint_node` assigned to `_` and discarded. No shutdown hook. Clean Flask shutdown leaves Tendermint subprocess and monitoring thread running.

### M8. `docker.from_env()` clients created without closing
- **Files:** `plugins/aea-test-autonomy/aea_test_autonomy/docker/base.py:97`, `fixture_helpers.py` (15+ instances)
- **Impact:** Each call creates a new DockerClient with HTTP connection pool. Never closed. Accumulates connections during test runs.

### M9. `asyncio.create_task()` task reference not stored
- **File:** `packages/valory/connections/abci/connection.py:842`
- **Impact:** Task may be garbage-collected before completion. `disconnect()` cannot cancel/await the server task.

### M10. 11 suppressed `safety` CVEs without documentation
- **File:** `tox.ini:546`
- **Impact:** Each `safety check -i XXXXX` should have a comment explaining why the CVE is safe to ignore.

### M11. `curl | sh` and unchecked binary downloads in Dockerfiles
- **Files:** `deployments/Dockerfiles/autonomy/Dockerfile:10`, `autonomy-user/Dockerfile:21`, `tendermint/install.sh`
- **Impact:** Docker and Tendermint binaries downloaded and executed without checksum verification. MITM risk during image builds.

### M12. Node.js 16 EOL base image
- **File:** `deployments/Dockerfiles/hardhat/Dockerfile:1`
- **Impact:** `node:16.7.0` reached EOL September 2023. Contains known unpatched vulnerabilities.

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
