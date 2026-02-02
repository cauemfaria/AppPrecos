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
      
      // Check for updates every 60 minutes
      if (r) {
        setInterval(() => {
          r.update()
        }, 60 * 60 * 1000)
      }
    },
    onRegisterError(error: any) {
      // eslint-disable-next-line no-console
      console.log('SW registration error', error)
    },
  })

  const close = () => {
    setNeedRefresh(false)
  }

  // Also check for updates when the tab becomes visible again
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // Trigger update check via service worker registration
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
    <div className="fixed bottom-24 left-4 right-4 md:bottom-8 md:right-8 md:left-auto z-[100] animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="bg-white rounded-2xl shadow-2xl border border-blue-100 p-4 md:p-5 flex flex-col gap-3 max-w-sm ml-auto">
        <div className="flex items-start gap-3">
          <div className="bg-blue-50 p-2 rounded-xl">
            <RefreshCw className="w-5 h-5 text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-bold text-gray-900">
              Atualização Disponível
            </h3>
            <p className="text-xs text-gray-500 mt-1 leading-relaxed">
              Uma nova versão do AppPrecos está pronta. Deseja atualizar agora?
            </p>
          </div>
          <button 
            onClick={close}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex gap-2 mt-1">
          <button
            onClick={() => updateServiceWorker(true)}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2.5 px-4 rounded-xl transition-all shadow-sm active:scale-95"
          >
            Atualizar Agora
          </button>
          <button
            onClick={close}
            className="bg-gray-100 hover:bg-gray-200 text-gray-600 text-xs font-bold py-2.5 px-4 rounded-xl transition-all"
          >
            Depois
          </button>
        </div>
      </div>
    </div>
  )
}

export default ReloadPrompt
