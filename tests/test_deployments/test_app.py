
import logging
import os
import stat
import shutil
import urllib
import socket
import tempfile
import subprocess
from pathlib import Path
import requests
import time
from deployments.Dockerfiles.localnode.app import (
    load_genesis,
    get_defaults,
    override_config_toml,
    CONFIG_OVERRIDE,
    create_app,
)
from deployments.Dockerfiles.localnode.tendermint import (
    DEFAULT_RPC_LADDR
)


ENCODING = "utf-8"
VERSION = "0.34.11"
HTTP = "http://"

parse_result = urllib.parse.urlparse(DEFAULT_RPC_LADDR)
IP, PORT = parse_result.hostname, parse_result.port


# utility functions
def readonly_handler(func, path, execinfo) -> None:
    """If permission is readonly, we change and retry."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def port_is_open(ip: str, port: int) -> bool:
    """Assess whether a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_open = sock.connect_ex((ip, port)) == 0
    sock.close()
    return is_open


def wait_for_node_to_run(func):
    """Wait for Tendermint node to run"""
    def wrapper(*args, **kwargs):
        i, max_retries = 0, 5
        while not port_is_open(IP, PORT) and i < max_retries:
            logging.debug(f"waiting for node... t={i}")
            i += time.sleep(1) or 1
        response = requests.get(f"{HTTP}{IP}:{PORT}/status")
        success = response.status_code == 200
        logging.debug(response.json())
        assert success, "Tendermint node not running"
        func(*args, **kwargs)
    return wrapper


# base classes
class BaseTendermintTest:
    """BaseTendermintTest"""

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test."""
        cls.tendermint = shutil.which("tendermint")
        cls.original_dir = os.getcwd()
        cls.dir = os.environ["TMHOME"] = tempfile.mkdtemp()
        cls.path = Path(cls.dir)
        assert not os.listdir(str(cls.path))

        os.chdir(cls.dir)
        command = [cls.tendermint, 'init', 'validator', '--home',  f'{cls.dir}']
        process = subprocess.Popen(command, stderr=subprocess.PIPE)
        _, stderr = process.communicate()
        assert not stderr, stderr

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test."""
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.dir, ignore_errors=True, onerror=readonly_handler)


class BaseTendermintServerTest(BaseTendermintTest):
    """Test Tendermint server app"""

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test."""
        super().setup_class()
        cls.proxy_app = os.environ["PROXY_APP"] = "kvstore"
        cls.create_empty_blocks = os.environ["CREATE_EMPTY_BLOCKS"] = "true"
        os.environ["LOG_FILE"] = str(cls.path / "tendermint.log")
        logging.info(f"logfile: {os.environ['LOG_FILE']}")
        cls.app, cls.tendermint_node = create_app(Path(cls.dir) / "tm_state")
        cls.app.config["TESTING"] = True
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test."""
        cls.app_context.pop()
        cls.tendermint_node.stop()
        super().teardown_class()


# unit tests
def test_tendermint_executable_found():
    assert shutil.which("tendermint"), "No `tendermint` executable found"
    output = subprocess.check_output(["tendermint", "version"])
    assert output.decode(ENCODING).strip() == VERSION


class TestTendermintServerUtilityFunctions(BaseTendermintTest):
    """Test Tendermint server utility functions"""

    def test_load_genesis(self):
        expected_keys = {'genesis_time', 'chain_id', 'initial_height', 'consensus_params', 'validators', 'app_hash'}
        json = load_genesis()
        assert set(json.keys()) == expected_keys

    def test_get_defaults(self):
        expected_keys = {'genesis_time', 'app_hash'}
        defaults = get_defaults()
        assert set(defaults.keys()) == expected_keys

    def test_override_config_toml(self):
        path = Path(os.environ["TMHOME"]) / "config" / "config.toml"
        assert path.is_file(), f"not a file: {path}"
        content = path.read_text("utf-8")
        assert all(old in content and new not in content for old, new in CONFIG_OVERRIDE)
        override_config_toml()
        content = path.read_text("utf-8")
        assert not any(old in content or new not in content for old, new in CONFIG_OVERRIDE)


class TestTendermintServerApp(BaseTendermintServerTest):
    """Test Tendermint server app"""

    @wait_for_node_to_run
    def test_files_exist(self):
        """Test that the necessary files are present"""

        def remove_prefix(text: str, prefix: str):
            """str.removeprefix only from python3.9 onward"""
            return text[text.startswith(prefix) and len(prefix):]

        expected_file_names = [
            '/config',
            '/data',
            '/config/config.toml',
            '/config/priv_validator_key.json',
            '/config/genesis.json',
            '/config/node_key.json',
            '/data/priv_validator_state.json',
        ]

        file_names = [remove_prefix(str(p), self.dir) for p in self.path.rglob('*')]
        # we may create extra files, just want to check these exist
        missing_files = set(expected_file_names).difference(file_names)
        assert not missing_files

    @wait_for_node_to_run
    def test_get_request_status(self):
        """Check local node is running"""
        response = requests.get(f"{HTTP}{IP}:{PORT}/status")
        data = response.json()
        assert data["result"]["node_info"]["version"] == VERSION

    @wait_for_node_to_run
    def test_handle_notfound(self):
        """Test handle not found"""
        with self.app.test_client() as client:
            response = client.get("/non_existing_endpoint")
            assert response.status_code == 404

    @wait_for_node_to_run
    def test_get_app_hash(self):
        """Test get app hash"""
        time.sleep(3)  # requires some extra time!
        with self.app.test_client() as client:
            response = client.get("/app_hash")
            data = response.get_json()
            assert response.status_code == 200
            assert "error" not in data
            assert "app_hash" in data


class TestTendermintGentleResetServer(BaseTendermintServerTest):
    """Test Tendermint gentle reset"""

    @wait_for_node_to_run
    def test_gentle_reset(self):
        """Test gentle reset"""
        with self.app.test_client() as client:
            response = client.get("/gentle_reset")
            data = response.get_json()
            assert response.status_code == 200
            assert data["status"] is True


class TestTendermintHardResetServer(BaseTendermintServerTest):
    """Test Tendermint hard reset"""

    @wait_for_node_to_run
    def test_hard_reset(self):
        """Test hard reset"""
        with self.app.test_client() as client:
            response = client.get("/hard_reset")
            data = response.get_json()
            assert response.status_code == 200
            assert data["status"] is True


class TestTendermintLogMessages(BaseTendermintServerTest):
    """Test Tendermint message logging"""

    @wait_for_node_to_run
    def test_logs_after_stopping(self):

        def get_logs():
            with open(os.environ["LOG_FILE"], 'r') as f:
                lines = "".join(f.readlines())
            return lines

        def get_missing(messages):
            i, max_retries = 0, 5
            while messages and i < max_retries:
                i += time.sleep(1) or 1
                messages = [line for line in messages if line not in get_logs()]
            return messages

        before_stopping = [
            "Tendermint process started",
            "Monitoring thread started",
            "Starting multiAppConn service",
            "Starting localClient service",
            "This node is a validator",
        ]

        after_stopping = [
            "Monitoring thread terminated",
            "Tendermint process stopped",
        ]

        assert not get_missing(before_stopping)
        self.tendermint_node.stop()
        assert not get_missing(after_stopping)
