import { useEffect, useState } from 'react'
import api from '../services/api'

export function useBackendConnection() {
  const [isConnected, setIsConnected] = useState(false)
  const [isChecking, setIsChecking] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    let retryCount = 0
    const maxRetries = 5
    const retryDelay = 1500

    const checkConnection = async () => {
      try {
        setIsChecking(true)
        setError(null)
        const response = await api.get('/health', { timeout: 5000 })
        if (isMounted && response.data?.connected === true) {
          setIsConnected(true)
          setIsChecking(false)
        }
      } catch (err: any) {
        if (!isMounted) return

        retryCount++
        const message = err.message || 'Servidor inacessível'

        if (retryCount < maxRetries) {
          setError(`${message} (tentativa ${retryCount}/${maxRetries})`)
          setTimeout(checkConnection, retryDelay)
        } else {
          setError(`Não foi possível conectar ao servidor. Verifique sua conexão e recarregue a página.`)
          setIsChecking(false)
        }
      }
    }

    checkConnection()

    return () => {
      isMounted = false
    }
  }, [])

  return { isConnected, isChecking, error }
}
