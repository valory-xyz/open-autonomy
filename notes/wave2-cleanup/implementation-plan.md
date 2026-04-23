# Implementation plan — cleanup waves 1 + 2

Companion to `wave2-cleanup-report.md`. Sequenced action items, with
explicit gates so phases don't step on each other. Read the report first
for the rationale behind each line item.

## TL;DR ordering

```
Day 0:  start Wave 1 (cleanup-deps) in every downstream repo  ─┐
Day 0:  start Phase 1 hub work in open-autonomy + tomte       ─┤ parallel
                                                               │
Day N:  Wave 1 PR merges on repo X                             │
        AND Phase 1.1 / 1.2 / 1.3 done                         │
        ──► open Wave 2a PR on repo X                          │
                                                               │
Day M:  Wave 2a merged on repo X                               │
        AND Phase 1.4 (tomte 0.7.0) done                       │
        ──► open Wave 2b PR on repo X                          │
                                                               │
Final:  consistency sweep across the fleet                     ─┘
```

Centralisation (Phase 1, hub work) goes first because downstream PRs
depend on it: stubs link to a canonical URL, `.gitleaks.toml [extend]`
needs a pinnable SHA, and `tomte scaffold tox` needs a template that
only exists after the tomte release.

---

## Phase 0 — Wave 1: run the `cleanup-deps` skill (per repo)

**Start:** immediately (day 0). Does not block on Phase 1.

**Why now:** the skill only depends on `open-autonomy` PR #2477 landing on
`main` (done) and each downstream targeting
`open-aea-ledger-ethereum==2.2.1` (they do). It touches `pyproject.toml`
/ `tox.ini [deps-packages]`, which Wave 2a also touches — so Wave 2a on
repo X must wait for Wave 1 to merge on repo X.

**Per-repo procedure:**

1. Open the skill: `/cleanup-deps /Users/dhairya/Desktop/Work/Valory/Github/<repo>`.
2. Skill produces a per-repo PR (branch `chore/dependency-cleanup`) with:
   - contract.py `web3`/`eth_abi`/`eth_utils`/`hexbytes` → `ledger_api.api.*` rewrites
   - contract.yaml + skill.yaml dep block pruning
   - `pyproject.toml` / `tox.ini` dep prune
   - fingerprint/hash regen
3. Reviewer merges.

**Repos to run on (11):**

- `mech`, `mech-predict`, `mech-interact`, `mech-agents-fun`, `mech-client`,
  `mech-server`
- `trader`, `optimus`, `meme-ooorr`, `IEKit`, `market-creator`

**Signal for "safe to start Wave 2a on repo X":**

```bash
git log origin/main --grep="cleanup-deps\|minimise.*dependency" | head -1
```

returns a non-empty merge commit.

---

## Phase 1 — Hub work (blocking for Phase 2 and 3)

All three (1.1, 1.2, 1.3) can run in parallel; 1.4 is largest and can
also start in parallel but will finish last.

### 1.1 — `open-autonomy`: promote `CONTRIBUTING.md` to canonical

- Rewrite so it reads as repo-agnostic (it's the OA contribution workflow,
  applicable to any AEA-agent repo).
- Keep: pre-commit routine, PR checklist, coding-style rules, `tomte
  format-code` → `tomte check-code` order.
- Remove anything repo-specific ("autonomy" as the code owner etc.) or
  move it to a repo-specific notes box at the bottom.
- Canonical URL:
  `https://github.com/valory-xyz/open-autonomy/blob/main/CONTRIBUTING.md`.
- **Gate:** URL resolves on `main` post-merge.

### 1.2 — `open-autonomy`: settle `.gitleaks.toml` as canonical

- Confirm OA's current `.gitleaks.toml` is what we want every downstream
  to extend. Minor cleanup if needed.
- Merge to `main`.
- **Record the merge SHA** — downstream stubs will pin this SHA in
  their `[extend] path = …/<SHA>/.gitleaks.toml`.
- **Gate:** SHA recorded and documented alongside this plan.

### 1.3 — `tomte`: drop spell-check, release `0.6.6`

- Delete `tomte/tomte/scripts/check_spelling.sh`.
- Delete the `check_spelling` click command from `tomte/tomte/cli.py`.
- Strip spell-check mentions from `tomte/README.md`.
- Bump version in `tomte/pyproject.toml`: `0.6.5` → `0.6.6`.
- Cut release; publish to PyPI.
- **Gate:** `pip install tomte[cli]==0.6.6` resolves;
  `tomte --help` does not list `check-spelling`.

### 1.4 — `tomte`: add `scaffold tox`, release `0.7.0`

- Add `tomte/tomte/templates/tox.ini.j2` encoding the canonical
  `[testenv:*]` recipes. Derive from the most-complete downstream
  tox.ini; strip repo-specific env sections.
- Add `tomte scaffold tox` click command. Reads per-repo overrides from
  `[tool.tomte.scaffold]` in the target repo's `pyproject.toml`:
  `service_specific_packages`, `extra_deps_packages`, `extra_testenvs`.
- Bump version: `0.6.6` → `0.7.0` (minor — new feature).
- Cut release; publish.
- **Gate:** running `tomte scaffold tox` in a clean checkout of `mech`
  after Wave 1 merged produces a `tox.ini` whose lint output
  (`tox -e black-check,isort-check,flake8,mypy,pylint,darglint`) is
  byte-identical to the current one.

---

## Phase 2 — Wave 2a: "delete things" (per repo)

**Starts when:** Wave 1 PR merged on that repo *and* Phase 1.1/1.2/1.3
done.

**One PR per repo.** Title suggestion:
`chore: wave-2a cleanup — spelling + CONTRIBUTING + pytest/setup.cfg/pylintrc → pyproject.toml`.

**Procedure (per repo):**

1. `git checkout -b chore/cleanup-wave2a`
2. **Delete spell-check**
   - `rm .spelling`
   - Remove `[testenv:spell-check]` block from `tox.ini`
   - Remove `- run: tox -e spell-check` step from CI workflow(s)
3. **`CONTRIBUTING.md` → stub** (10 lines, links to canonical). Exceptions:
   - `open-aea`: keep current content; add link to canonical at top for
     "if you're contributing to an agent based on AEA".
   - `mech-client`, `mech-server`: keep current content (library/service
     repos with their own workflow).
4. **`pytest.ini` → `[tool.pytest.ini_options]` in `pyproject.toml`,
   then `rm pytest.ini`.** Repos: `open-aea`, `mech-interact`,
   `mech-client`, `IEKit`.
5. **`setup.cfg` → fold all `[tool.*]` into `pyproject.toml`, then
   `rm setup.cfg`.** Repos: `open-autonomy`, `open-aea`,
   `mech-agents-fun`, `mech-server`. Mapping:
   - `[isort]` → `[tool.isort]`
   - `[flake8]` → `[tool.flake8]` (add `Flake8-pyproject` to tomte
     flake8 extra if not already there)
   - `[mypy]` + `[mypy-*]` → `[tool.mypy]` + `[[tool.mypy.overrides]]`
   - `[darglint]` → `[tool.darglint]`
   - `[bdist_wheel]` → drop entirely (`uv_build` replaces setuptools)
6. **`.pylintrc` → `[tool.pylint]` in `pyproject.toml`, then
   `rm .pylintrc`.** Repos: `open-autonomy`, `open-aea`, `mech`,
   `mech-predict`, `mech-interact`, `mech-agents-fun`, `mech-server`,
   `IEKit`. Use `[tool.pylint."messages control"]` with the dotted-quote
   form.
7. **Collapse `.gitleaks.toml`**
   - If repo currently has a forked copy (OA, OAEA, trader, IEKit):
     1. `gitleaks detect --config=.gitleaks.toml` → capture findings.
     2. Replace with stub:
        ```toml
        [extend]
        path = "https://raw.githubusercontent.com/valory-xyz/open-autonomy/<PHASE_1.2_SHA>/.gitleaks.toml"

        [allowlist]
        description = "repo-specific additions"
        regexes = ['''bafybei[a-z2-7]{52}''']
        paths = [ ... ]  # repo-specific
        ```
     3. `gitleaks detect --config=.gitleaks.toml` → require same findings.
   - If repo has no `.gitleaks.toml` (mech, mech-predict, mech-interact,
     mech-agents-fun, mech-client, mech-server, meme-ooorr): add the
     stub fresh; triage any new findings.
8. **Guard checks** before opening PR:
   - `tomte check-code`
   - `tox -e check-dependencies`
   - `tox -e check-hash`
   - `tox -e check-packages`
   - (if `[tool.pylint]` moved) `tox -e pylint`
9. Open PR.

**Gate to Phase 3:** Phase 2 PRs merged (or at least green + approved)
for every repo.

---

## Phase 3 — Wave 2b: "scaffold tox" (per repo)

**Starts when:** Wave 2a merged on that repo *and* Phase 1.4 done
(tomte `0.7.0` on PyPI).

**One PR per repo.** Title suggestion:
`chore: wave-2b cleanup — scaffold tox.ini from tomte template`.

**Procedure (per repo):**

1. `git checkout -b chore/cleanup-wave2b`
2. Bump `tomte[*]==0.6.6` → `tomte[*]==0.7.0` in every occurrence in
   `tox.ini` and `pyproject.toml`.
3. Add `[tool.tomte.scaffold]` to `pyproject.toml` capturing repo
   specifics (`service_specific_packages`, `extra_deps_packages`,
   `extra_testenvs`).
4. Run `tomte scaffold tox`. Review the diff vs. current `tox.ini`.
5. **Parity check:** for each canonical env, run against both old and
   new tox.ini in separate worktrees:
   - `tox -e black-check`
   - `tox -e isort-check`
   - `tox -e flake8`
   - `tox -e mypy`
   - `tox -e pylint`
   - `tox -e darglint`
   - `tox -e bandit`
   - `tox -e safety`
   Require byte-identical output. If any diverges, adjust the scaffold
   overrides, not the template (the template is canonical).
6. If Phase 2 step 5 or 6 missed any `[mypy-*]` / `[flake8]` / `[isort]`
   section still in `tox.ini`, move it to `pyproject.toml` now. The
   template should not carry these.
7. Guard checks (same list as Phase 2 step 8).
8. Open PR.

**Gate to Phase 4:** every repo has merged Phase 3.

---

## Phase 4 — Consistency sweep

One small PR per outlier.

1. **Tomte pin consistency.** Grep every repo:
   ```bash
   for r in <REPOS>; do
     grep -H "tomte\[.*\]==" "$r/tox.ini" "$r/pyproject.toml" | head -3
   done
   ```
   Require every pin to be the same minor version.
2. **CI `tox -e` env consistency.** Every agent repo should call the
   same canonical lint + check envs. Diff workflows.
3. **Gitleaks canonical pin SHA consistency.** Every stub pins the
   same `<SHA>`. If OA's canonical has moved since Phase 1.2, decide
   whether to re-pin across the fleet (intentional ratchet PR) or not.
4. **Vulture whitelists.** If any repo is failing `tox -e vulture`
   because the whitelist drifted post-Wave-1, update it.
5. Close out — no further waves.

---

## Blocked-on graph

```
                ┌─ Phase 0 (Wave 1, per repo) ─────────────────┐
                │                                              │
                │ Phase 1.1 CONTRIB (OA)    ──┐                │
                │ Phase 1.2 gitleaks (OA)   ──┤                │
                │ Phase 1.3 tomte 0.6.6     ──┤                │
                │                             ▼                ▼
                │                       Phase 2 (Wave 2a, per repo)
                │                                              │
                │ Phase 1.4 tomte 0.7.0     ──────────────────▶│
                │                                              ▼
                │                                 Phase 3 (Wave 2b, per repo)
                │                                              │
                │                                              ▼
                │                                    Phase 4 (sweep)
                └──────────────────────────────────────────────┘
```

Nothing in Phase 0 blocks Phase 1, and vice versa — they run in
parallel. Phase 2 waits on Phase 0 (same repo) + Phase 1.1/1.2/1.3.
Phase 3 waits on Phase 2 (same repo) + Phase 1.4.

---

## Effort estimates

| Phase | Work | Owner surface | ≈ effort |
|---|---|---|---|
| Phase 0 | 11 Wave-1 PRs | 1 person × 11 sessions (skill-driven) + reviewers | 1–2 weeks wall-clock |
| Phase 1.1 | CONTRIBUTING canonical | OA maintainer | half a day |
| Phase 1.2 | Gitleaks canonical SHA pin | OA maintainer | half a day |
| Phase 1.3 | tomte 0.6.6 (drop spell-check) | tomte maintainer | half a day |
| Phase 1.4 | tomte 0.7.0 (scaffold tox) | tomte maintainer | 3–5 days (template + tests + release) |
| Phase 2 | 11–13 Wave-2a PRs | 1 person × 11 sessions | 1 week wall-clock |
| Phase 3 | 11 Wave-2b PRs | 1 person × 11 sessions + parity verification | 1 week wall-clock |
| Phase 4 | Consistency sweep | 1 person | half a day |

Wall-clock, end to end, assuming parallel execution: ~3–4 weeks.

---

## Open decisions (from the report, still pending)

1. **Is tomte the right home for the tox scaffold?** Alternative:
   a dedicated `valory-xyz/agent-repo-template` cookiecutter. Tomte is
   lighter; cookiecutter covers more (CI workflows, Makefile, README
   skeleton).
2. **Pin the gitleaks canonical by SHA or by branch?** SHA (proposed)
   prevents surprise rule changes breaking downstream CI; branch is
   zero-maintenance. Recommend SHA with a yearly ratchet.
3. **Long-term: replace `tox` with `uv run`-based tasks?** Could
   eliminate `[testenv:*]` scaffolding entirely. Not scoped here but
   worth raising while we're already editing every tox.ini.
4. **Move `tox -e check-*` (check-hash, check-packages,
   check-abciapp-specs, …) into `autonomy check-*` subcommands?**
   OA already implements the checks; tox is just the dispatcher.
   Collapsing would remove more tox scaffolding.
