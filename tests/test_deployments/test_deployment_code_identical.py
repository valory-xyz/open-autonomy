
from typing import List, Type
import difflib
import inspect
import logging

import pytest

from deployments.Dockerfiles.localnode.tendermint import (
    StoppableThread as DeploymentTread,
    TendermintParams as DeploymentParams,
    TendermintNode as DeploymentNode,
)

from packages.valory.connections.abci.connection import (
    StoppableThread as PackageTread,
    TendermintParams as PackageParams,
    TendermintNode as PackageNode,
)


@pytest.mark.parametrize(
    "deployment_cls, package_cls", [
        (DeploymentTread, PackageTread),
        (DeploymentParams, PackageParams),
        (DeploymentNode, PackageNode),
    ]
)
def test_deployment_class_identical(deployment_cls: Type, package_cls: Type) -> None:
    """Assert TendermintParams code is identical"""

    def get_lines(cls: Type) -> List[str]:
        return inspect.getsource(cls).splitlines(keepends=False)

    p_code, d_code = map(get_lines, (deployment_cls, package_cls))
    differences = difflib.unified_diff(p_code, d_code, lineterm="")
    report = "\n".join(differences)
    if report:
        logging.error(report)
    assert not report
