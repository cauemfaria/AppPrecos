import { supabase } from './supabase'

export const CREDITS_PER_SCAN = 10

export async function fetchUserScanCount(userId: string): Promise<number> {
  const { count, error } = await supabase
    .from('processed_urls')
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
