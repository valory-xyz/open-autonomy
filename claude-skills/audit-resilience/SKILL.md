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

#### Canonical: `MAX_WORKER_THREADS=1` + no-timeout call = subsystem outage

This is the single most common indefinite-hang shape in open-autonomy connections. Every reference elsewhere in this skill (BP8, the priority rules, the quality checklist, the Step 3 stuck identification) points back here:

> If `MAX_WORKER_THREADS = 1` (common pattern), only one request can be processed at a time. If a request handler blocks — hanging HTTP call with no timeout, `time.sleep()` during retries, third-party library that wraps HTTP without timeout configured (`httpx.Client(http2=True)`, internal `requests.request(...)` calls in vendor SDKs) — **ALL subsequent requests queue behind it**. The agent's FSM continues but cannot interact with that connection at all. Recovery requires an agent restart.

When you see any of these in combination, treat it as the canonical pattern: `MAX_WORKER_THREADS=1` + a call site that can hang + no enforcement timeout at the calling layer.

#### Additional threading details

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
- Does this match the canonical `MAX_WORKER_THREADS=1` + indefinite-hang call pattern? (See architecture reference and BP8.) Includes third-party HTTP client wrappers without internal timeouts (`httpx.Client`, internal `requests.request`).
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

A call site that can block for longer than the calling round's `round_timeout` (or, in single-worker connections, longer than any operator-tolerated outage window). Two flavours:

```python
# BUG: long timeout on Web3 — blocks the thread for up to 60s
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
```

```python
# BUG: no timeout at all — third-party SDKs that wrap requests / httpx
# without configuring a timeout block indefinitely. Common cases:
#   - py_clob_client → httpx.Client(http2=True)   no timeout
#   - py_builder_relayer_client → requests.request(...) no timeout
```

**See the canonical statement** in the "BaseSyncConnection Threading Model" architecture reference for why `MAX_WORKER_THREADS=1` + any indefinite-hang call site = subsystem outage. BP8 is the actionable check; that section explains the mechanism.

**Fix:** use a short timeout where the API supports one. Where you can't modify the third-party source, enforce a deadline at the calling layer with `concurrent.futures.ThreadPoolExecutor` + `future.result(timeout=N)`, or set library-respected env vars (e.g. `HTTPX_DEFAULT_TIMEOUT`). Check `pyproject.toml` to decide whether the dep is editable / in-repo (you can patch it) vs pinned third-party (you must wrap).

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

### BP15: Idempotency on Retry of Financial Actions

**The single biggest gap in resilience review for trading services.** BP8 / BP9 flag blocking timeouts. BP15 asks the harder question: *if this call retries — at the connection layer OR via FSM round re-entry — can it duplicate a financial action?*

The pattern: a connection-layer call to a non-idempotent endpoint (place order, redeem, set approval, transfer, swap) returns an error or times out **after** the upstream has accepted the request. The agent's behaviour sees the failure, the round eventually times out, the FSM transitions to a retry path, and the next period re-enters the same call site. Two side-effects on the upstream from one logical action.

Even if the connection itself does not retry, the **FSM retries the entire round** on its own timeout. CLOB nonces, on-chain nonces, and Safe nonces protect *some* of this — but the audit must flag the *pattern* and verify the dedup mechanism per call site.

**How to check, per non-idempotent POST / state-changing call:**

1. **Identify the call site and the calling round.** Grep for `requests.post`, `httpx.post`, third-party client `.execute() / .post_order() / .submit_*()`, contract `.transact()`, etc.
2. **Determine whether the round can re-enter the call after its timeout fires.** Walk the `transition_function`: does the round timeout path eventually loop back to this round?
3. **Document the dedup mechanism** at this call site:
   - **On-chain nonce / sequence number** (CLOB nonce, Safe nonce, ETH transaction nonce, sequencer-enforced ordering) — usually safe; verify the nonce is actually included in the signed payload.
   - **Idempotency key in request payload** (`Idempotency-Key` header, `client_order_id`, `request_id`) — safe **if the upstream honours it** (check the API docs / library source).
   - **On-chain check before submit** (read state, then write only if not already done) — TOCTOU-prone but generally acceptable.
   - **None of the above** — flag as **P1** (financial impact). The bug is that two independent attempts on a flaky network produce two upstream side-effects.
4. **For relayer / exchange APIs**, check the upstream contract: does the API guarantee idempotency, or is dedup the client's responsibility?

**Bug example:**
```python
# polymarket_client/connection.py — bet placement, no idempotency key
def _place_bet(self, order_args):
    signed = self._client.create_order(order_args)
    response = self._client.post_order(signed)  # ← network error after upstream accepts
    # No idempotency key, no on-chain dedup — FSM retries this round → duplicate order
```

**Why it matters:** Direct financial impact. A 1-in-1000 transient network blip, taken across a busy trading service, produces a duplicate order roughly daily.

### BP16: Stringified-Exception Retry Conditions

```python
# BUG: retry decision based on substring match of exception message
try:
    return self._client.do_thing()
except Exception as e:
    if "rate limit exceeded" not in str(e).lower():
        raise
    # else retry
```

Two failure modes:
1. **Upstream message format changes** → the substring no longer matches → retry silently stops working (the retry path becomes dead code with no test coverage).
2. **Unrelated exception** whose `str()` happens to contain the substring → retries inappropriately on a non-transient error (e.g. an auth failure with the word "exceeded" in it).

**Search pattern (inside `except` blocks):**
- `in str(e)`, `in repr(e)`, `in str(exception)`, `in str(exc)`
- `e.args[0] ==`, `e.message ==`, `f"{e}".lower()`

**Fix:** prefer `isinstance(e, SpecificError)`; check `response.status_code` on the response; use library-provided exception types where available (`RateLimitError`, `httpx.HTTPStatusError`, etc.).

### BP17: Defined-but-Unenforced Security Allowlists

```python
class _Connection:
    _ALLOWED_METHODS = {"get_user", "post_event"}     # actually enforced via dispatch
    _VALID_ENDPOINTS = {re.compile(r"/v1/[a-z]+/?$")}  # ← never referenced!
```

A class-level constant whose name implies enforcement but is never actually consulted. Looks like security config; isn't. Often shows up alongside a real allowlist that *is* enforced — the dead one gives a false sense of defence-in-depth.

**Search pattern:** enumerate class-level constants whose name contains `VALID|ALLOWED|PERMITTED|DENY|BLOCK|WHITELIST|BLACKLIST|FORBIDDEN`. For each, grep the class body (and any subclass) for references. Unreferenced → finding.

**Fix:** wire the allowlist into the dispatch path, or remove it.

### BP18: Inverted Fail-Safe on Unknown State

```python
# BUG: external check returned "unknown" → assumed optimistic outcome
balance = self._check_balance(...)  # returns None on RPC failure
if balance is None:
    self.context.logger.warning("Could not check balance, skipping")
    state.sufficient_funds = True   # ← optimistic default
    return True
```

The external dependency returned "unknown" (RPC down, response malformed). The handler claims the optimistic outcome — funds OK — and downstream code proceeds to spend funds it never verified existed. The observability gap (RPC down) silently becomes a financial-action error (failed payment, failed swap, failed deposit) at the gateway / counterparty.

**Search pattern:** `if X is None:` or `if not X:` followed within a few lines by an assignment that sets a state flag to `True` or a permissive default, where `X` was assigned from a fallible external call. Particularly suspicious when the comment says "skipping" — that often signals the author chose the optimistic path on purpose.

**Fix:** invert to the conservative outcome (`sufficient_funds = False`, `proceed = False`); OR model an explicit third state (`enum: Sufficient | Insufficient | Unknown`) so callers can distinguish "unable to check" from "checked and OK".

**Why it matters:** This pattern silently turns an upstream observability gap into a downstream financial error. The agent appears healthy; the failure surfaces at the counterparty side, with no audit trail upstream.

### BP19: TLS Verification Disabled / Hardcoded Credentials

Grep-level checks. Each finding is independent; flag every match.

- **`verify=False`** on `requests.*` / `httpx.*` / `aiohttp.*` — disables TLS certificate verification, opens MITM. Search: `verify=False`, `verify = False`, `ssl=False`, `ssl_context=None` in HTTP-call sites.
- **API keys / tokens hardcoded as string literals** — search for assignment patterns: `api_key\s*=\s*"`, `token\s*=\s*"`, `secret\s*=\s*"`, `Bearer ` literal. Cross-reference against `.gitleaks` output if available.
- **Secrets in URL query strings** — `?apikey=`, `?token=`, `?api_key=`, `?key=` — these end up in HTTP server logs, proxy logs, and browser histories. Headers are safer.
- **`set_api_creds` failure paths** — when credential setup can fail (e.g. `client.create_or_derive_api_key()`), is the connection gracefully marked unusable, or does it silently allow unauthenticated traffic? Trace from the credential-setup call to the first request.

**Fix:** never disable TLS in production code; load secrets from env vars or a secrets manager; pass via headers; fail closed on credential-setup error.

### BP20: Pagination Partial-Failure Semantics

```python
# Typical paginator
results = []
page = 0
while True:
    resp, err = self._fetch_page(page)
    if err is not None:
        return None, err   # ← partial accumulation discarded
    if not resp:
        break
    results.extend(resp)
    page += 1
return results, None
```

A `while True:` paginator that fetches pages 1..N and accumulates. If page 5 fails (5xx or timeout), the typical pattern returns `None, error` and the partially accumulated list is discarded. Whether this is *correct* depends entirely on the caller's contract — and that contract is rarely documented.

**How to check, per paginated fetch:**
1. Identify the loop and the accumulator variable.
2. Locate the failure return path — does it return the partial list, an empty list, `None`, or raise?
3. Identify all callers and ask: do they treat partial as "no data," pass-through, or expect "all-or-nothing"?
4. Flag mismatches: caller assumes complete data, paginator returns partial; or caller wants partial, paginator drops it.

**Fix:** make the contract explicit at the function signature level — return type `Tuple[List, Optional[Error]]` for partial-OK, or raise / return `(None, error)` for all-or-nothing. Document at the call site.

### BP21: Response Size Bounds

External calls that can return arbitrarily large responses are a memory and latency footgun:

- **Subgraph queries with no `first:` / `limit:` / `skip:` clause** — The Graph defaults can return thousands of records.
- **Iterating an unbounded list from an external source** in memory (e.g. `mech_responses` loop, full chat history fetch).
- **Streaming binary responses through `response.body.decode()` or `response.text` without size check** — covered partly by BP5 for malformed bytes; BP21 is the *size* dimension, not the encoding dimension.
- **`requests.get(...).content`** with no `stream=True` and no max-size guard — entire body loaded into memory.

**Fix:** enforce size limits at the call site (`len(response.content) > MAX_BYTES`); chunk via pagination with explicit page-size; reject responses > N bytes; for subgraph, always specify `first: 1000` (or appropriate cap).

### BP22: Clock-Window-Signed Requests

Signed orders, EIP-712 typed data, relayer transactions, and many exchange APIs include a **timestamp** plus an **expiry window**. Two failure modes:

1. **Agent clock drift vs upstream** — if the agent's wall clock is more than the expiry window off, every signed request fails signature verification. Drift can be invisible until NTP misconfigures.
2. **Multi-agent timestamp divergence** — in a multi-agent service, agents that build the same payload independently see different `time.time()` values. The aggregated payload is rejected for one set of agents and accepted for another, partitioning consensus.

**How to check:**
1. Find call sites that build a signed payload for an external counterparty: relayer / exchange POSTs, EIP-712 messages, signed orders.
2. Inspect how the payload's `timestamp` / `nonce` / `expiry` is computed.
   - `time.time()` / `datetime.now()` → drift-prone, **NOT consensus-safe** in a multi-agent service.
   - `self.context.state.round_sequence.last_round_transition_timestamp` (a property on `RoundSequence`, NOT on `BaseSynchronizedData` — it is the agreed Tendermint block time of the last transition) → consensus-safe.
   - A timestamp field written into a payload by a predecessor round and read via `synchronized_data` → consensus-safe.
3. Verify the agent's NTP / clock-sync mechanism if `time.time()` is used. Document the deployment expectation.

**Note:** this intersects with `audit-fsm` C5 (determinism in `end_block`). A timestamp produced in `end_block` must come from `synchronized_data`, not `time.time()`.

### BP23: `MagicMock` Without `spec=` Hides Production-Only Bugs

A meta-resilience pattern: tests pass, prod crashes. `MagicMock(...)` (and `Mock(...)`, `AsyncMock(...)`) without a `spec=` / `spec_set=` argument auto-vivifies any attribute access — `mock.foo`, `mock.bar.baz`, `mock.does_not_exist()` all succeed and return fresh MagicMocks. When a test mocks an HTTP response, an SDK client, or a connection object, **missing-attribute or attribute-rename bugs in the production code path silently pass tests** because the mock obligingly provides whatever the production code asks for.

Bug shapes this hides:
- Production code reads `response.body` but the test sets `MagicMock(text="...")`. In the real call site, `response.body` is bytes that need decoding; the mock test never exercises the `.decode()` failure.
- Production code's accessor was renamed (`.text` → `.json()`); tests still pass `MagicMock(text="...")` and don't notice. Or vice versa.
- Production code accesses a method that no longer exists on the upstream library — mock provides it anyway.

Concrete past finding: an `AgentDB` connection's `response.text` access bug went undetected because tests used `MagicMock(text="...")` — without `spec=`, missing-attribute failures silently succeeded in tests.

**Search pattern (in `tests/` directories within audit scope):**
- `MagicMock(`, `Mock(`, `AsyncMock(` calls used to substitute for HTTP responses, SDK clients, or connection objects
- `mocker.patch(...)` / `mocker.patch.object(...)` whose `return_value` is unspecced
- Any `Mock` whose attributes are populated only via `mock.foo = ...` post-hoc (no `spec=`)

For each, verify a `spec=ClassName` (or `spec_set=ClassName`) argument is present. If not, flag the test as a candidate false-negative.

**Bug example:**
```python
# BUG: any attribute access on this mock succeeds; missing attributes return MagicMocks
mock_response = MagicMock(text="ok", status_code=200)
# If production reads response.body, mock returns a fresh MagicMock — test passes
# In prod, real Response.body is bytes; downstream .decode() fails on binary content

# Fix: spec= constrains attribute access to the spec class's attribute set
from requests import Response
mock_response = MagicMock(spec=Response)
mock_response.text = "ok"
mock_response.status_code = 200
# mock_response.body now raises AttributeError — bug surfaces in test
```

**Severity guidance:**
- If the underlying production bug masked by the mock is P0/P1, flag the test pattern as the **regression-escape root cause** and pull the severity through.
- Otherwise, this is **P3** — systemic test hygiene. But list every unspec'd HTTP/SDK mock in the audit scope; the next BP1-BP22 finding could easily be hidden behind one.

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

### CC8: Worst-Case Blocking vs Round Timeout

For each external call site, you already gathered (in Step 1) the worst-case blocking time: `sum of retry delays + per-attempt timeouts + library-internal blocking`. Now compare it against the `round_timeout` of the round that calls it.

**If `worst_case_blocking > round_timeout`:** the round's timeout fires while the worker is still blocked. The FSM transitions on, but the worker thread keeps running until the underlying I/O completes. This produces:
- **Orphaned threads** that accumulate over time (file descriptors, HTTP connections, cached state).
- **Re-entrancy bugs** — the next period enters the same call site while the previous worker is still running.
- **Resource leaks** — most acute on connections with `MAX_WORKER_THREADS=1`, where the next request queues behind the orphan.

**How to check:**
1. For each call site, compute worst-case blocking from the data already gathered in Step 1.
2. Look up `round_timeout` for the calling round in `models.Params` or via `event_to_timeout` → ROUND_TIMEOUT.
3. Flag any site where `worst_case_blocking > round_timeout`.

**Concrete past finding:** trader's polymarket retry budget was 60 s; `BetPlacementRound.round_timeout` was 30 s. The round transitioned out before the connection responded, leaving an orphaned worker thread that kept running after the FSM had moved on.

**Fix:** cap retry budget at `round_timeout / 2`; OR move the call to a cancellable executor with `future.result(timeout=...)`; OR raise the round_timeout if the upstream genuinely needs the longer budget (with caveats — see CC2 circuit breaker).

### CC9: Observability Table per Call Site

The skill already flags individual logging gaps (CC3 inconsistent error reporting). CC9 is the *catalog*: build a table per call site so reviewers see the systemic pattern at a glance. Without this, stale fallback values (BP7) and silent `return None` failures stay invisible until P&L diverges.

| Call site | Logs success | Logs failure | Emits metric | Bubbles to UI |
|---|---|---|---|---|
| `behaviours/foo.py:123` | ✓ INFO | ✓ ERROR | ✗ | ✗ |
| `behaviours/bar.py:45` | ✗ | ✓ WARNING | ✗ | partial |
| ... | | | | |

A row that is mostly ✗ on the failure side is the high-leverage finding — that call site can fail invisibly. Combine this with BP7 (stale fallback) to identify "stale rate goes silent, agent trades on it for weeks" patterns.

---

## Scope Extension: `service.yaml` Overrides

Both this skill and `audit-fsm` historically read package source only and miss runtime parameter overrides. If `services/*/service.yaml` exists in the audit scope:

1. Parse the `overrides` block. Build a table of every overridden param, its target skill, and the override value.
2. For overrides that change resilience-relevant parameters, flag if the override:
   - Disables a safety mechanism (retry count to 0; timeout set to a very large value or `null`; `verify=False`)
   - Changes a URL to one with different TLS / auth requirements (e.g. http instead of https)
   - Sets an API key / token to an env var that defaults to a placeholder (`${OAR_API_KEY:str:dummy}`) — production deployments depend on the env var being set; if it isn't, the agent makes anonymous requests
3. When multiple `services/*/service.yaml` exist for the same agent, build a comparison table — drift between deployments often hides resilience regressions in one variant but not the other.

Past examples worth flagging by name: trader's `trader_pearl/` (Omenstrat) vs `polymarket_trader/` (Polystrat); meme-ooorr's env-var-driven X402 gateway URL + API key wiring.

---

## Methodology Guardrails

These guardrails reduce false positives observed in prior runs. Apply them before flagging any finding.

### Verify every sub-agent finding before accepting it

The Step B analysis agents return **candidate** findings with **candidate** severities, not final ones. The spawning agent (you) MUST hand-verify each candidate against the source before promoting it into the report. Sub-agents over-report because they lack the cross-cutting view.

For each candidate finding, before accepting:

1. **Read the cited `file:line` in the actual source.** Confirm the bug exists as described — not a misread, not a paraphrase that drifts from the code, not a citation pointing at the wrong line.
2. **Confirm the bug is real.** Apply the data-type trace guardrail (below). Apply the verbatim BP1 reminder (below). Re-check exception hierarchies and `except` clause widths personally.
3. **Re-evaluate severity.** Sub-agents systematically over-classify. Concretely:
   - "Unused / dead config" (defined-but-unenforced allowlist, vestigial constant) is **L**, not P0/P1, unless removing it actively enables an attack.
   - A `verify=False` in a test fixture or development helper is **not P0** even though the regex matches.
   - "JSONDecodeError uncaught" inside an `except ValueError` block is **not a finding** (BP1 false positive).
4. **Consolidate split findings.** If three sub-agent findings point at one root cause (e.g. three separate P0s that all stem from one missing timeout in a third-party library wrapper), report ONCE at the appropriate priority, not three times.
5. **Demote liberally.** If you can't reproduce the sub-agent's reasoning from the source in under a minute, the finding is probably wrong — drop it or downgrade to P3/P4 with an "informational" note.

Sub-agent classification is input, not output. The report is your judgment, not the union of sub-agent outputs.

### Force the data-type trace before flagging

When a check requires reasoning about a value's runtime type (BP1 dispatch, BP2 null guards, "type X passed where Y expected" claims), reason about the **runtime** type, not the static annotation. In open-autonomy, payload fields and DB-backed properties are JSON-deserialized — the runtime type may differ from the annotation.

Before flagging:
1. Locate the **last assignment** to the variable along the call path.
2. If that assignment is `json.loads(...)`, `self.db.get_strict(...)`, or a payload field whose value was JSON-serialized at write time, the runtime type is whatever the producer wrote — `dict`, `list`, `str`, `int` — not the annotation.
3. Do NOT flag a type mismatch unless you can name **both** the expected type AND the actual runtime type with `file:line` citations for each.

A concrete past failure: ~5 false positives in one run, all "JSONDecodeError uncaught" claims that were inside `except ValueError` blocks. BP1 already covers this — `JSONDecodeError` is a `ValueError` subclass — but the discovery agent didn't internalize the rule at the point of application.

### Pre-flag BP1 reminder (verbatim)

Before flagging "JSONDecodeError uncaught" / "missing JSON error handling" at any `response.json()` or `json.loads(...)` call:

1. Read the surrounding `except` clause(s).
2. If the except clause is `except ValueError`, `except (..., ValueError)`, `except Exception`, or any superclass of `ValueError` — **the JSON error IS caught.** Do not flag.
3. Only flag if the except clause is strictly more specific than `ValueError` (e.g. only `RequestException`, `KeyError`, or specific custom exceptions) AND `JSONDecodeError` would escape uncaught.

Belt-and-suspenders, since BP1 already documents the rule. The reminder exists because discovery agents have repeatedly flagged false positives here.

### Strip framework-scheduled events from end_block reasoning

When tracing FSM impact (Step 2) and you observe a transition that fires on an event scheduled by `event_to_timeout` (most commonly `ROUND_TIMEOUT`): that event is dispatched by the framework, not emitted by `end_block()`. Don't reason about it as if a behaviour returns it — model it as a wall-clock timeout that the framework injects.

### Single-finding-per-bug discipline

If a call site is flagged by multiple BPs (e.g. BP8 no-timeout AND BP15 idempotency AND CC8 worst-case blocking), report once with all relevant BP IDs cited, not three times.

---

## Coverage Limitations

This skill audits **external-request resilience**. The following are explicitly NOT covered — the audit report should call this out so consumers know what they still need to do:

- **FSM correctness and safety** → run `/audit-fsm` (companion skill).
- **Security review** of credential handling, env-var injection in `skill.yaml`, `eval` / `exec` patterns, unsafe deserialization (`pickle.loads`) → run `/security-review`.
- **Dependency CVEs / pinning currency** for `httpx`, `requests`, `web3`, `py_clob_client`, etc. → run `pip-audit` / `safety check` after this audit. Out of scope for a static audit.
- **Mathematical correctness** of strategy / pricing logic — out of scope.
- **Smart-contract resilience** (reentrancy, gas griefing, ordering attacks) — out of scope.
- **Network / load testing** under sustained outage — out of scope; this audit is static.

Include a "What this audit did not cover" section in every report.

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
6. Checks for all bug patterns (BP1–BP23)
7. Applies the Methodology Guardrails (data-type trace, BP1 reminder, sub-agent verification) before flagging

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
9. Compute worst-case-blocking vs round_timeout per call site (CC8)
10. Build the per-call-site observability table (CC9)
11. Parse `services/*/service.yaml` overrides and flag resilience-relevant changes (Scope Extension)

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
| **P1** | [Financial impact side-effects, idempotency-on-retry gaps] | Side-effect | | |
| **P2** | [Important bugs] | Various | | |
| **P3** | [Systemic improvements] | All | | |
| **P4** | [Low-impact fixes] | Various | | |

---

## Observability Table (CC9)

| Call site | Logs success | Logs failure | Emits metric | Bubbles to UI |
|---|---|---|---|---|

---

## Service-Level Override Findings

[Rows from `services/*/service.yaml` parsing — env-var defaults that fall back to `dummy`, retry/timeout overrides that disable safety, URL/key drift between deployments]

---

## What This Audit Did Not Cover

- FSM correctness and safety (run `/audit-fsm`)
- Security review of credential handling, env-var injection, `eval`/`exec`, unsafe deserialization (run `/security-review`)
- Dependency CVEs (run `pip-audit` / `safety check`)
- Mathematical correctness of strategy / pricing logic
- Smart-contract resilience (reentrancy, gas griefing, ordering attacks)
- Network / load testing under sustained outage (this audit is static)
- [Add scope exclusions specific to this run, e.g. "service.yaml overrides not parsed because no services/ directory in scope"]
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
- [ ] BP1 pre-flag reminder applied — verified `except` clauses do NOT include `ValueError` before flagging
- [ ] The `{"data": null}` pattern is checked everywhere `.get("data", {})` is used
- [ ] The `Subgraph.process_response` override is checked for `None` error message handling
- [ ] All fallback/cached values are cataloged with their staleness risk
- [ ] All retry strategies are documented and compared (CC1)
- [ ] Thread blocking and timeout risks are documented (including third-party library internals)
- [ ] Third-party httpx/requests clients are checked for missing timeouts
- [ ] `MAX_WORKER_THREADS` and executor deduplication risks are documented
- [ ] Pre-FSM handler crashes are checked (accessing synchronized_data before FSM starts)
- [ ] Connection `on_send` payload deserialization is checked for exception handling
- [ ] **BP15** — every non-idempotent POST has its dedup mechanism documented (or flagged as P1)
- [ ] **BP16** — `except` blocks decode retry eligibility via `isinstance` / status code, not substring match
- [ ] **BP17** — every class-level `_VALID_*` / `_ALLOWED_*` constant is referenced from the dispatch path
- [ ] **BP18** — `if X is None:` branches on fallible external calls do NOT default to optimistic state
- [ ] **BP19** — no `verify=False`; no hardcoded credentials; no secrets in URL query strings
- [ ] **BP20** — every paginated fetch documents partial-failure semantics
- [ ] **BP21** — every external response with potentially unbounded size has a size cap
- [ ] **BP22** — signed payloads with timestamps use consensus-safe time when in a multi-agent service
- [ ] **BP23** — every `MagicMock` / `Mock` / `AsyncMock` substituting for an HTTP response, SDK client, or connection object uses `spec=`
- [ ] **CC8** — worst-case-blocking vs round_timeout computed for every call site
- [ ] **CC9** — observability table built; rows that are mostly ✗ on failure are flagged
- [ ] `services/*/service.yaml` overrides parsed and resilience-relevant changes flagged
- [ ] Data-type trace performed before flagging type-mismatch findings (Methodology Guardrails)
- [ ] The crash/stuck/side-effect classification is complete
- [ ] The priority matrix covers every finding
- [ ] Each fix description is specific enough to implement directly
- [ ] Report includes "What this audit did not cover" section
