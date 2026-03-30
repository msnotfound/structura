import { useState } from 'react'
import { Building2, Zap, Mail, Lock, User, Loader2 } from 'lucide-react'

interface LoginPageProps {
  onLogin: (token: string, user: { name: string; email: string }) => void
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [isRegister, setIsRegister] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login'
      const body = isRegister
        ? { name, email, password }
        : { email, password }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Authentication failed')
      }

      const data = await response.json()
      localStorage.setItem('auth_token', data.token)
      localStorage.setItem('auth_user', JSON.stringify(data.user))
      onLogin(data.token, data.user)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #050d1a 0%, #0c1632 50%, #071424 100%)',
      padding: '20px',
    }}>
      {/* Background effect */}
      <div style={{
        position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none',
      }}>
        <div style={{
          position: 'absolute', top: '10%', left: '15%',
          width: '400px', height: '400px',
          background: 'radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%)',
          borderRadius: '50%', filter: 'blur(60px)',
        }} />
        <div style={{
          position: 'absolute', bottom: '10%', right: '15%',
          width: '350px', height: '350px',
          background: 'radial-gradient(circle, rgba(34,211,238,0.06) 0%, transparent 70%)',
          borderRadius: '50%', filter: 'blur(60px)',
        }} />
      </div>

      <div style={{
        width: '100%', maxWidth: '420px',
        position: 'relative', zIndex: 1,
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            background: 'linear-gradient(135deg, #3b82f6, #22d3ee)',
            borderRadius: '16px', padding: '14px',
            boxShadow: '0 0 40px rgba(59,130,246,0.3)',
            marginBottom: '16px',
          }}>
            <Building2 style={{ width: '28px', height: '28px', color: 'white' }} />
          </div>
          <h1 style={{
            fontSize: '1.75rem', fontWeight: 800,
            background: 'linear-gradient(135deg, #3b82f6, #22d3ee)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '-0.03em',
          }}>
            STRUCTURA
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)', marginTop: '4px' }}>
            Autonomous Structural Intelligence
          </p>
        </div>

        {/* Auth Card */}
        <div style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '20px',
          padding: '32px 28px',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
        }}>
          <h2 style={{
            fontSize: '1.25rem', fontWeight: 700, color: 'white',
            marginBottom: '6px',
          }}>
            {isRegister ? 'Create Account' : 'Welcome Back'}
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.45)', marginBottom: '24px' }}>
            {isRegister ? 'Sign up to start analyzing floor plans' : 'Sign in to continue your analysis'}
          </p>

          <form onSubmit={handleSubmit}>
            {isRegister && (
              <div style={{ marginBottom: '14px' }}>
                <label style={{
                  display: 'block', fontSize: '0.75rem', fontWeight: 600,
                  color: 'rgba(255,255,255,0.6)', marginBottom: '6px',
                }}>Name</label>
                <div style={{ position: 'relative' }}>
                  <User style={{
                    position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)',
                    width: '16px', height: '16px', color: 'rgba(255,255,255,0.3)',
                  }} />
                  <input
                    type="text"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    required
                    placeholder="Your name"
                    style={{
                      width: '100%', padding: '10px 12px 10px 38px',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '10px', color: 'white',
                      fontSize: '0.88rem', outline: 'none',
                      transition: 'border-color 0.2s',
                    }}
                    onFocus={e => e.target.style.borderColor = 'rgba(59,130,246,0.5)'}
                    onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
                  />
                </div>
              </div>
            )}

            <div style={{ marginBottom: '14px' }}>
              <label style={{
                display: 'block', fontSize: '0.75rem', fontWeight: 600,
                color: 'rgba(255,255,255,0.6)', marginBottom: '6px',
              }}>Email</label>
              <div style={{ position: 'relative' }}>
                <Mail style={{
                  position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)',
                  width: '16px', height: '16px', color: 'rgba(255,255,255,0.3)',
                }} />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  placeholder="you@example.com"
                  style={{
                    width: '100%', padding: '10px 12px 10px 38px',
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '10px', color: 'white',
                    fontSize: '0.88rem', outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={e => e.target.style.borderColor = 'rgba(59,130,246,0.5)'}
                  onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
                />
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block', fontSize: '0.75rem', fontWeight: 600,
                color: 'rgba(255,255,255,0.6)', marginBottom: '6px',
              }}>Password</label>
              <div style={{ position: 'relative' }}>
                <Lock style={{
                  position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)',
                  width: '16px', height: '16px', color: 'rgba(255,255,255,0.3)',
                }} />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  placeholder="Min 6 characters"
                  minLength={6}
                  style={{
                    width: '100%', padding: '10px 12px 10px 38px',
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '10px', color: 'white',
                    fontSize: '0.88rem', outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={e => e.target.style.borderColor = 'rgba(59,130,246,0.5)'}
                  onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
                />
              </div>
            </div>

            {error && (
              <div style={{
                background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
                borderRadius: '8px', padding: '10px 12px', marginBottom: '14px',
                fontSize: '0.82rem', color: '#f87171',
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%', padding: '11px',
                background: loading ? 'rgba(59,130,246,0.3)' : 'linear-gradient(135deg, #3b82f6, #2563eb)',
                border: 'none', borderRadius: '10px',
                color: 'white', fontSize: '0.92rem', fontWeight: 700,
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                transition: 'all 0.2s ease',
                boxShadow: loading ? 'none' : '0 4px 16px rgba(59,130,246,0.3)',
              }}
            >
              {loading ? (
                <>
                  <Loader2 style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} />
                  {isRegister ? 'Creating account...' : 'Signing in...'}
                </>
              ) : (
                isRegister ? 'Create Account' : 'Sign In'
              )}
            </button>
          </form>

          <div style={{
            marginTop: '20px', textAlign: 'center',
            fontSize: '0.82rem', color: 'rgba(255,255,255,0.4)',
          }}>
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              onClick={() => { setIsRegister(!isRegister); setError('') }}
              style={{
                background: 'none', border: 'none', color: '#60a5fa',
                fontWeight: 600, cursor: 'pointer', fontSize: '0.82rem',
              }}
            >
              {isRegister ? 'Sign In' : 'Sign Up'}
            </button>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          textAlign: 'center', marginTop: '24px', display: 'flex',
          alignItems: 'center', justifyContent: 'center', gap: '6px',
          fontSize: '0.72rem', color: 'rgba(255,255,255,0.25)',
        }}>
          <Zap style={{ width: '12px', height: '12px', color: '#22d3ee' }} />
          Powered by Gemini 2.5 Flash + Cerebras Qwen 3 235B
        </div>
      </div>
    </div>
  )
}
