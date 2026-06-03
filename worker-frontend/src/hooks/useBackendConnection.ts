import { useCallback, useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { getSessionSafe } from '../lib/supabase'
import { useAuthStore } from '../store/useAuthStore'
import { verifyBackendReady } from '../services/api'

// Plain instance — no auth interceptors so the health check works before any session exists.
const healthApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://appprecos.onrender.com/api',
  timeout: 10_000,
})

// While disconnected, poll quickly so we unblock the instant the server wakes from sleep.
const RETRY_WHILE_DOWN_MS = 3_000
// While healthy, verify periodically in the background.
const VERIFY_WHILE_UP_MS = 25_000
// Mid-session, require this many consecutive failures before blocking the UI
// (avoids flicker on a single transient blip). The very first load blocks immediately.
const FAILURES_BEFORE_BLOCK = 2

export function useBackendConnection() {
  const [isConnected, setIsConnected] = useState(false)
  const [hasConnectedOnce, setHasConnectedOnce] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mountedRef = useRef(true)
  const inFlightRef = useRef(false)
  const failuresRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Mirror of isConnected for scheduling decisions without stale closures.
  const connectedRef = useRef(false)

  const clearTimer = () => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }

  // The single source of truth. Always reschedules itself, so the loop can
  // never silently die — recovery is guaranteed and fully automatic.
  const check = useCallback(async () => {
    if (!mountedRef.current || inFlightRef.current) return
    inFlightRef.current = true

    try {
      const res = await healthApi.get('/health')
      if (!mountedRef.current) return

      if (res.data?.connected === false) {
        throw new Error('Backend reported not connected')
      }

      // Health is OK — now probe the real authenticated API.
      const needsRealProbe = !connectedRef.current || failuresRef.current > 0
      if (needsRealProbe) {
        const { session: storeSession, loading: authLoading } = useAuthStore.getState()
        // Wait until auth bootstrap finishes so we don't false-negative on getSessionSafe.
        if (authLoading) return

        let session = storeSession
        if (!session) {
          session = await getSessionSafe()
        }
        if (!session) {
          // Health OK but session not yet available (or auth read stalled) —
          // reschedule without counting a failure so the loop keeps polling.
          return
        }
        await verifyBackendReady()
      }
      if (!mountedRef.current) return

      failuresRef.current = 0
      connectedRef.current = true
      setIsConnected(true)
      setHasConnectedOnce(true)
      setError(null)
    } catch (err: unknown) {
      if (!mountedRef.current) return

      failuresRef.current += 1
      const offline = typeof navigator !== 'undefined' && !navigator.onLine
      const timedOut = (err as { code?: string })?.code === 'ECONNABORTED'

      // Block on the very first load (never connected) or after repeated failures.
      if (!connectedRef.current || failuresRef.current >= FAILURES_BEFORE_BLOCK) {
        connectedRef.current = false
        setIsConnected(false)
        setError(
          offline
            ? 'Sem conexão com a internet. Aguardando reconexão...'
            : timedOut
              ? 'Servidor iniciando... Isso pode levar até 1 minuto.'
              : 'Conectando ao servidor... Isso pode levar até 1 minuto.',
        )
      }
    } finally {
      inFlightRef.current = false
      if (mountedRef.current) {
        clearTimer()
        // Poll fast while down or after any failure; slow only when fully healthy.
        const healthy = connectedRef.current && failuresRef.current === 0
        const delay = healthy ? VERIFY_WHILE_UP_MS : RETRY_WHILE_DOWN_MS
        timerRef.current = setTimeout(check, delay)
      }
    }
  }, [])

  // Force an immediate check (manual button, regained focus, back online).
  const retry = useCallback(() => {
    if (inFlightRef.current) return
    clearTimer()
    check()
  }, [check])

  useEffect(() => {
    mountedRef.current = true

    const onVisible = () => {
      if (document.visibilityState === 'visible') retry()
    }

    // Re-check the instant the user returns to the app or the network comes back.
    // This is what makes "open the app after Render slept" recover on its own,
    // without needing to leave and come back.
    document.addEventListener('visibilitychange', onVisible)
    window.addEventListener('focus', retry)
    window.addEventListener('online', retry)

    check()

    return () => {
      mountedRef.current = false
      clearTimer()
      document.removeEventListener('visibilitychange', onVisible)
      window.removeEventListener('focus', retry)
      window.removeEventListener('online', retry)
    }
  }, [check, retry])

  // isChecking stays true the whole time we are not connected, so the modal
  // shows a continuous loading state rather than flickering into an error view.
  return { isConnected, hasConnectedOnce, isChecking: !isConnected, error, retry }
}
