# !/usr/bin/env python

# WS client example

import asyncio
import websockets
from packages.valory.skills.abstract_round_abci.serializer import DictProtobufStructSerializer
# from typing import Generator
# from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
# from packages.valory.skills.abstract_round_abci.base import DegenerateRound
# from packages.valory.skills.abstract_round_abci.behaviours import (
#     AbstractRoundBehaviour,
#     BaseState,
# )
#
# benchmark_tool = BenchmarkTool()
#
#
# class BroadcastStateToServerRound(DegenerateRound):
#     """Broadcast data to server"""
#
#
# class BroadcastStateBehaviour(BaseState):
#     """Broadcast period state data to server"""
#
#     state_id = "broadcast"
#     matching_round = BroadcastStateToServerRound
#
#     def async_act(self) -> Generator:
#         """
#         Do the action.
#
#         Take the period state and broadcast it to the server
#         """
#
#         with benchmark_tool.measure(self).local():
#             period_count = self.current_period_count
#             data = self.period_state.db.get_all()
#             self.context.logger.info(f"Broadcasting data to server:\n{data}")
#             yield from self.send_to_server(data)
#             yield from self.wait_until_round_end()
#
#     async def send_to_server(self, data):
#         """Send data to the server"""
#
#         url = "ws://127.0.0.1:9999/"
#
#         try:
#             async with websockets.connect(url) as websocket:
#                 await websocket.send(data)
#         except ConnectionRefusedError as e:
#             self.context.logger.warning(f'Could not send message:\n{e}')
#         except websockets.exceptions.ConnectionClosed as e:
#             self.context.logger.warning(f'Connection closed:\n{e}')
#
#         self.set_done()


async def message():
    url = "ws://127.0.0.1:9999/"
    data = {"green": "eggs", "1": 2}
    try:
        async with websockets.connect(url) as websocket:
            message = DictProtobufStructSerializer.encode(data)
            await websocket.send(message)
    except ConnectionRefusedError as e:
        print(f'Could not send message:\n{e}')
    except websockets.exceptions.ConnectionClosed as e:
        print(f'Connection closed:\n{e}')


asyncio.get_event_loop().run_until_complete(message())
