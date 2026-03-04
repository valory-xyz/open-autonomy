---
name: audit-fsm
description: Audit open-autonomy FSM apps for correctness and safety
argument-hint: "[path/to/skill or packages/]"
disable-model-invocation: true
---

# Audit FSM Skill

You are an expert auditor for **open-autonomy** FSM (Finite State Machine) apps. Your job is to analyse FSM skill code for correctness bugs, safety issues, and configuration problems.

Open-autonomy is a Python framework for creating decentralized multi-agent systems. Source and docs: https://github.com/valory-xyz/open-autonomy

## How to Use Arguments

- If `$ARGUMENTS` is provided, audit only those paths (e.g. `packages/valory/skills/registration_abci`)
- If `$ARGUMENTS` is empty, discover and audit all skills under `packages/`
- Multiple paths can be space-separated

## FSM Architecture Reference

This section encodes the domain knowledge you need. Do NOT rely on external documentation — use this as your ground truth.

### Core Abstractions

#### AbciApp (base.py)

The state machine definition. Key class attributes:

```python
class AbciApp(Generic[EventType], ABC, metaclass=_MetaAbciApp):
    initial_round_cls: AppState                     # Entry point round class
    initial_states: Set[AppState] = set()           # Set of possible starting rounds
    transition_function: AbciAppTransitionFunction  # Dict[AppState, Dict[Event, AppState]]
    final_states: Set[AppState] = set()             # Terminal rounds
    event_to_timeout: EventToTimeout = {}           # Dict[Event, float] — timeout scheduling
    cross_period_persisted_keys: FrozenSet[str]     # DB keys preserved across periods
    db_pre_conditions: Dict[AppState, Set[str]]     # Required DB keys before initial states
    db_post_conditions: Dict[AppState, Set[str]]    # Guaranteed DB keys after final states
    background_apps: Set[BackgroundApp] = set()     # Concurrent background tasks
```

**Critical detail — timeout scheduling:** The framework only schedules timeouts for events that appear as keys in a round's `transition_function` entry. If an event is in `event_to_timeout` but never appears in any round's transition keys, the timeout is **never scheduled** and is dead configuration.

#### _MetaAbciApp Metaclass Validation

The metaclass already validates at class definition time:
- All non-final states have at least one non-timeout transition
- All non-final states have at most one timeout transition
- Final states have no outgoing transitions
- Initial states are not final states
- `db_pre_conditions` keys match `initial_states`
- `db_post_conditions` keys match `final_states`
- Pre-conditions and post-conditions do not intersect

**Do NOT re-report issues the metaclass already catches.** If a transition is missing from the metaclass perspective, Python would raise at import time.

#### AbstractRound (base.py)

Consensus states. Key attributes and methods:

```python
class AbstractRound(Generic[EventType], ABC):
    payload_class: Optional[Type[BaseTxPayload]]        # Accepted payload type
    synchronized_data_class: Type[BaseSynchronizedData]  # Data model

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Called each block. Returns (new_data, event) to trigger transition, or None."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Validate incoming payload. Raises on invalid."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process valid payload into round state."""
```

**Important:** The event returned by `end_block()` must exist as a key in that round's `transition_function` entry. If it doesn't, the transition silently fails.

#### Common Round Types

- **CollectSameUntilThresholdRound**: Collects payloads; emits `done_event` when threshold agents agree, `none_event` for empty consensus, `no_majority_event` when majority impossible
- **CollectDifferentUntilThresholdRound**: Collects distinct payloads; emits `done_event` after threshold + block confirmations
- **CollectNonEmptyUntilThresholdRound**: Like CollectDifferent but filters empty attributes
- **CollectDifferentUntilAllRound** / **CollectSameUntilAllRound**: Require 100% participation
- **OnlyKeeperSendsRound**: Single designated agent submits; `done_event` / `fail_event`

Each of these base classes defines which events can be emitted. Subclasses must wire all possible events in the transition function.

#### BaseTxPayload (base.py)

```python
@dataclass(frozen=True)
class BaseTxPayload(metaclass=_MetaPayload):
    sender: str
    # Subclass fields are the payload data
```

- Frozen dataclass — immutable after creation
- `_MetaPayload` maintains a global registry: `"{module}.{ClassName}"` → class
- Registration happens at class creation (import time), which is single-threaded

#### BaseBehaviour (behaviour_utils.py)

```python
class BaseBehaviour(AsyncBehaviour, IPFSBehaviour, CleanUpBehaviour, ABC):
    matching_round: Type[AbstractRound]  # Links behaviour to its round

    async def async_act(self) -> Generator:
        """Main logic — must be implemented by subclasses."""

    def send_a2a_transaction(self, payload) -> Generator:
        """Send payload to consensus layer."""
```

### Background Apps

Background apps run concurrently with the main FSM.

```python
class BackgroundAppType(Enum):
    TERMINATING = 0   # Highest priority: terminates parent when done
    EVER_RUNNING = 1  # Medium priority: runs indefinitely, no start/end events
    NORMAL = 2        # Lowest priority: bounded lifecycle with start/end events
    INCORRECT = 3     # Invalid configuration

class BackgroundAppConfig:
    round_cls: AppState
    abci_app: Optional[Type[AbciApp]] = None
    start_event: Optional[EventType] = None
    end_event: Optional[EventType] = None
```

**Priority ordering:** `bg_apps_prioritized` groups apps by type: TERMINATING → EVER_RUNNING → NORMAL. This controls which background result takes precedence in `end_block()`.

### Composition / Chaining

Apps are composed via `chain()` in `abci_app_chain.py`:

```python
def chain(
    abci_apps: Tuple[Type[AbciApp], ...],
    abci_app_transition_mapping: AbciAppTransitionMapping,  # Dict[AppState, AppState]
) -> Type[AbciApp]:
```

The mapping connects final states of one app to initial states of the next. The `chain()` function validates:
- No duplicate apps or round classes
- All mapping keys are final states, all values are initial states
- DB post-conditions of predecessor satisfy pre-conditions of successor
- Event timeout consistency across apps

---

## Audit Checklist

### Critical (C) — Bugs that cause incorrect runtime behaviour

#### C1: Shared Mutable References

**What:** `([],) * n` creates `n` references to the **same** list object. Appending to any index mutates all of them.

**Search pattern:** Grep for `\(\[\],?\) \* \d+` or `\(\[\]\,\) \*` or `\({}\,\) \*` in Python files.

**Bug example:**
```python
grouped: Tuple[List, ...] = ([],) * 3
grouped[0].append("x")
# grouped is now (["x"], ["x"], ["x"]) — all same object!
```

**Correct:**
```python
grouped: Tuple[List, ...] = tuple([] for _ in range(3))
```

**Why it matters:** Silently corrupts data structures. In the framework, this broke background app priority grouping — all apps ended up in all priority groups.

#### C2: Operator Precedence in Boolean Guards

**What:** Python `and` binds tighter than `or`. Complex boolean expressions without explicit parentheses can evaluate differently than intended.

**Search pattern:** Look for multi-line `if` conditions combining `and`/`or`, especially with `not`. Focus on conditions that span 3+ lines or mix `and`/`or` operators.

**Bug example:**
```python
if (
    not params.use_slashing
    and background_cls.auto_behaviour_id() == SLASHING_ID
    or background_cls == PendingOffencesBehaviour  # BUG: always True branch
):
    continue
```

The `or background_cls == PendingOffencesBehaviour` is evaluated at the top level, making the entire condition True whenever `background_cls == PendingOffencesBehaviour`, regardless of `use_slashing`.

**Correct:**
```python
if (
    not params.use_slashing
    and (
        background_cls.auto_behaviour_id() == SLASHING_ID
        or background_cls == PendingOffencesBehaviour
    )
):
    continue
```

**Why it matters:** Silently skips or includes wrong code paths. In the framework, this unconditionally skipped `PendingOffencesBehaviour`.

#### C3: Transition Function Completeness for Round Events

**What:** Every event that `end_block()` can return must appear as a key in that round's `transition_function` entry. Otherwise the transition silently fails and the round hangs.

**How to check:**
1. For each round class, find all `return` statements in `end_block()` that return `(data, SomeEvent.EVENT_NAME)`
2. Verify each such event appears in the round's entry in `transition_function`
3. For rounds extending `CollectSameUntilThresholdRound` etc., check that `done_event`, `none_event`, `no_majority_event` (and `fail_event` for keeper rounds) are all wired in the transition function

**Why it matters:** A missing transition means the round never completes, hanging the entire agent service.

#### C4: Dead Timeouts

**What:** Entries in `event_to_timeout` for events that never appear as keys in any round's `transition_function` are dead config — the framework never schedules them.

**How to check:**
1. Collect all events from `event_to_timeout` keys
2. Collect all events that appear as keys in `transition_function` (across all rounds)
3. Events in (1) but not in (2) are dead timeouts

**Why it matters:** Developers may believe a timeout is protecting against hangs, when in fact it never fires. This creates a false sense of safety.

### High (H) — Issues with significant impact

#### H1: Background App Configuration

**What:** Verify `BackgroundAppConfig` instances are correctly typed:
- EVER_RUNNING: no `start_event`, no `end_event`, no `abci_app`
- TERMINATING: has `start_event`, no `end_event`, has `abci_app`
- NORMAL: has `start_event`, has `end_event`, has `abci_app`
- Any other combination is INCORRECT

Also check for shared mutable state between app configs (see C1).

**Search pattern:** Grep for `BackgroundAppConfig`, `background_apps`, `bg_apps`.

#### H2: Composition Chain Completeness

**What:** In composed apps using `chain()`:
- Every final state in the mapping must be a valid final state of one of the composed apps
- Every initial state target must be a valid initial state of one of the composed apps
- `cross_period_persisted_keys` should include all keys needed by the first app in the chain
- `abci_app_transition_mapping` must cover all final states that should lead to another app

**Search pattern:** Grep for `abci_app_transition_mapping`, `chain(`, `cross_period_persisted_keys`.

#### H3: Resource Lifecycle

**What:** Look for:
- Sockets or file handles opened without context managers (`with` statements)
- `subprocess.Popen` or process `terminate()` without corresponding `wait()` (creates zombies)
- `requests.get/post` without `timeout` parameter

**Search pattern:** Grep for `open(`, `socket.socket(`, `.terminate()`, `Popen(`, `requests.get`, `requests.post` — then check surrounding context for proper cleanup.

### Medium (M) — Issues that indicate potential problems

#### M1: Payload Class Registration

**What:** Each round's `payload_class` attribute must reference a valid `BaseTxPayload` subclass. The class must be importable (registered via `_MetaPayload` at import time).

**How to check:** For each round, verify `payload_class` is set and points to a class that inherits from `BaseTxPayload`.

#### M2: Event Enum Completeness

**What:** Look for:
- Event enum members defined but never used in any `transition_function` or `end_block()` return — dead config
- Events referenced in code but not defined in the enum

**Search pattern:** Parse the event enum, then cross-reference with `transition_function` definitions and `end_block()` returns.

#### M3: DB Pre/Post Conditions Consistency

**What:** Beyond what the metaclass checks:
- `db_pre_conditions` keys should match `initial_states` (metaclass checks this)
- `db_post_conditions` keys should match `final_states` (metaclass checks this)
- In composed apps, post-conditions of predecessor should be a superset of pre-conditions of successor
- Check that keys listed in conditions are actually read/written by the corresponding rounds

#### M4: Thread Join Without Timeout

**What:** `thread.join()` calls without a `timeout` parameter can hang indefinitely, blocking CI runners and agent processes.

**Search pattern:** Grep for `\.join\(\)` in Python files, distinguish `thread.join()` from `str.join()` by context.

### Low (L) — Code quality and maintainability

#### L1: Dead Code

**What:** Unused instance variables set in `__init__` or `setup()` but never read. Unreachable code after unconditional `return`/`raise`/`break`.

#### L2: Stale Imports and Unused Events

**What:** Imports that are no longer used. Event enum members with no references.

#### L3: Docstring / Transition Function Drift

**What:** Comments or docstrings describing the FSM that don't match the actual `transition_function` definition.

---

## False Positive Guidance

These patterns look suspicious but are **correct by design**. Do NOT report them:

### `synchronized_data.update()` return value not captured
```python
synchronized_data.update(synchronized_data_class=SomeSyncData, **kwargs)
# No variable captures the return value
```
**Why it's fine:** `update()` mutates the underlying `AbciAppDB` in-place before returning a new wrapper object. The mutation happens regardless of whether the return value is captured.

### `check_tx` not tracking offences while `deliver_tx` does
**Why it's fine:** Offence tracking must be **deterministic** (consensus-critical). `check_tx` is non-deterministic (per-node mempool validation), so offence tracking there would break consensus.

### `sys.getsizeof()` for transaction size validation
**Why it's fine:** Provides a conservative upper bound vs raw byte length. The overhead is constant and negligible against the ~1 MiB transaction size limit.

### `_is_healthy = False` after successful Tendermint reset
**Why it's fine:** Intentional per-cycle state reset so the next `_start_reset()` begins a fresh health check cycle.

### Payload registry mutations during import
**Why it's fine:** `_MetaPayload` registers payload classes at class creation time. Class creation is single-threaded in Python; the GIL protects simple dict writes during import.

### Test helpers using stub signatures or contract IDs
**Why it's fine:** Intentional separation of concerns. Behaviour tests validate flow logic, not serialization correctness. Using stubs is correct test design.

---

## Analysis Procedure

Follow these steps in order:

### Step 1: Discovery

Determine the scope of the audit:

```
# If $ARGUMENTS is provided, use those paths directly
# Otherwise, discover all skill directories:
Glob pattern: packages/**/skills/*/rounds.py
```

Build a list of skill directories to audit. Each skill directory should contain some subset of: `rounds.py`, `behaviours.py`, `payloads.py`, `models.py`, `__init__.py`.

### Step 2: Parallel Analysis

Launch up to **3 parallel Explore agents**, dividing skills evenly among them. Each agent should:

1. **Read the key files** in each assigned skill:
   - `rounds.py` — AbciApp definition, round classes, transition function, events
   - `behaviours.py` — behaviour classes, matching_round links
   - `payloads.py` — payload definitions
   - `models.py` — if it exists, for parameter and data model definitions

2. **Run all checks from the Audit Checklist** (C1–C4, H1–H3, M1–M4, L1–L3)

3. **Return findings** as a structured list with:
   - Check ID (e.g. C1, H2)
   - File path and line number
   - Code snippet showing the issue
   - Explanation of why it's a problem
   - Suggested fix

Give each agent the full checklist (copy the relevant sections from this skill) so it can work independently.

### Step 3: Structural Analysis

After agents return, perform a final cross-cutting check:
- For composed apps, verify chain consistency (H2) across skill boundaries
- Check for conflicting event names or round IDs across composed skills
- Verify `cross_period_persisted_keys` cover all necessary data flow

### Step 4: Generate Report

Merge all findings into a single structured report.

---

## Output Format

Present the audit report as follows:

```markdown
# FSM Audit Report

**Scope:** [list of audited skill paths]
**Date:** [current date]

## Critical Findings

### [C#]: [Title]
- **File:** `path/to/file.py:line`
- **Issue:** [description]
- **Code:**
  ```python
  [problematic code snippet]
  ```
- **Fix:**
  ```python
  [corrected code snippet]
  ```

## High Findings
[same format]

## Medium Findings
[same format]

## Low Findings
[same format]

## Summary

| Severity | Count |
|----------|-------|
| Critical | N     |
| High     | N     |
| Medium   | N     |
| Low      | N     |

## Notes
[Any false-positive exclusions or caveats about the audit scope]
```

If no findings at a severity level, include the section header with "No findings." underneath.
