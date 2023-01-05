# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
from pathlib import Path
from typing import Callable, Dict, Set, cast
from unittest import mock

import flask
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
"""


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

    app: flask.app.Flask
    app_context: flask.ctx.AppContext
    tendermint_node: TendermintNode
    perform_monitoring = True
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
        cls.dump_dir = Path(tempfile.mkdtemp())
        cls.app, cls.tendermint_node = create_app(
            dump_dir=cls.dump_dir,
            perform_monitoring=cls.perform_monitoring,
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

    def setup(self) -> None:
        """Setup"""
        self.genesis_filepath = Path(os.environ["TMHOME"], "config", "genesis.json")
        self.genesis_config = load_genesis()

    def teardown(self) -> None:
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
        response = requests.get(f"{http_}{loopback}:{rpc_port}/status")
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
        )

        with self.app.test_client() as client:
            response = client.post("/params", json=dummy_data)
            assert response.status_code == 200
            data = cast(JSONLike, response.get_json())
            assert data["status"] is True
            assert data["error"] is None

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


def mock_get_node_command_kwargs() -> Dict:
    """Get the node command kwargs"""
    kwargs = {
        "bufsize": 1,
        "universal_newlines": True,
    }

    # Pipe stdout and stderr even if we're not going to read to provoke the buffer fill
    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.STDOUT

    if platform.system() == "Windows":  # pragma: nocover
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore
    else:
        kwargs["preexec_fn"] = os.setsid  # type: ignore

    return kwargs


class TestTendermintBufferFailing(BaseTendermintServerTest):
    """Test Tendermint buffer"""

    perform_monitoring = False  # Setting this flag to False and not monitoring makes the buffer to fill and freeze Tendermint
    debug_tendermint = True  # This will cause more logging -> faster failure

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test."""
        with mock.patch.object(
            TendermintParams,
            "get_node_command_kwargs",
            return_value=mock_get_node_command_kwargs(),
        ):
            super().setup_class()

    @wait_for_occupied_rpc_port
    def test_tendermint_buffer(self) -> None:
        """Test Tendermint buffer"""

        with pytest.raises(requests.exceptions.Timeout):
            # Give the test 30 seconds for it to throw a timeout
            for _ in range(30):
                # If it hangs for 5 seconds, we assume it's not working.
                # Increasing the timeout should have no effect,
                # the node is unresponsive at this point.
                requests.get(self.tm_status_endpoint, timeout=5)
                time.sleep(1)

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test."""
        # After the test, the node has hanged. We need to kill it and not stop it.
        cls.tendermint_node._process.kill()
        cls.app_context.pop()
        shutil.rmtree(cls.tm_home, ignore_errors=True, onerror=readonly_handler)


class TestTendermintBufferWorking(BaseTendermintServerTest):
    """Test Tendermint buffer"""

    perform_monitoring = True
    debug_tendermint = True

    @wait_for_node_to_run
    def test_tendermint_buffer(self) -> None:
        """Test Tendermint buffer"""

        # Give the test 60 seconds for it to work
        for _ in range(60):
            try:
                res = requests.get(self.tm_status_endpoint, timeout=5)
                # We expect all responses to be OK
                assert res.status_code == 200
            except Exception as e:
                raise AssertionError(e)

            time.sleep(1)


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
