import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuthStore } from '../store/useAuthStore'
import {
  fetchUserScanCount,
  creditsFromScans,
  getCachedScanCount,
  setCachedScanCount,
  clearStatsCache,
} from '../lib/userStats'

export function useUserStats() {
  const user = useAuthStore((s) => s.user)
  const [totalScans, setTotalScans] = useState(() => {
    if (!user?.id) return 0
    return getCachedScanCount(user.id) ?? 0
  })
  const requestId = useRef(0)

  const refresh = useCallback(async () => {
    if (!user?.id) {
      clearStatsCache()
      setTotalScans(0)
      return
    }

    const id = ++requestId.current
    const count = await fetchUserScanCount(user.id)
    if (id !== requestId.current) return

    setCachedScanCount(user.id, count)
    setTotalScans(count)
  }, [user?.id])

  useEffect(() => {
    if (!user?.id) {
      clearStatsCache()
      setTotalScans(0)
      return
    }

    const cached = getCachedScanCount(user.id)
    if (cached !== null) setTotalScans(cached)

    refresh()
  }, [user?.id, refresh])

  return {
    totalScans,
    credits: creditsFromScans(totalScans),
    refresh,
  }
}
