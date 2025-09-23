import httpx

r = httpx.get("https://api.openai.com/v1")
print(r.status_code)
