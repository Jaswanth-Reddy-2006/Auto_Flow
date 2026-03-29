import { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'
import { Zap, Send, Trash2, Command, Clock, AlertCircle, Mic, Volume2, VolumeX, Phone, MessageSquare } from 'lucide-react'

const BACKEND_URL = 'http://127.0.0.1:8000'

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'ai',
      text: "Hey! I'm AutoFlow. I can help you with:\n\n• Browse websites (YouTube, WhatsApp Web)\n• Open local apps\n• Run CLI commands\n• Find and manage files\n\nWhat would you like me to do?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState('checking')
  const [isMaximized, setIsMaximized] = useState(false)
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [viewMode, setViewMode] = useState('chat') // 'chat' or 'call'
  const [isListening, setIsListening] = useState(false)
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const textareaRef = useRef(null)
  const recognitionRef = useRef(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [input])

  // Status polling
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/status`, { timeout: 2000 })
        setStatus(res.data)
      } catch {
        setStatus({ server: 'offline', browser: 'none' })
      }
    }
    checkStatus()
    const interval = setInterval(checkStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Voice Synthesis (TTS)
  const speak = useCallback((text) => {
    if (!isVoiceEnabled || !window.speechSynthesis) return
    window.speechSynthesis.cancel() // Stop any current speech
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 1.1
    utterance.pitch = 1
    
    // Auto-Listen logic for Call Mode
    utterance.onend = () => {
      if (viewMode === 'call') {
        setTimeout(() => {
          if (!isListening) toggleListening()
        }, 800) // 800ms breath for natural flow
      }
    }
    
    window.speechSynthesis.speak(utterance)
  }, [isVoiceEnabled, viewMode, isListening])

  // Voice Recognition (STT)
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = false
      recognitionRef.current.lang = 'en-US'

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        setIsListening(false)
        if (transcript) sendMessageDirect(transcript)
      }

      recognitionRef.current.onerror = () => setIsListening(false)
      recognitionRef.current.onend = () => setIsListening(false)
    }
  }, [])

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
    } else {
      // Silence before listening to prevent AI hearing itself
      window.speechSynthesis.cancel() 
      try {
        recognitionRef.current?.start()
        setIsListening(true)
      } catch (err) {
        console.error("SpeechRecognition start error:", err)
      }
    }
  }

  const clearChat = useCallback(() => {
    setMessages([{
      id: Date.now(),
      role: 'ai',
      text: "Chat cleared. How can I help you?",
      timestamp: new Date(),
    }])
    inputRef.current?.focus()
  }, [])

  const sendMessageDirect = async (text) => {
    if (!text.trim() || isLoading) return

    // Handle commands
    if (text.trim() === '/clear') {
      clearChat()
      setInput('')
      return
    }

    const userMsg = {
      id: Date.now(),
      role: 'user',
      text: text.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const res = await axios.post(`${BACKEND_URL}/ask`, { prompt: text.trim() }, { timeout: 120000 })
      const aiResponseText = res.data.result
      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        text: aiResponseText,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, aiMsg])
      if (isVoiceEnabled) speak(aiResponseText)
    } catch (err) {
      const errorMsg = err.code === 'ECONNABORTED'
        ? 'Request timed out. The task may still be running in the background.'
        : 'Error reaching backend. Please check if the server is running.'
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: 'ai',
        text: errorMsg,
        timestamp: new Date(),
        isError: true
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const sendMessage = () => sendMessageDirect(input)

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
    if (e.key === 'Escape') {
      setShowShortcuts(false)
    }
  }

  // Format timestamp
  const formatTime = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  // Electron IPC
  const ipc = (() => {
    try {
      if (window.require) {
        return window.require('electron').ipcRenderer
      }
      return null
    } catch (e) {
      return null
    }
  })()

  useEffect(() => {
    if (!isLoading) inputRef.current?.focus()
  }, [isLoading])

  const closeWindow = () => ipc?.send('close-window')
  const minimizeWindow = () => ipc?.send('minimize-window')
  const toggleMaximize = () => {
    ipc?.send('toggle-maximize')
    setIsMaximized(v => !v)
  }

  // Status config
  const statusConfig = {
    online: { dot: 'dot-online', label: 'Connected', badge: 'badge-online' },
    offline: { dot: 'dot-offline', label: 'Offline', badge: 'badge-offline' },
    none: { dot: 'dot-offline', label: 'Not Linked', badge: 'badge-offline' },
    linked: { dot: 'dot-online', label: 'Main Chrome', badge: 'badge-online' },
    dedicated: { dot: 'dot-online', label: 'AutoFlow Chrome', badge: 'badge-online' },
    checking: { dot: 'dot-checking', label: 'Connecting...', badge: 'badge-checking' },
  }
  const serverStatus = statusConfig[status.server] || statusConfig.checking
  const browserStatus = statusConfig[status.browser] || statusConfig.none

  // Quick action suggestions
  const suggestions = [
    "Open Chrome",
    "Play music on YouTube",
    "Open Notepad",
    "Check weather"
  ]

  return (
    <div className="app">
      {/* Title Bar */}
      <div className="titlebar" data-drag-region="true">
        <div className="titlebar-left">
          <div className="app-icon">
            <Zap size={20} fill="currentColor" />
          </div>
          <span className="app-name">AutoFlow</span>
          <div className="flex items-center gap-2">
            <div className={`status-badge ${serverStatus.badge}`}>
              <span className={`status-dot ${serverStatus.dot}`} />
              <span className="status-label">API: {serverStatus.label}</span>
            </div>
            <div className={`status-badge ${browserStatus.badge}`}>
              <span className={`status-dot ${browserStatus.dot}`} />
              <span className="status-label">Browser: {browserStatus.label}</span>
            </div>
          </div>
        </div>
          <div className="window-controls">
            <button
              className={`wc-btn ${viewMode === 'call' ? 'text-primary' : 'text-muted'}`}
              onClick={() => {
                const nextMode = viewMode === 'chat' ? 'call' : 'chat'
                setViewMode(nextMode)
                if (nextMode === 'call') {
                  setIsVoiceEnabled(true)
                  speak("Call Mode activated. I am listening.")
                  setTimeout(() => toggleListening(), 2000) // Start listening after greeting
                } else {
                  window.speechSynthesis.cancel()
                  setIsListening(false)
                }
              }}
              title={viewMode === 'chat' ? "Enter Call Mode" : "Return to Chat"}
            >
              {viewMode === 'chat' ? <Phone size={16} /> : <MessageSquare size={16} />}
            </button>
            <button
              className={`wc-btn ${isVoiceEnabled ? 'text-primary' : 'text-muted'}`}
              onClick={() => setIsVoiceEnabled(!isVoiceEnabled)}
              title={isVoiceEnabled ? "Disable AI Voice" : "Enable AI Voice"}
            >
              {isVoiceEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
            </button>
            <button
              className="wc-btn wc-shortcuts"
            onClick={() => setShowShortcuts(!showShortcuts)}
            title="Keyboard Shortcuts"
          >
            <Command size={14} />
          </button>
          <button className="wc-btn wc-min" onClick={minimizeWindow} title="Minimize">─</button>
          <button className="wc-btn wc-max" onClick={toggleMaximize} title="Maximize">
            {isMaximized ? '❐' : '□'}
          </button>
          <button className="wc-btn wc-close" onClick={closeWindow} title="Close">✕</button>
        </div>
      </div>

      {/* Shortcuts Panel */}
      {showShortcuts && (
        <div className="shortcuts-panel">
          <h3>Keyboard Shortcuts</h3>
          <div className="shortcut-item">
            <kbd>Enter</kbd>
            <span>Send message</span>
          </div>
          <div className="shortcut-item">
            <kbd>Shift</kbd> + <kbd>Enter</kbd>
            <span>New line</span>
          </div>
          <div className="shortcut-item">
            <kbd>/clear</kbd>
            <span>Clear chat history</span>
          </div>
          <div className="shortcut-item">
            <kbd>Esc</kbd>
            <span>Close panels</span>
          </div>
          <button className="close-shortcuts" onClick={() => setShowShortcuts(false)}>
            Close
          </button>
        </div>
      )}

      {/* Main Content Area */}
      {viewMode === 'chat' ? (
        <>
          <div className="messages-wrapper">
            <div className="messages">
              {messages.map((msg) => (
                <div key={msg.id} className={`msg-row ${msg.role === 'user' ? 'msg-row-user' : 'msg-row-ai'}`}>
                  {msg.role === 'ai' && (
                    <div className="avatar">
                      <Zap size={18} fill="currentColor" />
                    </div>
                  )}
                  <div className="message-group">
                    <div className={`bubble ${msg.role === 'user' ? 'bubble-user' : 'bubble-ai'} ${msg.isError ? 'bubble-error' : ''}`}>
                      {msg.text.split('\n').map((line, i) => (
                        <div key={i} style={{ marginBottom: i < msg.text.split('\n').length - 1 ? '4px' : 0 }}>
                          {line || ' '}
                        </div>
                      ))}
                    </div>
                    <div className={`timestamp ${msg.role === 'user' ? 'timestamp-user' : 'timestamp-ai'}`}>
                      <Clock size={10} />
                      {formatTime(msg.timestamp)}
                      {msg.isError && <AlertCircle size={10} style={{ marginLeft: '4px', color: '#fca5a5' }} />}
                    </div>
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

          {/* Suggestions */}
          {messages.length <= 2 && !isLoading && (
            <div className="suggestions-bar">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  className="suggestion-chip"
                  onClick={() => sendMessageDirect(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          {/* Input Bar */}
          <div className="input-bar">
            <button
              className="clear-btn"
              onClick={clearChat}
              title="Clear chat"
              disabled={messages.length <= 1}
            >
              <Trash2 size={18} />
            </button>
            <div className="input-container">
              <textarea
                ref={(el) => {
                  inputRef.current = el
                  textareaRef.current = el
                }}
                className="input-field"
                placeholder="Ask AutoFlow to do something... (type /clear to reset)"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                rows={1}
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={toggleListening}
                className={`input-btn mic-btn ${isListening ? 'listening-pulse' : ''}`}
                title={isListening ? "Stop Listening" : "Start Voice Command"}
              >
                <Mic size={18} color={isListening ? '#ff4b2b' : 'currentColor'} />
              </button>
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="input-btn send-btn"
                title="Send Message"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </>
      ) : (
        /* Immersive Call View */
        <div className="call-mode-wrapper">
          <div className="call-header">
            <h2>Call Mode</h2>
            <p className="call-subtitle">
              {isLoading ? "PROCESSING..." : isListening ? "LISTENING..." : "READY"}
            </p>
          </div>

          <div className={`call-avatar-container ${isLoading ? 'pulse-speak' : isListening ? 'pulse-listen' : ''}`}>
             <div className="call-avatar-inner">
                <Zap size={80} fill="currentColor" className={isLoading ? 'shake-icon' : ''} />
             </div>
          </div>

          <div className="call-transcription">
             <p>{messages[messages.length - 1]?.text.slice(0, 150)}{messages[messages.length - 1]?.text.length > 150 ? "..." : ""}</p>
          </div>

          <div className="call-controls">
             <button 
                className={`call-ctrl-btn call-mic-btn ${isListening ? 'active' : ''}`}
                onClick={toggleListening}
             >
                <Mic size={28} />
             </button>
             <button 
                className="call-ctrl-btn call-end-btn"
                onClick={() => setViewMode('chat')}
             >
                <MessageSquare size={28} />
             </button>
          </div>
        </div>
      )}
    </div>
  )
}
