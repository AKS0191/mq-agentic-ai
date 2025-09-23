import httpx, certifi, ssl

ssl_context = ssl.create_default_context(cafile=certifi.where())
r = httpx.get("https://api.openai.com/v1", verify=ssl_context)
print(r.status_code)
