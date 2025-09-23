import httpx, certifi, os

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

r = httpx.get("https://api.openai.com/v1")
print(r.status_code, r.text[:100])
