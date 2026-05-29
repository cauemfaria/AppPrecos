import { useEffect, useState } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'

interface ReloadPromptProps {
  /**
   * When true, a detected update is applied immediately (page reload) with no prompt.
   * Use on screens where the user has no in-progress work that could be lost — i.e. the
   * login page. When false (default), a dismissable bottom banner is shown instead.
   */
  autoUpdate?: boolean
}

const ReloadPrompt = ({ autoUpdate = false }: ReloadPromptProps) => {
  const [dismissed, setDismissed] = useState(false)

  const {
    needRefresh: [needRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r: ServiceWorkerRegistration | undefined) {
      // eslint-disable-next-line no-console
      console.log('SW Registered: ' + r)
      if (r) {
        setInterval(() => { r.update() }, 60 * 60 * 1000)
      }
    },
    onRegisterError(error: unknown) {
      // eslint-disable-next-line no-console
      console.log('SW registration error', error)
    },
  })

  // Trigger SW update check when the tab regains focus
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        navigator.serviceWorker.getRegistration().then(reg => {
          if (reg) reg.update()
        })
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  // Auto-reload when on the login page (autoUpdate=true) — safe, no user data at risk
  useEffect(() => {
    if (needRefresh && autoUpdate) {
      updateServiceWorker(true)
    }
  }, [needRefresh, autoUpdate, updateServiceWorker])

  // Reset dismissed state whenever a fresh update becomes available
  useEffect(() => {
    if (needRefresh) setDismissed(false)
  }, [needRefresh])

  // Nothing to render: no update, already auto-updating, or user dismissed
  if (!needRefresh || autoUpdate || dismissed) return null

  return (
    <div
      className="fixed bottom-4 left-4 right-4 z-50 rounded-2xl p-4 flex items-center justify-between gap-3"
      style={{
        backgroundColor: 'var(--color-surface)',
        boxShadow: 'var(--shadow-lg)',
        border: '1px solid var(--color-border)',
      }}
    >
      <div className="min-w-0">
        <p
          className="text-sm font-semibold truncate"
          style={{ color: 'var(--color-text)', fontFamily: 'var(--font-body)' }}
        >
          Nova versão disponível
        </p>
        <p
          className="text-xs mt-0.5"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-body)' }}
        >
          Atualize para obter as últimas melhorias.
        </p>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => setDismissed(true)}
          className="px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200"
          style={{
            border: '1px solid var(--color-border)',
            color: 'var(--color-text-muted)',
            backgroundColor: 'transparent',
            fontFamily: 'var(--font-body)',
          }}
        >
          Agora não
        </button>
        <button
          onClick={() => updateServiceWorker(true)}
          className="px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 active:scale-[0.97]"
          style={{
            backgroundColor: 'var(--color-primary)',
            color: 'white',
            fontFamily: 'var(--font-body)',
          }}
        >
          Atualizar
        </button>
      </div>
    </div>
  )
}

export default ReloadPrompt
