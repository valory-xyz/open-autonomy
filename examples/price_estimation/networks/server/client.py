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

"""Client for testing"""

import random
import asyncio
import websockets
from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)


async def send_data() -> None:
    """Send data"""
    url = "ws://192.168.1.102:8080/"
    period_count = random.randint(0, 10)
    data = {
        "period_count": period_count,
        "db_content": {"nested": True, "value": 2, "recursive": {"value": True}},
    }
    try:
        async with websockets.connect(url) as websocket:
            message = DictProtobufStructSerializer.encode(data)
            await websocket.send(message)
    except ConnectionRefusedError as e:
        print(f"Could not send message:\n{e}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed:\n{e}")


def main():
    """Main"""
    asyncio.get_event_loop().run_until_complete(send_data())


if __name__ == "__main__":
    main()
