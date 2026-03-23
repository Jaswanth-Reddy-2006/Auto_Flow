import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const BACKEND_URL = 'http://127.0.0.1:8000'

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'ai',
      text: "Hey! I'm AutoFlow. Ask me to move your mouse, open apps, or just chat. Type 'test the hand' to see what I can do! 🤖",
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState('checking') // 'online' | 'offline' | 'checking'
  const [isMaximized, setIsMaximized] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // ── Status polling ──────────────────────────────────────────────────────────
  useEffect(() => {
    const checkStatus = async () => {
      try {
        await axios.get(`${BACKEND_URL}/`, { timeout: 2000 })
        setStatus('online')
      } catch {
        setStatus('offline')
      }
    }
    checkStatus()
    const interval = setInterval(checkStatus, 3000)
    return () => clearInterval(interval)
  }, [])

  // ── Auto-scroll ─────────────────────────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // ── Send message ────────────────────────────────────────────────────────────
  const sendMessage = async () => {
    const text = input.trim()
    if (!text || isLoading) return

    const userMsg = { id: Date.now(), role: 'user', text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const res = await axios.post(`${BACKEND_URL}/ask`, { prompt: text })
      const aiMsg = { id: Date.now() + 1, role: 'ai', text: res.data.result }
      setMessages((prev) => [...prev, aiMsg])
    } catch (err) {
      const errMsg = {
        id: Date.now() + 1,
        role: 'ai',
        text: '⚠️ Could not reach the AutoFlow backend. Make sure `uvicorn main:app` is running on port 8000.',
        isError: true,
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setIsLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // ── Window controls (Electron IPC) ──────────────────────────────────────────
  const ipc = (() => {
    try { return window.require('electron').ipcRenderer } catch { return null }
  })()

  const closeWindow    = () => ipc?.send('close-window')
  const minimizeWindow = () => ipc?.send('minimize-window')
  const toggleMaximize = () => {
    ipc?.send('toggle-maximize')
    setIsMaximized(v => !v)
  }

  // ── Status config ──────────────────────────────────────────────────────────
  const statusConfig = {
    online: { dot: 'dot-online', label: 'Connected to AutoFlow', badge: 'badge-online' },
    offline: { dot: 'dot-offline', label: 'Backend Offline', badge: 'badge-offline' },
    checking: { dot: 'dot-checking', label: 'Connecting…', badge: 'badge-checking' },
  }
  const { dot, label, badge } = statusConfig[status]

  return (
    <div className="app">
      {/* ── Title Bar ─────────────────────────────────────────────────── */}
      <div className="titlebar" data-drag-region="true">
        <div className="titlebar-left">
          <div className="app-icon">⚡</div>
          <span className="app-name">AutoFlow</span>
          <div className={`status-badge ${badge}`}>
            <span className={`status-dot ${dot}`} />
            <span className="status-label">{label}</span>
          </div>
        </div>
        <div className="window-controls">
          <button className="wc-btn wc-min" onClick={minimizeWindow} title="Minimize">─</button>
          <button className="wc-btn wc-max" onClick={toggleMaximize} title="Maximize">
            {isMaximized ? '❐' : '□'}
          </button>
          <button className="wc-btn wc-close" onClick={closeWindow} title="Close">✕</button>
        </div>
      </div>

      {/* ── Message List ───────────────────────────────────────────────── */}
      <div className="messages-wrapper">
        <div className="messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`msg-row ${msg.role === 'user' ? 'msg-row-user' : 'msg-row-ai'}`}>
              {msg.role === 'ai' && (
                <div className="avatar">⚡</div>
              )}
              <div className={`bubble ${msg.role === 'user' ? 'bubble-user' : 'bubble-ai'} ${msg.isError ? 'bubble-error' : ''}`}>
                {msg.text}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="msg-row msg-row-ai">
              <div className="avatar">⚡</div>
              <div className="bubble bubble-ai typing-bubble">
                <span className="dot-bounce" style={{ animationDelay: '0ms' }} />
                <span className="dot-bounce" style={{ animationDelay: '150ms' }} />
                <span className="dot-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* ── Input Bar ─────────────────────────────────────────────────── */}
      <div className="input-bar">
        <textarea
          ref={inputRef}
          className="input-field"
          placeholder="Ask AutoFlow to do something… (Enter to send)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          rows={1}
          disabled={isLoading}
        />
        <button
          className={`send-btn ${isLoading ? 'send-btn-loading' : ''}`}
          onClick={sendMessage}
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? '…' : '▲'}
        </button>
      </div>
    </div>
  )
}
