import httpx, certifi, ssl, os

os.environ["SSL_CERT_FILE"] = certifi.where()
ssl_context = ssl.create_default_context(cafile=certifi.where())

try:
    r = httpx.get("https://api.openai.com/v1", verify=ssl_context)
    print("✅ Success:", r.status_code, r.text[:100])
except Exception as e:
    print("❌ Error:", e)
