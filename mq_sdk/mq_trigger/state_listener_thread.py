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
import json

from ..utilities.subscriber import MQSubscriber


class StateBackgroundListener(threading.Thread):
    def __init__(self,
                ccdt_path: str,
                on_state_change):
        super().__init__()
        self.on_state_change = on_state_change
        self.subscriber = MQSubscriber(
            ccdt_path=ccdt_path
        ) 
        self.subscriber.subscribe()
        self._stop_event = threading.Event()

    def run(self):
        print('BackgroundListener:: Start listening...')
        md, gmo = self.subscriber.getMessageConfig()
        while not self._stop_event.is_set():
            try:
                md = self.subscriber.resetMD(md)
                messageJSON = self.subscriber.subscription.get(None, md, gmo)
                msgObject = json.loads(messageJSON.decode())
                self.on_state_change(msgObject)
            except Exception as e:
                if not "MQRC_NO_MSG_AVAILABLE" in str(e):
                    print(f'BackgroundListener error: {e}')
                    return

    def stop(self):
        self._stop_event.set()
