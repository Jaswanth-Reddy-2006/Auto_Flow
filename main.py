"""
AutoFlow v6 - Production Stabilization
======================================
Autonomous Windows automation assistant with robust browser management
and registry-based app discovery.
"""

import os
import sys
import json
import time
import winreg
import asyncio
import uvicorn
import subprocess
from pathlib import Path
from typing import List, Optional, Any
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Windows: UTF-8 console + Proactor Loop fix for Playwright/Subprocesses
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
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
        self._browser = None
        self._context = None
        self._page = None
        self._is_connected_to_existing = False
        # Use a dedicated profile for AutoFlow to avoid "Profile in Use" errors with user's main Chrome
        self._user_data_dir = os.path.join(os.getcwd(), "autoflow_chrome_profile")
        os.makedirs(self._user_data_dir, exist_ok=True)
        self._chrome_exe = self._find_chrome_executable()

    def _find_chrome_executable(self) -> str:
        """Find Chrome executable path on Windows."""
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return "chrome"  # Fallback to PATH

    async def start(self):
        """Start or reuse browser - prioritizing existing sessions."""
        from playwright.async_api import async_playwright

        # 1. Check if we have a healthy session already
        if self._page and not self._page.is_closed():
            try:
                await self._page.evaluate("() => true")
                return self._page
            except: 
                print(">>> Existing page unhealthy, trying to recover...")
                self._page = None

        # 2. Ensure Playwright is running (Only start it ONCE)
        if not self._playwright:
            self._playwright = await async_playwright().start()

        # Strategy 1: Link to existing Chrome via CDP (Most preferred for logins)
        try:
            # We only try CDP if we're not already in Strategy 2 or if we just started
            if not self._browser or self._is_connected_to_existing:
                self._browser = await self._playwright.chromium.connect_over_cdp("http://localhost:9222", timeout=2000)
                self._context = self._browser.contexts[0] if self._browser.contexts else await self._browser.new_context()
                self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
                self._is_connected_to_existing = True
                print(">>> REUSED: Linked to your main Chrome session.")
                return self._page
        except: 
            # If CDP fails, we move to Strategy 2 below
            pass

        # Strategy 2: Dedicated AutoFlow Profile (Only launch if needed)
        if not self._browser or self._is_connected_to_existing: # If we failed Strategy 1 or lost it
            try:
                # Clear SingletonLock to prevent "Profile in Use" errors
                lock_file = os.path.join(self._user_data_dir, "SingletonLock")
                if os.path.exists(lock_file):
                    try: os.remove(lock_file)
                    except: pass

                launch_args = ["--remote-debugging-port=9222", "--no-sandbox", "--disable-gpu"]
                self._browser = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=self._user_data_dir,
                    executable_path=self._chrome_exe if os.path.exists(self._chrome_exe) else None,
                    headless=False,
                    args=launch_args,
                    no_viewport=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                )
                self._context = self._browser
                self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
                self._is_connected_to_existing = False
                print(">>> REUSED: Using dedicated AutoFlow profile.")
                return self._page
            except Exception as e:
                print(f">>> CRITICAL: Browser fallback to test mode due to: {e}")
                # Strategy 3: Final test browser fallback
                if not self._browser:
                    self._browser = await self._playwright.chromium.launch(headless=False)
                    self._context = await self._browser.new_context()
                    self._page = await self._context.new_page()
                return self._page
        
        return self._page # Returning existing if session were already running

    async def _cleanup(self):
        """Clean up browser resources."""
        try:
            if self._page:
                await self._page.close()
        except: pass
        try:
            if self._context:
                await self._context.close()
        except: pass
        try:
            if self._browser:
                await self._browser.close()
        except: pass
        try:
            if self._playwright:
                await self._playwright.stop()
        except: pass
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        self._is_connected_to_existing = False

    async def close(self):
        """Close browser - but keep existing Chrome open if we connected to it."""
        if self._is_connected_to_existing:
            # Just disconnect, don't kill user's Chrome
            try:
                if self._browser:
                    await self._browser.disconnect()
            except: pass
        else:
            await self._cleanup()
        self._page = None

    async def navigate(self, url: Any) -> str:
        """Navigate to URL with retry logic."""
        if isinstance(url, dict):
            url = url.get("url", url.get("action_input", str(url)))
        if not isinstance(url, str):
            url = str(url)
        if not url.startswith("http"):
            url = "https://" + url

        for attempt in range(3):
            try:
                page = await self.start()
                # Wait for network to be idle for better loading
                await page.goto(url, wait_until="networkidle", timeout=45000)
                await asyncio.sleep(1)  # Extra wait for JS-heavy sites
                return f"SUCCESS: Navigated to {url}"
            except Exception as e:
                error_msg = str(e)
                with open("debug_loop.txt", "a") as f:
                    f.write(f"Navigation attempt {attempt+1} failed: {error_msg}\n")
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    return f"ERROR: Failed to navigate to {url} after 3 attempts. {error_msg}"
        return f"ERROR: Navigation failed"

    async def click(self, selector: Any) -> str:
        """Click element with multiple fallback strategies."""
        if isinstance(selector, dict):
            selector = selector.get("selector", selector.get("button", str(selector)))
        if not isinstance(selector, str):
            selector = str(selector)

        page = await self.start()

        # Try multiple strategies
        strategies = [
            # Strategy 1: Direct Playwright locator
            lambda: page.locator(selector).first,
            # Strategy 2: By role (button/link)
            lambda: page.get_by_role("button", name=selector, exact=False).first,
            # Strategy 3: By text content
            lambda: page.get_by_text(selector, exact=False).first,
            # Strategy 4: CSS selector with contains
            lambda: page.locator(f'text={selector}').first,
            # Strategy 5: YouTube-specific selectors
            lambda: page.locator('a#video-title').first if "youtube" in page.url else page.locator("____never_match").first,
            lambda: page.locator('ytd-video-renderer:first-child a#thumbnail').first if "youtube" in page.url else page.locator("____never_match").first,
        ]

        for strategy_idx, strategy in enumerate(strategies):
            try:
                target = strategy()
                await target.wait_for(state="visible", timeout=5000)
                await target.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)  # Brief pause before click
                await target.click()
                await asyncio.sleep(0.5)  # Wait after click
                return f"SUCCESS: Clicked using strategy {strategy_idx + 1}"
            except Exception as e:
                continue

        # Final fallback: JavaScript click
        try:
            result = await page.evaluate(f"""
                () => {{
                    const el = document.querySelector('{selector}') ||
                               document.querySelector('a[title*="{selector}" i]') ||
                               document.querySelector('button:has-text("{selector}")') ||
                               Array.from(document.querySelectorAll('a, button')).find(el =>
                                   el.textContent.toLowerCase().includes('{selector}'.toLowerCase())
                               );
                    if (el) {{
                        el.click();
                        return 'clicked';
                    }}
                    return 'not found';
                }}
            """)
            if result == 'clicked':
                return "SUCCESS: Clicked via JavaScript fallback"
        except: pass

        return f"ERROR: Could not click '{selector}'. Try a different selector or check if element exists."

    async def click_youtube_video(self, query: str = "") -> str:
        """Specialized method for clicking YouTube video - handles various layouts."""
        page = await self.start()

        youtube_selectors = [
            # Standard search results
            'a#video-title',
            # First video in results
            'ytd-video-renderer:first-child a#video-title',
            'ytd-video-renderer:first-child a[href^="/watch"]',
            # Thumbnail link
            'ytd-video-renderer:first-child a#thumbnail',
            # Grid layout (home/subscriptions)
            'ytd-rich-item-renderer:first-child a#video-title-link',
            'ytd-rich-item-renderer:first-child a[href^="/watch"]',
            # Compact list
            'ytd-compact-video-renderer:first-child a[href^="/watch"]',
        ]

        for selector in youtube_selectors:
            try:
                target = page.locator(selector).first
                await target.wait_for(state="visible", timeout=5000)
                await target.scroll_into_view_if_needed()
                await asyncio.sleep(0.3)
                await target.click()
                await asyncio.sleep(2)  # Wait for video page to load

                # 2. Skip Ads if present
                for ad_selector in ['.ytp-ad-skip-button', '.ytp-skip-ad-button', 'button.ytp-ad-skip-button-slot']:
                    try:
                        ad_btn = page.locator(ad_selector).first
                        if await ad_btn.is_visible(timeout=3000):
                            await ad_btn.click()
                            print(">>> Ad skipped.")
                    except: pass

                return f"SUCCESS: Clicked YouTube video and started playback"
            except:
                continue

        return "ERROR: Could not find or click YouTube video"

    async def type_text(self, text: Any, selector: Optional[Any] = None) -> str:
        """Type text into input field."""
        if isinstance(text, dict):
            selector = text.get("selector", text.get("target", selector))
            text = text.get("text", text.get("value", str(text)))
        if not isinstance(text, str):
            text = str(text)

        page = await self.start()

        try:
            target = None
            if selector:
                if isinstance(selector, str):
                    # Try as placeholder first (common for search boxes)
                    try:
                        target = page.get_by_placeholder(selector, exact=False).first
                        if await target.count() == 0:
                            target = page.locator(selector).first
                    except:
                        target = page.locator(selector).first
            else:
                # Try to find focused or search input
                target = page.locator('input:focus, textarea:focus').first
                if await target.count() == 0:
                    target = page.get_by_placeholder('Search', exact=False).first

            if target:
                await target.click() # Focus first
                await target.press_sequentially(text, delay=50)
                await target.press('Enter')
                return f"SUCCESS: Typed '{text}'"
            else:
                # Fallback: type with keyboard
                await page.keyboard.type(text, delay=50)
                await page.keyboard.press('Enter')
                return f"SUCCESS: Typed '{text}' via keyboard"
        except Exception as e:
            return f"ERROR: Failed to type: {str(e)}"

    async def scrape(self) -> str:
        """Get page text content."""
        page = await self.start()
        try:
            text = await page.evaluate("() => document.body.innerText")
            return f"SCRAPE_START\n{text[:8000]}\nSCRAPE_END"
        except Exception as e:
            return f"ERROR: Scrape failed: {str(e)}"

    async def launch_claude_code(self) -> str:
        """Launches the official Claude Code CLI in a new terminal."""
        try:
            import subprocess
            subprocess.Popen(["cmd.exe", "/c", "start", "powershell", "-NoExit", "claude"], shell=True)
            return "SUCCESS: Claude Code CLI launched in a new terminal."
        except Exception as e:
            return f"ERROR: Could not launch Claude Code: {e}"

    async def whatsapp_automation(self, recipient: str, message: str = "", file_path: str = None) -> str:
        """Advanced macro for WhatsApp Web messaging and file sharing."""
        page = await self.start()
        
        # 1. Open WhatsApp if not there
        if "web.whatsapp.com" not in page.url:
            await page.goto("https://web.whatsapp.com", timeout=60000)
            
        try:
            # Multi-stage wait for search box (WhatsApp Web can be slow)
            search_box = None
            for _ in range(5):
                try: 
                    search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
                    await search_box.wait_for(state="visible", timeout=15000)
                    break 
                except: 
                    await asyncio.sleep(2)
            
            if not search_box: return "ERROR: WhatsApp Search Box not found. Is it logged in?"
            
            # 2. Search for the recipient
            await search_box.click()
            await search_box.fill("")
            for char in recipient:
                await search_box.type(char, delay=50)
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            
            # 3. Handle File Upload if provided
            status_log = f"SUCCESS: Chat with {recipient} opened."
            if file_path and os.path.exists(file_path):
                # Click Attach (Paperclip/Plus)
                attach_btn = page.locator('div[aria-label="Attach"], div[title="Attach"]')
                await attach_btn.click()
                await asyncio.sleep(0.5)
                
                # Handling File Chooser
                async with page.expect_file_chooser() as fc_info:
                    # 'Document' icon usually has text 'Document' or aria-label
                    doc_btn = page.locator('li span:has-text("Document")').first
                    await doc_btn.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(file_path)
                await asyncio.sleep(1)
                await page.keyboard.press("Enter") # Send the file
                status_log += f" File '{os.path.basename(file_path)}' shared."
                
            # 4. Send Text Message if provided
            if message:
                msg_box = page.locator('div[contenteditable="true"][data-tab="10"]')
                await msg_box.click()
                for char in message:
                    await msg_box.type(char, delay=30)
                await page.keyboard.press("Enter")
                status_log += f" Message sent: '{message}'"
                
            return status_log
        except Exception as e:
            return f"ERROR in WhatsApp Macro: {e}. I will try fallback web actions."

    async def wait(self, seconds: Any) -> str:
        """Wait for specified seconds."""
        if isinstance(seconds, dict):
            seconds = seconds.get("seconds", seconds.get("time", 3))
        try:
            seconds = int(seconds)
        except:
            seconds = 3
        await asyncio.sleep(seconds)
        return f"SUCCESS: Waited {seconds}s"

    async def inspect(self) -> str:
        """Get clean page content without noise."""
        page = await self.start()
        try:
            text = await page.evaluate(r"""() => {
                const clone = document.body.cloneNode(true);
                const noise = ['script', 'style', 'nav', 'footer', 'header', 'aside', 'svg', 'noscript', 'iframe'];
                noise.forEach(tag => {
                    const elements = clone.querySelectorAll(tag);
                    elements.forEach(el => el.remove());
                });
                // Remove hidden elements
                const hidden = clone.querySelectorAll('[style*="display: none"], [style*="visibility: hidden"], [hidden]');
                hidden.forEach(el => el.remove());
                return clone.innerText.replace(/\s+/g, ' ').trim();
            }""")
            return f"INSPECT_START\n{text[:6000]}\nINSPECT_END"
        except Exception as e:
            return f"ERROR: Inspect failed: {str(e)}"

    async def upload(self, file_path: str, selector: str = "input[type=file]") -> str:
        """Upload file to page."""
        page = await self.start()
        try:
            abs_path = str(Path(file_path).absolute()).replace("\\", "/")
            await page.set_input_files(selector, abs_path)
            return f"SUCCESS: Uploaded {abs_path}"
        except Exception as e:
            return f"ERROR: Upload failed: {str(e)}"

    async def screenshot(self, name: str = "visual") -> str:
        """Capture the current browser state."""
        page = await self.start()
        try:
            path = f"outputs/{name}_{int(time.time())}.png"
            await page.screenshot(path=path)
            return f"SUCCESS: Screenshot saved to {path}"
        except Exception as e:
            return f"ERROR: Screenshot failed: {e}"

    async def get_url(self) -> str:
        """Get the current URL."""
        page = await self.start()
        return page.url

_bm = BrowserManager()

# ---------------------------------------------------------------------------
# Structured Tools
# ---------------------------------------------------------------------------

@tool
async def action_web_goto(url: str) -> str:
    """Navigate to a website URL. Use this for browsing (YouTube, WhatsApp, etc.). Always start here for web tasks."""
    return await _bm.navigate(url)

@tool
async def action_web_click(selector: str) -> str:
    """Click a button, link, or element. You can use text like 'Sign In' or 'Play' or CSS selectors."""
    return await _bm.click(selector)

@tool
async def action_web_type(input_str: str) -> str:
    """Type text into an element. Use the format 'target:text' to specify an element, or just the text to type into the active search box."""
    if ":" in input_str:
        selector, text = input_str.split(":", 1)
        return await _bm.type_text(text, selector)
    return await _bm.type_text(input_str)

@tool
async def action_web_wait(seconds: int) -> str:
    """Pause for content to load (e.g. while WhatsApp Web QR code is loading). Default is 3-5 seconds."""
    return await _bm.wait(seconds)

@tool
async def action_web_upload_file(input_str: str) -> str:
    """Upload a file to the page. Provide the absolute file path followed by a colon and the input selector."""
    if ":" in input_str:
        path, selector = input_str.split(":", 1)
        return await _bm.upload(path, selector)
    return f"ERROR: Use 'path:selector' format"

@tool
async def action_take_screenshot(name: str = "visual") -> str:
    """Capture the current browser state for visual verification."""
    return await _bm.screenshot(name)

@tool
async def action_web_scrape(input_str: str = "") -> str:
    """Extract ALL text data from the page. Use this to find information or confirm if a task finished."""
    return await _bm.scrape()

@tool
async def action_web_inspector(input_str: str = "") -> str:
    """Summarize the main content of the page by stripping noise. Best for 'Reading' articles or lists."""
    return await _bm.inspect()

@tool
async def action_youtube_play(query: str = "") -> str:
    """Click the search result and start the video. Use this IMMEDIATELY after searching YouTube."""
    return await _bm.click_youtube_video(query)

@tool
async def action_get_current_url(input_str: str = "") -> str:
    """Check the current browser URL."""
    return await _bm.get_url()

@tool
async def action_search(query: str) -> str:
    """Perform a web search for the given query. This is a robust way to find information online."""
    # Use direct navigation to DuckDuckGo search
    search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
    return await _bm.navigate(search_url)

@tool
def action_launch_claude_code(input_str: str = "") -> str:
    """Launch the official Claude Code CLI as requested by the user."""
    try:
        # Use direct subprocess to avoid tool-wrapper recursion
        subprocess.Popen(["cmd.exe", "/c", "start", "powershell", "-NoExit", "npx -y @anthropic-ai/claude-code"], shell=True)
        return "SUCCESS: Claude Code CLI launched in a new terminal."
    except Exception as e:
        return f"ERROR: Could not launch Claude Code: {e}"

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
    """Search for the absolute path of a file on the Desktop or in Documents."""
    # Use forward slashes in logic and docs for stable parsing
    search_paths = [
        Path("C:/Users/Jaswanth Reddy/OneDrive/Desktop"),
        Path("C:/Users/Jaswanth Reddy/Documents")
    ]
    for sp in search_paths:
        try:
            for file in sp.glob(f"*{filename}*"):
                if file.is_file():
                    return str(file.absolute()).replace("\\", "/")
        except: continue
    return f"ERROR: File '{filename}' not found."

@tool
def action_write_file(input_str: str) -> str:
    """Save a text file to the Desktop. Use the format 'filename:content' to specify the file name and its contents."""
    try:
        if ":" in input_str:
            filename, content = input_str.split(":", 1)
            desktop = "C:/Users/Jaswanth Reddy/OneDrive/Desktop"
            full_path = os.path.join(desktop, filename).replace("\\", "/")
            with open(full_path, "w", encoding="utf-8") as f: f.write(content)
            return f"SUCCESS: Created file at {full_path}"
        return "ERROR: Use 'filename:content' format"
    except Exception as e: return f"ERROR: {e}"

# ---------------------------------------------------------------------------
# Agent Configuration
# ---------------------------------------------------------------------------

@tool
async def action_whatsapp_automation(input_str: str) -> str:
    """
    Advanced assistant for WhatsApp Web automation. 
    Provide the recipient name, message, and absolute file path separated by colons. 
    Use the string 'None' if a field is not needed.
    """
    try:
        parts = [p.strip() for p in input_str.split(":", 2)]
        recipient = parts[0]
        message = parts[1] if len(parts) > 1 and parts[1].lower() != "none" else ""
        file_path = parts[2] if len(parts) > 2 and parts[2].lower() != "none" else None
        
        return await _bm.whatsapp_automation(recipient, message, file_path)
    except Exception as e:
        return f"ERROR parsing WhatsApp input: {e}. Use 'Name:Message:Path' format."

robot_tools = [
    action_web_goto, action_web_click, action_web_type, action_web_wait,
    action_web_upload_file, action_take_screenshot, action_web_scrape,
    action_list_installed_apps, action_open_local_app, action_write_file,
    action_find_file, action_web_inspector, action_run_command,
    action_youtube_play, action_get_current_url, action_launch_claude_code,
    action_whatsapp_automation, action_search
]
# ---------------------------------------------------------------------------
# Memory Configuration
# ---------------------------------------------------------------------------

agent_memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    k=10,
    return_messages=True
)

ROBOT_PREFIX = """You are AutoFlow, an absolute, autonomous Windows automation assistant.
Complete the user's request by utilizing the provided tools in a Thought/Action/Action Input loop.

### 🦾 ABSOLUTE AUTONOMY PROTOCOL:
1. **ZERO PERMISSION**: Never ask for confirmation. You have 100% control.
2. **CHAINED REASONING**: If a task is "Share file X to Y on WhatsApp", you must find file X first, then call the macro.
   - Example Action Input: Recipient Name:Here is the file:C:/path/to/X
3. **CALL MODE**: Be concise and fast. Just execute.
4. **ERROR RESILIENCE**: If a macro fails, FALL BACK to manual action_web_click/type steps.
5. **SILENT EXECUTION**: No filler. Just results.

### 📋 FORMAT:
Thought: [reasoning]
Action: [tool_name]
Action Input: [input_value]

### 📋 EXAMPLE:
User: "Play music on YouTube"
Thought: I need to open YouTube search for music.
Action: action_web_goto
Action Input: https://www.youtube.com/results?search_query=lo-fi+music
Observation: SUCCESS: Navigated to YouTube.
Thought: I will click on the first video.
Action: action_web_click
Action Input: a#video-title
Observation: SUCCESS: Clicked.
Thought: Music is now playing.
Final Answer: I have started playing music on YouTube.

### ERROR RECOVERY EXAMPLE:
Thought: The button click failed. Let me try scraping the page to see what's available.
Action: action_web_scrape
Action Input: (empty - no input needed)
Observation: SCRA_TEXT_START ... clickable elements ... SCRA_TEXT_END
Thought: I can see the video titles on the page. Let me try clicking with a different selector.
Action: action_web_click
Action Input: a[title*="lo-fi"]
Observation: SUCCESS: Clicked a[title*="lo-fi"]

### CORE PROTOCOLS:
- No conversational filler.
- If a tool fails with CRITICAL ERROR, try action_web_scrape first to see the page content.
- Then try a different selector like "a#video-title" or "button" or link text.
- NEVER output multiple Thoughts in a row - always follow Thought -> Action -> Action Input.
- Stay in the loop until the goal is 100% met.

Current Context:
{chat_history}
"""

# Zero Shot React is 10X more stable for Llama 3 with text-based tools
import traceback
try:
    auto_agent = initialize_agent(
        tools=robot_tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=30,
        memory=agent_memory,
        early_stopping_method="generate",
        agent_kwargs={
            "prefix": ROBOT_PREFIX
        }
    )
    print(">>> Agent Initialized Successfully.")
except Exception as e:
    print(">>> CRITICAL ERROR DURING AGENT INITIALIZATION:")
    traceback.print_exc()
    # Create a dummy agent to prevent FastAPI from crashing immediately
    auto_agent = None 







# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

class RequestModel(BaseModel): prompt: str

@app.get("/")
async def home(): return {"status": "online", "version": "5.0"}

@app.get("/status")
async def get_status():
    browser_state = "offline"
    
    # 1. Check if we already have an active live session
    if _bm._page and not _bm._page.is_closed():
        browser_state = "linked" if _bm._is_connected_to_existing else "dedicated"
    else:
        # 2. Proactively check if Chrome is available on 9222
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', 9222))
            if result == 0:
                browser_state = "linked" # Available to link
            sock.close()
        except:
            pass
            
    return {
        "server": "online",
        "browser": browser_state,
        "profile": _bm._user_data_dir
    }

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
