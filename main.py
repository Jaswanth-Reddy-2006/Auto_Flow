"""
AutoFlow Phase 3 - Web Eyes with Playwright
==========================================
A FastAPI server that uses LangChain (Llama3) to control OS-level
mouse/keyboard and navigate the web via Playwright.
"""

import time
import asyncio
import pyautogui
import screeninfo
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

from langchain_ollama import ChatOllama
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from playwright.sync_api import sync_playwright
import uvicorn
import os
from pathlib import Path

# Ensure outputs directory for screenshots
os.makedirs("outputs", exist_ok=True)

# ---------------------------------------------------------------------------
# App & LLM Setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AutoFlow Brain & Hand Bridge",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatOllama(model="llama3", temperature=0)

# ---------------------------------------------------------------------------
# Browser Manager
# ---------------------------------------------------------------------------

class BrowserManager:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None

    def start(self):
        # If playwright isn't started, or browser is disconnected, start from scratch
        if not self._playwright or (self._browser and not self._browser.is_connected()):
            if self._playwright:
                try: self._playwright.stop()
                except: pass
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=False)
            self._page = self._browser.new_page()
        
        # Ensure page exists and is not closed
        if not self._page or self._page.is_closed():
             self._page = self._browser.new_page()
             
        return self._page

    def navigate(self, url: str) -> str:
        page = self.start()
        if not url.startswith("http"): url = "https://" + url
        page.goto(url)
        return f"Successfully navigated to {url}"

    def click(self, selector: str) -> str:
        page = self.start()
        try:
            if not selector.startswith((".", "#", "[")):
                 page.get_by_text(selector, exact=False).first.click()
            else:
                 page.click(selector)
            return f"Clicked element: '{selector}'"
        except Exception as e:
            return f"Error clicking: {str(e)}"

    def type_text(self, text: str) -> str:
        page = self.start()
        try:
            # YouTube / General search bar common locators
            target = page.get_by_placeholder("Search", exact=False).first
            if not target.is_visible():
                target = page.locator("input").first
            
            target.fill(text)
            target.press("Enter")
            return f"Typed '{text}' and hit Enter."
        except Exception as e:
            return f"Error typing: {str(e)}"

    def scrape(self) -> str:
        page = self.start()
        # Extract meaningful text from the page
        text = page.evaluate("document.body.innerText")
        return f"SCRA_TEXT_START\n{text[:5000]}\nSCRA_TEXT_END"

    def take_screenshot(self, name: str = "shot") -> str:
        page = self.start()
        path = f"outputs/{name}_{int(time.time())}.png"
        page.screenshot(path=path)
        return f"Screenshot saved to: {path}"

    def close(self):
        if self._browser: self._browser.close()
        if self._playwright: self._playwright.stop()
        self._playwright = self._browser = self._page = None
        return "Browser closed."

_bm = BrowserManager()

# ---------------------------------------------------------------------------
# Tools - RENAMED to avoid any collision
# ---------------------------------------------------------------------------

@tool
def action_web_goto(url: str) -> str:
    """Open a URL or website."""
    return _bm.navigate(url)

@tool
def action_web_click(text_or_selector: str) -> str:
    """Click a button or link."""
    return _bm.click(text_or_selector)

@tool
def action_web_search(query: str) -> str:
    """Search for something on current page. Types into first input field and hits Enter."""
    return _bm.type_text(query)

@tool
def action_take_screenshot(name: str = "error") -> str:
    """Take a screenshot of the current page for visual debugging."""
    print(f"--- TOOL: Take Screenshot ({name}) ---")
    return _bm.take_screenshot(name)

@tool
def action_write_file(filename_and_content: str) -> str:
    """
    Saves a text file to your DESKTOP.
    Format: 'filename.txt:Your text content'
    Example: 'news.txt:This is the summary content.'
    """
    print(f"--- TOOL: Write File ({filename_and_content[:50]}...) ---")
    try:
        if ":" not in filename_and_content:
            return "Error: Use 'filename.txt:content' format."
        
        filename, content = filename_and_content.split(":", 1)
        # Use explicit OneDrive Desktop path found on the machine
        desktop = r"C:\Users\Jaswanth Reddy\OneDrive\Desktop"
        full_path = os.path.join(desktop, filename.strip())
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"SUCCESS: Created file at {full_path}"
    except Exception as e:
        return f"File Error: {str(e)}"

@tool
def action_web_goto(url: str) -> str:
    """Open a URL."""
    print(f"--- TOOL: Goto ({url}) ---")
    return _bm.navigate(url)

@tool
def action_web_scrape(input_str: str = "") -> str:
    """Scrape text from the current page."""
    print("--- TOOL: Scrape ---")
    return _bm.scrape()

@tool
def action_test_mouse(input_str: str = "") -> str:
    """Test mouse move and typing 'Hello from AutoFlow!'."""
    try:
        monitor = screeninfo.get_monitors()[0]
        cx, cy = monitor.width // 2, monitor.height // 2
    except:
        cx, cy = 500, 500
    pyautogui.moveTo(cx, cy, duration=0.8)
    pyautogui.hotkey("win")
    time.sleep(1.0)
    pyautogui.typewrite("Hello from AutoFlow!", interval=0.05)
    return "SUCCESS: Mouse/Keyboard test passed."

# ---------------------------------------------------------------------------
# Agent Configuration
# ---------------------------------------------------------------------------

robot_tools = [
    action_web_goto, action_web_click, action_web_search, 
    action_web_scrape, action_write_file, action_take_screenshot,
    action_test_mouse
]

ROBOT_PREFIX = """You are AutoFlow, an advanced computer control robot.
You can use tools to bridge the web and the local desktop.

AVAILABLE TOOLS:
- action_web_goto(url): Open a site.
- action_web_scrape: Read all text.
- action_write_file(name_colon_text): Save to Desktop (e.g. 'news.txt:Text here').
- action_take_screenshot: Save a visual.
- action_test_mouse: Test mouse.

Example: To save a summary of 'Pizza' to pizza.txt:
Action: action_write_file
Action Input: pizza.txt:This is a summary of pizza.

Format:
Thought: I need to do X.
Action: [tool name]
Action Input: [input string]
(Wait for result)"""

auto_agent = initialize_agent(
    tools=robot_tools,
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10, 
    agent_kwargs={"prefix": ROBOT_PREFIX}
)

# ---------------------------------------------------------------------------
# API Models & Endpoints
# ---------------------------------------------------------------------------

class RequestModel(BaseModel):
    prompt: str

@app.get("/")
def home():
    print("Health check pinged!")
    return {"status": "online", "agent": "AutoFlow v3"}

@app.post("/ask")
def ask_robot(req: RequestModel):
    print(f"Robot received: {req.prompt}")
    try:
        res = auto_agent.run(req.prompt)
        return {"prompt": req.prompt, "result": res}
    except Exception as e:
        print(f"Error in agent: {e}")
        return {"prompt": req.prompt, "result": f"Error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
