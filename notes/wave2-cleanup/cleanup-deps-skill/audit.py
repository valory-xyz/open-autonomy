#!/usr/bin/env python3
"""
Audit helper for the cleanup-deps skill.

Scans an open-autonomy downstream repo for the cleanup targets identified in
open-autonomy PR #2477 and prints a punch-list of files to edit, grouped by
kind. Does not modify anything.

Usage: python audit.py <repo-path>

Exit code: 0 (always). Output is structured markdown — pipe into the
skill's Step 1 inventory file.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Third-party imports that PR 2477 routes through ledger_api / open-aea helpers.
# Matching any of these in a repo-local contract.py / skill .py is a cleanup
# candidate.
CONTRACT_IMPORT_PATTERNS: List[Tuple[str, str]] = [
    ("web3 (top-level)", r"^\s*(?:from\s+web3[._\s]|import\s+web3\b)"),
    ("eth_abi", r"^\s*(?:from\s+eth_abi\b|import\s+eth_abi\b)"),
    ("eth_utils", r"^\s*(?:from\s+eth_utils\b|import\s+eth_utils\b)"),
    ("eth_typing", r"^\s*from\s+eth_typing\s+import"),
    ("hexbytes", r"^\s*from\s+hexbytes\s+import"),
    ("Crypto.Hash", r"^\s*from\s+Crypto\.Hash\s+import"),
    ("packaging.version", r"^\s*from\s+packaging\.version\s+import"),
    ("py_eth_sig_utils", r"^\s*(?:from\s+py_eth_sig_utils\b|import\s+py_eth_sig_utils\b)"),
    ("solders", r"^\s*(?:from\s+solders\b|import\s+solders\b)"),
]

# Stdlib-reachable imports in skill / framework code.
SKILL_IMPORT_PATTERNS: List[Tuple[str, str]] = [
    ("pytz", r"^\s*(?:import\s+pytz\b|from\s+pytz\s+import)"),
    ("typing_extensions", r"^\s*from\s+typing_extensions\s+import"),
    ("python-dotenv", r"^\s*(?:from\s+dotenv\s+import|import\s+dotenv\b)"),
    ("multiaddr", r"^\s*(?:import\s+multiaddr\b|from\s+multiaddr\b)"),
    ("texttable", r"^\s*(?:import\s+texttable\b|from\s+texttable\b)"),
    ("gql", r"^\s*(?:import\s+gql\b|from\s+gql\b|from\s+gql\.)"),
    ("watchdog", r"^\s*(?:import\s+watchdog\b|from\s+watchdog\b)"),
    ("ipfshttpclient", r"^\s*(?:import\s+ipfshttpclient\b|from\s+ipfshttpclient\b)"),
]

# YAML dependency keys that PR 2477 drops (reached transitively through
# open-aea-ledger-ethereum==2.2.1 / open-aea-ledger-cosmos==2.2.1 or stdlib).
YAML_DROPPABLE_KEYS: Set[str] = {
    "eth-abi",
    "eth-utils",
    "eth_typing",
    "hexbytes",
    "pycryptodome",
    "py-eth-sig-utils",
    "packaging",
    "ipfshttpclient",
    "multiaddr",
    "pytz",
    "typing_extensions",
    "solders",
    "texttable",
    "watchdog",
    "gql",
}

# Names that are often declared but reachable transitively. Flag for manual
# review — don't auto-drop.
YAML_REVIEW_KEYS: Set[str] = {
    "web3",
    "requests",
    "ecdsa",
    "aiohttp",
    "pytest",
    "open-aea-test-autonomy",
    "protobuf",
    "hypothesis",
    "pytest-asyncio",
}

YAML_DEP_LINE = re.compile(r"^\s{2}([A-Za-z0-9_\-]+):\s*($|\{|\'|\")")


def iter_files(root: Path, glob: str) -> List[Path]:
    return sorted(p for p in root.rglob(glob) if "/.git/" not in str(p))


def scan_source(
    files: List[Path], patterns: List[Tuple[str, str]]
) -> Dict[str, List[Tuple[Path, int, str]]]:
    """For each file, find the first line matching any pattern."""
    compiled = [(label, re.compile(rgx)) for label, rgx in patterns]
    hits: Dict[str, List[Tuple[Path, int, str]]] = {lbl: [] for lbl, _ in patterns}
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for label, rgx in compiled:
                if rgx.search(line):
                    hits[label].append((f, lineno, line.strip()))
                    break
    return hits


def scan_yaml_deps(
    files: List[Path],
) -> Tuple[Dict[Path, List[str]], Dict[Path, List[str]]]:
    """Return (droppable_hits, review_hits) keyed by yaml path."""
    droppable: Dict[Path, List[str]] = {}
    review: Dict[Path, List[str]] = {}
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        in_deps = False
        for line in text.splitlines():
            if line.startswith("dependencies:"):
                in_deps = True
                continue
            if in_deps:
                if line and not line.startswith(" "):
                    in_deps = False
                    continue
                m = YAML_DEP_LINE.match(line)
                if not m:
                    continue
                key = m.group(1)
                if key in YAML_DROPPABLE_KEYS:
                    droppable.setdefault(f, []).append(key)
                elif key in YAML_REVIEW_KEYS:
                    review.setdefault(f, []).append(key)
    return droppable, review


def vendored_packages(repo: Path) -> Set[str]:
    """Best-effort: names of AEA packages vendored by open-autonomy.

    These should NOT be edited in a downstream repo — sync via
    `autonomy packages sync` instead. The list is intentionally narrow;
    expand as needed.
    """
    return {
        "gnosis_safe",
        "gnosis_safe_proxy_factory",
        "multisend",
        "erc20",
        "service_registry",
        "service_registry_token_utility",
        "service_manager",
        "registries_manager",
        "component_registry",
        "agent_registry",
        "recovery_module",
        "multicall2",
        "sign_message_lib",
        "staking_token",
        "staking_activity_checker",
        "erc8004_identity_registry",
        "erc8004_identity_registry_bridger",
        "poly_safe_creator_with_recovery_module",
        "squads_multisig",
        "abstract_abci",
        "abstract_round_abci",
        "transaction_settlement_abci",
        "registration_abci",
        "reset_pause_abci",
        "termination_abci",
        "slashing_abci",
        "offend_abci",
        "offend_slash_abci",
    }


def classify(path: Path, vendored: Set[str]) -> str:
    """Return 'vendored' or 'custom' for a packages/**/contract.py path."""
    parts = path.parts
    try:
        idx = parts.index("packages")
    except ValueError:
        return "custom"
    # packages/<author>/<kind>/<name>/...
    if idx + 3 < len(parts) and parts[idx + 3] in vendored:
        return "vendored"
    return "custom"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: audit.py <repo-path>", file=sys.stderr)
        return 2
    repo = Path(sys.argv[1]).resolve()
    if not (repo / "packages").is_dir():
        print(f"! {repo} has no packages/ directory — not an AEA repo.", file=sys.stderr)
        return 2

    vendored = vendored_packages(repo)
    contract_py = iter_files(repo / "packages", "contract.py")
    skill_py = [
        p
        for p in iter_files(repo / "packages", "*.py")
        if "/skills/" in str(p) or "/connections/" in str(p)
    ]
    yaml_files = (
        iter_files(repo / "packages", "contract.yaml")
        + iter_files(repo / "packages", "skill.yaml")
        + iter_files(repo / "packages", "connection.yaml")
    )

    custom_contracts = [p for p in contract_py if classify(p, vendored) == "custom"]
    vendored_contracts = [p for p in contract_py if classify(p, vendored) == "vendored"]

    print(f"# cleanup-deps audit — {repo}\n")
    print(f"- repo-local custom contracts scanned: {len(custom_contracts)}")
    print(f"- vendored contracts (do not edit): {len(vendored_contracts)}")
    print(f"- skill/connection .py files scanned: {len(skill_py)}")
    print(f"- YAML manifests scanned: {len(yaml_files)}\n")

    # --- Bucket 1: custom contract.py with third-party web3/eth_* imports
    print("## Bucket 1 — custom contract.py files needing ledger_api swap\n")
    contract_hits = scan_source(custom_contracts, CONTRACT_IMPORT_PATTERNS)
    files_needing_swap: Set[Path] = set()
    for label, hits in contract_hits.items():
        for f, _ln, _txt in hits:
            files_needing_swap.add(f)
    if not files_needing_swap:
        print("_None — custom contracts already clean._\n")
    else:
        for f in sorted(files_needing_swap):
            rel = f.relative_to(repo)
            labels_for_file = sorted(
                {
                    label
                    for label, hits in contract_hits.items()
                    for hf, _, _ in hits
                    if hf == f
                }
            )
            print(f"- `{rel}` — imports: {', '.join(labels_for_file)}")
        print()

    # --- Bucket 2: skill .py imports that can move to stdlib / aea helpers
    print("## Bucket 2 — skill/connection .py files with swap candidates\n")
    skill_hits = scan_source(skill_py, CONTRACT_IMPORT_PATTERNS + SKILL_IMPORT_PATTERNS)
    files_by_label: Dict[str, Set[Path]] = {}
    for label, hits in skill_hits.items():
        for f, _ln, _txt in hits:
            files_by_label.setdefault(label, set()).add(f)
    any_skill = False
    for label in sorted(files_by_label):
        paths = sorted(files_by_label[label])
        if not paths:
            continue
        any_skill = True
        print(f"### {label}")
        for f in paths:
            print(f"- `{f.relative_to(repo)}`")
        print()
    if not any_skill:
        print("_None — skill/connection code already clean._\n")

    # --- Bucket 3: YAML droppable deps
    print("## Bucket 3 — YAML manifests with droppable `dependencies:` entries\n")
    droppable, review = scan_yaml_deps(yaml_files)
    if not droppable:
        print("_None — YAML manifests already minimal._\n")
    else:
        for f in sorted(droppable):
            print(
                f"- `{f.relative_to(repo)}` — drop: "
                f"{', '.join(sorted(set(droppable[f])))}"
            )
        print()

    print("## Bucket 4 — YAML manifests with entries to review (keep or drop)\n")
    if not review:
        print("_None._\n")
    else:
        print(
            "_These deps may be needed (direct imports) or droppable (transitive via "
            "open-aea-*). Cross-check against the `.py` imports in the same package._\n"
        )
        for f in sorted(review):
            print(
                f"- `{f.relative_to(repo)}` — review: "
                f"{', '.join(sorted(set(review[f])))}"
            )
        print()

    # --- Bucket 5: vendored contracts (never edit)
    print("## Bucket 5 — vendored packages (DO NOT EDIT — sync from OA)\n")
    if not vendored_contracts:
        print("_No vendored AEA packages detected._\n")
    else:
        vendored_names: Set[str] = set()
        for f in vendored_contracts:
            # packages/<author>/contracts/<name>/contract.py → <name>
            parts = f.parts
            try:
                idx = parts.index("packages")
                vendored_names.add(parts[idx + 3])
            except (ValueError, IndexError):
                continue
        for n in sorted(vendored_names):
            print(f"- `{n}` (sync with `autonomy packages sync`)")
        print()

    # --- Next steps
    print("## Next steps")
    print(
        "Feed this inventory into the cleanup-deps skill's Step 2 onward. "
        "Start with Bucket 1 (contract.py swaps — highest-risk, verify parity), "
        "then Bucket 2 (skill .py), then Buckets 3 & 4 (YAML prune). "
        "Do not touch Bucket 5."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
