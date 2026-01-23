import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
print(f"Clé API (premiers chars): {api_key[:10] if api_key else 'MANQUANTE'}...")

response = requests.post(
    "https://api.mistral.ai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": "Dis bonjour"}],
        "max_tokens": 50
    },
    timeout=60
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")