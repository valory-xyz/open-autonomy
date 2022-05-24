import logging
import os
import stat
import shutil
import tempfile
import subprocess
from pathlib import Path
import pytest
from deployments.Dockerfiles.localnode.app import (
    load_genesis,
    get_defaults,
    override_config_toml,
    CONFIG_OVERRIDE,
    create_app,
)


# utility functions
def readonly_handler(func, path, execinfo) -> None:
    """If permission is readonly, we change and retry."""

    os.chmod(path, stat.S_IWRITE)
    func(path)


@pytest.fixture(scope="class")
def server_app():
    """We keep server app around for all integration tests."""
    yield create_app()


# unit tests
def test_tendermint_executable_found():
    assert shutil.which("tendermint"), "No `tendermint` executable found"


class BaseTendermintTest:

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test."""
        cls.tendermint = shutil.which("tendermint")
        cls.original_dir = os.getcwd()
        cls.dir = os.environ["TMHOME"] = tempfile.mkdtemp()
        os.chdir(cls.dir)
        command = [cls.tendermint, 'init', 'validator', f'--home', f'{cls.dir}']
        process = subprocess.Popen(command, stderr=subprocess.PIPE)
        _, stderr = process.communicate()
        assert not stderr, stderr

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test."""
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.dir, onerror=readonly_handler)
        assert not os.path.exists(cls.dir)


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
        assert not any(old in content and new not in content for old, new in CONFIG_OVERRIDE)


class TestTendermintServerApp(BaseTendermintTest):
    """Test Tendermint server app"""

    @classmethod
    def setup_class(cls) -> None:
        super().setup_class()
        cls.proxy_app = os.environ["PROXY_APP"] = tempfile.mkdtemp()

    def test_app(self, server_app):
        assert server_app == 1

