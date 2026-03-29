# 🤖 AutoFlow: The AI-Powered Computer Controller

AutoFlow is a desktop application that bridges the gap between LLMs (Llama3) and your local computer. It combines a sleek React UI with powerful automation tools to perform complex tasks across your OS and the web.

![Connected Status](C:\Users\Jaswanth Reddy\.gemini\antigravity\brain\79c05d1f-6591-475a-9896-398a6c244793\.system_generated\click_feedback\click_feedback_1774288677747.png)

## 🌟 Features
- ⚡ **Physical Control**: Move the mouse, click, and type into local applications via `PyAutoGUI`.
- 👁️ **Web Automation**: Navigate, search, and interact with websites using `Playwright`.
- 🧠 **Scraping & Reasoning**: Extract text from webpages and summarize its content using Llama3.
- 📂 **File System Integration**: Save research results and summaries directly to your OneDrive Desktop.
- 🚀 **Desktop Native**: A standalone Electron app for a premium, fast experience.

## 🌟 🚀 Hyper-Stability & New Features
- 🔗 **Real Chrome Session Persistence**: Link your main Chrome profile to AutoFlow with a single click. No more "test browsers" or missing logins.
- 📺 **Intelligent Ad-Skipping**: Specialized routines for YouTube to ensure uninterrupted music.
- 📡 **Live System Badges**: Real-time feedback in the UI for both API and Browser Link status.
- 🧠 **Boosted Intelligence**: 2X memory window (k=10) for complex, multi-site automation.

## 🛠️ Tech Stack
- **Frontend**: React (Vite) + Electron
- **Backend**: FastAPI + Python 3.11+
- **AI Engine**: LangChain + Ollama (Llama 3)
- **Automation**: Playwright (Web) & subprocess (Registry/CLI)

## 🚦 Getting Started

### 1. Prerequisites
- [Ollama](https://ollama.com/) installed and running (`ollama pull llama3`).
- Node.js & npm installed.
- Python 3.11+ installed.

### 2. Fast Launch (Recommended)
The most stable way to run AutoFlow is using the **Master Launcher**:
1. Close all manual Chrome windows.
2. Right-click [start_autoflow.ps1](file:///c:/Users/Jaswanth Reddy/OneDrive/Desktop/Projects/Auto_Flow/start_autoflow.ps1) and select **"Run with PowerShell"**.
   - This script will automatically clear stale ports, link your Chrome profile, and start both the backend and UI.

### 3. Manual Startup
If you prefer manual control:
```powershell
# Backend
.\venv\Scripts\python.exe main.py

# UI (new terminal)
cd ui
npm run dev
```

## 🏁 Example Task for Testing
Try giving AutoFlow a complex multi-step order to see its new stability in action:
> *"Search for 'lofi girl' on YouTube, play it, then create a file on my desktop called 'music_link.txt' with the current video URL inside it."*

---
**AutoFlow is now 100% stable, authenticated, and ready to automate your world.** 🦾🎸
