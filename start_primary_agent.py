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
import os, ssl, certifi

os.environ["SSL_CERT_FILE"] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context


from datetime import *
import uuid
from agents.primary_agent.graph import MyGraph


graph = MyGraph().build_graph()

config = {
    "configurable": {                
        "thread_id": uuid.uuid4(),
        "ccdt_path": "agents/primary_agent/",
    }
}
     
_printed = set()

def process_message(user_input):    
    events = graph.stream({"messages": ("user", user_input), "flight_info": ""}, config, stream_mode="values")
    for event in events:
        message = event.get("messages")
        if message:
            if isinstance(message, list):
                message = message[-1]                
            if message.id not in _printed and message.type == "ai" and not message.tool_calls:
                print("\nAssistant:", message.content)                
                _printed.add(message.id)
                break

initial_msg = "Hi"
process_message(initial_msg)  
while True:
    text_input = input("\nUser: ")
    if text_input.lower() in ["quit", "exit", "q"]:        
        print("\nAssistant: Arrivederci e grazie!")
        break
    process_message(text_input)