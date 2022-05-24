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

"""Base configurations."""

from collections import OrderedDict
from typing import Dict, FrozenSet, Optional, cast

from aea.configurations.data_types import PublicId
from aea.helpers.base import SimpleIdOrStr

from aea_swarm.configurations.constants import DEFAULT_SERVICE_FILE, SERVICE


class Service:  # pylint: disable=too-many-instance-attributes
    """Service package configuration."""

    default_configuration_filename = DEFAULT_SERVICE_FILE
    package_type = SERVICE
    schema = "service_schema.json"

    FIELDS_ALLOWED_TO_UPDATE: FrozenSet[str] = frozenset()
    __slots__ = (
        "name",
        "author",
        "version",
        "description",
        "aea_version",
        "license",
        "agent",
        "network",
        "number_of_agents",
    )

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: SimpleIdOrStr,
        author: SimpleIdOrStr,
        agent: PublicId,
        version: str = "",
        license_: str = "",
        aea_version: str = "",
        description: str = "",
        number_of_agents: int = 4,
        network: Optional[str] = None,
    ) -> None:
        """Initialise object."""

        self.name = name
        self.author = author
        self.agent = PublicId.from_str(str(agent))
        self.version = version
        self.license = license_
        self.aea_version = aea_version
        self.description = description
        self.number_of_agents = number_of_agents
        self.network = network

    @property
    def json(
        self,
    ) -> Dict:
        """Returns an ordered Dict for service config."""

        config = OrderedDict(
            {
                "name": self.name,
                "author": self.author,
                "agent": self.agent,
                "version": self.version,
                "license": self.license,
                "aea_version": self.aea_version,
                "description": self.description,
                "number_of_agents": self.number_of_agents,
                "network": self.network,
            }
        )

        return config

    @classmethod
    def from_json(cls, obj: Dict) -> "Service":
        """Initialize object from json."""

        params = dict(
            name=cast(str, obj.get("name")),
            author=cast(str, obj.get("author")),
            agent=cast(str, obj.get("agent")),
            version=cast(str, obj.get("version")),
            license_=cast(str, obj.get("license")),
            aea_version=cast(str, obj.get("aea_version")),
            description=cast(str, obj.get("description")),
            number_of_agents=cast(int, obj.get("number_of_agents")),
            network=cast(str, obj.get("network")),
        )

        return cls(**params)  # type: ignore
