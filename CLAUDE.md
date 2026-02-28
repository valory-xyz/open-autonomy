# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open Autonomy is a Python framework for creating decentralized multi-agent systems (MAS) that run as autonomous services. Agents coordinate via an ABCI (Application Blockchain Interface) consensus mechanism backed by Tendermint, enabling trust-minimized, transparent operations including on-chain interactions.

Built on top of the **open-aea** (Autonomous Economic Agent) framework. The CLI entry point is `autonomy` (defined in `autonomy/cli/`).

## Common Commands

### Development Setup
```bash
make new_env && pipenv shell
autonomy packages sync --update-packages
pip install --no-deps plugins/aea-test-autonomy
```

### Testing
```bash
# Framework unit tests (autonomy/ and tests/) with coverage
make test

# Test a specific skill (e.g. skill=counter)
make test-skill skill=counter

# Test a specific subpackage with coverage
# tdir = test path (without "test_" prefix), dir = dotted module path
make test-sub-p tdir=connections/test_abci.py dir=connections.abci
make test-sub-p tdir=skills/test_counter/ dir=skills.counter

# Run a single test file directly
pytest -rfE tests/test_autonomy/test_cli/test_analyse.py

# Run tests for a specific package
aea test by-path packages/valory/skills/abstract_round_abci
```

### Formatting & Linting
```bash
# Auto-format code
tomte format-code             # runs black + isort

# Check all code quality
tomte check-code              # runs all linters

# Individual linters via tox
tox -e black-check            # formatting check
tox -e isort-check            # import order check
tox -e flake8                 # style
tox -e mypy                   # type checking (strict, Python 3.14)
tox -e pylint                 # linting
tox -e darglint               # docstring validation (Sphinx style)
```

### Pre-PR Checklist
```bash
make clean
tomte format-code
tomte check-code
make security                 # bandit + safety + gitleaks

# If you modified an AbciApp definition:
tox -e abci-docstrings

# If you modified files in packages/:
make generators               # updates docstrings, copyright, hashes, API docs
make common-checks-1          # checks copyright, hashes, packages

# Otherwise just:
tox -e fix-copyright

# After committing:
make common-checks-2          # checks API docs, ABCI specs, handlers, dialogues
```

### Package Management
```bash
autonomy packages sync        # sync packages with registry
autonomy packages lock        # lock package hashes
autonomy packages lock --check  # verify hashes match
```

## Architecture

### Core Framework (`autonomy/`)
- **cli/** - Click-based CLI (`autonomy` command). Subcommands: analyse, deploy, mint, service, scaffold_fsm, develop, fetch, publish, packages, hash
- **deploy/generators/** - Deployment generation for Docker Compose (`docker_compose/`), localhost (`localhost/`), and Kubernetes (`kubernetes/`)
- **analyse/** - Tools for benchmarking, log analysis, FSM spec validation, handler/dialogue checking
- **chain/** - On-chain configuration and utilities for interacting with Olas registries
- **replay/** - Transaction and state replay utilities
- **configurations/** - Configuration loading/validation for services and deployments
- **services/** - Service abstractions and management
- **data/** - Embedded contracts and Dockerfiles shipped with the package

### Valory Packages (`packages/valory/`)

Packages follow the AEA component model with these types:

- **skills/** - ABCI-based FSM (Finite State Machine) skills. The core abstraction:
  - `abstract_round_abci/` - Base skill providing the round-based ABCI app framework (`base.py` has `AbciApp`, `AbstractRound`, `BaseBehaviour` etc.)
  - `registration_abci/` - Agent registration rounds
  - `transaction_settlement_abci/` - On-chain transaction settlement via Gnosis Safe
  - `reset_pause_abci/` - Reset and pause logic between periods
  - Other skills compose these base skills into complete agent services

- **contracts/** - Solidity contract wrappers (Gnosis Safe, registries, multisend, ERC20, etc.)
- **protocols/** - Communication protocols (abci, tendermint, ipfs, acn_data_share)
- **connections/** - Network connections (abci for Tendermint, ipfs for IPFS)
- **agents/** - Agent configurations that compose skills into runnable agents
- **services/** - Multi-agent service definitions (compose agents into a service)

### FSM App Pattern

The central design pattern is the **FSM App**: skills define a finite state machine where:
1. **Rounds** (`AbstractRound` subclasses) represent consensus states - agents vote/share payloads
2. **Behaviours** (`BaseBehaviour` subclasses) execute logic for each round and send transactions
3. **AbciApp** ties rounds together with transitions into a complete state machine
4. Skills are composed by chaining multiple `AbciApp`s together via `abci_app_chain.py`

### Test Infrastructure
- **plugins/aea-test-autonomy** - Testing plugin providing base test classes and fixtures
- **packages/valory/skills/*/tests/** - Each package has co-located tests
- **tests/** - Framework-level tests mirroring `autonomy/` structure
- Test markers: `integration` (external services required), `e2e` (end-to-end agent tests)

## Code Style

- **Line length:** 88 (Black)
- **Imports:** isort with Black-compatible profile, custom section ordering (FUTURE, STDLIB, THIRDPARTY, FIRSTPARTY, PACKAGES, LOCALFOLDER)
- **Type hints:** strict mypy with `--disallow-untyped-defs`
- **Docstrings:** Sphinx style (`:param:`, `:return:`, `:raises:`)
- **Copyright headers:** Apache 2.0 on all files (auto-fixed via `tox -e fix-copyright`)
- **License policy:** MIT, BSD, Apache 2.0 allowed; GPL/LGPL/MPL prohibited

## Key Dependencies

- `open-aea[all]==2.1.0rc4` - Core AEA framework
- `web3>=7,<8` - Ethereum interaction
- `docker==7.1.0` - Container management for deployments
- `Flask==2.0.2` - Tendermint monitoring server
- `tomte` - Valory's linting/tooling meta-package
