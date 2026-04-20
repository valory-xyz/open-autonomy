# open-aea-helpers

CLI helpers for CI and dependency management in AEA / open-autonomy projects. Ships an `aea-helpers` entry point that bundles the scripts previously scattered across individual repos — dependency consistency checks, doc IPFS hash verification, release preparation, agent/service runners, and a few PyInstaller helpers.

## Installation

```bash
pip install open-aea-helpers
```

## Usage

```bash
aea-helpers --help
```

Common subcommands:

- `aea-helpers check-dependencies` — cross-check package manifest dependencies against tox/pyproject pins
- `aea-helpers check-doc-hashes` — verify (or `--fix`) IPFS hashes embedded in markdown docs
- `aea-helpers bump-dependencies` — bump version pins across the repo in one pass
- `aea-helpers make-release` — release automation
- `aea-helpers run-agent` / `aea-helpers run-service` — thin wrappers around the `aea` / `autonomy` runners

Intended to be invoked from CI jobs and local pre-release checks, not at agent runtime.
