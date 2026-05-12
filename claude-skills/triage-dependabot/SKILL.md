---
name: triage-dependabot
description: Triage open Dependabot security alerts on the current GitHub repo. For each alert, decide (1) whether the vulnerable dependency is reachable from production code, then (2) whether the CVE's threat model is actually exploitable given how this codebase uses the package. Production-AND-applicable alerts get a tracking issue opened; production-but-not-applicable alerts get dismissed with reason `inaccurate`; test/dev-only alerts get dismissed with reason `not_used`. Repo-agnostic — works across the Valory fleet.
argument-hint: "[--limit N]  # optional cap on alerts processed per run"
disable-model-invocation: true
---

# Triage Dependabot alerts (prod vs test, then act)

Walk every open Dependabot security alert on the current repo. Classify the vulnerable dependency by whether it is **reachable from production code** or **only from tests / dev tooling / CI**. Then act in one pass:

| Classification | Action |
| -------------- | ------ |
| **Production-reachable AND exploit-applicable** | Leave Dependabot alert open. Open a new GitHub issue on the repo that references the alert, names the CVE / GHSA / severity, lists the production paths that pull in the vulnerable package, the exploit-surface analysis, and the suggested upgrade pin. |
| **Production-reachable but exploit NOT applicable** (CVE's threat model doesn't map to this codebase's usage) | Dismiss the Dependabot alert with `dismissed_reason=inaccurate` and a comment naming the threat-model mismatch. No repo issue. |
| **Test / dev / CI-only import path** | Dismiss with `dismissed_reason=not_used` naming the test/dev paths it was found in. No repo issue. |
| **Unclassifiable** | Skip. Print a line to stderr for manual review. **Never** auto-dismiss without evidence. |

Conservative default: **when uncertain about exploit applicability, open the issue.** A false-positive issue is cheap to close after a one-line maintainer comment; a false-negative dismissal hides a real vulnerability. But "import in prod ≠ exploit-applicable" — see Phase 2.5.

This skill runs fully autonomously on invocation — it mutates GitHub state (dismisses alerts, opens issues). Do not invoke from conversational context; require explicit `/triage-dependabot`.

---

## Phase 0 — Ground truth

```bash
# 1. Confirm we're in a git repo with a GitHub remote
gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"' > /tmp/td_repo.txt 2>/dev/null \
  || { echo "ERROR: not in a GitHub repo (gh repo view failed)"; exit 1; }
REPO=$(cat /tmp/td_repo.txt)
echo "operating on $REPO"

# 2. Confirm Dependabot alerts API is reachable for this repo
# (Endpoint requires the alerts feature enabled + token with `security_events` scope.)
gh api "repos/$REPO/dependabot/alerts?per_page=1" --jq 'length' > /dev/null 2>&1 \
  || { echo "ERROR: dependabot alerts API unreachable — check repo has Dependabot enabled and gh token has security_events scope"; exit 1; }

# 3. Confirm a Python project layout exists (this skill currently keys off Python ecosystems)
test -f pyproject.toml \
  || { echo "ERROR: no pyproject.toml — skill only supports Python repos right now"; exit 1; }
```

Capture into working memory:

| Field | Source |
| ----- | ------ |
| `REPO` | `<owner>/<name>` from `gh repo view` |
| `PROD_PATHS` | Default: `autonomy/ packages/ agent/` — adjust to repo. See Phase 2.1 for repo-specific overrides. |
| `TEST_PATHS` | Default: `tests/ scripts/ .github/` plus every `**/tests/` subdir under `packages/`. |
| `LIMIT` | Optional `--limit N` arg; otherwise process all open alerts. |
| `ARCHETYPE` | Repo archetype (see §0.1). Drives the exploit-surface threshold in Phase 2.5. |

### 0.1 Repo archetype

Different archetypes have radically different exploit surfaces for the *same* CVE. A header-leak CVE in `urllib3` matters for an internet-facing web service handling user auth tokens; it doesn't matter for a CLI link checker that holds no auth state. The skill needs this distinction baked into Phase 2.5's reasoning, not bolted on after the fact.

Classify the current repo into one of:

| Archetype | Signal | Exploit-surface posture |
| --------- | ------ | ----------------------- |
| `cli-tool` | Entry point is a `console_scripts` / `[tool.poetry.scripts]`, runs once and exits, no long-lived HTTP listener, processes developer-controlled inputs. E.g. tomte, aea-helpers, dev/CI plugins. | **Narrow.** CVEs requiring browser sessions, server-side cookies, persistent attacker control, or untrusted-remote inputs do not apply. Memory-DoS CVEs only matter if uptime is a contract. |
| `framework` | Library/SDK consumed by other projects. No own entry point. E.g. open-autonomy, open-aea, mech-interact. | **Wide.** Any CVE that consumers may hit applies — must err on the side of bumping, because downstream usage isn't fully known. |
| `service` | Long-running process, network-facing, handles untrusted input. E.g. middleware HTTP API, mech-server, agent HTTP endpoints. | **Wide.** Default-apply for any CVE in the request/response or auth path. Memory-DoS, header-leak, deserialization CVEs all real. |
| `scaffold` | A starter template — runtime exposure depends on downstream usage, not on this repo's own code. E.g. olas-sdk-starter. | **Inherit consumer's archetype.** Treat as `framework` unless a specific consumer is in scope. |
| `unknown` | None of the above. | Default to `framework` posture. |

Heuristics to detect automatically (run in Phase 0):

```bash
# console_scripts / poetry-scripts hint cli-tool
HAS_SCRIPTS=$(python3 -c "
import tomllib, pathlib
d = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
print(bool(
    d.get('project', {}).get('scripts')
    or d.get('tool', {}).get('poetry', {}).get('scripts')
))" 2>/dev/null)

# fastapi / flask / aiohttp / uvicorn imports in non-test code hint service
HAS_SERVER=$(grep -rlE "^(import|from)[[:space:]]+(fastapi|flask|aiohttp\.web|uvicorn|starlette)" \
  "${PROD_DIRS[@]}" --include="*.py" 2>/dev/null | grep -v "/tests/" | head -1)

# packages/ tree with valory/skills hints framework (open-autonomy fleet)
HAS_PACKAGES_TREE=$([ -d packages/valory ] && echo "yes" || echo "no")

# starter / template / scaffold in repo name or README hint scaffold
IS_SCAFFOLD=$(grep -iE "starter|template|scaffold|boilerplate" README.md 2>/dev/null | head -1)
```

These are hints, not proofs. When the classification is ambiguous, **default to `framework`** so the skill errs on the side of bumping. A human can override by writing `archetype: cli-tool` in a per-repo `.triage-dependabot.yaml` config (future enhancement — for now, hardcode the override at the top of the per-alert loop).

---

## Phase 1 — Fetch open Dependabot alerts

```bash
TMP=$(mktemp -d)
set -euo pipefail

# Parse optional --limit N from argv. Default: no cap.
LIMIT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="$2"; shift 2 ;;
    --limit=*) LIMIT="${1#*=}"; shift ;;
    *) shift ;;
  esac
done
[[ -n "$LIMIT" ]] && [[ ! "$LIMIT" =~ ^[0-9]+$ ]] \
  && { echo "ERROR: --limit must be a non-negative integer, got: $LIMIT"; exit 1; }

gh api "repos/$REPO/dependabot/alerts?state=open&per_page=100" --paginate \
  > "$TMP/alerts.json" \
  || { echo "ERROR: failed to list Dependabot alerts for $REPO"; exit 1; }

# Sanity: must be a non-null JSON array
jq -e 'type == "array"' "$TMP/alerts.json" > /dev/null \
  || { echo "ERROR: alerts response is not a JSON array — likely API error or scope problem"; cat "$TMP/alerts.json" | head -20; exit 1; }

N_ALERTS=$(jq 'length' "$TMP/alerts.json")
if [[ -n "$LIMIT" && "$LIMIT" -lt "$N_ALERTS" ]]; then
  echo "found $N_ALERTS open alerts on $REPO; processing first $LIMIT per --limit"
  N_PROCESS="$LIMIT"
else
  echo "found $N_ALERTS open alerts on $REPO"
  N_PROCESS="$N_ALERTS"
fi
```

The per-alert loop in Phase 3 / the reference loop below must iterate `0..N_PROCESS-1`, not `0..N_ALERTS-1`. Phase 4 summary should report both `seen` (N_ALERTS) and `processed` (N_PROCESS) when they differ, so the operator knows how many alerts remain in the backlog.

Fields used per alert (`jq` paths below):

| Field | Path |
| ----- | ---- |
| Alert number | `.number` |
| Alert URL | `.html_url` |
| Severity | `.security_advisory.severity` |
| GHSA / CVE | `.security_advisory.ghsa_id`, `.security_advisory.cve_id` |
| Summary | `.security_advisory.summary` |
| Package name | `.security_vulnerability.package.name` |
| Ecosystem | `.security_vulnerability.package.ecosystem` (skip if `≠ pip`) |
| Vulnerable range | `.security_vulnerability.vulnerable_version_range` |
| First patched | `.security_vulnerability.first_patched_version.identifier` |
| Direct/transitive | `.dependency.scope` (`runtime` or `development`) |
| Manifest path | `.dependency.manifest_path` |

**Skip immediately** any alert where:

- `ecosystem != "pip"` (this skill only handles Python deps right now — flag for operator)
- `state != "open"` (defensive; we filtered on the query but pagination races happen)
- `auto_dismissed_at != null` (already auto-dismissed by GitHub)

---

## Phase 2 — Classify each alert (production vs test/dev)

For every alert, gather evidence in a defined order. **First decisive signal wins**, with conservative "default to production" as the tie-breaker.

### 2.1 Resolve production vs test path sets

Production paths and test paths vary by repo. Compute once per skill run and **export** so the values cross subshell / `<<<PY` heredoc boundaries cleanly. Then use bash arrays plus `"${arr[@]}"` expansion at every grep call site — never store the dir set as a space-joined string that gets re-split implicitly across function calls.

```bash
# Production paths — top-level Python source dirs that ship in the wheel/sdist.
# Candidate list is per-repo; this default covers open-autonomy + the downstream fleet.
PROD_DIRS=()
for d in autonomy packages plugins libs aea operate agent; do
  [[ -d "$d" ]] && PROD_DIRS+=("$d")
done

# Test paths — top-level test dirs PLUS in-package `tests/` subdirs that aren't shipped logic
TEST_DIRS=(tests scripts .github benchmark examples mints docs)
# Filter to only existing dirs to avoid `grep: tests: No such file or directory` noise
TEST_DIRS=($(for d in "${TEST_DIRS[@]}"; do [[ -d "$d" ]] && echo "$d"; done))

# Per-package nested tests/ — these are TEST even though they live under packages/
mapfile -t PKG_TEST_DIRS < <(find packages plugins -type d -name tests 2>/dev/null)

export PROD_DIRS TEST_DIRS PKG_TEST_DIRS   # propagate to any python -c / heredoc helpers

echo "PROD_DIRS=${PROD_DIRS[*]}"
echo "TEST_DIRS=${TEST_DIRS[*]}"
echo "PKG_TEST_DIRS count=${#PKG_TEST_DIRS[@]}"
```

**Critical**: every grep invocation that uses these sets MUST expand the array with `"${arr[@]}"` (quoted-each-element), not the unquoted string form `$ARR`. The unquoted form gets re-split by IFS, which silently fails on directory names with spaces and — more commonly — drops the entire list when the variable inherits empty across a subshell boundary. Signal C grepped 12 alerts to "zero hits" against open-aea before this was caught.

```bash
# RIGHT
grep -rlnE "$REGEX" "${PROD_DIRS[@]}" --include="*.py"

# WRONG — collapses to one string, breaks on spaces, vulnerable to empty-var bug
grep -rlnE "$REGEX" $PROD_DIRS --include="*.py"
```

**Important nuance**: under `packages/<author>/skills/<skill_name>/`, the skill's own production code (`behaviours.py`, `rounds.py`, `models.py`, `handlers.py`) is production; its sibling `tests/` subdir is not. Per-skill `tests/` dirs are captured by the `find packages plugins -type d -name tests` line above and grepped as TEST.

### 2.2 Signal A — GitHub's own `dependency.scope`

Direct dependencies have a reliable `scope` field set by Dependabot from manifest parsing:

```bash
SCOPE=$(jq -r ".[$i].dependency.scope // \"unknown\"" "$TMP/alerts.json")
```

- `runtime` → direct production dep. Strong signal toward **PROD**, but verify with Signal C (an unimported dep is still dev-effectively).
- `development` → direct dev/test dep. Strong signal toward **DEV**, but verify with Signal C (config drift is real).
- `unknown` / null → transitive dep. Fall through to Signal B.

### 2.3 Signal B — pyproject.toml dep-group membership

Direct or transitive, the top-level pin (if any) tells us which group the dep entered the project via:

```bash
PKG=$(jq -r ".[$i].security_vulnerability.package.name" "$TMP/alerts.json")

# PEP 621 [project] dependencies → production
grep -qE "^[[:space:]]*\"$PKG([\[<>=!~,].*)?\"" pyproject.toml \
  && grep -qE "^[[:space:]]*\"$PKG" <(awk '/^dependencies\s*=\s*\[/,/^\]/' pyproject.toml) \
  && echo "found in [project] dependencies (production)"

# PEP 735 [dependency-groups] / dev → test/dev
awk '/^\[dependency-groups\]/,/^\[/' pyproject.toml \
  | grep -qE "\"$PKG([\[<>=!~,].*)?\"" \
  && echo "found in [dependency-groups] (test/dev)"

# Poetry-shape [tool.poetry.group.<name>.dependencies] → check group name
awk '/^\[tool\.poetry\.group\..*\.dependencies\]/,/^\[/' pyproject.toml \
  | grep -B5 "^$PKG\s*=" | head -1 \
  | grep -q "test\|dev\|tests" && echo "found in poetry dev/test group"
```

This is shell-form for documentation. In practice, use Python with `tomllib` (stdlib in 3.11+) for accuracy:

```python
import tomllib, sys, pathlib
data = tomllib.loads(pathlib.Path("pyproject.toml").read_text())

def group_for(pkg: str) -> str | None:
    """Return 'prod', 'dev', or None for this package's declaration group."""
    # PEP 621 [project] dependencies
    for spec in data.get("project", {}).get("dependencies", []):
        if spec.split("[")[0].split("=")[0].split(">")[0].split("<")[0].strip() == pkg:
            return "prod"
    # PEP 735 [dependency-groups] (uv / pip)
    for group_name, specs in data.get("dependency-groups", {}).items():
        for spec in specs:
            spec_str = spec if isinstance(spec, str) else spec.get("include-group", "")
            if spec_str.split("[")[0].split("=")[0].split(">")[0].split("<")[0].strip() == pkg:
                return "dev"  # all PEP 735 groups in Valory repos are dev/test
    # Poetry groups
    for group_name, group in data.get("tool", {}).get("poetry", {}).get("group", {}).items():
        deps = group.get("dependencies", {})
        if pkg in deps:
            return "dev" if group_name in {"dev", "test", "tests", "lint", "ci"} else "prod"
    # Poetry main
    if pkg in data.get("tool", {}).get("poetry", {}).get("dependencies", {}):
        return "prod"
    return None  # transitive — fall through to Signal C
```

### 2.4 Signal C — import-graph scan (decisive)

Whatever the pyproject says, the **import graph is ground truth**. If production code does `import <pkg>` (or `from <pkg> import …`), the alert is production regardless of pin group.

Step 1: map the package distribution name to its importable top-level module(s). PyPI distribution names and Python module names diverge frequently (`PyYAML` → `yaml`, `protobuf` → `google.protobuf`, `python-dotenv` → `dotenv`, `Pillow` → `PIL`). Resolve via `importlib.metadata` if the package is installed locally:

```python
import importlib.metadata as im
top_modules: list[str] = []
try:
    files = im.files(pkg) or []
    # Package modules — directories with __init__.py (e.g. requests/__init__.py)
    pkg_dirs = sorted({
        str(f).split("/")[0]
        for f in files
        if str(f).endswith("/__init__.py") and not str(f).startswith(".")
    })
    # Single-file top-level modules (e.g. six.py, attr.py installed at the
    # site-packages root with no enclosing package directory).
    single_files = sorted({
        str(f).removesuffix(".py")
        for f in files
        if str(f).endswith(".py") and "/" not in str(f) and not str(f).startswith(".")
    })
    top_modules = sorted(set(pkg_dirs) | set(single_files))
except im.PackageNotFoundError:
    pass

# Fallback applies on BOTH paths: PackageNotFoundError AND empty-after-filter
# (e.g. a package that ships only data files, or a metadata listing that
# matches no .py top-levels). Without this, packages like `six` — which
# ships as a single top-level file via a stricter installer that records
# fewer entries — would silently yield an empty grep target.
if not top_modules:
    top_modules = [pkg.replace("-", "_")]
```

If the package isn't installed (deep transitive, never landed in the venv), fall back to the conservative substitution `pkg.replace("-", "_")` and grep both forms.

Step 2: grep across **every** top-level module the package ships. PyPI packages frequently expose multiple importable top-levels (`setuptools` → `setuptools` + `pkg_resources` + `_distutils_hack`; `protobuf` → `google` for `from google.protobuf...`; `Pillow` → `PIL`). Build an alternation so a single grep catches any of them:

```bash
# Join the list from Step 1 into an alternation, escaping regex metachars
# (top modules can contain `.` for namespace packages like google.protobuf).
MODULE_RE=$(printf '%s\n' "${top_modules[@]}" | sed 's/\./\\./g' | paste -sd'|' -)

# Use "${arr[@]}" array expansion (see §2.1 critical note) — never the
# unquoted string form, which collapses on subshell boundaries and silently
# returns 0-hits even when the package IS imported in prod.
PROD_HIT_FILES=$(grep -rlnE "^(import|from)[[:space:]]+(${MODULE_RE})([[:space:]]|\.|$)" \
  "${PROD_DIRS[@]}" --include="*.py" 2>/dev/null \
  | grep -v "/build/" | grep -v "/tests/")
PROD_HITS=$(echo "$PROD_HIT_FILES" | grep -c . || echo 0)

TEST_HIT_FILES=$(grep -rlnE "^(import|from)[[:space:]]+(${MODULE_RE})([[:space:]]|\.|$)" \
  "${TEST_DIRS[@]}" "${PKG_TEST_DIRS[@]}" --include="*.py" 2>/dev/null \
  | grep -v "/build/")
TEST_HITS=$(echo "$TEST_HIT_FILES" | grep -c . || echo 0)
```

Two extra filters worth keeping:

- `grep -v "/build/"` — many `plugins/<plugin>/build/lib/...` paths exist after a `poetry build` run; those are dist-copies of source under the same `plugins/<plugin>/<plugin>/` tree. They double-count if not filtered.
- `grep -v "/tests/"` in the PROD pipeline — guards against the case where `PROD_DIRS` includes `packages/` (or `plugins/`) and the recursive grep walks into per-package `tests/` subdirs. Those should always count as TEST, never PROD, regardless of which top-level dir they live under.

The `^(import|from)\s+<mod>([\s.]|$)` anchor is deliberate: it matches `import foo`, `from foo import …`, `from foo.bar import …`, but **not** `# import foo` (comment) or `from foobar import …` (different package). The trailing alternation `([\s.]|$)` is what prevents `foobar` from matching when grepping for `foo`.

Step 3: classify. The verdict consults all three signals — A (`dependency.scope`), B (`group_for(pkg)` from §2.3), and C (import counts above) — in priority order:

- `PROD_HITS > 0` → **PROD**, regardless of A/B (import-graph evidence wins).
- `PROD_HITS == 0` AND `TEST_HITS > 0` → **DEV** (only reachable from tests/CI).
- No imports anywhere; classification falls through to A then B:
  - `scope == "development"` → **DEV**.
  - `scope == "runtime"` → **PROD** (declared prod, even if currently unimported — better to fix the dep than the imports).
  - `scope == "unknown"` AND `group_for(pkg) == "prod"` → **PROD** (the project explicitly lists this in `[project] dependencies` / Poetry main → it's production-relevant, dismissing it as unimported would silently bypass an asserted prod dep).
  - `scope == "unknown"` AND `group_for(pkg) == "dev"` → **DEV** (declared in a dev/test group; no imports means it's safe to dismiss as unused).
  - `scope == "unknown"` AND `group_for(pkg)` is `None` (true transitive) → **UNCLASSIFIABLE** (no signal at all; skip and flag for human review, or fall through to §2.5 transitive reverse-walk if available).

Without the Signal B clauses, the verdict drops a real layer of information on the floor — exactly the case where stacking signals is supposed to pay off.

### 2.5 Exploit-surface analysis — does the CVE's threat model map to this codebase?

**This is the most important step the skill performs**, and the one most likely to be skipped by a naive "imported in prod → open issue" classifier. A CVE describes a *bug under specific preconditions*; whether those preconditions are reachable in *this* codebase is a separate question.

Real failure mode this phase prevents: imagine `urllib3` ships a CVE where the **streaming-redirect path with proxy auth** leaks `Authorization` headers to the redirect target. The codebase imports `urllib3` for a CLI **link checker** that issues stateless HEAD requests to documented URLs and carries no auth headers. Signal C → PROD hit → issue opened → maintainer comments "this CVE doesn't apply to a link checker" → wasted cycles.

This phase exists to catch that case **before** the issue is opened.

#### 2.5.1 Fetch the GHSA's actual description

The Dependabot alert payload's `.security_advisory.summary` is a one-liner. The fuller threat-model description lives in the GHSA database. Pull it:

```bash
# GitHub Security Advisory full payload, including description + references
gh api "/advisories/$GHSA_ID" \
  --jq '{summary: .summary, description: .description, severity: .severity, cwe_ids: [.cwe_ids[]?.cwe_id]}' \
  > "$TMP/advisory_${GHSA_ID}.json"
```

Read the `description` and `cwe_ids` fields. The CWE IDs are a strong typed hint about the bug class.

#### 2.5.2 Identify the CVE's required preconditions

Working from the advisory's description, write down (mentally or in scratch state) what an attacker needs in order to trigger the bug:

| Bug class (common CWE patterns) | Typical required preconditions |
| ------------------------------- | ------------------------------ |
| Header / cookie / token leak (CWE-200, CWE-201) | Code sends sensitive headers; attacker controls a URL or redirect target |
| Decompression / zip bomb (CWE-409) | Code reads streaming bodies from attacker-controlled URLs; client process uptime matters |
| Path traversal (CWE-22) | Code passes attacker-controlled paths to file I/O |
| Deserialization RCE (CWE-502) | Code deserializes pickle / yaml / msgpack from attacker-controlled bytes |
| SQL injection (CWE-89) | Code builds queries from attacker-controlled strings |
| ReDoS (CWE-1333) | Code runs the vulnerable regex against attacker-controlled strings |
| CSRF (CWE-352) | Server-side web app with browser-driven OAuth / form flows |
| Command injection (CWE-78) | Code passes attacker-controlled args to subprocess / shell |
| SSRF (CWE-918) | Code fetches URLs whose host is attacker-controlled |
| TLS bypass (CWE-295) | Code makes outbound HTTPS to internet-facing hosts |
| Privilege escalation in deserialized config (CWE-94) | Code loads attacker-controlled config files |

#### 2.5.3 Map preconditions against the calling code

For each PROD import path found in Signal C, **read the calling file** (or the relevant function) and answer:

1. Does the calling code carry the sensitive state the CVE targets? (auth headers? session cookies? privileged file paths? OAuth state?)
2. Does the calling code accept input from an untrusted source? (network user? HTTP request body? environment variable populated by an external system?) Or is the input developer-controlled (repo source, hardcoded URL, deterministic config)?
3. Is the calling process long-lived / network-reachable, or one-shot CLI?

Cross-reference the answers against the preconditions from §2.5.2. If **any** required precondition is absent, the CVE is **not applicable** in this codebase even though the package is imported in prod.

#### 2.5.4 The archetype multiplier

Apply the `ARCHETYPE` value from Phase 0.1:

| Archetype | Default exploit-surface posture |
| --------- | ------------------------------- |
| `cli-tool` | **Strict** — CVEs requiring browser sessions, long-running listeners, untrusted-remote inputs, server-side state are presumed not-applicable. Memory-DoS CVEs are not-applicable unless uptime is a contractual concern. The CVE must show a concrete exploit chain that fits the CLI usage to count as applicable. |
| `framework` / `scaffold` | **Permissive** — consumers may use the framework in any archetype, so a CVE that's exploitable in *some* downstream consumer is applicable here. Default to PROD-applicable unless the CVE is structurally impossible (e.g. an auth CVE in a library that has no auth code at all). |
| `service` | **Permissive** — long-running, network-reachable, often handles user input. Default to PROD-applicable. |
| `unknown` | Treat as `framework`. |

#### 2.5.5 Final verdict

Combine §2.5.3 (preconditions match) with §2.5.4 (archetype posture):

| §2.5.3 result | §2.5.4 archetype | Verdict |
| ------------- | ---------------- | ------- |
| All preconditions reachable | any | **PROD-APPLICABLE** → open issue (Phase 3.2) |
| One or more preconditions absent | `service` / `framework` / `scaffold` | **PROD-APPLICABLE** → open issue (default to caution; consumers may differ) |
| One or more preconditions absent | `cli-tool` | **NOT-APPLICABLE** → dismiss with `inaccurate` (Phase 3.3) |
| Truly ambiguous (precondition reachability not determinable without runtime trace) | any | **PROD-APPLICABLE** → open issue, default to caution |

When dismissing as `inaccurate`, the `dismissed_comment` must name **which precondition is absent** in plain English. "Tomte's link checker carries no auth headers; the CVE requires a sensitive-header forward via redirect — precondition absent." That comment is the audit trail; a future reviewer needs to be able to challenge the call.

### 2.6 Transitive deps — reverse-resolve the chain

For transitive deps (`scope == "unknown"` or no pin in pyproject.toml), figure out which **direct** deps pull the vulnerable package in:

```bash
# uv repos
uv tree --package "$PKG" --invert 2>/dev/null

# Poetry repos (Poetry >= 1.2): --why prints every direct dep that pulls $PKG
# transitively, with its full path. This is correct; `poetry show -t | grep -B1`
# (the obvious-looking form) does NOT walk to the parent — `grep -B1` returns
# the previous *line* in the tree's flat text output, which is a sibling at
# the same indent, not the dependency-graph parent. That misidentifies the
# root and risks silently dismissing transitives whose actual root is a prod
# dep.
poetry show --why "$PKG" 2>/dev/null

# Fallback if neither is available: parse uv.lock / poetry.lock directly for
# `dependencies` entries of each root package and resolve which ones pull $PKG.
```

If **every** reverse-dep root is a dev/test group root, mark **DEV**. If **any** reverse-dep root is in `[project] dependencies` (prod), mark **PROD**. This is the right call even if production code itself never does `import <transitive>` — the transitive is in the production install footprint and exploitable at runtime.

---

## Phase 3 — Act on the classifications

For every alert, take exactly one action: **dismiss**, **open issue**, or **skip**. Build a per-alert audit record so the Phase 4 summary is honest about what happened.

### 3.1 Dismiss a DEV-only alert

**`dismissed_comment` has a hard 280-character limit** on the Dependabot alerts API (`HTTP 422: Invalid property /dismissed_comment: Only 280 characters are allowed`). The wordy default below is ~330 chars and **will fail** without truncation. Build a terser default and cap defensively:

```bash
# Pick a terse, deterministic comment — favour information density over prose,
# because we lose ~50 chars to the test-hit file list when it's long.
DISMISS_COMMENT="Triaged: \`$PKG\` only in test/dev (PROD scan: 0 imports). Locations: $TEST_HIT_FILES. Re-evaluate if prod imports \`$PKG\`."

# Hard cap at 280; truncate with an ellipsis so it's obvious the comment was clipped.
if [[ ${#DISMISS_COMMENT} -gt 280 ]]; then
  DISMISS_COMMENT="${DISMISS_COMMENT:0:277}..."
fi

gh api -X PATCH "repos/$REPO/dependabot/alerts/$ALERT_NUM" \
  -f state="dismissed" \
  -f dismissed_reason="not_used" \
  -f dismissed_comment="$DISMISS_COMMENT" \
  --jq '.state' \
  || { echo "ERROR: failed to dismiss alert #$ALERT_NUM"; SKIPPED+=("$ALERT_NUM:dismiss-api-error"); continue; }
```

When `$TEST_HIT_FILES` is empty (pure transitive dismissals like `pillow` arriving via `ledgerwallet` with zero imports), use a different terser default to avoid `Locations: .` dangling:

```bash
if [[ -z "$TEST_HIT_FILES" ]]; then
  DISMISS_COMMENT="Triaged: \`$PKG\` not imported anywhere (prod or test). Transitive via $REVERSE_DEP_ROOT. Re-evaluate if any code imports \`$PKG\`."
fi
```

**Required**: `dismissed_reason` must be one of the GitHub-documented enum values: `fix_started`, `inaccurate`, `no_bandwidth`, `not_used`, `tolerable_risk`. This skill uses **two** of them, each with strict criteria:

- `not_used` — the package import path is not reachable from production code. Phase 2.4 Signal C decides this. The dismissal comment names the test/dev paths found.
- `inaccurate` — the package IS imported in production code, but the CVE's threat model preconditions are absent in this codebase's usage. Phase 2.5 decides this. The dismissal comment names which precondition is absent.

Do **not** use `tolerable_risk` — that's "the bug is real and reachable, but the impact is low enough that we accept it." It requires a human cost/benefit call; the skill never has the context to make it.

Do **not** use `fix_started` or `no_bandwidth` — those mean "we're working on it" / "we don't have time." Neither describes the skill's actual reasoning.

### 3.1b Dismiss a NOT-APPLICABLE alert (Phase 2.5 verdict)

For alerts where the package is imported in PROD but Phase 2.5 ruled the CVE's preconditions absent. The dismissal comment must name the specific precondition that's absent — that's the audit trail.

```bash
# $PRECONDITION_ABSENT is set in Phase 2.5.3 — e.g.,
#   "sensitive-header carriage" / "long-lived process / uptime contract"
#   / "OAuth browser session" / "deserialization of attacker bytes"
DISMISS_COMMENT="Triaged: \`$PKG\` imported in prod but CVE threat model not applicable. Required: $PRECONDITION_ABSENT. Archetype: $ARCHETYPE. See $ALERT_URL for the CVE; this codebase does not satisfy the precondition."

if [[ ${#DISMISS_COMMENT} -gt 280 ]]; then
  DISMISS_COMMENT="${DISMISS_COMMENT:0:277}..."
fi

gh api -X PATCH "repos/$REPO/dependabot/alerts/$ALERT_NUM" \
  -f state="dismissed" \
  -f dismissed_reason="inaccurate" \
  -f dismissed_comment="$DISMISS_COMMENT" \
  --jq '.state' \
  || { echo "ERROR: failed to dismiss alert #$ALERT_NUM"; SKIPPED+=("$ALERT_NUM:dismiss-api-error"); continue; }
```

### 3.2 Open a tracking issue for a PROD-APPLICABLE alert

Before opening, **dedupe**: search for an existing open issue tagged with the same GHSA ID, to avoid spam on repeat runs.

```bash
EXISTING=$(gh issue list --repo "$REPO" --state open --search "$GHSA_ID in:title,body" --json number,url --jq '.[0].url // ""')
if [[ -n "$EXISTING" ]]; then
  echo "skip: existing issue for $GHSA_ID at $EXISTING"
  SKIPPED+=("$ALERT_NUM:existing-issue:$EXISTING")
  continue
fi
```

Issue title format (under 70 chars). Lead with `[Security]` so the issue is filterable, then the **package and a human-readable summary** — the GHSA ID belongs in the body, not the title, because reviewers don't scan ID strings. The skill's dedupe search (`$GHSA_ID in:title,body`) still works because the GHSA appears in the body.

```
[Security][<severity>] <package>: <short summary>
```

Build the short summary from `.security_advisory.summary`, which Dependabot returns as a string usually of the form `"<package>: <description>."` — but with three real-world wrinkles you have to handle: (1) case mismatch between the advisory's package capitalisation (`Authlib:`) and the API's `.package.name` (`authlib`); (2) some summaries omit the colon entirely (`"GitPython reference APIs has a path traversal..."`); (3) advisories often end with a period.

```bash
PKG_LOWER=$(tr '[:upper:]' '[:lower:]' <<<"$PKG")
SUM_LOWER=$(tr '[:upper:]' '[:lower:]' <<<"$SUMMARY")
RAW="$SUMMARY"
if [[ "$SUM_LOWER" == "${PKG_LOWER}: "* ]]; then       # case-insensitive "Pkg: " strip
  RAW="${SUMMARY:$((${#PKG}+2))}"
elif [[ "$SUM_LOWER" == "${PKG_LOWER} "* ]]; then      # no-colon "Pkg " strip
  RAW="${SUMMARY:$((${#PKG}+1))}"
fi
RAW="${RAW%.}"                                          # strip trailing period
RAW="$(tr '[:lower:]' '[:upper:]' <<<"${RAW:0:1}")${RAW:1}"  # sentence-case first letter

PREFIX="[Security][${SEVERITY}] ${PKG}: "
BUDGET=$((70 - ${#PREFIX}))
if [[ ${#RAW} -gt $BUDGET ]]; then
  SUMMARY_SHORT="${RAW:0:$((BUDGET-1))}…"
else
  SUMMARY_SHORT="$RAW"
fi
TITLE="${PREFIX}${SUMMARY_SHORT}"
```

Worked examples:

| Raw advisory `.summary` | Title produced |
| ----------------------- | -------------- |
| `urllib3: Sensitive headers forwarded across origins in proxied low-level redirects.` | `[Security][high] urllib3: Sensitive headers forwarded across origins in pr…` |
| `GitPython: Insecure non-multi options accepted by clone / clone_from` | `[Security][high] GitPython: Insecure non-multi options accepted by clone…` |
| `Authlib: Cross-site request forging when using cache` | `[Security][medium] Authlib: Cross-site request forging when using cache` |

The GHSA ID lives in the issue body's `## Dependabot alert` block, which is what `gh issue list --search "$GHSA_ID in:title,body"` matches against for dedupe on repeat runs.

**Pre-create labels idempotently.** `gh issue create --label X` errors with `could not add label: 'X' not found` if the label doesn't already exist in the target repo. Since this skill is repo-agnostic across the Valory fleet, most target repos won't have these labels — every first PROD action would fail without this. Run once per skill invocation, before the per-alert loop:

```bash
# Idempotent label creation — `2>/dev/null || true` swallows the "already exists" error.
gh label create security              --color B60205 --description "Security vulnerability" --repo "$REPO" 2>/dev/null || true
gh label create dependabot            --color 0366D6 --description "Dependabot-reported"     --repo "$REPO" 2>/dev/null || true
gh label create triage-dependabot     --color 5319E7 --description "Opened by triage-dependabot skill" --repo "$REPO" 2>/dev/null || true
```

Issue body template (use a heredoc to preserve formatting):

```bash
ISSUE_URL=$(gh issue create --repo "$REPO" \
  --title "$TITLE" \
  --label "security,dependabot,triage-dependabot" \
  --body "$(cat <<EOF
## Dependabot alert

- Alert: $ALERT_URL
- Package: \`$PKG\` (pip)
- Severity: **$SEVERITY**
- GHSA: $GHSA_ID
- CVE: $CVE_ID
- Vulnerable range: \`$VULN_RANGE\`
- First patched: \`$FIRST_PATCHED\`

## Summary

$ADVISORY_SUMMARY

## Production reachability

Triage scan found the vulnerable package imported from the following production paths:

$PROD_HIT_FILES_BULLETED

(Scan covered: PROD_DIRS=$PROD_DIRS. Test/dev paths excluded.)

## Exploit-surface analysis

**Repo archetype:** $ARCHETYPE

**CVE preconditions** (from the GHSA description):
$CVE_PRECONDITIONS

**Codebase's usage pattern at the import sites:**
$USAGE_PATTERN_NOTES

**Applicability verdict:** $APPLICABILITY_VERDICT — $APPLICABILITY_REASONING

If you (the maintainer) judge the preconditions absent, close this issue and dismiss the linked Dependabot alert with reason \`inaccurate\` and a comment naming the missing precondition.

## Suggested fix

Upgrade the pin in \`pyproject.toml\` to \`>= $FIRST_PATCHED\` (or the next minor/major if a closer pin exists). If the package is transitive, identify the direct dep pulling it via \`uv tree --package $PKG --invert\` (or \`poetry show --why $PKG\`) and bump that.

If the package is owned by the open-autonomy / open-aea framework, the bump should go through \`/bump-versions\` instead of a manual pin edit.

## Why this issue exists

Triaged by the \`triage-dependabot\` skill. The Dependabot alert remains open as the source of truth; this issue tracks the in-repo work to fix it.
EOF
)")

# `gh issue create` does NOT support `--jq` (that flag is `gh api`-only).
# The command prints the new issue URL on stdout already, so the command
# substitution captures it directly. Don't append `--jq '.url'` — the
# subprocess will exit 1 with "unknown flag: --jq" and the URL will be lost.

echo "opened: $ISSUE_URL for $GHSA_ID"
```

The Dependabot alert is **not** dismissed for prod cases — it stays open and is the canonical record. The repo issue tracks the engineering work.

### 3.3 Skip (unclassifiable) alerts

Print one line per skipped alert to stderr so the operator can paginate:

```bash
echo "SKIP #$ALERT_NUM: $PKG ($GHSA_ID) — no production imports, no test imports, scope=$SCOPE. Manual review needed: $ALERT_URL" >&2
```

Never auto-dismiss a skipped alert. The whole point of skipping is "the skill doesn't know enough".

---

## Phase 4 — Summary

Bucket skips into two categories so the exit code reflects the actual failure surface:

| Bucket | When | Exit-code impact |
| ------ | ---- | ---------------- |
| `non-pip-ecosystem` | Alert's `ecosystem != "pip"` (Docker, npm, GitHub Actions). Expected — the skill scope is pip-only. | None. These are permanent state, not a per-run signal. |
| `unclassifiable` | Pip alert that fell through every signal (`scope=unknown`, no imports, no pyproject group, no transitive root). Genuinely "skill doesn't know enough". | Exit 1 — this is the real "incomplete run" signal CI/cron should react to. |

A naive `exit 1 if any skip` rule would fire on every run for any repo carrying even one permanent Docker/npm alert, defeating the purpose for cron wrappers.

End with a single stdout block summarising the run:

```
=== triage-dependabot summary for $REPO ===
Alerts seen:        $N_ALERTS
Processed:          $N_PROCESS                # respects --limit
Dismissed (DEV):    $N_DISMISSED
Issue opened (PROD): $N_OPENED
Skipped (non-pip):  $N_SKIPPED_ECOSYSTEM      # informational, no exit-code impact
Skipped (unclassifiable): $N_SKIPPED_UNCLASS  # exits 1 if > 0

Dismissed alerts:
  #123 PyYAML       GHSA-... (test-only: tests/helpers/yaml_loader.py)
  ...

Opened issues:
  #456 https://github.com/owner/repo/issues/456  GHSA-... cryptography
  ...

Skipped — non-pip ecosystem (informational):
  #654 GHSA-... docker-image (ecosystem=docker)
  ...

Skipped — unclassifiable (review manually):
  #789 GHSA-... obscure-pkg — no imports found, scope=unknown
  ...
```

Exit code: `1` if `N_SKIPPED_UNCLASS > 0`, else `0`. `N_SKIPPED_ECOSYSTEM` never affects exit code.

---

## Reference: full per-alert loop (shell + python combo)

This is the structural reference. Adapt to the repo (the Python pyproject parser is the heavyweight bit — keep it in a `python3 - <<'PY'` block invoked per-alert, or pre-compute a `dep_groups.json` once).

```bash
set -euo pipefail
TMP=$(mktemp -d)
REPO=$(gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"')
gh api "repos/$REPO/dependabot/alerts?state=open&per_page=100" --paginate > "$TMP/alerts.json"

N=$(jq 'length' "$TMP/alerts.json")
DISMISSED=(); OPENED=(); SKIPPED_ECOSYSTEM=(); SKIPPED_UNCLASS=()

# Path sets as bash ARRAYS — see §2.1 critical note. Do not use space-joined
# strings; they collapse across subshell boundaries and silently null out.
PROD_DIRS=()
for d in autonomy packages plugins libs aea operate agent; do
  [[ -d "$d" ]] && PROD_DIRS+=("$d")
done
TEST_DIRS=()
for d in tests scripts .github benchmark examples mints docs; do
  [[ -d "$d" ]] && TEST_DIRS+=("$d")
done
mapfile -t PKG_TEST_DIRS < <(find packages plugins -type d -name tests 2>/dev/null)
export PROD_DIRS TEST_DIRS PKG_TEST_DIRS

for i in $(seq 0 $((N-1))); do
  ALERT=$(jq ".[$i]" "$TMP/alerts.json")
  ALERT_NUM=$(jq -r '.number' <<<"$ALERT")
  ALERT_URL=$(jq -r '.html_url' <<<"$ALERT")
  ECOSYSTEM=$(jq -r '.security_vulnerability.package.ecosystem' <<<"$ALERT")
  PKG=$(jq -r '.security_vulnerability.package.name' <<<"$ALERT")
  SEVERITY=$(jq -r '.security_advisory.severity' <<<"$ALERT")
  GHSA_ID=$(jq -r '.security_advisory.ghsa_id' <<<"$ALERT")
  CVE_ID=$(jq -r '.security_advisory.cve_id // "n/a"' <<<"$ALERT")
  SUMMARY=$(jq -r '.security_advisory.summary' <<<"$ALERT")
  VULN_RANGE=$(jq -r '.security_vulnerability.vulnerable_version_range' <<<"$ALERT")
  FIRST_PATCHED=$(jq -r '.security_vulnerability.first_patched_version.identifier // "unknown"' <<<"$ALERT")
  SCOPE=$(jq -r '.dependency.scope // "unknown"' <<<"$ALERT")

  if [[ "$ECOSYSTEM" != "pip" ]]; then
    SKIPPED+=("$ALERT_NUM:non-pip-ecosystem:$ECOSYSTEM")
    echo "SKIP #$ALERT_NUM: ecosystem=$ECOSYSTEM (only pip is supported)" >&2
    continue
  fi

  # … Signal B + Signal C classification per Phase 2 …
  # … take action per Phase 3 …
done

# … print Phase 4 summary …
```

---

## Hard rules

1. **Only act on `state=open` alerts.** Don't poke at already-dismissed alerts.
2. **Skip non-pip ecosystems.** GitHub Actions / Docker / npm alerts can appear on Valory repos (e.g. `.github/workflows/*.yml` action pins) — flag them for manual review.
3. **Conservative default: when uncertain, open an issue, don't dismiss.** A false-positive issue costs one `gh issue close` command; a false-negative dismissal costs a quietly-shipped CVE.
4. **Two dismissal reasons, two strict criteria.**
   - `not_used` — Phase 2.4 Signal C proved the package is reachable only from test/dev paths. Comment names the test/dev files.
   - `inaccurate` — Phase 2.5 proved the CVE's threat-model preconditions are absent in this codebase's usage of the package. Comment names which precondition is absent.
   Never use `tolerable_risk` / `fix_started` / `no_bandwidth` — those need human cost/benefit calls the skill never has the context for.
5. **Dedupe before opening.** Search existing open issues by GHSA ID; never spam duplicates on repeat runs.
6. **Don't dismiss with no evidence.** Skip + log if neither prod nor test imports are found and the manifest is silent.
7. **Print stderr lines for skips.** The summary table is for the actor; the per-alert skip lines are for the human reviewer paginating through stderr.
8. **Exit non-zero only if an alert was skipped as `unclassifiable`.** `non-pip-ecosystem` skips are expected and informational — exiting on them would fire on every run for any repo carrying a Docker / npm / GitHub Actions alert, breaking cron wrappers.

---

## Files / state mutated

| Surface | What changes |
| ------- | ------------ |
| Dependabot alerts — DEV-only path | `state=dismissed`; `dismissed_reason=not_used`; comment includes the test/dev paths the scan found |
| Dependabot alerts — PROD-but-not-applicable | `state=dismissed`; `dismissed_reason=inaccurate`; comment names the absent CVE precondition + archetype |
| Repo issues — PROD-applicable | New issues opened with title `[Security][<sev>] <pkg>: <short summary>` (GHSA in body, not title), labels `security,dependabot,triage-dependabot`, body containing alert URL + prod import paths + **exploit-surface analysis** + suggested fix |
| Repo issues (existing) | Skipped via dedupe (no edit) |
| Working tree | Nothing — the skill only mutates GitHub state, not files |

---

## When NOT to run this skill

- The repo has Dependabot disabled — exit cleanly at Phase 0.
- You're partway through `/bump-versions` and `pyproject.toml` is in flight — the classification logic reads pyproject as source of truth; mid-bump state could misclassify. Finish the bump first, then triage.
- The repo has ecosystems beyond pip (Docker, npm, GitHub Actions) that you want triaged — current skill scope is pip only. Extending to other ecosystems means new import-graph resolvers and per-ecosystem prod/test path conventions.
