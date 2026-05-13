---
name: triage-security
description: Triage open security alerts on the current GitHub repo — both Dependabot (dependency CVEs) and Code Scanning (CodeQL / SnykCode / other tools that emit to GitHub's code-scanning API). For each alert, decide whether the bug's threat model is actually exploitable given this codebase's archetype, calling code, and reachability. Applicable findings get a tracking issue opened; not-applicable findings get dismissed with the appropriate per-source reason (`inaccurate` / `not_used` for Dependabot; `false positive` / `used in tests` for Code Scanning). Repo-agnostic — works across the Valory fleet.
argument-hint: "[--limit N] [--rerun-dismissed] [--source dependabot|code-scanning|both]  # --limit caps alerts processed; --rerun-dismissed walks already-dismissed Dependabot alerts and reports verdict drift (no mutations, Dependabot-only); --source defaults to `both`"
disable-model-invocation: true
---

# Triage security alerts (Dependabot + Code Scanning)

Walk every open security alert on the current repo from both Dependabot (`/repos/{r}/dependabot/alerts`) and Code Scanning (`/repos/{r}/code-scanning/alerts`). For each alert, classify by whether it is **reachable from production code** and then whether the bug's **threat model preconditions are satisfied** by this codebase's actual usage. Then act in one pass:

| Source | Classification | Confidence + extras | Action |
| ------ | -------------- | ------------------- | ------ |
| **Dependabot** | Production-reachable AND exploit-applicable | any | Open tracking issue, leave Dependabot alert open. |
| **Dependabot** | Production-reachable but exploit NOT applicable — cli-tool | **high** | Dismiss with `inaccurate` (+ audit issue per §3.1c). |
| **Dependabot** | Production-reachable but exploit NOT applicable — framework / scaffold + §2.5.6b passes | **high** | Dismiss with `inaccurate` (+ audit issue). |
| **Dependabot** | Production-reachable but exploit NOT applicable — moderate/low conf OR framework + §2.5.6b fails | — | Open issue + `needs-human-review`. Do NOT dismiss. |
| **Dependabot** | Test / dev / CI-only import path | n/a | Dismiss with `not_used` (+ audit issue). |
| **Code Scanning** | Rule matches `RULE_HUMAN_REVIEW_PATTERNS` (cert/TLS bypass, injection in prod, hardcoded secrets non-test, auth/authz, RCE/deserialization, path traversal) | any | Open issue + `needs-human-review`. **Never auto-dismiss this rule class.** |
| **Code Scanning** | Applicable — flagged code is reachable from prod entry point AND §2.5 preconditions hold | any | Open tracking issue, leave code-scanning alert open. |
| **Code Scanning** | NOT applicable (false positive) — cli-tool + §2.5 ruled preconditions absent | **high** | Dismiss with `false positive` (+ audit issue). |
| **Code Scanning** | NOT applicable — framework/service archetype OR moderate/low confidence | — | Open issue + `needs-human-review`. Do NOT dismiss. |
| **Code Scanning** | Flagged file is under `tests/` / `PKG_TEST_DIRS` | n/a | Dismiss with `used in tests` (+ audit issue). |
| Either source | Unclassifiable | n/a | Skip. stderr line for manual review. **Never** auto-dismiss without evidence. |

Conservative defaults: **when uncertain, open the issue.** A false-positive issue is cheap to close; a false-negative dismissal hides a real vulnerability. **`won't fix` (code-scanning) and `tolerable_risk` (Dependabot) are never set by the skill** — those are maintainer-only risk-accept calls.

Three paths to autonomous dismissal:
1. Dependabot: cli-tool + high confidence + preconditions absent → `inaccurate`
2. Dependabot: framework/scaffold + high confidence + §2.5.6b structural-impossibility passes → `inaccurate`
3. Dependabot: test/dev-only import path (Signal C) → `not_used`
4. Code-scanning: file under tests/ → `used in tests`
5. Code-scanning: cli-tool + high confidence + §2.5 preconditions absent + rule NOT in `RULE_HUMAN_REVIEW_PATTERNS` → `false positive`

Every dismissal produces a closed audit-trail issue (§3.1c) labelled `security-audit`. The 280-char `dismissed_comment` carries a one-line summary + audit-issue URL pointer.

This skill runs fully autonomously on invocation — it mutates GitHub state (dismisses alerts, opens issues). Do not invoke from conversational context; require explicit `/triage-security`.

---

## Phase 0 — Ground truth

```bash
# 0. Platform check. The skill targets Linux + macOS bash; runs untested on
#    Git Bash / MSYS / Cygwin. Native PowerShell / cmd.exe is not supported
#    (the skill uses heredocs, process substitution, array expansion).
case "$(uname -s 2>/dev/null)" in
  Linux*|Darwin*) ;;  # supported
  MINGW*|MSYS*|CYGWIN*)
    echo "WARN: running under $(uname -s) — Git Bash / MSYS path is untested. Most operations should work; report any failures." >&2
    ;;
  *)
    echo "WARN: unrecognized platform $(uname -s). Skill is bash-only and may fail on this OS." >&2
    ;;
esac

# Required CLIs — fail fast if anything is missing so the operator gets a clear
# message instead of a cryptic mid-loop error 40 minutes in.
for cmd in gh jq python3 grep find sed tr printf mktemp; do
  command -v "$cmd" >/dev/null 2>&1 \
    || { echo "ERROR: required CLI not found on PATH: $cmd"; exit 1; }
done

# 1. Confirm we're in a git repo with a GitHub remote
gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"' > /tmp/td_repo.txt 2>/dev/null \
  || { echo "ERROR: not in a GitHub repo (gh repo view failed)"; exit 1; }
REPO=$(cat /tmp/td_repo.txt)
echo "operating on $REPO"

# 2. Confirm alert APIs are reachable. Each is OPTIONAL — the skill can run
#    against either source, or both. Source selection happens in Phase 1.
#    Track availability so Phase 1 can fetch only what's actually enabled.
DEPENDABOT_AVAILABLE="no"
CODESCAN_AVAILABLE="no"
if gh api "repos/$REPO/dependabot/alerts?per_page=1" --jq 'length' > /dev/null 2>&1; then
  DEPENDABOT_AVAILABLE="yes"
else
  echo "WARN: Dependabot alerts API unreachable — Dependabot path will be skipped" >&2
fi
if gh api "repos/$REPO/code-scanning/alerts?per_page=1" --jq 'length' > /dev/null 2>&1; then
  CODESCAN_AVAILABLE="yes"
else
  echo "WARN: code-scanning alerts API unreachable — code-scanning path will be skipped" >&2
fi
[[ "$DEPENDABOT_AVAILABLE" == "no" && "$CODESCAN_AVAILABLE" == "no" ]] \
  && { echo "ERROR: neither Dependabot nor code-scanning is enabled on $REPO. Nothing to triage."; exit 1; }

# 3. Confirm a Python project layout exists (this skill currently keys off Python ecosystems)
test -f pyproject.toml \
  || { echo "ERROR: no pyproject.toml — skill only supports Python repos right now"; exit 1; }
```

### 0.2 RULE_HUMAN_REVIEW_PATTERNS — code-scanning rule classes that NEVER auto-dismiss

For code-scanning alerts (Phase 2-cs), some bug classes carry **asymmetric risk**: a false-positive dismissal of a real vulnerability is catastrophic, while a false-positive issue is cheap to close. For these classes the skill bypasses §2.5 and routes directly to a `needs-human-review` issue — regardless of how clean the confidence-tier analysis looks.

Pattern-match each alert's `rule.id` (and `rule.tags` for CWE-based matching) against this list. Match → force `needs-human-review`.

```bash
# Glob patterns matched case-insensitively against alert.rule.id.
# Add patterns here based on observed false-positive cost vs the
# blast radius of a real miss. Tested against actual SnykCode + CodeQL
# rule IDs seen on the Valory fleet.
RULE_HUMAN_REVIEW_PATTERNS=(
  # Cert / TLS verification bypass — bypass of HTTPS trust path
  "*disabled-certificate-check*"
  "*SSLVerificationBypass*"
  "*TooPermissiveTrustManager*"
  "*MissingCertVerification*"
  "*InsecureProtocol*"

  # Injection — SQL, XSS, command, XML — when fired on prod code
  "*SQLInjection*"
  "*XSS*"
  "*CommandInjection*"
  "*ShellInjection*"
  "*InsecureXmlParser*"
  "*XmlInjection*"
  "*LdapInjection*"
  "*TaintedFormatString*"

  # Hardcoded secrets in NON-test code. The /test variants of these
  # rules are auto-dismissable as `used in tests`; the bare names are not.
  "*HardcodedPassword"
  "*HardcodedCredential*"
  "*HardcodedNonCryptoSecret"
  "*HardcodedKey"
  "*EmbeddedCredentials*"

  # Auth / authz — can't statically prove "middleware X handles this"
  "*MissingAuth*"
  "*WeakAuthorization*"
  "*BrokenAccessControl*"
  "*authentication*"
  "*authorization*"

  # Deserialization / RCE — highest blast radius
  "*UnsafeDeserialization*"
  "*UnsafePickle*"
  "*PickleLoad*"
  "*UnsafeYaml*"
  "*CodeInjection*"
  "*EvalUsage*"
  "*UnsafeReflection*"

  # Path traversal — too easy to misjudge input-sourcing
  "*PathTraversal*"
  "*TaintedPath*"
  "*ZipSlip*"
)

# Helper: does the alert's rule.id match any pattern? (Phase 2-cs uses this.)
matches_human_review_pattern() {
  local rule_id="$1"
  # Lower-case both sides for case-insensitive match
  local rid_lower="${rule_id,,}"
  for pat in "${RULE_HUMAN_REVIEW_PATTERNS[@]}"; do
    local pat_lower="${pat,,}"
    # Bash glob match; `*foo*` matches "foo" anywhere in rule_id
    # shellcheck disable=SC2053
    [[ "$rid_lower" == $pat_lower ]] && return 0
  done
  return 1
}
```

The list is **deliberately conservative** on injection / RCE / auth — false-positive issues on `*PathTraversal*` are cheap; false-negative dismissals of a real one are expensive. Refine over time based on the actual false-positive rate observed in dismissed audit issues.

The skill does NOT match rule IDs with a `/test` suffix (e.g. `python/NoHardcodedPasswords/test`) against these patterns — those are tool-vendor-tagged test variants and are handled by the file-path-in-tests/ check in Phase 2-cs. Pattern matching applies to the bare (non-/test) rule IDs.

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

These are hints, not proofs. When the classification is ambiguous, **default to `framework`** so the skill errs on the side of bumping. A human can override by writing `archetype: cli-tool` in a per-repo `.triage-security.yaml` config (future enhancement — for now, hardcode the override at the top of the per-alert loop).

---

## Phase 1 — Fetch alerts (Dependabot + Code Scanning)

```bash
TMP=$(mktemp -d)
set -euo pipefail

# Parse argv.
#   --limit N            cap on per-source alerts processed
#   --rerun-dismissed    Dependabot-only read-only verdict-drift report (§3.0)
#   --source X           dependabot | code-scanning | both (default: both)
LIMIT=""
MODE="live"
SOURCE="both"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="$2"; shift 2 ;;
    --limit=*) LIMIT="${1#*=}"; shift ;;
    --rerun-dismissed) MODE="rerun-dismissed"; shift ;;
    --source) SOURCE="$2"; shift 2 ;;
    --source=*) SOURCE="${1#*=}"; shift ;;
    *) shift ;;
  esac
done
[[ -n "$LIMIT" ]] && [[ ! "$LIMIT" =~ ^[0-9]+$ ]] \
  && { echo "ERROR: --limit must be a non-negative integer, got: $LIMIT"; exit 1; }
case "$SOURCE" in
  dependabot|code-scanning|both) ;;
  *) echo "ERROR: --source must be dependabot|code-scanning|both, got: $SOURCE"; exit 1 ;;
esac

# rerun-dismissed mode is Dependabot-only. The skill only walks new open
# code-scanning alerts — never re-evaluates already-dismissed ones (per the
# operational decision that won't-fix / used-in-tests / false-positive
# dismissals are final calls; the rerun mode would create noise without
# operational value here).
if [[ "$MODE" == "rerun-dismissed" ]]; then
  if [[ "$SOURCE" == "code-scanning" ]]; then
    echo "ERROR: --rerun-dismissed is incompatible with --source=code-scanning. Use --source=dependabot or --source=both (code-scanning fetch is skipped in rerun mode)."
    exit 1
  fi
  SOURCE="dependabot"   # silently narrow if user passed --source=both
  STATE_FILTER="state=dismissed"
  echo "MODE=rerun-dismissed — read-only verdict-drift report on Dependabot dismissals only"
else
  STATE_FILTER="state=open"
fi

# Initialize the unified alert list. Each alert gets a `_source` field
# inserted at fetch time so Phase 2 can dispatch on it without re-querying.
echo "[]" > "$TMP/alerts.json"

if [[ "$SOURCE" == "dependabot" || "$SOURCE" == "both" ]]; then
  if [[ "$DEPENDABOT_AVAILABLE" == "yes" ]]; then
    gh api "repos/$REPO/dependabot/alerts?${STATE_FILTER}&per_page=100" --paginate \
      > "$TMP/alerts_dependabot.json" \
      || { echo "ERROR: failed to list Dependabot alerts"; exit 1; }
    jq -e 'type == "array"' "$TMP/alerts_dependabot.json" > /dev/null \
      || { echo "ERROR: Dependabot response not a JSON array"; head -20 "$TMP/alerts_dependabot.json"; exit 1; }
    # Tag each alert with `_source: "dependabot"` and merge into the unified list.
    jq 'map(. + {_source: "dependabot"})' "$TMP/alerts_dependabot.json" \
      > "$TMP/alerts_dependabot_tagged.json"
    jq -s 'add' "$TMP/alerts.json" "$TMP/alerts_dependabot_tagged.json" \
      > "$TMP/alerts_merged.json"
    mv "$TMP/alerts_merged.json" "$TMP/alerts.json"
    echo "fetched $(jq 'length' "$TMP/alerts_dependabot_tagged.json") Dependabot alerts"
  else
    echo "Dependabot unavailable on $REPO — skipping that source"
  fi
fi

if [[ "$SOURCE" == "code-scanning" || "$SOURCE" == "both" ]]; then
  if [[ "$CODESCAN_AVAILABLE" == "yes" ]]; then
    gh api "repos/$REPO/code-scanning/alerts?${STATE_FILTER}&per_page=100" --paginate \
      > "$TMP/alerts_codescan.json" \
      || { echo "ERROR: failed to list code-scanning alerts"; exit 1; }
    jq -e 'type == "array"' "$TMP/alerts_codescan.json" > /dev/null \
      || { echo "ERROR: code-scanning response not a JSON array"; head -20 "$TMP/alerts_codescan.json"; exit 1; }
    jq 'map(. + {_source: "code-scanning"})' "$TMP/alerts_codescan.json" \
      > "$TMP/alerts_codescan_tagged.json"
    jq -s 'add' "$TMP/alerts.json" "$TMP/alerts_codescan_tagged.json" \
      > "$TMP/alerts_merged.json"
    mv "$TMP/alerts_merged.json" "$TMP/alerts.json"
    echo "fetched $(jq 'length' "$TMP/alerts_codescan_tagged.json") code-scanning alerts"
  else
    echo "Code scanning unavailable on $REPO — skipping that source"
  fi
fi

N_ALERTS=$(jq 'length' "$TMP/alerts.json")
if [[ -n "$LIMIT" && "$LIMIT" -lt "$N_ALERTS" ]]; then
  echo "found $N_ALERTS alerts on $REPO ($SOURCE); processing first $LIMIT per --limit"
  N_PROCESS="$LIMIT"
else
  echo "found $N_ALERTS alerts on $REPO ($SOURCE)"
  N_PROCESS="$N_ALERTS"
fi
```

The per-alert loop in Phase 3 / the reference loop below must iterate `0..N_PROCESS-1`, not `0..N_ALERTS-1`. Phase 4 summary should report both `seen` (N_ALERTS) and `processed` (N_PROCESS) when they differ, so the operator knows how many alerts remain in the backlog.

### 1.1 Fields per alert source

The `_source` field added in Phase 1 routes each alert into the correct Phase 2 path.

**Dependabot alert fields:**

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

**Code-scanning alert fields:**

| Field | Path |
| ----- | ---- |
| Alert number | `.number` |
| Alert URL | `.html_url` |
| Tool | `.tool.name` (CodeQL, SnykCode, …) |
| Rule ID | `.rule.id` |
| Rule severity | `.rule.severity` (note / warning / error) or `.rule.security_severity_level` (low/medium/high/critical) |
| Rule description | `.rule.description` (one-liner) |
| Rule help / extended | `.rule.help` or `.rule.full_description` |
| Rule tags | `.rule.tags` (array — CWE-N entries surface here as `external/cwe/cwe-N`) |
| Flagged file | `.most_recent_instance.location.path` |
| Flagged line range | `.most_recent_instance.location.start_line`, `.end_line` |
| Flagged code message | `.most_recent_instance.message.text` |

**Skip immediately** any alert where:

- (Dependabot) `ecosystem != "pip"` — this skill only handles Python deps right now; bucket as `non-pip-ecosystem` skip (informational, no exit-code impact)
- `state != "open"` in live mode (defensive; pagination races happen)
- `auto_dismissed_at != null` (already auto-dismissed by GitHub)
- (Code Scanning) `.most_recent_instance.location.path == null` — the alert has no resolvable file location; flag for manual review (rare, usually a tool config error)
- (Code Scanning) flagged file path does not exist in the working tree — likely a stale alert against a now-deleted file; bucket as `stale-alert` skip

---

## Phase 2 — Classify each alert (per-source dispatch)

For every alert, the per-source dispatch in Phase 2 produces a normalized classification (`PROD` / `DEV` / `UNCLASSIFIABLE`) and a per-source verdict. Then Phase 2.5 runs the exploit-surface analysis (shared between sources). Finally Phase 3 acts based on the combined verdict.

```bash
# Per-alert loop dispatch — runs at the top of every iteration.
SOURCE_OF_THIS_ALERT=$(jq -r ".[$i]._source" "$TMP/alerts.json")

case "$SOURCE_OF_THIS_ALERT" in
  dependabot) ;;       # fall through to §2.1–§2.4 (existing Dependabot logic)
  code-scanning) ;;    # jump to §2.cs (new code-scanning logic, below)
  *) echo "ERROR: unknown _source: $SOURCE_OF_THIS_ALERT"; SKIPPED+=("$ALERT_NUM:unknown-source"); continue ;;
esac
```

The Dependabot logic that follows (§2.1–§2.4) is unchanged from the previous skill version. The code-scanning logic (§2.cs) is new and lives after §2.4.

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

# Per-package nested tests/ — these are TEST even though they live under packages/.
# Use a `while read` loop (not `mapfile`) — macOS ships bash 3.2 by default, and
# `mapfile` is a bash-4+ builtin. The skill must run on the default macOS shell.
PKG_TEST_DIRS=()
while IFS= read -r _d; do
  PKG_TEST_DIRS+=("$_d")
done < <(find packages plugins -type d -name tests 2>/dev/null)

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

### 2.cs Code-scanning classification (alternate to §2.2–§2.4)

For alerts with `_source == "code-scanning"`, the Dependabot signals (A: dependency.scope, B: pyproject group, C: import-graph scan) don't apply — the alert points at a specific line in our own code, not a vulnerable dependency. The code-scanning classification uses three different signals applied in priority order. **First decisive signal wins**.

#### 2.cs.1 Signal F — file location

The flagged file's location alone usually decides DEV vs PROD for code-scanning. Use the same `PROD_DIRS` / `TEST_DIRS` / `PKG_TEST_DIRS` arrays from §2.1.

```bash
ALERT_FILE=$(jq -r ".[$i].most_recent_instance.location.path" "$TMP/alerts.json")
ALERT_LINE=$(jq -r ".[$i].most_recent_instance.location.start_line // 0" "$TMP/alerts.json")

# Defensive: file must exist in the working tree. Stale alerts against
# deleted files get skipped (see Phase 1 skip rules).
[[ -f "$ALERT_FILE" ]] || { SKIPPED+=("$ALERT_NUM:stale-alert:$ALERT_FILE"); continue; }

# Classify the alert file's location.
ALERT_IN_TESTS="no"
ALERT_IN_PROD="no"

# Test paths — top-level and per-package
for d in "${TEST_DIRS[@]}" "${PKG_TEST_DIRS[@]}"; do
  if [[ "$ALERT_FILE" == "$d/"* ]] || [[ "$ALERT_FILE" == *"/$d/"* ]]; then
    ALERT_IN_TESTS="yes"
    break
  fi
done

# Prod paths
if [[ "$ALERT_IN_TESTS" == "no" ]]; then
  for d in "${PROD_DIRS[@]}"; do
    if [[ "$ALERT_FILE" == "$d/"* ]]; then
      ALERT_IN_PROD="yes"
      break
    fi
  done
fi
```

Verdict from Signal F:
- `ALERT_IN_TESTS == "yes"` → **DEV** → Phase 3.1d dismiss as `used in tests`. Skip §2.5 entirely (the analysis doesn't matter — the bug isn't in prod).
- `ALERT_IN_PROD == "yes"` → **PROD** → continue to Signal G + §2.5.
- Neither → **UNCLASSIFIABLE** — file is outside both prod and test trees (scripts/, docs/, top-level config files, etc.). Skip with a stderr note for manual review.

#### 2.cs.2 Signal G — rule-pattern force-review

For PROD-classified alerts, check whether the rule ID matches `RULE_HUMAN_REVIEW_PATTERNS` (§0.2). If yes, skip §2.5 and force route to Phase 3.2 with `needs-human-review`. This is the "high-stakes bug class" carve-out from the design discussion.

```bash
RULE_ID=$(jq -r ".[$i].rule.id" "$TMP/alerts.json")
RULE_SEVERITY=$(jq -r ".[$i].rule.severity // .[$i].rule.security_severity_level // \"unknown\"" "$TMP/alerts.json")

if matches_human_review_pattern "$RULE_ID"; then
  FORCE_REVIEW="true"
  REVIEW_REASON="rule.id matches RULE_HUMAN_REVIEW_PATTERNS — high-stakes bug class, never auto-dismiss"
fi
```

#### 2.cs.3 Signal H — function-privacy heuristic (input to §2.5)

For PROD-classified alerts that didn't get force-reviewed, walk the AST of the flagged file and find the enclosing function for the flagged line. If the enclosing function's name starts with `_` (Python's private-by-convention), that's evidence the flagged code is **less likely** reachable from a public entry point — feeds into §2.5.6 confidence as a positive signal toward "not-applicable" verdicts.

```python
# python3 - <<'PY' to determine the function privacy of the flagged line.
import ast, pathlib, os, sys
file_path = os.environ["ALERT_FILE"]
target_line = int(os.environ["ALERT_LINE"])
try:
    tree = ast.parse(pathlib.Path(file_path).read_text())
except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
    print("unknown")
    sys.exit()

enclosing = None
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        start = node.lineno
        end = getattr(node, "end_lineno", start)
        if start <= target_line <= end:
            # Take the innermost (largest start_line) enclosing function
            if enclosing is None or start > enclosing.lineno:
                enclosing = node

if enclosing is None:
    print("module-level")  # flagged code is at module scope, not in a function
elif enclosing.name.startswith("_"):
    print("private")
else:
    print("public")
PY
```

The output (`public` / `private` / `module-level` / `unknown`) feeds into §2.5.6 as one of the confidence-tier inputs. `private` shifts confidence toward `high` for not-applicable verdicts (since the code is one layer further from external callers); `module-level` shifts confidence toward `moderate` (executes at import time, less constrained); `public` is neutral.

This is not a reachability proof — a `_helper` can be called from a public API in the same file. But it's a useful priors signal absent a full call-graph trace.

#### 2.cs.4 Signal I — for code-scanning, §2.5.1 source is the rule itself

For Dependabot, §2.5.1 fetches the GHSA description. For code-scanning, the equivalent advisory text comes directly from the alert payload — no external fetch needed:

| Phase 2.5 input | Dependabot source | Code-scanning source |
| --------------- | ----------------- | -------------------- |
| `$ADVISORY_DESCRIPTION` | `gh api /advisories/$GHSA_ID .description` | `.rule.help // .rule.full_description // .rule.description` |
| `$CWE_IDS` | `.security_advisory.cwe_ids` | `.rule.tags` filtered for `external/cwe/cwe-N` patterns, mapped to `CWE-N` form |
| `$VULNERABLE_SYMBOL` (§2.5.4) | extracted from advisory description | the actual flagged line(s) — pulled from `$ALERT_FILE` via `sed -n "${ALERT_LINE}p"` |
| `$ADVISORY_SUMMARY` | `.security_advisory.summary` | `.rule.description // .most_recent_instance.message.text` |

§2.5.2 (per-advisory checklist derivation) works the same way — read the rule description, derive Qs against the flagged code. §2.5.4 morphs from "is the vulnerable symbol used anywhere in prod" to "what does the flagged code actually do that triggered this rule" — the answer is already in `$ALERT_FILE` at `$ALERT_LINE`, no grep needed.

#### 2.cs.5 Skip §2.5.6b for code-scanning

The structural-impossibility check (§2.5.6b) is Dependabot-specific — it asks "does the framework's public API expose attacker-controlled input to the vulnerable subsystem of a third-party dep?" For code-scanning, the bug *is* in our code; the structural-impossibility framing doesn't apply. Set `STRUCTURAL_IMPOSSIBLE="n/a"` for code-scanning alerts so the §2.5.7 action matrix routes through the cli-tool / framework / service rows on confidence alone.

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

Read the `description` and `cwe_ids` fields. The advisory **description is the primary source of truth** for §2.5.2 — it carries the specific threat model for *this* advisory, which is usually narrower than the CWE class average. The `cwe_ids` are a hint about the bug class, used as a sanity check (see §2.5.2's reference patterns) and to drive optional MITRE supplementation in §2.5.1b.

#### 2.5.1b MITRE CWE supplementation (optional, sparse-advisory fallback)

Most GHSA descriptions are rich enough to derive a checklist directly (see §2.5.2). When an advisory is sparse — one-line summary, no code samples, no named vulnerable API — supplement with the MITRE CWE definition for additional context:

```bash
# Pull the CWE definition for each CWE the advisory carries. MITRE publishes
# per-CWE JSON; the canonical definition includes description, common
# consequences, detection methods, mitigations. Use as context for §2.5.2,
# never as the *primary* source — the advisory's specifics dominate.
for CWE_ID in $(jq -r '.cwe_ids[]' "$TMP/advisory_${GHSA_ID}.json"); do
  CWE_NUM="${CWE_ID#CWE-}"
  curl -sf "https://cwe.mitre.org/data/definitions/${CWE_NUM}.json" \
    -o "$TMP/cwe_${CWE_NUM}.json" \
    || echo "WARN: MITRE fetch failed for $CWE_ID — proceeding with advisory text only" >&2
done
```

When the MITRE fetch succeeds, the fields most useful for §2.5.2 are:
- `Description` / `Extended_Description` — abstract bug-class description
- `Common_Consequences` — typed list of impacts (`Confidentiality`, `Integrity`, `Availability`, `Authentication`) which suggests which Qs to ask
- `Detection_Methods` — hints about what code shapes to grep for
- `Potential_Mitigations` — inversion of these often surfaces preconditions

This step is **optional and skippable** — most advisories don't need it. Add it to the workflow only when §2.5.2's per-advisory derivation can't produce ≥2 testable Qs from the advisory text alone (the trigger for the §2.5.6 sparse-advisory cap).

#### 2.5.2 Derive the CVE's required preconditions

Read the advisory description fetched in §2.5.1 (and optionally §2.5.1b MITRE supplement) and **derive the precondition checklist directly from it**. The advisory describes the *specific* bug with its *specific* preconditions — that's the source of truth, not a static class-average mapping.

Structure the output as Q1, Q2, … so the audit trail has stable referents. The operator (running this skill via Claude Code, which is the supported mode) reads the advisory text and produces:

1. **A list of preconditions the attacker needs**, extracted from phrases like "An attacker can …", "requires …", "when the application …", "affects code that …" in the advisory description.
2. **A list of named vulnerable symbols** for §2.5.4 (class.method, function names, kwargs, flags — these are typically formatted in backticks or code blocks in the advisory).
3. **For each precondition, a testable Q** phrased against the calling code: "Does the calling code do X?" Reword the precondition into a question the §2.5.3 step can answer `reachable` / `absent` / `unknown` against this specific codebase.

The questions should be **as narrow as the advisory allows.** If the advisory names `ProxyManager.connection_from_url(...).urlopen(..., assert_same_host=False)`, don't ask the abstract Q "does the code carry sensitive headers" — ask the sharper "does the code call `ProxyManager.connection_from_url` with `assert_same_host=False` and any sensitive header." Sharper Qs produce sharper verdicts.

Write each Q&A answer down. The audit trail must include the derived Q list verbatim — a future reviewer needs to know what was asked, not just the verdict.

**Reference patterns** (use as a sanity check that you've covered the standard preconditions for the bug class — NOT as a dispatch table). Common CWE classes and the kinds of Qs they typically require:

| CWE ID(s) | Bug class | Typical question shape |
| --------- | --------- | ---------------------- |
| CWE-200, CWE-201, CWE-209 | Information / header / token leak | Does calling code carry sensitive state? Does the leak path require attacker-controlled destination? Can the attacker influence that destination? |
| CWE-22, CWE-23 | Path traversal | Does calling code pass external/attacker-controlled paths to the vulnerable API? |
| CWE-78, CWE-77, CWE-88 | Command / argument injection | Does calling code pass external args to subprocess / shell? Is the vulnerable spawn helper invoked? |
| CWE-89 | SQL injection | Does calling code build queries from external strings? Is the vulnerable codepath actually invoked (raw-SQL vs ORM-only)? |
| CWE-94, CWE-502, CWE-915 | Code injection / deserialization RCE | Does calling code deserialize / eval external bytes? Is the unsafe loader invoked, vs the safe variant? |
| CWE-295, CWE-297, CWE-345, CWE-322 | TLS / cert / signature bypass | Does calling code make outbound TLS to non-internal hosts? Is the trust decision based on the vulnerable verification path? Are hostnames user-controlled? |
| CWE-352 | CSRF | Is there a browser-driven request flow? Does the vulnerable endpoint actually exist in our service? |
| CWE-400, CWE-409, CWE-770, CWE-789, CWE-1333 | DoS — memory / regex / compression | Does calling code accept attacker-controlled bytes of arbitrary length? Uptime contract — long-lived service vs one-shot CLI? |
| CWE-918 | SSRF | Does calling code fetch URLs with externally-supplied hosts? Is the deployment environment sensitive to internal-network access? |
| CWE-601 | Open redirect | Does calling code expose redirect targets to user input? Is this a web frontend holding session state? |
| CWE-327, CWE-328, CWE-326, CWE-916 | Weak crypto | Does calling code use the weak primitive for a security-sensitive purpose? Are keys/parameters under our control? |
| CWE-862, CWE-863 | Missing / incorrect authz | Does calling code expose any endpoint gated by the vulnerable check? |
| CWE-203 | Observable / timing discrepancy | Is the vulnerable comparison used in a security-sensitive context? Is timing exploitable across many requests? |
| CWE-674 | Uncontrolled recursion (distinct from CWE-1333 ReDoS) | Does calling code accept attacker-controlled depth-bearing input? Uptime contract? |
| CWE-732 | Incorrect permission assignment | Does calling code create files on a shared filesystem via the vulnerable API? Are files sensitive? |
| CWE-377, CWE-378, CWE-379 | Insecure temp file | Does calling code use vulnerable temp-file API in a shared-tmp context? Are race windows exploitable in practice? |
| CWE-426, CWE-427 | Untrusted search path | Does the process spawn subprocesses / load libs from PATH-resolved names? Is PATH attacker-controllable? |
| CWE-79 | XSS | Does calling code render the vulnerable template / sink to a browser? Is data piped into the sink external? |
| CWE-20 | Improper input validation (class-wide) | Does calling code pass external input to the vulnerable API? Downstream consequence + caller-side shielding? |

The above is a hint about which question shapes typically apply for a CWE class — use it to verify your derived Qs aren't missing a standard precondition. Always derive from the advisory text; never use this table as the sole source.

**Why per-advisory derivation beats a static dispatch:** the same CWE class can describe wildly different bugs. CWE-22 might be "path traversal in `clone_from` clone target" in one advisory and "path traversal in `os.path.join` with `..` segments" in another — the preconditions differ. A static dispatch gives you the *average*; the advisory text gives you the *specific*. For an autonomous-dismissal decision, specific wins.

#### 2.5.3 Map preconditions against the calling code

For each PROD import path found in Signal C, **read the calling file** (or the relevant function) and answer:

1. Does the calling code carry the sensitive state the CVE targets? (auth headers? session cookies? privileged file paths? OAuth state?)
2. Does the calling code accept input from an untrusted source? (network user? HTTP request body? environment variable populated by an external system?) Or is the input developer-controlled (repo source, hardcoded URL, deterministic config)?
3. Is the calling process long-lived / network-reachable, or one-shot CLI?

Cross-reference the answers against the **checklist Qs from §2.5.2**. For each Q, record one of: `reachable` (precondition satisfied by the calling code), `absent` (precondition cannot be satisfied given the calling code), or `unknown` (cannot determine without runtime trace or deeper analysis). If **any** required precondition is `absent`, the CVE is candidate **not applicable**. If **any** is `unknown`, the analysis is candidate **moderate confidence** at best (see §2.5.6).

#### 2.5.4 Vulnerable-symbol call-graph trace (one level)

Signal C in §2.4 confirms the package is imported. That's necessary but not sufficient — the *specific vulnerable API* named in the advisory must also be reachable. Many CVEs name a concrete function/method/flag (`ProxyManager.connection_from_url`, `assert_hostname`, `yaml.unsafe_load`, `Repo.clone_from(multi_options=...)`). If the calling code uses the package but never reaches the vulnerable symbol, the CVE is not exploitable in this codebase even though Signal C lit up.

This is a one-level static grep — not full call-graph analysis. It catches the common case where the calling code uses a different entrypoint of the same package.

Step 1 — extract the vulnerable symbol(s) from the advisory description. Look for class.method, function names, kwargs, and CLI flags:

```bash
# Extract code-like tokens (Class.method, function(, --flag) from the advisory.
# Curate the list — the regex over-collects; human/LLM judgment picks which
# of these are the actual vulnerable surface vs prose references.
jq -r '.description' "$TMP/advisory_${GHSA_ID}.json" \
  | grep -oE '`[^`]+`|\b[A-Z][A-Za-z0-9_]*\.[a-z_][A-Za-z0-9_]*\b|\b[a-z_][A-Za-z0-9_]+\(' \
  | sort -u
```

Step 2 — grep production code for each candidate symbol. Use the same `PROD_DIRS` array machinery as §2.4 (quoted-each-element expansion, `/build/` and `/tests/` filtered):

```bash
# For each curated vulnerable symbol $SYM (escape regex metachars first):
SYM_RE=$(printf '%s' "$SYM" | sed 's/[][\\/.*^$+?{}()|]/\\&/g')

SYMBOL_HITS=$(grep -rlnE "$SYM_RE" "${PROD_DIRS[@]}" --include="*.py" 2>/dev/null \
  | grep -v "/build/" | grep -v "/tests/" \
  | wc -l | tr -d ' ')
```

Step 3 — verdict feeds into §2.5.6 confidence:

| Vulnerable symbol in advisory? | `SYMBOL_HITS` | Effect |
| ------------------------------ | ------------- | ------ |
| Yes, specific symbol named | `> 0` | Strong evidence CVE is reachable — confidence shifts toward **high** for an "applicable" verdict |
| Yes, specific symbol named | `0` | Strong evidence CVE is NOT reachable — confidence shifts toward **high** for a "not-applicable" verdict (this is the §2.5.3 `absent` case backed by code evidence, not just inference) |
| No specific symbol named (CVE is class-wide — e.g. "any use of `requests` with proxies") | n/a | Skip this step; confidence ceiling is **moderate** at best because there's no symbol to grep for |
| Symbol named but obscured by aliasing / dynamic dispatch | n/a | Mark as `unknown` for §2.5.3 — confidence drops one tier |

This step is **the difference between dismissing as `not_used` (Phase 2.4 found no imports anywhere) and dismissing as `inaccurate` with high confidence (Phase 2.4 found imports, but Phase 2.5.4 confirmed the vulnerable surface is unreached).**

Known limitations — these are the cases where the grep is insufficient and confidence MUST drop:
- **Dynamic dispatch** — `getattr(obj, method_name)` where `method_name` is computed at runtime. Grep won't see it.
- **Framework abstraction** — the calling code goes through a framework's HTTP transport (e.g. `web3.HTTPProvider` → `requests` → `urllib3`); the vulnerable symbol is reached internally, not by direct call. Grep at this level won't see it.
- **Aliased imports** — `from urllib3 import ProxyManager as PM` then `PM.connection_from_url(...)`. The earlier import-graph scan catches the import; this step won't catch the use unless the alias is grepped too.

When any of these patterns is plausible given the package's role, drop the confidence tier and mark the precondition `unknown` in §2.5.3.

#### 2.5.5 The archetype multiplier

Apply the `ARCHETYPE` value from Phase 0.1:

| Archetype | Default exploit-surface posture |
| --------- | ------------------------------- |
| `cli-tool` | **Strict** — CVEs requiring browser sessions, long-running listeners, untrusted-remote inputs, server-side state are presumed not-applicable. Memory-DoS CVEs are not-applicable unless uptime is a contractual concern. The CVE must show a concrete exploit chain that fits the CLI usage to count as applicable. |
| `framework` / `scaffold` | **Permissive** — consumers may use the framework in any archetype, so a CVE that's exploitable in *some* downstream consumer is applicable here. Default to PROD-applicable unless the CVE is structurally impossible (e.g. an auth CVE in a library that has no auth code at all). |
| `service` | **Permissive** — long-running, network-reachable, often handles user input. Default to PROD-applicable. |
| `unknown` | Treat as `framework`. |

#### 2.5.6 Confidence tier

Derive a confidence tier in `{high, moderate, low}` from the §2.5.3 precondition map AND the §2.5.4 vulnerable-symbol trace. The tier is what gates dismissal in Phase 3 — `inaccurate` dismissals require **high** confidence.

| Confidence | All of these must hold |
| ---------- | ---------------------- |
| **high** | Every Q derived in §2.5.2 was answered `reachable` or `absent` (no `unknown`) **AND** the §2.5.4 vulnerable-symbol trace produced a definitive yes/no (specific symbol named in advisory + grep returned `0` or `>0` hits, no aliasing / framework-internal / dynamic-dispatch caveats applied) **AND** the archetype is unambiguous from §0.1 heuristics **AND** §2.5.2 produced ≥2 testable Qs from the advisory (sparse-advisory check) |
| **moderate** | At least one of the above conditions is borderline: one Q is `unknown`, OR the advisory names the CVE class-wide with no specific symbol to grep for, OR the archetype detection landed on `unknown` and defaulted to `framework`, OR the advisory was too sparse to derive ≥2 testable Qs even with the §2.5.1b MITRE supplement |
| **low** | Multiple Qs are `unknown`, OR aliasing/framework-internal dispatch is plausible AND the symbol grep returned `0` hits (false-negative risk), OR the calling code reaches the package through a third-party transport whose behavior isn't audited in this repo |

Two heuristics worth applying mechanically:

- If §2.5.2 derived ≥2 specific testable Qs from the advisory AND §2.5.4 produced a definitive symbol-trace result AND the archetype is `cli-tool` or `service` (unambiguous), default to **high**.
- If §2.5.2 could only derive ≤1 Q (sparse advisory) OR the archetype is `unknown`, ceiling is **moderate** regardless of how clean the other signals are. The sparse-advisory case is the right signal that we don't know enough to dismiss autonomously — when even MITRE supplementation (§2.5.1b) can't produce a checklist, route to `needs-human-review` rather than guess.

#### 2.5.6b Structural impossibility check (frameworks / scaffolds only)

The §2.5.5 archetype rule defaults `framework` and `scaffold` to "permissive" — consumers may use the framework in ways this repo can't anticipate, so default to PROD-APPLICABLE. But §2.5.5's prose carries an escape clause: *"unless the CVE is structurally impossible (e.g. an auth CVE in a library that has no auth code at all)."* Without operationalizing it, the matrix routes every framework + precondition-absent case to a `needs-human-review` issue — which produces issue spam for cases that are genuinely autonomous-dismissible (e.g. a GitPython CVE in a framework that only calls `Repo(local_path)` and exposes no clone API).

This step makes the escape clause operational. For framework / scaffold archetypes, **before** falling through to the permissive default in §2.5.7, check whether **all three conditions hold**:

1. **Symbol grep was definitive (§2.5.4)** — the advisory named a specific vulnerable symbol AND the grep returned exactly 0 hits in prod code, with no aliasing / dynamic-dispatch / framework-internal caveats applied. If the advisory is class-wide ("any use of `requests` with proxies"), this condition fails — there's no symbol to grep for, so structural impossibility can't be proven.

2. **Existing import sites are orthogonal in usage** — walk every prod file from §2.4 Signal C and read what the imported symbols are actually used for. Classify each call site as:
   - `orthogonal` — the imported symbols are used only for purposes the advisory doesn't name. Examples: importing a class but using only its constructor / read-only methods / non-vulnerable methods (e.g. `Repo(local_path)` for HEAD/working-tree reads when the CVE is in `Repo.clone_from`); importing exception classes; importing types/constants.
   - `vulnerable-adjacent` — the call site actually invokes a method/attribute named by the advisory, OR uses the symbol in a way that could reach the vulnerable code path under normal control flow (e.g. importing `PoolManager` and calling `.request()` when the CVE is in the high-level request path).

   All Signal C call sites must be `orthogonal`. If any is `vulnerable-adjacent`, the check fails — the existing usage is at least one method-call away from the CVE, and a small caller change could complete the path.

   Note: this is a stricter test than §2.5.4 alone. §2.5.4 says "the vulnerable symbol isn't called *right now*"; condition 2 here says "and the framework isn't using the same subsystem in a way that's one step away from calling it."

3. **No public API forwards external inputs to the vulnerable subsystem** — enumerate the framework's public API and ask whether any parameter could plausibly become the vulnerable kwarg/argument named in the advisory.

   **Enumerate via AST**, not grep — `def name(self, url, ...)` with the body using `urllib3.PoolManager(...)` is the kind of call site that condition 3 cares about, and grep can't reliably extract parameter names from formatted multi-line `def` signatures. Run this once per skill invocation, cache the result:

   ```python
   # python3 - <<'PY' to scan PROD_DIRS for public-API surface.
   import ast, pathlib, json, os
   prod_dirs = os.environ["PROD_DIRS"].split()  # set by §2.1 array expansion
   public_apis: list[dict] = []
   for d in prod_dirs:
       root = pathlib.Path(d)
       if not root.exists():
           continue
       for p in root.rglob("*.py"):
           parts = str(p).split("/")
           if "tests" in parts or "build" in parts:
               continue
           try:
               tree = ast.parse(p.read_text())
           except (SyntaxError, UnicodeDecodeError):
               continue
           for node in ast.walk(tree):
               if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                   continue
               if node.name.startswith("_"):           # private by convention
                   continue
               params = [a.arg for a in node.args.args if a.arg != "self"]
               kwonly = [a.arg for a in node.args.kwonlyargs]
               public_apis.append({
                   "file": str(p), "line": node.lineno, "name": node.name,
                   "params": params + kwonly,
               })
   print(json.dumps(public_apis))
   PY
   ```

   **Match against the advisory's vulnerable inputs.** Use the vulnerable-symbol extraction from §2.5.4 step 1 — it already produces a candidate list (function names, kwargs, flags). For each public API in the AST output, check whether any of its parameter names fuzzy-match the advisory's vulnerable inputs. A *match* is one of:
   - exact name (`proxy`, `url`, `headers`, `cookies`, `target_path`, `multi_options`)
   - common alias (`url` matches `target_url` / `endpoint` / `remote`; `path` matches `file_path` / `dest`; `options` matches `opts` / `kwargs`)
   - the parameter is typed as `**kwargs` AND the calling code passes through to the vulnerable API (one-step grep)

   If **zero matches** → condition 3 passes (no public API exposes the vulnerable input). If **any match** → condition 3 fails — the public API plausibly forwards external input to the vulnerable subsystem, route to `needs-human-review`.

   This is intentionally permissive on the *match* side (treats common-alias as a hit) so we err toward human review when the surface is ambiguous, but conservative on the *enumeration* side (only `def` at module top-level or class methods, ignoring private `_name` and dunders).

   Examples:
   - `def make_request(self, url, headers=None, proxy=None)` in a framework + urllib3 proxy/header CVE → params `[url, headers, proxy]` match `url` + `proxy` + `headers` → **fail**.
   - `def bump_version(self, package: str, version: str)` in `aea-dev-helpers` + GitPython clone CVE → params `[package, version]` match nothing in `[remote, url, path, clone_target, multi_options]` → **pass**.
   - `def read_config(self, path: str)` in a framework + GitPython path-traversal CVE → param `path` matches `path` → **fail** (even if the function never touches git, the parameter shape is dangerous when combined with the imported `Repo` class).

When **all three conditions hold**, the framework's code structurally cannot reach the vulnerable surface AND doesn't expose a public API a consumer could exploit. Mark the verdict **NOT-APPLICABLE (structural)** — this is high-confidence on par with cli-tool dismissal, eligible for autonomous `inaccurate` dismissal.

Worked example — **passes**: open-aea + GitPython CVEs (CWE-20, CWE-94, CWE-22 on `clone_from` / `multi_options`). Open-aea imports `from git import Repo` only in `aea-dev-helpers/bump_version.py`, uses it as `Repo(local_path)` to read the working tree, exposes no public API that takes a clone URL or path. (1) symbol grep for `clone_from` / `multi_options` = 0. (2) all imports are read-only Repo operations, orthogonal to the clone subsystem. (3) public API of `aea-dev-helpers` is a CLI bump-version tool — no parameter could become a clone URL. → all three conditions hold → autonomous dismiss.

Worked example — **fails**: a framework that imports `from urllib3 import PoolManager` and exposes `def make_request(url, headers, proxy=None)`. Even if the framework's own callsites don't trigger the CVE, condition (3) fails — the public API forwards user-controlled inputs into the vulnerable subsystem. Must route to `needs-human-review` issue.

The `cli-tool` archetype doesn't need this check — it already gets autonomous dismissal under §2.5.7 directly. The `service` archetype also doesn't get this check — services ARE the consumer (long-running, real attack surface), so framework-style structural-impossibility doesn't apply.

#### 2.5.7 Final verdict + action matrix

Combine §2.5.3 (preconditions match), §2.5.5 (archetype posture), §2.5.6 (confidence tier), and §2.5.6b (structural-impossibility check for frameworks) into one action call. The action matrix is conservative on the dismissal side and permissive on the issue side — false-positive issues are cheap, false-negative dismissals are expensive. But for framework / scaffold archetypes, §2.5.6b lets the skill bypass the "default to caution" rule when structural impossibility is provable, so we don't drown the human reviewer in spurious issues.

**Dependabot action matrix** (unchanged from prior version):

| Preconditions | Archetype | Confidence | §2.5.6b | Verdict | Action (Dependabot) |
| ------------- | --------- | ---------- | ------- | ------- | ------ |
| All `reachable` | any | high or moderate | n/a | **PROD-APPLICABLE** | Open issue (Phase 3.2). If confidence = moderate, additionally label `needs-human-review`. |
| All `reachable` | any | low | n/a | **PROD-APPLICABLE** | Open issue + `needs-human-review` label. Body must call out the uncertainty source(s). |
| Any `absent` | `cli-tool` | **high** | n/a | **NOT-APPLICABLE** | Dismiss with `inaccurate` (Phase 3.1b). Comment names which Q failed and references the §2.5.4 symbol-grep result. |
| Any `absent` | `cli-tool` | moderate / low | n/a | **NOT-APPLICABLE (low-conf)** | Open issue + `needs-human-review` label. Do NOT dismiss — the maintainer decides. |
| Any `absent` | `framework` / `scaffold` | **high** | **passes** | **NOT-APPLICABLE (structural)** | Dismiss with `inaccurate` (Phase 3.1b). Comment names which §2.5.6b condition was decisive — typically the missing public-API surface or the orthogonal import pattern. |
| Any `absent` | `framework` / `scaffold` | high | **fails** | **PROD-APPLICABLE** | Open issue + `needs-human-review`. Body explains which §2.5.6b condition failed (e.g. "framework exposes `make_request(url, headers, proxy)` — consumer might satisfy CWE-200 Q1+Q3"). |
| Any `absent` | `framework` / `scaffold` | moderate / low | any | **PROD-APPLICABLE** | Open issue + `needs-human-review`. The signals aren't reliable enough for structural-impossibility to be safe. |
| Any `absent` | `service` | any | n/a | **PROD-APPLICABLE** | Open issue. Services are long-running and themselves the consumer — structural impossibility doesn't apply. |
| Any `unknown` | any | any | n/a | **PROD-APPLICABLE** | Open issue + `needs-human-review`. Do NOT dismiss. |

**Code-scanning action matrix** (new):

| Signal F (file location) | Signal G (rule pattern) | Preconditions | Archetype | Confidence | Verdict | Action (Code Scanning) |
| ------------------------ | ----------------------- | ------------- | --------- | ---------- | ------- | ---------------------- |
| **in tests/** | any | n/a | any | n/a | **TEST-ONLY** | Dismiss with `used in tests` (Phase 3.1d). |
| in prod | **force-review** | n/a | any | n/a | **NEEDS-HUMAN-REVIEW** | Open issue + `needs-human-review`. **NEVER** auto-dismiss this rule class. |
| in prod | normal | All `reachable` | any | any | **PROD-APPLICABLE** | Open issue. If confidence != high, additionally label `needs-human-review`. |
| in prod | normal | Any `absent` | `cli-tool` | **high** | **FALSE-POSITIVE** | Dismiss with `false positive` (Phase 3.1e). Comment names the failing Q + Signal H privacy hint. |
| in prod | normal | Any `absent` | `cli-tool` | moderate / low | NOT-APPLICABLE (low-conf) | Open issue + `needs-human-review`. |
| in prod | normal | Any `absent` | `framework` / `scaffold` | any | **PROD-APPLICABLE** | Open issue + `needs-human-review`. Consumers may use the framework's public API in ways that hit the flagged path. |
| in prod | normal | Any `absent` | `service` | any | **PROD-APPLICABLE** | Open issue. Services are themselves the consumer; conservative-by-default. |
| in prod | normal | Any `unknown` | any | any | **PROD-APPLICABLE** | Open issue + `needs-human-review`. |
| **unclassifiable file location** | any | n/a | any | n/a | **SKIP** | stderr line for manual review — flagged file outside both prod and test trees. |

The two matrices share the same Phase 2.5 confidence-tier logic. The Dependabot matrix has the extra `§2.5.6b structural-impossibility` column because consumer-context unknowability matters when the bug is in a third-party dep. The code-scanning matrix is **stricter on framework auto-dismissal** — the bug is in our own code, so "consumer might hit this" is even more relevant than in the Dependabot case; no autonomous dismissal for framework/scaffold code-scanning alerts.

When dismissing, the `dismissed_comment` must name:
- Dependabot `inaccurate`: which checklist Q failed + (framework/scaffold) which §2.5.6b condition was decisive.
- Dependabot `not_used`: where the test/dev imports were found.
- Code-scanning `false positive`: which Q failed + Signal H result (function privacy) + reference to the audit issue.
- Code-scanning `used in tests`: the test path the alert fired against.

Examples:

- Dependabot cli-tool: "Tomte's link checker carries no auth headers — CWE-200 Q1 absent. §2.5.4 grep for `connection_from_url` = 0 hits."
- Dependabot framework structural: "Open-aea: GitPython CVE not reachable. §2.5.6b — only `Repo(local_path)` read usage in `bump_version.py` (orthogonal), no public API forwards URLs/paths to clone subsystem."
- Code-scanning cli-tool false-positive: "`python/HardcodedNonCryptoSecret` in `tomte/cli.py:142` — the 'secret' is a deterministic content hash (Q1 absent); function is `_compute_pkg_hash` (private). Not exploitable."
- Code-scanning used-in-tests: "`python/reDOS` in `tests/test_url_parsing.py:88` — test fixture for a parser; the regex never sees attacker input at runtime."

That comment is the audit trail; a future reviewer needs enough information to challenge the call without re-running the analysis from scratch.

#### 2.5.8 Out of scope: PoC harness

The gold-standard verification of "is this CVE exploitable in this codebase" is to run the public exploit PoC against the actual codebase. This skill does **not** automate that for three reasons:

- PoCs are CVE-specific and hand-crafted; they don't generalize into a harness.
- The PoC may be destructive (RCE, data exfiltration) — running it in a developer environment is not safe by default.
- The threat model is "exploitable from where the calling code sits," not "the bug still exists upstream" — the PoC tests the latter.

If a `moderate` or `low`-confidence dismissal is challenged by the maintainer, **PoC verification is the documented escalation path.** Note that in the `needs-human-review` issue body so the maintainer knows what to do next.

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

When `MODE=rerun-dismissed`, **Phase 3.0 runs instead of 3.1 / 3.1b / 3.2 / 3.3** — the skill produces a report comparing the new verdict to the recorded `dismissed_reason` for each alert, and takes no actions. Use this after a §2.5 logic change to surface previously-dismissed alerts whose verdict would now differ.

### 3.0 Rerun-dismissed report mode (read-only)

Walks already-dismissed alerts and reports verdict drift between the current skill logic and the historical dismissal. No `gh api PATCH`, no `gh issue create` — the only mutations are to stdout / the report file.

```bash
# Run §2.4 (Signal C) + §2.5 (exploit-surface) for the alert, producing the
# same $VERDICT / $CONFIDENCE / $STRUCTURAL_IMPOSSIBLE / $NEW_DISMISSED_REASON
# variables as the live path. Then compare to recorded fields.
RECORDED_REASON=$(jq -r ".[$i].dismissed_reason" "$TMP/alerts.json")
RECORDED_COMMENT=$(jq -r ".[$i].dismissed_comment // \"\"" "$TMP/alerts.json")

# Map the live-path verdict back to the reason the skill *would* use today.
if [[ "$VERDICT" == "DEV" ]]; then
  NEW_REASON="not_used"
elif [[ "$VERDICT" == "NOT-APPLICABLE" || "$VERDICT" == "NOT-APPLICABLE (structural)" ]] \
   && [[ "$CONFIDENCE" == "high" ]] \
   && { [[ "$ARCHETYPE" == "cli-tool" ]] || [[ "$STRUCTURAL_IMPOSSIBLE" == "true" ]]; }; then
  NEW_REASON="inaccurate"
else
  NEW_REASON="open-issue"  # would route to Phase 3.2 with needs-human-review under live mode
fi

case "${RECORDED_REASON}:${NEW_REASON}" in
  "${RECORDED_REASON}:${RECORDED_REASON}")
    AGREE+=("$ALERT_NUM $PKG $GHSA_ID ($RECORDED_REASON)") ;;
  "not_used:inaccurate" | "inaccurate:not_used")
    REFINE+=("$ALERT_NUM $PKG $GHSA_ID (was=$RECORDED_REASON now=$NEW_REASON — same action, different reason)") ;;
  *":open-issue")
    DRIFT+=("$ALERT_NUM $PKG $GHSA_ID (was=$RECORDED_REASON now=open-issue — skill would NO LONGER dismiss; consider reopening manually if applicable)") ;;
  *)
    OTHER+=("$ALERT_NUM $PKG $GHSA_ID (was=$RECORDED_REASON now=$NEW_REASON)") ;;
esac
```

End of run, print:

```
=== triage-security rerun-dismissed report for $REPO (Dependabot-only) ===
Alerts re-evaluated: $N_PROCESS
Agree (skill still endorses the dismissal): ${#AGREE[@]}
Refine (same action, different reason — informational): ${#REFINE[@]}
DRIFT (skill would no longer dismiss): ${#DRIFT[@]}
Other (verdict swap, e.g. not_used → inaccurate or vice versa): ${#OTHER[@]}

DRIFT — review these manually:
  ...
Other — review these manually:
  ...
```

**Never auto-reopen a dismissed alert** in this mode. A human dismissal is a human decision; the skill's job is to surface drift, not override the call. If `DRIFT` is non-empty, the operator reviews each entry and decides whether to manually reopen the alert via the GitHub UI or via `gh api -X PATCH ... -f state=open`.

Exit code in rerun mode: `0` if `DRIFT` is empty (skill agrees with all historical dismissals), `1` otherwise.

### 3.1 Dismiss a DEV-only alert

**`dismissed_comment` has a hard 280-character limit** on the Dependabot alerts API (`HTTP 422: Invalid property /dismissed_comment: Only 280 characters are allowed`). The wordy default below is ~330 chars and **will fail** without truncation. Build a terser default and cap defensively:

```bash
# Step 1 — open the closed audit-trail issue (see §3.1c). Symmetric with §3.1b:
# every dismissal — `not_used` or `inaccurate` — gets a closed audit issue,
# so all dismissals are searchable via the `security-audit` label.
DISMISSAL_REASON="not_used"
AUDIT_URL=$(create_audit_issue)
[[ -n "$AUDIT_URL" ]] || { echo "ERROR: audit issue creation failed for #$ALERT_NUM — abort dismissal"; SKIPPED+=("$ALERT_NUM:audit-create-error"); continue; }

# Step 2 — terse summary + URL pointer to the audit issue. The audit body
# carries the full Signal C evidence; this comment is just navigation.
DISMISS_COMMENT="\`$PKG\` test/dev-only (0 PROD imports). Full analysis: $AUDIT_URL"

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
  DISMISS_COMMENT="\`$PKG\` not imported (prod or test). Transitive via $REVERSE_DEP_ROOT. Full analysis: $AUDIT_URL"
fi
```

**Required**: `dismissed_reason` must be one of the GitHub-documented enum values: `fix_started`, `inaccurate`, `no_bandwidth`, `not_used`, `tolerable_risk`. This skill uses **two** of them, each with strict criteria:

- `not_used` — the package import path is not reachable from production code. Phase 2.4 Signal C decides this. The dismissal comment names the test/dev paths found.
- `inaccurate` — the package IS imported in production code, but the CVE's threat model preconditions are absent in this codebase's usage. Phase 2.5 decides this. The dismissal comment names which precondition is absent.

Do **not** use `tolerable_risk` — that's "the bug is real and reachable, but the impact is low enough that we accept it." It requires a human cost/benefit call; the skill never has the context to make it.

Do **not** use `fix_started` or `no_bandwidth` — those mean "we're working on it" / "we don't have time." Neither describes the skill's actual reasoning.

### 3.1b Dismiss a NOT-APPLICABLE alert (Phase 2.5 verdict, **high confidence only**)

For alerts where the package is imported in PROD but Phase 2.5.7 ruled the CVE's preconditions absent AND Phase 2.5.6 returned `high` confidence. Two paths into this branch:

- **cli-tool path** — archetype is `cli-tool` and `high` confidence (preconditions absent under direct call analysis).
- **framework-structural path** — archetype is `framework` / `scaffold`, `high` confidence, AND §2.5.6b structural-impossibility check passes all three conditions.

**Do not enter this branch on `moderate` / `low` confidence** OR **on framework/scaffold without §2.5.6b passing** — those cases must take the issue path (Phase 3.2) with the `needs-human-review` label.

Since §2.5.2 derives a per-advisory checklist that's almost always longer than the 280-char dismissed_comment limit, this branch **always opens a closed audit-trail issue first** (see §3.1c), then embeds the audit issue URL in the dismissed_comment. The dismissal alone isn't a complete audit trail — the closed audit issue is.

```bash
# Required pre-conditions to reach this branch:
[[ "$VERDICT" == "NOT-APPLICABLE" ]] || [[ "$VERDICT" == "NOT-APPLICABLE (structural)" ]] \
  || { echo "guard: only NOT-APPLICABLE / NOT-APPLICABLE (structural) reaches 3.1b"; continue; }
[[ "$CONFIDENCE" == "high" ]] \
  || { echo "guard: only high-confidence reaches 3.1b — route to 3.2 with needs-human-review"; continue; }
if [[ "$ARCHETYPE" == "framework" || "$ARCHETYPE" == "scaffold" ]]; then
  [[ "$STRUCTURAL_IMPOSSIBLE" == "true" ]] \
    || { echo "guard: framework/scaffold requires §2.5.6b pass to dismiss — route to 3.2"; continue; }
fi

# $FAILED_Q is set in §2.5.3 — e.g., "Q1 (no auth headers)" (now per-advisory, not CWE-class)
# $SYMBOL_TRACE is set in §2.5.4 — e.g., "grep `connection_from_url`=0"
# $STRUCTURAL_REASON is set in §2.5.6b when applicable — e.g., "no public API forwards to ProxyManager"
#
# Step 1 — open the closed audit-trail issue (see §3.1c). Required for the
# full per-advisory Q list, which doesn't fit in the 280-char dismissed_comment.
AUDIT_URL=$(create_audit_issue)   # §3.1c — returns the issue URL on stdout
[[ -n "$AUDIT_URL" ]] || { echo "ERROR: audit issue creation failed for #$ALERT_NUM — abort dismissal"; SKIPPED+=("$ALERT_NUM:audit-create-error"); continue; }

# Step 2 — dismissed_comment becomes a fixed pointer + one-line summary.
# Templates fit ~120 chars summary + 90 chars URL within the 280 cap.
if [[ "$ARCHETYPE" == "framework" || "$ARCHETYPE" == "scaffold" ]]; then
  DISMISS_COMMENT="\`$PKG\` CVE structurally unreachable ($ARCHETYPE, high-conf). Full analysis: $AUDIT_URL"
else
  DISMISS_COMMENT="\`$PKG\` CVE not applicable ($ARCHETYPE, high-conf). Full analysis: $AUDIT_URL"
fi

if [[ ${#DISMISS_COMMENT} -gt 280 ]]; then
  DISMISS_COMMENT="${DISMISS_COMMENT:0:277}..."
fi

# Step 3 — dismiss the alert.
gh api -X PATCH "repos/$REPO/dependabot/alerts/$ALERT_NUM" \
  -f state="dismissed" \
  -f dismissed_reason="inaccurate" \
  -f dismissed_comment="$DISMISS_COMMENT" \
  --jq '.state' \
  || { echo "ERROR: failed to dismiss alert #$ALERT_NUM (audit issue $AUDIT_URL was already created)"; SKIPPED+=("$ALERT_NUM:dismiss-api-error:$AUDIT_URL"); continue; }
```

Failure-mode note: if the dismissal fails after the audit issue was created, the audit issue exists as an orphan. Operator should either retry the dismissal or close the audit issue manually. The `SKIPPED` entry carries the audit URL so it can be cleaned up.

### 3.1c Open a closed audit-trail issue (every dismissal)

Long-form audit record for **every** dismissal — both `not_used` and `inaccurate`. Created closed (`gh issue create` then immediate `gh issue close`) so it doesn't appear in default "open issues" views but remains searchable by label (`security-audit`).

Why this exists: dismissals need an audit trail that's complete and uniformly discoverable. For `inaccurate`, §2.5.2's per-advisory Q list + §2.5.3's per-Q answers + §2.5.4's symbol trace + §2.5.6b's structural-impossibility result together produce 500–2000 chars — far beyond the 280-char `dismissed_comment` cap. For `not_used`, the Signal C evidence usually fits in 280 but the symmetric design ensures `label:security-audit` returns *every* dismissal regardless of reason, which is operationally simpler than two-path search.

The audit body adapts based on `$DISMISSAL_REASON`:

```bash
# called as: AUDIT_URL=$(create_audit_issue)
create_audit_issue() {
  local audit_title audit_body audit_url body_analysis
  audit_title="[Security-audit][closed] ${PKG} #${ALERT_NUM} (${GHSA_ID}) — ${DISMISSAL_REASON}"
  # 70-char title budget — truncate package + GHSA if needed.
  if [[ ${#audit_title} -gt 70 ]]; then
    audit_title="${audit_title:0:67}..."
  fi

  # Title — varies by source, since code-scanning alerts don't have GHSA IDs.
  if [[ "$SOURCE_OF_THIS_ALERT" == "code-scanning" ]]; then
    audit_title="[Security-audit][closed] ${RULE_ID} #${ALERT_NUM} — ${DISMISSAL_REASON}"
  else
    audit_title="[Security-audit][closed] ${PKG} #${ALERT_NUM} (${GHSA_ID}) — ${DISMISSAL_REASON}"
  fi
  [[ ${#audit_title} -gt 70 ]] && audit_title="${audit_title:0:67}..."

  # The analysis body has FOUR cases — per dismissal reason. For not_used and
  # used-in-tests, §2.5 didn't run; the body just records the path-based evidence.
  # For inaccurate and false-positive, the full §2.5 stack ran and the body
  # carries the long-form Q-checklist analysis.
  case "$DISMISSAL_REASON" in
    not_used)
      body_analysis=$(cat <<EOF
## Classification: DEV-only (Dependabot Signal C)

The package is reachable only from test / dev / CI paths. Phase 2.5 (exploit-surface analysis) was NOT run — the verdict is mechanical: 0 prod imports = not exploitable in prod.

**Signal C scan results:**
- PROD imports found: 0 (across \`${PROD_DIRS[*]}\`)
- TEST imports found at: ${TEST_HIT_FILES:-none (pure transitive)}
- Transitive root: ${REVERSE_DEP_ROOT:-N/A — direct dev/test pin}
- pyproject.toml group: ${PYPROJECT_GROUP:-unknown}

**Why this is a safe dismissal:** the package's vulnerable code paths are not reachable from any code that ships in the production install footprint.

**Re-evaluate if:** any code under \`${PROD_DIRS[*]}\` adds an \`import ${PKG}\` line, or the package is moved from a dev/test group to the production dependency list.
EOF
)
      ;;
    "used in tests")
      body_analysis=$(cat <<EOF
## Classification: TEST-ONLY (code-scanning Signal F)

The flagged file is under a test path. Phase 2.5 was NOT run — the bug, even if real, doesn't ship to production.

**Signal F scan result:**
- Flagged file: \`${ALERT_FILE}\`:${ALERT_LINE}
- Matched against TEST_DIRS / PKG_TEST_DIRS — file is in a test tree.
- Rule: \`${RULE_ID}\` (severity: ${RULE_SEVERITY})

**Why this is a safe dismissal:** the flagged code runs only at test/CI time; it does not execute in production deployments.

**Re-evaluate if:** the file is moved out of the test tree into a prod path, or the test scaffolding is repurposed as a runtime helper.
EOF
)
      ;;
    inaccurate|"false positive")
      body_analysis=$(cat <<EOF
## Advisory / rule summary (§2.5.1)

${ADVISORY_SUMMARY}

## Derived precondition checklist (§2.5.2)

The Qs below are derived per-advisory from the GHSA description / code-scanning rule (and optionally §2.5.1b MITRE supplement), not from a static table. Each Q is answered against this specific codebase in §2.5.3.

${CWE_CHECKLIST_ANSWERS}

## Vulnerable-symbol trace (§2.5.4)

${SYMBOL_TRACE_RESULT}

## Structural-impossibility check (§2.5.6b, Dependabot framework/scaffold only)

${STRUCTURAL_CHECK_RESULT:-N/A — code-scanning alert OR not a framework/scaffold archetype}

## Code-scanning Signal H (function privacy, code-scanning only)

${SIGNAL_H_RESULT:-N/A — Dependabot alert}

## Decisive reasoning

${APPLICABILITY_REASONING}
EOF
)
      ;;
    *)
      body_analysis="(unknown dismissal reason: $DISMISSAL_REASON — please review)"
      ;;
  esac

  # Header — adapts to source. Dependabot fields vs code-scanning fields.
  if [[ "$SOURCE_OF_THIS_ALERT" == "code-scanning" ]]; then
    audit_body=$(cat <<EOF
**Dismissed code-scanning alert:** #${ALERT_NUM} — ${ALERT_URL}
**Tool:** ${TOOL:-unknown}
**Rule ID:** \`${RULE_ID}\`
**Rule severity:** ${RULE_SEVERITY}
**CWE(s):** ${CWE_IDS:-none}
**Flagged file:** \`${ALERT_FILE}\`:${ALERT_LINE}
**Archetype:** ${ARCHETYPE}
**Skill confidence:** ${CONFIDENCE:-n/a}
**Dismissal reason:** \`${DISMISSAL_REASON}\` (this audit issue is auto-closed)

${body_analysis}

## How to challenge this dismissal

If you (the maintainer) judge any answer or evidence wrong:
1. Reopen the code-scanning alert via the GitHub Security tab.
2. Reopen this audit issue and comment with the corrected analysis + evidence.
3. If the corrected analysis shows the finding is applicable, fix the flagged code; track in a new issue if needed.

Skill version / commit: ${SKILL_VERSION:-unknown} (see commit log of the triage-security skill).
EOF
)
  else
    audit_body=$(cat <<EOF
**Dismissed Dependabot alert:** #${ALERT_NUM} — ${ALERT_URL}
**Package:** \`${PKG}\` (pip)
**Severity:** ${SEVERITY}
**GHSA / CVE:** ${GHSA_ID} / ${CVE_ID}
**CWE(s):** ${CWE_IDS}
**Vulnerable range:** \`${VULN_RANGE}\` — first patched in \`${FIRST_PATCHED}\`
**Archetype:** ${ARCHETYPE}
**Skill confidence:** ${CONFIDENCE:-n/a (not_used path)}
**Dismissal reason:** \`${DISMISSAL_REASON}\` (this audit issue is auto-closed)

${body_analysis}

## How to challenge this dismissal

If you (the maintainer) judge any answer or evidence wrong:
1. Reopen the Dependabot alert via the GitHub Security tab.
2. Reopen this audit issue and comment with the corrected analysis + evidence.
3. If the corrected analysis shows the CVE is applicable, treat as a normal upgrade.

Skill version / commit: ${SKILL_VERSION:-unknown} (see commit log of the triage-security skill).
EOF
)
  fi

  audit_url=$(gh issue create --repo "$REPO" \
    --title "$audit_title" \
    --label "security,dependabot,triage-security,security-audit" \
    --body "$audit_body") || return 1

  # Close immediately — the audit issue is a permanent record, not a TODO.
  gh issue close "$audit_url" --repo "$REPO" --comment "Auto-closed — see alert ${ALERT_URL} for the live state." >/dev/null 2>&1 || true

  echo "$audit_url"
}
```

The `security-audit` label must be created idempotently up front (alongside the existing `security` / `dependabot` / `triage-security` / `needs-human-review` labels in §3.2):

```bash
gh label create security-audit  --color C2E0C6 --description "Permanent audit record for a triage-security dismissal (auto-closed)" --repo "$REPO" 2>/dev/null || true
```

**All four dismissal paths** (§3.1 not_used / §3.1b inaccurate / §3.1d used-in-tests / §3.1e false-positive) call `create_audit_issue`. The `dismissed_comment` ends with `Full analysis: ${AUDIT_URL}` for each. Net effect: `gh issue list --repo "$REPO" --state closed --label security-audit` returns every dismissal the skill has ever performed across both Dependabot and code-scanning sources.

### 3.1d Dismiss a code-scanning alert as `used in tests`

For code-scanning alerts where Signal F (§2.cs.1) found the flagged file under `TEST_DIRS` / `PKG_TEST_DIRS`. The flagged bug, even if real, doesn't ship to production. Symmetric with Dependabot's §3.1 (`not_used`).

```bash
DISMISSAL_REASON="used in tests"
AUDIT_URL=$(create_audit_issue)
[[ -n "$AUDIT_URL" ]] || { echo "ERROR: audit issue creation failed for code-scanning #$ALERT_NUM — abort dismissal"; SKIPPED+=("$ALERT_NUM:audit-create-error"); continue; }

DISMISS_COMMENT="\`${RULE_ID}\` in test path \`${ALERT_FILE}\`:${ALERT_LINE} — not in prod runtime. Full analysis: $AUDIT_URL"
[[ ${#DISMISS_COMMENT} -gt 280 ]] && DISMISS_COMMENT="${DISMISS_COMMENT:0:277}..."

gh api -X PATCH "repos/$REPO/code-scanning/alerts/$ALERT_NUM" \
  -f state="dismissed" \
  -f dismissed_reason="used in tests" \
  -f dismissed_comment="$DISMISS_COMMENT" \
  --jq '.state' \
  || { echo "ERROR: failed to dismiss code-scanning alert #$ALERT_NUM"; SKIPPED+=("$ALERT_NUM:dismiss-api-error:$AUDIT_URL"); continue; }
```

### 3.1e Dismiss a code-scanning alert as `false positive` (high confidence only)

For code-scanning alerts where:
1. Signal F (§2.cs.1) classified as PROD (in prod dirs)
2. Signal G (§2.cs.2) did NOT match `RULE_HUMAN_REVIEW_PATTERNS`
3. Archetype is `cli-tool`
4. §2.5 preconditions all `absent` or `reachable` (no `unknown`)
5. §2.5.6 returned `high` confidence

`framework` / `scaffold` / `service` archetypes never reach this path — code-scanning flags bugs in our own code, so "consumer might hit this" is decisive for framework. The action matrix routes those to issue + needs-human-review.

```bash
# Guards
[[ "$VERDICT" == "FALSE-POSITIVE" ]] || { echo "guard: only FALSE-POSITIVE reaches 3.1e"; continue; }
[[ "$CONFIDENCE" == "high" ]] || { echo "guard: 3.1e requires high confidence"; continue; }
[[ "$ARCHETYPE" == "cli-tool" ]] || { echo "guard: 3.1e is cli-tool-only; framework/service routes to 3.2"; continue; }
[[ "$FORCE_REVIEW" != "true" ]] || { echo "guard: rule in RULE_HUMAN_REVIEW_PATTERNS — must route to 3.2"; continue; }

DISMISSAL_REASON="false positive"
AUDIT_URL=$(create_audit_issue)
[[ -n "$AUDIT_URL" ]] || { echo "ERROR: audit issue creation failed for #$ALERT_NUM — abort dismissal"; SKIPPED+=("$ALERT_NUM:audit-create-error"); continue; }

# $FAILED_Q from §2.5.3; $SIGNAL_H_RESULT from §2.cs.3 (private/public/module-level)
DISMISS_COMMENT="\`${RULE_ID}\` in \`${ALERT_FILE}\`:${ALERT_LINE} not applicable (${ARCHETYPE}, high-conf): ${FAILED_Q}; function=${SIGNAL_H_RESULT}. Full analysis: $AUDIT_URL"
[[ ${#DISMISS_COMMENT} -gt 280 ]] && DISMISS_COMMENT="${DISMISS_COMMENT:0:277}..."

gh api -X PATCH "repos/$REPO/code-scanning/alerts/$ALERT_NUM" \
  -f state="dismissed" \
  -f dismissed_reason="false positive" \
  -f dismissed_comment="$DISMISS_COMMENT" \
  --jq '.state' \
  || { echo "ERROR: failed to dismiss code-scanning alert #$ALERT_NUM"; SKIPPED+=("$ALERT_NUM:dismiss-api-error:$AUDIT_URL"); continue; }
```

**Never** auto-set `won't fix` — that's the maintainer's "we accept the risk" call (analog of Dependabot's `tolerable_risk`).

### 3.2 Open a tracking issue for an APPLICABLE alert (both sources)

Before opening, **dedupe**: search for an existing open issue. The dedupe key differs by source:
- Dependabot: GHSA ID (unique per CVE).
- Code-scanning: combination of `rule.id` + `file:line` (uniquely identifies the finding).

```bash
if [[ "$SOURCE_OF_THIS_ALERT" == "code-scanning" ]]; then
  # Dedupe by rule.id + file:line; both appear in the issue body
  DEDUPE_KEY="${RULE_ID} ${ALERT_FILE}:${ALERT_LINE}"
else
  DEDUPE_KEY="$GHSA_ID"
fi
EXISTING=$(gh issue list --repo "$REPO" --state open --search "\"$DEDUPE_KEY\" in:title,body" --json number,url --jq '.[0].url // ""')
if [[ -n "$EXISTING" ]]; then
  echo "skip: existing issue for $DEDUPE_KEY at $EXISTING"
  SKIPPED+=("$ALERT_NUM:existing-issue:$EXISTING")
  continue
fi
```

Issue title format (under 70 chars):
- Dependabot: `[Security][<severity>] <package>: <short summary>`
- Code-scanning: `[Security][<severity>] <rule.id>: <file>:<line>`

The Dependabot title's GHSA ID lives in the body (dedupe match still works because the GHSA ID appears in the body). For code-scanning, the rule + file:line is enough to identify the finding; severity goes in the title.

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
gh label create code-scanning         --color 0E8A16 --description "Code-scanning (CodeQL / SnykCode / etc.) reported" --repo "$REPO" 2>/dev/null || true
gh label create triage-security     --color 5319E7 --description "Opened by triage-security skill" --repo "$REPO" 2>/dev/null || true
gh label create needs-human-review    --color FBCA04 --description "Skill confidence below threshold — maintainer call required" --repo "$REPO" 2>/dev/null || true
gh label create security-audit        --color C2E0C6 --description "Permanent audit record for a triage-security dismissal (auto-closed)" --repo "$REPO" 2>/dev/null || true
```

Issue body template (use a heredoc; per-source branches inside).

For **Dependabot** PROD-applicable / needs-human-review:

```bash
LABELS="security,dependabot,triage-security"
[[ "$NEEDS_REVIEW" == "true" ]] && LABELS="$LABELS,needs-human-review"

ISSUE_URL=$(gh issue create --repo "$REPO" \
  --title "$TITLE" \
  --label "$LABELS" \
  --body "$(cat <<EOF
## Dependabot alert

- Alert: $ALERT_URL
- Package: \`$PKG\` (pip)
- Severity: **$SEVERITY**
- GHSA: $GHSA_ID
- CVE: $CVE_ID
- CWE(s): $CWE_IDS
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
**Skill verdict:** $VERDICT
**Skill confidence:** $CONFIDENCE

**CWE checklist (§2.5.2):**
$CWE_CHECKLIST_ANSWERS

**Vulnerable-symbol trace (§2.5.4):**
$SYMBOL_TRACE_RESULT

**Structural-impossibility check (§2.5.6b, framework/scaffold only):**
$STRUCTURAL_CHECK_RESULT

**Codebase's usage pattern at the import sites:**
$USAGE_PATTERN_NOTES

**Reasoning:** $APPLICABILITY_REASONING

If this issue carries the \`needs-human-review\` label, the skill's confidence was below the threshold for autonomous dismissal. Maintainer review: either (a) confirm the bump should go ahead, or (b) dismiss the linked Dependabot alert with reason \`inaccurate\` and a comment naming the missing precondition.

## Suggested fix

Upgrade the pin in \`pyproject.toml\` to \`>= $FIRST_PATCHED\` (or the next minor/major if a closer pin exists). If the package is transitive, identify the direct dep via \`uv tree --package $PKG --invert\` (or \`poetry show --why $PKG\`) and bump that. If the package is owned by the open-autonomy / open-aea framework, the bump should go through \`/bump-versions\`.

## Why this issue exists

Triaged by the \`triage-security\` skill. The Dependabot alert remains open as the source of truth; this issue tracks the in-repo work to fix it.
EOF
)")
```

For **code-scanning** APPLICABLE / needs-human-review (force-review rules always land here):

```bash
LABELS="security,code-scanning,triage-security"
[[ "$NEEDS_REVIEW" == "true" || "$FORCE_REVIEW" == "true" ]] && LABELS="$LABELS,needs-human-review"

# Pull the flagged code snippet for the body (5 lines of context around the alert line).
CONTEXT_START=$((ALERT_LINE - 2)); [[ $CONTEXT_START -lt 1 ]] && CONTEXT_START=1
CONTEXT_END=$((ALERT_LINE + 2))
SNIPPET=$(sed -n "${CONTEXT_START},${CONTEXT_END}p" "$ALERT_FILE" 2>/dev/null | head -10)

ISSUE_URL=$(gh issue create --repo "$REPO" \
  --title "$TITLE" \
  --label "$LABELS" \
  --body "$(cat <<EOF
## Code-scanning alert

- Alert: $ALERT_URL
- Tool: $TOOL
- Rule ID: \`$RULE_ID\`
- Severity: **$RULE_SEVERITY**
- CWE(s): $CWE_IDS
- File: \`$ALERT_FILE\`:$ALERT_LINE

## Flagged code

\`\`\`python
$SNIPPET
\`\`\`

**Tool message:** $ADVISORY_SUMMARY

## Rule description

$ADVISORY_DESCRIPTION

## Exploit-surface analysis

**Repo archetype:** $ARCHETYPE
**Skill verdict:** $VERDICT
**Skill confidence:** $CONFIDENCE
**Force-review (RULE_HUMAN_REVIEW_PATTERNS match):** ${FORCE_REVIEW:-no}
**Signal H (function privacy):** ${SIGNAL_H_RESULT:-n/a}

**CWE checklist (§2.5.2):**
$CWE_CHECKLIST_ANSWERS

**Reasoning:** $APPLICABILITY_REASONING

If this issue carries the \`needs-human-review\` label, the skill could not autonomously dismiss. Maintainer review: either (a) fix the flagged code, then close this issue; or (b) dismiss the linked code-scanning alert with the appropriate reason (\`false positive\` / \`used in tests\` / \`won't fix\`) and close this issue with a comment naming the reason.

**Force-review rule classes** (cert/TLS bypass, injection, hardcoded secrets non-test, auth/authz, RCE/deserialization, path traversal) ALWAYS route here — the skill never auto-dismisses them, even when its analysis says "looks fine."

## Why this issue exists

Triaged by the \`triage-security\` skill. The code-scanning alert remains open as the source of truth; this issue tracks the in-repo work to fix or formally dismiss it.
EOF
)")
```

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

**This phase runs only in live mode.** Under `--rerun-dismissed`, Phase 3.0's verdict-drift block is the entire summary — skip Phase 4 there.

Bucket skips into two categories so the exit code reflects the actual failure surface:

| Bucket | When | Exit-code impact |
| ------ | ---- | ---------------- |
| `non-pip-ecosystem` | Alert's `ecosystem != "pip"` (Docker, npm, GitHub Actions). Expected — the skill scope is pip-only. | None. These are permanent state, not a per-run signal. |
| `unclassifiable` | Pip alert that fell through every signal (`scope=unknown`, no imports, no pyproject group, no transitive root). Genuinely "skill doesn't know enough". | Exit 1 — this is the real "incomplete run" signal CI/cron should react to. |

A naive `exit 1 if any skip` rule would fire on every run for any repo carrying even one permanent Docker/npm alert, defeating the purpose for cron wrappers.

End with a single stdout block summarising the run:

```
=== triage-security summary for $REPO ===
Source(s):          $SOURCE                       # dependabot | code-scanning | both
Alerts seen:        $N_ALERTS (dependabot=$N_DB, code-scanning=$N_CS)
Processed:          $N_PROCESS                    # respects --limit

— Dependabot —
Dismissed (DEV, not_used):                    $N_DISMISSED_DEV
Dismissed (PROD-not-applic, inaccurate):      $N_DISMISSED_INACCURATE
Issue opened (PROD-applicable, high-conf):    $N_OPENED_APPLICABLE_DB
Issue opened (needs-human-review):            $N_OPENED_REVIEW_DB

— Code Scanning —
Dismissed (TEST-ONLY, used in tests):         $N_DISMISSED_CS_TEST
Dismissed (false positive, high-conf):        $N_DISMISSED_CS_FP
Issue opened (PROD-applicable):               $N_OPENED_APPLICABLE_CS
Issue opened (needs-human-review):            $N_OPENED_REVIEW_CS
  — incl. force-review (RULE_HUMAN_REVIEW_PATTERNS match): $N_FORCE_REVIEW

— Shared —
Audit-trail issues opened (closed):  $N_AUDIT_ISSUES   # 1 per dismissal across both sources
Skipped (non-pip):              $N_SKIPPED_ECOSYSTEM   # informational, no exit-code impact
Skipped (stale-alert):          $N_SKIPPED_STALE       # code-scanning alert against deleted file
Skipped (unclassifiable):       $N_SKIPPED_UNCLASS     # exits 1 if > 0

Dismissed Dependabot alerts:
  #123 PyYAML       GHSA-... (not_used)
  #124 urllib3      GHSA-... (inaccurate, high-conf)
  ...

Dismissed Code-scanning alerts:
  #45  python/reDOS         tests/test_url.py:88 (used in tests)
  #51  python/HardcodedNon… autonomy/util.py:142 (false positive, cli-tool high-conf)
  ...

Opened issues:
  #456 …/issues/456  GHSA-... cryptography     (high-conf applicable, Dependabot)
  #457 …/issues/457  GHSA-... requests         (moderate-conf, needs-human-review, Dependabot)
  #460 …/issues/460  python/SSLVerificationBy… (force-review, Code Scanning)
  ...

Skipped — non-pip ecosystem (informational):
  #654 GHSA-... docker-image (ecosystem=docker)
  ...

Skipped — stale code-scanning alerts (file deleted):
  #88  python/unused-import tests/legacy/old.py (file no longer exists)
  ...

Skipped — unclassifiable (review manually):
  #789 GHSA-... obscure-pkg — no imports found, scope=unknown
  #92  python/SomeRule scripts/odd.py (outside both PROD_DIRS and TEST_DIRS)
  ...
```

The `needs-human-review` bucket is the primary calibration signal: if it grows over time, either the §2.5.2 CWE checklist or the §0.2 `RULE_HUMAN_REVIEW_PATTERNS` list (for code-scanning) needs refinement.

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
# macOS bash 3.2 compat — `mapfile` is bash 4+, use `while read` instead.
PKG_TEST_DIRS=()
while IFS= read -r _d; do
  PKG_TEST_DIRS+=("$_d")
done < <(find packages plugins -type d -name tests 2>/dev/null)
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

1. **Only act on `state=open` alerts.** Don't poke at already-dismissed alerts (except in `--rerun-dismissed` Dependabot-only read-only mode).
2. **Skip non-pip Dependabot ecosystems.** GitHub Actions / Docker / npm alerts can appear (e.g. `.github/workflows/*.yml` action pins) — flag them for manual review. The skill is Python-only by current scope.
3. **Conservative default: when uncertain, open an issue, don't dismiss.** A false-positive issue costs one `gh issue close` command; a false-negative dismissal costs a quietly-shipped vuln. The §2.5.6 confidence tier, §2.5.6b structural-impossibility check, and §0.2 `RULE_HUMAN_REVIEW_PATTERNS` list together formalize this — only `high` confidence + (cli-tool / framework-with-§2.5.6b-passes / file-in-tests/) dismisses autonomously, and code-scanning alerts matching `RULE_HUMAN_REVIEW_PATTERNS` always route to human review regardless of confidence.
4. **Four dismissal reasons, strict criteria.** All share a uniform audit-trail requirement.
   - **Dependabot `not_used`** — Phase 2.4 Signal C proved the package is reachable only from test/dev paths. Comment names the test/dev files. No confidence tier required.
   - **Dependabot `inaccurate`** — Phase 2.5 proved CVE preconditions absent **AND Phase 2.5.6 returned `high` confidence**, AND either (a) archetype is `cli-tool`, OR (b) archetype is `framework` / `scaffold` AND §2.5.6b structural-impossibility passes all three conditions.
   - **Code-scanning `used in tests`** — Signal F (§2.cs.1) placed the flagged file under `TEST_DIRS` / `PKG_TEST_DIRS`. No §2.5 needed.
   - **Code-scanning `false positive`** — Phase 2.5 ruled preconditions absent **AND Phase 2.5.6 returned `high` confidence**, AND archetype is `cli-tool`, AND rule does NOT match `RULE_HUMAN_REVIEW_PATTERNS`, AND Signal G (force-review) did not fire. Framework / scaffold / service archetypes never reach this path — code-scanning alerts on consumer-facing or service code always route to human review.

   **Required side-effect (ALL FOUR reasons): open a closed audit-trail issue (§3.1c) BEFORE the dismissal, and embed the audit URL in the dismissed_comment.** The audit issue body adapts to the reason. The 280-char comment alone is never a complete audit trail; the closed audit issue is. Uniform audit-issue creation means `gh issue list --label security-audit` returns every dismissal regardless of source or reason.

   **Never use `tolerable_risk` (Dependabot) or `won't fix` (code-scanning) or `fix_started` / `no_bandwidth`.** Those are human risk-accept calls — the skill never has the context to make them.
5. **`RULE_HUMAN_REVIEW_PATTERNS` (code-scanning) is absolute.** When a code-scanning alert's `rule.id` matches a pattern in the list (§0.2), the skill bypasses §2.5 entirely and opens an issue with `needs-human-review`. **Never auto-dismiss this rule class**, regardless of how clean the confidence-tier analysis looks. These are bug classes where false-negative dismissal cost is too high (cert/TLS bypass, injection in prod, hardcoded secrets non-test, auth/authz, RCE/deserialization, path traversal).
6. **Dedupe before opening.** Search existing open issues by GHSA ID (Dependabot) or rule.id + file:line (code-scanning); never spam duplicates on repeat runs.
7. **Don't dismiss with no evidence.** Skip + log if neither prod nor test signals are conclusive.
8. **Print stderr lines for skips.** The summary table is for the actor; the per-alert skip lines are for the human reviewer paginating through stderr.
9. **Exit non-zero only if an alert was skipped as `unclassifiable`.** `non-pip-ecosystem` and `stale-alert` skips are expected and informational — exiting on them would fire on every run, breaking cron wrappers.
10. **Rerun-dismissed mode is Dependabot-only AND strictly read-only.** Under `--rerun-dismissed`, the skill MAY NOT call `gh api -X PATCH` or `gh issue create`. Its only output is the verdict-drift report to stdout. Code-scanning dismissals are never re-evaluated (final-call assumption — see Phase 1 argv validation).

---

## Files / state mutated

| Surface | What changes |
| ------- | ------------ |
| (rerun-dismissed mode, Dependabot-only) | Nothing — read-only verdict-drift report to stdout |
| **Dependabot** alerts — DEV-only path (Signal C) | `state=dismissed`; `dismissed_reason=not_used`; comment carries one-line summary + audit issue URL |
| **Dependabot** alerts — PROD-but-not-applicable, cli-tool/framework-with-§2.5.6b + high confidence | `state=dismissed`; `dismissed_reason=inaccurate`; comment carries one-line summary + audit issue URL |
| **Code-scanning** alerts — file under TEST_DIRS / PKG_TEST_DIRS (Signal F) | `state=dismissed`; `dismissed_reason=used in tests`; comment carries file:line + audit issue URL |
| **Code-scanning** alerts — false positive, cli-tool + high confidence + rule NOT in `RULE_HUMAN_REVIEW_PATTERNS` | `state=dismissed`; `dismissed_reason=false positive`; comment carries failing Q + Signal H result + audit issue URL |
| Closed audit-trail issues — one per dismissal across both sources | New issues opened **and immediately closed** with title `[Security-audit][closed] …`, labels `security,dependabot,triage-security,security-audit`. Body adapts by reason (Signal C / Signal F / full §2.5). Permanent record; searchable via `gh issue list --state closed --label security-audit`. |
| Repo issues — Dependabot PROD-applicable | New issue, title `[Security][<sev>] <pkg>: <summary>`, labels `security,dependabot,triage-security`, body carries exploit-surface analysis + suggested fix |
| Repo issues — Code-scanning APPLICABLE / force-review | New issue, title `[Security][<sev>] <rule.id>: <file>:<line>`, labels `security,code-scanning,triage-security`, body carries flagged-code snippet + rule description + Signal H + analysis |
| Repo issues — PROD-not-applicable but autonomous-dismissal gate not met (moderate/low confidence, framework/scaffold with §2.5.6b failing, OR code-scanning RULE_HUMAN_REVIEW_PATTERNS match) | Same as above, **additionally labeled `needs-human-review`**. Underlying alert NOT dismissed — the maintainer makes the final call. |
| Repo issues (existing) | Skipped via dedupe (no edit) |
| Labels | First-run idempotent creation of `security`, `dependabot`, `code-scanning`, `triage-security`, `needs-human-review`, `security-audit` |
| Working tree | Nothing — the skill only mutates GitHub state, not files |

---

## When NOT to run this skill

- Neither Dependabot nor code-scanning is enabled on the repo — exits cleanly at Phase 0.
- You're partway through `/bump-versions` and `pyproject.toml` is in flight — the Dependabot classification reads pyproject as source of truth; mid-bump state could misclassify. Finish the bump first, then triage.
- The repo has Dependabot ecosystems beyond pip (Docker, npm, GitHub Actions) that you want triaged — current skill scope is pip-only on the Dependabot side. Code scanning is tool-agnostic (works for any tool that emits to `/code-scanning/alerts`).
