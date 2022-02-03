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
from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional

import joblib
import pandas as pd

from packages.valory.skills.abstract_round_abci.io.store import (
    CustomObjectType,
    NativelySupportedObjectType,
    SupportedFiletype,
    SupportedObjectType,
)


CustomLoaderType = Optional[Callable[[str], CustomObjectType]]
SupportedLoaderType = Callable[[str], SupportedObjectType]


class AbstractLoader(ABC):  # pylint: disable=too-few-public-methods
    """An abstract `Loader` class."""

    @abstractmethod
    def load(self, path: str) -> SupportedObjectType:
        """Load a file."""


class CSVLoader(AbstractLoader):  # pylint: disable=too-few-public-methods
    """A csv files Loader."""

    def load(self, path: str) -> NativelySupportedObjectType:
        """Read a pandas dataframe from a csv file.

        :param path: the path of the csv.
        :return: the pandas dataframe.
        """
        try:
            return pd.read_csv(path)
        except FileNotFoundError as e:
            raise IOError(f"File {path} was not found!") from e


class ForecasterLoader(AbstractLoader):  # pylint: disable=too-few-public-methods
    """A `pmdarima` forecaster loader."""

    def load(self, path: str) -> NativelySupportedObjectType:
        """Load a `pmdarima` forecaster.

        :param path: path to store the forecaster.
        :return: a `pmdarima.pipeline.Pipeline`.
        """
        try:
            return joblib.load(path)
        except (NotADirectoryError, FileNotFoundError) as e:
            raise IOError(f"Could not detect {path}!") from e


class JSONLoader(AbstractLoader):  # pylint: disable=too-few-public-methods
    """A JSON file loader."""

    def load(self, path: str) -> NativelySupportedObjectType:
        """Read a json file.

        :param path: the path to retrieve the json file from.
        :return: the deserialized json file's content.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except OSError as e:
            raise IOError(f"Path '{path}' could not be found!") from e

        except json.JSONDecodeError as e:
            raise IOError(f"File '{path}' has an invalid JSON encoding!") from e

        except ValueError as e:
            raise IOError(f"There is an encoding error in the '{path}' file!") from e


class Loader(
    CSVLoader, ForecasterLoader, JSONLoader
):  # pylint: disable=too-few-public-methods
    """Class which loads files."""

    def __init__(
        self, filetype: Optional[SupportedFiletype], custom_loader: CustomLoaderType
    ):
        """Initialize a `Loader`."""
        self.__filetype_to_loader: Dict[SupportedFiletype, SupportedLoaderType] = {
            SupportedFiletype.JSON: JSONLoader().load,
            SupportedFiletype.PM_PIPELINE: ForecasterLoader().load,
            SupportedFiletype.CSV: CSVLoader().load,
        }

        self.loader = self._get_loader_from_filetype(filetype, custom_loader)

    def _get_loader_from_filetype(
        self, filetype: Optional[SupportedFiletype], custom_loader: CustomLoaderType
    ) -> SupportedLoaderType:
        """Get a file loader from a given filetype or keep a custom loader."""
        if filetype is not None:
            return self.__filetype_to_loader[filetype]

        if custom_loader is not None:
            return custom_loader

        raise ValueError(
            "Please provide either a supported filetype or a custom loader function."
        )

    def load(self, path: str) -> SupportedObjectType:
        """Load a file from a given path."""
        return self.loader(path)
