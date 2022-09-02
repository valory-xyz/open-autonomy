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

"""This module contains all the interaction operations of the behaviours with IPFS."""


import os
from shutil import rmtree
from typing import Any, Optional, Type

from aea_cli_ipfs.ipfs_utils import DownloadError, IPFSTool, NodeError
from ipfshttpclient.exceptions import ErrorResponse

from packages.valory.skills.abstract_round_abci.io_.load import (
    CustomLoaderType,
    Loader,
    SupportedFiletype,
    SupportedObjectType,
)
from packages.valory.skills.abstract_round_abci.io_.store import (
    CustomStorerType,
    Storer,
)


class IPFSInteractionError(Exception):
    """A custom exception for IPFS interaction errors."""


class IPFSInteract:
    """Class for interacting with IPFS."""

    def __init__(
        self, domain: str, loader_cls: Type = Loader, storer_cls: Type = Storer
    ):
        """Initialize an `IPFSInteract`.

        :param domain: the IPFS domain name.
        """
        try:
            # Create an IPFS tool.
            self.__ipfs_tool = IPFSTool(domain)
            # Check IPFS node.
            self.__ipfs_tool.check_ipfs_node_running()
            # Set loader/storer class.
            self._loader_cls = loader_cls
            self._storer_cls = storer_cls
        except (NodeError, Exception) as e:  # pragma: no cover
            raise IPFSInteractionError(str(e)) from e

    @staticmethod
    def __remove_filepath(filepath: str) -> None:
        """Remove a file or a folder. If filepath is not a file or a folder, an `IPFSInteractionError` is raised."""
        if os.path.isfile(filepath):
            os.remove(filepath)
        elif os.path.isdir(filepath):
            rmtree(filepath)
        else:  # pragma: no cover
            raise IPFSInteractionError(f"`{filepath}` is not an existing filepath!")

    def _send(self, filepath: str) -> str:
        """Send a file to the IPFS node.

        :param filepath: the filepath of the file or folder to send
        :return: the file's hash
        """
        try:
            _, hash_, _ = self.__ipfs_tool.add(filepath)
        except ValueError as e:  # pragma: no cover
            raise IPFSInteractionError(str(e)) from e
        finally:
            self.__remove_filepath(filepath)

        return hash_

    def _download(
        self,
        hash_: str,
        target_dir: str,
        multiple: bool = False,
        filename: Optional[str] = None,
    ) -> str:
        """Download a file from the IPFS node.

        :param hash_: hash of file to download
        :param target_dir: directory to place downloaded file
        :param multiple: whether multiple files are expected to be downloaded. The hash should be a folder's hash.
        :param filename: the original name of the file to download
        :return: the filepath of the downloaded file
        """
        if multiple:
            # IPFS tool creates a folder named as the basename of `target_dir` inside `target_dir`.
            filepath = os.path.join(target_dir, os.path.basename(target_dir))
        elif filename is not None:
            filepath = os.path.join(target_dir, filename)
        else:  # pragma: no cover
            raise IPFSInteractionError(
                "Filename cannot be `None` when uploading a single file!"
            )

        if os.path.exists(target_dir):  # pragma: no cover
            # TODO investigate why sometimes the path exists. It shouldn't, because `_send` removes it.
            self.__remove_filepath(target_dir)

        try:
            self.__ipfs_tool.download(hash_, target_dir)
        except (DownloadError, PermissionError, ErrorResponse) as e:  # pragma: no cover
            raise IPFSInteractionError(str(e)) from e

        return filepath

    def store_and_send(
        self,
        filepath: str,
        obj: SupportedObjectType,
        multiple: bool,
        filetype: Optional[SupportedFiletype] = None,
        custom_storer: Optional[CustomStorerType] = None,
        **kwargs: Any,
    ) -> str:
        """Temporarily store a file locally, in order to send it to IPFS and retrieve a hash, and then delete it."""
        filepath = os.path.normpath(filepath)
        if multiple:
            # Add trailing slash in order to treat path as a folder.
            filepath = os.path.join(filepath, "")
        storer = self._storer_cls(filetype, custom_storer, filepath)

        try:
            storer.store(obj, multiple, **kwargs)
        except IOError as e:  # pragma: no cover
            raise IPFSInteractionError(str(e)) from e

        return self._send(filepath)

    def get_and_read(  # pylint: disable=too-many-arguments
        self,
        hash_: str,
        target_dir: str,
        multiple: bool = False,
        filename: Optional[str] = None,
        filetype: Optional[SupportedFiletype] = None,
        custom_loader: CustomLoaderType = None,
    ) -> SupportedObjectType:
        """Get, store and read a file from IPFS."""
        target_dir = os.path.normpath(target_dir)
        filepath = self._download(hash_, target_dir, multiple, filename)
        loader = self._loader_cls(filetype, custom_loader)

        try:
            return loader.load(filepath, multiple)
        except IOError as e:  # pragma: no cover
            raise IPFSInteractionError(str(e)) from e
