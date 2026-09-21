import './ChatMessage.css'

function ToolSteps({ steps }) {
  if (!steps || steps.length === 0) return null
  return (
    <details className="tool-steps">
      <summary className="tool-steps-summary">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>
        </svg>
        {steps.length} agent step{steps.length > 1 ? 's' : ''}
      </summary>
      <div className="tool-steps-list">
        {steps.map((s, i) => (
          <div key={i} className="tool-step">
            <span className="tool-step-agent">{s.agent}</span>
            <span className="tool-step-arrow">→</span>
            <span className="tool-step-name">{s.tool}</span>
            {s.result?.error && (
              <span className="tool-step-err">⚠ {s.result.error}</span>
            )}
          </div>
        ))}
      </div>
    </details>
  )
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`msg-row ${isUser ? 'msg-row-user' : 'msg-row-bot'} animate-fadeIn`}>
      {!isUser && (
        <div className="msg-avatar bot-avatar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="8" r="4"/>
            <path d="M6 20v-2a6 6 0 0 1 12 0v2"/>
          </svg>
        </div>
      )}

      <div className={`msg-bubble ${isUser ? 'bubble-user' : 'bubble-bot'} ${message.error ? 'bubble-error' : ''}`}>
        <p className="msg-text">{message.content}</p>
        {!isUser && <ToolSteps steps={message.steps} />}
      </div>

      {isUser && (
        <div className="msg-avatar user-avatar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
      )}
    </div>
  )
}
