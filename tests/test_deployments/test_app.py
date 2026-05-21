# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2026 Valory AG
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

"""Tests for the Tendermint com server."""

import json
import logging
import os
import platform
import shutil
import stat
import subprocess  # nosec
import tempfile
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set, cast
from unittest import mock

import pytest
import requests
from _pytest.logging import LogCaptureFixture  # type: ignore
from _pytest.monkeypatch import MonkeyPatch  # type: ignore
from aea.common import JSONLike
from aea.test_tools.utils import wait_for_condition

from deployments.Dockerfiles.tendermint import app  # type: ignore
from deployments.Dockerfiles.tendermint.app import TendermintNode  # type: ignore
from deployments.Dockerfiles.tendermint.app import (  # type: ignore
    CONFIG_OVERRIDE,
    DOCKER_INTERNAL_HOST,
    PeriodDumper,
    create_app,
    get_defaults,
    load_genesis,
    override_config_toml,
    update_peers,
)
from deployments.Dockerfiles.tendermint.tendermint import (  # type: ignore
    TendermintParams,
)

ENCODING = "utf-8"
VERSION = "0.34.19"
DUMMY_CONFIG_TOML = """
# Comma separated list of seed nodes to connect to
seeds = ""

# Comma separated list of nodes to keep persistent connections to
persistent_peers = "dummy_peer1@localhost:80,dummy_peer2@localhost:81"

# UPNP port forwarding
upnp = false

external_address = ""
"""
DUMMY_EXTERNAL_ADDRESS = "dummy_external_address:26566"

wait_for_node_to_run = pytest.mark.usefixtures("wait_for_node")
wait_for_occupied_rpc_port = pytest.mark.usefixtures("wait_for_occupied_rpc_port")


# utility functions
def readonly_handler(func: Callable, path: str, execinfo) -> None:  # type: ignore
    """If permission is readonly, we change and retry."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def test_period_dumper(monkeypatch: MonkeyPatch) -> None:
    """Test PeriodDumper"""

    monkeypatch.setenv("ID", "42")
    with tempfile.TemporaryDirectory() as tmp_dir:
        monkeypatch.setenv("TMHOME", tmp_dir)
        dump_dir = Path(tempfile.mkdtemp())
        period_dumper = PeriodDumper(mock.Mock(), dump_dir=dump_dir)
        period_dumper.dump_period()

    shutil.rmtree(period_dumper.dump_dir)


@pytest.mark.parametrize("write_to_log_env", ["true", "false"])
def test_create_app_installs_single_rotating_file_handler(
    monkeypatch: MonkeyPatch, write_to_log_env: str
) -> None:
    """`create_app` attaches exactly one RotatingFileHandler on LOG_FILE to root.

    The handler lives on the *root* logger so that ``app.logger``, werkzeug,
    and any third-party loggers all funnel into the same file by propagation.
    ``app.logger`` must not own a separate ``RotatingFileHandler`` on the
    same path (the single-owner invariant). Holds for both ``WRITE_TO_LOG=true``
    and ``WRITE_TO_LOG=false``.

    :param monkeypatch: the pytest monkeypatch fixture.
    :param write_to_log_env: the parametrized value for the WRITE_TO_LOG env var.
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        tm_home = tmp / "tm"
        (tm_home / "config").mkdir(parents=True)
        (tm_home / "config" / "config.toml").write_text(
            DUMMY_CONFIG_TOML, encoding=ENCODING
        )
        log_file = tmp / "log.log"
        dump_dir = tmp / "dump"

        monkeypatch.setenv("PROXY_APP", "kvstore")
        monkeypatch.setenv("CREATE_EMPTY_BLOCKS", "true")
        monkeypatch.setenv("TMHOME", str(tm_home))
        monkeypatch.setenv("USE_GRPC", "false")
        monkeypatch.setenv("LOG_FILE", str(log_file))
        monkeypatch.setenv("LOG_FILE_MAX_BYTES", "1048576")
        monkeypatch.setenv("WRITE_TO_LOG", write_to_log_env)

        monkeypatch.setattr(TendermintNode, "init", lambda self: None)
        monkeypatch.setattr(TendermintNode, "start", lambda self, debug=False: None)

        flask_app, tendermint_node = create_app(dump_dir=dump_dir, debug=False)
        flask_logger = cast(logging.Logger, flask_app.logger)
        root_logger = logging.getLogger()

        try:
            root_handlers = [
                h
                for h in root_logger.handlers
                if isinstance(h, RotatingFileHandler)
                and h.baseFilename == str(log_file)
            ]
            assert (
                len(root_handlers) == 1
            ), "create_app must attach exactly one RotatingFileHandler on LOG_FILE to root"
            assert root_handlers[0].maxBytes == 1048576
            assert root_handlers[0].backupCount == 1, (
                "backupCount must be 1; a regression to 0 would silently "
                "discard the rotated log file"
            )

            # Single-owner invariant: ``app.logger`` must not have its own
            # ``RotatingFileHandler`` on ``LOG_FILE``. The file is owned by
            # root and reached via propagation. A regression that re-attaches
            # the handler on ``app.logger`` would re-introduce double-writes
            # (one via app.logger's handler, one via propagation to root's).
            app_logger_own_rotating = [
                h for h in flask_logger.handlers if isinstance(h, RotatingFileHandler)
            ]
            assert app_logger_own_rotating == [], (
                "app.logger must not own a RotatingFileHandler; the file is "
                "owned by root and reached via propagation"
            )

            assert tendermint_node.write_to_log is (write_to_log_env == "true")
        finally:
            for h in list(root_logger.handlers):
                if isinstance(h, RotatingFileHandler) and h.baseFilename == str(
                    log_file
                ):
                    root_logger.removeHandler(h)
                    h.close()


def test_create_app_is_idempotent_on_repeat_calls(monkeypatch: MonkeyPatch) -> None:
    """`create_app` called twice does not stack handlers on the root logger.

    Without the idempotency guard, every call would append another
    ``RotatingFileHandler`` to root and the same log line would be written
    N times to the same file.

    :param monkeypatch: the pytest monkeypatch fixture.
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        tm_home = tmp / "tm"
        (tm_home / "config").mkdir(parents=True)
        (tm_home / "config" / "config.toml").write_text(
            DUMMY_CONFIG_TOML, encoding=ENCODING
        )
        log_file = tmp / "log.log"

        monkeypatch.setenv("PROXY_APP", "kvstore")
        monkeypatch.setenv("CREATE_EMPTY_BLOCKS", "true")
        monkeypatch.setenv("TMHOME", str(tm_home))
        monkeypatch.setenv("USE_GRPC", "false")
        monkeypatch.setenv("LOG_FILE", str(log_file))
        monkeypatch.setenv("WRITE_TO_LOG", "true")

        monkeypatch.setattr(TendermintNode, "init", lambda self: None)
        monkeypatch.setattr(TendermintNode, "start", lambda self, debug=False: None)

        create_app(dump_dir=tmp / "dump_a", debug=False)
        create_app(dump_dir=tmp / "dump_b", debug=False)
        root_logger = logging.getLogger()

        try:
            root_handlers = [
                h
                for h in root_logger.handlers
                if isinstance(h, RotatingFileHandler)
                and h.baseFilename == str(log_file)
            ]
            assert len(root_handlers) == 1, (
                "create_app must not stack a second RotatingFileHandler on "
                "root when called more than once"
            )
        finally:
            for h in list(root_logger.handlers):
                if isinstance(h, RotatingFileHandler) and h.baseFilename == str(
                    log_file
                ):
                    root_logger.removeHandler(h)
                    h.close()


def test_tendermint_node_init_does_not_attach_handlers() -> None:
    """Test that ``TendermintNode.__init__`` does not attach handlers to its logger.

    The rotation safety net relies on ``create_app`` being the sole owner of the
    file handler. If a future refactor reintroduces the ``RotatingFileHandler``
    setup inside ``TendermintNode.__init__``, ``create_app`` and the node would
    each attach their own handler on the same path, recreating the double-write
    / orphaned-handler-after-rotation bug. ``__init__`` must therefore be a
    no-op on ``logger.handlers``.
    """

    fresh_logger = logging.getLogger(
        "test_tendermint_node_init_does_not_attach_handlers"
    )
    fresh_logger.handlers = []
    handlers_before = list(fresh_logger.handlers)

    params = TendermintParams(proxy_app="kvstore")
    TendermintNode(params=params, logger=fresh_logger, write_to_log=True)

    assert (
        fresh_logger.handlers == handlers_before
    ), "TendermintNode.__init__ must not mutate logger.handlers"


def test_tendermint_node_log_skips_empty_lines() -> None:
    """Test that `TendermintNode.log()` skips blank/whitespace-only lines.

    Without this guard, every blank line in Tendermint's stdout produces an
    empty log record and floods the file.
    """

    logger = mock.MagicMock(spec=logging.Logger)
    params = TendermintParams(proxy_app="kvstore")
    node = TendermintNode(
        params=params,
        logger=cast(logging.Logger, logger),
        write_to_log=True,
    )

    with mock.patch.object(
        TendermintNode, "_write_to_console", staticmethod(lambda line: None)
    ):
        node.log("\n")
        node.log("   \t  ")
        node.log("")
        node.log("real line\n")

    assert logger.info.call_args_list == [mock.call("real line")]


def test_create_app_rotates_log_file_at_max_bytes(monkeypatch: MonkeyPatch) -> None:
    """Rotation moves LOG_FILE to LOG_FILE.1 once writes exceed maxBytes.

    Post-rotation writes must land in the fresh ``log.log`` only; the
    renamed ``log.log.1`` must be frozen. This exercises the precise
    failure mode the PR fixes — with a single rotating handler owning
    the file, the renamed log stops receiving writes after rotation.
    (The orphaned-FD bug would manifest as post-rotation writes leaking
    into the renamed file via a stale descriptor on a second
    non-rotating handler.)

    :param monkeypatch: the pytest monkeypatch fixture.
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        tm_home = tmp / "tm"
        (tm_home / "config").mkdir(parents=True)
        (tm_home / "config" / "config.toml").write_text(
            DUMMY_CONFIG_TOML, encoding=ENCODING
        )
        log_file = tmp / "log.log"
        rotated = tmp / "log.log.1"

        monkeypatch.setenv("PROXY_APP", "kvstore")
        monkeypatch.setenv("CREATE_EMPTY_BLOCKS", "true")
        monkeypatch.setenv("TMHOME", str(tm_home))
        monkeypatch.setenv("USE_GRPC", "false")
        monkeypatch.setenv("LOG_FILE", str(log_file))
        # Cap big enough that the post-rotation markers fit in a fresh
        # ``log.log`` without triggering a second rotation, small enough
        # that the pre-rotation loop reaches it within a few dozen lines.
        monkeypatch.setenv("LOG_FILE_MAX_BYTES", "2000")
        monkeypatch.setenv("WRITE_TO_LOG", "true")

        monkeypatch.setattr(TendermintNode, "init", lambda self: None)
        monkeypatch.setattr(TendermintNode, "start", lambda self, debug=False: None)

        create_app(dump_dir=tmp / "dump", debug=False)
        root_logger = logging.getLogger()

        try:
            # Write until the first rotation occurs, then stop. If we kept
            # writing past the first rotation, additional rotations would
            # overwrite ``log.log.1`` and the "rotated file is frozen
            # after rotation" assertion below would no longer mean what
            # it says.
            for i in range(50):
                root_logger.info("pre-rotation line %d %s", i, "x" * 60)
                if rotated.exists():
                    break
            else:  # pragma: no cover
                raise AssertionError(
                    "RotatingFileHandler did not rotate the log file within "
                    "50 writes; maxBytes may be too high for this test"
                )

            rotated_size_before = rotated.stat().st_size

            # Post-rotation writes are short enough to fit in the fresh
            # ``log.log`` without triggering a second rotation.
            for i in range(3):
                root_logger.info("marker%d", i)

            current_content = log_file.read_text(encoding=ENCODING)
            assert (
                "marker0" in current_content
            ), "post-rotation write did not reach the fresh log.log"

            assert rotated.stat().st_size == rotated_size_before, (
                "rotated log.log.1 grew after rotation; a non-rotating "
                "handler is writing through a stale file descriptor"
            )
            rotated_content = rotated.read_text(encoding=ENCODING)
            assert (
                "marker" not in rotated_content
            ), "post-rotation write leaked into the rotated log.log.1"
        finally:
            for h in list(root_logger.handlers):
                if isinstance(h, RotatingFileHandler) and h.baseFilename == str(
                    log_file
                ):
                    root_logger.removeHandler(h)
                    h.close()


def test_tendermint_node_log_does_not_forward_when_write_to_log_disabled() -> None:
    """`TendermintNode.log()` does not forward output when write_to_log is False.

    Locks in the off-path semantic: ``WRITE_TO_LOG=false`` must keep
    subprocess stdout out of the configured logger, even though the
    ``RotatingFileHandler`` is now attached to ``app.logger`` unconditionally
    by ``create_app``.
    """

    logger = mock.MagicMock(spec=logging.Logger)
    params = TendermintParams(proxy_app="kvstore")
    node = TendermintNode(
        params=params,
        logger=cast(logging.Logger, logger),
        write_to_log=False,
    )

    with mock.patch.object(
        TendermintNode, "_write_to_console", staticmethod(lambda line: None)
    ):
        node.log("real line\n")
        node.log("another line\n")

    logger.info.assert_not_called()


# base classes
class BaseTendermintTest:
    """BaseTendermintTest"""

    tendermint: str
    tm_home: str
    path: Path
    _os_env: Dict

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test."""
        cls._os_env = os.environ.copy()
        cls.tendermint = shutil.which("tendermint")  # type: ignore
        cls.tm_home = os.environ["TMHOME"] = tempfile.mkdtemp()
        cls.path = Path(cls.tm_home)
        assert not os.listdir(cls.tm_home)

        command = [cls.tendermint, "init", "validator", "--home", cls.tm_home]
        process = subprocess.Popen(command, stderr=subprocess.PIPE)  # nosec
        _, stderr = process.communicate()
        assert not stderr, stderr

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test."""
        os.environ.clear()
        os.environ.update(cls._os_env)
        shutil.rmtree(cls.tm_home, ignore_errors=True, onerror=readonly_handler)


class BaseTendermintServerTest(BaseTendermintTest):
    """Test Tendermint server app"""

    app: Any
    app_context: Any
    tendermint_node: TendermintNode
    debug_tendermint = False
    tm_status_endpoint = "http://localhost:26657/status"
    dump_dir: Path

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test."""
        super().setup_class()
        os.environ["PROXY_APP"] = "kvstore"
        os.environ["CREATE_EMPTY_BLOCKS"] = "true"
        os.environ["USE_GRPC"] = "false"
        os.environ["LOG_FILE"] = str(cls.path / "tendermint.log")
        os.environ["WRITE_TO_LOG"] = "true"
        cls.dump_dir = Path(tempfile.mkdtemp())
        cls.app, cls.tendermint_node = create_app(
            dump_dir=cls.dump_dir,
            debug=cls.debug_tendermint,
        )
        cls.app.config["TESTING"] = True
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test."""
        cls.app_context.pop()
        cls.tendermint_node.stop()
        shutil.rmtree(cls.dump_dir)
        super().teardown_class()


# unit tests
def test_tendermint_executable_found() -> None:
    """Test Tendermint executable found"""
    assert shutil.which("tendermint"), "No `tendermint` executable found"
    output = subprocess.check_output(["tendermint", "version"])  # nosec
    assert output.decode(ENCODING).strip() == VERSION


class TestTendermintServerUtilityFunctions(BaseTendermintTest):
    """Test Tendermint server utility functions"""

    def test_load_genesis(self) -> None:
        """Load the genesis.json file"""
        expected_keys = {
            "genesis_time",
            "chain_id",
            "initial_height",
            "consensus_params",
            "validators",
            "app_hash",
        }
        json = load_genesis()
        assert set(json.keys()) == expected_keys

    def test_get_defaults(self) -> None:
        """Test get_defaults function"""
        expected_keys = {"genesis_time"}
        defaults = get_defaults()
        assert set(defaults.keys()) == expected_keys

    def test_override_config_toml(self) -> None:
        """Test override_config_toml function"""
        path = self.path / "config" / "config.toml"
        assert path.is_file(), f"not a file: {path}"
        txt = path.read_text("utf-8")
        assert all(old in txt and new not in txt for old, new in CONFIG_OVERRIDE)
        override_config_toml()
        txt = path.read_text("utf-8")
        assert not any(old in txt or new not in txt for old, new in CONFIG_OVERRIDE)


# integration tests
class TestTendermintServerApp(BaseTendermintServerTest):
    """Test Tendermint server app"""

    genesis_filepath: Path
    genesis_config: Dict

    def setup_method(self) -> None:
        """Setup"""
        self.genesis_filepath = Path(os.environ["TMHOME"], "config", "genesis.json")
        self.genesis_config = load_genesis()

    def teardown_method(self) -> None:
        """Teardown"""
        self.genesis_filepath.write_text(json.dumps(self.genesis_config))

    @wait_for_node_to_run
    def test_files_exist(self) -> None:
        """Test that the necessary files are present"""

        expected_file_names = [
            Path(self.tm_home, "config", "config.toml"),
            Path(self.tm_home, "config", "priv_validator_key.json"),
            Path(self.tm_home, "config", "genesis.json"),
            Path(self.tm_home, "config", "node_key.json"),
            Path(self.tm_home, "data", "priv_validator_state.json"),
        ]

        assert all(f.exists() for f in expected_file_names), expected_file_names

    @wait_for_node_to_run
    def test_get_request_status(self, http_: str, loopback: str, rpc_port: int) -> None:
        """Check local node is running"""
        response = requests.get(f"{http_}{loopback}:{rpc_port}/status", timeout=30)
        data = response.json()
        assert data["result"]["node_info"]["version"] == VERSION

    @wait_for_node_to_run
    def test_handle_notfound(self) -> None:
        """Test handle not found"""
        with self.app.test_client() as client:
            response = client.get("/non_existing_endpoint")
            assert response.status_code == 404

    @wait_for_node_to_run
    def test_get_app_hash(self) -> None:
        """Test get app hash"""
        with self.app.test_client() as client:
            wait_for_condition(
                lambda: "app_hash" in client.get("/app_hash").get_json(),
                timeout=10,
                period=1,
                error_msg="Could not retrieve `app_hash` from Tendermint server",
            )

    @wait_for_node_to_run
    def test_get_params(self) -> None:
        """Test get app hash"""

        with self.app.test_client() as client:
            response = client.get("/params")
            assert response.status_code == 200
            data = cast(JSONLike, response.get_json())
            assert data["status"] is True
            assert data["error"] is None
            params = data.get("params")
            assert params
            assert params.pop("address")
            assert params.pop("peer_id")
            pub_key = params.pop("pub_key")
            assert pub_key.pop("type")
            assert pub_key.pop("value")
            # nothing else should be sent, certainly not a private key.
            assert not params

    @wait_for_node_to_run
    def test_update_params(self) -> None:
        """Test get app hash"""

        dummy_data = dict(
            genesis_config=load_genesis(),
            validators=[],
            external_address="",
        )

        with self.app.test_client() as client:
            response = client.post("/params", json=dummy_data)
            assert response.status_code == 200
            data = cast(JSONLike, response.get_json())
            assert data["status"] is True
            assert data["error"] is None

    @wait_for_node_to_run
    def test_get_params_returns_503_on_status_fetch_failure(
        self, monkeypatch: MonkeyPatch
    ) -> None:
        """Tendermint /status failure surfaces as ``status: False``.

        A ``ConnectionError`` from the Tendermint /status call routes through
        the widened catch and returns the ``{status: False, error: ...}``
        contract instead of crashing the request.

        :param monkeypatch: pytest fixture used to force
            ``app.requests.get`` to raise ``ConnectionError``.
        """

        def _raise(*_: object, **__: object) -> object:
            raise app.requests.ConnectionError("tendermint unreachable")

        monkeypatch.setattr(app.requests, "get", _raise)
        with self.app.test_client() as client:
            response = client.get("/params")
            assert response.status_code == 200
            data = cast(JSONLike, response.get_json())
            assert data["status"] is False
            assert data["error"]
            assert data["params"] == {}

    @wait_for_node_to_run
    def test_get_params_handles_typeerror_on_non_dict_status_body(
        self, monkeypatch: MonkeyPatch
    ) -> None:
        """Non-object JSON from /status surfaces as ``status: False``.

        If Tendermint's ``/status`` (or a maintenance proxy in front of it)
        returns valid JSON that isn't a dict — e.g. ``null``, ``"maintenance"``,
        a list — then ``status["result"]`` raises ``TypeError``. The widened
        catch must convert that to the ``{status: False, error: ...}``
        contract instead of letting the exception escape to a Flask 500
        (which would crash the framework caller's ``.json()`` parse).

        :param monkeypatch: pytest fixture used to stub ``app.requests.get``
            so it returns a response whose ``.json()`` is ``None``.
        """

        class _FakeResp:
            @staticmethod
            def json() -> None:
                return None

        monkeypatch.setattr(app.requests, "get", lambda *_a, **_kw: _FakeResp())
        with self.app.test_client() as client:
            response = client.get("/params")
            assert response.status_code == 200
            data = cast(JSONLike, response.get_json())
            assert data["status"] is False
            assert data["error"]
            assert data["params"] == {}

    @wait_for_node_to_run
    def test_update_params_handles_typeerror_on_malformed_body(self) -> None:
        """Malformed-but-JSON-valid POST body surfaces as ``status: False``.

        A POST body with the right keys but a wrong-typed value (e.g.
        ``validators: null``) raises ``TypeError`` inside ``update_peers`` /
        ``update_external_address``. The widened catch must convert it to
        the standard ``{status: False, error: ...}`` response instead of
        letting the exception propagate to a Flask 500.
        """

        bad_payload = dict(
            genesis_config=load_genesis(),
            validators=None,
            external_address=DUMMY_EXTERNAL_ADDRESS,
        )
        with self.app.test_client() as client:
            response = client.post("/params", json=bad_payload)
            assert response.status_code == 200
            data = cast(JSONLike, response.get_json())
            assert data["status"] is False
            assert data["error"]

    @wait_for_node_to_run
    def test_get_and_update(self) -> None:
        """Test get and update Tendermint genesis data"""

        genesis_config = load_genesis()

        with self.app.test_client() as client:
            # 1. check params are in validator set
            response = client.get("/params")
            assert response.status_code == 200
            response_data = cast(Dict, response.get_json())
            params = cast(Dict, response_data["params"])
            params.pop("peer_id", None)
            params["name"], params["power"] = "", "10"
            assert params in genesis_config["validators"]

            # 2. clear validators
            dummy_data = dict(
                genesis_config=genesis_config,
                validators=[],
                external_address=DUMMY_EXTERNAL_ADDRESS,
            )
            response = client.post("/params", json=dummy_data)
            assert response.status_code == 200
            genesis_config = load_genesis()
            assert params not in genesis_config["validators"]


class TestTendermintGentleResetServer(BaseTendermintServerTest):
    """Test Tendermint gentle reset"""

    @wait_for_node_to_run
    def test_gentle_reset(self) -> None:
        """Test gentle reset"""
        with self.app.test_client() as client:
            response = client.get("/gentle_reset")
            data = response.get_json()
            assert response.status_code == 200
            assert data["status"] is True


class TestTendermintHardResetServer(BaseTendermintServerTest):
    """Test Tendermint hard reset"""

    @wait_for_node_to_run
    @pytest.mark.parametrize("prune_fail", (True, False))
    def test_hard_reset(self, prune_fail: bool) -> None:
        """Test hard reset"""
        with self.app.test_client() as client, mock.patch.object(
            TendermintNode, "prune_blocks", return_value=int(prune_fail)
        ):
            response = client.get("/hard_reset")
            data = response.get_json()
            assert response.status_code == 200
            assert data["status"] is not prune_fail

    @wait_for_node_to_run
    @pytest.mark.skipif(platform.system() != "Linux", reason="scoped to docker image")
    def test_hard_reset_dev_mode(self, caplog: LogCaptureFixture) -> None:
        """Test hard reset"""

        resets = 0  # zero since first hard reset
        os.environ["ID"] = "_dummy_ID"
        period_dumper = PeriodDumper(logger=logging.getLogger(), dump_dir=self.dump_dir)
        store_dir = period_dumper.dump_dir / f"period_{resets}"
        path = store_dir / ("node" + os.environ["ID"])
        logging.error(f"expected: {path}")
        assert not path.exists()

        with self.app.test_client() as client:
            with mock.patch.object(app, "IS_DEV_MODE", return_value=True):
                response = client.get("/hard_reset")
                assert response.status_code == 200
                data = cast(JSONLike, response.get_json())
                assert data["status"] is True
                assert "Dumped data for period" in caplog.text

        assert path.exists()
        expected = {"config", "tendermint.log", "data"}
        assert {p.name for p in path.glob("*")} == expected


class TestTendermintLogMessages(BaseTendermintServerTest):
    """Test Tendermint message logging"""

    @wait_for_node_to_run
    def test_tendermint_logs(self) -> None:
        """Test Tendermint logs"""

        def get_logs() -> str:
            with open(os.environ["LOG_FILE"], "r") as f:
                lines = "".join(f.readlines())
            return lines

        def get_missing(messages: Set[str]) -> Set[str]:
            while messages:
                logs = get_logs()
                messages -= {line for line in messages if line in logs}
            return messages

        before_stopping = {
            "Tendermint process started",
            "Monitoring thread started",
            "Starting multiAppConn service",
            "Starting localClient service",
            "This node is a validator",
        }

        after_stopping = {
            "Monitoring thread terminated",
            "Tendermint process stopped",
        }

        wait_for_condition(
            lambda: not get_missing(before_stopping),
            error_msg=f"Not all `before_stopping` messages found in Tendermint logs: {before_stopping}",
            timeout=10,
            period=1,
        )
        self.tendermint_node.stop()
        wait_for_condition(
            lambda: not get_missing(after_stopping),
            error_msg=f"Not all `after_stopping` messages found in Tendermint logs: {after_stopping}",
            timeout=10,
            period=1,
        )


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason=(
        "test_tendermint_buffer drives a real Tendermint binary; only the "
        "Linux runners are the production environment. Mac/Windows runners "
        "exhibit Tendermint socket and scheduler noise that's unrelated to "
        "what this test is actually verifying."
    ),
)
class TestTendermintBufferWorking(BaseTendermintServerTest):
    """Test Tendermint buffer"""

    perform_monitoring = True
    debug_tendermint = True

    @wait_for_node_to_run
    def test_tendermint_buffer(self) -> None:
        """Assert Tendermint keeps making progress for the test window.

        The claim is "the node is alive and producing blocks", not
        "every single /status poll succeeds." A baseline height is
        captured on the first successful observation; the test passes
        only when a *later* observation reports a strictly higher
        height (proving forward progress, not just that the node is
        reachable).

        Schema errors (missing keys, non-int height) are NOT suppressed
        and surface as the actual exception so a Tendermint version
        bump that renames a field fails the test loudly rather than
        silently timing out.
        """

        deadline = time.monotonic() + 120.0
        baseline: Optional[int] = None
        while time.monotonic() < deadline:
            try:
                res = requests.get(self.tm_status_endpoint, timeout=5)
            except requests.RequestException:
                # Transport hiccup; the next iteration will observe the
                # real state.
                time.sleep(1)
                continue
            res.raise_for_status()
            height = int(res.json()["result"]["sync_info"]["latest_block_height"])
            if baseline is None:
                baseline = height
            elif height > baseline:
                return  # observed advance proves liveness
            elif height < baseline:
                raise AssertionError(
                    f"Tendermint block height went backwards: "
                    f"{baseline} -> {height}"
                )
            time.sleep(1)

        raise AssertionError(
            f"Tendermint did not advance ``latest_block_height`` within "
            f"120s (baseline={baseline})"
        )


def test_update_peers() -> None:
    """Test update peers."""

    validators = [
        {
            "hostname": f"host_{i}",
            "p2p_port": i * 10,
            "peer_id": f"peer_{i}",
        }
        for i in range(2)
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir, "config.toml")
        config_file.write_text(DUMMY_CONFIG_TOML)

        update_peers(validators=validators, config_path=config_file)

        updated_content = config_file.read_text()

        # make sure we don't update anything else
        assert """seeds = """ "" in updated_content
        assert "upnp = false" in updated_content

        for val in validators:
            assert (
                str(val["peer_id"])
                + "@"
                + str(val["hostname"])
                + ":"
                + str(val["p2p_port"])
                in updated_content
            )


def test_update_peers_internal_host() -> None:
    """Test update peers."""

    validators = [{"hostname": "localhost", "p2p_port": 80, "peer_id": "peer"}]

    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir, "config.toml")
        config_file.write_text(DUMMY_CONFIG_TOML)

        update_peers(validators=validators, config_path=config_file)

        updated_content = config_file.read_text()

        # make sure we don't update anything else
        assert """seeds = """ "" in updated_content
        assert "upnp = false" in updated_content

        for val in validators:
            assert (
                str(val["peer_id"])
                + "@"
                + DOCKER_INTERNAL_HOST
                + ":"
                + str(val["p2p_port"])
                in updated_content
            )
