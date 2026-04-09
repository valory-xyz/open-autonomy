# Scripts Consolidation Report: open-aea & open-autonomy

## Current State

### Tool landscape today

There are **four** tools that downstream repos depend on:

| Tool | What it does | Where it lives | Dep chain |
|------|-------------|----------------|-----------|
| **`autonomy` CLI** | Package management, FSM analysis, deployments | `open-autonomy/autonomy/cli/` | `open-autonomy -> open-aea` |
| **`aea-helpers`** | Agent runtime + CI helpers | `open-autonomy/plugins/aea-helpers/` | `aea-helpers -> open-autonomy -> open-aea` |
| **`aea-test-autonomy`** | Test infrastructure (Docker fixtures, base classes) | `open-autonomy/plugins/aea-test-autonomy/` | `aea-test-autonomy -> open-autonomy` |
| **`tomte`** | Linting meta-package + CLI (black, isort, flake8, mypy, copyright, doc-links, etc.) | Separate repo (`valory-xyz/tomte`) | No aea/autonomy dep, MIT licensed |

Downstream repos use these cleanly: `tomte` for code quality, `autonomy` CLI for package ops, `aea-helpers` for runtime/CI, `aea-test-autonomy` for test infra. **No downstream repo calls `scripts/` directly.**

The problem is that `open-aea` and `open-autonomy` themselves still have `scripts/` directories with ~30 scripts between them, many duplicated — and some are near-identical copies of what `tomte` already provides.

---

### Scripts inventory

#### open-aea/scripts/ (22 files)

| Script | Purpose | Invoked by | Migration target |
|--------|---------|-----------|-----------------|
| `check_copyright_notice.py` | Validate/fix copyright headers | `tox -e check-copyright`, `tox -e fix-copyright` | **Use `tomte check-copyright`** (tomte already has this) |
| `check_doc_links.py` | Validate doc HTTP links are reachable | `tox -e check-doc-links-hashes` | **Use `tomte check-doc-links`** (tomte already has this) |
| `check_doc_ipfs_hashes.py` | Validate/fix IPFS hashes in docs | `tox -e fix-doc-hashes` | Already in aea-helpers as `check-doc-hashes` |
| `check_ipfs_hashes_pushed.py` | Verify IPFS hashes are reachable on gateway | `tox -e check-doc-links-hashes` | `open-aea-ci-helpers` |
| `check_dependencies.py` | Verify installed deps match Pipfile | `tox -e dependencies-check` | Already in aea-helpers as `check-dependencies` |
| `check_imports_and_dependencies.py` | Verify imports match declared deps | `tox -e dependencies-check` | `open-aea-ci-helpers` |
| `check_package_versions_in_docs.py` | Verify package IDs in docs match configs | `tox -e package-version-checks` | `open-aea-ci-helpers` |
| `check_pipfile_and_toxini.py` | Verify Pipfile and tox.ini specs match | Development use | **Delete** (obsolete — repos moved to uv/pyproject.toml) |
| `check_pyproject_and_toxini.py` | Verify pyproject.toml and tox.ini align | GitHub Actions workflow | `open-aea-ci-helpers` |
| `freeze_dependencies.py` | Freeze pip env to requirements.txt | `tox -e liccheck` | **Use `tomte freeze-dependencies`** (tomte already has this) |
| `generate_api_docs.py` | Generate API docs from source | `tox -e check-api-docs`, `tox -e generate-api-documentation` | `open-aea-ci-helpers` |
| `generate_package_list.py` | Generate markdown table of packages | `tox -e fix-doc-hashes` | `open-aea-ci-helpers` |
| `bump_aea_version.py` | Bump version across codebase | Release process (manual) | Keep in open-aea (repo-specific) |
| `update_package_versions.py` | Update package versions + rehash | Release process (manual) | Keep in open-aea (repo-specific) |
| `update_plugin_versions.py` | Update plugin versions | Release process (manual) | Keep in open-aea (repo-specific) |
| `deploy_to_registry.py` | Deploy packages to AEA registry | Manual/CI deployment | Keep in open-aea (repo-specific) |
| `publish_packages_to_local_registry.py` | Publish to IPFS | Manual deployment | Keep in open-aea (repo-specific) |
| `spell-check.sh` | Markdown spell check | `tox -e spell-check` | **Delete** (use `tomte check-spelling`) |
| `whitelist.py` | Vulture dead code allowlist | `tox -e vulture` | Keep (data file, not a script) |
| `log_parser.py` | Parse profiling logs | Standalone utility | **Delete** (unused in CI) |
| `install.sh` / `install.ps1` | End-user installers | Direct download | Keep in open-aea |
| `acn/` | ACN node runner | Manual deployment | Keep in open-aea |
| `update_symlinks_cross_platform.py` | Create test fixture symlinks | GitHub Actions | Keep in open-aea (repo-specific) |

#### open-autonomy/scripts/ (11 files)

| Script | Purpose | Invoked by | Migration target |
|--------|---------|-----------|-----------------|
| `check_copyright.py` | Validate/fix copyright headers | `tox -e check-copyright`, `tox -e fix-copyright` | **Use `tomte check-copyright`** (DUPLICATE — delete) |
| `check_doc_links.py` | Validate doc HTTP links | `tox -e check-doc-links` | **Use `tomte check-doc-links`** (DUPLICATE — delete) |
| `check_ipfs_hashes_pushed.py` | Verify IPFS hashes on gateway | `tox -e check-ipfs-hashes-pushed` | **DUPLICATE** -> `open-aea-ci-helpers` |
| `check_third_party_hashes.py` | Cross-ref hashes with open-aea | `tox -e check-packages` | `open-aea-ci-helpers` |
| `freeze_dependencies.py` | Freeze pip env | Not directly invoked | **Use `tomte freeze-dependencies`** (DUPLICATE — delete) |
| `generate_api_documentation.py` | Generate API docs | `tox -e check-api-docs`, `tox -e generate-api-documentation` | **DUPLICATE** -> `open-aea-ci-helpers` |
| `generate_package_list.py` | Generate package markdown | `tox -e generate-package-list` | **DUPLICATE** -> `open-aea-ci-helpers` |
| `generate_contract_list.py` | Generate contract addresses doc | Standalone | Keep (OA-specific) |
| `whitelist.py` | Vulture allowlist | `tox -e vulture` | Keep (data file) |
| `pre-add` / `pre-push` | Git hooks | Manual git hook install | Keep or move to `.githooks/` |
| `RELEASE_PROCESS.md` | Release documentation | N/A (docs) | Keep |

---

## Migration strategy

### Step 1: Switch to tomte for overlapping scripts

`tomte` already provides its own standalone implementations of these tools (inside `tomte.tools.*`). The local `scripts/` copies in both repos are near-identical duplicates. Downstream repos already use `tomte` for these successfully.

**Scripts to replace with tomte:**

| Local script | Replace with | Notes |
|-------------|-------------|-------|
| `check_copyright_notice.py` (open-aea) | `tomte check-copyright` | Downstream repos already use this |
| `check_copyright.py` (open-autonomy) | `tomte check-copyright` | Same |
| `check_doc_links.py` (both repos) | `tomte check-doc-links` | Same |
| `freeze_dependencies.py` (both repos) | `tomte freeze-dependencies` | Same |
| `spell-check.sh` (open-aea) | `tomte check-spelling` | Same |

**Action:** Update `tox.ini` in both repos to call `tomte <command>` instead of `scripts/<script>.py`, then delete the local copies.

### Step 2: Create `open-aea-ci-helpers` plugin

For scripts that tomte does NOT cover, create a new plugin in `open-aea/plugins/`:

```
open-aea/
  plugins/
    aea-ci-helpers/                    # Plugin directory name
      aea_ci_helpers/                  # Python package name
        __init__.py
        cli.py                         # Click CLI entry point
        check_ipfs_pushed.py           # From check_ipfs_hashes_pushed.py
        check_imports.py               # From check_imports_and_dependencies.py
        check_pyproject.py             # From check_pyproject_and_toxini.py
        check_pkg_versions.py          # From check_package_versions_in_docs.py
        generate_api_docs.py           # From generate_api_docs.py
        generate_pkg_list.py           # From generate_package_list.py
      setup.py
```

**Naming convention (following Valory's `open-` prefix convention):**

| | Value |
|---|---|
| Plugin directory | `aea-ci-helpers` |
| Python package | `aea_ci_helpers` |
| **PyPI package** | **`open-aea-ci-helpers`** |
| CLI command | `aea-ci` |

**Commands:**
- `aea-ci check-ipfs-pushed` — verify IPFS hashes are reachable on gateway
- `aea-ci check-imports` — verify imports match declared dependencies
- `aea-ci check-pyproject` — verify pyproject.toml and tox.ini alignment
- `aea-ci check-pkg-versions` — verify package versions in docs match configs
- `aea-ci generate-api-docs` — generate API documentation from source
- `aea-ci generate-pkg-list` — generate markdown table of packages

**Dependencies:** `click`, `requests`, `pyyaml`, `open-aea` (lightweight — no autonomy dependency)

### Step 3: Update open-autonomy to consume the new plugin

1. Add `open-aea-ci-helpers` as a tox dependency in open-autonomy
2. Update `tox.ini` to call `aea-ci <command>` instead of `scripts/<script>.py`
3. Delete the duplicated scripts from `open-autonomy/scripts/`
4. Keep OA-specific: `check_third_party_hashes.py`, `generate_contract_list.py`, `whitelist.py`, git hooks

### Step 4: Delete obsolete scripts

| Script | Repo | Reason |
|--------|------|--------|
| `check_pipfile_and_toxini.py` | open-aea | Pipfile is dead, repos use uv/pyproject.toml |
| `spell-check.sh` | open-aea | Replaced by `tomte check-spelling` |
| `log_parser.py` | open-aea | Unused standalone utility |

---

## Dependency chain after refactor

```
tomte                       (independent, MIT licensed, no aea/autonomy dep)
open-aea-ci-helpers     ->  open-aea (only)
aea-helpers             ->  open-autonomy -> open-aea
open-aea-test-autonomy  ->  open-autonomy -> open-aea

open-aea uses:         tomte + open-aea-ci-helpers (no circular dep)
open-autonomy uses:    tomte + open-aea-ci-helpers + aea-helpers + open-aea-test-autonomy
downstream repos use:  tomte + open-aea-ci-helpers (optional) + aea-helpers + open-aea-test-autonomy
```

No circular dependencies.

---

## What stays in scripts/ after cleanup

### open-aea/scripts/ (9 files kept)

| Script | Reason to keep |
|--------|---------------|
| `bump_aea_version.py` | Release process, repo-specific |
| `update_package_versions.py` | Release process, repo-specific |
| `update_plugin_versions.py` | Release process, repo-specific |
| `deploy_to_registry.py` | Deployment, repo-specific |
| `publish_packages_to_local_registry.py` | Deployment, repo-specific |
| `update_symlinks_cross_platform.py` | CI fixture setup, repo-specific |
| `whitelist.py` | Vulture data file |
| `install.sh` / `install.ps1` | End-user installers |
| `acn/` | ACN node binary |

### open-autonomy/scripts/ (5 files kept)

| Script | Reason to keep |
|--------|---------------|
| `check_third_party_hashes.py` | OA-specific (cross-refs with open-aea) |
| `generate_contract_list.py` | OA-specific (fetches from registries) |
| `whitelist.py` | Vulture data file |
| `pre-add` / `pre-push` | Git hooks |
| `RELEASE_PROCESS.md` | Documentation |

---

## Effort estimate

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| Step 1: Switch to tomte | 1 day | None (tomte already installed) |
| Step 2: Create open-aea-ci-helpers | 2-3 days | None |
| Step 3: Remove OA duplicates | 1 day | Step 2 |
| Step 4: Delete obsolete | 1 hour | Step 1 |
| **Total** | **4-5 days** | |
