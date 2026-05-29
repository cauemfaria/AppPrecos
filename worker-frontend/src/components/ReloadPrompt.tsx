import { useEffect } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'

interface ReloadPromptProps {
  /**
   * When true, a detected update is applied immediately (page reload) with no prompt.
   * Use on screens where the user has no in-progress work that could be lost — i.e. the
   * login page. When false (default), a persistent top banner is shown instead.
   */
  autoUpdate?: boolean
}

const ReloadPrompt = ({ autoUpdate = false }: ReloadPromptProps) => {
  const {
    needRefresh: [needRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r: ServiceWorkerRegistration | undefined) {
      console.log('SW Registered: ' + r)
      if (r) {
        setInterval(() => { r.update() }, 60 * 60 * 1000)
      }
    },
    onRegisterError(error: unknown) {
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
      } else if (document.visibilityState === 'hidden' && needRefresh && !autoUpdate) {
        // App minimized/backgrounded and there's a pending update for an authenticated user.
        // Apply it silently so it's ready when they return.
        updateServiceWorker(true)
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [needRefresh, autoUpdate, updateServiceWorker])

  // Auto-reload when on the login page (autoUpdate=true) — safe, no user data at risk
  useEffect(() => {
    if (needRefresh && autoUpdate) {
      updateServiceWorker(true)
    }
  }, [needRefresh, autoUpdate, updateServiceWorker])

  // Nothing to render: no update or already auto-updating on login page
  if (!needRefresh || autoUpdate) return null

  // Show persistent top banner (like a push notification) when user is logged in
  return (
    <div
      className="fixed top-0 left-0 right-0 z-50 p-3 flex items-center justify-between gap-3"
      style={{
        backgroundColor: 'var(--color-primary)',
        boxShadow: 'var(--shadow-md)',
      }}
    >
      <div className="min-w-0 flex-1">
        <p
          className="text-sm font-semibold truncate"
          style={{ color: 'white', fontFamily: 'var(--font-body)' }}
        >
          Nova versão disponível
        </p>
        <p
          className="text-xs mt-0.5 truncate"
          style={{ color: 'rgba(255,255,255,0.8)', fontFamily: 'var(--font-body)' }}
        >
          Termine o que está fazendo e atualize
        </p>
      </div>

      <button
        onClick={() => updateServiceWorker(true)}
        className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 active:scale-[0.97]"
        style={{
          backgroundColor: 'rgba(255,255,255,0.2)',
          color: 'white',
          fontFamily: 'var(--font-body)',
          backdropFilter: 'blur(4px)',
        }}
      >
        Atualizar
      </button>
    </div>
  )
}

export default ReloadPrompt
