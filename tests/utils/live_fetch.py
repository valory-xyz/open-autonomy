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


def _build_session() -> requests.Session:
    """Build a requests session that retries transient network errors.

    urllib3 counts connect / read / status failures against ``total``,
    not in addition to it — setting them individually here would shorten
    the effective retry count on mixed failure sequences. ``total=5`` is
    the single source of truth.

    :return: the configured session.
    """
    retry = Retry(
        total=5,
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
) -> requests.Response:
    """Fetch a live upstream URL or skip the test if it stays unreachable.

    Behaviour by response category:

    - **Connect / read / timeout failure** after exhausting retries:
      the test is **skipped** (``pytest.skip``). These are infra-level
      problems that don't indicate a real bug in the subject under test.
    - **5xx / 429** after exhausting retries: the test is **skipped**.
      Same reasoning — transient upstream unavailability.
    - **4xx** (other than 429): the test **fails** via
      ``response.raise_for_status``. A 404 means the URL is wrong
      (a real bug) and a 403 from GitHub means the access pattern is
      wrong; neither should be silently swallowed.
    - **2xx**: the response is returned to the caller.

    :param url: the upstream URL to fetch.
    :param timeout: per-attempt timeout in seconds.
    :return: the successful (2xx) response.
    """
    try:
        response = _build_session().get(url, timeout=timeout)
    except (requests.ConnectionError, requests.Timeout) as exc:
        pytest.skip(f"upstream unreachable after retries: {url} ({exc})")

    if response.status_code in _TRANSIENT_STATUS:
        pytest.skip(f"upstream returned {response.status_code} after retries: {url}")

    # 4xx (other than 429) is a real bug — surface it.
    response.raise_for_status()
    return response
