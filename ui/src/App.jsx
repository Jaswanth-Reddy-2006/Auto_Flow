import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Zap, Monitor, Laptop, Globe, Send } from 'lucide-react'

const BACKEND_URL = 'http://127.0.0.1:8000'

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'ai',
      text: "Hey! I'm AutoFlow. Ready to help you with your desktop tasks. 🤖✨",
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

  // Split sendMessage logic to support direct voice trigger
  const sendMessageDirect = async (text) => {
    if (!text || isLoading) return
    const userMsg = { id: Date.now(), role: 'user', text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const res = await axios.post(`${BACKEND_URL}/ask`, { prompt: text })
      const aiResponseText = res.data.result;
      const aiMsg = { id: Date.now() + 1, role: 'ai', text: aiResponseText }
      setMessages((prev) => [...prev, aiMsg])
    } catch (err) {
      setMessages(prev => [...prev, { id: Date.now(), role: 'ai', text: 'Error reaching backend.', isError: true }]);
    } finally {
      setIsLoading(false)
    }
  }

  const sendMessage = () => sendMessageDirect(input);

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // ── Window controls (Electron IPC) ──────────────────────────────────────────
  const ipc = (() => {
    try {
      // Better electron check
      if (window?.process?.type === 'renderer') {
         const { ipcRenderer } = window.require('electron');
         return ipcRenderer;
      }
      return null;
    } catch (e) {
      return null;
    }
  })()

  const closeWindow    = () => {
    console.log('Closing window...')
    ipc?.send('close-window')
  }
  const minimizeWindow = () => {
    console.log('Minimizing window...')
    ipc?.send('minimize-window')
  }
  const toggleMaximize = () => {
    console.log('Toggling maximize...')
    ipc?.send('toggle-maximize')
    setIsMaximized(v => !v)
  }


  // ── Status config ──────────────────────────────────────────────────────────
  const statusConfig = {
    online: { dot: 'dot-online', label: 'Connected', badge: 'badge-online' },
    offline: { dot: 'dot-offline', label: 'Offline', badge: 'badge-offline' },
    checking: { dot: 'dot-checking', label: 'Connecting…', badge: 'badge-checking' },
  }
  const { dot, label, badge } = statusConfig[status]

  return (
    <div className="app">
      {/* ── Title Bar ─────────────────────────────────────────────────── */}
      <div className="titlebar" data-drag-region="true">
        <div className="titlebar-left">
          <div className="app-icon">
            <Zap size={20} fill="currentColor" />
          </div>
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
                <div className="avatar">
                  <Zap size={18} fill="currentColor" />
                </div>
              )}
              <div className={`bubble ${msg.role === 'user' ? 'bubble-user' : 'bubble-ai'} ${msg.isError ? 'bubble-error' : ''}`}>
                {msg.text}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="msg-row msg-row-ai">
              <div className="avatar">
                 <Zap size={18} fill="currentColor" />
              </div>
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
        <div className="input-container">
          <textarea
            ref={inputRef}
            className="input-field"
            placeholder="Ask AutoFlow to do something..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
            disabled={isLoading}
          />
        </div>
        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? '…' : <Send size={20} />}
        </button>
      </div>
    </div>
  )
}

