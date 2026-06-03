import { create } from 'zustand'
import type { Session, User, AuthChangeEvent } from '@supabase/supabase-js'
import { supabase, getSessionSafe, type Profile } from '../lib/supabase'

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
    getSessionSafe().then((session) => {
      set({ session, user: session?.user ?? null, loading: false })
      if (session?.user) {
        const userId = session.user.id
        setTimeout(() => {
          fetchProfile(userId).then((profile) => set({ profile }))
        }, 0)
      }
    }).catch(() => {
      set({ loading: false })
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event: AuthChangeEvent, session: Session | null) => {
        set({ session, user: session?.user ?? null, loading: false })
        if (session?.user) {
          // Defer the profile fetch OUT of this callback. supabase-js holds an
          // internal auth lock while the callback runs; calling another supabase
          // method (the profiles query) synchronously here can deadlock the lock,
          // hanging every future getSession()/token refresh until a full reload.
          const userId = session.user.id
          setTimeout(() => {
            fetchProfile(userId).then((profile) => set({ profile }))
          }, 0)
        } else {
          set({ profile: null })
        }
      }
    )

    return () => subscription.unsubscribe()
  },

  setProfile: (profile: Profile | null) => set({ profile }),

  signOut: async () => {
    await supabase.auth.signOut()
    set({ session: null, user: null, profile: null })
  },
}))
