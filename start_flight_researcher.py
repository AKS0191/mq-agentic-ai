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

import time
import uuid
from mq_sdk.mq_trigger.message_listener import MessageListener
from agents.flights_searcher.graph import MyGraph

from mq_sdk.utilities.types import Message

config = {
    "configurable": {                
        "thread_id": uuid.uuid4(),
        "ccdt_path": "agents/flights_searcher/",
    }
}

class TaskManager:
    _printed = set()
    def __init__(self, agent):                
        self.agent = agent                       
        self.message_listener = MessageListener(
            ccdt_path="agents/flights_searcher/",
            on_message=self.on_message
        )

    def on_message(self, incoming_message: Message):        
        msg = incoming_message.message
        thread_id = incoming_message.thread_id
        print(f'Message: {msg} in thread_id: {thread_id}')
        config["configurable"]["thread_id"] = thread_id
        events = self.agent.stream({"messages": ("human", msg), "flight_info": ""}, config, stream_mode="values")
        for event in events:
            message = event.get("messages")
            if message:
                if isinstance(message, list):
                    message = message[-1]
                if message.id not in self._printed and message.type == "ai" and not message.tool_calls:
                    self.message_listener.send_reply(incoming_message.mqmd, message.content)
                    print("\nAssistant:", message.content)
                    self._printed.add(message.id)
                    break


if __name__ == "__main__":
    graph = MyGraph().build_graph()
    assistant = TaskManager(agent=graph)
    try:
        while True:
            time.sleep(1)  
    except KeyboardInterrupt:
        print("\nStopping listener...")
        assistant.shutdown()       
