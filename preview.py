import requests
import sys
import os
import asyncio
from playwright.async_api import async_playwright

def check_backend():
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend [127.0.0.1:8000]: ONLINE")
            return True
    except:
        pass
    print("❌ Backend [127.0.0.1:8000]: OFFLINE (Run: python main.py)")
    return False

def check_ollama():
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama [11434]: ONLINE")
            return True
    except:
         pass
    print("❌ Ollama [11434]: OFFLINE (Ensure Ollama is running)")
    return False

async def check_playwright():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("http://example.com")
            await browser.close()
            print("✅ Playwright: FUNCTIONAL")
            return True
    except Exception as e:
        print(f"❌ Playwright: FAILED ({e})")
    return False

async def main():
    print("="*40)
    print("      AutoFlow System Health Check")
    print("="*40)
    
    b = check_backend()
    o = check_ollama()
    p = await check_playwright()
    
    print("="*40)
    if b and o and p:
        print("🚀 ALL SYSTEMS GO! You are ready to chat.")
    else:
        print("⚠️  FIX THE ERRORS ABOVE BEFORE CHATTING.")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
