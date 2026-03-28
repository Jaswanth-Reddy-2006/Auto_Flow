import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_browser():
    prompt = "Open google.com and tell me what you see."
    print(f"Testing Browser Tool with prompt: '{prompt}'")
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"prompt": prompt},
            timeout=120
        )
        print(f"Status: {response.status_code}")
        print(f"Result: {response.json().get('result', 'No result')}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_browser()
