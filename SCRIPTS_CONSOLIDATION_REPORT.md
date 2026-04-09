# Scripts Consolidation Report: open-aea & open-autonomy

## Current State

### Tool landscape today

There are **four** tools that downstream repos depend on:

| Tool | What it does | Where it lives | Dep chain |
|------|-------------|----------------|-----------|
| **`autonomy` CLI** | Package management, FSM analysis, deployments | `open-autonomy/autonomy/cli/` | `open-autonomy -> open-aea` |
| **`aea-helpers`** | Agent runtime + CI helpers | `open-autonomy/plugins/aea-helpers/` | `aea-helpers -> open-autonomy -> open-aea` |
| **`aea-test-autonomy`** | Test infrastructure (Docker fixtures, base classes) | `open-autonomy/plugins/aea-test-autonomy/` | `aea-test-autonomy -> open-autonomy` |
| **`tomte`** | Linting meta-package (black, isort, flake8, mypy, etc.) | Separate repo (`valory-xyz/tomte`) | No aea/autonomy dep |

Downstream repos use these cleanly: `tomte` for code quality, `autonomy` CLI for package ops, `aea-helpers` for runtime/CI, `aea-test-autonomy` for test infra. **No downstream repo calls `scripts/` directly.**

The problem is that `open-aea` and `open-autonomy` themselves still have `scripts/` directories with ~30 scripts between them, many duplicated.

---

### Scripts inventory

#### open-aea/scripts/ (22 files)

| Script | Purpose | Invoked by | Could migrate? |
|--------|---------|-----------|----------------|
| `check_copyright_notice.py` | Validate/fix copyright headers | `tox -e check-copyright`, `tox -e fix-copyright` | Yes -> `aea-ci-helpers` |
| `check_doc_links.py` | Validate doc HTTP links are reachable | `tox -e check-doc-links-hashes` | Yes -> `aea-ci-helpers` |
| `check_doc_ipfs_hashes.py` | Validate/fix IPFS hashes in docs | `tox -e check-doc-links-hashes`, `tox -e fix-doc-hashes` | Already in aea-helpers as `check-doc-hashes` |
| `check_ipfs_hashes_pushed.py` | Verify IPFS hashes are reachable on gateway | `tox -e check-doc-links-hashes` | Yes -> `aea-ci-helpers` |
| `check_dependencies.py` | Verify installed deps match Pipfile | `tox -e dependencies-check` | Already in aea-helpers as `check-dependencies` |
| `check_imports_and_dependencies.py` | Verify imports match declared deps | `tox -e dependencies-check` | Yes -> `aea-ci-helpers` |
| `check_package_versions_in_docs.py` | Verify package IDs in docs match configs | `tox -e package-version-checks` | Yes -> `aea-ci-helpers` |
| `check_pipfile_and_toxini.py` | Verify Pipfile and tox.ini specs match | Development use | Obsolete (repos moved to uv) |
| `check_pyproject_and_toxini.py` | Verify pyproject.toml and tox.ini align | GitHub Actions workflow | Yes -> `aea-ci-helpers` |
| `freeze_dependencies.py` | Freeze pip env to requirements.txt | `tox -e liccheck` | Yes -> `aea-ci-helpers` |
| `generate_api_docs.py` | Generate API docs from source | `tox -e check-api-docs`, `tox -e generate-api-documentation` | Yes -> `aea-ci-helpers` |
| `generate_package_list.py` | Generate markdown table of packages | `tox -e fix-doc-hashes` | Yes -> `aea-ci-helpers` |
| `bump_aea_version.py` | Bump version across codebase | Release process (manual) | Keep in open-aea (repo-specific) |
| `update_package_versions.py` | Update package versions + rehash | Release process (manual) | Keep in open-aea (repo-specific) |
| `update_plugin_versions.py` | Update plugin versions | Release process (manual) | Keep in open-aea (repo-specific) |
| `deploy_to_registry.py` | Deploy packages to AEA registry | Manual/CI deployment | Keep in open-aea (repo-specific) |
| `publish_packages_to_local_registry.py` | Publish to IPFS | Manual deployment | Keep in open-aea (repo-specific) |
| `spell-check.sh` | Markdown spell check | `tox -e spell-check` | Already handled by `tomte check-spelling` |
| `whitelist.py` | Vulture dead code allowlist | `tox -e vulture` | Keep (data file, not a script) |
| `log_parser.py` | Parse profiling logs | Standalone utility | Keep or delete (unused in CI) |
| `install.sh` / `install.ps1` | End-user installers | Direct download | Keep in open-aea |
| `acn/` | ACN node runner | Manual deployment | Keep in open-aea |
| `update_symlinks_cross_platform.py` | Create test fixture symlinks | GitHub Actions | Keep in open-aea (repo-specific) |

#### open-autonomy/scripts/ (11 files)

| Script | Purpose | Invoked by | Could migrate? |
|--------|---------|-----------|----------------|
| `check_copyright.py` | Validate/fix copyright headers | `tox -e check-copyright`, `tox -e fix-copyright` | **DUPLICATE** of open-aea's version -> `aea-ci-helpers` |
| `check_doc_links.py` | Validate doc HTTP links | `tox -e check-doc-links` | **DUPLICATE** -> `aea-ci-helpers` |
| `check_ipfs_hashes_pushed.py` | Verify IPFS hashes on gateway | `tox -e check-ipfs-hashes-pushed` | **DUPLICATE** -> `aea-ci-helpers` |
| `check_third_party_hashes.py` | Cross-ref hashes with open-aea | `tox -e check-packages` | Yes -> `aea-ci-helpers` |
| `freeze_dependencies.py` | Freeze pip env | Not directly invoked | **DUPLICATE** -> `aea-ci-helpers` |
| `generate_api_documentation.py` | Generate API docs | `tox -e check-api-docs`, `tox -e generate-api-documentation` | **DUPLICATE** -> `aea-ci-helpers` |
| `generate_package_list.py` | Generate package markdown | `tox -e generate-package-list` | **DUPLICATE** -> `aea-ci-helpers` |
| `generate_contract_list.py` | Generate contract addresses doc | Standalone | Keep (OA-specific) |
| `whitelist.py` | Vulture allowlist | `tox -e vulture` | Keep (data file) |
| `pre-add` / `pre-push` | Git hooks | Manual git hook install | Keep or move to `.githooks/` |
| `RELEASE_PROCESS.md` | Release documentation | N/A (docs) | Keep |

---

## Proposal: New plugin structure

### Split aea-helpers into two plugins

```
open-aea/
  plugins/
    aea-ci-helpers/          # NEW — generic CI tooling, no autonomy dep
      aea_ci_helpers/
        __init__.py
        cli.py               # Click CLI entry point
        check_copyright.py   # From scripts/check_copyright_notice.py
        check_doc_links.py   # From scripts/check_doc_links.py
        check_ipfs_pushed.py # From scripts/check_ipfs_hashes_pushed.py
        check_imports.py     # From scripts/check_imports_and_dependencies.py
        check_pyproject.py   # From scripts/check_pyproject_and_toxini.py
        freeze_deps.py       # From scripts/freeze_dependencies.py
        generate_api_docs.py # From scripts/generate_api_docs.py
        generate_pkg_list.py # From scripts/generate_package_list.py
        check_pkg_versions.py # From scripts/check_package_versions_in_docs.py
      setup.py
      # Dependencies: click, requests, pyyaml, open-aea (lightweight)

open-autonomy/
  plugins/
    aea-helpers/             # EXISTING — autonomy-specific runtime helpers
      aea_helpers/
        cli.py
        run_agent.py         # Stays (needs autonomy)
        run_service.py       # Stays (needs autonomy)
        config_replace.py    # Stays
        bump_dependencies.py # Stays (needs autonomy)
        check_dependencies.py # Stays (needs autonomy pkg manager)
        check_doc_hashes.py  # Stays (needs autonomy pkg manager)
        make_release.py      # Stays
        pyinstaller_deps.py  # Stays (build-binary-deps, bin-template-path)
        check_binary.py      # Stays
        bin_template.py      # Stays
      setup.py
      # Dependencies: open-autonomy, click, ...

    aea-test-autonomy/       # EXISTING — unchanged
```

### Naming convention

| Package | PyPI name | Import name | CLI name |
|---------|-----------|-------------|----------|
| CI helpers | `aea-ci-helpers` | `aea_ci_helpers` | `aea-ci` |
| Runtime helpers | `aea-helpers` | `aea_helpers` | `aea-helpers` |
| Test infra | `aea-test-autonomy` | `aea_test_autonomy` | (pytest plugin, no CLI) |

### Dependency chain after refactor

```
aea-ci-helpers -> open-aea (only)
aea-helpers -> open-autonomy -> open-aea
aea-test-autonomy -> open-autonomy -> open-aea

open-aea uses: aea-ci-helpers (in tox, no circular dep)
open-autonomy uses: aea-ci-helpers + aea-helpers + aea-test-autonomy
downstream repos use: aea-ci-helpers + aea-helpers + aea-test-autonomy + tomte
```

No circular dependencies.

---

## Migration plan

### Phase 1: Create `aea-ci-helpers` in open-aea

1. Create `open-aea/plugins/aea-ci-helpers/` with setup.py
2. Migrate the 9 generic scripts as Click subcommands:
   - `aea-ci check-copyright` (from `check_copyright_notice.py`)
   - `aea-ci check-doc-links` (from `check_doc_links.py`)
   - `aea-ci check-ipfs-pushed` (from `check_ipfs_hashes_pushed.py`)
   - `aea-ci check-imports` (from `check_imports_and_dependencies.py`)
   - `aea-ci check-pyproject` (from `check_pyproject_and_toxini.py`)
   - `aea-ci check-pkg-versions` (from `check_package_versions_in_docs.py`)
   - `aea-ci freeze-deps` (from `freeze_dependencies.py`)
   - `aea-ci generate-api-docs` (from `generate_api_docs.py`)
   - `aea-ci generate-pkg-list` (from `generate_package_list.py`)
3. Update open-aea's `tox.ini` to call `aea-ci <command>` instead of `scripts/<script>.py`
4. Delete migrated scripts from `open-aea/scripts/`
5. Keep repo-specific scripts: `bump_aea_version.py`, `update_*.py`, `deploy_*.py`, `publish_*.py`, `install.*`, `acn/`, `whitelist.py`

### Phase 2: Remove duplicates from open-autonomy

1. Add `aea-ci-helpers` as a dependency of open-autonomy (in tox.ini test deps)
2. Update open-autonomy's `tox.ini` to call `aea-ci <command>` instead of `scripts/<script>.py`
3. Delete duplicated scripts: `check_copyright.py`, `check_doc_links.py`, `check_ipfs_hashes_pushed.py`, `freeze_dependencies.py`, `generate_api_documentation.py`, `generate_package_list.py`
4. Keep OA-specific: `check_third_party_hashes.py`, `generate_contract_list.py`, `whitelist.py`, git hooks, `RELEASE_PROCESS.md`

### Phase 3: Downstream repos

Downstream repos already use `aea-helpers` and `tomte`. They may optionally add `aea-ci-helpers` for local dev, but most CI checks are already handled by `tomte` + `aea-helpers` at the downstream level. No mandatory changes.

### Phase 4: Cleanup obsolete scripts

1. Delete `check_pipfile_and_toxini.py` from open-aea (Pipfile is dead, repos use uv/pyproject.toml)
2. Delete `spell-check.sh` from open-aea (handled by `tomte check-spelling`)
3. Delete `log_parser.py` from open-aea (unused standalone utility)
4. Move `NOTES.md` and `RELEASE_PROCESS.md` to `docs/` if appropriate

---

## What stays in scripts/ after cleanup

### open-aea/scripts/ (kept)

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

### open-autonomy/scripts/ (kept)

| Script | Reason to keep |
|--------|---------------|
| `check_third_party_hashes.py` | OA-specific (cross-refs with open-aea) |
| `generate_contract_list.py` | OA-specific (fetches from registries) |
| `whitelist.py` | Vulture data file |
| `pre-add` / `pre-push` | Git hooks |
| `RELEASE_PROCESS.md` | Documentation |

---

## Overlap with tomte

`tomte` already provides some of the same functionality via its CLI:
- `tomte check-copyright` — overlaps with `check_copyright_notice.py`
- `tomte check-doc-links` — overlaps with `check_doc_links.py`
- `tomte check-spelling` — overlaps with `spell-check.sh`
- `tomte freeze-dependencies` — overlaps with `freeze_dependencies.py`

**Recommendation:** Downstream repos already use `tomte` for these. The question is whether open-aea and open-autonomy should also use `tomte` instead of their own scripts. If so, `aea-ci-helpers` would only need the scripts that tomte does NOT cover (check-ipfs-pushed, check-imports, generate-api-docs, generate-pkg-list, check-pyproject, check-pkg-versions).

This reduces `aea-ci-helpers` to ~6 commands instead of 9.

---

## Effort estimate

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| Phase 1: Create aea-ci-helpers | 2-3 days | None |
| Phase 2: Remove OA duplicates | 1 day | Phase 1 |
| Phase 3: Downstream (optional) | N/A | No changes needed |
| Phase 4: Delete obsolete | 1 hour | Phase 1 + 2 |
| **Total** | **3-4 days** | |
