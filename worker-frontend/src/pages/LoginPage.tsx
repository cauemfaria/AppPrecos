import { useState } from 'react'
import { supabase } from '../lib/supabase'
import { Mail, Lock, Eye, EyeOff, LogIn, UserPlus, Chrome } from 'lucide-react'

type Mode = 'signin' | 'signup'

export default function LoginPage() {
  const [mode, setMode] = useState<Mode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      if (mode === 'signin') {
        const { error: authError } = await supabase.auth.signInWithPassword({ email, password })
        if (authError) throw authError
      } else {
        const { error: authError } = await supabase.auth.signUp({ email, password })
        if (authError) throw authError
        setSuccess('Verifique seu e-mail para confirmar o cadastro!')
      }
    } catch (err: unknown) {
      const msg: string = err instanceof Error ? err.message : 'Erro desconhecido'
      if (msg.includes('Invalid login credentials')) setError('E-mail ou senha incorretos')
      else if (msg.includes('Email not confirmed')) setError('Confirme seu e-mail antes de entrar')
      else if (msg.includes('User already registered')) setError('E-mail já cadastrado — faça login')
      else if (msg.includes('Password should be at least')) setError('A senha deve ter pelo menos 6 caracteres')
      else setError(msg || 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogle = async () => {
    setGoogleLoading(true)
    setError(null)
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin },
    })
    setGoogleLoading(false)
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-6"
      style={{ backgroundColor: 'var(--color-background)', fontFamily: 'var(--font-body)' }}
    >
      {/* Logo / header */}
      <div className="mb-8 text-center">
        <div className="flex items-center justify-center gap-2 mb-1">
          <h1
            className="text-3xl font-bold"
            style={{ fontFamily: 'var(--font-heading)', color: 'var(--color-primary)' }}
          >
            economiX
          </h1>
          <span
            className="text-sm font-bold px-2 py-0.5 rounded-lg"
            style={{ backgroundColor: 'var(--color-cta)', color: 'white', fontFamily: 'var(--font-body)' }}
          >
            Funcionário
          </span>
        </div>
        <p className="text-sm mt-2" style={{ color: 'var(--color-text-muted)' }}>
          Faça login para registrar os preços dos produtos
        </p>
      </div>

      {/* Card */}
      <div
        className="w-full max-w-sm rounded-2xl p-6"
        style={{
          backgroundColor: 'var(--color-surface)',
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--color-border)',
        }}
      >
        {/* Mode toggle */}
        <div className="flex rounded-xl overflow-hidden mb-6" style={{ border: '1px solid var(--color-border)' }}>
          {(['signin', 'signup'] as Mode[]).map(m => (
            <button
              key={m}
              type="button"
              onClick={() => { setMode(m); setError(null); setSuccess(null) }}
              className="flex-1 py-2 text-sm font-semibold transition-colors duration-200"
              style={{
                backgroundColor: mode === m ? 'var(--color-primary)' : 'transparent',
                color: mode === m ? 'white' : 'var(--color-text-muted)',
                fontFamily: 'var(--font-body)',
              }}
            >
              {m === 'signin' ? 'Entrar' : 'Criar conta'}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl text-sm" style={{ backgroundColor: '#FEF2F2', color: '#DC2626' }}>
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 rounded-xl text-sm" style={{ backgroundColor: '#F0FDF4', color: '#16A34A' }}>
            {success}
          </div>
        )}

        <form onSubmit={handleEmailAuth} className="space-y-4">
          {/* Email input */}
          <div className="relative">
            <Mail
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
              style={{ color: 'var(--color-text-muted)' }}
            />
            <input
              type="email"
              placeholder="seu@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              className="w-full pl-10 pr-4 py-3 rounded-xl text-sm"
              style={{
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text)',
                fontFamily: 'var(--font-body)',
                outline: 'none',
                transition: 'border-color 200ms ease',
              }}
              onFocus={e => (e.target.style.borderColor = 'var(--color-primary)')}
              onBlur={e => (e.target.style.borderColor = 'var(--color-border)')}
            />
          </div>

          {/* Password input */}
          <div className="relative">
            <Lock
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
              style={{ color: 'var(--color-text-muted)' }}
            />
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Senha"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="w-full pl-10 pr-10 py-3 rounded-xl text-sm"
              style={{
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text)',
                fontFamily: 'var(--font-body)',
                outline: 'none',
                transition: 'border-color 200ms ease',
              }}
              onFocus={e => (e.target.style.borderColor = 'var(--color-primary)')}
              onBlur={e => (e.target.style.borderColor = 'var(--color-border)')}
            />
            <button
              type="button"
              onClick={() => setShowPassword(v => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2"
            >
              {showPassword
                ? <EyeOff className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
                : <Eye className="w-4 h-4" style={{ color: 'var(--color-text-muted)' }} />
              }
            </button>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all duration-200 active:scale-[0.98] disabled:opacity-60"
            style={{
              backgroundColor: 'var(--color-primary)',
              color: 'white',
              fontFamily: 'var(--font-body)',
              boxShadow: '0 4px 14px rgba(37,99,235,0.25)',
            }}
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : mode === 'signin' ? (
              <><LogIn className="w-4 h-4" /> Entrar</>
            ) : (
              <><UserPlus className="w-4 h-4" /> Criar conta</>
            )}
          </button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-3 my-4">
          <div className="flex-1 h-px" style={{ backgroundColor: 'var(--color-border)' }} />
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>ou</span>
          <div className="flex-1 h-px" style={{ backgroundColor: 'var(--color-border)' }} />
        </div>

        {/* Google */}
        <button
          type="button"
          onClick={handleGoogle}
          disabled={googleLoading}
          className="w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all duration-200 active:scale-[0.98] disabled:opacity-60"
          style={{
            border: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-surface)',
            color: 'var(--color-text)',
            fontFamily: 'var(--font-body)',
          }}
        >
          {googleLoading ? (
            <span className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
          ) : (
            <><Chrome className="w-4 h-4" /> Continuar com Google</>
          )}
        </button>
      </div>

      <p className="mt-6 text-xs text-center" style={{ color: 'var(--color-text-muted)' }}>
        Ao continuar, você concorda com os termos de uso.
      </p>
    </div>
  )
}
