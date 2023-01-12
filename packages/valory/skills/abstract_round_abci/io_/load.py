# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""This module contains all the loading operations of the behaviours."""

import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from packages.valory.skills.abstract_round_abci.io_.store import (
    CustomObjectType,
    NativelySupportedSingleObjectType,
    SupportedFiletype,
    SupportedObjectType,
    SupportedSingleObjectType,
)


CustomLoaderType = Optional[Callable[[str], CustomObjectType]]
SupportedLoaderType = Callable[[str], SupportedSingleObjectType]


class AbstractLoader(ABC):
    """An abstract `Loader` class."""

    @abstractmethod
    def load_single_object(
        self, serialized_object: str
    ) -> NativelySupportedSingleObjectType:
        """Load a single object."""

    def load(self, serialized_objects: Dict[str, str]) -> SupportedObjectType:
        """
        Load one or more serialized objects.

        :param serialized_objects: A mapping of filenames to serialized object they contained.
        :return: the loaded file(s).
        """
        if len(serialized_objects) == 0:
            # no objects are present, raise an error
            raise ValueError('"serialized_objects" does not contain any objects')

        objects = {}
        for filename, body in serialized_objects.items():
            objects[filename] = self.load_single_object(body)

        if len(objects) > 1:
            # multiple object are present
            # we return them as mapping of
            # names and their value
            return objects

        # one object is present, we simply return it as an object, i.e. without its name
        _name, deserialized_body = objects.popitem()
        return deserialized_body


class JSONLoader(AbstractLoader):
    """A JSON file loader."""

    def load_single_object(
        self, serialized_object: str
    ) -> NativelySupportedSingleObjectType:
        """Read a json file.

        :param serialized_object: the file serialized into a JSON string.
        :return: the deserialized json file's content.
        """
        try:
            deserialized_file = json.loads(serialized_object)
            return deserialized_file
        except json.JSONDecodeError as e:  # pragma: no cover
            raise IOError(
                f"File '{serialized_object}' has an invalid JSON encoding!"
            ) from e
        except ValueError as e:  # pragma: no cover
            raise IOError(
                f"There is an encoding error in the '{serialized_object}' file!"
            ) from e


class Loader(AbstractLoader):
    """Class which loads objects."""

    def __init__(self, filetype: Optional[Any], custom_loader: CustomLoaderType):
        """Initialize a `Loader`."""
        self._filetype = filetype
        self._custom_loader = custom_loader
        self.__filetype_to_loader: Dict[SupportedFiletype, SupportedLoaderType] = {
            SupportedFiletype.JSON: JSONLoader().load_single_object,
        }

    def load_single_object(self, serialized_object: str) -> SupportedSingleObjectType:
        """Load a single file."""
        loader = self._get_single_loader_from_filetype()
        return loader(serialized_object)

    def _get_single_loader_from_filetype(self) -> SupportedLoaderType:
        """Get an object loader from a given filetype or keep a custom loader."""
        if self._filetype is not None:
            return self.__filetype_to_loader[self._filetype]

        if self._custom_loader is not None:  # pragma: no cover
            return self._custom_loader

        raise ValueError(  # pragma: no cover
            "Please provide either a supported filetype or a custom loader function."
        )
