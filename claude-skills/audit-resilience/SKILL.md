---
name: audit-resilience
description: Audit all external HTTP requests in an open-autonomy agent service for resilience — failure modes, FSM propagation, crash/stuck/side-effect classification, and prioritized fix plan
argument-hint: "[path/to/skill or packages/]"
disable-model-invocation: false
---

# External Request Resilience Audit

You are an expert resilience auditor for **open-autonomy** agent services. Your job is to discover every external HTTP request the service makes, systematically test each failure mode, trace how failures propagate through the FSM, classify operational impact, and produce a prioritized fix plan.

Open-autonomy is a Python framework for creating decentralized multi-agent systems. Source and docs: https://github.com/valory-xyz/open-autonomy

## How to Use Arguments

- If `$ARGUMENTS` is provided, audit only those paths (e.g. `packages/valory/skills/decision_maker_abci`)
- If `$ARGUMENTS` is empty, discover and audit all skills, connections, and handlers under `packages/`
- Multiple paths can be space-separated

---

## Framework HTTP Architecture Reference

This section encodes the domain knowledge you need. Do NOT rely on external documentation — use this as your ground truth.

### Three HTTP Stacks

Open-autonomy services use three distinct HTTP stacks. You must identify which stack each external call uses, because error handling is completely different.

#### Stack 1: Framework path (`get_http_response` via `BaseBehaviour`)

Used by behaviours that call `yield from self.get_http_response(...)`.

- Returns an `HttpMessage` with `status_code`, `status_text`, `body`
- **Unreachable / DNS / timeout**: the HTTP client connection catches ALL exceptions and returns `status_code=600` with the traceback in `body`
- `ApiSpecs.process_response()` then attempts JSON parse on body:
  - **JSON decode error** → returns `None` (logs error)
  - **Key/index mismatch in response structure** → raises `UnexpectedResponseError` → caught → returns `None`
  - **Does NOT check status_code** — a 500 with valid JSON body will be parsed and keys extracted normally
- Common retry pattern via `_handle_response()` in querying behaviours:
  - `res is None` → increments retries, sleeps with `backoff_factor^retries_attempted`, sets `FetchStatus.FAIL` when retries exceeded
  - `res is not None` → resets retries, returns data
- **The sleep is cooperative** (`yield from self.sleep()`). The round timeout fires via Tendermint's `update_time()` on the next block. The timeout event transitions the FSM, but the sleeping behaviour continues until it yields — it just becomes irrelevant because the round has moved on.

#### Stack 2: Direct path (`requests.get` / `requests.post`)

Used by connections and handlers that import `requests` directly.

- **Unreachable / timeout / SSL**: `requests.exceptions.RequestException` raised
- **4xx/5xx**: must call `raise_for_status()` explicitly; otherwise status code is silently accepted
- **JSON decode on non-JSON body**: `response.json()` raises `requests.exceptions.JSONDecodeError` which is NOT a subclass of `RequestException` — it inherits from `ValueError`
- **Critical bug pattern**: code that catches `RequestException` will NOT catch `JSONDecodeError` from `response.json()`

#### Stack 3: Third-party library wrappers

Some connections use third-party API client libraries that wrap HTTP internally. **These are a major source of indefinite-hang bugs because the internal HTTP clients often have no timeout configured.**

Known libraries and their internals:
- **`py_clob_client`** (ClobClient): uses **`httpx`** (NOT `requests`). The module-level `httpx.Client(http2=True)` has **no timeout configured by default**. Raises `PolyApiException` on API errors, but also raises bare `Exception` on validation failures (e.g., invalid price/tick size). The httpx exception hierarchy is separate from requests — `httpx.RequestError` is NOT `requests.RequestException`.
- **`py_builder_relayer_client`** (RelayClient): uses **`requests`** internally. The internal `requests.request()` call has **no timeout configured by default**. Raises `RelayerApiException` (subclass of `RelayerClientException`).

You must trace through library source code to understand what exceptions can escape and whether timeouts are configured.

### HTTP Handler Dispatch

Check whether handlers are dispatched with or without try-catch wrapping. In many services:
- `handlers.py` dispatches to handler functions WITHOUT a global try-catch
- If a handler throws an unhandled exception, no HTTP response is sent to the client
- The client hangs until its own timeout
- The HTTP server connection typically has a response timeout (e.g. 5 seconds) that partially mitigates this

**Pre-FSM crashes:** Handlers can be called before the FSM has started (e.g., health checks from load balancers during initialization). Accessing `synchronized_data`, `shared_state`, or other FSM-dependent properties at this point raises `AttributeError`, `TypeError`, or `JSONDecodeError`. Any handler that accesses these without try-except is vulnerable.

### Exception Propagation in Behaviours

The framework's execution path for behaviours:

```
async_act() (generator) → __handle_tick() → async_act_wrapper()
```

**Critical:** `async_act_wrapper()` and `__handle_tick()` in `behaviour_utils.py` only catch `StopIteration`. Any other exception in a behaviour's generator **propagates uncaught and crashes the agent process**.

What happens after a behaviour crash:
1. The generator raises an exception that escapes `__handle_tick()`
2. **The agent process crashes.** The exception is fatal — it is NOT caught by the AEA framework.
3. The agent must be restarted externally (process supervisor, Docker restart policy, manual intervention).
4. If the root cause persists (e.g., an external API keeps returning bad data), the agent enters a **crash loop** — restarting and immediately crashing again upon reaching the same behaviour.

### BaseSyncConnection Threading Model

Synchronous connections (e.g., `PolymarketClientConnection`) use `BaseSyncConnection` which dispatches `on_send` via `_run_in_pool` into a `ThreadPoolExecutor`.

**Critical:** If `MAX_WORKER_THREADS = 1` (common pattern), only one request can be processed at a time. If a request handler blocks (hanging HTTP call with no timeout, or `time.sleep()` during retries), **ALL subsequent requests queue behind it**. The agent's FSM continues but cannot interact with that connection at all.

Additional threading details:
- `on_send()` runs in the pool thread. If it crashes (e.g., `json.loads` of a malformed SRR payload), the `_task_done_callback` logs the exception but **no response envelope is ever sent**. The skill behaviour waiting for the response will time out.
- The `_route_request()` dispatcher typically has a broad `except Exception` catch-all that converts any exception into an error response — this is the safety net for unhandled exceptions in request handlers. But code OUTSIDE `_route_request()` (e.g., payload deserialization in `on_send()`) is NOT protected.

### FSM Composition and Error Recovery

Understanding how errors propagate through composed FSMs:

- **Terminal/degenerate rounds** (e.g. `FailedMarketManagerRound`, `ImpossibleRound`) end the current period
- **`ImpossibleRound`**: A degenerate terminal state used as a defensive transition that "should never be reached." Reachable from rounds like `SamplingRound`, `BlacklistingRound`, `BenchmarkingRandomnessRound` via `FETCH_ERROR` or `NONE` events. Period timeout eventually fires and resets.
- **Reset flow**: typically `FailedRound` → `ResetAndPauseRound` → back to initial state. `ResetAndPauseRound` has its own timeout; if it also fails: `FinishedResetAndPauseErrorRound` → `ResetAndPauseRound` (loops).
- **Special timeouts**: Some rounds have domain-specific timeouts (e.g., `REDEEM_ROUND_TIMEOUT` of 3600s for redemption operations).
- **Cross-period persistence**: `cross_period_persisted_keys` determines what data survives a period reset
- Under sustained outage: the agent loops through periods without making progress (trading)

### Stale Data Preservation Pattern

Performance summary behaviours often implement a stale-data preservation pattern: before voting, the behaviour replaces N/A metrics with values from the previous successful fetch. This means:
- Metrics, agent_details, agent_performance, profit_over_time, and prediction_history are individually preserved if the new fetch failed but existing data exists
- Stale data is served to the UI even when subgraphs are down
- This is graceful degradation by design, but means the UI can show increasingly stale data without indication

### Background Thread Patterns

Some services run operations in background threads (e.g. `ThreadPoolExecutor`):
- These operations are NOT on the FSM path
- Blocking I/O in the executor blocks the thread pool, preventing other background tasks
- Does NOT block the main agent loop or FSM
- But can block HTTP handler responses if the handler submits work to the same executor
- **Deduplication risk**: `executor.submit()` returns a `Future`, but if the return value is discarded, there's no way to check if a task is already running. Multiple rapid requests can queue duplicate operations (e.g., duplicate swap transactions).

### Subgraph.process_response Override Pattern

Services often define a `Subgraph(ApiSpecs)` subclass that overrides `process_response` to check for The Graph-specific errors (e.g., "payment required"). This override pattern is a common source of crashes:
```python
error_message = error_data.get(error_message_key, None)
if payment_required_error in error_message:  # ← TypeError if error_message is None!
```
Always check that the override handles `None` error messages.

### Retry Strategy Patterns

Document every retry pattern you find. Common patterns in open-autonomy services:

| Pattern | Typical location | Mechanism |
|---------|-----------------|-----------|
| Framework exponential backoff | Querying behaviours | `backoff_factor^retries_attempted` via cooperative `yield from self.sleep()` |
| Connection linear backoff | Sync connections | `time.sleep(RETRY_DELAY * (attempt + 1))` — **blocks the connection thread** |
| Unbounded retry via condition loop | `wait_for_condition_with_sleep` | Loops until condition returns True or round timeout fires — **no max retry count** |
| No retry | Direct `requests.get` in handlers | Single attempt, failure returns None or raises |
| Library-internal retry | Third-party API clients | Varies — must trace through library code |

---

## Audit Procedure

### Step 0: Discovery — Find All External Requests

Use parallel Explore agents to find every external HTTP call in the codebase.

**Search patterns:**

```
# Framework HTTP path
Grep: get_http_response
Grep: ApiSpecs
Grep: process_response

# Direct requests path
Grep: requests\.get
Grep: requests\.post
Grep: requests\.put
Grep: requests\.delete
Grep: requests\.request
Grep: requests\.Session

# httpx path (used by some third-party libs)
Grep: httpx\.Client
Grep: httpx\.get
Grep: httpx\.post

# Web3 / RPC
Grep: Web3\(
Grep: HTTPProvider
Grep: w3\.eth\.
Grep: send_raw_transaction
Grep: wait_for_transaction_receipt

# Third-party API clients
Grep: ClobClient
Grep: RelayClient
Grep: PolyApi

# Connection dispatch
Grep: SrrMessage
Grep: _route_request
Grep: on_send

# Threading
Grep: ThreadPoolExecutor
Grep: executor\.submit
Grep: time\.sleep
Grep: MAX_WORKER_THREADS

# Generic URL patterns
Grep: BASE_URL|base_url|API_URL|api_url
Grep: https?://
```

For each external call found, record:
1. **URL / base URL** (hardcoded or configurable via params)
2. **HTTP method** (GET/POST)
3. **Called from** (file:line)
4. **Which HTTP stack** (framework, direct requests, or third-party library)
5. **Purpose** (what data it fetches/submits)
6. **Retry mechanism** (if any)

### Step 1: Deep Failure Analysis Per Endpoint

For EACH external request discovered, analyze these failure modes:

#### HTTP Error Codes
- **5xx (500, 502, 503)**: Server errors, most common during outages
- **429**: Rate limiting — does the code handle this differently?
- **403/401**: Auth failures — are API keys involved?
- **404**: Resource not found — is this treated as "no data" or as an error?

#### Network Failures
- **Unreachable / DNS failure**: What exception is raised? Is it caught?
- **Timeout**: Is a timeout configured? What happens when it fires?
- **SSL errors**: Certificate issues, MITM detection

#### Malformed Responses (200 OK but bad data)
- **Non-JSON body** (HTML error page from CDN/proxy): Does `response.json()` / `json.loads()` crash?
- **`{}` (empty object)**: Do subsequent `.get()` calls return sensible defaults?
- **`{"data": null}`**: The `.get("data", {})` pattern returns `None` (not `{}`!) when the value is explicitly `null`. Does the code use an `or {}` guard?
- **`{"data": {"expected_key": null}}`**: Explicit null values vs missing keys
- **Unexpected schema** (new/removed fields): Are fields accessed with `.get()` or direct `["key"]`?
- **Empty array where list expected**: `[]` vs `None` vs missing key
- **Binary/gzipped body**: Can `response.body.decode()` or `response.text` crash?
- **Truncated JSON**: Proxy/CDN may cut response mid-stream

#### Interaction with Retries
- Does the retry logic catch the right exceptions?
- Can retries cause the behaviour to exceed the round timeout?
- Calculate worst-case blocking time: `sum of all retry delays + request timeouts`
- Does the retry sleep block a shared thread?

### Step 2: FSM Impact Tracing

For each failure path identified in Step 1, trace what happens to the FSM:

1. **Immediate effect**: What does the calling function return on failure?
2. **Behaviour effect**: Does the behaviour send a payload? What payload value?
3. **Round effect**: What event does the round emit? (`done_event`, `none_event`, `no_majority_event`, timeout)
4. **Transition**: Where does the FSM go? Is it a terminal state? Check `ImpossibleRound` and other degenerate states.
5. **Recovery**: How does the agent recover? How long until it resumes normal operation?
6. **Stale data**: Is previous successful data preserved and served to the UI?

Document the trace as a chain:
```
API returns 500 → _fetch_data() returns None → behaviour sends payload=None
→ CollectSameUntilThresholdRound fires none_event=Event.FETCH_ERROR
→ FailedRound (terminal) → ResetAndPauseRound → back to initial state
→ Next period: retries from scratch
```

Also check the composed FSM transitions in `composition.py` — terminal rounds in one skill may map to different states in the composed app.

### Step 3: Operational Impact Classification

Classify every failure path into exactly one of three categories:

#### Category A: CRASHES the agent

Any unhandled exception in a behaviour generator or connection thread.

**Identification checklist:**
- Is the exception type caught by the surrounding try-except? (Check exception hierarchy carefully)
- Is `JSONDecodeError` (a `ValueError`) caught when only `RequestException` is in the except clause?
- Is `KeyError` from dict access caught?
- Is `AttributeError` from None-dereference caught?
- Is `UnicodeDecodeError` from `.decode()` caught?
- Is `TypeError` from operating on None caught? (e.g., `"string" in None`)
- Does the `Subgraph.process_response` override handle `None` error messages?
- Does the broad `except Exception` that catches it also mask other bugs?
- Can handlers crash before the FSM starts (pre-FSM property access)?

**For each crash path, determine:**
- Is this a behaviour crash (fatal — kills the agent process) or a connection thread crash (may be recoverable)?
- How common is the trigger? (CDN outage = common, binary garbage = rare)
- Will the agent crash-loop on restart if the root cause persists?

#### Category B: Gets the agent STUCK

The agent process is alive but unable to make progress.

**Identification checklist:**
- Can a `time.sleep()` in a synchronous connection block message processing?
- Can retry backoff exceed the round timeout?
- Can a background thread block waiting for I/O? Is the thread pool shared?
- Can the FSM enter a loop (reset → retry → fail → reset)?
- Are there any `thread.join()` without timeout?
- Is `wait_for_transaction_receipt()` called without timeout?
- Do third-party library HTTP clients have timeout configured? (Check httpx.Client AND requests internally)
- Is `MAX_WORKER_THREADS=1`? Can a single blocking call stall all operations for that connection?
- Is `json.loads` of inbound payloads outside the `_route_request` try-except?

**For each stuck path, determine:**
- Duration: how long is the agent stuck?
- Scope: does it block only one subsystem, or the entire agent?
- Recovery: automatic (timeout fires) or requires restart?

#### Category C: Runs with UNINTENDED SIDE-EFFECTS

The most insidious category. The agent appears healthy but makes wrong decisions or serves wrong data.

**Identification checklist:**
- Are there hardcoded fallback values that go stale over time? (exchange rates, gas prices)
- Does a function return a wrong value instead of None on error? (e.g., `next(..., list[0])` instead of `next(..., None)`, or `return False` where `return None` is expected)
- When a partial failure occurs, does the agent trade on a subset of data without awareness? (e.g., partial category fetch → concentration risk)
- Are UI endpoints serving stale cached data without indicating staleness? (Check the stale-data preservation pattern)
- Can missing enrichment data (probabilities, confidence scores) default to 0 instead of None?
- Is there a gap between a state change (trade placed) and its recording (bets.json updated) where a crash could cause duplicate actions?
- Can duplicate tasks be queued in a ThreadPoolExecutor without deduplication? (e.g., duplicate swap transactions)

**For each side-effect, determine:**
- Does it affect trading decisions? (direct financial impact)
- Does it affect only the UI? (user-facing but not financial)
- Is there a mitigation in place? (deduplication, validation, on-chain checks)
- Does the side-effect compound over time? (stale rates diverge further from reality)

---

## Bug Patterns to Watch For

These are proven bug patterns discovered in open-autonomy services. Check for each one proactively.

### BP1: `JSONDecodeError` not caught alongside `RequestException`

```python
# BUG: JSONDecodeError is a ValueError, not RequestException
try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()  # ← JSONDecodeError escapes!
except RequestException as e:
    # Only catches network/HTTP errors, not JSON parse errors
```

**Fix:** `except (RequestException, ValueError)` or `except Exception`

### BP2: `{"data": null}` vs `{"data": {}}` — missing `or {}` guard

```python
# BUG: .get("data", {}) returns None when value is explicitly null
data = response_json.get("data", {})  # Returns None, not {}!
items = data.get("items", [])  # AttributeError: 'NoneType' has no attribute 'get'
```

**Fix:** `data = response_json.get("data", {}) or {}`

### BP3: Wrong fallback in `next()` iteration

```python
# BUG: Returns WRONG item instead of None when target not found
result = next((item for item in items if item["id"] == target_id), items[0])
```

**Fix:** `next(..., None)`

### BP4: `if not value` is True for zero

```python
# BUG: Treats 0 as missing
price = data.get("usd")
if not price:  # True when price == 0!
    price = FALLBACK_PRICE
```

**Fix:** `if price is None:`

### BP5: `UnicodeDecodeError` on binary response body

```python
# BUG: .decode() can fail on binary/gzipped data
decoded = response.body.decode()  # UnicodeDecodeError
data = json.loads(decoded)
```

**Fix:** Wrap in try-except or use `response.body.decode(errors="replace")`

### BP6: `KeyError` on assumed dict keys

```python
# BUG: Direct key access without .get()
timestamp = int(stat["date"])  # KeyError if "date" missing
answer_hex = answer["answer"][2:]  # KeyError if "answer" missing
nested = answer["question"]["questionId"]  # KeyError at any level
```

**Fix:** `stat.get("date")` with fallback or skip. For nested access, validate at each level.

### BP7: Stale hardcoded fallback values

```python
FALLBACK_RATE = 0.089935  # From 2026-02-11 — goes stale over time
```

**Fix:** Add timestamp tracking; refuse to use fallback older than N hours; add monitoring

### BP8: Thread blocking without timeout

```python
# BUG: Blocks thread for up to 60 seconds
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
```

Also check for **no timeout at all** in third-party libraries:
```python
# BUG: httpx.Client with no timeout — blocks indefinitely
client = httpx.Client(http2=True)  # No timeout!
# BUG: requests.request with no timeout — blocks indefinitely
response = requests.request("POST", url, json=data)  # No timeout!
```

**Fix:** Use shorter timeout, or run in a separate thread pool. For third-party libraries where you can't modify the source: wrap calls with `concurrent.futures.ThreadPoolExecutor` + `future.result(timeout=N)` to enforce a deadline at the calling layer, or set environment variables if the library respects them (e.g. `HTTPX_DEFAULT_TIMEOUT`). Check `pyproject.toml` to determine if a dependency is third-party (pinned version, installed via pip) vs internal (editable, in-repo).

### BP9: Retry backoff exceeding round timeout

```python
# Total sleep: 1+2+4+8+16+32 = 63 seconds
# Round timeout: 30 seconds
# The behaviour sleeps past the round timeout!
sleep_time = backoff_factor ** retries_attempted
```

**Fix:** Cap total retry time to fraction of round timeout, or make retries aware of remaining time

### BP10: Handler dispatch without global try-catch

```python
# BUG: If handler raises, no HTTP response is sent, client hangs
handler = self._handlers.get(path)
response = handler(request, dialogue, **kwargs)  # No try-except!
```

**Fix:** Wrap dispatch in try-except that returns HTTP 500

### BP11: Return type mismatch (`False` instead of `None`)

```python
# BUG: Returns False where Optional[int] is expected
def _estimate_gas(...) -> Optional[int]:
    if not w3:
        return False  # Should be None!

# Caller checks: if tx_gas is None: skip
# False is not None → passes through → tx_data["gas"] = False → crash
```

**Fix:** Ensure error returns match the declared return type.

### BP12: No deduplication of executor-submitted tasks

```python
# BUG: Every request submits a new task, no check if one is running
def _handle_request(self, ...):
    self.executor.submit(self._expensive_operation)  # Future discarded!
```

**Fix:** Track the Future; check `future.running()` or use a flag with `threading.Lock`.

### BP13: `TypeError` from `in` operator on `None`

```python
# BUG: Subgraph.process_response override
error_message = error_data.get(error_message_key, None)
if "payment required" in error_message:  # TypeError if error_message is None!
```

**Fix:** Add `if error_message is not None:` guard before the `in` check.

### BP14: Connection payload deserialization outside `_route_request`

```python
# BUG: json.loads outside the _route_request try-except
payload = json.loads(srr_message.payload)  # JSONDecodeError escapes on_send!
response, error = self._route_request(payload=payload)
```

**Fix:** Move deserialization inside `_route_request` or add try-except in `on_send`.

---

## Cross-cutting Issues to Check

After analyzing individual endpoints, check for these systemic patterns:

### CC1: Inconsistent retry strategies
Document every retry mechanism in the codebase and note inconsistencies. Create a table:
| Call site | Retries | Backoff type | Max wait | Timeout param |

Pay special attention to inverted priorities: if critical financial operations (bet placement, position redemption) have zero retries and no timeout while market data queries have 3 retries with 60s blocking, flag this.

### CC2: No circuit breaker
Failed services retried every period under sustained outage → log noise, wasted latency, behaviours spending round timeout sleeping through retries. No backoff between periods.

### CC3: Inconsistent error reporting
Some failures log at WARNING, some at ERROR, some silently return None. No structured error tracking or metrics.

### CC4: Stale cached/fallback data
Identify all fallback values, cached rates, and preserved stale data. How old can each one get? What's the drift impact? Include the stale-data preservation pattern in performance summaries.

### CC5: Missing `timeout` on requests
Every `requests.get()` / `requests.post()` without a `timeout=` parameter can hang indefinitely. Also check httpx clients and Web3 HTTPProvider.

### CC6: Thread safety
If multiple threads access shared state (e.g., a cached price dict), are there race conditions? Note: `MAX_WORKER_THREADS=1` prevents races within a single connection, but executor task deduplication is still an issue.

### CC7: `{"data": null}` vs `{"data": {}}` inconsistency
Check if `.get("data", {})` patterns consistently use `or {}` guards. Inconsistent application means some code paths crash on null values while others handle them.

---

## Analysis Procedure

### Step A: Run Discovery

Launch up to 3 parallel Explore agents to find all external requests. Divide the codebase:
- Agent 1: All `skills/` directories
- Agent 2: All `connections/` directories
- Agent 3: All `handlers.py` files + `models.py` (for URL configurations)

Each agent should search using the patterns from Step 0 and return a structured list of all external calls found.

### Step B: Deep Analysis

For each external endpoint discovered, launch analysis agents (up to 3 in parallel). Each agent:
1. Reads the call site and all surrounding context
2. Traces the exception handling path from the call to the top-level handler
3. Fills in the failure matrix for all failure modes (Step 1)
4. Traces FSM impact (Step 2) — including composed FSM transitions in `composition.py`
5. Classifies operational impact (Step 3)
6. Checks for all bug patterns (BP1–BP14)

### Step C: Cross-cutting Analysis

After all endpoints are analyzed:
1. Build the retry strategy comparison table (CC1)
2. Check for circuit breaker patterns (CC2)
3. Audit error logging consistency (CC3)
4. Catalog all fallback/cached values (CC4)
5. Grep for `requests.get|post` without `timeout=` (CC5)
6. Check httpx clients and Web3 HTTPProvider for missing timeouts (CC5)
7. Check shared state access patterns (CC6)
8. Check `{"data": null}` guard consistency (CC7)

### Step D: Generate Report

Merge all findings into the output document.

---

## Output Format

Generate a markdown document with this structure:

```markdown
# External Request Resilience Audit

Deep analysis of every external HTTP dependency: what happens under each failure mode
(HTTP errors, unreachable, malformed data, empty 200s) and how failures propagate through the FSM.

---

## How the framework handles HTTP

[Document all HTTP stacks as they apply to this specific service, including handler dispatch and threading model]

---

## [N]. [Service/API Name]

| | |
|---|---|
| **Base URL** | [URL or "Configurable via `param_name`"] |
| **Endpoints** | [List of endpoints called] |
| **Called from** | [file:line references] |
| **Method** | GET/POST |
| **Purpose** | [What data it fetches/submits] |

### Failure matrix

| Failure mode | [Call site 1] | [Call site 2] | ... |
|---|---|---|---|
| **HTTP 500** | [behavior] | [behavior] | |
| **HTTP 429 / 403 / 404** | | | |
| **Unreachable / DNS / timeout** | | | |
| **200 but non-JSON body** | | | |
| **200 but `{}`** | | | |
| **200 but `{"data": null}`** | | | |
| **200 but unexpected keys** | | | |

### FSM impact

[Trace the failure through the FSM with chain notation, including composed FSM transitions]

### Bugs found

[List with severity, location, description]

---

[Repeat for each service/API]

---

## Summary: All Bugs Found

| # | Severity | Location | Bug |
|---|----------|----------|-----|
| 1 | **HIGH** | `file.py:line` | Description |

---

## Summary: Severity Classification

| Severity | Service | Failure Impact | FSM Outcome |
|----------|---------|----------------|-------------|

---

## Cross-cutting Issues

### 1. [Issue title]
[Description with evidence]

### 2. [Issue title]
...

---

## Operational Impact Classification

### A. What can CRASH the agent

[Table with trigger, where exception escapes, how external failure causes it]

**What happens after a behaviour crash:**
[Numbered recovery sequence]

**Net assessment:** [Which crash is most likely and impactful]

---

### B. What can get the agent STUCK

[Table with trigger, mechanism, duration, recovery]

**Net assessment:** [Which stuck scenario is most impactful]

---

### C. Agent keeps running with UNINTENDED SIDE-EFFECTS

[Table with trigger, side-effect, severity, trading impact]

**Net assessment:** [Which side-effect is highest risk]

---

## Combined Priority Matrix

| Priority | Issue | Category | Fix complexity | Fix description |
|----------|-------|----------|----------------|-----------------|
| **P0** | [Agent crashes] | Crash | Low/Med/High | [Specific fix] |
| **P1** | [Financial impact side-effects] | Side-effect | | |
| **P2** | [Important bugs] | Various | | |
| **P3** | [Systemic improvements] | All | | |
| **P4** | [Low-impact fixes] | Various | | |
```

### Priority Assignment Rules

- **P0**: Any unhandled exception that crashes the agent or a critical connection thread. Also: indefinite thread blocking with no timeout (requires agent restart).
- **P1**: Side-effects with direct or indirect financial impact (wrong calculations, stale rates affecting decisions, duplicate transactions)
- **P2**: Bugs that return wrong data, silent failures that mask problems, stuck states > 60s
- **P3**: Systemic improvements (circuit breakers, retry standardization, monitoring), concentration risk
- **P4**: UI-only issues, cosmetic data errors, low-probability triggers

---

## Quality Checklist

Before finalizing the report, verify:

- [ ] Every external URL/endpoint in the codebase is accounted for
- [ ] Every failure mode (HTTP error, unreachable, malformed, empty) is analyzed for each endpoint
- [ ] Every failure path is traced through to the FSM outcome (including composed FSM)
- [ ] Every unhandled exception path is identified (check exception hierarchies carefully!)
- [ ] The `JSONDecodeError` vs `RequestException` distinction is checked everywhere `response.json()` is called in a `RequestException` except block
- [ ] The `{"data": null}` pattern is checked everywhere `.get("data", {})` is used
- [ ] The `Subgraph.process_response` override is checked for `None` error message handling
- [ ] All fallback/cached values are cataloged with their staleness risk
- [ ] All retry strategies are documented and compared
- [ ] Thread blocking and timeout risks are documented (including third-party library internals)
- [ ] Third-party httpx/requests clients are checked for missing timeouts
- [ ] `MAX_WORKER_THREADS` and executor deduplication risks are documented
- [ ] Pre-FSM handler crashes are checked (accessing synchronized_data before FSM starts)
- [ ] Connection `on_send` payload deserialization is checked for exception handling
- [ ] The crash/stuck/side-effect classification is complete
- [ ] The priority matrix covers every finding
- [ ] Each fix description is specific enough to implement directly
