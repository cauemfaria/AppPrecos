import { supabase } from './supabase'

export const CREDITS_PER_SCAN = 10

type StatsCache = { userId: string; totalScans: number }

let statsCache: StatsCache | null = null

export function getCachedScanCount(userId: string): number | null {
  if (statsCache?.userId === userId) return statsCache.totalScans
  return null
}

export function setCachedScanCount(userId: string, totalScans: number) {
  statsCache = { userId, totalScans }
}

export function clearStatsCache() {
  statsCache = null
}

export async function fetchUserScanCount(userId: string): Promise<number> {
  const { count, error } = await supabase
    .from('scanned_prices')
    .select('id', { count: 'exact', head: true })
    .eq('scanned_by', userId)

  if (error) {
    console.error('[userStats] failed to fetch scan count', error)
    return 0
  }
  return count ?? 0
}

export function creditsFromScans(scanCount: number): number {
  return scanCount * CREDITS_PER_SCAN
}
