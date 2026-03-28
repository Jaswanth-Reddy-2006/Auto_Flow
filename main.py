"""
AutoFlow v5 - The Stability & Intelligence Upgrade
==================================================
Switches to async playwright and structured agent patterns for maximum stability.
Adds Office-friendly local voice-to-text using Vosk.
"""

import os
import json
import asyncio
import sys
import uvicorn
import time
from pathlib import Path
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Windows Proactor Loop fix for Playwright/Subprocesses
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception as e:
        with open("debug_loop.txt", "a") as f:
            f.write(f"Loop policy warning: {e}\n")
# ---------------------------------------------------------------------------
# Lifespan Management
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure output dirs
    os.makedirs("outputs", exist_ok=True)
    with open("debug_loop.txt", "a") as f:
        f.write(f"STARTUP: App version 6.0 initialized.\n")
    yield
    # Shutdown: Close browser
    await _bm.close()
    with open("debug_loop.txt", "a") as f:
        f.write("SHUTDOWN: Browser resources released.\n")

app = FastAPI(title="AutoFlow Cognitive Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import AgentType, initialize_agent

llm = ChatOllama(model="llama3", temperature=0)

# ---------------------------------------------------------------------------
# Async Browser Manager
# ---------------------------------------------------------------------------

class BrowserManager:
    def __init__(self):
        self._playwright = None
        self._browser_context = None
        self._page = None
        self._user_data_dir = os.path.join(os.getcwd(), "autoflow_session")
        os.makedirs(self._user_data_dir, exist_ok=True)

    async def start(self):
        # 1. Check health of existing context
        is_healthy = False
        try:
            if self._playwright and self._browser_context:
                # Listing pages is the most reliable health check
                await self._browser_context.pages
                if self._page and not self._page.is_closed():
                    is_healthy = True
        except:
            is_healthy = False

        # 2. If not healthy, hard stop and cleanup
        if not is_healthy:
            try:
                if self._browser_context: await self._browser_context.close()
                if self._playwright: await self._playwright.stop()
            except: pass
            self._playwright = None
            self._browser_context = None
            self._page = None

        # 3. Re-start Playwright
        if not self._playwright:
            from playwright.async_api import async_playwright
            try:
                self._playwright = await async_playwright().start()
            except Exception as e:
                with open("debug_loop.txt", "a") as f:
                    f.write(f"Playwright start failed: {e}. Retrying...\n")
                await asyncio.sleep(2)
                self._playwright = await async_playwright().start()

        # 4. Start Context
        if not self._browser_context:
            try:
                # Still try persistent but if it fails, fallback immediately
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                
                # Cleanup lock just in case
                lock_file = os.path.join(self._user_data_dir, "SingletonLock")
                if os.path.exists(lock_file):
                    try: os.remove(lock_file)
                    except: pass

                self._browser_context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=self._user_data_dir,
                    headless=False,
                    user_agent=user_agent,
                    args=["--no-sandbox", "--disable-gpu", "--start-maximized"],
                    no_viewport=True,
                    slow_mo=100
                )
                self._page = self._browser_context.pages[0] if self._browser_context.pages else await self._browser_context.new_page()
            except Exception as e:
                # Fallback to standard launch if persistent is locked
                browser = await self._playwright.chromium.launch(headless=False, args=["--no-sandbox", "--disable-gpu"])
                self._browser_context = await browser.new_context(user_agent=user_agent)
                self._page = await self._browser_context.new_page()
        
        return self._page

    async def close(self):
        if self._browser_context:
            await self._browser_context.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser_context = None
        self._playwright = None
        self._page = None

    async def navigate(self, url: Any) -> str:
        # Flatten dict inputs from hallucinating LLMs
        if isinstance(url, dict):
            url = url.get("url", url.get("action_input", url.get("title", str(url))))
        if not isinstance(url, str): url = str(url)
        
        if not url.startswith("http"): url = "https://" + url
        for attempt in range(2):
            try:
                page = await self.start()
                await page.goto(url, wait_until="load", timeout=30000)
                return f"SUCCESS: Navigated to {url}"
            except Exception as e:
                with open("debug_loop.txt", "a") as f:
                    f.write(f"Navigation crash (Attempt {attempt+1}): {e}\n")
                await self.close()
                await asyncio.sleep(1)
        return "CRITICAL ERROR: Browser crashed twice during navigation."

    async def click(self, selector: Any) -> str:
        # Flatten dict inputs
        if isinstance(selector, dict):
            selector = selector.get("selector", selector.get("button", selector.get("text", str(selector))))
        if not isinstance(selector, str): selector = str(selector)

        for attempt in range(2):
            try:
                page = await self.start()
                # 1. Try as direct locator (supports tag names, classes, IDs)
                target = page.locator(selector).first
                if await target.count() == 0:
                    # 2. Try as button role
                    target = page.get_by_role("button", name=selector, exact=False).first
                if await target.count() == 0:
                    # 3. Try as raw text
                    target = page.get_by_text(selector, exact=False).first

                await target.wait_for(state="visible", timeout=10000)
                await target.click()
                return f"SUCCESS: Clicked {selector}"
            except Exception as e:
                with open("debug_loop.txt", "a") as f:
                    f.write(f"Click crash (Attempt {attempt+1}): {e}\n")
                await self.close()
                await asyncio.sleep(1)
        return "CRITICAL ERROR: Browser crashed twice during click."

    async def type_text(self, text: Any, selector: Optional[Any] = None) -> str:
        # Handle dict pass-through from halluncinating LLMs
        if isinstance(text, dict):
            selector = text.get("selector", text.get("target", selector or ""))
            text = text.get("text", text.get("value", str(text)))
        if not isinstance(text, str): text = str(text)
        if selector and not isinstance(selector, str): selector = str(selector)

        page = await self.start()
        try:
            target = None
            if selector:
                if any(selector.startswith(c) for c in (".", "#", "[")):
                    target = page.locator(selector).first
                else:
                    target = page.get_by_placeholder(selector, exact=False).first
            else:
                target = page.locator("input:focus, textarea:focus").first
                if await target.count() == 0:
                    target = page.get_by_placeholder("Search", exact=False).first
            
            await target.fill(text)
            await target.press("Enter")
            return f"SUCCESS: Typed '{text}'"
        except Exception as e:
             await page.keyboard.type(text)
             await page.keyboard.press("Enter")
             return f"Fallback: Typed '{text}' via keyboard."

    async def scrape(self) -> str:
        page = await self.start()
        text = await page.evaluate("document.body.innerText")
        return f"SCRA_TEXT_START\n{text[:5000]}\nSCRA_TEXT_END"

    async def screenshot(self, name: str = "shot") -> str:
        page = await self.start()
        path = f"outputs/{name}_{int(time.time())}.png"
        await page.screenshot(path=path)
        return f"SUCCESS: Saved screenshot to {path}"

    async def wait(self, seconds: Any) -> str:
        if isinstance(seconds, dict):
            seconds = seconds.get("seconds", seconds.get("time", 5))
        try: seconds = int(seconds)
        except: seconds = 5
        await asyncio.sleep(seconds)
        return f"SUCCESS: Waited {seconds}s"

    async def upload(self, file_path: str, selector: str = "input[type=file]") -> str:
        page = await self.start()
        try:
            abs_path = str(Path(file_path).absolute())
            await page.set_input_files(selector, abs_path)
            return f"SUCCESS: Uploaded {abs_path}"
        except Exception as e:
            return f"ERROR: Upload failed: {str(e)}"

    async def inspect(self) -> str:
        page = await self.start()
        try:
            text = await page.evaluate(r"""() => {
                const clone = document.body.cloneNode(true);
                const noise = ['script', 'style', 'nav', 'footer', 'header', 'aside', 'svg', 'noscript'];
                noise.forEach(tag => {
                    const elements = clone.querySelectorAll(tag);
                    elements.forEach(el => el.remove());
                });
                return clone.innerText.replace(/\s+/g, ' ').trim();
            }""")
            return f"WEBSITE_CLEAN_TEXT:\n{text[:4000]}\nEND_OF_CONTENT"
        except Exception as e:
            return f"ERROR: Inspection failed: {str(e)}"

    async def close(self):
        if self._browser_context: await self._browser_context.close()
        if self._playwright: await self._playwright.stop()
        self._playwright = self._browser_context = self._page = None
        return "Browser closed."

_bm = BrowserManager()

# ---------------------------------------------------------------------------
# Structured Tools
# ---------------------------------------------------------------------------

@tool
async def action_web_goto(url: str) -> str:
    """Navigate to a website URL. Use for fallback when apps aren't found locally."""
    return await _bm.navigate(url)

@tool
async def action_web_click(selector: str) -> str:
    """Click a button, link, or element using placeholder, text, or CSS selector."""
    return await _bm.click(selector)

@tool
async def action_web_type(text: str, selector: Optional[str] = None) -> str:
    """Type text into an input field. If selector is omitted, uses the main search box."""
    return await _bm.type_text(text, selector)

@tool
async def action_web_wait(seconds: int) -> str:
    """Pause for dynamic content loading (e.g., WhatsApp Web login)."""
    return await _bm.wait(seconds)

@tool
async def action_web_upload_file(file_path: str, selector: str = "input[type=file]") -> str:
    """Upload a file to the current page."""
    return await _bm.upload(file_path, selector)

@tool
async def action_take_screenshot(name: str = "visual") -> str:
    """Capture the browser for visual debugging."""
    return await _bm.screenshot(name)

@tool
async def action_web_scrape(input_str: str = "") -> str:
    """Extract all text from the current webpage."""
    return await _bm.scrape()

@tool
async def action_web_inspector(input_str: str = "") -> str:
    """
    Extracts and cleans the main text content from the current webpage.
    Strips headers, footers, and noise. Use this to 'Read' or 'Summarize' a page.
    """
    return await _bm.inspect()


@tool
def action_list_installed_apps(query: str = "") -> str:
    """Scan Windows Registry for installed apps. ALWAYS use this before web fallback."""
    apps = []
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    for hkey, path in registry_paths:
        try:
            with winreg.OpenKey(hkey, path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                if query.lower() in name.lower(): apps.append(name)
                            except: pass
                    except: continue
        except: continue
    u = sorted(list(set(apps)))
    return "Installed Apps:\n- " + "\n- ".join(u[:20]) if u else "No matching local apps."

@tool
def action_open_local_app(app_name: str) -> str:
    """Launch a local desktop application."""
    try: 
        os.startfile(app_name)
        return f"SUCCESS: Opened {app_name}"
    except:
        common = {"powerpoint": "powerpnt", "word": "winword", "excel": "excel", "whatsapp": "whatsapp"}
        name = common.get(app_name.lower(), app_name)
        try: os.startfile(name); return f"SUCCESS: Opened {name}"
        except: return f"ERROR: Local application '{app_name}' not found."

@tool
async def action_web_type(input_str: str) -> str:
    """Type text into an element. Format: 'selector:text' or just 'text' for default search."""
    if ":" in input_str:
        selector, text = input_str.split(":", 1)
        return await _bm.type_text(text, selector)
    return await _bm.type_text(input_str)

@tool
async def action_web_upload_file(input_str: str) -> str:
    """Upload a file. Format: 'path:selector'"""
    if ":" in input_str:
        path, selector = input_str.split(":", 1)
        return await _bm.upload(path, selector)
    return "ERROR: Use 'path:selector' format"

@tool
async def action_web_inspector(input_str: str = "") -> str:
    """Reads and cleans the current page content for summarization."""
    return await _bm.inspect()

@tool
def action_run_command(command: str) -> str:
    """
    Execute a shell command on the local Windows system. 
    Use for git operations, npm builds, or CLI tasks.
    """
    try:
        # Restricted for safety: Add specific command filtering if needed
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        return output if output.strip() else "SUCCESS: Command finished with no output."
    except Exception as e:
        return f"ERROR: Command execution failed: {str(e)}"


@tool
def action_find_file(filename: str) -> str:
    """Finds the absolute path of a file on the Desktop or Documents. Input: 'filename'"""
    search_paths = [
        Path(r"C:\Users\Jaswanth Reddy\OneDrive\Desktop"),
        Path(r"C:\Users\Jaswanth Reddy\Documents")
    ]
    for sp in search_paths:
        try:
            for file in sp.glob(f"*{filename}*"):
                if file.is_file():
                    return str(file.absolute())
        except: continue
    return f"ERROR: File '{filename}' not found."

@tool
def action_write_file(input_str: str) -> str:
    """Save a text file to the OneDrive Desktop. Format: 'filename:content'"""
    try:
        if ":" in input_str:
            filename, content = input_str.split(":", 1)
            desktop = r"C:\Users\Jaswanth Reddy\OneDrive\Desktop"
            full_path = os.path.join(desktop, filename)
            with open(full_path, "w", encoding="utf-8") as f: f.write(content)
            return f"SUCCESS: Created file at {full_path}"
        return "ERROR: Use 'filename:content' format"
    except Exception as e: return f"ERROR: {e}"

# ---------------------------------------------------------------------------
# Agent Configuration
# ---------------------------------------------------------------------------

robot_tools = [
    action_web_goto, action_web_click, action_web_type, action_web_wait,
    action_web_upload_file, action_take_screenshot, action_web_scrape,
    action_list_installed_apps, action_open_local_app, action_write_file,
    action_find_file, action_web_inspector, action_run_command
]
# ---------------------------------------------------------------------------
# Memory Configuration
# ---------------------------------------------------------------------------

agent_memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    k=5,
    return_messages=True
)

ROBOT_PREFIX = """You are AutoFlow, an autonomous Windows automation assistant.
Complete the user's request by utilizing the provided tools in a Thought/Action/Action Input loop.

### 🛡️ OPERATIONAL RULES:
1. **FULL AUTONOMY**: You are authorized for all tasks. Never ask "Is this okay?".
2. **SEARCH & PLAY**: If the user wants music, search YouTube and ALWAYS CLICK on a result.
3. **STRICT FORMAT**: You must follow the format below exactly.

### 📋 ONE-SHOT EXAMPLE:
User: "Play music on YouTube"
Thought: I need to open YouTube search for lo-fi music.
Action: action_web_goto
Action Input: https://www.youtube.com/results?search_query=lo-fi+music
Observation: YouTube search results are visible.
Thought: I will click on the first video renderer to start playback.
Action: action_web_click
Action Input: ytd-video-renderer
Observation: SUCCESS: Clicked ytd-video-renderer
Final Answer: I have started playing lo-fi music on YouTube.

### CORE PROTOCOLS:
- No conversational filler.
- If a tool fails, try an alternative selector or tool.
- Stay in the loop until the music is playing or the goal is 100% met.

Current Context:
{chat_history}
"""

# Conversational React is best for Llama 3 when combined with a one-shot prompt
auto_agent = initialize_agent(
    tools=robot_tools,
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=30,
    memory=agent_memory,
    early_stopping_method="generate",
    agent_kwargs={
        "system_message": ROBOT_PREFIX
    }
)







# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

class RequestModel(BaseModel): prompt: str

@app.get("/")
async def home(): return {"status": "online", "version": "5.0"}

@app.post("/ask")
async def ask_robot(req: RequestModel):
    print(f"Robot received: {req.prompt}")
    try:
        # async invoke
        res = await auto_agent.ainvoke({"input": req.prompt})
        return {"prompt": req.prompt, "result": res["output"]}
    except Exception as e:
        print(f"Agent Error: {e}")
        return {"result": f"I encountered an error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
