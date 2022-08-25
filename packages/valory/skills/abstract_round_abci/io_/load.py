# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
import os.path
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
    def load_single_file(self, path: str) -> SupportedSingleObjectType:
        """Load a single file."""

    def load(self, path: str, multiple: bool) -> SupportedObjectType:
        """Load one or more files.

        :param path: the path to the file to load. If multiple, then the path should be a folder with the files.
        :param multiple: whether multiple files are expected to be loaded. The path should be a folder with the files.
        :return: the loaded file.
        """
        if multiple:
            if not os.path.isdir(path):  # pragma: no cover
                raise ValueError(
                    f"Cannot load multiple files from `{path}`! "
                    f"Please make sure that the path is a folder containing the files."
                )

            objects = {}
            for filename in os.listdir(path):
                filename = os.fsdecode(filename)
                filepath = os.path.join(path, filename)
                objects[filename] = self.load_single_file(filepath)

            return objects

        return self.load_single_file(path)


class JSONLoader(AbstractLoader):
    """A JSON file loader."""

    def load_single_file(self, path: str) -> NativelySupportedSingleObjectType:
        """Read a json file.

        :param path: the path to retrieve the json file from.
        :return: the deserialized json file's content.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except OSError as e:  # pragma: no cover
            raise IOError(f"Path '{path}' could not be found!") from e

        except json.JSONDecodeError as e:  # pragma: no cover
            raise IOError(f"File '{path}' has an invalid JSON encoding!") from e

        except ValueError as e:  # pragma: no cover
            raise IOError(f"There is an encoding error in the '{path}' file!") from e


class Loader(AbstractLoader):
    """Class which loads files."""

    def __init__(self, filetype: Optional[Any], custom_loader: CustomLoaderType):
        """Initialize a `Loader`."""
        self._filetype = filetype
        self._custom_loader = custom_loader
        self.__filetype_to_loader: Dict[SupportedFiletype, SupportedLoaderType] = {
            SupportedFiletype.JSON: JSONLoader().load_single_file,
        }

    def load_single_file(self, path: str) -> SupportedSingleObjectType:
        """Load a single file."""
        loader = self._get_single_loader_from_filetype()
        return loader(path)

    def _get_single_loader_from_filetype(self) -> SupportedLoaderType:
        """Get a file loader from a given filetype or keep a custom loader."""
        if self._filetype is not None:
            return self.__filetype_to_loader[self._filetype]

        if self._custom_loader is not None:  # pragma: no cover
            return self._custom_loader

        raise ValueError(  # pragma: no cover
            "Please provide either a supported filetype or a custom loader function."
        )
