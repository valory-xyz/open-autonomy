
#!/usr/bin/env python

# WS server example

import asyncio
import websockets
from packages.valory.skills.abstract_round_abci.serializer import DictProtobufStructSerializer


PORT = 9999

connected = set()


async def handler(websocket, path):
    # at the end of a period
    # each agent sends a copy of their shared state to the server
    # - all observations, the source of the observation and the final aggregate estimate
    # deduplicate the data
    connected.add(websocket)

    try:
        async for message in websocket:
            data = DictProtobufStructSerializer.decode(message)
            print(f"> here's some:\n{data}")
    except websockets.exceptions.ConnectionClosed as e:
        print("Agent disconnected")
    finally:
        connected.remove(websocket)
    # data = await websocket.recv()
    # print(f">here's some {data}")


async def main():
    async with websockets.serve(handler, "127.0.0.1", PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
# start_server = websockets.serve(handler, "127.0.0.1", PORT)
# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()

