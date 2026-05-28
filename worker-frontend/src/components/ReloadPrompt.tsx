import { useEffect } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'

const ReloadPrompt = () => {
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

  useEffect(() => {
    if (needRefresh) {
      updateServiceWorker(true)
    }
  }, [needRefresh, updateServiceWorker])

  return null
}

export default ReloadPrompt
