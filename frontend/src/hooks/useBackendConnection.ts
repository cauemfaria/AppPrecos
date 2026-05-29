import { useEffect, useState } from 'react'
import axios from 'axios'

// Plain instance with no auth interceptors — health check must work before any session exists
const healthApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://appprecos.onrender.com/api',
  timeout: 8000,
})

export function useBackendConnection() {
  const [isConnected, setIsConnected] = useState(false)
  const [isChecking, setIsChecking] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    let retryCount = 0
    const maxRetries = 5
    const retryDelay = 3000

    const checkConnection = async () => {
      try {
        setIsChecking(true)
        setError(null)
        const response = await healthApi.get('/health')
        if (isMounted && response.data?.connected === true) {
          setIsConnected(true)
          setIsChecking(false)
        }
      } catch (err: any) {
        if (!isMounted) return

        retryCount++
        const message = err.code === 'ECONNABORTED'
          ? 'Tempo esgotado'
          : 'Servidor inacessível'

        if (retryCount < maxRetries) {
          setError(`${message} — tentando novamente (${retryCount}/${maxRetries})`)
          setTimeout(checkConnection, retryDelay)
        } else {
          setError('Não foi possível conectar ao servidor. Verifique sua conexão e recarregue a página.')
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
