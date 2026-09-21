import './Sidebar.css'

const QUICK_PROMPTS = [
  { label: '📋 My Details', text: 'Show me my HR details' },
  { label: '✏️ Update Address', text: 'I want to update my current address' },
  { label: '📞 Update Contact', text: 'I want to update my contact number' },
  { label: '👥 Staff List', text: 'Show me all staff under my supervision' },
  { label: '➕ Add Staff', text: 'I want to add a new staff member' },
]

const LEVEL_ICONS = {
  level1: '🟦',
  level2: '🟧',
  level3: '🟥',
}

export default function Sidebar({ user, open, onClose, onClear, onLogout, levelName }) {
  return (
    <>
      {/* Overlay for mobile */}
      {open && <div className="sidebar-overlay" onClick={onClose} />}

      <aside className={`sidebar ${open ? 'sidebar-visible' : ''}`} id="sidebar">
        {/* Brand */}
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" width="32" height="32">
              <circle cx="20" cy="20" r="20" fill="url(#sgrad)" />
              <path d="M14 27c0-3.314 2.686-6 6-6s6 2.686 6 6" stroke="#fff" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="20" cy="16" r="4" fill="#fff"/>
              <defs>
                <linearGradient id="sgrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#2563eb"/><stop offset="1" stopColor="#f97316"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div>
            <span className="sidebar-brand-name">HR Portal</span>
            <span className="sidebar-brand-sub">Employee Assistant</span>
          </div>
        </div>

        {/* Employee Info Card */}
        {user ? (
          <div className="employee-card" id="employee-card">
            <div className="employee-avatar">
              {user.name ? user.name[0].toUpperCase() : '?'}
            </div>
            <div className="employee-info">
              <p className="employee-name">{user.name || 'Employee'}</p>
              <p className="employee-id">{user.employee_id}</p>
              <div className={`badge badge-${user.status}`}>
                {LEVEL_ICONS[user.status]} {levelName[user.status] || user.status}
              </div>
            </div>
          </div>
        ) : (
          <div className="employee-card skeleton">
            <div className="skeleton-avatar" />
            <div className="skeleton-lines">
              <div className="skeleton-line" />
              <div className="skeleton-line short" />
            </div>
          </div>
        )}

        {/* Divider */}
        <div className="sidebar-divider" />

        {/* Quick actions */}
        <div className="sidebar-section">
          <p className="sidebar-section-label">Quick Actions</p>
          <div className="quick-prompts" id="quick-prompts">
            {QUICK_PROMPTS.map((p, i) => (
              <button
                key={i}
                id={`quick-${i}`}
                className="quick-prompt-btn"
                onClick={() => {
                  const textarea = document.getElementById('chat-input')
                  if (textarea) {
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set
                    nativeInputValueSetter.call(textarea, p.text)
                    textarea.dispatchEvent(new Event('input', { bubbles: true }))
                    textarea.focus()
                  }
                }}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="sidebar-divider" />

        {/* Access info */}
        {user && (
          <div className="sidebar-section">
            <p className="sidebar-section-label">Your Access</p>
            <div className="access-info">
              {user.status === 'level1' && (
                <p className="access-text">✅ View & update your own profile</p>
              )}
              {user.status === 'level2' && (
                <>
                  <p className="access-text">✅ View & update your own profile</p>
                  <p className="access-text">✅ View all Level 1 staff details</p>
                  <p className="access-text">✅ Add new Level 1 staff</p>
                </>
              )}
              {user.status === 'level3' && (
                <>
                  <p className="access-text">✅ View & update your own profile</p>
                  <p className="access-text">✅ View Level 1 & Level 2 details</p>
                  <p className="access-text">✅ Add Level 1 staff & Level 2 managers</p>
                </>
              )}
            </div>
          </div>
        )}

        {/* Spacer */}
        <div className="sidebar-spacer" />

        {/* Actions */}
        <div className="sidebar-footer">
          <button id="clear-chat" className="sidebar-action-btn clear-btn" onClick={onClear}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
              <path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
            </svg>
            Clear Chat
          </button>
          <button id="logout-btn" className="sidebar-action-btn logout-btn" onClick={onLogout}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Sign Out
          </button>
        </div>
      </aside>
    </>
  )
}
