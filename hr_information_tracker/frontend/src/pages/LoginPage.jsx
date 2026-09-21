import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './LoginPage.css'

const API = 'http://localhost:8000'

export default function LoginPage() {
  const [employeeId, setEmployeeId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPass, setShowPass] = useState(false)
  const navigate = useNavigate()

  async function handleLogin(e) {
    e.preventDefault()
    if (!employeeId.trim() || !password.trim()) {
      setError('Please fill in all fields.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id: employeeId.trim(), password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail || 'Login failed. Please try again.')
        return
      }
      localStorage.setItem('hr_token', data.access_token)
      localStorage.setItem('hr_employee_id', data.employee_id)
      localStorage.setItem('hr_status', data.status)
      navigate('/chat')
    } catch {
      setError('Cannot reach the server. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const levelLabel = {
    level1: 'Staff',
    level2: 'Manager',
    level3: 'Boss',
  }

  return (
    <div className="login-root">
      {/* Decorative background blobs */}
      <div className="blob blob-1" />
      <div className="blob blob-2" />
      <div className="blob blob-3" />

      <div className="login-card animate-bounceIn">
        {/* Logo & Brand */}
        <div className="login-brand">
          <div className="login-logo">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="20" cy="20" r="20" fill="url(#grad)" />
              <path d="M14 27c0-3.314 2.686-6 6-6s6 2.686 6 6" stroke="#fff" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="20" cy="16" r="4" fill="#fff"/>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#2563eb"/>
                  <stop offset="1" stopColor="#f97316"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div>
            <h1 className="login-title">HR Portal</h1>
            <p className="login-subtitle">Employee Self-Service</p>
          </div>
        </div>

        <p className="login-welcome">Welcome back! Sign in to your account.</p>

        <form onSubmit={handleLogin} className="login-form" id="login-form" noValidate>
          {/* Employee ID */}
          <div className="field-group">
            <label htmlFor="employee-id" className="field-label">Employee ID</label>
            <div className="field-input-wrapper">
              <span className="field-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </span>
              <input
                id="employee-id"
                type="text"
                className="field-input"
                placeholder="e.g. EMP001"
                value={employeeId}
                onChange={e => setEmployeeId(e.target.value)}
                autoComplete="username"
              />
            </div>
          </div>

          {/* Password */}
          <div className="field-group">
            <label htmlFor="password" className="field-label">Password</label>
            <div className="field-input-wrapper">
              <span className="field-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </span>
              <input
                id="password"
                type={showPass ? 'text' : 'password'}
                className="field-input"
                placeholder="Enter your password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="field-toggle"
                onClick={() => setShowPass(p => !p)}
                aria-label={showPass ? 'Hide password' : 'Show password'}
              >
                {showPass ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="login-error animate-fadeIn" role="alert">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            id="login-submit"
            type="submit"
            className="login-btn"
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : 'Sign In'}
          </button>
        </form>

        {/* Level legend */}
        <div className="login-legend">
          <p className="legend-label">Access Levels</p>
          <div className="legend-badges">
            <span className="badge badge-level1">Level 1 — Staff</span>
            <span className="badge badge-level2">Level 2 — Manager</span>
            <span className="badge badge-level3">Level 3 — Boss</span>
          </div>
        </div>
      </div>
    </div>
  )
}
