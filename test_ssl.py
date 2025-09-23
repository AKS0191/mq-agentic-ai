import os
import certifi

# Force all HTTPS requests to use certifi's CA bundle
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
print("SSL certificates set to certifi bundle:", certifi.where())
