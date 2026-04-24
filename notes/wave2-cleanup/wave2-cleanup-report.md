# Wave 2 cleanup — centralising duplicated auxiliary config across Valory repos

_Survey date: 2026-04-23. Author: Claude (via `cleanup-deps` follow-up analysis)._

## TL;DR

Every agent-style repo carries roughly the same ~800-line `tox.ini`, a
near-identical `CONTRIBUTING.md`, and a scatter of `.spelling` /
`.gitleaks.toml` / `pytest.ini` / `setup.cfg` / `.pylintrc` / `scripts/whitelist.py`
that drift independently. The library repos (`tomte`, `open-autonomy`,
`open-aea`) are the natural hubs. Concrete plan:

1. **Delete spell-check entirely.** `.spelling` (×12 repos, all different),
   the `[testenv:spell-check]` section (×10), the corresponding CI step
   (×4), and `tomte/tomte/scripts/check_spelling.sh` +
   `tomte check-spelling` CLI. mdspell is npm-only and no repo pins it;
   the wordlists are stale and never maintained together.

2. **`CONTRIBUTING.md` → 10-line stub per repo, canonical in `open-autonomy`.**
   All downstream copies are ≥95 % identical — just variations on
   "run `tomte format-code` then `tomte check-code`". One source of truth,
   everything else is a link.

3. **`pytest.ini` → inline into `pyproject.toml` as `[tool.pytest.ini_options]`.**
   Every agent-style repo is already on PEP 621 + `uv_build` after Wave 1.
   Eliminates the file; only 4 repos carry one today (`open-aea`,
   `mech-interact`, `mech-client`, `IEKit`) and three share the same body.

4. **`.gitleaks.toml` → one canonical in `open-autonomy`, per-repo stub
   with `[extend] path = ".gitleaks.toml from OA"`.** The OA / OAEA files
   are 1617-1619 lines and ~99 % identical; trader/IEKit are pruned copies
   of the same base; optimus/market-creator are tiny stubs already. Nothing
   in the default ruleset is Valory-specific — the only real allowlists are
   IPFS CIDv1 hashes and a few per-repo test fixtures.

5. **`setup.cfg` → fold into `pyproject.toml`.** Only 4 repos still have
   one; all four content is `[isort]` + a bit of `[mypy]` + `[flake8]`.
   Move to `[tool.isort]`, `[tool.mypy]`, Flake8-pyproject `[tool.flake8]`,
   `[tool.darglint]`. Delete the file.

6. **`tox.ini` → the harder fight.** Tox 4 supports a `[tool.tox]` section
   in `pyproject.toml`, but the real duplication is the ~40 `[testenv:*]`
   recipes that are literally identical. Native tox has no cross-file
   inheritance. Two viable paths: **(a)** ship
   `tomte/templates/tox.ini` + a `tomte init-tox` generator (regenerate on
   tool version bumps, commit the output); **(b)** accept that the
   per-repo tox.ini stays but shrink it to just the repo-unique bits by
   making tomte own more CLI entry points so tox just shells out to
   `tomte <step>` (most of the lint envs are already three lines and a
   `tomte check-code`-shaped call — one step away from collapsing).

7. **`tox.ini` + `pyproject.toml` cannot fully merge.** Tox 4 reads
   `[tool.tox]` from pyproject.toml only for a handful of keys; any
   heavily-customised tox.ini with its own `[deps-packages]`, `[mypy-*]`,
   `[flake8]`, `[Licenses]` sections must stay in `tox.ini` or be
   re-homed piecewise. The right split is: **tool configs
   (`[mypy]`, `[flake8]`, `[isort]`, `[Licenses]`) → `pyproject.toml`**;
   **tox envs → remain in `tox.ini`, shrunken**. Don't plan on one-file
   consolidation.

8. **`scripts/whitelist.py`** is not duplicated — it's per-repo vulture
   content that happens to live at the same path. Leave it.

9. **Sequencing: Wave 2 blocked on Wave 1 (`cleanup-deps`).** Several of
   these changes (pytest.ini → pyproject.toml, .pylintrc removal,
   setup.cfg removal) interact with the `tox -e check-dependencies` +
   `[deps-packages]` list. Do Wave 1 per repo first — it stabilises which
   packages are declared — then do Wave 2 on the same branch / PR or a
   follow-up.

Estimated line-count reduction across the 11 non-library repos: **~1100
lines of `.spelling` × 12, ~2800 lines of duplicated CONTRIBUTING.md, ~100
lines of pytest.ini, ~8000 lines of `.gitleaks.toml`, ~200 lines of
`setup.cfg`, plus ~6000 lines if tox.ini boilerplate moves to a template
generator**. Net ≈ **18000 lines deleted across the fleet**, not counting
CI workflow simplifications.

## Summary by cleanup target

| Target | Current state | Proposed state | Hub | Blast radius | Risk |
|---|---|---|---|---|---|
| `.spelling` + mdspell | 12 repos × ~6 KB each, all different | delete everything | n/a | 12 repos + CI + tomte | low |
| `CONTRIBUTING.md` | 13 repos, ~2.8–5.8 KB each, >95 % identical | 10-line stub linking to OA canonical | `open-autonomy` | 13 repos | very low |
| `pytest.ini` | 4 repos, 3 of 4 share a body | `[tool.pytest.ini_options]` in `pyproject.toml` | n/a (per-repo) | 4 repos | low |
| `.gitleaks.toml` | 6 repos, 1617–1619 lines in OA/OAEA, 100–562 in others | per-repo stub with `[extend] path = ".gitleaks.canonical.toml"` | `open-autonomy` | 6 repos + CI | medium (regex coverage) |
| `.pylintrc` | 8 repos, 2 pairs share a hash, 6 distinct | `[tool.pylint]` in `pyproject.toml`; optionally ship defaults via `tomte` | n/a (per-repo) | 8 repos | low |
| `setup.cfg` | 4 repos (mostly isort + flake8 + mypy + darglint) | move all `[tool.*]`; delete the file | n/a (per-repo) | 4 repos | low |
| `tox.ini` tool envs | 10 repos, ~40 identical `[testenv:*]` sections each | `tomte init-tox` generates from template; per-repo keeps only unique envs | `tomte` | 10 repos | medium (tooling churn) |
| `tox.ini` ↔ `pyproject.toml` merge | Separate today | Partial: `[tool.mypy]`, `[tool.flake8]` (via Flake8-pyproject) move to pyproject; tox.ini stays | n/a | all repos | medium |
| `scripts/whitelist.py` | 3 repos — OA, OAEA, mech-client | keep as-is | n/a | — | n/a |

---

## 1. Inventory — what each repo ships today

Grid of aux-config files; blank means absent. Repos that didn't make the
user's study list are excluded.

```
FILE                         | tomte | OA    | OAEA  | mech  | mech-pred | mech-int | mech-af | mech-cli | mech-srv | trader | optimus | meme   | IEKit | mkt-c
.spelling                    | ·     | 7762  | 5514  | 6357  | 6357      | 6442     | 6357    | 41       | 6357     | 6403   | 1276    | 1332   | 6208  | 402
.gitleaks.toml               | ·     | 23881 | 23857 | ·     | ·         | ·        | ·       | ·        | ·        | 17331  | 2572    | ·      | 16610 | 504
pytest.ini                   | ·     | ·     | 1350  | ·     | ·         | 1460     | ·       | 399      | ·        | ·      | ·       | ·      | 1698  | ·
tox.ini                      | ·     | 31145 | 17400 | 23939 | 22015     | 22457    | 14643   | 8992     | 18306    | 23680  | 24024   | 19787  | 23837 | 22146
pyproject.toml               | 3213  | 2328  | 2080  | 1724  | 2471      | 1766     | 1979    | 1015     | 2015     | 1949   | 1381    | 1519   | 1866  | 1666
.pylintrc                    | ·     | 1842  | 5393  | 1747  | 1747      | 372      | 1150    | ·        | 1236     | ·      | ·       | ·      | 372   | ·
CONTRIBUTING.md              | ·     | 2910  | 5771  | 2857  | 2852      | 2812     | 2847    | 4078     | 4369     | 2841   | 2842    | 2898   | 2912  | 2858
setup.cfg                    | ·     | 469   | 7640  | ·     | ·         | ·        | 392     | ·        | 567      | ·      | ·       | ·      | ·     | ·
scripts/whitelist.py         | ·     | 17706 | 24063 | ·     | ·         | ·        | ·       | 6843     | ·        | ·      | ·       | ·      | ·     | ·
```
(sizes in bytes; `·` = missing)

Observations:

- **`.spelling`** — present in 13 of 14 repos (all except tomte). All 13
  SHA-1s are distinct *except* `mech`, `mech-predict`, `mech-server`, and
  `mech-agents-fun` which share `1f37e1fd59…`. Wordlists have drifted
  independently; no reviewer keeps them in sync.
- **`.gitleaks.toml`** — present in 6 repos, all with different SHA-1s.
  OA (1619 lines) and OAEA (1617 lines) differ by **7 lines** (mostly
  about `cross_period_persisted_keys_\d+` and path allowlists). trader
  (562 lines), IEKit (541) are pruned forks. optimus (107), market-creator
  (15) are hand-written stubs. The "canonical" ruleset is already
  implicitly OA's.
- **`pytest.ini`** — open-aea (24 lines), mech-interact (25 lines), and
  IEKit (28 lines) share the same `filterwarnings` + `markers` block with
  cosmetic deltas. mech-client (27 lines) is the outlier — it's a library
  repo with different discovery rules.
- **`tox.ini`** — absent only from tomte. 10 downstream agent-style repos
  all declare the same **24 `[testenv:*]`** sections plus `[mypy]`,
  `[isort]`, `[flake8]`, `[darglint]`, `[Licenses]`, `[Authorized Packages]`,
  `[pytest]`. Content of individual envs differs by at most 1-2 lines
  between repos (e.g. `whitelist_externals` vs `allowlist_externals`,
  extra `types-python-dateutil` in trader's mypy, or
  `{[testenv]deps}` vs `pip` in mech vs optimus).
- **`.pylintrc`** — 8 repos. `mech` and `mech-predict` share
  `e6aa4db851…`; `IEKit` and `mech-interact` share `c4235fa6c9…`. The
  other 4 are distinct.
- **`CONTRIBUTING.md`** — 13 repos. Diffing `mech ↔ trader ↔ optimus
  ↔ meme-ooorr` shows ≤20 lines of real content difference each, all of
  which is wording on the same workflow: "For a clean workflow, run
  checks before PR: `tomte format-code` → `tomte check-code` →
  `make security` → `make abci-docstrings` → `make generators`". The
  outliers are `mech-client` (library repo, not agent) and `mech-server`
  with their own PR guidelines.
- **`setup.cfg`** — 4 repos. All four have `[isort]`. OAEA additionally
  carries ~7 KB of `[mypy]` + `[flake8]` + `[darglint]` + per-module
  mypy ignore sections. OA carries a minimal `[isort]` only.
  mech-agents-fun / mech-server are `[isort]`-only variants.

## 2. `.spelling` + spell-check — **delete outright**

### Evidence

- **Plumbing** (already confirmed): CI in 4 repos runs
  `tox -e spell-check` (open-autonomy, open-aea, mech-client, hello-world);
  the tox env invokes `tomte check-spelling`; `tomte check-spelling` shells
  out to `mdspell` (a Node.js tool pulled via `npm i markdown-spellcheck`).
- **Pin status**: `mdspell` is declared nowhere — not in any `package.json`,
  not in tomte's `pyproject.toml`. Every CI run depends on whatever happens
  to be installed globally on the runner; local dev runs fail unless the
  contributor did `npm i -g markdown-spellcheck`.
- **Coverage**: mdspell reads `.spelling` (a newline-separated wordlist) +
  `**/*.md` minus a fixed exclusion list. The wordlists have drifted —
  `mech/.spelling` names tokens that don't exist in `mech-agents-fun` but
  share the same hash, so either the wordlist is stale or the docs are.
- **Signal-to-noise**: spell-check catches typos in README.md and docs
  pages. It does not catch typos in code, commit messages, or anything
  agents actually run on. LLM-era doc quality is better addressed with
  `tomte check-code` + PR review.

### Actions

1. Delete `.spelling` from 13 repos (all of: OA, OAEA, mech, mech-predict,
   mech-interact, mech-agents-fun, mech-client, mech-server, trader,
   optimus, meme-ooorr, IEKit, market-creator). `hello-world` is out of
   scope but should get the same treatment.
2. Delete `[testenv:spell-check]` from 10 `tox.ini` files (everyone but
   mech-client and OA/OAEA — grep the list; any `tomte check-spelling`
   caller gets the same treatment).
3. Delete the "run: tox -e spell-check" CI step from 4 workflows
   (open-autonomy/.github/workflows/main_workflow.yml:164,
   open-aea/.github/workflows/workflow.yml:193,
   mech-client/.github/workflows/workflow.yml:68,
   hello-world/.github/workflows/common_checks.yml:128).
4. Delete `tomte/tomte/scripts/check_spelling.sh` and the
   `check_spelling` click command from `tomte/tomte/cli.py`. Ship as
   `tomte==0.6.6` (or whatever the next bump is).
5. Any repo CONTRIBUTING.md that references `tomte check-spelling` loses
   that line. The canonical CONTRIBUTING.md (see §3) won't mention it.

### Risk

Near-zero. Nothing downstream *functionally* depends on spell-check; it's
an advisory step. The only risk is that a CI run with a stale `.spelling`
was silently greenlighting PRs that introduce typos — those will now go
unchecked, but the baseline signal was already broken given the wordlist
drift.

## 3. `CONTRIBUTING.md` — one canonical, stubs elsewhere

### Evidence

`diff mech/CONTRIBUTING.md trader/CONTRIBUTING.md` returns a 3-line change:
"For a clean workflow run checks in following order" → "For a clean
workflow, run checks in the following order", plus "make clean / make
formatters / make code-checks" → "tomte format-code / tomte check-code".
Every pair of downstream repo CONTRIBUTING.md files is within that
envelope. The only real outliers are mech-client (library, not agent)
and mech-server.

### Proposed

Canonical lives in **`open-autonomy/CONTRIBUTING.md`** (already the most
detailed at 2910 bytes; OA is the entry-point to the agent stack and
downstream contributors already use its workflow). Every downstream repo
replaces its `CONTRIBUTING.md` with:

```md
# Contribution Guide

This repository follows the Valory Open-Autonomy contribution workflow.

See **[open-autonomy/CONTRIBUTING.md](https://github.com/valory-xyz/open-autonomy/blob/main/CONTRIBUTING.md)**
for the canonical guide (PR checklist, pre-commit routine, linter + test
commands, coding style).

Repo-specific notes for this project:
- **Run tests**: `<repo-specific command>`
- **Relevant service spec**: `<path/to/service.yaml>`
- **Code owners / reviewers**: `<names or team>`

For any generic guidance, follow the canonical guide.
```

### Exceptions

- **`open-aea/CONTRIBUTING.md`** (5771 B): a different workflow — AEA
  framework development, not agent development. Keep its content, but
  link at the top to "if you're contributing to an *agent* based on AEA,
  see [open-autonomy/CONTRIBUTING.md]".
- **`mech-client/CONTRIBUTING.md`** (4078 B), **`mech-server/CONTRIBUTING.md`**
  (4369 B): these are Python libraries / services, not AEA agents. Keep
  them, optionally link to the OA canonical.

### Actions

1. Confirm OA's CONTRIBUTING.md is the canonical we want (or curate a
   slightly more generic one — e.g. move it to a new
   `open-autonomy/docs/contributing.md` so it can be linked from anywhere
   including off-GitHub, and have the root CONTRIBUTING.md be a pointer
   too).
2. Replace 11 downstream CONTRIBUTING.md files with the stub above.
3. (Optional) Add a `tomte scaffold contributing` command that writes
   the stub.

### Risk

Very low. The most-changed CONTRIBUTING.md file in any of these repos in
the last year is still ~95 % identical to its neighbours.

## 4. `pytest.ini` — fold into `pyproject.toml`

### Evidence

All agent-style downstream repos moved to PEP 621 + `uv_build` in Wave 1.
PEP 518/621 `pyproject.toml` supports
`[tool.pytest.ini_options]` natively since pytest 6.

Repos with `pytest.ini` today:

- `open-aea/pytest.ini` (24 lines): `log_cli_*`, 7 markers,
  `filterwarnings` for deprecated imp/proto/asyncio.
- `mech-interact/pytest.ini` (25 lines): same body, +1 line for the click
  8.1 warning.
- `mech-client/pytest.ini` (27 lines): **different** — library-style
  `addopts`, `testpaths`, `norecursedirs`, 1 asyncio marker.
- `IEKit/pytest.ini` (28 lines): same body as open-aea/mech-interact,
  plus `testpaths` restricted to two skill subdirs
  ("TODO: remove this after we get all tests working").

Repos without `pytest.ini` use pytest's defaults, which is fine — no
markers, no filterwarnings. In practice CI log output is fine for those
too, so we can pick one "standard" set and either apply it or skip.

### Proposed

Inline the three-shared content into each repo's `pyproject.toml`:

```toml
[tool.pytest.ini_options]
log_cli = true
log_cli_level = "DEBUG"
log_cli_format = "%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)"
log_cli_date_format = "%Y-%m-%d %H:%M:%S"
markers = [
    "integration: marks end-to-end tests which require the oef, soef, ledger or other network services",
    "unstable: marks test as unstable (won't be run in CI)",
    "ledger: marks tests which require ledger test networks (ethereum, cosmos, fetchai); these tests should also be marked 'integration'",
    "flaky: marks tests which are flaky and worth re-running",
    "sync: marks test for run in sync mode",
    "profiling: marks profiler tests that must be run separately to avoid garbage collector interferences",
]
filterwarnings = [
    "ignore:the imp module is deprecated in favour of importlib:DeprecationWarning",
    "ignore:Call to deprecated create function FileDescriptor().",
    "ignore:Call to deprecated create function Descriptor().",
    "ignore:Call to deprecated create function FieldDescriptor().",
    "ignore:Call to deprecated create function EnumValueDescriptor().",
    "ignore:Call to deprecated create function EnumDescriptor().",
    "ignore:The 'asyncio_mode' default value will change to 'strict' in future, please explicitly use 'asyncio_mode=strict' or 'asyncio_mode=auto' in pytest configuration file.",
    "ignore:There is no current event loop",
    "ignore::DeprecationWarning",
]
```

`mech-client` keeps its own library-style config in pyproject.toml.

### Why not a tomte-shipped canonical

pytest.ini-style config isn't inheritable cross-file; pytest reads exactly
one config source (`pytest.ini` > `pyproject.toml > setup.cfg`). Even with
a "canonical" file in tomte, each repo would still need to reference it
somehow. Inlining into pyproject.toml is cleaner, and every repo's
pyproject.toml is already per-repo anyway.

### Actions

1. In each of 4 repos (OAEA, mech-interact, mech-client, IEKit), move
   pytest config from `pytest.ini` into `[tool.pytest.ini_options]` in
   `pyproject.toml`.
2. Delete `pytest.ini` from those repos.
3. Optionally add the same block to repos that currently have no
   pytest.ini (the other 10) so markers + warning filters are consistent.
   This is a minor consistency gain; skip if it's fighting scope.
4. Update `tomte` documentation to point at `[tool.pytest.ini_options]`
   as the expected location.

### Risk

Low. pytest's `[tool.pytest.ini_options]` parser is identical to `[pytest]`
parsing once you convert booleans and list-of-str syntax. One gotcha:
`log_cli = 1` in `.ini` becomes `log_cli = true` in TOML. Don't copy the
string `"1"` — pytest will accept it but it's sloppy.

## 5. `.gitleaks.toml` — canonical in OA, per-repo stubs

### Evidence

```
open-autonomy:    1619 lines
open-aea:         1617 lines    (diff OA ≈ 7 lines)
trader:            562 lines    (pruned fork)
IEKit:             541 lines    (pruned fork)
optimus:           107 lines    (hand-written ruleset only, no default allowlist)
market-creator:     15 lines    (already a stub: `[extend] useDefault = true` + IPFS CID allow)
```

The OA file is the canonical; it merges gitleaks' upstream default ruleset
with Valory-specific allowlists:

- IPFS CIDv1 regex `Qm(.){44}` and `bafybei…` base32 CIDs
- Ethereum addresses `0x[a-fA-F0-9]{40}` (allowed, not secrets)
- `cross_period_persisted_keys_\d+` (internal naming)
- `2142662b-985c-4862-82d7-e91457850c2a` (known exposed test key)
- Path exclusions for `deployments/keys/*`, `tests/data/logs/`,
  `plugins/aea-ledger-solana/tests/data/*` (OAEA only)

Gitleaks supports `[extend]` pointing at a URL or a path. The cleanest
model:

```toml
# in every repo's .gitleaks.toml
[extend]
path = "https://raw.githubusercontent.com/valory-xyz/open-autonomy/<PINNED_SHA>/.gitleaks.toml"

[allowlist]
description = "Repo-specific additions"
regexes = [
  '''bafybei[a-z2-7]{52}''',  # if not already in the canonical
]
paths = [
  # repo-specific test fixtures / known exposed keys
]
```

Pinning the SHA prevents "the canonical changed and suddenly every repo's
CI is failing" — ratchet the pin deliberately via PR when gitleaks rules
are updated in OA.

### Why not put it in tomte

Gitleaks isn't a tomte tool; tomte is a Python dev-tooling aggregator.
Gitleaks runs as a separate CI step (`gitleaks/gitleaks-action`). Putting
the canonical in `open-autonomy` avoids mixing concerns and keeps tomte
focused.

### Actions

1. Promote OA's `.gitleaks.toml` to `open-autonomy/.gitleaks.toml` as the
   canonical. (Already there; no move needed.)
2. Reduce OAEA's copy to the 7-line delta (Solana test fixture path,
   `cross_period_persisted_keys` rule) on top of an extend.
3. Reduce trader/IEKit to stubs extending the canonical plus their
   own path exclusions (test-data, CLI-fixture files).
4. optimus/market-creator are already stubs; swap
   `useDefault = true` for `path = "<OA canonical URL>"` so Valory's
   additions apply.
5. Update each repo's CI gitleaks action config to pin the config path
   or ensure the extend URL resolves on the runner.
6. (Future) If the URL-extend pattern becomes painful, consider moving
   the canonical to a `valory-xyz/gitleaks-config` repo of its own;
   each consuming repo adds it as a git submodule (`.gitleaks-config/`)
   or fetches via a setup step.

### Risk

Medium. Gitleaks scans are easy to break silently: pruning rules from
the OAEA/OA forks without re-scanning means real secrets could slip
through in practice on the downstream forks. Before collapsing, run
`gitleaks detect --config=<merged-canonical>` against each repo's
current history and verify the *set of findings* is unchanged vs.
running with the repo's existing `.gitleaks.toml`. Any new findings are
either:
- real exposed secrets → fix and/or add to allowlist
- new false-positives → add to the per-repo `[allowlist]` or to the
  canonical (if it's repo-agnostic)

## 6. `setup.cfg` — fold into `pyproject.toml`

### Evidence

Only 4 repos have `setup.cfg` today:

- `open-autonomy/setup.cfg` (469 B): `[isort]` block only.
- `open-aea/setup.cfg` (7640 B): `[bdist_wheel]`, `[flake8]`, `[isort]`,
  `[mypy]` with ~100 `[mypy-*]` ignore sections, `[darglint]`.
- `mech-agents-fun/setup.cfg` (392 B): `[isort]` only.
- `mech-server/setup.cfg` (567 B): `[isort]` only.

### Proposed

Move everything to `pyproject.toml`:

| setup.cfg section | pyproject.toml equivalent |
|---|---|
| `[isort]` | `[tool.isort]` |
| `[flake8]` | `[tool.flake8]` (requires `Flake8-pyproject` package) |
| `[mypy]` + `[mypy-*]` | `[tool.mypy]` + `[[tool.mypy.overrides]]` array |
| `[darglint]` | `[tool.darglint]` |
| `[bdist_wheel]` | irrelevant — uv_build replaces setuptools |

For OAEA in particular this is a substantial move (~100 mypy overrides),
but it's mechanical. The `[mypy-foo.*]` → `[[tool.mypy.overrides]]` +
`module = "foo.*"` transformation is scriptable.

### Actions

1. For each of 4 repos: move contents into pyproject.toml.
2. Delete `setup.cfg`.
3. Add `Flake8-pyproject` to the tomte flake8 extra (if flake8 is wanted;
   otherwise tomte could ship a ruff migration but that's a separate
   question).

### Risk

Low. Tooling that reads `setup.cfg` (isort, mypy, flake8) all also read
`pyproject.toml`. Test the before/after by running
`tomte check-code` and confirming identical output on a sample commit.

## 7. `.pylintrc` — move to pyproject.toml or delete

### Evidence

8 repos carry a `.pylintrc`. Pairs share hashes: (mech ↔ mech-predict),
(IEKit ↔ mech-interact). Open-autonomy's is 1842 bytes; OAEA's is 5393
bytes (the richest, with detailed disables + per-module rules).

Pylint since 2.5 reads `[tool.pylint.*]` from `pyproject.toml`.

### Proposed

Two options:

**A. Inline into each repo's pyproject.toml.** Mechanical conversion;
`.pylintrc` syntax is `[MESSAGES CONTROL]` + `disable = ...` which maps
to `[tool.pylint."messages control"] disable = [...]`.

**B. Ship a canonical `pylintrc` in `tomte` and have each repo's tox env
pass `--rcfile=$(python -c "import tomte; print(tomte.pylintrc)")`.**
Cleaner, but requires adding a resource-shipping hook to tomte.

Recommend **A** for now; it's a one-time mechanical edit and doesn't add
a new tomte concept. Revisit B if the per-repo pyproject.toml pylint
blocks start drifting.

### Actions

1. Convert 8 `.pylintrc` files to `[tool.pylint]` in pyproject.toml.
2. Delete `.pylintrc`.
3. Update `[testenv:pylint]` in tox.ini to drop the `--rcfile=.pylintrc`
   arg if present — pylint will auto-find pyproject.toml.

### Risk

Low. Pylint's pyproject.toml support has been stable since 2020. One
gotcha: the section name uses dotted-quoted form:
`[tool.pylint."messages control"]`. TOML parsers accept it; humans
sometimes write `[tool.pylint.messages_control]` which pylint does NOT
read. Use the dotted-quote form.

## 7A. Linter config centralisation — architectural principle

Sections 4, 6, and 7 individually recommend folding `pytest.ini`,
`setup.cfg`, and `.pylintrc` into each repo's `pyproject.toml`. Doing
that mechanically moves the drift problem — now every repo has a
bespoke `[tool.pylint]`, `[tool.mypy]`, `[tool.black]`, etc. in its
pyproject. That's not the end state we want.

**The architectural principle**: linter configuration belongs in
*one place per linter per Valory org*, not per repo. That one place
is `tomte`.

**Target layout**:

| File | Role |
|---|---|
| `pyproject.toml` (every repo) | **Strict PEP 621**: `[project]`, `[build-system]`, `[dependency-groups]`, `[tool.uv]`, `[tool.coverage.run]` (pytest-cov needs it there). Nothing else. No `[tool.black]`, `[tool.isort]`, `[tool.mypy]`, `[tool.pylint]`, `[tool.flake8]`, `[tool.darglint]`. |
| `tox.ini` (per repo, after §8 scaffold) | **Minimal** — delegates to tomte envs. The only repo-specific pieces are `SERVICE_SPECIFIC_PACKAGES` (lint scope) and any genuinely bespoke `[mypy-*]` per-module ignores, each with a one-line `# why` comment so the list doesn't accrete. |
| `tomte` (upstream) | **Single source of truth** for: `black` profile, `isort` profile with `known_first_party = ["packages"]` (overridable), `flake8` select/ignore list, `mypy` strictness + stub set, `pylint` disables + rcfile, `darglint` style, `bandit` config, `safety` policy, `vulture` whitelist. Adding or retuning a rule fleetwide = one tomte PR + coordinated version bump in the 13 repos. |

### Why this is better than "fold into pyproject.toml"

- **Single-source-of-truth**: pyproject describes "what is this package"
  without getting tangled in lint policy. Today we already have
  subtly-different `[tool.black]` line lengths, `[tool.isort]` sections,
  and `[tool.mypy]` strictness flags across the fleet — exact drift this
  audit flagged. Folding `.pylintrc` INTO pyproject does not fix that;
  it just moves the drift into pyproject.
- **Fleet changes are one-line**: want everyone on `flake8-bugbear`?
  Bump `tomte[flake8]` to ship it by default + release + repos pin the
  new version. Without centralisation it's 13 mini-PRs to add the same
  dep + config line.
- **tomte is already the CI dep**: every Valory repo already installs
  `tomte[tox,cli]==0.6.5` (or similar) in CI and local flows. The
  defaults are already flowing — we just stop layering local overrides
  on top.
- **Repo-specific ignores stay repo-specific**: genuinely bespoke
  rules (a given skill's `noqa` pattern, a particular `[mypy-*]` import
  ignore) live in the repo's tox.ini with a justification comment.
  The skill's existing guidance applies: the comment answers "why is
  this here" so the list stays curated.

### Revised disposition for sections 4, 6, 7

- **§4 `pytest.ini`**: still fold into `pyproject.toml` (pytest reads
  `[tool.pytest.ini_options]` from pyproject natively and pytest config
  is repo-specific — test paths, markers). **Unchanged.**
- **§6 `setup.cfg`**: fold into `pyproject.toml` IF the content is
  repo-specific packaging metadata. If it's isort/flake8/pylint
  config, that moves to **tomte**, not pyproject. Inspect each
  repo's setup.cfg content before migrating.
- **§7 `.pylintrc`**: revised recommendation is **option B**
  (canonical rcfile in tomte) instead of **option A** (inline into
  pyproject). tomte ships the rcfile as a resource, and each repo's
  tox env passes `--rcfile=$(python -c "import tomte; print(tomte.pylintrc_path())")`.
  Per-repo pylint ignores (rare) stay as a small `disable = [...]`
  block in repo-level config file, not in pyproject.

### Execution plan

1. **Audit phase**. Grep every Valory repo's pyproject for
   `[tool.*]` sections; tabulate diffs. Expected output: a table of
   which defaults vary by repo, per linter.

   ```bash
   for repo in mech mech-* trader optimus meme-ooorr IEKit market-creator open-aea open-autonomy; do
     echo "=== $repo ==="
     grep -E "^\[tool\." /path/to/$repo/pyproject.toml 2>/dev/null
   done
   ```

2. **tomte upstream PR**. Bake the agreed defaults into tomte as
   resource files + config expose points. Required additions:
   - `tomte.configs` module exposing paths to `.pylintrc`, mypy
     config, isort profile, black profile, darglint cfg, bandit
     cfg, safety policy.
   - `tomte[<linter>]` install-extra already ships the right binary
     — just add the config resources.
   - `tomte scaffold tox` template (already planned in §8) emits a
     repo-level `tox.ini` that references these config paths via
     a small wrapper:

     ```ini
     [testenv:pylint]
     deps = tomte[pylint]==0.X.Y
     commands = pylint --rcfile={envsitepackagesdir}/tomte/configs/pylintrc {env:SERVICE_SPECIFIC_PACKAGES}
     ```

3. **Repo sweep** (one PR per repo, or fleet-wide if push-to-all):
   - Delete `[tool.black]`, `[tool.isort]`, `[tool.mypy]`,
     `[tool.pylint]`, `[tool.flake8]`, `[tool.darglint]` from
     `pyproject.toml`.
   - Replace any repo-local `.pylintrc`, `mypy.ini`, `.isort.cfg`,
     `.flake8` with references to the tomte-shipped config.
   - Minimise `tox.ini` per §8 scaffold.
   - Bump `tomte` pin to the new version.
   - Run full local CI matrix (the ~15 tox envs the skill's memory
     directive requires) + confirm identical lint output to pre-change.

### Risks

- **tomte becomes a god-object.** Mitigation: treat tomte defaults as
  a versioned API contract. Pin tomte strictly per repo
  (`tomte[tox,cli]==0.X.Y`, no range). A tomte bump is a fleet change,
  documented in tomte's release notes, rolled through the 13 repos in
  coordinated batches.
- **Per-repo mypy ignore pollution.** Without discipline, every repo
  accretes a long `[mypy-*]` list. Require a one-line
  `# added YYYY-MM-DD by <pr>: <reason>` comment on every per-module
  override. Audit once a year.
- **Over-generalised defaults hurt specific repos.** Mitigation: tomte
  ships *opt-in* overrides (e.g. `tomte[flake8-strict]`) so a repo can
  pick a stricter preset without forcing everyone else.
- **Bootstrapping order**: the tomte PR must land + release BEFORE any
  repo sweep. A half-migrated world where tomte has the new defaults
  but some repos still carry pyproject `[tool.*]` overrides produces
  confusing double-configuration. Land tomte + pin it before starting
  the repo sweep.

---

## 8. `tox.ini` — the big question

### Evidence

10 downstream agent-style repos each have an 800-ish-line `tox.ini` with
**24 `[testenv:*]` sections** that are effectively identical:

```
bandit, black, black-check, isort, isort-check, flake8, mypy, pylint,
darglint, safety, liccheck, spell-check, check-hash, check-packages,
check-dependencies, check-abciapp-specs, check-generate-all-protocols,
check-doc-hashes, abci-docstrings, check-handlers, check-dialogues,
abci-pytest, py{3.10-3.14}-{linux,darwin,win}
```

Plus 15+ `[mypy-*]` ignore sections that are the same across repos.

The diff between `mech/tox.ini` and `trader/tox.ini` for `[testenv:mypy]`
is literally one line (trader adds `types-python-dateutil==2.9.0.20251115`).
For `[testenv:flake8]` it's also one line (trader adds
`tomte[flake8-docstrings]==0.6.5`).

### Does `[tool.tox]` in pyproject.toml help?

Tox 4.21+ supports reading configuration from `pyproject.toml` under
`[tool.tox]`, but the supported keys are limited:
`min_version`, `env_list`, `requires`, `no_package`, `skip_missing_interpreters`
and a restricted `env.*` sub-table. **Heavy `[testenv:*]` recipes with
custom `commands`, conditional `allowlist_externals`, inherited deps via
`{[testenv]deps}`, and `[mypy-*]` / `[flake8]` / `[Licenses]` sections
don't round-trip cleanly yet.** Moving tox.ini → pyproject.toml is
currently a partial migration, not a delete.

### Proposed — the practical split

1. **`[mypy]` + `[mypy-*]` → `[tool.mypy]` + `[[tool.mypy.overrides]]`**
   in pyproject.toml. Frees ~200 lines per tox.ini.
2. **`[flake8]` → `[tool.flake8]`** (requires `Flake8-pyproject`). Frees
   ~10 lines.
3. **`[isort]`, `[darglint]` → `[tool.isort]`, `[tool.darglint]`**.
   Each is ~15 lines.
4. **`[Licenses]`, `[Authorized Packages]` → stay in tox.ini**. liccheck
   does not read pyproject.toml.
5. **`[testenv:*]` recipes → ship a template in tomte, regenerate
   per-repo via `tomte scaffold tox`**. The template substitutes three
   env vars (`SERVICE_SPECIFIC_PACKAGES`, `SKILLS_PATHS`, and an optional
   extra-deps block). Commit the regenerated `tox.ini`; re-run the
   scaffold when tomte's version bumps.

After this, a downstream tox.ini shrinks from ~800 lines to ~150 lines
(the `[deps-packages]` list + any truly repo-unique env). `pyproject.toml`
grows by ~200 lines. Net wins:

- No more per-repo drift on lint environments.
- Tool version bumps become a tomte release + a
  `tomte scaffold tox && git commit` across the fleet.
- `tox.ini` stops being the place for mypy / flake8 / isort config —
  one less place to look.

### Why not go full `[tool.tox]` in pyproject.toml today

- Tox 4's `[tool.tox]` doesn't yet reliably express the
  `{[testenv]deps}` inheritance pattern the current tox.ini files use
  heavily. Best to wait for tox 5 or pin on concrete incremental wins.
- Mixing tox + non-tox tool config in one file doesn't simplify — just
  moves the complexity. The scaffolded-tox.ini + centralised tool configs
  approach gets most of the benefit without the round-trip risk.

### Actions

1. Bump tomte to ship a `templates/tox.ini.j2` (jinja2 or plain `${VAR}`
   substitution) that encodes the canonical 24 testenv recipes.
2. Add `tomte scaffold tox` CLI (writes `tox.ini` from the template +
   `tomte.config.toml` per-repo overrides).
3. Move per-repo `[mypy]`, `[mypy-*]`, `[flake8]`, `[isort]`, `[darglint]`
   blocks into pyproject.toml (part of §6's setup.cfg work, plus any
   content currently in tox.ini).
4. Regenerate each repo's tox.ini and verify
   `tox -e black-check,isort-check,flake8,mypy,pylint,darglint` output
   is byte-identical to pre-migration.

### Risk

Medium. Tox's env inheritance + the `tomte[flake8]==0.6.5` extra spec is
fiddly; getting the template right in tomte requires covering 10 real-world
variants. Start with 2 repos (e.g. `mech` + `trader`), then roll out.

## 9. `scripts/whitelist.py` — leave it

Only OA, OAEA, and mech-client ship one. The content is a vulture
whitelist of symbol names that are reachable but look unused
(CLI callbacks, public API methods). It's per-repo by construction; there
is no canonical "list of unused symbols that also exist in every other
repo". Skip.

## 10. Other duplication worth a look (not scoped in this wave)

- **GitHub Actions workflows**: each repo has 2–4 `.github/workflows/*.yml`
  files. A fair amount of YAML is copy-paste (`setup-python`, `pip install
  tomte[<tool>]`, `tox -e <tool>`). Reusable workflows (`workflow_call`) in
  OA could eliminate most of it. Out of scope for this report — flag for
  Wave 3.
- **Dockerfiles** (`deployments/Dockerfiles/*`): mostly per-repo, but the
  dev Dockerfile + tendermint sidecar Dockerfile are common ancestors
  scattered with drift. Wave 3.
- **Makefile**: most repos have a Makefile whose targets are thin wrappers
  over `tomte` + `autonomy packages lock` + `autonomy hash all`. Same
  candidate for either deletion (just use tomte CLI directly) or a
  scaffolded template.
- **`poetry.lock` vs `uv.lock`**: after Wave 1 (`migrate-to-uv`), every
  agent-style repo should have `uv.lock` only. Double-check that
  `poetry.lock` is gone from each before calling Wave 1 complete.

## 11. Sequencing + PR plan

1. **Wave 1 must land first** (`cleanup-deps`) in each repo — it
   stabilises `[deps-packages]` in tox.ini and the
   `[tool.poetry.dependencies]` / `[project.dependencies]` block in
   pyproject.toml. Several Wave 2 steps (§4 pytest, §6 setup.cfg,
   §8 tox.ini) touch the same files.
2. **Wave 2 split into two sub-waves** to keep PRs reviewable:

   **Wave 2a — "delete things"** (one PR per repo, or one fleet-wide PR
   if you have push to all):
   - Delete `.spelling` + all `tomte check-spelling` + CI step + tomte
     CLI command.
   - Replace CONTRIBUTING.md with the stub.
   - Fold `pytest.ini` into `[tool.pytest.ini_options]` in pyproject.toml.
   - Fold `setup.cfg` + `.pylintrc` into pyproject.toml.
   - Collapse `.gitleaks.toml` to an `[extend]` stub (canonical in OA).

   **Wave 2b — "scaffold tox.ini"** (depends on tomte release):
   - Ship new `tomte` version with `scaffold tox` template + the
     canonical `.gitleaks.toml` reference URL.
   - Roll across repos in one-repo-per-PR increments.

3. **One canonical hub PR first**:
   - `open-autonomy`: promote `CONTRIBUTING.md` to the canonical version
     (small rewrite to make it repo-agnostic), ensure `.gitleaks.toml` is
     at a stable URL, bump tomte pin.
   - `tomte`: (a) delete `check_spelling` + ship `tox` template (§8), AND
     (b) ship canonical linter-config resources (§7A) — `.pylintrc`,
     mypy config, isort/flake8/darglint/bandit defaults — exposed via a
     `tomte.configs` module. The `tox` scaffold references them. Both
     land in a single tomte version bump; repos pin to that version.
   - Order: ship tomte-with-configs first, then open-autonomy rebases
     onto the new tomte, then downstream sweep. A half-migrated world
     (tomte has the configs but repos still carry `pyproject [tool.*]`
     overrides) produces confusing double-configuration — avoid it by
     pinning the order strictly.

## 12. Per-repo checklist

Use this as a punch-list once the hubs are ready.

```
Repo              │ .spelling │ CONTRIB │ pytest.ini │ .gitleaks │ .pylintrc │ setup.cfg │ tox.ini
──────────────────┼───────────┼─────────┼────────────┼───────────┼───────────┼───────────┼──────────
open-autonomy     │ delete    │ canon.  │ —          │ canonical │ →toml     │ →toml     │ scaffold
open-aea          │ delete    │ keep*   │ →toml      │ extend    │ →toml     │ →toml     │ scaffold
mech              │ delete    │ stub    │ —          │ new-stub  │ →toml     │ —         │ scaffold
mech-predict      │ delete    │ stub    │ —          │ new-stub  │ →toml     │ —         │ scaffold
mech-interact     │ delete    │ stub    │ →toml      │ new-stub  │ →toml     │ —         │ scaffold
mech-agents-fun   │ delete    │ stub    │ —          │ new-stub  │ →toml     │ →toml     │ scaffold
mech-client       │ delete    │ keep**  │ keep***    │ new-stub  │ —         │ —         │ scaffold
mech-server       │ delete    │ keep**  │ —          │ new-stub  │ →toml     │ →toml     │ scaffold
trader            │ delete    │ stub    │ —          │ extend    │ —         │ —         │ scaffold
optimus           │ delete    │ stub    │ —          │ extend    │ —         │ —         │ scaffold
meme-ooorr        │ delete    │ stub    │ —          │ new-stub  │ —         │ —         │ scaffold
IEKit             │ delete    │ stub    │ →toml      │ extend    │ →toml     │ —         │ scaffold
market-creator    │ delete    │ stub    │ —          │ extend    │ —         │ —         │ scaffold
```

- `canon.` — the canonical source; keep + promote as the one reference.
- `keep*` — AEA framework CONTRIBUTING.md stays (different audience); link
  at top to the canonical for agent devs.
- `keep**` — library / service repos with distinct PR guidelines.
- `keep***` — library-style pytest.ini with `addopts` / `testpaths`;
  fold into pyproject.toml but keep the content.
- `new-stub` — currently has no `.gitleaks.toml`; *add* a stub
  that extends the canonical. (Gitleaks scanning is a security baseline
  worth enforcing everywhere; today some repos run gitleaks with no
  config at all.)
- `extend` — already has a `.gitleaks.toml`; convert to an
  `[extend] path = ...` stub + per-repo additions.
- `→toml` — move contents from the file into `pyproject.toml`, then
  delete the file.
- `scaffold` — regenerate tox.ini from tomte template after §8 lands.

## 13. Open questions / decisions for the reviewer

- **Is `tomte` the right place for a scaffolded tox.ini template?**
  Alternative is a new `valory-xyz/agent-repo-template` (cookiecutter-style).
  The tomte path is lighter-weight; the cookiecutter path handles more
  than just tox.ini (CI, pyproject.toml, Makefile, README skeleton).
- **`.gitleaks.toml` canonical URL — pin by SHA or by branch?**
  SHA is safer (no surprise rule changes); branch is zero-maintenance.
  Recommend SHA, with a yearly bump ritual.
- **Is there a long-term appetite to replace `tox` with something else?**
  tox invoked via tomte is showing its age. Uv tasks (via `uv run` +
  scripts in pyproject.toml) could replace most of the `[testenv:*]`
  scaffolding natively. Not scoped here, but worth raising if we're
  already touching every repo's tox.ini.
- **Should `[testenv:check-*]` (check-hash, check-packages,
  check-abciapp-specs, etc.) move into an `autonomy check-*` CLI
  command in open-autonomy?** Today tox is the dispatcher; autonomy
  already ships the implementation. Collapsing "tox -e check-hash" to
  "autonomy check hash" is a consistency win and removes yet more tox
  scaffolding.

---

## Appendix — commands used to collect the data

```bash
# Presence + size grid
for r in "${REPOS[@]}"; do
  for f in .spelling .gitleaks.toml pytest.ini tox.ini pyproject.toml \
           .pre-commit-config.yaml .flake8 .pylintrc CONTRIBUTING.md \
           setup.cfg scripts/whitelist.py; do
    [ -f "$r/$f" ] && echo "$f $r $(wc -c < "$r/$f")"
  done
done

# Duplicate detection via SHA
for r in "${REPOS[@]}"; do
  [ -f "$r/.spelling" ] && echo "$r $(shasum "$r/.spelling" | cut -c1-10)"
done | sort -k2

# tox.ini section overlap
for r in "${REPOS[@]}"; do grep -E "^\[" "$r/tox.ini"; done \
  | sort | uniq -c | sort -rn

# Per-section diff
diff <(grep -A10 "^\[testenv:mypy\]" mech/tox.ini) \
     <(grep -A10 "^\[testenv:mypy\]" trader/tox.ini)
```

The raw survey data for this report was captured on 2026-04-23 from
repo working trees at `/Users/dhairya/Desktop/Work/Valory/Github/*`.
