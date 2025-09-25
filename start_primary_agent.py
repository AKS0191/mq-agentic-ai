# -*- coding: utf-8 -*-
import os
import uuid
import argparse
import threading
import queue
import certifi
import truststore

truststore.inject_into_ssl()
os.environ["SSL_CERT_FILE"] = certifi.where()

# Optional Rich (terminal UI enhancements)
_RICH_OK = False
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    _RICH_OK = True
    console = Console()
except Exception:
    console = None  # type: ignore

# Optional Tkinter (GUI)
_TK_OK = False
try:
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText
    _TK_OK = True
except Exception:
    pass

# Config / state
_config = {
    "configurable": {
        "thread_id": uuid.uuid4(),
        "ccdt_path": "agents/primary_agent/",
    }
}
_graph = None
_printed_ids = set()


def debug(msg: str, enabled: bool):
    if not enabled:
        return
    if _RICH_OK and console:
        console.log(f"[debug] {msg}")
    else:
        print(f"[DEBUG] {msg}")


def build_graph(debug_enabled=False):
    global _graph
    if _graph is None:
        debug("Building graph...", debug_enabled)
        from agents.primary_agent.graph import MyGraph
        _graph = MyGraph().build_graph()
        debug("Graph built.", debug_enabled)
    return _graph


def _final_ai_message_from_event(message):
    if not message:
        return None
    if isinstance(message, list):
        message = message[-1]
    if message.id in _printed_ids:
        return None
    if message.type == "ai" and not getattr(message, "tool_calls", None):
        _printed_ids.add(message.id)
        return message.content
    return None


def stream_response(user_input: str, emit_callback, debug_enabled=False):
    graph = build_graph(debug_enabled)
    events = graph.stream(
        {"messages": ("user", user_input), "flight_info": ""},
        _config,
        stream_mode="values"
    )
    for event in events:
        content = _final_ai_message_from_event(event.get("messages"))
        if content:
            emit_callback(content)
            break


def process_message_plain(user_input: str, debug_enabled=False):
    stream_response(user_input, lambda c: print(f"\nAssistant: {c}"), debug_enabled)


def process_message_rich(user_input: str, debug_enabled=False):
    if not _RICH_OK or not console:
        return process_message_plain(user_input, debug_enabled)
    with console.status(f"[cyan]Thinking: {user_input}"):
        holder = {}
        stream_response(user_input, lambda c: holder.setdefault("resp", c), debug_enabled)
    resp = holder.get("resp", "(no response)")
    console.print(
        Panel(
            Markdown(str(resp)) if isinstance(resp, str) else str(resp),
            title="Assistant",
            border_style="green"
        )
    )


def process_message(user_input: str, use_rich: bool, debug_enabled=False):
    if use_rich and _RICH_OK:
        process_message_rich(user_input, debug_enabled)
    else:
        process_message_plain(user_input, debug_enabled)


def safe_input(prompt_text: str) -> str:
    try:
        return input(prompt_text)
    except EOFError:
        return ""
    except KeyboardInterrupt:
        return "exit"


class ChatGUI:
    def __init__(self, debug_enabled=False):
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
        tk.Button(bar, text="Quit", command=self.root.destroy).pack(side="left")

        self.entry.focus_set()
        self.msg_queue = queue.Queue()
        self.root.after(120, self._drain_queue)
        self._append("[system] Ready. Type and press Enter. /quit to exit.\n", "sys")
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
            self.root.destroy()
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

    def run(self):
        self.root.mainloop()


def run_cli(use_rich=True, debug_enabled=False):
    if use_rich and _RICH_OK and console:
        console.print("[bold green]Type your message. (quit/exit to leave)[/bold green]")
    else:
        print("Type your message. (quit/exit to leave)")
    process_message("Hi", use_rich, debug_enabled)
    while True:
        if use_rich and _RICH_OK and console:
            try:
                user_text = console.input("\n[bold blue]User> [/]")
            except (EOFError, KeyboardInterrupt):
                user_text = "exit"
        else:
            user_text = safe_input("\nUser> ")
        if not user_text:
            continue
        if user_text.lower() in ("quit", "exit", "q"):
            farewell = "Goodbye."
            if use_rich and _RICH_OK and console:
                console.print(f"[magenta]{farewell}")
            else:
                print(farewell)
            break
        process_message(user_text, use_rich, debug_enabled)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true", help="Launch Tk GUI")
    parser.add_argument("--no-rich", action="store_true", help="Disable Rich TUI even if available")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    use_rich = (not args.no_rich) and _RICH_OK

    if args.gui:
        if not _TK_OK:
            msg = "Tkinter not available. Falling back to CLI."
            if use_rich and console:
                console.print(f"[red]{msg}[/red]")
            else:
                print(msg)
            run_cli(use_rich, args.debug)
        else:
            ChatGUI(debug_enabled=args.debug).run()
    else:
        run_cli(use_rich, args.debug)


if __name__ == "__main__":
    main()