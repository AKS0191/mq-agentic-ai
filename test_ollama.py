import subprocess

user_input = "Hi"

result = subprocess.run(
    ["ollama", "chat", "mistral", "--prompt", user_input],
    capture_output=True,
    text=True
)

output = result.stdout.strip()
print(output)
