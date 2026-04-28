# Contribution Guide

This is the canonical contribution guide for the Valory **AEA-agent** stack
(Open Autonomy + Open AEA + every downstream agent repository under
[valory-xyz](https://github.com/valory-xyz)). Downstream repos stub-link
to this document and add a small "repo-specific notes" footer of their
own.

The repo-specific notes for **this** repository (`open-autonomy`) live at
the bottom of this file under "Notes for `open-autonomy`".

## Creating a pull request

- **Target branch:** double-check the PR is opened against the correct
  branch before submitting.
- **Branch naming:** kebab-case, two or three words at most
  (`some-feature`, `fix/some-bug`, `feat/some-feature`).
- **Tag the relevant ticket/issue:** describe the purpose of the PR with
  context. Apply labels (`enhancement`, `bug`, `test`, ...) where they
  fit.
- **Sensible description:** reviewers should not have to reverse-engineer
  the *why* from the diff.
- **Comment the non-obvious:** invariants, hidden constraints, workarounds.
  Don't restate what well-named code already says.
- **Code reviews:** two reviewers per PR.
- **Linters must pass.** Don't open a PR with red CI.
- **Tests for new behaviour.** New code, new tests; bug fixes get a
  regression test.
- **Cross-impact note.** If the change might affect other branches or
  downstream consumers, say so in the description.

## Pre-commit routine — run on every commit

Run these in order, before every commit. Skipping any one has caused CI
failures in the past, so don't cherry-pick a subset.

```bash
# 1. Auto-format
tomte format-code              # black + isort

# 2. Static analysis
tomte check-code               # black-check, isort-check, flake8, mypy, pylint, darglint

# 3. Security
tomte check-security           # bandit + safety
gitleaks detect                # secret scan (canonical config in this repo)

# 4. Copyright headers
tox -e fix-copyright           # bumps year on every touched file
tox -e check-copyright         # CI-mirror gate

# 5. Dependency consistency
tox -e check-dependencies      # tox.ini ↔ pyproject.toml ↔ packages/*.yaml
```

**If you modified anything under `packages/`**, also run:

```bash
# 6. Regenerate skill/agent artifacts (ABCI docstrings, fingerprints)
tox -e abci-docstrings         # only if an AbciApp definition changed
autonomy packages lock         # re-fingerprint + cascade hashes
tox -e fix-doc-hashes          # IPFS hashes in docs

# 7. Verify
tox -e check-hash
tox -e check-packages
```

**Hashing rule.** Always run `autonomy packages lock` *last*, after every
other edit / lint / format step has settled. Locking earlier is wasted
work — any subsequent edit re-dirties the fingerprints and requires a
re-lock.

**If you added or changed public docstrings:**

```bash
tox -e generate-api-documentation
tox -e check-api-docs
```

## Documentation — docstrings and inline comments

Docstrings are Sphinx-style (`:param:`, `:return:`, `:raises:`).

```python
def some_method(some_arg: Type) -> ReturnType:
    """
    Short imperative summary on the first line.

    Longer explanation if the method is non-trivial. Skip the long form
    when the method is obvious from name + types.

    :param some_arg: what it represents (not its type — types are in the
        signature already).
    :return: what is returned and under what conditions.
    :raises SomeError: when this happens.
    """
```

Inline comments: write them only when the *why* is non-obvious — a hidden
constraint, an invariant, a workaround. If the code already speaks for
itself, no comment.

## Code style

- **Line length:** 88 (Black).
- **Imports:** isort with the Black-compatible profile, sectioned
  `FUTURE → STDLIB → THIRDPARTY → FIRSTPARTY → PACKAGES → LOCALFOLDER`.
- **Type hints:** strict mypy. `disallow-untyped-defs` is on.
- **Guard clauses:** prefer early returns over deep nesting.
- **Copyright:** Apache 2.0 header on every source file
  (auto-applied by `tox -e fix-copyright`).
- **License policy:** MIT, BSD, and Apache 2.0 are allowed;
  GPL / LGPL / MPL are not.

The exact tool versions and the linter configurations live in
[`tomte`](https://github.com/valory-xyz/tomte) and ship as resources
inside the package. Pin `tomte[*]` strictly per repo
(`tomte[tox,cli]==X.Y.Z`, no range). Bumping a tool version is a
fleet-coordinated tomte release, not a per-repo change.

## Running tests locally

Most unit tests run without any extra setup. A subset of the test suite
relies on docker fixtures — anything decorated
`@pytest.mark.integration` / `@pytest.mark.e2e` or pulling in fixture
classes like `registries_scope_class`, `UseACNNode`,
`UseFlaskTendermintNode`, `UseTendermint`, or the `register_reset`
recovery helpers. If you only run unit tests
(`-m 'not integration and not e2e'`), no docker is needed.

If you do need the integration / e2e images:

```bash
docker pull valory/autonolas-registries:latest    # registries_scope_class
docker pull valory/acn-node:latest                # UseACNNode
docker pull tendermint/tendermint:v0.34.19        # UseTendermint
docker pull valory/slow-tendermint-server:0.1.0   # register_reset helpers
```

The Tendermint sidecar image is built locally from
`deployments/Dockerfiles/tendermint/` (path varies by repo — see your
repo's notes section).

## Agent / FSM-app guidance

For repos that ship FSM apps (any AEA-agent service), see the
**[FSM Apps Introduction](https://stack.olas.network/open-autonomy/key_concepts/fsm_app_introduction/)**
in the Open Autonomy documentation for design recommendations.

---

## Notes for `open-autonomy`

This file is the canonical guide for the whole stack, but a few things
are specific to this repository:

- The Tendermint sidecar Dockerfile lives at
  `deployments/Dockerfiles/tendermint/`. Build with:

  ```bash
  TM="deployments/Dockerfiles/tendermint/"
  docker build "$TM" \
    -t valory/open-autonomy-tendermint:0.1.0 \
    -t valory/open-autonomy-tendermint:1.0.0 \
    -t valory/open-autonomy-tendermint:latest
  ```

- `.github/workflows/main_workflow.yml` additionally pulls
  `valory/contracts-amm`, `valory/safe-contract-net`, and
  `trufflesuite/ganache:beta`. Those fixture classes have no callers in
  this repo and can be omitted locally; keep this section in sync with
  the workflow.

- `autonomy/constants.py::ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH` must
  match the hash for `abstract_round_abci` in `packages/packages.json`
  after every `autonomy packages lock`.

- API docs live under `docs/api/**.md` and are regenerated by
  `tox -e generate-api-documentation`. CI runs the check-mode equivalent
  (`tox -e check-api-docs`); if it fails, regenerate and stage the
  result.

- `make security` here is shorthand for `bandit + safety + gitleaks`
  bundled. You can run them individually if you prefer.
