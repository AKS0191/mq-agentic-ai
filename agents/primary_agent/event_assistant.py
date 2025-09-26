import os

# Optional: OpenAI
_OPENAI_OK = False
try:
    import openai
    _OPENAI_OK = True
except ImportError:
    pass

# Optional: Ollama
_OLLAMA_OK = False
try:
    import ollama
    _OLLAMA_OK = True
except ImportError:
    pass


class EventAssistant:
    """
    Loads AI backend (OpenAI or Ollama) automatically.
    Provides `get_tools()` placeholder for your tool nodes.
    """

    def __init__(self):
        self.backend = None
        self._init_backend()

    def _init_backend(self):
        # First try OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY")
        if _OPENAI_OK and openai_key:
            self.backend = "openai"
            self.client = openai
            self.client.api_key = openai_key
            print("[INFO] Using OpenAI backend")
            return

        # Then try Ollama
        if _OLLAMA_OK:
            try:
                ollama.models()
                self.backend = "ollama"
                self.client = ollama
                print("[INFO] Using Ollama backend")
                return
            except Exception as e:
                print(f"[WARN] Ollama server not responding: {e}")

        # Fallback: No backend
        self.backend = "echo"
        print("[WARN] No AI backend available. Using echo fallback.")

    def ask(self, prompt: str):
        """
        Ask the AI backend to generate a response.
        Returns string.
        """
        try:
            if self.backend == "openai":
                response = self.client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()

            elif self.backend == "ollama":
                resp = self.client.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
                return resp["content"]

            else:
                # Echo fallback
                return prompt

        except Exception as e:
            print(f"[ERROR] AI backend failed: {e}")
            return prompt

    def get_tools(self):
        """
        Return list of tools for the graph.
        Replace with your real tools.
        """
        return ["search_flights", "get_flight_info"]
