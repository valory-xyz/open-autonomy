# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Test log parser."""

import tempfile
from pathlib import Path

from autonomy.analyse.logs.collection import LogCollection


LOGS = """[2023-09-26 06:27:56,015] [INFO] [agent] Entered in the 'check_transaction_history_behaviour' behaviour
[2023-09-26 06:27:56,078] [ERROR] [agent] get_safe_nonce unsuccessful! Received: Message(sender=valory/ledger:0.19.0,to=valory/trader_abci:0.1.0,code=500,data=b'',dialogue_reference=('974278ff7b4e00019f7542a193987a8359b1c785d11a98a84bfaff2ea77b1e8f', '6b8e33fe183de2ac45e8d8f9625db5562b6230677fdc6995efc4ce05c798f83a'),message=Traceback (most recent call last):

  File "/usr/lib/python3.10/http/client.py", line 287, in _read_status
    raise RemoteDisconnected("Remote end closed connection without"

http.client.RemoteDisconnected: Remote end closed connection without response


During handling of the above exception, another exception occurred:


Traceback (most recent call last):

  File "/usr/lib/python3.10/http/client.py", line 287, in _read_status
    raise RemoteDisconnected("Remote end closed connection without"

urllib3.exceptions.ProtocolError: ('Connection aborted.', RemoteDisconnected('Remote end closed co,message_id=-1,performative=error,target=1)
[2023-09-26 06:27:56,103] [INFO] [agent] arrived block with timestamp: 2023-09-26 06:27:55.040545
"""

LOGS_CLEAN = """Entered in the 'check_transaction_history_behaviour' behaviour
get_safe_nonce unsuccessful! Received: Message(sender=valory/ledger:0.19.0,to=valory/trader_abci:0.1.0,code=500,data=b'',dialogue_reference=('974278ff7b4e00019f7542a193987a8359b1c785d11a98a84bfaff2ea77b1e8f', '6b8e33fe183de2ac45e8d8f9625db5562b6230677fdc6995efc4ce05c798f83a'),message=Traceback (most recent call last):
File "/usr/lib/python3.10/http/client.py", line 287, in _read_status
raise RemoteDisconnected("Remote end closed connection without"
http.client.RemoteDisconnected: Remote end closed connection without response
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
File "/usr/lib/python3.10/http/client.py", line 287, in _read_status
raise RemoteDisconnected("Remote end closed connection without"
urllib3.exceptions.ProtocolError: ('Connection aborted.', RemoteDisconnected('Remote end closed co,message_id=-1,performative=error,target=1)
arrived block with timestamp: 2023-09-26 06:27:55.040545
"""


def test_multiline_parse() -> None:
    """Test multiline logs parsing."""

    with tempfile.TemporaryDirectory() as temp_dir:
        file = Path(temp_dir, "log.txt")
        file.write_text(LOGS)
        parsed = "\n".join(list(map(lambda x: x[2], LogCollection.parse(file=file))))

        for line in LOGS_CLEAN.split("\n"):
            assert line in parsed
