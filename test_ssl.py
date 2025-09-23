import ssl
import urllib.request

try:
    url = "https://api.openai.com/v1"
    context = ssl.create_default_context()
    response = urllib.request.urlopen(url, context=context)
    print("✅ SSL connection successful")
except ssl.SSLError as e:
    print("❌ SSL error:", e)
except Exception as e:
    print("❌ Other error:", e)
