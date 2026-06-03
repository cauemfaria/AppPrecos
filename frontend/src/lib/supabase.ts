import { createClient, type Session } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('[supabase] Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})

/**
 * Reads the current session but is guaranteed to settle within `timeoutMs`.
 *
 * supabase-js guards token reads/refreshes with an internal lock that can stall
 * indefinitely (notably on mobile after the tab is frozen/resumed). Racing the
 * read against a timeout ensures callers — like the connection poller and the
 * request interceptor — can never hang forever waiting on the auth client.
 */
export async function getSessionSafe(timeoutMs = 5000): Promise<Session | null> {
  try {
    const result = await Promise.race([
      supabase.auth.getSession(),
      new Promise<{ data: { session: Session | null } }>((resolve) =>
        setTimeout(() => resolve({ data: { session: null } }), timeoutMs),
      ),
    ])
    return result.data.session
  } catch {
    return null
  }
}

export type Profile = {
  id: string
  email: string | null
  full_name: string | null
  avatar_url: string | null
  created_at: string
  updated_at: string
}
