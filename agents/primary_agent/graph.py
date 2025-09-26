from .event_assistant import EventAssistant

def build_graph(self, debug_enabled=False):
    """
    Builds the agent graph connecting assistant and tools.
    Returns compiled graph or None if failed.
    """
    try:
        if debug_enabled:
            print("[DEBUG] Initializing EventAssistant...")
        assistant = EventAssistant()

        if debug_enabled:
            print("[DEBUG] Adding nodes and edges to graph...")
        self.builder.add_node("assistant", assistant)
        self.builder.add_node("tools", create_tool_node_with_fallback(assistant.get_tools()))
        self.builder.add_edge(START, "assistant")
        self.builder.add_conditional_edges("assistant", tools_condition)
        self.builder.add_edge("tools", "assistant")

        if debug_enabled:
            print("[DEBUG] Compiling graph...")
        return self.builder.compile(checkpointer=self.memory)

    except Exception as e:
        print(f"[ERROR] Graph build failed: {e}")
        return None
