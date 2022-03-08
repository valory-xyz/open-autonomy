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

"""This module contains all the storing operations of the behaviours."""


import json
import os.path
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast

import joblib
import pandas as pd
from pmdarima.pipeline import Pipeline

from packages.valory.skills.abstract_round_abci.io.paths import create_pathdirs


StoredJSONType = Union[dict, list]
NativelySupportedSingleObjectType = Union[StoredJSONType, Pipeline, pd.DataFrame]
NativelySupportedMultipleObjectsType = Dict[str, NativelySupportedSingleObjectType]
NativelySupportedObjectType = Union[
    NativelySupportedSingleObjectType, NativelySupportedMultipleObjectsType
]
NativelySupportedStorerType = Callable[[NativelySupportedObjectType, bool, Any], None]
CustomSingleObjectType = TypeVar("CustomSingleObjectType")
CustomMultipleObjectsType = Dict[str, CustomSingleObjectType]
CustomObjectType = Union[CustomSingleObjectType, CustomMultipleObjectsType]
CustomStorerType = Callable[[CustomObjectType, Any], None]
SupportedSingleObjectType = Union[NativelySupportedObjectType, CustomObjectType]
SupportedMultipleObjectsType = Dict[str, SupportedSingleObjectType]
SupportedObjectType = Union[SupportedSingleObjectType, SupportedMultipleObjectsType]
SupportedStorerType = Union[NativelySupportedStorerType, CustomStorerType]


class SupportedFiletype(Enum):
    """Enum for the supported filetypes of the IPFS interacting methods."""

    JSON = auto()
    PM_PIPELINE = auto()
    CSV = auto()


class AbstractStorer(ABC):
    """An abstract `Storer` class."""

    def __init__(self, path: str):
        """Initialize an abstract storer."""
        self._path = path
        # Create the dirs of the path if it does not exist.
        create_pathdirs(path)

    @staticmethod
    @abstractmethod
    def store_single_file(
        filename: str, obj: SupportedSingleObjectType, **kwargs: Any
    ) -> None:
        """Store a single file."""

    def store(self, obj: SupportedObjectType, multiple: bool, **kwargs: Any) -> None:
        """Store one or multiple files."""
        if multiple:
            if not isinstance(obj, dict):  # pragma: no cover
                raise ValueError(
                    f"Cannot store multiple files of type {type(obj)}!"
                    f"Should be a dictionary of filenames mapped to their objects."
                )
            for filename, single_obj in obj.items():
                filename = os.path.join(self._path, filename)
                self.store_single_file(filename, single_obj, **kwargs)
        else:
            self.store_single_file(self._path, obj, **kwargs)


class JSONStorer(AbstractStorer):
    """A JSON file storer."""

    @staticmethod
    def store_single_file(
        filename: str, obj: NativelySupportedObjectType, **kwargs: Any
    ) -> None:
        """Store a JSON."""
        if not any(isinstance(obj, type_) for type_ in (dict, list)):
            raise ValueError(  # pragma: no cover
                f"`JSONStorer` cannot be used with a {type(obj)}! Only with a {StoredJSONType}"
            )

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=4)
        except (TypeError, OSError) as e:  # pragma: no cover
            raise IOError(str(e)) from e


class CSVStorer(AbstractStorer):
    """A CSV file storer."""

    @staticmethod
    def store_single_file(
        filename: str, obj: NativelySupportedObjectType, **kwargs: Any
    ) -> None:
        """Store a pandas dataframe."""
        if not isinstance(obj, pd.DataFrame):
            raise ValueError(  # pragma: no cover
                f"`JSONStorer` cannot be used with a {type(obj)}! Only with a {pd.DataFrame}"
            )

        index = kwargs.get("index", False)

        try:
            obj.to_csv(filename, index=index)
        except (TypeError, OSError) as e:  # pragma: no cover
            raise IOError(str(e)) from e


class ForecasterStorer(AbstractStorer):
    """A pmdarima Pipeline storer."""

    @staticmethod
    def store_single_file(
        filename: str, obj: NativelySupportedObjectType, **kwargs: Any
    ) -> None:
        """Store a pmdarima Pipeline."""
        if not isinstance(obj, Pipeline):
            raise ValueError(  # pragma: no cover
                f"`JSONStorer` cannot be used with a {type(obj)}! Only with a {Pipeline}"
            )

        try:
            joblib.dump(obj, filename)
        except (ValueError, OSError) as e:  # pragma: no cover
            raise IOError(str(e)) from e


class Storer(CSVStorer, ForecasterStorer, JSONStorer):
    """Class which stores files."""

    def __init__(
        self,
        filetype: Optional[SupportedFiletype],
        custom_storer: Optional[CustomStorerType],
        path: str,
    ):
        """Initialize a `Storer`."""
        super().__init__(path)
        self.__filetype_to_storer: Dict[SupportedFiletype, SupportedStorerType] = {
            SupportedFiletype.JSON: cast(
                Callable[[StoredJSONType, Any], None], JSONStorer(path).store
            ),
            SupportedFiletype.PM_PIPELINE: cast(
                Callable[[Pipeline, Any], None], ForecasterStorer(path).store
            ),
            SupportedFiletype.CSV: cast(
                Callable[[pd.DataFrame, Any], None], CSVStorer(path).store
            ),
        }

        self.storer = self._get_storer_from_filetype(filetype, custom_storer)

    def _get_storer_from_filetype(
        self,
        filetype: Optional[SupportedFiletype],
        custom_storer: Optional[CustomStorerType],
    ) -> SupportedStorerType:
        """Get a file storer from a given filetype or keep a custom storer."""
        if filetype is not None:
            return self.__filetype_to_storer[filetype]

        if custom_storer is not None:  # pragma: no cover
            return custom_storer

        raise ValueError(  # pragma: no cover
            "Please provide either a supported filetype or a custom storing function."
        )

    def store(self, obj: SupportedObjectType, multiple: bool, **kwargs: Any) -> None:
        """Store one or more objects."""
        self.storer(obj, multiple, **kwargs)  # type: ignore
