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

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode


def create_tool_node_with_fallback(tools: list) -> dict:
    """Creates a tool node with fallback error handling."""
    
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_general_error)], exception_key="error"
    )

def handle_tool_general_error(state) -> dict:
    """Handles general tool errors."""
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def extract_message_from_event(event: dict) -> str:
    message = event.get("messages")        
    if message:
        if isinstance(message, list):
            message = message[-1]            
        return message.content
    return None, None