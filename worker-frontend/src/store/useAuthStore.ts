import { create } from 'zustand'
import type { Session, User } from '@supabase/supabase-js'
import { supabase, type Profile } from '../lib/supabase'

interface AuthState {
  session: Session | null
  user: User | null
  profile: Profile | null
  loading: boolean
  initialize: () => () => void
  setProfile: (profile: Profile | null) => void
  signOut: () => Promise<void>
}

async function fetchProfile(userId: string): Promise<Profile | null> {
  const { data } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single()
  return data
}

export const useAuthStore = create<AuthState>((set) => ({
  session: null,
  user: null,
  profile: null,
  loading: true,

  initialize: () => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      set({ session, user: session?.user ?? null, loading: false })
      if (session?.user) {
        fetchProfile(session.user.id).then(profile => set({ profile }))
      }
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        set({ session, user: session?.user ?? null, loading: false })
        if (session?.user) {
          const profile = await fetchProfile(session.user.id)
          set({ profile })
        } else {
          set({ profile: null })
        }
      }
    )

    return () => subscription.unsubscribe()
  },

  setProfile: (profile) => set({ profile }),

  signOut: async () => {
    await supabase.auth.signOut()
    set({ session: null, user: null, profile: null })
  },
}))
