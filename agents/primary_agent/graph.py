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

from langgraph.graph import StateGraph 
from langgraph.graph import StateGraph, START 
from langgraph.prebuilt import tools_condition 
from langgraph.checkpoint.memory import MemorySaver
from agents.primary_agent.assistant import (
    EventAssistant,    
    State, 
)
from agents.primary_agent.utilities import create_tool_node_with_fallback

class MyGraph:
    builder:StateGraph = None
    memory: MemorySaver = None

    def __init__(self) -> None:
        self.memory = MemorySaver()
        self.builder = StateGraph(State)

    def build_graph(self):
        assistant = EventAssistant()
        self.builder.add_node("assistant", assistant)
        self.builder.add_node("tools", create_tool_node_with_fallback(assistant.get_tools()))
        self.builder.add_edge(START, "assistant")
        self.builder.add_conditional_edges(
            "assistant",
            tools_condition,
        )
        self.builder.add_edge("tools", "assistant")
        return self.builder.compile(checkpointer=self.memory)
    