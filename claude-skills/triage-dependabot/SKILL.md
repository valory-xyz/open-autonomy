---
name: triage-dependabot
description: Triage open Dependabot security alerts on the current GitHub repo. For each alert, decide whether the vulnerable dependency is reachable from production code or only test/dev/CI code. Production-relevant alerts get a tracking issue opened (alert stays open); test-only alerts get dismissed with reason `not_used`. Repo-agnostic — works across the Valory fleet.
argument-hint: "[--limit N]  # optional cap on alerts processed per run"
disable-model-invocation: true
---

# Triage Dependabot alerts (prod vs test, then act)

Walk every open Dependabot security alert on the current repo. Classify the vulnerable dependency by whether it is **reachable from production code** or **only from tests / dev tooling / CI**. Then act in one pass:

| Classification | Action |
| -------------- | ------ |
| **Production** | Leave Dependabot alert open. Open a new GitHub issue on the repo that references the alert, names the CVE / GHSA / severity, lists the production paths that pull in the vulnerable package, and suggests the upgrade pin. |
| **Test / dev / CI only** | Dismiss the Dependabot alert via API with `state=dismissed`, `dismissed_reason=not_used`, and a `dismissed_comment` naming the test/dev paths it was found in. No repo issue is opened. |
| **Unclassifiable** | Skip. Print a line to stderr so the operator can review manually. **Never** auto-dismiss without evidence. |

Conservative default: **when uncertain, treat as production.** A false-negative dismissal hides a real vulnerability; a false-positive issue is cheap to close.

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

---

## Phase 1 — Fetch open Dependabot alerts

```bash
TMP=$(mktemp -d)
set -euo pipefail

gh api "repos/$REPO/dependabot/alerts?state=open&per_page=100" --paginate \
  > "$TMP/alerts.json" \
  || { echo "ERROR: failed to list Dependabot alerts for $REPO"; exit 1; }

# Sanity: must be a non-null JSON array
jq -e 'type == "array"' "$TMP/alerts.json" > /dev/null \
  || { echo "ERROR: alerts response is not a JSON array — likely API error or scope problem"; cat "$TMP/alerts.json" | head -20; exit 1; }

N_ALERTS=$(jq 'length' "$TMP/alerts.json")
echo "found $N_ALERTS open alerts on $REPO"
```

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

Production paths and test paths vary by repo. Compute per-repo:

```bash
# Production paths — top-level Python source dirs that ship in the wheel/sdist
PROD_DIRS=$(for d in autonomy packages agent; do [[ -d "$d" ]] && echo "$d"; done | tr '\n' ' ')

# Test paths — top-level test dirs PLUS in-package `tests/` subdirs that aren't shipped logic
TEST_DIRS="tests scripts .github"
PKG_TEST_DIRS=$(find packages -type d -name tests 2>/dev/null | tr '\n' ' ' || true)

echo "PROD_DIRS=$PROD_DIRS"
echo "TEST_DIRS=$TEST_DIRS"
echo "PKG_TEST_DIRS=$PKG_TEST_DIRS"
```

**Important nuance**: under `packages/<author>/skills/<skill_name>/`, the skill's own production code (`behaviours.py`, `rounds.py`, `models.py`, `handlers.py`) is production; its sibling `tests/` subdir is not. Treat per-skill `tests/` dirs as test paths even though they live under `packages/`.

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
try:
    files = im.files(pkg) or []
    top_modules = sorted({
        str(f).split("/")[0].removesuffix(".py")
        for f in files
        if str(f).endswith((".py", "/__init__.py")) and "/" in str(f) and not str(f).startswith(".")
    })
except im.PackageNotFoundError:
    # Fallback: try the distribution name itself, common case
    top_modules = [pkg.replace("-", "_")]
```

If the package isn't installed (deep transitive, never landed in the venv), fall back to the conservative substitution `pkg.replace("-", "_")` and grep both forms.

Step 2: grep each top module under prod paths and test paths:

```bash
PROD_HITS=$(grep -rlnE "^(import|from)[[:space:]]+($MODULE)([[:space:]]|\.|$)" \
  $PROD_DIRS --include="*.py" 2>/dev/null | wc -l | tr -d ' ')

TEST_HITS=$(grep -rlnE "^(import|from)[[:space:]]+($MODULE)([[:space:]]|\.|$)" \
  $TEST_DIRS $PKG_TEST_DIRS --include="*.py" 2>/dev/null | wc -l | tr -d ' ')
```

The `^(import|from)\s+<mod>([\s.]|$)` anchor is deliberate: it matches `import foo`, `from foo import …`, `from foo.bar import …`, but **not** `# import foo` (comment) or `from foobar import …` (different package).

Step 3: classify.

- `PROD_HITS > 0` → **PROD**, regardless of Signal A/B.
- `PROD_HITS == 0` AND `TEST_HITS > 0` → **DEV** (only reachable from tests/CI).
- `PROD_HITS == 0` AND `TEST_HITS == 0` AND `dependency.scope == "development"` → **DEV** (declared dev, no imports anywhere — pin is unused but still scoped dev).
- `PROD_HITS == 0` AND `TEST_HITS == 0` AND `dependency.scope == "runtime"` → **PROD** (declared prod, even if currently unimported — better to fix the dep than the imports).
- `PROD_HITS == 0` AND `TEST_HITS == 0` AND `scope == "unknown"` → **UNCLASSIFIABLE** (transitive of an unimported dep; skip and flag for human review).

### 2.5 Transitive deps — reverse-resolve the chain

For transitive deps (`scope == "unknown"` or no pin in pyproject.toml), figure out which **direct** deps pull the vulnerable package in:

```bash
# uv repos
uv tree --package "$PKG" --invert 2>/dev/null

# Poetry repos
poetry show -t --tree 2>/dev/null | grep -B1 "$PKG"

# Fallback: parse uv.lock / poetry.lock directly for `dependencies` of each root that resolves to PKG
```

If **every** reverse-dep root is a dev/test group root, mark **DEV**. If **any** reverse-dep root is in `[project] dependencies` (prod), mark **PROD**. This is the right call even if production code itself never does `import <transitive>` — the transitive is in the production install footprint and exploitable at runtime.

---

## Phase 3 — Act on the classifications

For every alert, take exactly one action: **dismiss**, **open issue**, or **skip**. Build a per-alert audit record so the Phase 4 summary is honest about what happened.

### 3.1 Dismiss a DEV-only alert

```bash
DISMISS_COMMENT="Triaged automatically: package \`$PKG\` is only reachable from non-production code. Test/dev locations found: $TEST_HIT_FILES. Production scan (PROD_DIRS=$PROD_DIRS) returned zero imports. Dismissing as \`not_used\` from production. Re-evaluate if production code starts importing \`$PKG\`."

gh api -X PATCH "repos/$REPO/dependabot/alerts/$ALERT_NUM" \
  -f state="dismissed" \
  -f dismissed_reason="not_used" \
  -f dismissed_comment="$DISMISS_COMMENT" \
  --jq '.state' \
  || { echo "ERROR: failed to dismiss alert #$ALERT_NUM"; SKIPPED+=("$ALERT_NUM:dismiss-api-error"); continue; }
```

**Required**: `dismissed_reason` must be one of the GitHub-documented enum values: `fix_started`, `inaccurate`, `no_bandwidth`, `not_used`, `tolerable_risk`. This skill uses `not_used` exclusively — it's the only one that means "the vulnerable code path is not reachable from this project's production surface", which is the only thing the skill verifies.

Do **not** use `tolerable_risk` — that's an explicit accept-the-risk decision and requires a human judgment call about exploit difficulty / impact.

### 3.2 Open a tracking issue for a PROD alert

Before opening, **dedupe**: search for an existing open issue tagged with the same GHSA ID, to avoid spam on repeat runs.

```bash
EXISTING=$(gh issue list --repo "$REPO" --state open --search "$GHSA_ID in:title,body" --json number,url --jq '.[0].url // ""')
if [[ -n "$EXISTING" ]]; then
  echo "skip: existing issue for $GHSA_ID at $EXISTING"
  SKIPPED+=("$ALERT_NUM:existing-issue:$EXISTING")
  continue
fi
```

Issue title format (under 70 chars):

```
Security: <GHSA_ID> — <PKG> (<SEVERITY>)
```

Issue body template (use a heredoc to preserve formatting):

```bash
ISSUE_URL=$(gh issue create --repo "$REPO" \
  --title "Security: $GHSA_ID — $PKG ($SEVERITY)" \
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

## Suggested fix

Upgrade the pin in \`pyproject.toml\` to \`>= $FIRST_PATCHED\` (or the next minor/major if a closer pin exists). If the package is transitive, identify the direct dep pulling it via \`uv tree --package $PKG --invert\` (or \`poetry show -t\`) and bump that.

If the package is owned by the open-autonomy / open-aea framework, the bump should go through \`/bump-versions\` instead of a manual pin edit.

## Why this issue exists

Triaged by the \`triage-dependabot\` skill. The Dependabot alert remains open as the source of truth; this issue tracks the in-repo work to fix it.
EOF
)" --jq '.url')

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

End with a single stdout block summarising the run:

```
=== triage-dependabot summary for $REPO ===
Alerts seen:        $N_ALERTS
Dismissed (DEV):    $N_DISMISSED
Issue opened (PROD): $N_OPENED
Skipped (UNCLASSIFIABLE): $N_SKIPPED

Dismissed alerts:
  #123 PyYAML       GHSA-... (test-only: tests/helpers/yaml_loader.py)
  ...

Opened issues:
  #456 https://github.com/owner/repo/issues/456  GHSA-... cryptography
  ...

Skipped (review manually):
  #789 GHSA-... obscure-pkg — no imports found, scope=unknown
  ...
```

If `N_SKIPPED > 0`, exit code 1 so CI / cron wrappers can spot incomplete runs without parsing the summary.

---

## Reference: full per-alert loop (shell + python combo)

This is the structural reference. Adapt to the repo (the Python pyproject parser is the heavyweight bit — keep it in a `python3 - <<'PY'` block invoked per-alert, or pre-compute a `dep_groups.json` once).

```bash
set -euo pipefail
TMP=$(mktemp -d)
REPO=$(gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"')
gh api "repos/$REPO/dependabot/alerts?state=open&per_page=100" --paginate > "$TMP/alerts.json"

N=$(jq 'length' "$TMP/alerts.json")
DISMISSED=(); OPENED=(); SKIPPED=()

PROD_DIRS=$(for d in autonomy packages agent; do [[ -d "$d" ]] && echo "$d"; done | tr '\n' ' ')
TEST_DIRS="tests scripts .github"
PKG_TEST_DIRS=$(find packages -type d -name tests 2>/dev/null | tr '\n' ' ' || true)

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
4. **`dismissed_reason=not_used` only.** That's the only outcome this skill verifies. Never use `tolerable_risk` / `inaccurate` — those need human judgment.
5. **Dedupe before opening.** Search existing open issues by GHSA ID; never spam duplicates on repeat runs.
6. **Don't dismiss with no evidence.** Skip + log if neither prod nor test imports are found and the manifest is silent.
7. **Print stderr lines for skips.** The summary table is for the actor; the per-alert skip lines are for the human reviewer paginating through stderr.
8. **Exit non-zero if any alert was skipped.** Lets CI / cron wrappers notice incomplete runs.

---

## Files / state mutated

| Surface | What changes |
| ------- | ------------ |
| Dependabot alerts (DEV) | `state` flipped to `dismissed`; `dismissed_reason=not_used`; `dismissed_comment` includes the test/dev paths the scan found |
| Repo issues (PROD) | New issues opened with title `Security: <GHSA> — <pkg> (<sev>)`, labels `security,dependabot,triage-dependabot`, body referencing the alert URL + prod import paths + suggested fix |
| Repo issues (existing) | Skipped via dedupe (no edit) |
| Working tree | Nothing — the skill only mutates GitHub state, not files |

---

## When NOT to run this skill

- The repo has Dependabot disabled — exit cleanly at Phase 0.
- You're partway through `/bump-versions` and `pyproject.toml` is in flight — the classification logic reads pyproject as source of truth; mid-bump state could misclassify. Finish the bump first, then triage.
- The repo has ecosystems beyond pip (Docker, npm, GitHub Actions) that you want triaged — current skill scope is pip only. Extending to other ecosystems means new import-graph resolvers and per-ecosystem prod/test path conventions.
