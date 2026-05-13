---
name: bump-versions
description: Bump `open-autonomy` and `open-aea` (and their plugins / upstream-pin tags) to the latest released versions across any Valory downstream repo. Reads HISTORY.md + upgrading.md for both frameworks, applies code changes to dev packages only for OA/OAEA breaking changes, bumps version pins everywhere, then syncs third-party hashes from all upstream repos.
argument-hint: "[oa=<version>] [oaea=<version>]  # both optional; defaults to latest GitHub release of each"
disable-model-invocation: true
---

# Bump `open-autonomy` + `open-aea` (and upstream pins) in any downstream repo

End-to-end procedure for bumping a Valory downstream repo (mech, mech-interact, mech-client, mech-server, mech-predict, mech-agents-fun, trader, optimus, market-creator, market-resolver, meme-ooorr, kv-store, funds-manager, genai, etc.) to the latest released `open-autonomy` and `open-aea`. Repo-agnostic — keys off `[project] dependencies` and `[tool.tomte] upstream_pins` in `pyproject.toml`, not a hardcoded repo list.

The two frameworks that drive **code changes** are `open-autonomy` (OA) and `open-aea` (OAEA). Everything else listed in `[tool.tomte] upstream_pins` (e.g. `valory-xyz/mech-interact`, `valory-xyz/genai`, `valory-xyz/mech`) is bumped **tag + third-party-hash only** — never apply code rewrites for those.

The procedure assumes the modern **uv + tox + PEP 621 `[project]`** layout the downstream fleet now uses. Repos still on Poetry need the equivalent edits applied to `[tool.poetry.dependencies]` / `poetry.lock` — the phase structure is unchanged.

---

## Phase 0 — Establish ground truth

Run these in parallel before doing anything else:

```bash
# 1. Confirm the current cwd is a Valory downstream repo (must have pyproject.toml + packages/packages.json)
test -f pyproject.toml && test -f packages/packages.json && echo "OK: looks like a downstream repo"

# 2. Current pins — match both layouts:
#    - PEP 621 / uv:  dependencies = ["open-autonomy[cli]==X", ...]   (leading quote)
#    - Poetry:        open-aea = {version = "==X", extras = [...]}     (bare key)
#    A PEP-621-only pattern silently no-ops on Poetry downstreams.
grep -E "^\s*(\"open-(autonomy|aea)|open-(autonomy|aea)[A-Za-z0-9_-]*\s*=)" pyproject.toml

# 3. Upstream pins listed for sync-only repos (read the whole [tool.tomte] block)
sed -n '/^\[tool\.tomte\]/,/^\[/p' pyproject.toml | grep -A100 "^upstream_pins"

# 4. Repo-local upgrading + history docs (some downstreams ship their own)
ls -1 HISTORY.md UPGRADING.md docs/upgrading.md 2>/dev/null
```

Record into working memory:

| Field | Source |
| ----- | ------ |
| `CUR_OA` | `open-autonomy[*]==X.Y.Z` in `pyproject.toml` |
| `CUR_OAEA` | `open-aea==X.Y.Z` or `open-aea-ledger-ethereum==X.Y.Z` |
| `UPSTREAM_PINS` | `[tool.tomte] upstream_pins` list — sync-only repos with their current tags |
| `HAS_DEV_PACKAGES` | `packages.json`'s `"dev"` map (list of in-repo packages) |
| `IS_FRAMEWORK_REPO` | `true` only for OA / OAEA themselves; for downstreams this is always `false` |

---

## Phase 1 — Resolve target versions

If the user passed `oa=` / `oaea=`, use those. Otherwise hit GitHub's "latest release" endpoint — it returns whatever release is currently marked Latest in the UI, which (unlike `gh release list | first`) doesn't get fooled by an out-of-order backport release published after a newer one:

```bash
# Latest OA release (tag name includes the leading 'v'; strip if you need the bare version)
gh api repos/valory-xyz/open-autonomy/releases/latest --jq '.tag_name'

# Latest OAEA release
gh api repos/valory-xyz/open-aea/releases/latest --jq '.tag_name'
```

Set `NEW_OA` (e.g. `0.21.20`) and `NEW_OAEA` (e.g. `2.2.3`). If they equal the current pins, **stop**: prose-only guidance silently sails past a no-op run and produces a "touched lockfile / re-formatted `packages.json`" PR for zero version change. Gate the rest of the skill on a real diff:

```bash
if [[ "$NEW_OA" == "$CUR_OA" && "$NEW_OAEA" == "$CUR_OAEA" ]]; then
  echo "Already at latest (open-autonomy==$CUR_OA, open-aea==$CUR_OAEA). Nothing to bump."
  exit 0
fi
```

### 1.1 Resolve plugin coupling

Plugin versions are not independent — they track one framework or the other:

| Package | Tracks | Notes |
| ------- | ------ | ----- |
| `open-autonomy[*]` (any extras) | OA | `[cli]`, `[all]`, etc. all share the framework version |
| `open-aea-test-autonomy` | **OA** | Lives in the open-autonomy monorepo at `plugins/aea-test-autonomy/` |
| `open-aea-helpers` | **OA** | Lives in the open-autonomy monorepo at `plugins/aea-helpers/` |
| `open-aea` | OAEA | The core framework |
| `open-aea-ledger-ethereum` / `-cosmos` / `-solana` / `-fetchai` | OAEA | `plugins/aea-ledger-*` |
| `open-aea-ledger-ethereum-hwi` | OAEA | optional `[hwi]` extra in OA since 0.21.18 |
| `open-aea-cli-ipfs` | OAEA | `plugins/aea-cli-ipfs` |
| `open-aea-cli-benchmark` | OAEA | `plugins/aea-cli-benchmark` |
| `open-aea-ci-helpers` / `open-aea-dev-helpers` | OAEA | `plugins/aea-{ci,dev}-helpers` |

**Verify the OA-side plugins are published for the target OA version** (PyPI sometimes lags by a few minutes after a release):

```bash
# Anchor the version on a non-digit boundary so 0.21.2 doesn't false-match inside 0.21.20.
# Fail loudly if either plugin isn't on PyPI yet — silent grep-no-match would otherwise let
# the bump proceed and trip later with a confusing dependency-resolution error.
for pkg in open-aea-test-autonomy open-aea-helpers; do
  pip index versions "$pkg" 2>/dev/null \
    | grep -qE "(^|[^0-9])$NEW_OA([^0-9]|$)" \
    || { echo "ERROR: $pkg==$NEW_OA not yet on PyPI — hold the bump until the publish job completes"; exit 1; }
done
```

### 1.2 Verify OA at `NEW_OA` pins OAEA at `NEW_OAEA`

The bump only makes sense if the new OA itself pins the new OAEA. Pull OA's own `pyproject.toml` at `v$NEW_OA` and read the `open-aea` line(s) — OA still ships Poetry-style (`[tool.poetry.dependencies]`), so the pin shape is e.g. `open-aea = {version = "==2.2.3", extras = ["all"]}`. Materialize the fetch first so a network/auth failure is distinguishable from an empty grep result (the latter would be the trust-OA's-pin branch):

```bash
TMP=${TMP:-$(mktemp -d)}
gh api "repos/valory-xyz/open-autonomy/contents/pyproject.toml?ref=v$NEW_OA" \
  --jq '.content' > "$TMP/oa_pyproject.b64" \
  || { echo "ERROR: gh api failed for OA pyproject.toml@v$NEW_OA — check tag exists, gh auth, rate limit"; exit 1; }
base64 -d "$TMP/oa_pyproject.b64" | grep -E '^[[:space:]]*open-aea[[:space:]]*='
```

If OA `v$NEW_OA` pins a different OAEA version than the user asked for, **trust OA's pin** and override `NEW_OAEA`. A printed pin line that's only inspected by eye will scroll past in a Claude-driven run — extract, compare, and override programmatically so the mismatch can't reach Phase 3+:

```bash
OA_PINNED_OAEA=$(
  base64 -d "$TMP/oa_pyproject.b64" \
    | grep -E '^[[:space:]]*open-aea[[:space:]]*=' \
    | grep -oE '==[0-9]+\.[0-9]+\.[0-9]+' \
    | head -1 \
    | sed 's/^==//'
)
if [[ -z "$OA_PINNED_OAEA" ]]; then
  echo "ERROR: could not extract open-aea pin from OA pyproject.toml@v$NEW_OA"; exit 1
fi
if [[ "$OA_PINNED_OAEA" != "$NEW_OAEA" ]]; then
  echo "WARNING: OA v$NEW_OA pins open-aea==$OA_PINNED_OAEA; you asked for $NEW_OAEA — overriding to OA's pin."
  NEW_OAEA="$OA_PINNED_OAEA"
fi
```

A mismatch left in place would fail `tox -e check-dependencies` and `autonomy packages sync` hundreds of lines later, with a stack trace that doesn't name Phase 1.2 as the root cause.

### 1.3 Resolve upstream-repo tags (sync-only repos)

For each entry in `[tool.tomte] upstream_pins`, find the release tag that itself pins `open-autonomy==$NEW_OA` and `open-aea==$NEW_OAEA`:

```bash
# List recent releases
gh release list --repo valory-xyz/<repo> --limit 10

# Inspect the target tag's pyproject.toml for OA/OAEA pins
gh api "repos/valory-xyz/<repo>/contents/pyproject.toml?ref=<tag>" \
  --jq '.content' | base64 -d | grep -E "open-(autonomy|aea)"
```

**Transitive upstream consistency**: if `trader` is in `upstream_pins` AND `mech-interact` is in `upstream_pins`, the `trader` tag you pick must itself pin the same `mech-interact` version you picked. Otherwise `autonomy packages sync` will surface conflicting CIDs. Walk the dependency chain.

**Release lag fallback**: if an upstream has merged the OA/OAEA bump but not cut a release yet, you can pin to a commit SHA in `pyproject.toml`'s `[tool.uv.sources]`:

```toml
[tool.uv.sources]
mech-interact = { git = "https://github.com/valory-xyz/mech-interact.git", rev = "<SHA>" }
```

Flag this to the user and update `upstream_pins` once the tag drops.

---

## Phase 2 — Read upgrade docs and identify breaking changes

This is the **only** phase that drives code changes. Surface the diff between `CUR_*` and `NEW_*` for both frameworks, then apply the changes scoped to `packages.json`'s `dev` map.

### 2.1 Fetch HISTORY + upgrading from upstream HEAD

`HISTORY.md` is authoritative — `docs/upgrading.md` is the user-facing distilled version. Read both: HISTORY for the full change set, upgrading for the call-to-action. Stage them in a fresh `mktemp -d` so parallel runs (or multiple users on a shared host) don't clobber one another.

**Critical**: each `gh api … > file` chain can fail silently — the redirect succeeds even if `gh api` errors, leaving a zero-byte file. Phase 2.2 then reads nothing, finds no breaking changes, and reports "no action required" — operator applies pin bumps without the code rewrites upgrading.md actually demanded. Guard every fetch:

```bash
set -euo pipefail
TMP=$(mktemp -d)

_fetch() {
  local repo="$1" path="$2" ref="$3" out="$4"
  gh api "repos/$repo/contents/$path?ref=$ref" --jq '.content' \
    | base64 -d > "$out"
  [[ -s "$out" ]] || { echo "ERROR: empty fetch — $repo:$path@$ref"; exit 1; }
}

# Open-autonomy — HISTORY.md and docs/upgrading.md
_fetch valory-xyz/open-autonomy HISTORY.md          "v$NEW_OA" "$TMP/oa_history.md"
_fetch valory-xyz/open-autonomy docs/upgrading.md   "v$NEW_OA" "$TMP/oa_upgrading.md"

# Open-aea — HISTORY.md and docs/upgrading.md
_fetch valory-xyz/open-aea      HISTORY.md          "v$NEW_OAEA" "$TMP/oaea_history.md"
_fetch valory-xyz/open-aea      docs/upgrading.md   "v$NEW_OAEA" "$TMP/oaea_upgrading.md"
```

Read **only the sections between `CUR_OA` and `NEW_OA`** in OA's docs, and between `CUR_OAEA` and `NEW_OAEA` in OAEA's docs. Both files are reverse-chronological — top of file is newest.

### 2.2 Classify each change

For every change between the two versions, tag it as one of:

| Class | Action |
| ----- | ------ |
| **Pin-only** (security floor, transitive bound) | Already covered by Phase 3 pin bumps; no code change |
| **YAML-only** (new field in `aea-config.yaml`, `connection.yaml`, etc.) | Apply to dev YAMLs in Phase 3.4 |
| **API change** (import path moved, signature changed, removed) | Apply to `.py` files in `packages.json` `dev` map only — see Phase 4 |
| **CI/tooling** (workflow runner pin, action version) | Apply in Phase 3.3 |
| **Removed feature** (e.g. `tomte check-spelling`, deprecated module) | Remove the corresponding usage in this repo |
| **No-op for downstream** (e.g. "PyPI metadata fix") | Skip |

**Discipline**: the upgrading.md sections are explicit about which changes downstream consumers must apply. Don't infer; if a section doesn't call for a change, don't make one. Conversely, every "Action required" / "Concrete upgrade steps" / "**Breaking**" callout is non-optional.

### 2.3 Where code changes apply (and where they don't)

Apply API/import rewrites **only** to files under paths in `packages.json`'s `"dev"` map. Concretely:

```bash
# List dev package paths from packages.json
python3 -c "
import json
d = json.load(open('packages/packages.json'))
for k in d.get('dev', {}):
    # keys look like 'agent/valory/trader/0.1.0' → 'packages/valory/agents/trader'
    kind, author, name, _ = k.split('/')
    kind_dir = {'agent':'agents','skill':'skills','contract':'contracts','connection':'connections','protocol':'protocols','service':'services','custom':'customs'}[kind]
    print(f'packages/{author}/{kind_dir}/{name}')
"
```

Third-party packages (the `"third_party"` map) are **never** edited by hand — they get refreshed by `autonomy packages sync --source` in Phase 5.

Non-package code (top-level `scripts/`, `tests/`, app entrypoints) is also fair game for OA/OAEA API rewrites — only the **packages/** tree is partitioned dev-vs-third-party.

---

## Phase 3 — Bump version pins everywhere

The same OLD version string appears in 5–10+ places per repo. Use a thorough grep before editing so you don't miss a site:

```bash
# Cast wide. Use -E with an explicit non-digit boundary so `==0.21.2` doesn't
# false-match inside `==0.21.20` (\b is GNU-grep-only and trips on BSD grep / macOS).
# Excludes uv.lock (regenerated), .git/, and node_modules.
grep -rlE "==${CUR_OA}([^0-9]|$)" \
  --include="*.toml" --include="*.ini" --include="*.yaml" --include="*.yml" \
  --include="*.py" --include="*.md" --include="*.txt" --include="*.json" \
  --include="*.sh" --include="Makefile" --include="Dockerfile" --include="Pipfile*" \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules

grep -rlE "==${CUR_OAEA}([^0-9]|$)" \
  --include="*.toml" --include="*.ini" --include="*.yaml" --include="*.yml" \
  --include="*.py" --include="*.md" --include="*.txt" --include="*.json" \
  --include="*.sh" --include="Makefile" --include="Dockerfile" --include="Pipfile*" \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules
```

Triage the hit list and apply edits in the sections below. Every hit must be addressed (edit or consciously skip with reason).

### 3.1 `pyproject.toml`

Modern downstreams use PEP 621 (`[project]` block) with `uv` — not `[tool.poetry]`. Update `[project] dependencies`:

```toml
[project]
dependencies = [
    "open-autonomy[cli]==<NEW_OA>",         # (or [all], or bare — preserve whatever extras the repo uses)
    "open-aea==<NEW_OAEA>",                  # only if explicitly listed
    "open-aea-ledger-ethereum==<NEW_OAEA>",
    "open-aea-ledger-cosmos==<NEW_OAEA>",
    "open-aea-cli-ipfs==<NEW_OAEA>",
    "open-aea-test-autonomy==<NEW_OA>",      # tracks OA, not OAEA — easy to get wrong
    "open-aea-helpers==<NEW_OA>",            # tracks OA, not OAEA
    # … rest of the transitive pins, bumped per upgrading.md guidance
]
```

Also bump these when upgrading.md / HISTORY.md says so:

- `requires-python` range (if the new framework adds/drops a Python minor)
- transitive pins flagged in HISTORY (e.g. `GitPython>=3.1.47`, `protobuf>=5,<7`, `cachetools` cap removal)
- `[tool.tomte] upstream_pins` — bump every entry's tag to the one you resolved in Phase 1.3
- `[tool.tomte] tomte_dep_pin` if HISTORY says tomte was bumped (e.g. `0.6.5 → 0.7.0`)

> **Plugin-coupling trap**: `open-aea-test-autonomy` and `open-aea-helpers` look like OAEA plugins but they're in the **open-autonomy** monorepo and version-track OA. If you set them to `==<NEW_OAEA>`, `pip` / `uv` will not find a matching release. See the table in Phase 1.1.

### 3.2 `tox.ini`

Every linter/test env carries its own dep block. Common sections to touch (the exact section names vary across repos — find with `grep "^\[" tox.ini`):

- `[deps-framework]` / `[deps-packages]` / `[deps-tests]` / `[extra-deps]` — main version pins
- `[testenv]` and per-`[testenv:*]` `deps =` blocks — anywhere `open-autonomy`, `open-aea*`, or `tomte` appears
- `[testenv:check-hash]`, `[testenv:check-packages]`, `[testenv:check-dependencies]`
- All `tomte[<extra>]` lines under `[testenv:bandit|black|isort|flake8|mypy|pylint|safety|darglint|liccheck|gitleaks|cli]`

Repos using `tomte tox -e <env>` instead of bare `tox -e <env>` inherit dep blocks from tomte's canonical config — many `[deps-*]` blocks may be thin or absent. Check the Makefile to see which form this repo uses.

**Parity invariant**: every dep added to `[project] dependencies` in `pyproject.toml` must also appear in `tox.ini`'s framework/packages dep blocks, or `tox -e check-dependencies` will fail with `<package> not found in tox.ini`. Mirror both directions.

**`tomte` bump caveats** (only if HISTORY shows tomte was bumped):

- tox 4 renamed `whitelist_externals` → `allowlist_externals`
- `tomte 0.7.0` ships canonical lint configs as packaged resources at `{envsitepackagesdir}/tomte/configs/<cfg>`; if HISTORY says configs are referenced via that path now and your repo still has a forked `.gitleaks.toml` / `.pylintrc`, drop the fork and reference the canonical resource
- `tomte 0.7.0` removed `check-spelling` — delete `[testenv:spell-check]` and any Makefile target that invokes it

### 3.3 `.github/workflows/*.yml`

Pull workflow files in the target OA release as the source of truth for runner / action pins:

```bash
TMP=${TMP:-$(mktemp -d)}
gh api "repos/valory-xyz/open-autonomy/contents/.github/workflows/main_workflow.yml?ref=v$NEW_OA" \
  --jq '.content' | base64 -d > "$TMP/oa_workflow.yml"

# Compare action versions, OS runners, Python matrix in your repo
diff <(grep -E 'uses:|runs-on:|python-version:' .github/workflows/main_workflow.yml | sort -u) \
     <(grep -E 'uses:|runs-on:|python-version:' "$TMP/oa_workflow.yml" | sort -u)
```

Update **every** `.github/workflows/*.yml` file, not only the main one (`release.yaml` is the usual miss):

- Action pins (`actions/checkout`, `actions/setup-python`, `actions/upload-artifact`, `codecov/codecov-action`, etc.) — never use `@master` / `@main`; always a pinned semver tag
- OS runners — never `*-latest`. Match the OA target's pins exactly (e.g. `ubuntu-24.04`, `macos-15`, `windows-2025`). Update everywhere they appear: `matrix.os`, `runs-on`, `if:` conditionals, step `name:` strings
- `pip install tomte[*]==<old>` — bump pin
- Docker image tags — `valory/open-autonomy-user:<old>` → `<NEW_OA>`
- `autonomy build-image` / `autonomy ... --version` arg in release jobs
- Python matrix — add new minor versions that the new OA supports (check OA's own matrix)

### 3.4 Dev package YAMLs

Every dev package's component YAML carries a `dependencies:` block with pinned versions of the plugins it uses. Search inside `packages/<author>/`:

```bash
# Search across every dev package path (computed in Phase 2.3) for old pins.
# Uses -E with non-digit boundary (BSD-grep-safe; \b/\| are GNU-only).
grep -rnE "==(${CUR_OAEA}|${CUR_OA})([^0-9]|$)" packages/ --include="*.yaml"
```

Typical hits and what they map to:

| YAML field | Tracks |
| ---------- | ------ |
| `open-aea-ledger-ethereum: { version: ==X }` | OAEA |
| `open-aea-ledger-cosmos: { version: ==X }` | OAEA |
| `open-aea-test-autonomy: { version: ==X }` | OA |
| `open-aea-cli-ipfs: { version: ==X }` | OAEA |

Constraint: only edit YAMLs under dev-package paths (from Phase 2.3). Third-party YAMLs (under `packages/<other-author>/` or marked third-party in `packages.json`) get rewritten by `autonomy packages sync` and edits will be reverted.

**Hash cascade**: every YAML edit invalidates the package's fingerprint. After editing, you **must** re-run `autonomy packages lock` (Phase 5) or `tox -e check-hash` will fail.

### 3.5 Less-obvious pin sites

These are easy to miss; sweep them explicitly:

- `deployments/Dockerfiles/**/requirements.txt` and `deployments/Dockerfiles/**/Dockerfile` — `open-autonomy[all]==X` baked into the Docker user image
- `docs/**/*.md` — tutorial snippets with `pip install open-autonomy==<old>`
- `Pipfile` / `Pipfile.lock` — some repos still ship pipenv alongside uv
- `scripts/*.sh` and repo-root bootstrap shells with `pip install ... ==<old>`
- `Makefile` targets that hardcode the version (rare but real)
- `mkdocs.yml` env_vars and template strings
- `setup.py` if the repo still ships one alongside `pyproject.toml`

If `grep -rnE "${CUR_OA}([^0-9]|$)"` (no `==` prefix) returns hits in non-code paths (READMEs, badges, CHANGELOGs), update those too **when** they're describing the supported version. Don't touch historical changelog entries.

---

## Phase 4 — Apply OA/OAEA code changes (dev packages only)

Reach this phase only if Phase 2 surfaced API / import / behavior changes in OA or OAEA between `CUR_*` and `NEW_*`.

### 4.1 Identify the change surface

For each "API change" / "Breaking" item from upgrading.md, build a concrete search:

| Type of change | How to find call sites |
| -------------- | ---------------------- |
| Symbol renamed / moved | `grep -rn "from autonomy\.<old_path>" packages/ tests/ scripts/` |
| Function signature change | `grep -rn "<func_name>(" packages/ tests/ scripts/` |
| Class API change (e.g. `setup` → `setup_method` for `BaseSkillTestCase`) | `grep -rn "<ClassName>" packages/ tests/` |
| Removed module | same as "Symbol renamed" |
| YAML schema change | `grep -rn "<old_field>" packages/ --include="*.yaml"` |

Confine edits to:

- Files under any dev-package path from Phase 2.3 (`packages/<author>/<kind>/<name>/...`)
- Top-level `tests/`, `scripts/`, app code (`agent/`, `funds-manager-cli/`, etc. — anything **not** under `packages/`)

Do **not** edit:

- Third-party package files under `packages/` — they get refreshed by sync
- `uv.lock` / `poetry.lock` — regenerated by Phase 5
- Anything in `.tox/`, `.venv/`, `__pycache__/`

### 4.2 Apply changes the same way the upgrading guide describes

For each change, write the smallest diff that satisfies the guide. Examples of common shapes:

```python
# OAEA 2.x: BaseSkillTestCase.setup() → setup_method() — rename def AND the super() call site.
class TestMyBehaviour(BaseSkillTestCase):
-    def setup(self) -> None:
-        super().setup()
+    def setup_method(self) -> None:
+        super().setup_method()
         ...
```

```yaml
# OA 0.21.20: named env-var placeholders surface via service.yaml overrides
# (no edit required — pre-existing ${VAR:type:default} syntax already supported)
```

```python
# OAEA 2.2.2: Polygon gas endpoint URL changed in plugin defaults
# (no edit required — picked up via plugin bump in 3.1)
```

After every code change, mentally trace the call sites once more. Open-aea/-autonomy bumps frequently cascade: a moved import in `abstract_round_abci` will show up in every dev skill that subclasses it.

### 4.3 Hardcoded skill-CID constants (only relevant to OA itself)

This is the framework's pattern — downstream services reference skills via YAML, not via hardcoded Python constants. **Skip this for downstream bumps.** Mentioned here only so you don't go hunting for it.

---

## Phase 5 — Sync third-party hashes from every upstream repo

Hash sync is non-negotiable and **must** run after Phase 3 edits (pin bumps) but **before** Phase 6 (lock + verify). Order matters because dev-package hashes cascade off third-party hashes.

### 5.1 Pre-audit third-party CID drift

`autonomy packages sync --source` only refreshes packages it already knows about — it trusts whatever CID is currently in `packages.json`. Drift from a prior bump (a CID miscopy, a never-synced upstream) is invisible to the regular sync path. Audit first:

Fetch each upstream's `packages.json` straight from GitHub via `gh api` (same path the rest of the skill uses for HISTORY/upgrading) — no local checkouts required:

```bash
python3 <<'PY'
import json, subprocess

local = json.load(open('packages/packages.json')).get('third_party', {})

# (repo, ref) for [tool.tomte] upstream_pins + the two frameworks.
UPSTREAMS = [
    ("valory-xyz/open-aea",      "v<NEW_OAEA>"),
    ("valory-xyz/open-autonomy", "v<NEW_OA>"),
    # + one entry per upstream_pins repo, using its resolved tag
]

def _fetch(repo, ref):
    raw = subprocess.check_output([
        "gh", "api",
        f"repos/{repo}/contents/packages/packages.json?ref={ref}",
        "--jq", ".content",
    ])
    import base64
    return json.loads(base64.b64decode(raw))

all_up = {}
for repo, ref in UPSTREAMS:
    data = _fetch(repo, ref)
    # Upstream-side dev map becomes our third-party map
    all_up.update(data.get("dev", {}))

drift = []
for k, v in local.items():
    uv = all_up.get(k)
    if uv and uv != v:
        drift.append((k, v, uv))

if drift:
    print(f'{len(drift)} drifted third-party CIDs (will be fixed by `sync --update-packages`):')
    for k, l, u in drift:
        print(f'  {k}\n    local:    {l}\n    upstream: {u}')
else:
    print('No third-party CID drift.')
PY
```

Drift gets corrected by `sync --update-packages` below, but knowing the baseline is what lets you spot a sync that *should* have updated a package but didn't.

### 5.2 Run sync against every upstream repo

Pass each tag **exactly as `gh release list` returns it** — `valory-xyz/open-aea` and `valory-xyz/open-autonomy` use the `v` prefix; some other upstreams have historically published without it. Don't guess the prefix; use the literal tag string.

```bash
# OAEA first (open-autonomy depends on it; some downstream third-party packages come from open-aea)
autonomy packages sync --source valory-xyz/open-aea:v$NEW_OAEA --update-packages

# OA
autonomy packages sync --source valory-xyz/open-autonomy:v$NEW_OA --update-packages

# Every entry from [tool.tomte] upstream_pins, using the tags resolved in Phase 1.3
autonomy packages sync --source valory-xyz/mech-interact:<TAG> --update-packages
autonomy packages sync --source valory-xyz/genai:<TAG> --update-packages
autonomy packages sync --source valory-xyz/kv-store:<TAG> --update-packages
autonomy packages sync --source valory-xyz/funds-manager:<TAG> --update-packages
# … repeat for every upstream_pins entry
```

If sync warns about packages it didn't recognise (not in any source), they come from a repo not yet in `upstream_pins`. Grep the package author/name across other Valory repos to find the source; add it to `upstream_pins`.

### 5.3 Sync error recovery

Two known failure modes (from real bumps):

- **`ValueError: not enough values to unpack (expected 1, got 0)` from `base.py:valid()`** — leftover empty cache dir from an interrupted fetch:
  ```bash
  find ~/.aea/cache/packages -mindepth 1 -maxdepth 1 -type d -empty -exec rmdir {} \;
  ```
- **`Destination path '...' already exists`** — a prior sync wrote a package to the wrong on-disk path. **Do not** reach for `git clean -fdx packages/` — `-fdx` deletes untracked **and gitignored** files, which will silently nuke any Phase 3.4 YAML edits or Phase 4 `.py` rewrites that aren't staged yet (and the doc never tells you to stage between phases). Instead stash, retry, then unstash:
  ```bash
  git stash push -u -- packages/    # captures untracked Phase 3-4 edits
  autonomy packages sync --source <repo>:<tag> --update-packages
  git stash pop                     # restore your in-progress edits
  ```
  If you've confirmed there are no in-progress edits under `packages/` (e.g. `git status -- packages/` is clean and `git ls-files --others --exclude-standard -- packages/` is empty), `git clean -fdx packages/` is fine — but verify first.

Don't treat either as a bump regression.

---

## Phase 6 — Lock + format + verify

Run in this exact order. Each step gates the next.

**Pick the right `tox` invocation form first.** Most of the modern fleet (market-creator, market-resolver, kv-store, funds-manager, genai, mech, mech-interact, …) runs envs through `tomte tox -e <env>` so the testenvs inherit dep blocks from tomte's canonical config. Bare `tox -e <env>` on those repos fails with `ERROR: env '<name>' not defined in tox config`. Detect once and use `$TOX` throughout:

```bash
# Pick the invocation form by reading the Makefile; warn loudly if absent so we
# don't silently default to bare `tox` on a uv-only repo that actually needs tomte.
if [[ ! -f Makefile ]]; then
  echo "WARNING: no Makefile — defaulting TOX=tox. Verify this repo doesn't require 'tomte tox'."
  TOX="tox"
elif grep -q "tomte tox" Makefile; then
  TOX="tomte tox"
else
  TOX="tox"
fi
echo "using TOX=$TOX"
```

**Ordering rule** (per open-autonomy `CLAUDE.md`): `autonomy packages lock` runs **once, at the end**, after every other edit/lint/format step has settled. Locking earlier is wasted work — any subsequent formatter-triggered rewrite under `packages/` re-dirties the fingerprints and forces a re-lock anyway.

```bash
# 1. Regenerate the lockfile and install
uv lock
uv sync --all-groups

# 2. Auto-format first (some pin changes trip isort/black, which would otherwise dirty
#    packages/ after a too-early `autonomy packages lock`)
$TOX -e black
$TOX -e isort

# 3. Lock once, after all edits have settled (third-party hashes cascade into dev fingerprints)
autonomy packages lock

# 4. Verify lock + format
$TOX -e black-check
$TOX -e isort-check
autonomy packages lock --check
```

Then run the **full CI suite locally** — every job referenced by `.github/workflows/*.yml`, not a subset. The downstream fleet has caught real regressions only on jobs that the bump author skipped locally.

```bash
# Discover the full job list
grep -E "tomte tox -e|^\s+- run:.*tox -e|^\s+- name:" .github/workflows/*.yml

# Typical envs to run (substitute Python minor for your interpreter):
$TOX -e flake8
$TOX -e mypy
$TOX -e pylint
$TOX -e darglint
$TOX -e bandit
$TOX -e safety           # add -i <ID> for new CVE exceptions per upgrading.md
$TOX -e liccheck         # add [Authorized Packages] entries for metadata-less new transitives
$TOX -e copyright-check
$TOX -e check-hash
$TOX -e check-packages
$TOX -e check-abciapp-specs
$TOX -e check-abci-docstrings
$TOX -e check-dependencies
$TOX -e py3.11-linux     # or py3.12, py3.13, py3.14 — whatever the matrix supports
# + every other env the workflow files actually run
```

If any step modifies files under `packages/` (linter auto-fixes, `# nosec` insertions, etc.), re-run `autonomy packages lock` before continuing.

### 6.1 Common verify-phase failures

These are repeat offenders on bump PRs. Recognise the symptom → apply the fix:

- **`Conflict on package <NAME>: specifier set '==<OLD>,==<NEW>' not satisfiable`** during `autonomy packages sync` or `tox -e check-hash` — a dev YAML still has an old plugin pin. Grep for the exact `<OLD>` string and update.
- **`<package> not found in tox.ini` from `check-dependencies`** — pyproject vs tox.ini dep parity drift. Mirror the new dep into `[deps-framework]` or `[deps-packages]`.
- **`UNKNOWN licenses: <pkg> is under license UNKNOWN`** in `liccheck` — a new transitive ships without `license` metadata on PyPI even though the upstream LICENSE file is real. Verify the actual license at the source (`gh api repos/<org>/<repo>/contents/LICENSE --jq '.content' | base64 -d`), then add to `[Authorized Packages]` in `tox.ini` with a one-line comment naming the verified license. **Do not add to `[Licenses]`** — that section is only for legitimate new license strings.
- **`ModuleNotFoundError` at pytest startup, every matrix cell fails in <1s** — a transitive pulled in a pytest plugin with a broken autoload (e.g. `anchorpy` via `open-aea-ledger-solana`). Fix in `[testenv] setenv` with `PYTEST_ADDOPTS=-p no:<plugin_name>` — NOT `[pytest] addopts`, which doesn't propagate to subprocesses. Avoid the broad `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; it kills `pytest-asyncio` / `pytest-cov` / `hypothesis` too.
- **`tox -e check-doc-links-hashes` fails on an external URL** — append the failing URL to the env's inline `-u "..."` ignore list with a one-line comment naming the host.
- **Local tox env says `No module named pip`** — known dev-vs-CI divergence on tox 4 + uv for envs whose commands run `python -m pip install ...`. Two options: temporarily add `pip` to the env's `deps =` (don't commit) OR bypass tox and run the underlying tool directly under `uv run` (e.g. `uv run aea-helpers check-dependencies ...`).

---

## Phase 7 — Stop after verify

The skill ends at Phase 6. **Do not** stage, commit, push, or open a PR — leave the working tree dirty for the user to inspect. The user runs their own commit/PR flow when ready.

Hand off with a short summary: which framework versions were bumped, which `upstream_pins` tags were refreshed, how many code edits Phase 4 applied, and the list of verify envs that passed locally.

---

## Files commonly modified (cheat-sheet)

| File | What changes |
| ---- | ------------ |
| `pyproject.toml` | `[project] dependencies`, `requires-python`, `[tool.tomte] upstream_pins`, `tomte_dep_pin` |
| `uv.lock` | Auto-regenerated by `uv lock` |
| `tox.ini` | Pin sites across all `[testenv:*]` deps, `[deps-framework]`/`[deps-packages]`, `[Authorized Packages]` additions for new metadata-less transitives, `[testenv] setenv` `PYTEST_ADDOPTS` if needed |
| `.github/workflows/*.yml` | Action pins, OS runner pins, Python matrix, `pip install tomte==`, Docker image tag, `autonomy build-image --version` |
| `packages/packages.json` | Third-party CIDs (sync), dev fingerprints (lock) |
| `packages/<author>/**/*.yaml` | `dependencies:` block pins on `open-aea-*` and `open-aea-test-autonomy` (dev packages only) |
| `packages/<author>/**/*.py` | API/import rewrites per OA/OAEA upgrading.md (dev packages only) |
| `deployments/Dockerfiles/**/requirements.txt` | `open-autonomy[all]==<NEW_OA>` pin in the Docker user image |
| `docs/**/*.md` | Tutorial snippets with version-pinned install commands |
| `scripts/*.sh`, `Pipfile*`, `Makefile`, `setup.py` | Any hardcoded version literals |

---

## Hard rules (do not violate)

1. **OA/OAEA drive code changes; everything else in `upstream_pins` is version+hash-only.** Never write a code edit because `mech-interact` or `genai` changed.
2. **Edit `.py` only under dev-package paths.** Third-party files under `packages/<author>/` get rewritten by sync.
3. **`open-aea-test-autonomy` and `open-aea-helpers` track OA**, not OAEA, despite the name. Pin them to `<NEW_OA>`.
4. **Run `autonomy packages lock` after every YAML edit** under `packages/`. Hashes cascade.
5. **Run the full CI suite locally before any push.** Every job from `.github/workflows/*.yml`, not a sampled subset.
6. **Don't `--amend` commits on a published PR branch.** Add new commits.
7. **Don't reference PR numbers / people / "X's rule" in code comments.** Write the underlying WHY or delete.

---

## Appendix: quick-reference grep patterns

All version-targeting greps below mirror Phase 3's `==X.Y.Z` + non-digit-boundary discipline so `0.21.2` doesn't false-match inside `0.21.20`. If you want a looser triage view (e.g. to find docs prose mentioning the version), drop the boundary deliberately and expect false positives.

```bash
# Every pin site that still references the old OA version (canonical sweep)
grep -rE "==${CUR_OA}([^0-9]|$)" --exclude-dir=.git --exclude-dir=.venv \
  --exclude=uv.lock --exclude=poetry.lock .

# Every pin site that still references the old OAEA version (canonical sweep)
grep -rE "==${CUR_OAEA}([^0-9]|$)" --exclude-dir=.git --exclude-dir=.venv \
  --exclude=uv.lock --exclude=poetry.lock .

# Every YAML dep block under dev packages (Phase 3.4 scope) — package-name match only,
# version-pin sweep already covered by the two patterns above
grep -rnE "open-aea|open-autonomy" packages/ --include="*.yaml" -B1 -A2

# Every `[tool.tomte] upstream_pins` entry (Phase 1.3 inventory)
sed -n '/^\[tool\.tomte\]/,/^\[/p' pyproject.toml | grep -E '"valory-xyz/'
```
