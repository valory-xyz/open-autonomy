# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Live upstream fetching helpers for tests.

Distinguishes transient network failure (skip) from real upstream data
mismatch (fail). Tests that verify drift between repo state and upstream
sources of truth keep their liveness guarantee without going red on a
runner DNS hiccup.
"""

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry  # type: ignore

_DEFAULT_TIMEOUT = 30
_TRANSIENT_STATUS = (500, 502, 503, 504, 429)


def live_session() -> requests.Session:
    """Build a requests session that retries transient network errors."""
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        status_forcelist=_TRANSIENT_STATUS,
        backoff_factor=1.0,
        raise_on_status=False,
        allowed_methods=frozenset(["GET", "HEAD", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_upstream_or_skip(
    url: str,
    timeout: int = _DEFAULT_TIMEOUT,
    session: requests.Session = None,
) -> requests.Response:
    """Fetch a live upstream URL or skip the test if it stays unreachable.

    Retries connect/read errors and transient 5xx / 429 responses with
    exponential backoff. If the request still fails after retries, the
    test is skipped rather than failed. Real upstream data mismatches
    surface to the caller via the response object as usual.

    :param url: the upstream URL to fetch.
    :param timeout: per-attempt timeout in seconds.
    :param session: optional pre-built session (reuses connection pool).
    :return: the successful response.
    """
    session = session or live_session()
    try:
        response = session.get(url, timeout=timeout)
    except (requests.ConnectionError, requests.Timeout) as exc:
        pytest.skip(f"upstream unreachable after retries: {url} ({exc})")

    if response.status_code in _TRANSIENT_STATUS:
        pytest.skip(f"upstream returned {response.status_code} after retries: {url}")

    response.raise_for_status()
    return response
