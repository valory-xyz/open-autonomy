
from typing import List, Type
import difflib
import inspect
import logging

from deployments.Dockerfiles.localnode.tendermint import (
    TendermintParams as DeploymentParams,
    TendermintNode as DeploymentNode,
)

from packages.valory.connections.abci.connection import (
    TendermintParams as PackageParams,
    TendermintNode as PackageNode,
)


def test_params_class_identical():
    """Assert TendermintParams code is identical"""

    def get_lines(cls: Type) -> List[str]:
        return inspect.getsource(cls).splitlines(keepends=False)

    p_code, d_code = map(get_lines, (PackageParams, DeploymentParams))
    p_code, d_code = map(get_lines, (PackageNode, DeploymentNode))
    differences = difflib.unified_diff(p_code, d_code, lineterm="")
    report = "\n".join(differences)
    if report:
        logging.error(report)
    assert not report


def test_node_class_identical():
    """Assert TendermintNode code is identical"""
