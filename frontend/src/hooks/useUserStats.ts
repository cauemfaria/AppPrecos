import { useCallback, useEffect, useState } from 'react'
import { useAuthStore } from '../store/useAuthStore'
import { fetchUserScanCount, creditsFromScans } from '../lib/userStats'

export function useUserStats() {
  const user = useAuthStore((s) => s.user)
  const [totalScans, setTotalScans] = useState(0)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    if (!user?.id) {
      setTotalScans(0)
      setLoading(false)
      return
    }
    setLoading(true)
    const count = await fetchUserScanCount(user.id)
    setTotalScans(count)
    setLoading(false)
  }, [user?.id])

  useEffect(() => {
    refresh()
  }, [refresh])

  return {
    totalScans,
    credits: creditsFromScans(totalScans),
    loading,
    refresh,
  }
}
