---
name: security-review
description: Security review of an open-autonomy agent service — cryptographic key handling, dynamic code execution, ABCI authentication and replay, secret exposure, dependency supply chain, and deployment hardening
argument-hint: "[path/to/skill or packages/ or service/]"
disable-model-invocation: false
---

# Security Review Skill

You are an expert security reviewer for **open-autonomy** agent services. Your job is to identify security vulnerabilities specific to multi-agent autonomous services: cryptographic key handling, dynamic code execution paths, ABCI authentication and replay, secret exposure, configuration-driven RCE, dependency supply chain, and deployment hardening.

Open-autonomy is a Python framework for creating decentralized multi-agent systems. Source and docs: https://github.com/valory-xyz/open-autonomy

This skill is **complementary** to the other audit skills:

- `/audit-fsm` — FSM correctness and safety. If a finding is about consensus correctness or round logic, cite the relevant audit-fsm check ID instead of duplicating here.
- `/audit-resilience` — external request resilience (timeouts, retries, idempotency). If a finding is about HTTP-level robustness, cite that skill.

Security findings that overlap with those skills (e.g. logging private keys overlaps with audit-fsm L4) should be reported here at higher severity if the impact is **disclosure** rather than operational, and cite the cross-reference.

## How to Use Arguments

- If `$ARGUMENTS` is provided, audit only those paths (e.g. `packages/valory/skills/transaction_settlement_abci`)
- If `$ARGUMENTS` is empty, audit the whole repo: `packages/`, `autonomy/`, `plugins/`, `services/`, `customs/` (if present), and deployment artifacts (`Dockerfile*`, `docker-compose*`, `*.yaml` configs)
- Multiple paths can be space-separated

---

## Open-Autonomy Security Architecture Reference

This section encodes the threat model. Use it as ground truth — do not rely on external documentation.

### Cryptographic Key Lifecycle

Open-autonomy agents hold private keys for one or more chains. Default file locations:
- `ethereum_private_key.txt`
- `solana_private_key.txt`
- `cosmos_private_key.txt`

Loaded by `aea` core via `aea.crypto.wallet.Wallet` (and the underlying `CryptoStore`) at startup. Used for:
- Signing ABCI payloads (each agent's `sender` field on consensus payloads)
- Signing on-chain transactions to a Gnosis Safe (multi-sig) or directly to a contract
- Establishing ACN (Agent Communication Network) identity
- Tendermint validator keys (separate, in `priv_validator_key.json`)

**Threat surface:**
- **Build-time leakage**: key file in container image layer, build artifact, or git history → permanent compromise.
- **Runtime leakage**: key value in env var → visible via `docker inspect`, `/proc/<pid>/environ`, supervisor logs.
- **Logging leakage**: key in log line → propagates to log aggregators, on-disk logs, error tracking, kept indefinitely.
- **Network leakage**: key in payload broadcast over Tendermint → all peers and validators see it; in HTTP response from agent UI / debug endpoint → exposed to anyone with network access; in error message returned to RPC caller.
- **Key derivation leakage**: mnemonic / seed / entropy logged or returned.

A leaked agent key generally allows:
- Submitting valid ABCI payloads as that agent
- Co-signing Safe transactions (in a 1-of-N or quorum-met scenario)
- Exhausting the agent's gas budget on chain
- Impersonating the agent in ACN

### ABCI Authentication and Replay Model

ABCI payloads carry `sender: str` (agent address). The framework verifies via Tendermint signature that the payload was signed by the claimed sender. The round then verifies:
- `sender` is in the active participant set
- Payload type matches the round's `payload_class`
- Threshold rules (e.g. `CollectSameUntilThresholdRound` requires N agents to agree)

**What the framework DOES guarantee (do not re-report as findings against standard rounds):**
- **Cross-period replay protection on standard rounds.** `BaseTxPayload.round_count` is monotonic and never resets across periods. The standard collection rounds (`CollectSameUntilThresholdRound`, etc.) verify it in `process_payload()` (`packages/valory/skills/abstract_round_abci/base.py:1417`): `if payload.round_count != self.synchronized_data.round_count: raise ABCIAppInternalError(...)`. A payload from a closed period therefore cannot be re-submitted in a later period as long as the round's `process_payload` invokes the parent's check.

**What is NOT verified by the framework:**
- **Payload field semantics**: an agent reporting "I have 1 ETH" is not cross-checked against actual on-chain balance. Field-level validation is the round/behaviour author's responsibility.
- **Cross-period replay on custom rounds that bypass the parent check.** Any round that overrides `process_payload()` without invoking the standard `round_count` verification re-opens the replay surface. This is the surface H6 audits.
- **Source authenticity beyond AEA identity**: if an agent's key is stolen, the attacker is indistinguishable from the legitimate agent. There is no per-payload TOFU or out-of-band confirmation.
- **Payload class identity stability**: `_MetaPayload` keys payloads by `"{module}.{ClassName}"`. Renaming the payload class or moving its module breaks deserialization of persisted Tendermint state — and creates a window where two distinct payload types share a registry key during rollout. Cross-reference: `audit-fsm` M1 (`Payload Class Mismatch`) and T6 (`_MetaPayload.registry Not Saved/Restored`).

### IPFS-Loaded Strategy Model (`customs/`)

**Scope caveat.** `customs/` and `FILE_HASH_TO_STRATEGIES` are **downstream service patterns** (e.g. `valory-xyz/trader`, `valory-xyz/optimus`) — they do NOT exist in `open-autonomy` itself. Audits scoped to the framework repo will produce vacuous "no findings" output for this section and for C3. Apply this subsection only when auditing a downstream service that adopts the pattern.

Strategies under `customs/` (e.g. `kelly_criterion`, `fixed_bet`) are loaded by IPFS hash at runtime:

1. The hash is configured in `aea-config.yaml` / `service.yaml` — typically as a param like `FILE_HASH_TO_STRATEGIES` mapping IPFS hashes to strategy module names.
2. Code is fetched from IPFS, the content hash is verified against the configured hash, and the module is **executed in the agent process**.

**Trust boundary:** the configured hash is the only thing standing between the agent and arbitrary code execution. The strategy code runs with full agent privileges:
- Access to private keys via the agent's `Wallet` / `CryptoStore` (`aea.crypto.wallet`)
- Access to environment variables
- Network access to all configured endpoints (RPC, exchange APIs, IPFS)
- Ability to read/write `synchronized_data` (consensus-critical state)

**Threat surface:**
- A wrong hash (typo, misconfiguration, malicious config injection) → agent fetches and executes attacker-chosen code.
- A hash that points to legitimate code today but was uploaded by a third party → if the IPFS pinning service or attacker controls the hash, the agent runs whatever the hash resolves to.
- Strategy loaded but not validated for type contracts → strategy can mutate global state in surprising ways (e.g. monkeypatch `Web3.eth.send_raw_transaction`).

### Configuration / Env-Var Resolution

`skill.yaml`, `aea-config.yaml`, `service.yaml` support env-var interpolation:

```yaml
api_url: ${API_URL:str:https://default.example}
api_key: ${API_KEY:str:dummy}
```

Resolution happens at agent startup. Resolved values flow into `Params` / `Model` instances and are read at runtime by behaviours.

**Threat surface:**
- **`dummy` / empty defaults in production**: if the env var isn't set, the agent runs with the placeholder. Anonymous requests to authenticated endpoints, wrong addresses, "test" keys.
- **Env-vars in `docker-compose.yaml` checked into git**: anyone with read access to the repo has the secret.
- **Env-vars baked into container image layers**: `ENV API_KEY=...` in a Dockerfile persists in the image even if overridden at runtime.
- **Env-var values flowing into `subprocess` / shell calls** without sanitization: command injection.
- **Env-var values used as Python module paths** (`importlib.import_module(os.environ['MODULE'])`): RCE.

### Tendermint Network Surface

Each agent ships with a Tendermint sidecar:
- RPC port (default 26657) — used for ABCI queries, block info, broadcast
- P2P port (default 26656) — peer-to-peer consensus
- ABCI app socket (default 26658) — the port the agent's `abci` connection listens on (`packages/valory/connections/abci/connection.py:110` `DEFAULT_ABCI_PORT`); Tendermint dials in to deliver `CheckTx` / `DeliverTx` etc. A 0.0.0.0 bind here lets any peer drive the application directly, bypassing Tendermint
- gRPC port (default 9090, optional)

**Threat surface:**
- RPC exposed on `0.0.0.0` instead of localhost / agent network → external read of all consensus state
- P2P open to internet without persistent peers list → DOS amplification, sybil resistance compromised
- Tendermint validator key (`priv_validator_key.json`) misplaced or world-readable → consensus signature forgery

### Container / Deployment Threat Surface

`autonomy deploy build` produces docker-compose / k8s manifests. Common defaults:
- Tendermint and agent processes run as **root** in container unless overridden
- Keys mounted via volume from host
- Logs written to mounted volume
- Health/debug endpoints potentially exposed (e.g. Flask Tendermint monitor on port 8080)

**Threat surface:**
- Root container = container escape → host compromise has broader blast radius
- World-readable mounted key file
- Health endpoint that returns synced state, validator info, or agent address without auth
- Debug routes that expose internal state in production builds

### Dependency Supply Chain

Open-autonomy uses `poetry` / `pipenv` and `tomte` for tooling. License policy (per `CLAUDE.md`):
- Allowed: MIT, BSD, Apache 2.0
- Prohibited: GPL, LGPL, MPL

Third-party trading libraries (`py_clob_client`, `web3`, `httpx`, `requests`, exchange-specific clients) are full-trust runtime deps with full keychain access.

**Threat surface:**
- Pinned dep with a known but unpatched CVE
- Typosquat (e.g. `python-requests` vs `requests`, `crpytography` vs `cryptography`)
- Transitive dep without pinning → lockfile drift across CI / dev / prod
- Dev-only dep bleeding into prod (`bandit`, `safety` in runtime container)
- Compromised release of an upstream package (rare but high-impact)
- Unsigned source distribution where wheel is unavailable

The repo's `tox -e safety` allowlist already pins known-unfixed CVEs in transitive deps. Audit the allowlist itself.

---

## Audit Checklist

### Critical (C) — Immediate compromise (RCE, key disclosure, full agent takeover)

#### C1: Dynamic Code Execution on Untrusted Input

**What:** `eval`, `exec`, `compile`, or dynamic import where the input is not statically known. Untrusted input includes anything sourced from: HTTP request, ABCI payload, env var, file content, IPFS, external API response.

**Search patterns:**
- `eval(`, `exec(`, `compile(` — any usage in `packages/`, `customs/`, `autonomy/`
- `importlib.import_module(`, `__import__(` with non-literal arguments
- `pickle.load`, `pickle.loads` on data not produced by the same trust boundary (file written by user, network response, IPFS payload)
- `marshal.loads`, `shelve.open` on untrusted data
- `yaml.load(...)` without `Loader=SafeLoader` — pre-5.4 `FullLoader` had **CVE-2020-14343** (arbitrary object construction); PyYAML ≥ 6.0 raises `TypeError` on missing `Loader`. Always pass `Loader=SafeLoader` (or `yaml.safe_load`) explicitly — even on PyYAML 6 — to be robust against future loader-default changes
- `subprocess.*` with `shell=True` AND interpolated arguments (`f"cmd {var}"`, `"cmd " + var`, `cmd % var`)
- `os.system(` with interpolated arguments
- `Template(...).substitute(...)` where the template itself comes from untrusted input

**Bug example:**
```python
# BUG: payload field interpolated into shell
def process_strategy(self, payload):
    strategy = payload.strategy_name
    subprocess.run(f"python -m {strategy}", shell=True)  # RCE
```

**Fix:** never `eval`/`exec`; use `yaml.safe_load`; use `subprocess.run([cmd, arg1, arg2], shell=False)`; for pickle, sign and verify or replace with JSON.

**Severity escalation:** If the input source is an ABCI payload or IPFS content, this is **unconditionally Critical** — a single malicious / compromised peer can pivot to RCE on every agent.

#### C2: Private Key Disclosure

**What:** Any code path that emits, persists, or returns a private key, mnemonic, seed, or signing material outside the AEA crypto/wallet boundary (`aea.crypto.wallet.Wallet`, `Crypto.sign_message`, `CryptoStore`).

**Search patterns:**
- Variable name regex inside `logger.*`, `print(`, `return`, response builders, payload constructors:
  - `private_key`, `priv_key`, `pk`, `sk`, `secret`, `seed`, `mnemonic`, `entropy`, `signing_key`, `wallet.private_key`
- HTTP handlers that read from the agent's `Wallet` / `CryptoStore` and return values in the response body (debug endpoints in particular)
- Behaviours that interpolate signed material into `payload` fields broadcast over Tendermint
- Files written by the agent that contain key material (`open(..., 'w')` with key in body)
- Exception handlers that include the key in the error message (`raise ValueError(f"Bad key: {key}")`)
- `__repr__` / `__str__` of wallet / signer objects that includes the key

**Bug example:**
```python
# BUG: full HTTP response body logging includes Authorization header containing the agent key
self.context.logger.info(f"Sent: {request}, Got: {response.json()}")
# request includes signed message that derives from the private key
```

**Cross-reference:** audit-fsm L4 covers this at the operational level. /security-review escalates to Critical because the impact is permanent disclosure.

**Fix:** never log key material; redact in `__repr__`; constrain key access to a single module that exposes only `sign(...)` not `get_key()`; review every debug endpoint.

#### C3: IPFS Strategy Hash Trust Bypass

**What:** Code paths that load Python modules from IPFS without hash verification, OR that allow the configured hash to be derived at runtime from untrusted input.

**Search patterns:**
- IPFS fetch + `importlib` / `exec` / `compile` of fetched bytes
- `FILE_HASH_TO_STRATEGIES` (or similar param) populated from external source rather than static config
- `customs/` loader code that fetches and evaluates without hash check
- Hash configured via env var that defaults to placeholder (`dummy`, empty) — production agents may run with unverified strategy

**Threat:** the IPFS hash IS the trust boundary. Bypassing it = arbitrary code execution with full agent privileges (keys, network, on-chain authority).

**Fix:** statically configure hashes; verify content hash matches configured hash before executing; reject placeholder defaults in production builds.

#### C4: Unsafe Deserialization on ABCI / Network Boundary

**What:** Connection / handler code that deserializes inbound payloads using formats that allow code execution (`pickle`, `yaml.load`, `marshal`).

**Search patterns:** in `connections/*/connection.py`, `handlers.py`, ABCI message handlers:
- `pickle.loads(message.body)`, `pickle.loads(srr_message.payload)`
- `yaml.load(...)` without `Loader=SafeLoader`
- `marshal.loads(...)`
- Custom deserializers that `eval` field values

**Distinct from `audit-resilience` BP14.** BP14 audits whether the connection's `on_send` / `_route_request` catches `JSONDecodeError` from `json.loads(message.payload)` — i.e. a malformed-input robustness concern. C4 audits whether the deserializer itself is code-executing — i.e. an RCE concern. A connection can simultaneously have a BP14 finding (no exception handling) and a clean C4 (uses `json.loads`), or vice versa (uses `pickle.loads` inside a generous try-except → C4 finding without BP14). Different threat classes; report independently.

**Fix:** use JSON; if a binary format is needed, use protobuf / msgpack with strict schemas.

#### C5: Hardcoded Secrets in Source Tree

**What:** API keys, JWTs, mnemonics, private keys, OAuth tokens, AWS credentials, or webhook URLs with embedded tokens, committed in source.

**Tooling:** `tox -e gitleaks` runs in CI. /security-review re-runs and reviews:
- The current `gitleaks.toml` allowlist for over-broad patterns
- New files added in the audit scope
- Test fixtures that may have been accidentally promoted to runtime code paths

**Search patterns** beyond gitleaks defaults. Gitleaks's built-in rules already cover common SaaS / cloud token shapes (Slack, GitHub, GitLab, AWS, Stripe, JWT, OpenAI, etc.) — do NOT re-list those literals here, listing them would re-trigger gitleaks on this file. Audit-specific additions:
- `0x[a-fA-F0-9]{64}` — 32-byte hex **shape** in non-test files. **High false-positive rate**: the same form matches Ethereum transaction hashes, block hashes, Keccak-256 outputs, storage-slot keys, IPFS CID v1 binary fields, and any `bytes32` literal. Triage before flagging: require proximity to a variable name in `{key, secret, mnemonic, pk, sk, private}`, OR exclude matches adjacent to `{tx_hash, block_hash, ipfs_hash, topic, slot}`. Without this triage, the rule fires on every block-hash literal in tests and tooling AND lets reviewers dismiss real keys as "just a hash"
- `mnemonic = "..."`, mnemonic-shaped 12/15/18/21/24-word strings in source

**Severity:** Critical regardless of intent — once committed, must be assumed compromised even after removal (git history retention).

**Fix:** rotate the disclosed credential; remove from history (`git filter-repo`); replace with env-var or secrets-manager reference; add to `gitleaks.toml` as a tested negative.

#### C6: Command Injection via Shell-Subprocess Interpolation

**What:** `subprocess.*(..., shell=True)` or `os.system(...)` where any argument is composed from external input (env var, payload field, HTTP query param, file content).

**Search patterns:**
- `subprocess.run(`, `subprocess.call(`, `subprocess.Popen(` with `shell=True`
- `os.system(`, `os.popen(`
- `commands.getoutput(` (if Python 2 legacy), `pty.spawn(`

For each, check whether arguments are static literals or interpolated.

**Bug example:**
```python
# BUG: agent_id from HTTP request flows into shell
@app.post("/restart")
def restart(agent_id: str):
    subprocess.run(f"systemctl restart agent-{agent_id}", shell=True)
```

**Fix:** `shell=False` and pass argv as a list; use `shlex.quote` for unavoidable shell paths; validate via allowlist before interpolation.

---

### High (H) — High-impact issues short of immediate RCE

#### H1: Env-Var-Driven Authentication with Insecure Defaults

**What:** `service.yaml` / `aea-config.yaml` / `skill.yaml` with env-var-interpolated auth credentials whose default is `dummy`, empty string, or a placeholder. Production deployments depend on the env var being set; if it isn't, the agent runs unauthenticated or with shared known-bad credentials.

**Search patterns** in YAML configs:
- `${[A-Z_]+:str:dummy}`, `${[A-Z_]+:str:}`, `${[A-Z_]+:str:test}`, `${[A-Z_]+:str:placeholder}`
- Param names matching `*_api_key`, `*_token`, `*_secret`, `*_password`, `*_credential`
- Param names matching `*_url`, `*_endpoint` where placeholder is suspicious (`localhost`, `example.com`)

**Fix:** require env var (no default), or default to a value that **fails closed** (e.g. an unauthenticated client that only allows read-only ops); add a startup check that refuses to run with placeholder values in production mode.

#### H2: Hardcoded Secrets in Deployment Artifacts

**What:** Secrets in `docker-compose.yaml`, `Dockerfile*`, `kubernetes.yaml`, `helm/` charts, GitHub Actions workflows, or `.env*` files committed to the repo.

**Search patterns:**
- `Dockerfile*`: `ENV API_KEY=`, `ARG SECRET=`, `RUN echo "..." > /key`
- `docker-compose.yaml`: literal values in `environment:` blocks (vs `${VAR}` references)
- `.github/workflows/*.yml`: literal tokens (vs `${{ secrets.X }}`)
- `.env`, `.env.local`, `.env.production` committed to git (these should be in `.gitignore`)
- `kubernetes/*.yaml`: `data:` blocks with base64-encoded plaintext (Secret manifests)

**Fix:** use Docker secrets / Kubernetes Secret resources with mounted files; use GitHub Actions encrypted secrets; ensure `.env*` is gitignored; rotate any value found.

#### H3: Container Running as Root

**What:** Dockerfiles without a `USER` directive, or with `USER root`, leave the agent process running as root inside the container.

**Search patterns:** `Dockerfile*`, especially `deployments/Dockerfiles/*/Dockerfile`:
- Absence of `USER` directive (Docker default = root)
- `USER root` explicitly set
- `RUN chown -R root:root /app` patterns

**Why high not critical:** root-in-container isn't immediate RCE on the host, but combined with any container-escape CVE (e.g. cgroup vulnerabilities, kernel bugs), the blast radius is much larger than non-root.

**Fix:** create a non-root user (`adduser --system --no-create-home agent`), `USER agent`, ensure mounted key files are readable by that uid only.

#### H4: Tendermint RPC Exposed Beyond Local Network

**What:** Tendermint RPC port (default 26657) bound to `0.0.0.0` or exposed in `docker-compose.yaml` `ports:` section without auth.

**Search patterns:**
- `docker-compose*.yaml`: `ports:` entries that publish 26657 / 26656 to the host
- Tendermint config (`config.toml`): `laddr = "tcp://0.0.0.0:26657"` instead of `tcp://127.0.0.1:26657`
- Kubernetes Service manifests with `type: LoadBalancer` for Tendermint

**Threat:** Tendermint RPC exposes block data, validator info, mempool state, and (in some configurations) `broadcast_tx_*` endpoints that allow anyone to submit transactions.

**Fix:** bind to localhost or to the agent-internal network; use a network policy / firewall to restrict ingress; require auth proxy for any external RPC access.

#### H5: ABCI Payload Field Validation Gaps

**What:** Payload fields read by `end_block()` or `process_payload()` that are used in security-sensitive contexts (signing material, addresses, amounts, contract addresses, URLs) without explicit validation.

**Search patterns:**
- Round / behaviour code that reads `payload.<field>` and uses it for: `Web3.toChecksumAddress(...)`, `Account.sign_message(...)`, contract write calls, HTTP requests to user-controlled URLs
- Payload classes whose fields are typed as `str` or `Any` (no Pydantic / dataclass-validation hooks)

**Threat scenario:** a compromised agent submits a payload with a malicious URL, address, or amount. If the round accepts the payload without bounds-checking, the consensus value drives downstream actions across all agents.

**Fix:** validate at `check_payload()` (round side) and at payload construction (behaviour side); use strict type hints (`Address`, `URL`, `PositiveInt`); reject out-of-range values.

#### H6: Replay Protection Gaps in Custom Rounds

**What:** Standard collection rounds inherit `process_payload()` from the framework, which verifies `payload.round_count == self.synchronized_data.round_count` (`packages/valory/skills/abstract_round_abci/base.py:1417`). H6 audits the narrower residual surface: **custom rounds that override `process_payload()` without invoking the parent check** (e.g. via `super().process_payload(payload)` or an equivalent `round_count` assertion).

**How to check:**
1. Grep for round subclasses that define their own `process_payload` (`def process_payload(self, payload`).
2. For each, verify the override either:
   - Calls `super().process_payload(payload)`, OR
   - Performs an equivalent `if payload.round_count != self.synchronized_data.round_count: raise ...` check.
3. If neither, this round's payloads from a closed period can be replayed in any later period — flag.
4. For payloads that drive on-chain transactions, also verify the resulting tx includes chain-id, contract nonce, and Safe nonce (these are independent of the ABCI-level check).

**Threat:** an adversary captures a payload signed by a participant in period N and re-submits it in period M to re-trigger a state-changing action. Standard rounds reject this at `process_payload`; overriding rounds may not.

**Distinct from `audit-resilience` BP15.** BP15 protects against the same logical action being re-submitted via FSM retry / connection-layer retry (accidental, internal trigger). H6 protects against an old payload from a closed period being replayed on the consensus layer (adversarial, external trigger). Different attacker model, different mitigation surface — the mitigations partially overlap (idempotency on the action vs nonce/round_count on the payload) but require independent assessment.

**Fix:** in every custom `process_payload` override, either call `super().process_payload(payload)` first, or replicate the `round_count` check explicitly.

#### H7: Dependency CVEs

**What:** Run `tox -e safety` (which uses tomte's allowlist) against the resolved environment. Each unaddressed CVE in a runtime dep is a finding. `pip-audit` is optional second-source coverage but is **NOT pre-configured** in this repo — there is no `[testenv:pip-audit]` stanza in `tox.ini` and `make security` runs only `safety`, `bandit`, and `gitleaks`. If you want pip-audit cross-check, install it manually (`pip install pip-audit`) and run separately; note in the report.

**Process:**
1. Run `tox -e safety`. Optionally `pip install pip-audit && pip-audit -r <lockfile>` for second-source coverage.
2. For each CVE not in the allowlist, document: package, version, CVE ID, severity per upstream, exploitability in this codebase (does the agent reach the vulnerable code path?).
3. Audit the existing tomte allowlist (`-i 37524 -i 38038 ...` in `tox.ini`) — for each pinned CVE, check whether upstream has shipped a fix that allows the pin to be removed.

**Fix:** upgrade the dep; if upgrade is impossible, document the mitigation in the allowlist with a date and re-check quarterly; for unreachable CVEs, document why they don't apply.

---

### Medium (M) — Hardening gaps and weak validation

#### M1: World-Readable Key Files in Container

**What:** Mounted private-key files with permissive mode (`0644`, `0755`), or container-internal copies created without chmod.

**Search patterns:**
- `Dockerfile*`: `COPY ethereum_private_key.txt` without subsequent `RUN chmod 600`
- `docker-compose*.yaml`: volume mounts of key files without explicit `read_only: true`
- Setup scripts that `cp` keys without chmod 600
- Kubernetes Secret mounts with `defaultMode: 0644`

**Fix:** `chmod 600 *_private_key.txt` after copy / mount; use Kubernetes Secret `defaultMode: 0400`; mount read-only.

#### M2: Debug / Health Endpoints Exposing Internal State

**What:** Flask Tendermint monitor (port 8080), agent debug routes, or health endpoints that return more than `{"status": "ok"}` — e.g. agent address, validator info, signed-payload count, configured params, last block.

**Search patterns:**
- `flask.*route(`, `@app.route(`, `@app.get(`, `@app.post(` in `packages/`, `autonomy/`, `deployments/`
- `make_response(`, `jsonify(` returning rich structures
- Response bodies that include `synchronized_data`, `params`, `address`, `validator`

**Threat:** reconnaissance for a targeted attack. Validator addresses + chain → fund tracing; configured RPCs → MITM target list; agent address → on-chain identity disclosure.

**Fix:** strip non-essential fields from health responses; gate debug routes behind `DEBUG=true` env var; require auth for any internal-state endpoint.

#### M3: Weak Validation at HTTP Handler Trust Boundaries

**What:** HTTP handlers in `handlers.py` that accept request bodies without schema validation. Audit-resilience covers crash patterns; /security-review M3 covers exploitability:
- SQL injection in any backing store query (rare in agents but check)
- Path traversal in any handler that reads/writes files based on request input (`open(f"data/{request.name}.json")`)
- SSRF in any handler that makes outbound requests to URLs from the request (`requests.get(request.url)`)
- XXE if XML parsing is used without `defusedxml`

**Search patterns:**
- `open(` with interpolated path component
- `requests.get(...)` with URL from request
- `xml.etree.ElementTree.parse(`, `lxml.etree.parse(` without `defusedxml`
- f-strings or `.format()` building SQL queries

**Fix:** validate inputs against a whitelist; resolve and check filesystem paths (`Path(...).resolve().is_relative_to(allowed_root)`); disallow user-controlled outbound URLs or restrict to allowlisted hosts; use `defusedxml.ElementTree`.

#### M4: Cryptographic Weakness

**What:**
- MD5 / SHA1 used for security purposes (signatures, MACs, password hashing)
- Hardcoded IVs / nonces in encryption
- ECB mode block ciphers
- `random.*` for security-critical randomness (use `secrets`)
- Custom HMAC implementations (use `hmac.compare_digest` for comparison)

**Search patterns:**
- `hashlib.md5(`, `hashlib.sha1(` — flag if used in `verify`, `auth`, `sign`, `mac` contexts
- `Crypto.Cipher.AES.MODE_ECB`, `AES.new(..., AES.MODE_ECB, ...)`
- `random.randint(`, `random.choice(`, `os.urandom(` (the latter is OK, but check usage) where the value is used as a key, IV, nonce, or token
- `==` comparison of HMACs / signatures (timing attack)

**Fix:** SHA-256+ for hashing; AES-GCM / ChaCha20-Poly1305 for encryption; `secrets.token_bytes(32)` for tokens; `hmac.compare_digest` for comparison.

#### M5: Loose CORS / Missing Security Headers

**What:** HTTP services (Flask Tendermint monitor, agent UI) with `Access-Control-Allow-Origin: *` or missing security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`).

**Search patterns:**
- `Access-Control-Allow-Origin` with `*`
- `flask_cors.CORS(app)` with default config (= permissive)
- Absence of header-setting middleware

**Fix:** restrict CORS to known origins; set security headers via middleware; for read-only endpoints, document the threat model explicitly.

#### M6: License Compliance Drift

**What:** Per `CLAUDE.md`, only MIT / BSD / Apache 2.0 are allowed; GPL / LGPL / MPL are prohibited. Dependency tree may include prohibited licenses transitively.

**Process:**
1. Run `pip-licenses --format=markdown` (or `tomte`'s license tooling if available) against the resolved environment.
2. Flag any dep with GPL / LGPL / MPL / AGPL / SSPL / proprietary license.
3. Audit copyleft creep in transitive deps.

**Fix:** replace the dep; add explicit exception with legal review; document in NOTICE / SBOM.

---

### Low (L) — Defense in depth and observability

#### L1: Missing Secrets-in-Logs Redaction Policy

C2 covers individual-call-site disclosure. L1 asks the systemic question: is there a redaction layer in the logging pipeline (formatter / `structlog` processor / `logging.config.dictConfig` filter) that masks secret-shaped values, or does every author bear the burden individually? If the latter, file as L1 — defense-in-depth gap.

#### L2: No Startup-Time Secret-Validation Check

**What:** Even with H1 fixed (no insecure defaults), there's value in a startup check that asserts every required secret env var is set and matches an expected shape (e.g. `API_KEY` must be 32+ chars, `PRIVATE_KEY` must be 64 hex chars).

**Fix:** add a `validate_secrets()` call at agent startup; fail fast with a clear error if a required secret is missing or malformed.

#### L3: Tendermint Persistent Peer List Hardcoding

**What:** `persistent_peers` configured statically rather than via service discovery. Not a vulnerability per se, but limits the network's resilience to peer churn.

**Fix:** documented as informational; consider DNS-based or registry-based peer discovery for production.

#### L4: SBOM / Build Provenance

**What:** Are container images built with reproducibility / SBOM attestation? Are wheels installed from a verified PyPI mirror? Is the build pipeline signed?

**Fix:** generate SBOM via `cyclonedx-py` or `syft`; sign images with `cosign`; pin to an internal index where possible.

#### L5: Audit-Log Coverage of Security-Sensitive Events

**What:** Are key operations (key-file load, on-chain tx submission, ABCI payload signing, strategy load, config-reload) recorded to a separate audit log distinct from operational logs? Without this, post-incident forensics is hard.

**Fix:** route security events to a dedicated logger / external audit sink; include timestamp, agent id, operation, outcome.

---

## False Positive Guidance

These patterns look suspicious but are **correct by design**. Do NOT report them:

### Test-fixture private keys
Test fixtures (`tests/`, `plugins/aea-test-autonomy/`, `conftest.py`) routinely include hardcoded test private keys for deterministic test setup. These are well-known throwaway keys used by Hardhat / Ganache / test Tendermint. Do NOT flag these as C5. Limit C5 to non-test code paths.

### Dummy / placeholder values in *test* config files
Test YAML configs (`tests/test_data/`, `aea-test-autonomy` fixtures) use placeholder URLs / keys / addresses for hermetic testing. Don't flag these as H1 — they aren't deployed.

### `pickle.loads` of internally-produced data
If a `pickle.loads` reads a file or buffer that the agent itself wrote in the same process or container (e.g. local cache restore), it is not RCE-exposed in the same way as network input. Reduce severity to High and note the trust assumption.

### `subprocess.run(..., shell=False)` with interpolated args
Argument interpolation is safe when `shell=False` because the shell isn't involved — argv is passed directly to `execve`. Don't flag these as C6. C6 requires `shell=True`.

### `random.*` for non-security uses
`random.choice` for jitter, log sampling, A/B test bucketing, etc. is fine. Limit M4 to uses where the output is a key, IV, nonce, token, password, or anything that protects a secret.

### Internal RPC ports without auth
Tendermint RPC bound to `127.0.0.1` or an internal Docker network without external publication is the framework's default and is OK. H4 only applies when the port is published to a host interface or routable network.

### `eval(` in framework metaprogramming
Some framework-internal code uses `eval` for limited purposes (e.g. `enum.Enum` value coercion in metaclass init). If the input is statically constructed inside the same module and not user-controlled, do not flag as C1. Verify the input source before flagging.

### Hardcoded contract addresses in `customs/` / package_overrides
Contract addresses are public on-chain. They are not secrets. Don't conflate with API keys.

---

## Methodology Guardrails

Two sets of guardrails apply: the **cross-skill** ones already documented in `/audit-fsm` and `/audit-resilience`, and the **security-specific** ones below.

**Apply the cross-skill guardrails from the sibling Methodology Guardrails sections without restating them here:**
- *Verify every sub-agent finding before accepting it* — read source, confirm severity, consolidate splits, demote liberally.
- *Force the data-type trace before flagging* — runtime type ≠ static annotation when JSON crosses the boundary.
- *Single-finding-per-bug* — one root cause = one report entry citing all relevant IDs.

These reduce duplication and prevent drift when the sibling skills evolve. Below are the guardrails that are genuinely specific to security review.

### Distinguish disclosure from exposure
- **Disclosure** = the secret has left the trust boundary (in a log, response, payload, file outside the agent dir).
- **Exposure** = the secret is reachable via a code path but not yet emitted (e.g. `Wallet.crypto_objects[<ledger>].entity` / `.private_key` is callable from a behaviour).

C2 is for disclosure. Exposure is M-level at most, often L (defense in depth). Don't over-escalate exposure to Critical.

### Trace every "untrusted input" claim to a source
For C1, C4, C6, M3 findings: name the **source** of the untrusted input (HTTP request body, ABCI payload field, env var, file content, IPFS payload). If you can't name it, downgrade or drop the finding.

### Dual-skill findings — cite the owning skill, demote here
If a finding fits `/audit-fsm` or `/audit-resilience` better, cite that skill's check ID as the primary and demote here. Examples:
- `logger.info(f'key={k}')` → cite `audit-fsm` L4 first; /security-review C2 adds only the disclosure framing.
- `requests.get(...)` with no timeout → `audit-resilience` BP8 / CC5 owns this; /security-review flags only if the missing timeout enables a security-relevant DoS or resource-exhaustion attack on a trust boundary.

---

## Coverage Limitations

This skill audits **agent-process security** in the open-autonomy codebase. The following are explicitly NOT covered — call this out in every report:

- **Smart-contract security** (reentrancy, gas griefing, signature replay on chain) — out of scope; covered by Solidity-specific tooling (Slither, Mythril, manual audit).
- **Cryptographic-library implementation review** — we trust `cryptography`, `eth_keys`, `web3.py` etc. as black boxes. CVEs in those libraries surface via H7.
- **Tendermint internals** — we audit configuration, not the consensus engine.
- **Network / load testing** under attack scenarios — this audit is static.
- **Penetration testing of deployed services** — out of scope; recommend a separate engagement.
- **Compliance** (SOC2, ISO 27001, GDPR) — this audit checks technical controls, not policy / process / documentation.
- **Insider threat / multi-party governance** — out of scope.
- **Physical security** of deployment hosts — out of scope.

Companion skills:
- `/audit-fsm` — FSM correctness and safety
- `/audit-resilience` — external request resilience

Include a "What this audit did not cover" section in every report.

---

## Analysis Procedure

### Step 0: Run Existing Security Tools

Before manual inspection, run the framework's tooling and capture the output:

```bash
# Bandit — static analysis for common Python security issues
tox -e bandit

# Safety — known CVEs in pinned dependencies (uses tomte allowlist)
tox -e safety

# Gitleaks — secrets scanning across history
tox -e gitleaks

# Or run all three in parallel
make security
```

**Process the output:**
- Bandit findings → cross-reference with the C/H/M checklist; many will already match (e.g. Bandit's `B602` ≈ C6, `B301` ≈ C4).
- Safety findings → record under H7 with package, version, CVE ID; check the tomte allowlist for explanations.
- Gitleaks findings → record under C5; for each, verify whether the secret is rotated.

**Tooling-unavailable case.** If the tox envs cannot run (network restrictions, missing tomte version), note in the report and proceed with manual checks. Do NOT block the audit on tool availability.

### Step 1: Static Discovery

Launch up to **3 parallel Explore agents**, dividing the codebase:

- **Agent 1 — code paths**: search `packages/`, `autonomy/`, `plugins/`, `customs/` for the C/H/M/L patterns above. For each match, capture file:line, the surrounding context, and the input source.
- **Agent 2 — configuration**: parse `aea-config.yaml`, every `service.yaml`, every `skill.yaml` under audit. Extract env-var-interpolated params; flag insecure defaults (H1) and any param with security-relevant naming.
- **Agent 3 — deployment**: read `Dockerfile*`, `docker-compose*.yaml`, `deployments/`, `kubernetes/` if present, and `.github/workflows/*.yml`. Flag root containers (H3), exposed RPC (H4), hardcoded secrets in deployment artifacts (H2), key-file permissions (M1).

Each agent should return a structured list of candidates with check ID, file:line, and a short justification.

### Step 2: Semantic Verification

For each candidate from Step 1, an analysis agent:
1. Reads the call site and surrounding context.
2. Traces the input source for any "untrusted input" claim.
3. Applies the False Positive Guidance.
4. Promotes / demotes severity based on the actual blast radius.
5. Produces a finding entry with code snippet, threat description, and concrete fix.

### Step 3: Cross-Cutting Synthesis

After per-finding analysis:
1. Build a "Secrets Inventory" table: every credential / key / token surface, its storage mechanism, its rotation policy.
2. Build a "Trust Boundaries" diagram-table: every input source that crosses a trust boundary (network, IPFS, env, file), with its validator (or absence thereof).
3. Build a "Dependency Risk" table: every runtime dep, its license, its CVE status.
4. Identify systemic patterns: e.g. "secrets are consistently set via env vars but no startup validation" → L2 finding cluster.

### Step 4: Generate Report

Merge all findings into the output format below.

---

## Output Format

Present the security review as follows:

```markdown
# Security Review

**Scope:** [list of audited paths / packages / services]
**Date:** [current date]
**Tools run:** bandit (Y/N), safety (Y/N), gitleaks (Y/N), pip-audit (Y/N — optional second-source; install manually)

## Executive Summary

- Critical findings: N
- High findings: N
- Medium findings: N
- Low findings: N

[2-3 sentences on the highest-impact findings and the systemic patterns they reveal]

## Critical Findings

### [C#]: [Title]
- **File:** `path/to/file.py:line`
- **Threat:** [what compromise this enables, who can trigger it]
- **Code:**
  ```python
  [problematic code snippet]
  ```
- **Fix:**
  ```python
  [corrected code snippet]
  ```
- **Cross-references:** [audit-fsm L4 / audit-resilience BP14 / etc., if applicable]

## High Findings
[same format]

## Medium Findings
[same format]

## Low Findings
[same format]

---

## Secrets Inventory

| Secret | Storage | Loaded by | Rotation policy |
|---|---|---|---|
| Ethereum private key | mounted volume | `aea.crypto.wallet.Wallet` | manual |
| ... |

## Trust Boundaries

| Boundary | Input source | Validator | Findings |
|---|---|---|---|
| ABCI payload | Tendermint network | `check_payload()` per round | H5 if missing |
| HTTP handler | external HTTP | per-handler `_validate_*` | M3 if missing |
| IPFS strategy | IPFS network | content-hash check | C3 if missing |
| Env-var config | host environment | none / startup check | H1 if defaulted |
| ... |

## Dependency Risk

| Package | Version | License | CVE status |
|---|---|---|---|
| ... |

## Tooling Output Summary

### Bandit
[counts by severity, top categories]

### Safety
[CVEs not in allowlist]

### Gitleaks
[hits, by file]

---

## What This Audit Did Not Cover

- Smart-contract security (run Slither / Mythril / manual contract audit)
- FSM correctness (run `/audit-fsm`)
- External request resilience (run `/audit-resilience`)
- Cryptographic-library internals (trust black boxes; CVEs surfaced via H7)
- Tendermint consensus internals
- Penetration testing of deployed services
- Compliance audits (SOC2 / ISO 27001 / GDPR)
- Insider threat / governance review
- [Add scope exclusions specific to this run]
```

If no findings at a severity level, include the section header with "No findings." underneath.
