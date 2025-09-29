# agents/primary_agent/graph.py
# -*- coding: utf-8 -*-
"""
Graph definition for the Primary Agent.
Uses Ollama (local mistral) as the LLM backend.
"""

import subprocess
import json
from langgraph.graph import StateGraph, START, END


class MyGraph:
    def __init__(self):
        self.builder = StateGraph(dict)

    def _ollama_chat_cli(self, prompt: str) -> str:
        """
        Call Ollama locally via CLI and return the model response.
        """
        try:
            result = subprocess.run(
                ["ollama", "run", "mistral"],
                input=prompt.encode("utf-8"),
                capture_output=True,
                check=True,
            )
            return result.stdout.decode("utf-8").strip()
        except Exception as e:
            return f"[echo] {prompt} (Ollama error: {e})"

    def _assistant_node(self, state: dict) -> dict:
        """
        Node function for handling assistant replies.
        """
        user_message = None
        messages = state.get("messages")
        if isinstance(messages, tuple) and messages[0] == "user":
            user_message = messages[1]
        elif isinstance(messages, str):
            user_message = messages

        if not user_message:
            return {"messages": ("ai", "[echo] (empty)")}

        response = self._ollama_chat_cli(user_message)
        return {"messages": ("ai", response)}

    def build_graph(self, debug_enabled=False):
        """
        Build and return the compiled graph.
        """
        self.builder.add_node("assistant", self._assistant_node)
        self.builder.add_edge(START, "assistant")
        self.builder.add_edge("assistant", END)

        return self.builder.compile()
