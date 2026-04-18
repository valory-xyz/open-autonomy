# Dependency Footprint Cleanup — Findings & Plan

Intermediate notes from an audit of the dependency footprint across:

- The `autonomy/` Python package (installed via `pip install open-autonomy`)
- The `packages/valory/*` AEA packages (each has its own YAML `dependencies:` block)

Scope: only the two surfaces above. `plugins/`, `deployments/`, `scripts/`, `docs/`, and `tests/` are out of scope.

---

## 1. `autonomy/` framework

### Declared vs. imported

- 41 deps declared across `setup.py` + `pyproject.toml`.
- 15 are actually imported by `autonomy/` code.
- 26 are transitive (mostly via `open-aea[all]` / `open-aea-ledger-ethereum`), test-only, or fully unused.

### Manifest drift bugs (`setup.py` ≠ `pyproject.toml`)

- `pyproject.toml` declares ~22 deps not in `setup.py`: `eth-utils`, `eth-abi`, `eth-account`, `eth_typing`, `py-ecc`, `py-eth-sig-utils`, `pycryptodome`, `ipfshttpclient`, `asn1crypto`, `ecdsa`, `grpcio`, `pytz`, `certifi`, `multidict`, `packaging`, `hypothesis`, `pytest-asyncio`, `toml`, `web3`, `open-aea-ledger-ethereum`, `open-aea-ledger-cosmos`, others.
- **Real bug**: `open-aea-ledger-ethereum` is imported by `autonomy/chain/config.py` but only declared in `pyproject.toml`, not `setup.py`. A plain `pip install open-autonomy` without `pyproject` resolution could be missing it.

### Classification (`autonomy/` only — `packages/` has its own manifests)

| Category | Deps |
|---|---|
| CORE (keep in base) | `open-aea[all]`, `open-aea-ledger-ethereum`, `requests`, `docker`, `jsonschema`, `Flask`, `werkzeug`, `gql`, `hexbytes` |
| CLI-ONLY (move to `[cli]` extra) | `click`, `open-aea-cli-ipfs`, `texttable`, `python-dotenv` |
| TEST-ONLY (move to `[test]` extra or drop) | `pytest`, `coverage`, `hypothesis`, `pytest-asyncio` |
| TRANSITIVE via `open-aea[all]` (drop from explicit list) | `aiohttp`, `protobuf`, `multiaddr`, `pycryptodome`, `ipfshttpclient`, `requests-toolbelt` |
| TRANSITIVE via `open-aea-ledger-ethereum` (drop) | `eth-utils`, `eth-abi`, `eth-account`, `eth_typing`, `py-ecc`, `py-eth-sig-utils` |
| Other transitive (drop) | `certifi`, `multidict`, `packaging`, `asn1crypto`, `ecdsa`, `grpcio`, `pytz` |
| Framework-unused | `watchdog` (only referenced under `deployments/`, not in installed `autonomy` package), `toml` (zero imports) |
| Borderline | `web3` (only TYPE_CHECKING hints in `chain/*.py`), `typing_extensions` (needed for Python 3.10 TypedDict) |

---

## 2. `packages/valory/*` — per-package YAML manifests

### Scale

- ~60 manifests with a `dependencies:` block (skills, contracts, connections, protocols, agents).
- ~28 distinct PyPI names declared across them.
- ~40–50 declarations are unused in the declaring package or are transitive.

### Decl-count leaders with problems

| PyPI name | Manifests declaring | Actually imported by | Notes |
|---|---|---|---|
| `pytest` | 33 | 0 production paths | Test-only; only used in `*/tests/*.py` |
| `open-aea-test-autonomy` | 13 | ~22 (test files) | Test-only |
| `web3` | 17 | ~14 | Mostly transitive via `open-aea-ledger-ethereum` |
| `open-aea-ledger-ethereum` | 13 | ~11 | Over-declared in contracts that don't import it |
| `protobuf` | 10 | 0 in declarers | Transitive; most declare with `any`, a few pin `<6,>=5` — inconsistent |
| `hexbytes` | 6 | 4 | 2 unused declarations |
| `eth-abi` | 5 | 3 | 2 unused; pinned `==5.2.0` mixing with unpinned elsewhere |
| `eth-utils` | 4 | 3 | 1 unused |
| `hypothesis` | 2 (connection+skill) | test files only | Test-only |

### Concrete over-declarations (representative, not exhaustive)

- `contracts/erc20` — declares 8 deps, uses 2 (`web3`, `protobuf`). Drop: `ecdsa`, `eth-abi`, `eth-utils`, `hexbytes`, `open-aea-ledger-ethereum`, `open-aea-test-autonomy`, `packaging`, `py-eth-sig-utils`.
- `contracts/erc8004_identity_registry_bridger` — declares `web3`, never imports it.
- `contracts/gnosis_safe` — declares `ecdsa`, `open-aea-ledger-ethereum`, `open-aea-test-autonomy`, `requests`, none used.
- `contracts/poly_safe_creator_with_recovery_module` — declares `eth-abi`, `eth-utils`, `open-aea-ledger-ethereum`, `open-aea-test-autonomy`, none used.
- `contracts/multisend`, `contracts/squads_transaction_settlement_abci`, `skills/slashing_abci`, `skills/termination_abci` — declare `hexbytes` without importing it.
- `skills/abstract_round_abci` — declares test-only deps (`pytest`, `hypothesis`) and IPFS deps (`ipfshttpclient`, `open-aea-cli-ipfs`) that are only used under `tests/`.
- `connections/p2p_libp2p_client` — declares `open-aea-ledger-ethereum` and `open-aea-ledger-cosmos` without importing them; `asn1crypto`/`ecdsa` appear transitive via libp2p.
- `contracts/squads_multisig` — declares `open-aea-ledger-solana` but actually imports `solders` directly; the AEA ledger is unused.
- `connections/http_client` — `aiohttp` declared twice (once `any`, once `>=3.8.5,<4.0.0`).
- Protocols (`acn`, `acn_data_share`, `contract_api`, `http`, `ipfs`, `ledger_api`, `tendermint`) — all declare `protobuf` but never `import google.protobuf`. Transitive via tendermint/abci.

### Unused declarations to delete outright

- `open-aea-ledger-cosmos` — `connections/p2p_libp2p_client` (no import).
- `open-aea-ledger-solana` — `contracts/squads_multisig` (uses `solders` instead).
- `py-eth-sig-utils` — `contracts/erc20` (no import anywhere in the package tree).

### Version-pin drift to normalise

- `protobuf`: `<6,>=5` in some, `any` in 8 others → pick one.
- `requests`: `<2.33.0,>=2.28.1` in three manifests, `any` in one.
- `ecdsa`: `>=0.15` vs `any`.
- `open-aea-ledger-ethereum`: `==2.2.1` everywhere except one `any`.

---

## 3. Proposed PR sequence

Ordered smallest/safest → largest. Each chunk is independently mergeable.

1. **PR 1 — autonomy manifest drift fix** (low risk, no behavior change)
   - Sync `pyproject.toml` and `setup.py` into agreement.
   - Add `open-aea-ledger-ethereum==2.2.1` to `setup.py` base_deps (fixes the real bug).
   - Strip pyproject-only transitive/unused deps so both files declare the same thing.

2. **PR 2 — autonomy: drop transitive + unused, split extras**
   - Remove `watchdog`, `toml`, `aiohttp`, `protobuf`, `multiaddr`, `requests-toolbelt` from base.
   - Introduce `[test]` extra containing `pytest`, `coverage`.
   - `[cli]` extra stops re-bundling into base.

3. **PR 3 — packages: test-dep cleanup** (mechanical, touches many YAMLs)
   - Remove `pytest`, `hypothesis`, `pytest-asyncio`, `open-aea-test-autonomy` from all production `dependencies:` blocks.
   - Re-run `autonomy packages lock` to update hashes.
   - Verify `aea test by-path ...` still works (test deps must still be available at test time — either via dev extras or test plugin).

4. **PR 4 — packages: eth-stack prune + protobuf normalise**
   - Per-package: remove `eth-*` / `hexbytes` declarations that are transitive via `open-aea-ledger-ethereum`.
   - Normalise `protobuf` constraint (or drop where purely transitive).
   - Re-lock hashes.

5. **PR 5 — outlier cleanups**
   - Delete `open-aea-ledger-cosmos` from `p2p_libp2p_client`.
   - Delete `open-aea-ledger-solana` from `squads_multisig`.
   - Delete `py-eth-sig-utils` from `erc20`.
   - Dedupe `aiohttp` in `http_client`.
   - Clean over-declarations in `contracts/{erc20,gnosis_safe,erc8004_identity_registry_bridger,poly_safe_creator_with_recovery_module}`.

---

## 4. Validation checklist for each PR

- `make test` passes.
- `aea test by-path packages/valory/skills/abstract_round_abci` passes.
- `autonomy packages lock --check` passes.
- `make common-checks-1` (copyright, hashes, packages) passes.
- For PRs touching `packages/`: `tox -e fix-doc-hashes` ran and doc hashes are current.

---

## 5. Open questions

- Should `gql` stay in base or move to an `[ipfs]` / `[subgraph]` extra? It's used only by `autonomy/chain/subgraph/client.py`.
- `web3` is used only under `TYPE_CHECKING` in `autonomy/chain/*.py` — viable to drop from base once a runtime fallback type alias is added, but low value given `open-aea-ledger-ethereum` pulls it anyway.
- Do any downstream services consume `autonomy.test_tools` at runtime (not just at test time)? That would affect whether `pytest` can truly leave base_deps.
