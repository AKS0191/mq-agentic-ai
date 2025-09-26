# -*- coding: utf-8 -*-
"""
Start Primary Agent (CLI / Rich TUI / Tk GUI)
Handles local LLM via Ollama or OpenAI.
Falls back to echo if graph/LLM unavailable.
"""

import os
import uuid
import argparse
import threading
import queue
from mq_sdk.utilities.subscriber import MQSubscriber

# Optional Rich UI
_RICH_OK = False
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    _RICH_OK = True
    console = Console()
except Exception:
    console = None

# Optional Tkinter GUI
_TK_OK = False
try:
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText
    _TK_OK = True
except Exception:
    pass

# Runtime config placeholder
_config = {
    "configurable": {
        "thread_id": uuid.uuid4(),
        "ccdt_path": "agents/primary_agent/",
    }
}

# -----------------------------
# Stream response function
# -----------------------------
def stream_response(user_input: str, emit_callback, debug_enabled=False):
    """
    Streams AI response for a user input.
    Falls back to echo if graph or LLM backend fails.
    Prints which backend is used.
    """
    try:
        from agents.primary_agent.graph import MyGraph
        from agents.primary_agent.event_assistant import EventAssistant

        graph = MyGraph().build_graph(debug_enabled=debug_enabled)
        if graph is None:
            raise RuntimeError("Graph is None. Falling back to assistant.")

        events = graph.stream(
            {"messages": ("user", user_input), "flight_info": ""},
            _config,
            stream_mode="values"
        )

        for event in events:
            content = None
            backend = "unknown"
            msgs = event.get("messages")
            if msgs:
                msg = msgs[-1] if isinstance(msgs, list) else msgs
                if getattr(msg, "type", None) == "ai":
                    content = getattr(msg, "content", None)
                    backend = getattr(msg, "backend", "AI")

            if content:
                emit_callback(f"[{backend}] {content}")
                break

    except Exception as e:
        if debug_enabled:
            print(f"[DEBUG] Stream error: {e}")
        try:
            assistant = EventAssistant()
            response = assistant.ask(user_input)
            emit_callback(f"[{assistant.backend}] {response}")
        except Exception as e2:
            if debug_enabled:
                print(f"[DEBUG] Fallback assistant failed: {e2}")
            emit_callback(f"[echo] {user_input}")

# -----------------------------
# CLI interaction
# -----------------------------
def run_cli(use_rich=True, debug_enabled=False, subscriber=None):
    if use_rich and _RICH_OK and console:
        console.print("[bold green]Type your message. (quit/exit to leave)[/bold green]")
    else:
        print("Type your message. (quit/exit to leave)")

    try:
        while True:
            if use_rich and _RICH_OK and console:
                try:
                    user_text = console.input("\n[bold blue]User> [/]")
                except (EOFError, KeyboardInterrupt):
                    user_text = "exit"
            else:
                try:
                    user_text = input("\nUser> ")
                except (EOFError, KeyboardInterrupt):
                    user_text = "exit"

            if not user_text:
                continue
            if user_text.lower() in ("quit", "exit", "q"):
                farewell = "Goodbye."
                if use_rich and _RICH_OK and console:
                    console.print(f"[magenta]{farewell}")
                else:
                    print(farewell)
                break

            stream_response(user_text, lambda r: print(f"Assistant: {r}"))
    finally:
        if subscriber:
            subscriber.close()

# -----------------------------
# GUI interaction
# -----------------------------
class ChatGUI:
    def __init__(self, subscriber, debug_enabled=False):
        self.subscriber = subscriber
        self.debug_enabled = debug_enabled
        self.root = tk.Tk()
        self.root.title("Primary Agent Chat")
        self.root.geometry("780x580")
        self.text = ScrolledText(self.root, wrap="word", state="disabled", font=("Menlo", 11))
        self.text.pack(fill="both", expand=True, padx=10, pady=10)

        bar = tk.Frame(self.root)
        bar.pack(fill="x", padx=10, pady=(0, 10))
        self.entry = tk.Entry(bar)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.on_send)
        tk.Button(bar, text="Send", command=self.on_send).pack(side="left", padx=6)
        tk.Button(bar, text="Quit", command=self._quit).pack(side="left")
        self.entry.focus_set()
        self.msg_queue = queue.Queue()
        self.root.after(120, self._drain_queue)
        threading.Thread(target=self._fetch, args=("Hi",), daemon=True).start()

    def _append(self, text, tag=None):
        self.text.configure(state="normal")
        if tag and tag not in self.text.tag_names():
            colors = {"sys": "#6b7280", "user": "#2563eb", "ai": "#059669"}
            self.text.tag_configure(tag, foreground=colors.get(tag, "black"))
        self.text.insert("end", text, tag)
        self.text.see("end")
        self.text.configure(state="disabled")

    def on_send(self, event=None):
        msg = self.entry.get().strip()
        if not msg:
            return
        if msg.lower() in ("/quit", "/exit"):
            self._quit()
            return
        self._append(f"User: {msg}\n", "user")
        self.entry.delete(0, "end")
        threading.Thread(target=self._fetch, args=(msg,), daemon=True).start()

    def _fetch(self, user_input):
        stream_response(user_input, lambda r: self.msg_queue.put(r), self.debug_enabled)

    def _drain_queue(self):
        try:
            while True:
                content = self.msg_queue.get_nowait()
                self._append(f"Assistant: {content}\n\n", "ai")
        except queue.Empty:
            pass
        self.root.after(120, self._drain_queue)

    def _quit(self):
        if self.subscriber:
            self.subscriber.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

# -----------------------------
# Main entry point
# -----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true", help="Launch Tk GUI")
    parser.add_argument("--no-rich", action="store_true", help="Disable Rich TUI")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    use_rich = (not args.no_rich) and _RICH_OK

    # Initialize MQSubscriber
    subscriber = MQSubscriber(ccdt_path="agents/primary_agent/")
    if not subscriber.subscribe():
        print("Failed to create MQ subscription. Exiting.")
        return

    try:
        if args.gui and _TK_OK:
            ChatGUI(subscriber=subscriber, debug_enabled=args.debug).run()
        else:
            run_cli(use_rich=use_rich, debug_enabled=args.debug, subscriber=subscriber)
    finally:
        subscriber.close()

if __name__ == "__main__":
    main()
