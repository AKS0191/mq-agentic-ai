import os
import certifi
import httpx

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

r = httpx.get("https://api.openai.com/v1")
print(r.status_code)  # Should return 401 if you haven’t set an API key
