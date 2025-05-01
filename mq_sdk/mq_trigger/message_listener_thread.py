# -*- coding: utf-8 -*-
# © Copyright IBM Corporation 2024, 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import threading
import time
import json

from mq_sdk.mq_agent.MQResponse import MQResponse
from mq_sdk.utilities.types import Message


class MessageListenerThread(threading.Thread):
    def __init__(self,
                ccdt_path: str,
                on_icoming_message):
        super().__init__()
        self.responder = MQResponse(
            ccdt_path=ccdt_path
        ) 
        self.on_incoming_message = on_icoming_message
        self.responder.perform_connection()
        self._stop_event = threading.Event()

    def send_reply(self, md , message):
        self.responder.respondToRequest(message, md)

    def run(self):
        while not self._stop_event.is_set():
            try:
                md, msgObject = self.responder.perform_get()
                if md is not None and msgObject is not None:
                    try:
                        msgObject_ = msgObject
                        print(f'MD type {type(md)}')
                        msg = Message(**json.loads(msgObject_))
                        msg.mqmd = md
                        self.on_incoming_message(msg)
                    except Exception as e:
                        print(f"Error parsing message: {e}")
                   
            except Exception as e:
                print(f"Error in MessageListenerThread: {e}")
            
    def stop(self):
        self._stop_event.set()
