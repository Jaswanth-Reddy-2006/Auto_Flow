import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_home():
    print("Testing Health Check...")
    try:
        response = requests.get(BASE_URL)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Failed: {e}")

def test_ask(prompt):
    print(f"\nTesting Prompt: '{prompt}'")
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"prompt": prompt},
            timeout=60
        )
        print(f"Status: {response.status_code}")
        print(f"Result: {response.json().get('result', 'No result')}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    # Wait for server to be ready if needed
    test_home()
    
    # Test Rule 0: General Knowledge (Expect direct answer, no tool call)
    test_ask("What is a polar bear's diet?")
    
    # Test Tool Use: Local App (Expect tool call trace in uvicorn logs)
    # test_ask("Check if PowerPoint is installed.")
