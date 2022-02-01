#!/usr/bin/env python

import asyncio

import websockets


connected = set()


async def handler(websocket):
    while True:
        message = await websocket.recv()
        print(message)


# async def handler(websocket, path):
#     # Register.
#     connected.add(websocket)
#     try:
#         async for message in websocket:
#             await websocket.send(f"listening to {message}")
#         # Broadcast a message to all connected clients.
#         # await asyncio.wait([ws.send("Hello!") for ws in connected])
#         # await asyncio.sleep(10)
#     finally:
#         # Unregister.
#         connected.remove(websocket)


# async def main():
#     async with websockets.serve(handler, "", 8001):
#         await asyncio.Future()  # run forever
#
#
# if __name__ == "__main__":
#     asyncio.run(main())

