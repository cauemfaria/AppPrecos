import React, { useEffect } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'
import { RefreshCw, X } from 'lucide-react'

const ReloadPrompt: React.FC = () => {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r: ServiceWorkerRegistration | undefined) {
      // eslint-disable-next-line no-console
      console.log('SW Registered: ' + r)
      if (r) {
        setInterval(() => { r.update() }, 60 * 60 * 1000)
      }
    },
    onRegisterError(error: any) {
      // eslint-disable-next-line no-console
      console.log('SW registration error', error)
    },
  })

  const close = () => setNeedRefresh(false)

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

  if (!needRefresh) return null

  return (
    <div
      className="fixed left-4 right-4 md:right-6 md:left-auto z-[200] animate-in fade-in slide-in-from-bottom-4 duration-300"
      style={{ bottom: 'calc(96px + env(safe-area-inset-bottom, 0px))' }}
    >
      <div
        className="max-w-sm ml-auto rounded-2xl p-4 flex flex-col gap-3"
        style={{
          backgroundColor: 'var(--color-text)',
          boxShadow: '0 8px 30px rgba(0,0,0,0.2)',
          fontFamily: 'var(--font-body)',
        }}
      >
        <div className="flex items-start gap-3">
          <div
            className="flex items-center justify-center w-9 h-9 rounded-xl shrink-0"
            style={{ backgroundColor: 'rgba(249,115,22,0.15)' }}
          >
            <RefreshCw className="w-4 h-4" style={{ color: 'var(--color-cta)' }} />
          </div>
          <div className="flex-1">
            <h3
              className="text-sm font-bold text-white"
              style={{ fontFamily: 'var(--font-heading)' }}
            >
              Atualização Disponível
            </h3>
            <p className="text-xs mt-0.5 leading-relaxed" style={{ color: '#94A3B8' }}>
              Uma nova versão do EconomiX está pronta.
            </p>
          </div>
          <button
            onClick={close}
            className="flex items-center justify-center w-6 h-6 rounded-full cursor-pointer transition-all hover:opacity-70 shrink-0"
            style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}
            aria-label="Fechar"
          >
            <X size={14} className="text-white" />
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => updateServiceWorker(true)}
            className="flex-1 text-xs font-bold py-2.5 px-4 rounded-xl cursor-pointer transition-all active:scale-[0.98]"
            style={{
              backgroundColor: 'var(--color-cta)',
              color: 'white',
              fontFamily: 'var(--font-body)',
            }}
          >
            Atualizar
          </button>
          <button
            onClick={close}
            className="text-xs font-medium py-2.5 px-4 rounded-xl cursor-pointer transition-all"
            style={{
              backgroundColor: 'rgba(255,255,255,0.1)',
              color: '#CBD5E1',
              fontFamily: 'var(--font-body)',
            }}
          >
            Depois
          </button>
        </div>
      </div>
    </div>
  )
}

export default ReloadPrompt
