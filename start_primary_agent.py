# -*- coding: utf-8 -*-
# ...existing code...
import truststore
truststore.inject_into_ssl()

import os
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

from datetime import *
import uuid
from agents.primary_agent.graph import MyGraph
# --- added imports ---
import argparse
import threading
import queue

# Rich (optional)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.live import Live
    from rich.spinner import Spinner
    _RICH_OK = True
except Exception:
    _RICH_OK = False
    Console = None  # type: ignore

# Tkinter (optional GUI)
try:
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText
    _TK_OK = True
except Exception:
    _TK_OK = False
# ...existing code...

graph = MyGraph().build_graph()

config = {
    "configurable": {                
        "thread_id": uuid.uuid4(),
        "ccdt_path": "agents/primary_agent/",
    }
}

_printed = set()
console = Console() if _RICH_OK else None


def _final_ai_message_from_event(message):
    if not message:
        return None
    if isinstance(message, list):
        message = message[-1]
    if message.id in _printed:
        return None
    if message.type == "ai" and not message.tool_calls:
        _printed.add(message.id)
        return message.content
    return None


def stream_response(user_input, emit_callback):
    events = graph.stream(
        {"messages": ("user", user_input), "flight_info": ""},
        config,
        stream_mode="values"
    )
    for event in events:
        content = _final_ai_message_from_event(event.get("messages"))
        if content:
            emit_callback(content)
            break


# -------- Rich TUI mode --------
def process_message_rich(user_input):
    if not _RICH_OK:
        return process_message_plain(user_input)
    with console.status(f"[bold cyan]Thinking about: {user_input}"):
        response_holder = {}
        def capture(resp):
            response_holder["resp"] = resp
        stream_response(user_input, capture)
    resp = response_holder.get("resp", "(no response)")
    console.print(
        Panel.fit(
            Markdown(str(resp)) if isinstance(resp, str) else str(resp),
            title="Assistant",
            border_style="green"
        )
    )


# -------- Plain fallback --------
def process_message_plain(user_input):
    events = graph.stream(
        {"messages": ("user", user_input), "flight_info": ""},
        config,
        stream_mode="values"
    )
    for event in events:
        message = event.get("messages")
        content = _final_ai_message_from_event(message)
        if content:
            print("\nAssistant:", content)
            break


# Public dispatcher
def process_message(user_input):
    if _RICH_OK:
        process_message_rich(user_input)
    else:
        process_message_plain(user_input)


# -------- Tkinter GUI --------
class ChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Primary Agent Chat")
        self.root.geometry("760x560")
        self.text = ScrolledText(self.root, wrap="word", state="disabled", font=("Menlo", 11))
        self.text.pack(fill="both", expand=True, padx=10, pady=10)

        bar = tk.Frame(self.root)
        bar.pack(fill="x", padx=10, pady=(0, 10))
        self.entry = tk.Entry(bar)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.on_send)
        tk.Button(bar, text="Send", command=self.on_send).pack(side="left", padx=6)
        tk.Button(bar, text="Quit", command=self.root.destroy).pack(side="left")

        self.msg_queue = queue.Queue()
        self.root.after(120, self._drain_queue)
        self._append("[system] Ready. Type a message or /quit\n", "sys")
        self._send_initial()

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
            self.root.destroy()
            return
        self._append(f"User: {msg}\n", "user")
        self.entry.delete(0, "end")
        threading.Thread(target=self._fetch, args=(msg,), daemon=True).start()

    def _fetch(self, user_input):
        def enqueue(resp):
            self.msg_queue.put(resp)
        stream_response(user_input, enqueue)

    def _drain_queue(self):
        try:
            while True:
                content = self.msg_queue.get_nowait()
                self._append(f"Assistant: {content}\n\n", "ai")
        except queue.Empty:
            pass
        self.root.after(120, self._drain_queue)

    def _send_initial(self):
        threading.Thread(target=self._fetch, args=("Hi",), daemon=True).start()

    def run(self):
        self.root.mainloop()


def run_cli():
    greeting = "Hi"
    process_message(greeting)
    while True:
        try:
            if _RICH_OK:
                user_text = Prompt.ask("\n[bold blue]User[/]")
            else:
                user_text = input("\nUser: ")
        except (EOFError, KeyboardInterrupt):
            bye = "Goodbye."
            if _RICH_OK:
                console.print(f"[bold yellow]{bye}")
            else:
                print(bye)
            break
        if user_text.lower() in ["quit", "exit", "q"]:
            farewell = "Arrivederci e grazie!"
            if _RICH_OK:
                console.print(f"[bold magenta]{farewell}")
            else:
                print("\nAssistant:", farewell)
            break
        process_message(user_text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true", help="Launch Tkinter GUI")
    args = parser.parse_args()

    if args.gui:
        if not _TK_OK:
            if _RICH_OK:
                console.print("[red]Tkinter not available. Falling back to terminal mode.[/red]")
            else:
                print("Tkinter not available. Falling back to terminal mode.")
            run_cli()
        else:
            ChatGUI().run()
    else:
        run_cli()


if __name__ == "__main__":
    main()
# ...existing code...