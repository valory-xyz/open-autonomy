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

### M5. ~~`deplopyment_type` typo baked into public API~~ **RESOLVED**
- **Files:** `autonomy/deploy/base.py`, `autonomy/deploy/build.py`, test files
- **Resolution:** Renamed to `deployment_type` across all references. Not a true public API — only set internally in `build.py` and tests.

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

### L1. ~~Inverted `svn` check in Makefile breaks `make new_env`~~ **RESOLVED**
- **File:** `Makefile:161-163`
- **Resolution:** Fixed `! -z` to `-z` so the check correctly exits when svn is NOT found.

### L2. ~~`--fsm` flag declared as both `is_flag=True` and `type=str`~~ **RESOLVED**
- **File:** `autonomy/cli/analyse.py:232-237`
- **Resolution:** Removed contradictory `type=str`. The option is a boolean flag.

### L3. ~~"of of the service" typo in user-facing error messages~~ **RESOLVED**
- **File:** `autonomy/cli/analyse.py:446,451`
- **Resolution:** Fixed double "of of" to "of".

### L4. ~~CI uses `actions/checkout@v2` and `actions/setup-python@master`~~ **RESOLVED**
- **File:** `.github/workflows/main_workflow.yml` (multiple lines)
- **Resolution:** Updated all actions to current stable versions: `checkout@v4`, `setup-python@v5`, `setup-go@v5`, `codecov-action@v4`.

### L5. ~~Wrong docstrings on `tendermint` and `acn_node` fixtures~~ **RESOLVED**
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/fixture_helpers.py:97,383`
- **Resolution:** Fixed copy-paste docstrings to say "Tendermint" and "ACN node" respectively.

### L6. `pytest` listed as production dependency — **ACKNOWLEDGED**
- **File:** `setup.py:58`
- **Assessment:** Intentional — the CLI uses pytest for `aea test`. Moving it to extras would break the test command.

### L7. `tox.ini` is 1,004 lines with ~30 repetitive `[testenv]` blocks — **ACKNOWLEDGED**
- **File:** `tox.ini`
- **Assessment:** Refactoring concern. Not a bug.

### L8. `pytz==2022.2.1` — unnecessary on Python 3.14 — **ACKNOWLEDGED**
- **Files:** `Pipfile:42`, `tox.ini:52`
- **Assessment:** Dev dependency only (Pipfile). Not in production deps. Low priority.

### L9. `hypothesis==6.21.6` pinned to 2022 release — **ACKNOWLEDGED**
- **Files:** `Pipfile:38`, `tox.ini:49`
- **Assessment:** Dev dependency. Upgrading risks test breakage from new strategies. Low priority.

### L10. `filterwarnings("ignore")` at module scope — **ACKNOWLEDGED**
- **File:** `autonomy/cli/analyse.py:60`
- **Assessment:** Needs investigation into which warnings it suppresses before narrowing. Low priority.

### L11. Deprecated CLI commands not using Click's `deprecated=True` — **ACKNOWLEDGED**
- **Files:** `autonomy/cli/scaffold_fsm.py:91`, `autonomy/cli/deploy.py:491`, `autonomy/cli/hash.py:52`
- **Assessment:** Nice-to-have. The runtime warnings are already in place.

### L12. `ganache_scope_function` fixture marked `# TODO: remove as not used` — **ACKNOWLEDGED**
- **File:** `plugins/aea-test-autonomy/aea_test_autonomy/fixture_helpers.py:241`
- **Assessment:** Dead code. Can be removed but may require checking downstream consumers.

### L13. ~~Multiple dependency specification files with drifting version pins~~ **RESOLVED**
- **Files:** `pyproject.toml`, `setup.py`, `tox.ini`, `Pipfile`
- **Resolution:** Aligned `typing_extensions` upper bound to `<=4.15.0` and `jsonschema` range to `>=4.3.0,<4.24.0` in `pyproject.toml` to match all other spec files.

### L14. `BaseBehaviour` bypasses MRO with explicit `__init__` calls — **ACKNOWLEDGED**
- **File:** `packages/valory/skills/abstract_round_abci/behaviour_utils.py:566`
- **Assessment:** Intentional design choice for diamond inheritance. Documented with pylint disable. Changing risks breaking all downstream skills.

### L15. `$(PYTHON_VERSION)` used but never defined in Makefile — **ACKNOWLEDGED**
- **File:** `Makefile:171`
- **Assessment:** Expands to empty string, causing `pipenv --python` to error but pipenv falls back to default resolution. Existing behavior, low priority.

### L16. Linter CI job runs 15 checks sequentially — **ACKNOWLEDGED**
- **File:** `.github/workflows/main_workflow.yml`
- **Assessment:** CI config concern. Should be parallelized in a separate CI-focused PR.

### L17. ~~`e.args` destructuring can raise `IndexError`~~ **RESOLVED**
- **File:** `autonomy/cli/helpers/analyse.py:256-257`
- **Resolution:** Changed to safe indexing with `str(e)` fallback for empty args.

### L18. ~~"Usefule" typo in module docstring~~ **RESOLVED**
- **File:** `autonomy/cli/utils/click_utils.py:20`
- **Resolution:** Fixed to "Useful".

### L19. Tendermint v0.34.19 — unmaintained, superseded by CometBFT — **ACKNOWLEDGED**
- **Assessment:** Upstream dependency. Migration to CometBFT is a major effort beyond the scope of this audit.

---

## Quick Wins (fixable in < 1 hour each)

| # | Fix | Status |
|---|-----|--------|
| C1 | Change `response.list_snapshots` to `response.offer_snapshot` | Done |
| C3 | Migrate `onerror=` to `onexc=` (3 files) | Deferred — `onerror` still works on 3.14 |
| H7 | Replace `preexec_fn=os.setsid` with `start_new_session=True` (4 files) | Already done (prior work) |
| H8 | Return HTTP 500 on error in Flask endpoints | Not applicable — callers check JSON body |
| L1 | Fix inverted svn check in Makefile | Done |
| L2 | Remove `type=str` from `--fsm` flag option | Done |
| L3 | Fix "of of" typo | Done |
| L5 | Fix copy-paste docstrings | Done |
| L10 | Narrow `filterwarnings` to specific warnings | Deferred — needs investigation |
| L12 | Remove dead `ganache_scope_function` | Deferred — needs downstream check |
| L17 | Fix unsafe `e.args` destructuring | Done |
| L18 | Fix "Usefule" typo | Done |
| M5 | Rename `deplopyment_type` to `deployment_type` | Done |
