---
name: cleanup-deps
description: Prune unused Python dependencies and replace third-party libs with ledger_api / open-aea helpers across a Valory open-autonomy downstream repo (mech, trader, optimus, mech-interact, etc.). Mirrors the patterns from open-autonomy PR #2477 (chore: minimise autonomy's runtime dependency footprint).
argument-hint: /path/to/repo
---

# Clean up dependencies in an open-autonomy downstream repo

Apply the dependency-minimisation patterns from
[open-autonomy#2477](https://github.com/valory-xyz/open-autonomy/pull/2477) to
the repo at `$ARGUMENTS`. The framework PR removes third-party libs (`web3`,
`eth_abi`, `eth_utils`, `eth_typing`, `hexbytes`, `Crypto`, `packaging`,
`py_eth_sig_utils`, `pytz`, `typing_extensions`, `ipfshttpclient`, `multiaddr`,
`texttable`, `gql`, `watchdog`, `python-dotenv`, Flask/Werkzeug from runtime,
`solders`) by routing through `ledger_api.api.*` and `open-aea` helpers. The
same transformations apply to every downstream repo because they all ship
custom AEA contracts/skills on the same ABI.

**Scope.** This skill does the *downstream-portable* subset only. Some PR 2477
work is framework-only (replacing `autonomy/deploy/_http_server.py`,
`autonomy/chain/subgraph/client.py`, the `[chain]` / `[docker]` / `[hwi]`
extras matrix); those do not apply to downstream consumers.

---

## Pre-flight

1. `cd $ARGUMENTS`
2. Confirm it's a downstream repo (has `packages/valory/` + `pyproject.toml`).
   If it is open-autonomy itself, stop and tell the user to pull PR 2477
   directly rather than re-deriving it.
3. `git status` — require a clean tree.
4. `git checkout main && git pull` (confirm the branch name — some repos use
   `develop` or `master`; check `git symbolic-ref refs/remotes/origin/HEAD`).
5. `git checkout -b chore/dependency-cleanup`
6. Confirm the target open-aea / open-autonomy versions. PR 2477 pins:
   - `open-aea[all]==2.2.1`
   - `open-aea-cli-ipfs==2.2.1`
   - `open-aea-ledger-ethereum==2.2.1` (and `-solana`, `-cosmos`, `-ethereum-hwi`)
   - `open-autonomy>=0.21.0,<0.22.0`
   If the downstream repo targets older versions, stop and ask the user
   whether to bump first (the ledger-api methods this skill relies on —
   `ledger_api.api.codec`, `ledger_api.api.keccak`, `event.topic`,
   `event.process_log`, `ledger_api.api.get_transfer_tx` — landed in
   `open-aea-ledger-*==2.2.1`).

## Step 1 — inventory

Build the change list **before editing anything**. Run the audit helper:

```bash
python .claude/skills/cleanup-deps/audit.py .
```

(or if the script isn't present, inline its logic with `ripgrep`). It should
report four buckets:

- **custom contracts** — `packages/*/*/contracts/*/contract.py` whose imports
  include any of: `web3`, `eth_abi`, `eth_utils`, `eth_typing`, `hexbytes`,
  `Crypto.Hash`, `packaging.version.Version`, `py_eth_sig_utils`, `solders`.
- **custom skills** — `packages/*/*/skills/**/*.py` with the same imports, or
  `import pytz` / `from typing_extensions import ...` (Literal, NewType,
  TypeGuard are all stdlib since 3.10).
- **YAML manifests** — every `contract.yaml` / `skill.yaml` / `connection.yaml`
  whose `dependencies:` block lists any of: `eth-abi`, `eth-utils`,
  `eth_typing`, `hexbytes`, `pycryptodome`, `py-eth-sig-utils`, `packaging`,
  `ecdsa` (non-cosmos use), `ipfshttpclient`, `multiaddr`, `pytz`,
  `typing_extensions`, `solders`, and `web3`/`requests` when the package
  doesn't actually import them directly.
- **pyproject / tox.ini** — same allowlist, plus `texttable`, `gql`, `watchdog`,
  `python-dotenv`, `aiohttp` (stdlib-reachable on 3.10+), and any `[mypy-*]`
  ignore sections pointing at packages we're dropping.

Save the inventory to a scratch file (`/tmp/cleanup-inventory.md`) — we'll
revisit it during verification. Do **not** commit this file.

**Vendored vs. custom.** For each contract/skill the inventory finds, check
whether the package is *re-exported* from open-autonomy (i.e. `valory/gnosis_safe`,
`valory/multisend`, `valory/erc20`, `valory/service_registry`,
`valory/abstract_round_abci`, etc.). If yes, **do not edit** — just sync the
updated hash via `autonomy packages sync` once PR 2477 is merged to the OA
version the repo pins. This skill only edits *repo-local* custom packages.

## Step 2 — contract.py mechanical swap

For every **custom** `contract.py` flagged in Step 1, apply this exact pattern.
Make the edits by hand — do not write a generalised script, because several
cases need judgement (e.g. does a `FilterParams` argument still need `Dict[str, Any]`
or `Union[int, str]`?).

### 2.1 Imports

Drop:
```python
from eth_abi import encode
from eth_utils import event_abi_to_log_topic, to_checksum_address, keccak, decode_hex
from eth_typing import ChecksumAddress, HexAddress, HexStr
from hexbytes import HexBytes
from web3 import Web3
from web3._utils.events import get_event_data
from web3.types import BlockData, BlockIdentifier, EventData, FilterParams, Nonce, TxData, TxParams, TxReceipt, Wei
from Crypto.Hash import keccak
from packaging.version import Version
from py_eth_sig_utils import ...
```

Add (once per file that touches `ledger_api.api.*`):
```python
from typing import Any, Dict, Optional, Union, cast     # add what's missing
from aea_ledger_ethereum import EthereumApi
```

For Solana contracts (e.g. `squads_multisig`):
```python
from aea_ledger_solana import SolanaApi  # type: ignore[import-not-found]  # pylint: disable=import-error
```

### 2.2 Cast at method entry

At the top of **every `@classmethod` / `@staticmethod` that touches
`ledger_api.api.*`**, add:
```python
ledger_api = cast(EthereumApi, ledger_api)
```
(or `SolanaApi` for Solana). Do this even when the method signature already
annotates `ledger_api: EthereumApi` — the cast is cheap at runtime and lets
mypy resolve `ledger_api.api.codec`.

### 2.3 Call-site substitutions

| Old | New |
|---|---|
| `Web3.to_checksum_address(x)` | `ledger_api.api.to_checksum_address(x)` |
| `Web3.keccak(...)` | `ledger_api.api.keccak(...)` |
| `eth_utils.to_checksum_address(x)` | `ledger_api.api.to_checksum_address(x)` |
| `eth_utils.keccak(x)` | `ledger_api.api.keccak(x)` |
| `eth_utils.decode_hex(v)` | `bytes.fromhex(v.removeprefix("0x"))` |
| `eth_abi.encode(types, values)` | `ledger_api.api.codec.encode(types, values)` |
| `eth_abi.default_codec._registry.get_encoder(typ)(arg)` | `ledger_api.api.codec._registry.get_encoder(typ)(arg)` |
| `Crypto.Hash.keccak.new(digest_bits=256, data=x).digest()` | `ledger_api.api.keccak(x)` |
| `HexBytes(bytes.fromhex(s))` | `bytes.fromhex(s)` |
| `HexBytes(x).to_0x_hex()` | `"0x" + x.hex()` |
| `entry["transactionHash"].to_0x_hex()` | `"0x" + entry["transactionHash"].hex()` |
| `ChecksumAddress(HexAddress(HexStr(addr)))` | `ledger_api.api.to_checksum_address(addr)` |
| `Version(v) >= Version("1.3.0")` | `tuple(int(p) for p in v.split(".")) >= (1, 3, 0)` |
| `solders.system_program.transfer(...)` | `ledger_api.api.get_transfer_tx(from_pk, to_pk, lamports)` |

### 2.4 Type substitutions

| Old annotation | New annotation |
|---|---|
| `BlockIdentifier` | `Union[int, str]` |
| `FilterParams` | `Dict[str, Any]` |
| `TxParams` | `Dict[str, Any]` |
| `TxReceipt` / `TxData` / `BlockData` | `Dict[str, Any]` |
| `EventData` | `Dict[str, Any]` |
| `Nonce` / `Wei` | `int` (they're `NewType` wrappers — runtime no-ops) |
| `ChecksumAddress` / `HexAddress` / `HexStr` | `str` |
| Return types `Tuple[TxParams, str]` | `Tuple[Dict[str, Any], str]` |

### 2.5 Event-log pattern

The most error-prone rewrite. Old:
```python
event_abi = contract.events.Foo().abi
event_topic = event_abi_to_log_topic(event_abi)
filter_params: FilterParams = {
    "from_block": from_block,          # ← PR 2477 also fixes: use fromBlock/toBlock
    "to_block": to_block,
    "address": contract.address,
    "topics": [event_topic],
}
w3 = ledger_api.api.eth
logs = w3.get_logs(filter_params)
entries = [get_event_data(w3.codec, event_abi, log) for log in logs]
```

New:
```python
event = contract.events.Foo()
filter_params: Dict[str, Any] = {
    "fromBlock": from_block,           # camelCase — web3 v7 stops normalising snake_case
    "toBlock": to_block,
    "address": contract.address,
    "topics": [event.topic],
}
logs = ledger_api.api.eth.get_logs(filter_params)
entries = [event.process_log(log) for log in logs]
```

The snake_case → camelCase fix is a **real pre-existing bug**: web3.py v7's
`FILTER_PARAM_NORMALIZERS` only normalises `address`, so snake_case keys pass
through and the RPC silently returns the full-range scan. If the repo's
contract still uses `from_block`/`to_block` in filter params, **fix that too**
even if the rest of the method didn't need a ledger_api swap.

### 2.6 Safe-tx bytes

`HexBytes`/web3-level hex helpers often hide a `0x` prefix choice. When
rewriting:
- If the value goes back into a JSON body or `build_transaction["data"]`,
  strip the `0x` prefix *before* `bytes.fromhex`: `data[2:]` or
  `data.removeprefix("0x")`. PR 2477 uses `data[Ox_CHARS:]` with
  `Ox_CHARS = 2` for clarity — follow repo convention.
- When emitting a hex string, use `"0x" + x.hex()`. `HexBytes(x).to_0x_hex()`
  returned the `0x`-prefixed form; plain `bytes.hex()` does not.

### 2.7 Parity verification (mandatory for EIP-712 / safe-hash paths)

Before committing any change that touches EIP-712 encoding, safe-tx hashing,
or multisend `encode_data`: capture a known-good input (a real safe-tx, a
real multisend payload) **on `main`** and record its output bytes. Repeat on
the branch after the rewrite. Require **byte-identical** output. If it
diverges by one byte, the rewrite is wrong.

### 2.8 Helpers that emit hex strings to multisend consumers

**Why this exists.** OA PR #2477 removed the `HexBytes(data)` wrapper
from `multisend.encode_data`. Pre-PR, any downstream contract helper that
returned a hex **string** (e.g. `return {"data": contract.encode_abi(...)}`)
worked by accident — `HexBytes(...)` silently coerced the str to bytes
inside `encode_data`. Post-PR, the same helper causes
`TypeError: can't concat str to bytes` on every multisend delivery
cycle. First discovered by `mech` in PR #435
(<https://github.com/valory-xyz/mech/pull/435>); fix was narrow (two
helpers) — the *expanded* fix is this audit, repo-wide.

**How to audit.** Run before touching anything else in Step 2. Vendored
contracts (multisend, gnosis_safe, etc.) are exempt — they're
synced from OA. Only *custom* contracts are in scope.

```bash
python3 - <<'PY'
import re
from pathlib import Path

EXCLUDE = {
    "multisend", "gnosis_safe", "gnosis_safe_proxy_factory",
    "service_registry", "service_registry_token_utility",
    "service_manager", "registries_manager", "component_registry",
    "agent_registry", "recovery_module", "multicall2",
    "sign_message_lib", "staking_token", "staking_activity_checker",
    "erc20", "erc8004_identity_registry",
    "erc8004_identity_registry_bridger",
    "poly_safe_creator_with_recovery_module", "squads_multisig",
}
ENCODE = re.compile(r"\.encode_abi\(|\.encodeABI\(|\.build_transaction\(.*\)\[['\"]data['\"]\]", re.DOTALL)
COERCE = re.compile(r"bytes\.fromhex\(|HexBytes\(|\.encode\(\)")

for contract_py in Path("packages/valory/contracts").rglob("contract.py"):
    if contract_py.parent.name in EXCLUDE:
        continue
    text = contract_py.read_text(encoding="utf-8", errors="ignore")
    if not ENCODE.search(text):
        continue
    blocks = re.split(r"(?m)^(?=\s{0,8}(?:def |@classmethod|@staticmethod))", text)
    for block in blocks:
        if ENCODE.search(block) and not COERCE.search(block):
            if re.search(r"return\s*(?:\{|dict\()", block) and ("data" in block or "tx_hash" in block):
                m = re.search(r"def\s+(\w+)", block)
                name = m.group(1) if m else "?"
                if name in {"__init__", "get_instance", "get_state", "get_raw_transaction"}:
                    continue
                print(f"{contract_py}:{name}")
PY
```

Any hit is almost certainly a post-bump crash.

**How to fix.** At the helper level — one fix, every caller is safe.

```python
# BEFORE — works on OA < 0.21.19 by accident
contract = cls.get_instance(ledger_api, contract_address)
data = contract.encode_abi(abi_element_identifier="foo", args=[...])
return {"data": data}

# AFTER — required for OA >= 0.21.19
contract = cls.get_instance(ledger_api, contract_address)
data = contract.encode_abi(abi_element_identifier="foo", args=[...])
return {"data": bytes.fromhex(data[2:])}   # strip the 0x prefix
```

Same fix when the source is `build_transaction(...)["data"]`:

```python
# BEFORE
tx_data = contract.functions.foo(args).build_transaction(
    {"gas": MIN_GAS, "gasPrice": MIN_GASPRICE}
)["data"]
return {"data": tx_data}

# AFTER
tx_data = contract.functions.foo(args).build_transaction(
    {"gas": MIN_GAS, "gasPrice": MIN_GASPRICE}
)["data"]
return {"data": bytes.fromhex(tx_data[2:])}
```

The fix must run **before** or **together with** the OA pin bump
(`open-autonomy==0.21.18` → `==0.21.19`) in the same Wave 1 PR.
Shipping the bump without the fix is a live regression that will
surface on every multisend delivery cycle on mainnet.

**Known hits across the Valory fleet (snapshot 2026-04-23):**

| Repo | Helpers | Status |
|---|---|---|
| `mech` | `hash_checkpoint.get_checkpoint_data`, `complementary_service_metadata.get_update_hash_tx_data` | fixed in PR #435 |
| `mech-server` | same 2 helpers (pre-fix copies) | needs fix in Wave 1 |
| `mech-agents-fun` | same 2 helpers | needs fix |
| `mech-predict` | same 2 helpers | needs fix |
| `optimus` | `_encode_call` in `velodrome_cl_pool`, `velodrome_cl_gauge`, `velodrome_router`, `velodrome_non_fungible_position_manager`, `velodrome_gauge` | needs fix |
| `trader` | `conditional_tokens.build_{redeem,merge}_positions_tx`, `relayer.build_{operator_deposit,exec}_tx`, `realitio.{build_claim_winnings,get_submit_answer_tx,build_withdraw_tx}`, `realitio_proxy.build_resolve_tx` | needs fix |
| `mech-client`, `mech-interact`, `meme-ooorr`, `IEKit` | — | no hits |

**Verification.** After applying the fix, at minimum add a unit test
that calls each touched helper and asserts `isinstance(result["data"],
bytes)` — mech PR #435 did this with `TestContractHelpersReturnBytes`
in `task_submission_abci/tests/test_behaviours.py`. If you can reach
testnet, run one multisend delivery end-to-end and confirm no
`TypeError: can't concat str to bytes` in logs.

## Step 3 — contract.yaml dep prune

For each custom `contract.yaml` the inventory flagged, rewrite its
`dependencies:` block to the minimum:

**Drop outright** (reached transitively through `open-aea-ledger-ethereum==2.2.1`):
- `ecdsa` (cosmos keeps it via `open-aea-ledger-cosmos`)
- `eth-abi`, `eth-utils`, `eth_typing`, `hexbytes`
- `pycryptodome`, `py-eth-sig-utils`, `packaging`
- `web3` (unless the `.py` still imports it directly — rare after Step 2)
- `requests` (unless the `.py` still imports it directly)
- `solders` (Solana contracts now use `ledger_api.api.get_transfer_tx`)
- `pytest`, `open-aea-test-autonomy` — **only if** their imports live under
  a `tests/` sub-dir (the AEA dep checker exempts `tests/`). If imports are
  in top-level `contract.py`, keep them.

**Ensure present**:
- `open-aea-ledger-ethereum: {version: ==2.2.1}` for every contract whose
  `contract_interface_paths` includes `ethereum:` **and** whose Python now
  calls `ledger_api.api.*`. PR 2477 added this to 6 contracts that had
  `dependencies: {}`.
- `open-aea-ledger-solana: {version: ==2.2.1}` for Solana contracts.

A truly stateless wrapper (interface-only, no Python beyond class body) can
legitimately end at `dependencies: {}`. PR 2477 left `erc8004_identity_registry`
at `{}` only after confirming its `.py` had no direct third-party imports.

## Step 4 — skill.yaml / connection.yaml dep prune

For each `skill.yaml` / `connection.yaml`, drop deps that aren't in any
*top-level* or `test_tools/` Python file:

- `pytz` → confirm all sites swapped to `datetime.timezone.utc`, then drop.
- `typing_extensions` → confirm all imports moved to `typing` (Literal,
  TypeGuard, NewType are stdlib on 3.10+), then drop.
- `requests` → if only `aea.helpers.http_requests` is used now, drop.
- `ipfshttpclient` → if the only reference was
  `ipfshttpclient.exceptions.ErrorResponse`, swap to
  `aea_cli_ipfs.ipfs_client.IPFSError` and drop `ipfshttpclient`.
- `open-aea-cli-ipfs` → keep only if actually imported; the `ipfs` connection
  itself now uses `aea_cli_ipfs.ipfs_client.IPFSError`.
- `protobuf` → if only needed transitively via open-aea, drop from skill YAMLs
  (keep on `connections/abci/connection.yaml` with range `<7,>=5`).
- `eth_typing`, `hexbytes` — drop (stdlib + open-aea-ledger-ethereum cover it).
- `hypothesis`, `pytest`, `pytest-asyncio`, `open-aea-test-autonomy` — **only
  if** all imports are under `tests/`. If `test_tools/*.py` imports them
  (which isn't exempted by the checker), keep them declared — OR wrap
  `import pytest` in a try/except stub (see Step 5).
- Loosen `py-ecc` from `==8.0.0` → `<10,>=8` (drand BLS API stable 7 → 9).

## Step 5 — source-file Python swaps in skills

Ripgrep and fix each site:

```bash
rg -n "^import pytz|from pytz " packages/
rg -n "from typing_extensions import " packages/
rg -n "^import requests|from requests " packages/   # inside skills / test_tools
rg -n "^from hexbytes import" packages/
rg -n "^from packaging.version import" packages/
```

Transforms:
- `import pytz; pytz.UTC` → `from datetime import timezone; timezone.utc`
- `from typing_extensions import Literal, TypeGuard, NewType` →
  `from typing import Literal, TypeGuard, NewType`
- `requests.get/post` → `aea.helpers.http_requests.get/post` (simple
  drop-in; returns a compatible `Response` wrapper with `.json()`)
- `import aiohttp` — on Py 3.10+ prefer stdlib (`urllib` or `asyncio` + `socket`)
  **only** if the call is one-shot. For anything polling, keep `aiohttp`.
- `from hexbytes import HexBytes` inside skill code → same transforms as
  Step 2.3.
- `packaging.version.Version` → tuple compare (Step 2.3).
- `python-dotenv` → `aea.helpers.base.load_env_file`
- `from Crypto.Hash import ...` → `ledger_api.api.keccak` (if EIP-712-shaped)
  or `hashlib` stdlib otherwise.

### 5.1 Pytest-missing shim for `test_tools/*.py`

If a `test_tools/*.py` file (i.e. *not* under `tests/`) imports `pytest`,
wrap the import so the skill still imports cleanly without pytest installed
(PR 2477 pattern, matches `abstract_round_abci/test_tools/common.py`):

```python
try:
    import pytest
except ImportError:  # pragma: no cover

    class _PytestMissing:  # pylint: disable=too-few-public-methods
        """Stub that raises a clear ImportError when `pytest` is touched."""

        def __getattr__(self, name: str) -> Any:
            raise ImportError(
                "pytest is required to use <skill>.test_tools. "
                "Install with `pip install pytest`."
            )

    pytest = _PytestMissing()  # type: ignore[assignment]
```

This lets the skill YAML drop its `pytest` dep without breaking users who
only import the runtime skill, not the test helpers.

## Step 6 — pyproject.toml / tox.ini cleanup

Strip matching entries from `pyproject.toml` and `tox.ini`. The usual
downstream-repo cleanup (smaller than framework PR 2477):

**`[tool.poetry.dependencies]` removals** — drop if no `.py` imports them
after Steps 2 & 5:
- `pytz`, `typing-extensions`, `ipfshttpclient`, `protobuf`,
  `eth-typing`, `eth-abi`, `eth-utils`, `hexbytes`, `pycryptodome`,
  `py-eth-sig-utils`, `packaging`, `texttable`, `gql`, `watchdog`,
  `python-dotenv`, `multiaddr`, `solders`
- `requests` — defer to transitive `open-aea-ledger-ethereum==2.2.1`
  (`requests>=2.32.5,<3`), drop any explicit upper bound like
  `<2.33.0,>=2.28.1` that conflicts.
- `ecdsa` — defer to transitive `open-aea-ledger-cosmos==2.2.1`
  (`ecdsa>=0.19.2,<0.20`).

**tox.ini cleanup**:
- Drop `[deps-*]` entries for packages we just dropped.
- Drop corresponding `[mypy-*]` `ignore_missing_imports` / `ignore_errors`
  sections (PR 2477 removed 17 dead ones in OA).
- If a custom subgraph-style client exists and gets swapped from `gql`, drop
  `--exclude solders`-style exclusions from the `check-dependencies` command.

**Dependabot / security cleanup (bonus)**:
- `web3` — bump to current minor if pinned (PR 2477 bumped 7.14.1 → 7.15.0
  for CVE-2026-40072).
- `requests` — bump to 2.33.1 if the lockfile pins it below (CVE-2026-25645).

## Step 7 — regenerate fingerprints / hashes / lockfile

After any `packages/` edit, the `fingerprint:` blocks and cascading
`bafybei...` pins are stale. The cascade is: **contracts → skills → agents
→ services**. Regenerate in that order:

```bash
# whichever the repo uses:
autonomy packages lock
# or
autonomy hash all --packages packages/
# fix doc hashes
tox -e fix-doc-hashes     # if the tox env exists
```

Don't hand-edit hashes — always run the tool. If a hash you didn't intend
to change moves, something in the cascade above is dirtier than you think
— don't commit until you understand why.

## Step 8 — guard checks

Run **all** of these in order. Each must pass before moving on:

```bash
tox -e check-hash
tox -e check-packages
tox -e check-dependencies   # the AEA dep checker — catches stale YAML deps
tox -e check-api-docs       # optional; only if the repo ships docs
tomte check-code            # black, isort, flake8, mypy, pylint, darglint
tomte check-security        # bandit, safety, vulture (optional but preferred)
```

Failure modes you'll hit:

- **`check-dependencies` says X is missing** — the YAML declares it but no
  `.py` imports it (dead dep). Drop from the YAML.
- **`check-dependencies` says X is undeclared** — the `.py` imports it but
  the YAML doesn't list it. Add the dep, or (if X is an `open-aea-*`
  variant) make sure the right ledger plugin is declared.
- **mypy fails on `ledger_api.api.codec`** — the `cast(EthereumApi, ledger_api)`
  is missing in that method. Add it.
- **`check-hash` fails** — rerun `autonomy packages lock`. If it still fails,
  a `fingerprint:` entry points at a file that no longer exists (or a file
  exists that isn't listed) — reconcile by hand.
- **mypy complains about `event.topic`** — the contract's web3 pin is
  older than v7. Update `web3<8,>=7.0.0` if the dep is kept.

## Step 9 — PR prep

Commit in logical chunks (mirror PR 2477's commit structure — reviewers find
this much easier than one 3000-line commit):

1. `chore(contracts): replace web3/eth_abi/eth_utils/hexbytes with ledger_api helpers`
2. `chore(contracts): prune unused YAML dependencies`
3. `chore(skills): drop pytz / typing_extensions / requests from source`
4. `chore(skills): prune skill.yaml dependencies`
5. `chore(deps): clean pyproject.toml and tox.ini`
6. `chore(packages): relock fingerprints`

Then:

```bash
git push -u origin chore/dependency-cleanup
gh pr create --title "chore: minimise runtime dependency footprint" \
  --body "$(cat <<'EOF'
## Summary
Mirror of [open-autonomy#2477](https://github.com/valory-xyz/open-autonomy/pull/2477) applied to this repo's custom contracts + skills. Routes all ABI-encoding, keccak, checksum, and event-log decoding through `ledger_api.api.*` (available via `open-aea-ledger-ethereum==2.2.1`) instead of direct `web3` / `eth_abi` / `eth_utils` / `hexbytes` imports. Drops now-transitive deps from YAMLs and `pyproject.toml`.

## Parity verifications performed
- EIP-712 safe-tx hash: byte-identical against `main`.
- Multisend `encode_data`: byte-identical on a realistic tx list.
- Filter-param topics: verified non-empty return on the same block range.

## Test plan
- [ ] `tox -e check-hash`
- [ ] `tox -e check-packages`
- [ ] `tox -e check-dependencies`
- [ ] `tomte check-code`
- [ ] Smoke test at least one on-chain call (mint, service register, or equivalent)

🤖 Generated with [Claude Code](https://claude.com/claude-code) via the cleanup-deps skill
EOF
)"
```

## What NOT to do

- **Don't** edit vendored packages (`valory/gnosis_safe`, `valory/multisend`,
  `valory/service_registry`, `valory/abstract_round_abci`, etc.) in the
  downstream repo — they're authored in open-autonomy and come in via
  `autonomy packages sync`. Editing them locally creates hash drift that
  will break on the next sync. Sync the new OA hashes after PR 2477 merges.
- **Don't** swap `aiohttp` for stdlib unless the call is one-shot. Poll loops
  should keep `aiohttp`.
- **Don't** drop `pytest` from a YAML if the skill imports it at top level
  (not under `tests/`) — use the `_PytestMissing` shim instead.
- **Don't** replace `web3` imports if the code uses actual web3 methods
  beyond `to_checksum_address` / `keccak` / `types` (e.g. `Web3.HTTPProvider`,
  `Web3.from_wei`). Those need real web3; keep the dep.
- **Don't** run `autonomy packages lock --no-check` unless the hash cascade
  is the only reason for failure. Let the tool catch structural mistakes.
- **Don't** collapse multi-step rewrites into a single commit. The parity
  verification is meaningless if a reviewer can't see the pre/post pair for
  a single primitive.

## Reference: the OA PR 2477 commits, mapped to steps

| OA commit theme | This skill's step |
|---|---|
| "sweep 16 contracts for type-only web3/eth_typing imports" | Step 2 |
| "gnosis_safe: thread ledger_api through encode.py" | Step 2 (EIP-712 parity) |
| "squads_multisig: drop solders" | Step 2 (Solana variant) |
| "align every manifest dependencies: block" | Step 3 + 4 |
| "drop stale/unused deps from abstract_round_abci/skill.yaml" | Step 4 |
| "ipfs connection: swap to upstream-inlined client" | Step 5 (ipfshttpclient → IPFSError) |
| "drop python-dotenv" → `aea.helpers.base.load_env_file` | Step 5 |
| "drop typing_extensions and aiohttp" | Step 5 |
| "pyproject rehome main deps" | Step 6 |
| "tox.ini cleanup and check-dependencies satisfaction" | Step 6 |
| "sync ABSTRACT_ROUND_ABCI_SKILL_WITH_HASH" | Step 7 |

Not covered (framework-only):
- `autonomy/deploy/_http_server.py` (Flask/Werkzeug → stdlib)
- `autonomy/chain/subgraph/client.py` (gql → http_requests)
- `[chain]` / `[docker]` / `[hwi]` extras — lazy imports with install-hint ImportErrors
- `texttable` inline ASCII renderer
