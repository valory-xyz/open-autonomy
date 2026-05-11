---
name: audit-fsm
description: Audit open-autonomy FSM apps for correctness and safety
argument-hint: "[path/to/skill or packages/]"
disable-model-invocation: false
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

#### AbciApp

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

#### AbstractRound

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

**Key round subclass attributes for data flow:**
- `collection_key`: DB key where the round stores all collected payloads (e.g. `"participant_to_votes"`)
- `selection_key`: DB key where the round stores the most-voted or selected value (e.g. `"most_voted_tx_hash"`)

The corresponding `SynchronizedData` property accessors must read from the **same** DB key. A mismatch means the property reads stale or wrong data.

#### BaseTxPayload

```python
@dataclass(frozen=True)
class BaseTxPayload(metaclass=_MetaPayload):
    sender: str
    # Subclass fields are the payload data
```

- Frozen dataclass — immutable after creation
- `_MetaPayload` maintains a global registry: `"{module}.{ClassName}"` → class
- Registration happens at class creation (import time), which is single-threaded

#### BaseBehaviour

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

**Important detail — event pruning during composition:** `chain()` builds a merged `transition_function` and then filters `event_to_timeout` to only include events that appear as keys in the merged transition function (lines 261-269 of `abci_app_chain.py`). Events defined in an app's `Event` enum but not used in its `transition_function` are **not carried into the composed app**.

### Library Skills

The open-autonomy framework ships several **library skills** — reusable building blocks designed to be composed into larger agent services, not run standalone:

- `registration_abci` — agent registration
- `reset_pause_abci` — reset and pause between periods
- `transaction_settlement_abci` — on-chain transaction settlement
- `slashing_abci` — slashing misbehaving agents
- `termination_abci` — graceful service termination
- `offend_abci` — offence tracking

Downstream projects compose these library skills with their own custom skills via `chain()`. Library skills often define `Event.ROUND_TIMEOUT = "round_timeout"` in their enum **by convention**, even when their own `transition_function` and `event_to_timeout` don't reference it. This is intentional:

1. **Extensibility:** Downstream services that compose these skills may subclass rounds or modify transition functions to add timeout handling. Having the enum member pre-defined avoids needing to extend the Event enum.
2. **Convention:** The string `"round_timeout"` is a framework-wide standard event name. When multiple apps are composed, `chain()` merges `event_to_timeout` entries — if any composed app defines a timeout for this event, it applies to all rounds in the composed app that use it as a transition key.
3. **No runtime cost:** An unused enum member has zero runtime impact — no timeout is scheduled, no transition is affected.

**Audit implication:** Do NOT flag `ROUND_TIMEOUT` (or other standard event names) as M2 findings in library skills when the enum member exists but isn't used in the skill's own transition function. This is a convention, not dead code.

**Project-specific library skills.** The list above is the *framework default*. Downstream projects often introduce their own library skills (skills meant to be composed only). When auditing a downstream repo:

- Skills with `is_abstract: true` in `skill.yaml` are typically library skills.
- Check the project's `CLAUDE.md` / `AGENTS.md` for an explicit library-skills list.
- Read `aea-config.yaml` of the agent under audit — skills that appear only as composition imports (and are never directly wired to the FSM by the agent) are library skills.
- Apply the M2 / C4 carve-outs to those project-specific library skills as well.

### `is_abstract: true` Semantics

A skill with `is_abstract: true` in its `skill.yaml` is composition-only — it is never instantiated as a top-level skill, only consumed by another `chain()` call. Audit checks branch on this flag:

- **Skip** "missing `fsm_specification.yaml`" findings — abstract skills are composed-only and don't need standalone wiring.
- **Skip** "missing dialogue X" findings if the dialogue is provided by the composing skill.
- **Demote** "missing handler" findings to informational unless the handler is required for composition (e.g. an `ABCIHandler` is mandatory).
- **Apply** the same M2 / C4 carve-outs as library skills (unused events / dead timeouts may be intentional extension points).

Prior audits avoided false positives on the `agent_performance` "missing dialogues" / "missing fsm_specification" findings only by accident — the CLI tool failed before reaching these checks. The `is_abstract` branch now makes the suppression deliberate.

### Test Infrastructure

The framework provides base test classes in `packages/valory/skills/abstract_round_abci/test_tools/` and `plugins/aea-test-autonomy/`.

#### Behaviour Test Base (`test_tools/base.py`)

```python
class FSMBehaviourBaseCase(BaseSkillTestCase, ABC):
    path_to_skill: Path                    # Must be set by subclass
    behaviour: AbstractRoundBehaviour

    def fast_forward_to_behaviour(self, behaviour, behaviour_id, synchronized_data):
        """Jump to a specific behaviour in the FSM."""

    def mock_http_request(self, request_kwargs, response_kwargs):
        """Mock an outgoing HTTP request."""

    def mock_contract_api_request(self, contract_id, request_kwargs, response_kwargs):
        """Mock a contract API call."""

    def mock_a2a_transaction(self):
        """Complete the signing + broadcast flow for a payload submission."""
        # 1. Mock SIGN_MESSAGE → SIGNED_MESSAGE
        # 2. Mock HTTP POST broadcast
        # 3. Mock HTTP GET receipt check

    def end_round(self, done_event):
        """Transition the round to completion."""

    def _test_done_flag_set(self):
        """Verify the round completion flag is set."""
```

**Setup/teardown:** `setup_class()` saves and clears `_MetaPayload.registry`; `teardown_class()` restores it. Subclasses overriding these must call `super()`.

#### Specialised Behaviour Tests (`test_tools/common.py`)

```python
class BaseRandomnessBehaviourTest(FSMBehaviourBaseCase):
    randomness_behaviour_class: Type[BaseBehaviour]  # Required
    next_behaviour_class: Type[BaseBehaviour]         # Required
    done_event: Any                                   # Required

class BaseSelectKeeperBehaviourTest(FSMBehaviourBaseCase):
    select_keeper_behaviour_class: Type[BaseBehaviour]  # Required
    next_behaviour_class: Type[BaseBehaviour]            # Required
    done_event: Any                                      # Required
```

#### Round Test Base (`test_tools/rounds.py`)

```python
class BaseRoundTestClass:
    _synchronized_data_class: Type[BaseSynchronizedData]  # Required
    _event_class: Any                                      # Required

    def _complete_run(self, test_runner, iter_count=MAX_PARTICIPANTS):
        """Execute the test generator."""
```

**Specialised round test classes** (each provides a `_test_round()` generator):
- `BaseCollectSameUntilAllRoundTest`
- `BaseCollectSameUntilThresholdRoundTest`
- `BaseCollectDifferentUntilAllRoundTest`
- `BaseOnlyKeeperSendsRoundTest`
- `BaseVotingRoundTest`

#### Fixture Helpers (`plugins/aea-test-autonomy`)

Mixin classes for external services: `UseFlaskTendermintNode`, `UseGanache`, `UseACNNode`, `UseRegistries`, `UseGnosisSafeHardHatNet`, `UseLocalIpfs`.

**Critical:** These must use `self` + `type(self)` pattern for fixtures, NOT `@classmethod @pytest.fixture` (broken in Python 3.14).

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

**Carve-out — framework-scheduled events:** Events scheduled by the framework via `event_to_timeout` (most commonly `ROUND_TIMEOUT`) are NOT emitted by `end_block()` — the framework dispatches them via Tendermint's `update_time()`. An event is `end_block`-emittable only if it is part of the round's base class event set (`done_event`, `none_event`, `no_majority_event`, `fail_event`) or returned explicitly by a custom `end_block` override. Do NOT flag a transition-function event as "missing from `end_block()`" if it is wired into `event_to_timeout` — that is the framework's job.

**Why it matters:** A missing transition means the round never completes, hanging the entire agent service.

#### C4: Dead Timeouts

**What:** Entries in `event_to_timeout` for events that never appear as keys in any round's `transition_function` are dead config — the framework never schedules them.

**How to check:**
1. Collect all events from `event_to_timeout` keys
2. Collect all events that appear as keys in `transition_function` (across all rounds)
3. Events in (1) but not in (2) are dead timeouts

**Why it matters:** Developers may believe a timeout is protecting against hangs, when in fact it never fires. This creates a false sense of safety.

**Caveat:** Skills whose directory name starts with `test_` (e.g. `test_abci`, `test_solana_tx_abci`) are **test/scaffold skills** that exist to exercise the framework, not production FSM apps. Dead timeouts in these skills are often intentional test fixtures (e.g. testing that `SharedState.setup()` can wire `event_to_timeout` from params). Do NOT flag these as C4 findings. See also the False Positive Guidance section.

#### C5: Non-Determinism in `end_block()`

**What:** `AbstractRound.end_block()` must be a **pure function of consensus state**. Reading wall-clock time, the file system, environment variables, randomness, or external services produces a different event on different agents — silently breaking consensus. The Tendermint replica picks one of the divergent state transitions; the others are wedged or marked Byzantine.

**Search patterns inside `end_block()` bodies (and any helper called from `end_block`):**
- File I/O: `open(`, `Path.read_*`, `json.load(open(`, `os.path.exists(`, `pathlib.*`
- Wall clock: `time.time()`, `datetime.now()`, `datetime.utcnow()`, `time.monotonic()` — use `self.context.state.round_sequence.last_round_transition_timestamp` (the agreed Tendermint block time of the last transition, set on `RoundSequence` from `self._blockchain.last_block.timestamp` — see `packages/valory/skills/abstract_round_abci/base.py`), or read a timestamp written into a payload field by a predecessor round (consensus-agreed, then surfaced via `synchronized_data`)
- Randomness: `random.*`, `secrets.*`, `os.urandom(` — use `synchronized_data.most_voted_randomness` (consensus randomness)
- Environment: `os.environ.get(`, `os.getenv(`
- Network / external services: `requests.*`, `urlopen(`, `socket.*`, `subprocess.*`, contract calls, IPFS reads
- Locale-dependent operations: `locale.*`, `re` patterns that depend on system locale

**Bug example:**
```python
def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
    # BUG: each agent reads its own local file
    with open("/tmp/benchmark_mode.json") as f:
        config = json.load(f)
    if config["mode"] == "benchmark":
        return self.synchronized_data, Event.BENCHMARK
    return self.synchronized_data, Event.NORMAL
```
Different agents may have different files → different events → consensus break.

**Severity by service shape:**
- **Multi-agent service:** Critical — consensus break.
- **Single-agent / sovereign service** (e.g. some Pearl-shipped configurations): demote to **Low (L)** with a note: *"severity escalates to Critical when the service runs with N>1 agents."* This keeps the finding in the standard L section of the report rather than vanishing — Pearl-shipped services regularly get promoted to multi-agent, so silent loss is the worst outcome.

**How to check:**
1. Walk every `end_block()` body and any function it calls.
2. **Also walk every `process_payload()` body in the same round.** `process_payload()` populates `self.synchronized_data` / round-local state that `end_block()` then reads — non-deterministic writes in `process_payload()` produce non-deterministic `end_block()` reads even when the `end_block()` body itself is clean. An auditor who walks only `end_block()` will report a clean C5 on a real consensus break.
3. Grep the imports of the round module for `time`, `datetime`, `random`, `os`, `requests`, `urllib`, `pathlib`.
4. For each non-deterministic call found, verify whether the surrounding code path can reach `end_block()` (directly or via `process_payload()` → `synchronized_data` propagation).
5. Check whether the agent's service config (look at `services/*/service.yaml` `number_of_agents`) is 1 or N to set severity.

**Fix:** All non-deterministic data must be sourced from `synchronized_data` — i.e. agreed via consensus by the predecessor round's payload.

#### C6: Unmapped Reachable Finals in Composition

**What:** In `chain()`-composed AbciApps, every **final state of an inner app** that is not declared as a terminal state of the composed app must appear as a **key** in `abci_app_transition_mapping`. Otherwise the composed FSM reaches that state and stops — there is no transition out, the round emits no further events, and the agent hangs.

**Important — what `chain()` does and does NOT validate.** The framework validates that mapping keys ARE final states of inner apps and that mapping values ARE initial states of other inner apps (`chain()` raises `ABCIAppInternalError` at construction time on violations). It does NOT verify that **every reachable inner final state** has been mapped. That is the gap this check covers.

**How to check:**
1. For each inner `AbciApp` in the chain, read `cls.final_states`.
2. Compute `reachable_finals = ⋃ inner.final_states for inner in chained_apps`.
3. Subtract:
   - `composed_app.final_states` (states deliberately terminal in the composed FSM).
   - `set(abci_app_transition_mapping.keys())` (states with an explicit successor).
4. The remainder is the set of **unmapped reachable finals**. Each one is a hang on reach.

**Bug example:**
```python
class InnerAppA(AbciApp):
    final_states = {DoneRound, FailedRound, ImpossibleRound}

# In composition.py:
abci_app_transition_mapping = {
    FinishedAppARound: SomeInitialRound,
    # BUG: FailedRound and ImpossibleRound are reachable finals of InnerAppA
    #      but absent from this mapping AND absent from composed_app.final_states
}
```

At runtime: agent enters `InnerAppA`, takes a `FAIL_EVENT` transition to `FailedRound`, the round commits with no outbound event mapping → composed FSM hangs.

**Severity rationale:** Same blast radius as C3 (transition function completeness). A round hang at composition level wedges the entire agent, with the same recovery profile.

**Search pattern:** locate the module that calls `chain(...)` (typically `composition.py`); enumerate `final_states` of every inner app referenced; compare against the mapping keys plus the composed app's terminal set.

**Why this needs to be its own check, not bundled under H2:** real audits have found this in production. Two unmapped finals in one repo's `composition.py` were the highest-impact FSM finding from a recent run and almost slipped through under H2's old "every mapping key/value valid" framing — those bullets are framework-validated and produce zero new findings, which masked the still-needed unmapped-finals check.

### High (H) — Issues with significant impact

#### H1: Background App Configuration

**What:** Verify `BackgroundAppConfig` instances are correctly typed:
- EVER_RUNNING: no `start_event`, no `end_event`, no `abci_app`
- TERMINATING: has `start_event`, no `end_event`, has `abci_app`
- NORMAL: has `start_event`, has `end_event`, has `abci_app`
- Any other combination is INCORRECT

Also check for shared mutable state between app configs (see C1).

**Search pattern:** Grep for `BackgroundAppConfig`, `background_apps`, `bg_apps`.

#### H2: Composition Chain Completeness (Index)

H2 used to bundle four bullets that have since been split or moved. Kept as an index so reports referencing H2 still resolve:

- **Mapping key validity** ("every mapping key is a valid final state of an inner app") — **framework-validated** by `chain()` at construction time. Do NOT re-flag.
- **Mapping value validity** ("every mapping value is a valid initial state of an inner app") — **framework-validated** by `chain()`. Do NOT re-flag.
- **Unmapped reachable finals** ("every reachable inner final has a mapping entry or is composed-terminal") — see **C6**.
- **`cross_period_persisted_keys` completeness for post-reset reads** — see **M7**.

If a finding genuinely fits "composition chain completeness" but doesn't match any of the above, surface it under H2 as a free-form finding — but in practice, every prior H2-shaped finding maps cleanly to one of the four targets above.

#### H3: Resource Lifecycle

**What:** Look for:
- Sockets or file handles opened without context managers (`with` statements)
- `subprocess.Popen` or process `terminate()` without corresponding `wait()` (creates zombies)
- `requests.get/post` without `timeout` parameter

**Search pattern:** Grep for `open(`, `socket.socket(`, `.terminate()`, `Popen(`, `requests.get`, `requests.post` — then check surrounding context for proper cleanup.

#### H4: `extended_requirements = ()` Override Without Compensating `end_block`

**What:** `_MetaAbstractRound.__init__` (`packages/valory/skills/abstract_round_abci/base.py:1066-1068`) reads each round subclass's `extended_requirements` tuple and verifies via `hasattr` that every named class attribute is defined. This catches "subclass forgot to set `done_event` / `none_event` / `collection_key` / `selection_key`" at class-creation time.

Setting `extended_requirements = ()` (or `tuple()`) in a subclass disables the loop — the metaclass passes any subset of attributes (including none). This is a legitimate escape hatch when the subclass overrides `end_block()` with custom logic that doesn't depend on the standard attributes.

It becomes a **footgun** when:
- The subclass omits one or more of the parent's required attributes, AND
- The subclass inherits the parent's `end_block()` (which still reads those attributes).

Result: class definition succeeds. The first time `end_block()` runs, `AttributeError: 'XRound' object has no attribute 'done_event'` (or `collection_key`, etc.) propagates uncaught from the behaviour generator — agent process crashes (`audit-resilience` Category A).

**How to check:**
1. Grep for `extended_requirements\s*=\s*\(\s*\)` and `extended_requirements:\s*Tuple.*=\s*\(\s*\)` and `extended_requirements\s*=\s*tuple\(\s*\)`.
2. For each match, identify the parent class and look up its `extended_requirements` (e.g. `CollectSameUntilThresholdRound.extended_requirements` covers `done_event`, `no_majority_event`, `none_event`, `collection_key`, `selection_key`).
3. Verify the subclass either:
   - Defines a custom `end_block()` (and the override does NOT read the missing attributes), OR
   - Defines all attributes that were in the parent's `extended_requirements` despite the override.
4. If neither, this is crash-on-reach. Promote severity to **Critical** in the report (the subclass crashes the agent the first time it runs).

**Bug example:**
```python
class AgentDBRound(CollectSameUntilThresholdRound):
    payload_class = AgentDBPayload
    extended_requirements = ()  # disables metaclass attribute check
    # missing: done_event, none_event, no_majority_event, collection_key, selection_key
    # inherits parent's end_block, which reads self.done_event → AttributeError at runtime
```

**Severity rationale:** Default H because legitimate uses of the empty override exist (custom-`end_block` rounds). Promote to C when the audit verifies the subclass inherits the parent's `end_block` AND omits at least one required attribute — that combination is a guaranteed crash.

**Search pattern:** `extended_requirements\s*=\s*(\(\s*\)|tuple\(\s*\))` in any round module.

### Medium (M) — Issues that indicate potential problems

#### M1: Payload Class Mismatch

**What:** Each round's `payload_class` attribute must reference the correct `BaseTxPayload` subclass — the one that matches the round's `keeper_payload` type hint (for `OnlyKeeperSendsRound`) or the payloads agents actually send to that round.

**How to check:** For each round, verify:
1. `payload_class` is set and points to a class that inherits from `BaseTxPayload`
2. For `OnlyKeeperSendsRound` subclasses: `payload_class` matches the `keeper_payload` type hint
3. The payload class fields match what `end_block()` accesses (e.g. `self.keeper_payload.some_field`)

**Severity escalation:** If `payload_class` points to the wrong class, this is **Critical** — the round will reject valid transactions at runtime because `check_payload()` validates against the wrong type.

#### M2: Event Enum Completeness

**What:** Look for:
- Event enum members defined but never used in any `transition_function` or `end_block()` return — dead config
- Events referenced in code but not defined in the enum

**Search pattern:** Parse the event enum, then cross-reference with `transition_function` definitions and `end_block()` returns.

**Caveat — library skills:** Standard event names like `ROUND_TIMEOUT = "round_timeout"` are conventionally defined in library skills (e.g. `registration_abci`, `reset_pause_abci`) even when not used in the skill's own transition function. This is an extensibility convention, not dead code. See the "Library Skills" section above. Do NOT flag these as M2 findings.

#### M3: DB Pre/Post Conditions Consistency

**What:** Beyond what the metaclass checks:
- `db_pre_conditions` keys should match `initial_states` (metaclass checks this)
- `db_post_conditions` keys should match `final_states` (metaclass checks this)
- In composed apps, post-conditions of predecessor should be a superset of pre-conditions of successor
- Check that keys listed in conditions are actually read/written by the corresponding rounds

#### M4: Thread Join Without Timeout

**What:** `thread.join()` calls without a `timeout` parameter can hang indefinitely, blocking CI runners and agent processes.

**Search pattern:** Grep for `\.join\(\)` in Python files, distinguish `thread.join()` from `str.join()` by context.

#### M5: `collection_key`/`selection_key` vs SynchronizedData Property Mismatch

**What:** Round subclasses of `CollectSameUntilThresholdRound` etc. define `collection_key` and `selection_key` that determine which DB keys the round writes to. The corresponding `SynchronizedData` properties must read from the **same** keys. A mismatch means the property returns wrong or missing data at runtime.

**How to check:**
1. For each round subclass, find the `collection_key` and `selection_key` values
2. Find the corresponding `SynchronizedData` properties that are meant to read that data
3. Verify the property calls `self.db.get_strict("same_key_name")` or `self.db.get("same_key_name")`

**Bug example:**
```python
class StatusResetRound(CollectSameUntilThresholdRound):
    collection_key = "participant_to_offence_reset"  # Writes here

class SynchronizedData(BaseSynchronizedData):
    @property
    def participant_to_offence_reset(self) -> DeserializedCollection:
        serialized = self.db.get_strict("participant_to_randomness")  # BUG: reads wrong key!
```

**Why it matters:** The property silently returns data from a different round, causing logic errors or `KeyError` crashes.

#### M6: SynchronizedData JSON Round-Trip Safety

**What:** Writes to `synchronized_data` go through `AbciAppDB.update()` which JSON-serializes values. Values that are not JSON-native (`set`, `Decimal`, `dataclass` instances, `datetime`, `tuple` of mixed types, custom enum members) silently lose fidelity (e.g. `tuple` → `list`) or raise `TypeError` at write time. Custom serializer hooks (e.g. `EGreedyPolicy.serialize` / `deserialize`) must be applied symmetrically on the read side.

Plus: when a `SynchronizedData` subclass uses **multiple inheritance** to combine data classes from composed skills (e.g. `class SynchronizedData(MechInteractSyncedData, MarketManagerSyncedData, TxSettlementSyncedData)`), two parents defining the same property name silently shadow according to MRO order. The subclass author may believe they are reading from skill A's data when they're actually reading from skill B's.

**How to check:**
1. For each round's `end_block()`, list keys + value-expressions written via `update(...)` or `update(synchronized_data_class=..., ...)`.
2. For each value, infer the type (walk back from the call site, or look at the payload field type, or trace through `json.loads`). Flag values that are not JSON-native unless a custom serializer is documented at both write and read sides.
3. For each `SynchronizedData` subclass with multiple base classes, walk the MRO and flag any property name defined in more than one parent — explicitly call out which parent wins.

**Bug examples:**
```python
# BUG (write-time crash): set is not JSON-serializable — TypeError at write time
self.synchronized_data.update(participants={agent1, agent2})

# BUG (write-time crash): Decimal is not JSON-serializable — TypeError at write time
# (same failure mode as set; do NOT mistake this for silent rounding to float)
self.synchronized_data.update(price=Decimal("0.123456789012345678"))

# BUG (silent precision loss): float arithmetic drifts BEFORE serialization;
# JSON round-trip then preserves the wrong value
self.synchronized_data.update(price=0.1 + 0.2)  # writes 0.30000000000000004

# BUG: same property name in two parents
class MechInteractSyncedData:
    @property
    def latest_event(self) -> str: return self.db.get_strict("mech_event")
class MarketManagerSyncedData:
    @property
    def latest_event(self) -> str: return self.db.get_strict("market_event")
class SynchronizedData(MechInteractSyncedData, MarketManagerSyncedData):
    pass  # reads mech_event — likely surprising for someone reading the file top-down
```

**Fix:** Use lists/dicts/primitives or apply explicit serialize/deserialize hooks. Pick distinct property names across composed data classes, or override explicitly with documented intent.

#### M7: `cross_period_persisted_keys` Completeness for Post-Reset Initial Reads

**What:** After a period reset (`ResetAndPauseRound`), the next period restarts at the chain's initial round. Any DB key that the initial round chain (or its behaviours) reads via `self.db.get` / `self.db.get_strict` must be in `cross_period_persisted_keys` — otherwise it's missing after the first reset and the read returns `None` / raises `KeyError`. The bug is invisible in the first period (the key was just written) and surfaces only after the reset.

**How to check:**
1. Identify the initial round chain after a reset (typically `RegistrationRound` → ... → first business round). Use the composed app's `transition_function` to follow **`Event.DONE`** from `ResetAndPauseRound` to the next round — this is the normal post-reset re-entry path. `Event.RESET_AND_PAUSE_TIMEOUT` and `Event.NO_MAJORITY` are failure paths that route to `FinishedResetAndPauseErrorRound` and do not represent the post-reset initial-read set (see `packages/valory/skills/reset_pause_abci/rounds.py:94-98`). Tracing the failure path will surface bogus keys or miss the real ones.
2. Statically collect every `self.db.get(...)` / `self.db.get_strict(...)` and every `self.synchronized_data.<property>` access in those rounds and their behaviours. Resolve property accesses to the underlying DB key.
3. Subtract `cross_period_persisted_keys` **AND `AbciAppDB.default_cross_period_keys`**. The framework auto-injects the defaults at every period boundary (`packages/valory/skills/abstract_round_abci/base.py:516-523` then `:549`); a skill that reads any of `{all_participants, participants, consensus_threshold, safe_contract_address}` after a reset does NOT need to redeclare them — they survive every period automatically. Subtracting only `cross_period_persisted_keys` produces false positives on every audit. The remaining diff is the set of keys that will genuinely be missing after the first reset.

**Why it matters:** First-period success masks the bug. Production crashes appear only after the first natural reset (often hours or days into a deployment).

#### M8: Misleading Event-Shaped Class Attributes on Round Subclasses

**What:** On `CollectSameUntilThresholdRound` and siblings, the framework's `end_block()` consults a fixed set of class attributes: `done_event`, `none_event`, `no_majority_event`, `collection_key`, `selection_key` (and `fail_event` for keeper rounds — see `extended_requirements`). Defining additional class attributes whose RHS is an `Event` enum value (e.g. `withdrawal_initiated: Event = Event.WITHDRAWAL_INITIATED`) does NOT wire that event into the round — the parent's `end_block()` never reads it.

Combined with a `transition_function` entry for that event, this produces a "looks-like-config-but-isn't" footgun. The current C3 check catches the dead transition. M8 catches the misleading attribute that gives the false impression the round will emit it.

**How to check:**
1. For each `CollectSameUntilThresholdRound` (or sibling) subclass, list class-level attributes whose RHS is an `Event` enum value.
2. Subtract the names actually consulted by the parent class (`done_event`, `none_event`, `no_majority_event`, `fail_event`, `collection_key`, `selection_key`) and any name read by a custom `end_block` override in the subclass.
3. The remainder is dead config. Suggested fix: either implement a custom `end_block()` that uses the attribute, or remove it.

**Why it matters:** Combined with a wired transition, the dead attribute makes a reader assume mid-round side transitions exist (e.g. "withdrawal can interrupt this round") when they don't — leading to design decisions based on capabilities the FSM doesn't actually have.

### Test (T) — Test correctness and coverage

#### T1: `@classmethod @pytest.fixture` Anti-Pattern

**What:** Python 3.14 broke the `@classmethod @pytest.fixture` combination. Autouse fixtures using this pattern are silently not detected, causing test setup to be skipped entirely.

**Search pattern:** Grep for `@classmethod` immediately followed by `@pytest.fixture` in test files.

**Bug example:**
```python
class UseGanache:
    @classmethod
    @pytest.fixture(autouse=True, scope="class")
    def _start_ganache(cls, ganache_scope_class):  # NEVER CALLED in Python 3.14!
        cls.key_pairs = ganache_scope_class.key_pairs
```

**Correct:**
```python
class UseGanache:
    @pytest.fixture(autouse=True, scope="class")
    def _start_ganache(self, ganache_scope_class):
        cls = type(self)  # Get class from instance
        cls.key_pairs = ganache_scope_class.key_pairs
```

**Why it matters:** Tests pass vacuously because setup never runs. External services (Ganache, Tendermint, IPFS) are never started, so integration tests silently skip their actual verification.

#### T2: Wrong Base Test Class for Round Type

**What:** Each round collection type has a corresponding base test class. Using the wrong one means the test validates incorrect invariants.

**Mapping:**
| Round Type | Correct Test Base |
|---|---|
| `CollectSameUntilAllRound` | `BaseCollectSameUntilAllRoundTest` |
| `CollectSameUntilThresholdRound` | `BaseCollectSameUntilThresholdRoundTest` |
| `CollectDifferentUntilAllRound` | `BaseCollectDifferentUntilAllRoundTest` |
| `OnlyKeeperSendsRound` | `BaseOnlyKeeperSendsRoundTest` |
| `VotingRound` | `BaseVotingRoundTest` |

**How to check:** For each round test class, verify it inherits from the base test that matches the round's actual parent class.

**Why it matters:** A threshold round tested with an "until all" base class will pass even if the threshold logic is broken.

#### T3: Missing Required Test Class Attributes

**What:** Test base classes require specific attributes to be set by subclasses. Missing attributes cause silent failures or confusing errors.

**Round tests** (`BaseRoundTestClass` subclasses) require:
- `_synchronized_data_class` — must match the round's `synchronized_data_class`
- `_event_class` — must be the event enum used by the AbciApp

**Behaviour tests** (`FSMBehaviourBaseCase` subclasses) require:
- `path_to_skill` — must point to the skill package directory

**Specialized behaviour tests** require:
- `BaseRandomnessBehaviourTest`: `randomness_behaviour_class`, `next_behaviour_class`, `done_event`
- `BaseSelectKeeperBehaviourTest`: `select_keeper_behaviour_class`, `next_behaviour_class`, `done_event`

**Search pattern:** Find test classes inheriting from these bases and verify attributes are set.

#### T4: Missing `mock_a2a_transaction()` in Behaviour Tests

**What:** When a behaviour sends a payload via `send_a2a_transaction()`, the test must call `mock_a2a_transaction()` to complete the signing and broadcast flow. Without it, the round never receives the payload.

**The correct sequence:**
```python
self.behaviour.act_wrapper()       # Behaviour runs and sends payload
self.mock_a2a_transaction()        # Mock signing + HTTP broadcast
self._test_done_flag_set()         # Verify round completed
self.end_round(done_event)         # Transition to next round
```

**What `mock_a2a_transaction()` does internally:**
1. Mocks `SIGN_MESSAGE` → `SIGNED_MESSAGE` via signing handler
2. Mocks HTTP POST to broadcast transaction
3. Mocks HTTP GET to check transaction receipt

**Why it matters:** Missing this call means the behaviour test never actually completes the round, so transitions are never tested.

#### T5: Incomplete Round Event Testing

**What:** Each round type can emit multiple events. All possible events should have test coverage:

- `CollectSameUntilThresholdRound`: `done_event`, `none_event`, `no_majority_event`
- `OnlyKeeperSendsRound`: `done_event`, `fail_event`
- `VotingRound`: positive and negative outcomes
- Custom `end_block()` implementations: every distinct return event

**How to check:** For each round, collect all events from `transition_function` keys. For each event, verify there's a test that triggers it.

**Why it matters:** Untested event paths may contain bugs in the data they produce or transitions they trigger.

#### T6: `_MetaPayload.registry` Not Saved/Restored

**What:** `FSMBehaviourBaseCase.setup_class()` saves and clears `_MetaPayload.registry`, and `teardown_class()` restores it. Test classes that override these methods without calling `super()` corrupt the payload registry for subsequent tests.

**Search pattern:** Look for `setup_class` or `teardown_class` overrides in test files that don't call `super()`.

**Why it matters:** Corrupted registry causes payload deserialization failures in unrelated tests, leading to flaky CI.

### Low (L) — Code quality and maintainability

#### L1: Dead Code

**What:** Unused instance variables set in `__init__` or `setup()` but never read. Unreachable code after unconditional `return`/`raise`/`break`.

#### L2: Stale Imports and Unused Events

**What:** Imports that are no longer used. Event enum members with no references.

#### L3: Docstring / Transition Function Drift

**What:** Comments or docstrings describing the FSM that don't match the actual `transition_function` definition.

#### L4: Logging Hygiene (Secret / PII Leakage)

**What:** Behaviour and connection log lines that interpolate variables holding credentials, signed material, or full HTTP responses expose secrets to log aggregators and on-disk logs. Once a secret is in a log stream, it must be assumed compromised.

**Search patterns:**
- Variable name regex inside `logger.*(f"... {x} ..."`, `logger.*("... %s ...", x)`, `logger.*("... " + x)`:
  - `private_key`, `priv_key`, `pk`, `sk`, `secret`, `token`, `api_key`, `apikey`, `password`, `passphrase`, `bearer`, `mnemonic`, `seed`, `nonce` (when used as crypto material, not RPC nonce)
- Whole-object logging that may contain nested credentials:
  - `signed_order`, `signed_tx`, `signed_message`, `credentials`, `headers` (when headers contain `Authorization`)
  - `request`, `response` objects logged in full
- Full HTTP body / response logging that may include access tokens or PII

**Why it's L not C:** the agent doesn't crash and consensus isn't broken; it's a security-posture issue. Severity escalates if the leaked material grants production access.

**Fix:** redact / hash before logging; log only metadata (key prefix, length); log structured fields rather than entire objects.

#### L5: Numeric Precision in Financial Logic

**What:** Common precision footguns in code that touches token amounts, prices, or financial calculations:
- `float` arithmetic on token amounts (silent rounding accumulates over many trades)
- Mixing 6-decimal (USDC) and 18-decimal (most ERC-20) without explicit unit tracking
- `==` / `!=` between two values where at least one is a `float`
- Hardcoded float constants used in `int(... * 10**N)` conversions (exact bits of the float matter)
- Arithmetic on results of older Solidity calls without checking for negative / overflow

**Search patterns:**
- `float(` inside files that handle on-chain balances or token amounts
- Hardcoded float literals (e.g. `0.089935`) used in conversions
- `==` / `!=` between two values when at least one is provably `float`
- `Decimal` mixed with `float` in the same expression

**Bug example:**
```python
FALLBACK_POL_TO_USD_RATE = 0.089935  # binary float — not exactly 0.089935
amount_usd = pol_amount * FALLBACK_POL_TO_USD_RATE
amount_usd_wei = int(amount_usd * (10**18))  # rounding accumulates
```

**Fix:** use integer wei (or `Decimal` with explicit precision); track decimals via a typed wrapper; never compare floats with `==`.

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

### Dead timeouts or unused events in `test_*` skills
Skills whose directory name starts with `test_` (e.g. `test_abci`, `test_solana_tx_abci`, `test_ipfs_abci`) are **test/scaffold skills** — they exist to exercise and test the framework, not as production FSM apps. Patterns that look like bugs in production skills are often intentional in test skills:
- `event_to_timeout` entries for events not in any `transition_function` (C4) — may exist to test that `SharedState.setup()` correctly wires timeout values from params
- Unused event enum members (M2) — may exist to test event handling infrastructure
- Incomplete round event testing (T5) — test skills often have minimal test coverage by design

**When auditing test skills:** Note them in the report under a separate "Test/Scaffold Skills" section rather than as findings. Only flag issues in test skills if they would cause the test itself to fail or produce incorrect test results.

### Mutable class-level dicts/lists in `BaseBehaviour` subclasses
```python
class MyBehaviour(BaseBehaviour):
    local_params: Dict[str, Any] = {}
    collected_data: List[str] = []
```
**Why it's fine:** Behaviours are single-instance per agent. These class-level mutables are used as instance state and are typically reset at the start of `async_act()`. This is NOT the same as the `([],) * n` bug (C1) which creates shared references within a single data structure. Only flag this if you can demonstrate that stale state from a previous round cycle actually causes a bug.

---

## Scope Extensions

### Auditing `customs/` Strategies

`customs/` directories (e.g. `customs/kelly_criterion/`, `customs/fixed_bet/`) are loaded by IPFS hash at runtime via `FILE_HASH_TO_STRATEGIES` and execute logic that drives the FSM's financial actions (e.g. bet sizing). They are out of scope for `skills/`-only audits but receive zero coverage today.

**When to extend:** if the agent's `aea-config.yaml` or any `services/*/service.yaml` references `FILE_HASH_TO_STRATEGIES` (or a similarly named param mapping IPFS hashes to strategy modules), audit those strategy directories with a reduced checklist.

**Reduced checklist for `customs/` modules:**
- L4 (logging hygiene) — strategies often log inputs and intermediate values
- L5 (numeric precision) — strategies typically compute bet sizing, expected value, Kelly fraction, etc.
- M1-style: type contracts on entry/exit functions (what does the calling behaviour expect back?)
- Error handling: do strategy functions degrade gracefully or raise into the calling behaviour? An uncaught exception in a strategy crashes the calling behaviour (audit-resilience Category A).

**Skip:** FSM-only checks (C3, C4, M2, M3, M5, M7, M8, T*) — there is no FSM in a strategy.

### Auditing `service.yaml` Overrides

Both this skill and `audit-resilience` historically read package source only and miss runtime parameter overrides. If the audit scope is a service (not just a skill) and `services/*/service.yaml` exists:

1. Parse each service's `overrides` block. List every parameter override, its target skill, and the override value.
2. For overrides that change behaviour-controlling parameters (timeouts, retry counts, URLs, contract addresses, feature flags), flag if the override:
   - Changes the value type from the default declared in the skill's `models.py` (e.g. int default, string override)
   - Sets a value that conflicts with `db_pre_conditions` (e.g. an override that expects a key not provided by an upstream round)
   - Disables a safety mechanism present in defaults (retry count to 0, timeout to a very large value, `verify=False`)
3. When multiple `services/*/service.yaml` exist for the same agent (e.g. `trader_pearl/` vs `polymarket_trader/`), build a comparison table — drift between deployments is a footgun.
4. Note: env-var-driven overrides (`${OAR_API_KEY:str:dummy}`) hide values entirely. Flag any param marked sensitive (URL, key, address) that defaults to `dummy` / empty / placeholder — production deployments depend on the env var being set.

---

## Methodology Guardrails

These guardrails reduce false positives observed in prior audit runs. Apply them before flagging any finding.

### Verify every sub-agent finding before accepting it

The Step 2 Explore agents return **candidate** findings with **candidate** severities, not final ones. The spawning agent (you) MUST hand-verify each candidate against the source before promoting it into the report. Sub-agents over-report because they lack the cross-cutting view across the audit scope.

For each candidate finding from a sub-agent, before accepting:

1. **Read the cited `file:line` in the actual source.** Confirm the bug exists as described — not a misread of static type vs runtime type, not a paraphrase that drifts from the actual code, not a citation pointing at the wrong line.
2. **Confirm the bug is real.** Apply the data-type trace guardrail (below). Apply the framework-scheduled-event carve-out (below). Check the False Positive Guidance section.
3. **Re-evaluate severity.** Sub-agents systematically over-classify. Concretely:
   - "Unused / dead code" (initial-only attributes, dead comments, vestigial fields) is **almost always L**, not C. Critical requires runtime impact.
   - A misnamed-but-harmless attribute is **L**, not C. Promote only if you can demonstrate a runtime path that reads / writes through it incorrectly.
   - Configuration that "looks misleading" is **L** unless misleading the reader produced (or is highly likely to produce) a downstream bug.
4. **Consolidate split findings.** If three sub-agent findings point at one root cause (e.g. three separate Cs that all stem from one mis-typed `AgentDB` accessor), report ONCE at the appropriate severity, not three times.
5. **Demote liberally.** If you can't reproduce the sub-agent's reasoning from the source in under a minute, the finding is probably wrong — drop it or downgrade to L with an "informational" note.

Sub-agent classification is input, not output. The report is your judgment, not the union of subagent outputs.

### Force the data-type trace before flagging type mismatches

Many false positives in prior runs (M5 mismatches, T2 wrong-base-class claims, "non-existent payload field" claims) came from agents reasoning about **annotated** types instead of **runtime** types. In open-autonomy, payload fields and DB-backed properties are JSON-deserialized — the runtime type may differ from the annotation.

When a check requires reasoning about a value's runtime type, before flagging:

1. Locate the **last assignment** to the variable along the call path (do not stop at the type annotation).
2. If that assignment is `json.loads(some_field)`, `self.db.get_strict(key)`, or a `BaseTxPayload` field whose value was JSON-serialized at write time, the runtime type is whatever the JSON producer wrote — which may be `dict`, `list`, `str`, `int`. Static annotations alone are not authoritative here.
3. For framework-DB-backed properties, trace from `selection_key` → property body → any `json.loads(...)` to determine the actual runtime type.
4. Do NOT flag a type mismatch unless you can name **both** the expected type AND the actual runtime type with a `file:line` citation for each.

A concrete past failure: a discovery agent claimed `isinstance(actions_data, dict)` was dead because `synced_data.actions` was annotated `Optional[List[...]]`. The annotation was a stale guess; the runtime value came from `json.loads(content)` and could be either a dict or a list.

### Strip framework-scheduled events from `end_block` completeness checks

C3 explicitly carves these out (see C3 above). Repeating here as a guardrail because prior runs surfaced this false positive (a discovery agent flagged `Event.ROUND_TIMEOUT` as "missing from `CheckFundsRound.end_block()`" — `ROUND_TIMEOUT` is scheduled by the framework via `event_to_timeout`, not emitted by `end_block`).

Before flagging an event as missing from `end_block()`:
- If the event appears in `event_to_timeout` for the round, **skip it** — the framework schedules the transition.
- If the event appears in the round's transition function but is neither a base-class event (`done`, `none`, `no_majority`, `fail`) nor in `event_to_timeout`, then it is genuinely missing — flag it under C3.

### Single-finding-per-bug discipline

If two checks (e.g. C3 dead transition + M8 misleading attribute) flag the same underlying bug, report once with both check IDs cited, not twice.

---

## Coverage Limitations

This skill audits **FSM correctness and safety** in `skills/`. The following are explicitly NOT covered — the audit report should call this out so consumers know what they still need to do:

- **External request resilience** → run `audit-resilience` (companion skill).
- **Security review** → run `/security-review`. This skill does not audit private-key handling, env-var injection in `skill.yaml`, `eval` / `exec` patterns, unsafe deserialization (`pickle.loads`), or supply-chain risks.
- **Numeric precision in financial logic** is L5-checked at a syntactic level only; mathematical correctness of strategy logic is out of scope.
- **Dependency CVEs** → run `pip-audit` / `safety check` after this audit.
- **Smart-contract audit** → out of scope; covered by Solidity-specific tooling.
- **Performance / gas optimisation** → out of scope.

Include a "What this audit did not cover" section in every report.

---

## Analysis Procedure

Follow these steps in order:

### Step 0: Run Existing CLI Analysis Tools

Before manual inspection, run the framework's built-in analysis commands to catch structural issues automatically. Use the Bash tool to execute these:

```bash
# Validate FSM spec consistency (transition function vs docstring vs yaml spec)
# This is the ONLY tool that accepts a --package flag for scoped analysis
autonomy analyse fsm-specs --package <skill-path>

# These three run repo-wide (no package scoping available).
autonomy analyse handlers
autonomy analyse dialogues
autonomy analyse docstrings
```

**Critical — filter unscoped output against `dev` packages only.** `handlers` / `dialogues` / `docstrings` walk every package under `packages/`, including framework-vendored ones in the `third_party` section of `packages/packages.json`. Findings against `third_party` packages belong to the upstream repo, not this audit. The composition / cross-skill analysis later in the audit STILL needs full visibility into those packages — but their CLI-tool errors are out-of-scope as findings.

Build the dev set once and reuse it across all unscoped tools:

```bash
# Each entry is "<type>/<author>/<name>/<version>"; on-disk path is
# packages/<author>/<type>s/<name>
jq -r '.dev | keys[]' packages/packages.json
```

For each error line emitted by `handlers` / `dialogues` / `docstrings`, drop the line if the cited path resolves under a `third_party` package (i.e. its `<author>/<type>s/<name>` is not in the dev set). The remaining lines are in-scope findings. Note in the report how many lines were filtered and from which third-party paths, so the consumer can see what was dropped and why.

`fsm-specs` is already scoped — invoke it only on dev skills (and only on the `$ARGUMENTS` subset if provided).

These tools catch issues the manual audit does not need to duplicate:
- `fsm-specs` validates that the FSM spec file, the docstring, and the `transition_function` definition are all consistent (**scoped** to target skill — invoke per dev skill)
- `handlers` verifies required handlers are defined and properly configured (**repo-wide; filter output to dev**)
- `dialogues` verifies dialogue definitions match protocol specifications (**repo-wide; filter output to dev**)
- `docstrings` checks the AbciApp class docstring matches the actual state machine definition (**repo-wide; filter output to dev**)

**Include the (filtered) output of these tools in the report.** If any in-scope error remains, report it as a finding. Then proceed with the manual checks below, which cover semantic and logic issues these tools cannot detect — and which DO read across into library / `third_party` packages where composition requires it.

**Tooling-unavailable case.** If the CLI tools fail with `No module named 'packages.valory.skills.abstract_round_abci'` (or similar import errors), the local `packages/` tree is missing library skills that the project policy doesn't sync (some downstream repos forbid `autonomy packages sync --all` because it bypasses a curated dependency set). This is a project policy choice, not a bug. Note in the report: *"CLI tools could not run because library skills are not in the local tree; proceeded with manual checks."* Do NOT report this as a finding, and do NOT block the audit on it.

### Step 1: Discovery

Determine the scope of the audit:

```
# If $ARGUMENTS is provided, use those paths directly
# Otherwise, discover all skill directories:
Glob pattern: packages/**/skills/*/rounds.py
```

Build a list of skill directories to audit. Each skill directory should contain some subset of: `rounds.py`, `behaviours.py`, `payloads.py`, `models.py`, `__init__.py`, and a `tests/` subdirectory.

### Step 2: Parallel Analysis

Launch up to **3 parallel Explore agents**, dividing skills evenly among them. Each agent should:

1. **Read the key files** in each assigned skill:
   - `rounds.py` — AbciApp definition, round classes, transition function, events
   - `behaviours.py` — behaviour classes, matching_round links
   - `payloads.py` — payload definitions
   - `models.py` — if it exists, for parameter and data model definitions
   - `tests/test_rounds.py` — round test classes
   - `tests/test_behaviours.py` — behaviour test classes

2. **Run all checks from the Audit Checklist** (C1–C6, H1–H4, M1–M8, T1–T6, L1–L5)

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

## What This Audit Did Not Cover

- External-request resilience (run `/audit-resilience`)
- Security review of credential handling, env-var injection, unsafe deserialization (run `/security-review`)
- Mathematical correctness of strategy logic (only syntactic L5 checks were applied)
- Dependency CVEs (run `pip-audit` / `safety check`)
- Smart-contract audit, gas optimisation
- [Add any further scope exclusions specific to this audit run, e.g. "CLI tools could not run because library skills are not in the local tree"]
```

If no findings at a severity level, include the section header with "No findings." underneath.
