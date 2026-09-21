import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import ChatMessage from '../components/ChatMessage'
import './ChatPage.css'

const API = 'http://localhost:8000'

function useApi() {
  const token = localStorage.getItem('hr_token')
  return async (path, options = {}) => {
    const res = await fetch(`${API}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...(options.headers || {}),
      },
    })
    return res
  }
}

export default function ChatPage() {
  const navigate = useNavigate()
  const apiFetch = useApi()

  const [user, setUser] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [groqKey, setGroqKey] = useState('')
  const [keyConfigured, setKeyConfigured] = useState(false)
  const [keyBannerVisible, setKeyBannerVisible] = useState(false)
  const [keyLoading, setKeyLoading] = useState(false)
  const [keyError, setKeyError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // ── Load user info & key status on mount ──────────────────────────────
  useEffect(() => {
    async function init() {
      try {
        const [meRes, keyRes] = await Promise.all([
          apiFetch('/auth/me'),
          apiFetch('/auth/key-status'),
        ])
        if (meRes.status === 401) { navigate('/login'); return }
        const meData = await meRes.json()
        const keyData = await keyRes.json()
        setUser(meData)
        setKeyConfigured(keyData.configured)
        setKeyBannerVisible(!keyData.configured)
        if (meData.name) {
          setMessages([{
            role: 'assistant',
            content: `👋 Hello ${meData.name}! I'm your HR Assistant. How can I help you today?`,
            id: Date.now(),
          }])
        }
      } catch {
        navigate('/login')
      }
    }
    init()
  }, [])

  // ── Scroll to bottom on new messages ────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // ── Submit GROQ key ──────────────────────────────────────────────────
  async function handleKeySubmit(e) {
    e.preventDefault()
    if (!groqKey.trim()) return
    setKeyLoading(true)
    setKeyError('')
    try {
      const res = await apiFetch('/auth/configure-key', {
        method: 'POST',
        body: JSON.stringify({ groq_api_key: groqKey.trim() }),
      })
      const data = await res.json()
      if (!res.ok) { setKeyError(data.detail || 'Invalid key.'); return }
      setKeyConfigured(true)
      setKeyBannerVisible(false)
      setGroqKey('')
    } catch {
      setKeyError('Could not reach the server.')
    } finally {
      setKeyLoading(false)
    }
  }

  // ── Send chat message ────────────────────────────────────────────────
  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return
    if (!keyConfigured) { setKeyBannerVisible(true); return }

    const userMsg = { role: 'user', content: text, id: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await apiFetch('/chat/message', {
        method: 'POST',
        body: JSON.stringify({ message: text, session_id: sessionId }),
      })
      const data = await res.json()
      if (!res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${data.detail || 'An error occurred.'}`, id: Date.now(), error: true }])
        return
      }
      setSessionId(data.session_id)
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply, id: Date.now(), steps: data.steps }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Server unreachable. Please check the backend.', id: Date.now(), error: true }])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  // ── Clear chat ───────────────────────────────────────────────────────
  async function handleClear() {
    if (sessionId) {
      await apiFetch(`/chat/history?session_id=${sessionId}`, { method: 'DELETE' })
    }
    setSessionId(null)
    setMessages(user ? [{
      role: 'assistant',
      content: `Chat cleared! How can I help you, ${user.name}?`,
      id: Date.now(),
    }] : [])
  }

  function handleLogout() {
    localStorage.clear()
    navigate('/login')
  }

  const levelName = { level1: 'Staff', level2: 'Manager', level3: 'Boss' }

  return (
    <div className="chat-root">
      {/* Sidebar */}
      <Sidebar
        user={user}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onClear={handleClear}
        onLogout={handleLogout}
        levelName={levelName}
      />

      {/* Main area */}
      <div className={`chat-main ${sidebarOpen ? 'sidebar-open' : ''}`}>
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-left">
            <button
              id="toggle-sidebar"
              className="icon-btn"
              onClick={() => setSidebarOpen(p => !p)}
              aria-label="Toggle sidebar"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="6" x2="21" y2="6"/>
                <line x1="3" y1="12" x2="21" y2="12"/>
                <line x1="3" y1="18" x2="21" y2="18"/>
              </svg>
            </button>
            <div className="chat-header-brand">
              <span className="chat-header-title">HR Assistant</span>
              <span className={`key-dot ${keyConfigured ? 'green' : 'red'}`} title={keyConfigured ? 'AI Ready' : 'API Key not set'} />
            </div>
          </div>
          {user && (
            <div className="chat-header-user">
              <span className={`badge badge-${user.status}`}>{levelName[user.status] || user.status}</span>
              <span className="chat-header-empid">{user.employee_id}</span>
            </div>
          )}
        </header>

        {/* GROQ Key Banner */}
        {keyBannerVisible && (
          <div className="key-banner animate-fadeIn">
            <div className="key-banner-content">
              <div className="key-banner-icon">🔑</div>
              <div>
                <p className="key-banner-title">Set your GROQ API Key to enable AI</p>
                <p className="key-banner-sub">Get your key at <a href="https://console.groq.com" target="_blank" rel="noreferrer">console.groq.com</a></p>
              </div>
            </div>
            <form onSubmit={handleKeySubmit} className="key-banner-form" id="key-form">
              <input
                id="groq-key-input"
                type="password"
                className="key-input"
                placeholder="gsk_..."
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
              />
              <button id="groq-key-submit" type="submit" className="key-btn" disabled={keyLoading}>
                {keyLoading ? <span className="spinner" style={{borderTopColor: '#fff', width:16, height:16}} /> : 'Save Key'}
              </button>
              <button type="button" className="key-dismiss" onClick={() => setKeyBannerVisible(false)}>✕</button>
            </form>
            {keyError && <p className="key-error">{keyError}</p>}
          </div>
        )}

        {/* Messages */}
        <div className="chat-messages" id="chat-messages">
          {messages.map((msg, i) => (
            <ChatMessage key={msg.id || i} message={msg} />
          ))}

          {loading && (
            <div className="typing-indicator animate-fadeIn">
              <div className="typing-avatar">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="8" r="4"/><path d="M6 20v-2a6 6 0 0 1 12 0v2"/>
                </svg>
              </div>
              <div className="typing-dots">
                <span /><span /><span />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <form id="chat-form" onSubmit={handleSend} className="chat-input-form">
            <textarea
              id="chat-input"
              ref={inputRef}
              className="chat-textarea"
              placeholder={keyConfigured ? 'Ask me about your HR details...' : 'Set your GROQ key above to start chatting'}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(e) }
              }}
              rows={1}
              disabled={!keyConfigured}
            />
            <button
              id="chat-send"
              type="submit"
              className="send-btn"
              disabled={!input.trim() || loading || !keyConfigured}
              aria-label="Send message"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </form>
          <p className="chat-hint">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  )
}
