
import logging
import os
import stat
import shutil
import socket
import tempfile
import subprocess
from pathlib import Path
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


# utility functions
def readonly_handler(func, path, execinfo) -> None:
    """If permission is readonly, we change and retry."""

    os.chmod(path, stat.S_IWRITE)
    func(path)


def port_is_open(ip: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip, port))
    sock.close()
    return result == 0


# unit tests
def test_tendermint_executable_found():
    assert shutil.which("tendermint"), "No `tendermint` executable found"


class BaseTendermintTest:

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test."""
        cls.tendermint = shutil.which("tendermint")
        cls.original_dir = os.getcwd()

        cls.path = path = Path("/tmp/tmp_test/")
        if path.is_dir():
            shutil.rmtree(str(path), onerror=readonly_handler)
        path.mkdir()
        assert not os.listdir(str(path))

        cls.dir = os.environ["TMHOME"] = str(path).strip()  # tempfile.mkdtemp()
        os.chdir(cls.dir)
        command = [cls.tendermint, 'init', 'validator', '--home',  f'{cls.dir}']
        process = subprocess.Popen(command, stderr=subprocess.PIPE)
        _, stderr = process.communicate()
        logging.debug(f"{' '.join(command)}, stdout {_}")
        assert not stderr, stderr

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test."""
        os.chdir(cls.original_dir)
        # shutil.rmtree(cls.dir, onerror=readonly_handler)
        # assert not os.path.exists(cls.dir)


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


class TestTendermintServerApp(BaseTendermintTest):
    """Test Tendermint server app"""

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test."""
        super().setup_class()
        cls.proxy_app = os.environ["PROXY_APP"] = "tcp://0.0.0.0:26667"  # "tcp://0.0.0.0:8080"
        cls.create_empty_blocks = os.environ["CREATE_EMPTY_BLOCKS"] = "true"
        os.environ["LOG_FILE"] = str(cls.path / "tendermint.log")
        cls.app, cls.tendermint_node = create_app(Path(cls.dir) / "tm_state")
        cls.app.config["TESTING"] = True
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    def test_files_exist(self):
        """Test that the necessary files are present"""

        def remove_prefix(text, prefix):  # str.removeprefix only in python3.9
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

    def test_handle_notfound(self):
        with self.app.test_client() as client:
            response = client.get("/non_existing_endpoint")
            assert response.status_code == 404

    def test_status(self):
        # http://localhost:26657/status
        success = False
        with self.app.test_client() as client:
            for _ in range(3):
                response = client.get("/status")
                if response.status_code == 200:
                    success = True
                    break
                time.sleep(1)
        assert success

    def test_get_app_hash(self):
        """Test get app hash"""
        with self.app.test_client() as client:
            response = client.get("/app_hash")
            logging.error(response.get_json())
            assert response.status_code == 200
            assert not response.get_json().get("error")

    # def test_get_gentle_reset(self):
    #     """Test get app hash"""
    #     with self.app.test_client() as client:
    #         response = client.get("/gentle_reset")
    #         assert response.status_code == 200

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test."""
        cls.app_context.pop()
        cls.tendermint_node.stop()
        super().teardown_class()
