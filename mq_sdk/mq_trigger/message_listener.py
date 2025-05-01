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

from .message_listener_thread import MessageListenerThread

class MessageListener:
    def __init__(self, ccdt_path, on_message):
        self.listener = MessageListenerThread(
            ccdt_path,
            on_message
        )
        self.listener.start()


    def send_reply(self, md, message):
        self.listener.send_reply(md, message)

    def shutdown(self):
        self.listener.stop()
        self.listener.join()
