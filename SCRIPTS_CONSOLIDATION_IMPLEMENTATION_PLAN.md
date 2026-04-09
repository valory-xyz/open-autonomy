# Scripts Consolidation — Implementation Plan

Phased rollout plan for the changes described in `SCRIPTS_CONSOLIDATION_REPORT.md`.

### Ground rules

1. **Local CI first.** Every phase must pass the repo's full CI suite locally before creating a draft PR. Run the full common/main workflow checks (linters, hash checks, copyright, tests) locally via `tox` or `make` and confirm they pass. Do not rely on remote CI to catch issues — fix them before pushing.

2. **Fresh branch from latest main.** For every repo (except the 5 agent repos which have existing cleanup branches), always start from a clean state:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b <branch-name>
   ```
   Agent repos (optimus, trader, meme-ooorr, IEKit, market-creator) already have `chore/repo-cleanup` branches — rebase those onto latest main instead of creating new branches.

---

## Phase 0: Preparation

**Scope:** No code changes. Alignment and setup.

- [ ] Get sign-off on SCRIPTS_CONSOLIDATION_REPORT.md from team
- [ ] Decide on version numbers for new/renamed packages
- [ ] Verify tomte's `check-copyright`, `check-doc-links`, `freeze-dependencies` produce identical output to the local scripts (smoke test)

**Duration:** 1 day

---

## Phase 1: tomte enhancements

**Scope:** Enhance tomte to close the feature gaps identified during comparison. Three enhancements are needed before tomte can replace the local scripts.

**Repo:** `valory-xyz/tomte`

### Gap analysis (completed)

| Script | Gap | Status |
|--------|-----|--------|
| `check-copyright` | Only supports single author ("Valory AG"). open-aea has 751 files with dual "Valory AG" + "Fetch.AI Limited" headers. Also hardcodes scan paths. | Needs enhancement |
| `check-doc-links` | open-aea's version is fundamentally different (validates internal links, images, markdown). open-autonomy's is close to tomte's but has repo-specific skip lists hardcoded. | Needs `--http-skips` / `--url-skips` already exist as CLI options — sufficient for open-autonomy. open-aea keeps its own script (different tool). |
| `freeze-dependencies` | Tomte doesn't filter out the framework package itself. open-aea filters `aea`, open-autonomy filters `open-autonomy`. Without filtering, liccheck checks the framework against itself. | Needs enhancement |
| `check-spelling` | Tomte's version is sufficient. | No changes needed |

### Enhancement 1: `check-copyright` — multiple authors + configurable scan paths

**Current:** `tomte check-copyright --author "Valory AG"`

**Proposed:**
```bash
# Multiple authors (repeatable flag)
tomte check-copyright --author "Valory AG" --author "Fetch.AI Limited"

# Configurable scan paths (repeatable flag, overrides defaults)
tomte check-copyright --author "Valory AG" --scan-path aea --scan-path packages --scan-path plugins

# Combined (for open-aea)
tomte check-copyright \
  --author "Valory AG" \
  --author "Fetch.AI Limited" \
  --scan-path aea --scan-path packages --scan-path plugins \
  --scan-path scripts --scan-path tests --scan-path benchmark --scan-path examples
```

**Implementation:**
- [ ] Make `--author` repeatable (`multiple=True` in Click)
- [ ] Support multiple copyright header patterns (one per author)
- [ ] In check mode: validate that at least one recognized author header is present
- [ ] In fix mode: update year ranges for all recognized author lines
- [ ] Add `--scan-path` repeatable option (defaults to `packages/{author}`, `tests`, `scripts` if not provided)
- [ ] Support mixed headers (Valory + FetchAI on same file) without error
- [ ] Tests for multi-author scenarios

### Enhancement 2: `freeze-dependencies` — exclude package filter

**Current:** `tomte freeze-dependencies --output-path requirements.txt`

**Proposed:**
```bash
# Exclude framework package from output
tomte freeze-dependencies --output-path requirements.txt --exclude-package open-autonomy
tomte freeze-dependencies --output-path requirements.txt --exclude-package open-aea
```

**Implementation:**
- [ ] Add `--exclude-package` repeatable option
- [ ] Filter out matching lines from pip freeze output (regex: `^{package}(==.*| .*)?$`)
- [ ] Tests for exclusion

### Enhancement 3: `check-doc-links` — no code changes needed

Tomte's `check-doc-links` already accepts `--http-skips` and `--url-skips` as CLI options. open-autonomy can pass its repo-specific skip lists via tox.ini. No tomte changes required.

**Note:** open-aea's `check_doc_links.py` is a fundamentally different tool (validates internal links, images, markdown structure) and will NOT be replaced by tomte. It moves to `open-aea-ci-helpers` instead.

### Tasks

- [ ] Implement Enhancement 1 (check-copyright multi-author + scan paths)
- [ ] Implement Enhancement 2 (freeze-dependencies exclude filter)
- [ ] Add/update tests for both enhancements
- [ ] Run tomte's own CI locally and confirm it passes
- [ ] Create draft PR for tomte
- [ ] Release new tomte version (e.g., `0.6.3`)

**Duration:** 2-3 days

---

## Phase 2: open-aea

**Scope:** Create the new `open-aea-ci-helpers` plugin. Switch open-aea's own `tox.ini` to use tomte + aea-ci instead of local scripts. Delete migrated/obsolete scripts.

**Repo:** `valory-xyz/open-aea`

### Step 2a: Create `open-aea-ci-helpers` plugin

- [ ] Create `plugins/aea-ci-helpers/` directory structure
- [ ] Create `setup.py` with PyPI name `open-aea-ci-helpers`
- [ ] Migrate scripts as Click subcommands:
  - [ ] `aea-ci check-ipfs-pushed` (from `scripts/check_ipfs_hashes_pushed.py`)
  - [ ] `aea-ci check-imports` (from `scripts/check_imports_and_dependencies.py`)
  - [ ] `aea-ci check-pyproject` (from `scripts/check_pyproject_and_toxini.py`)
  - [ ] `aea-ci check-pkg-versions` (from `scripts/check_package_versions_in_docs.py`)
  - [ ] `aea-ci generate-api-docs` (from `scripts/generate_api_docs.py`)
  - [ ] `aea-ci generate-pkg-list` (from `scripts/generate_package_list.py`)
- [ ] Add tests for new commands
- [ ] Verify all linters pass

### Step 2b: Switch open-aea's tox.ini

- [ ] Update tox environments to install `open-aea-ci-helpers` (from local `plugins/aea-ci-helpers`)
- [ ] Replace `scripts/check_copyright_notice.py` invocations with `tomte check-copyright`
- [ ] Replace `scripts/check_doc_links.py` invocations with `tomte check-doc-links`
- [ ] Replace `scripts/freeze_dependencies.py` invocations with `tomte freeze-dependencies`
- [ ] Replace `scripts/check_ipfs_hashes_pushed.py` invocations with `aea-ci check-ipfs-pushed`
- [ ] Replace `scripts/check_imports_and_dependencies.py` invocations with `aea-ci check-imports`
- [ ] Replace remaining script invocations with corresponding `aea-ci` commands
- [ ] Verify CI passes

### Step 2c: Delete migrated/obsolete scripts

- [ ] Delete `scripts/check_copyright_notice.py` (-> tomte)
- [ ] Delete `scripts/check_doc_links.py` (-> tomte)
- [ ] Delete `scripts/freeze_dependencies.py` (-> tomte)
- [ ] Delete `scripts/check_ipfs_hashes_pushed.py` (-> aea-ci)
- [ ] Delete `scripts/check_imports_and_dependencies.py` (-> aea-ci)
- [ ] Delete `scripts/check_pyproject_and_toxini.py` (-> aea-ci)
- [ ] Delete `scripts/check_package_versions_in_docs.py` (-> aea-ci)
- [ ] Delete `scripts/generate_api_docs.py` (-> aea-ci)
- [ ] Delete `scripts/generate_package_list.py` (-> aea-ci)
- [ ] Delete `scripts/check_pipfile_and_toxini.py` (obsolete)
- [ ] Delete `scripts/spell-check.sh` (-> tomte)
- [ ] Delete `scripts/log_parser.py` (unused)
- [ ] Delete `scripts/check_doc_ipfs_hashes.py` (-> aea-helpers `check-doc-hashes`)
- [ ] Delete `scripts/check_dependencies.py` (-> aea-helpers `check-dependencies`)

### Step 2d: Local CI verification

Run the full CI suite locally before creating the PR:

```bash
make clean
make formatters
make code-checks
make security
make common-checks-1
make common-checks-2
make test
```

Fix any failures before pushing.

### Step 2e: Release

- [ ] Create draft PR, confirm remote CI passes
- [ ] Release `open-aea-ci-helpers` to PyPI (initial version, e.g., `0.1.0`)
- [ ] Release `open-aea` with the tox.ini changes (patch version bump)

**Duration:** 2-3 days

---

## Phase 3: open-autonomy

**Scope:** Switch open-autonomy to use tomte + `open-aea-ci-helpers` instead of local scripts. Rename `aea-helpers` to `open-aea-helpers` on PyPI. Delete duplicate scripts.

**Repo:** `valory-xyz/open-autonomy`

### Step 3a: Switch open-autonomy's tox.ini

- [ ] Add `open-aea-ci-helpers` as a tox dep
- [ ] Replace `scripts/check_copyright.py` invocations with `tomte check-copyright`
- [ ] Replace `scripts/check_doc_links.py` invocations with `tomte check-doc-links`
- [ ] Replace `scripts/freeze_dependencies.py` invocations with `tomte freeze-dependencies`
- [ ] Replace `scripts/check_ipfs_hashes_pushed.py` invocations with `aea-ci check-ipfs-pushed`
- [ ] Replace `scripts/generate_api_documentation.py` invocations with `aea-ci generate-api-docs`
- [ ] Replace `scripts/generate_package_list.py` invocations with `aea-ci generate-pkg-list`
- [ ] Verify CI passes

### Step 3b: Delete duplicate scripts

- [ ] Delete `scripts/check_copyright.py`
- [ ] Delete `scripts/check_doc_links.py`
- [ ] Delete `scripts/freeze_dependencies.py`
- [ ] Delete `scripts/check_ipfs_hashes_pushed.py`
- [ ] Delete `scripts/generate_api_documentation.py`
- [ ] Delete `scripts/generate_package_list.py`

### Step 3c: Rename aea-helpers -> open-aea-helpers on PyPI

- [ ] Update `plugins/aea-helpers/setup.py`: change `name="aea-helpers"` to `name="open-aea-helpers"`
- [ ] Python package (`aea_helpers`) and CLI command (`aea-helpers`) remain unchanged
- [ ] Verify linters and tests pass
- [ ] Publish `open-aea-helpers` to PyPI (same version as current `aea-helpers`, e.g., `0.21.17`)
- [ ] Publish a final `aea-helpers` version on PyPI that depends on `open-aea-helpers` (bridge package for backwards compat, optional)

### Step 3d: Local CI verification

Run the full CI suite locally before creating the PR:

```bash
make clean
tomte format-code
tomte check-code
make security
make common-checks-1
make common-checks-2
make test
```

Fix any failures before pushing.

### Step 3e: Release

- [ ] Create draft PR, confirm remote CI passes
- [ ] Release `open-aea-helpers` to PyPI (renamed from `aea-helpers`)
- [ ] Release `open-autonomy` with all changes
- [ ] Delete `SCRIPTS_CONSOLIDATION_REPORT.md` and `SCRIPTS_CONSOLIDATION_IMPLEMENTATION_PLAN.md` from repo

**Duration:** 1-2 days

---

## Phase 4: Mech repos (6 repos)

**Scope:** Update dependency references from `aea-helpers` to `open-aea-helpers` and from local scripts (if any) to `tomte` / `aea-ci`.

**Repos:**
1. `valory-xyz/mech`
2. `valory-xyz/mech-interact`
3. `valory-xyz/mech-client`
4. `valory-xyz/mech-predict`
5. `valory-xyz/mech-server`
6. `valory-xyz/mech-agents-fun`

### Per-repo tasks

- [ ] Update `pyproject.toml`: `aea-helpers==X.Y.Z` -> `open-aea-helpers==X.Y.Z`
- [ ] Update `tox.ini`: any `aea-helpers` references
- [ ] Bump `open-aea` and `open-autonomy` version pins if needed
- [ ] Run full CI locally (`make all-checks` or equivalent) and fix any failures
- [ ] Create draft PR per repo only after local CI passes

**Duration:** 1 day (batch all 6)

---

## Phase 5: Library repos (3 repos)

**Scope:** Same dependency update as Phase 4.

**Repos:**
1. `valory-xyz/genai`
2. `valory-xyz/funds-manager`
3. `valory-xyz/kv-store`

### Per-repo tasks

- [ ] Update `pyproject.toml`: `aea-helpers==X.Y.Z` -> `open-aea-helpers==X.Y.Z`
- [ ] Update `tox.ini`: any `aea-helpers` references
- [ ] Bump `open-aea` and `open-autonomy` version pins if needed
- [ ] Run full CI locally and fix any failures
- [ ] Create draft PR per repo only after local CI passes

**Duration:** 0.5 day (batch all 3)

---

## Phase 6: Agent repos (5 repos)

**Scope:** Same dependency update as Phase 4. These repos also have the cleanup PRs from the earlier effort that may need rebasing.

**Repos:**
1. `valory-xyz/optimus`
2. `valory-xyz/trader`
3. `valory-xyz/meme-ooorr`
4. `valory-xyz/IEKit`
5. `valory-xyz/market-creator`

### Per-repo tasks

- [ ] Update `pyproject.toml`: `aea-helpers==X.Y.Z` -> `open-aea-helpers==X.Y.Z`
- [ ] Update `tox.ini`: any `aea-helpers` references
- [ ] Update `Makefile`: any `aea-helpers` CLI invocations (these already use `aea-helpers` CLI — the binary name doesn't change, only the pip package name)
- [ ] Bump `open-aea` and `open-autonomy` version pins if needed
- [ ] Rebase existing cleanup PRs if still open
- [ ] Run full CI locally (`make all-checks` or equivalent) and fix any failures
- [ ] Create draft PR per repo only after local CI passes

**Duration:** 1 day (batch all 5)

---

## Phase 7: Cleanup

**Scope:** Final housekeeping.

- [ ] Verify old `aea-helpers` PyPI package has a deprecation notice or redirect
- [ ] Remove `SCRIPTS_CONSOLIDATION_REPORT.md` and this plan from open-autonomy
- [ ] Update CLAUDE.md / README in open-aea and open-autonomy to document the new plugin structure
- [ ] Close any related tracking issues

**Duration:** 0.5 day

---

## Summary

| Phase | Repo(s) | What | Duration |
|-------|---------|------|----------|
| 0 | — | Preparation & sign-off | 1 day |
| 1 | tomte | Verify/fix feature parity | 1-3 days |
| 2 | open-aea | Create open-aea-ci-helpers, switch to tomte, delete scripts | 2-3 days |
| 3 | open-autonomy | Switch to tomte + aea-ci, rename aea-helpers, delete duplicates | 1-2 days |
| 4 | 6 mech repos | Update aea-helpers -> open-aea-helpers | 1 day |
| 5 | 3 library repos | Same | 0.5 day |
| 6 | 5 agent repos | Same + rebase cleanup PRs | 1 day |
| 7 | All | Final cleanup | 0.5 day |
| **Total** | | | **7-11 days** |

### Critical path

```
Phase 0 -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4/5/6 (parallel) -> Phase 7
```

Phases 4, 5, and 6 can run in parallel once Phase 3 is released.
