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

"""This module contains utilities for the 'counter_client' skill."""
# isort:skip_file # noqa
import base64
import datetime
import json
import struct

from packages.valory.protocols.http import (  # pylint: disable=no-name-in-module,import-error
    HttpMessage,
)


def decode_value(message: HttpMessage) -> int:
    """Decode the counter value."""
    content_bytes = message.body
    content = json.loads(content_bytes)
    counter_value_base64 = content["result"]["response"]["value"].encode("ascii")
    counter_value_bytes = base64.b64decode(counter_value_base64)
    counter_value, *_ = struct.unpack(">I", counter_value_bytes)
    return counter_value


def curdatetime() -> str:
    """Return current datetime in isoformat.

    This is a local method that does not depend on the global clock,
    so the usage of datetime.now() is not a problem here.

    :return: the current time in isoformat.
    """
    datetime.datetime.utcnow()
    return datetime.datetime.now().isoformat()
