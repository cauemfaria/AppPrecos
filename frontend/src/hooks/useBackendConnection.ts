import { useCallback, useEffect, useRef, useState } from 'react'
import axios from 'axios'

// Plain instance — no auth interceptors so the health check works before any session exists
const healthApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://appprecos.onrender.com/api',
  timeout: 8000,
})

/**
 * Exponential backoff schedule for initial "fast" retries.
 * Total covered window: ~50s, which handles Render free-tier cold starts (30–60s).
 * Index 0 is the delay after the 1st failure, index 4 after the 5th.
 */
const FAST_BACKOFF_MS = [3_000, 5_000, 8_000, 13_000, 21_000]

/** After all fast retries are exhausted, poll every 30s indefinitely. */
const SLOW_RETRY_MS = 30_000

/** Once connected, run a silent background health check on this interval. */
const BACKGROUND_CHECK_MS = 60_000

export function useBackendConnection() {
  const [isConnected, setIsConnected] = useState(false)
  const [isChecking, setIsChecking] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const mountedRef = useRef(true)
  const attemptRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clearTimer = () => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }

  /**
   * Core check function.
   * @param background - When true, a successful check updates state silently; a failed
   *   check surfaces the error and restarts the fast-retry cycle from the beginning.
   *   When false (foreground), isChecking=true is set and progress messages are shown.
   */
  const checkConnection = useCallback(async (background = false) => {
    if (!mountedRef.current) return

    if (!background) {
      setIsChecking(true)
      // Keep the existing error message visible while retrying so the user
      // can see "reconnecting (N/5)..." rather than a blank spinner
    }

    try {
      const response = await healthApi.get('/health')

      if (!mountedRef.current) return

      if (response.data?.connected === true) {
        setIsConnected(true)
        setIsChecking(false)
        setError(null)
        attemptRef.current = 0
        // Schedule next silent background health check
        clearTimer()
        timerRef.current = setTimeout(() => checkConnection(true), BACKGROUND_CHECK_MS)
      }
    } catch (err: unknown) {
      if (!mountedRef.current) return

      if (background) {
        // Background check failed — surface the modal and restart fast retries
        setIsConnected(false)
        setIsChecking(false)
        setError('Conexão com o servidor perdida.')
        attemptRef.current = 0
        clearTimer()
        timerRef.current = setTimeout(() => checkConnection(false), FAST_BACKOFF_MS[0])
        return
      }

      // Foreground retry
      attemptRef.current++
      const isTimeout = (err as { code?: string })?.code === 'ECONNABORTED'
      const reason = isTimeout ? 'Tempo esgotado' : 'Servidor inacessível'

      if (attemptRef.current <= FAST_BACKOFF_MS.length) {
        const delay = FAST_BACKOFF_MS[attemptRef.current - 1]
        setError(`${reason} — reconectando (${attemptRef.current}/${FAST_BACKOFF_MS.length})...`)
        setIsChecking(false)
        clearTimer()
        timerRef.current = setTimeout(() => checkConnection(false), delay)
      } else {
        // Fast retries exhausted — keep trying slowly, indefinitely
        setError('Servidor demorou para responder. Tentando novamente em instantes...')
        setIsChecking(false)
        clearTimer()
        timerRef.current = setTimeout(() => checkConnection(false), SLOW_RETRY_MS)
      }
    }
  }, [])

  /** Manual retry: resets the attempt counter and fires immediately. */
  const retry = useCallback(() => {
    clearTimer()
    attemptRef.current = 0
    checkConnection(false)
  }, [checkConnection])

  useEffect(() => {
    mountedRef.current = true
    checkConnection(false)
    return () => {
      mountedRef.current = false
      clearTimer()
    }
  }, [])

  return { isConnected, isChecking, error, retry }
}
