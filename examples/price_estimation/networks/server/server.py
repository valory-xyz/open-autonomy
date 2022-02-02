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

"""Server for testing"""

import asyncio
import websockets
from packages.valory.skills.abstract_round_abci.serializer import (
    DictProtobufStructSerializer,
)


PORT = 8080

connected = set()
period_data = {}


async def handler(websocket, path):
    """Handler"""
    # at the end of a period
    # each agent sends a copy of their shared state to the server
    # - all observations, the source of the observation and the final aggregate estimate
    # deduplicate the data
    # connected.add(websocket)

    try:
        async for message in websocket:
            data = DictProtobufStructSerializer.decode(message)
            period_count, content = data["period_count"], data["db_content"]
            if period_count not in period_data:
                period_data[period_count] = content
                print(f"> here's some new data:\n{period_count}: \t{content}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Agent disconnected:\n{e}")
    # finally:
    #     connected.remove(websocket)


async def main():
    """Main"""
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
