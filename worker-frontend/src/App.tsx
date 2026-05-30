import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import BarcodeScannerPage from './pages/BarcodeScannerPage'
import SettingsPage from './pages/SettingsPage'
import ReloadPrompt from './components/ReloadPrompt'
import LoginPage from './pages/LoginPage'
import ConnectionModal from './components/ConnectionModal'
import { useAuthStore } from './store/useAuthStore'
import { useBackendConnection } from './hooks/useBackendConnection'
import { ConnectionProvider } from './contexts/ConnectionContext'

function App() {
  const { session, loading, initialize } = useAuthStore()
  const { isConnected, hasConnectedOnce, isChecking, error, retry } = useBackendConnection()

  // [] is correct — initialize is a stable Zustand action ref, never changes
  useEffect(() => {
    const unsubscribe = initialize()
    return unsubscribe
  }, [])

  const renderContent = () => {
    // Step 1: Wait for Supabase to resolve the stored session (brief, ~100–300ms)
    if (loading) {
      return (
        <div
          className="min-h-screen flex items-center justify-center"
          style={{ backgroundColor: 'var(--color-background)' }}
        >
          <span
            className="w-10 h-10 border-4 rounded-full animate-spin"
            style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }}
          />
        </div>
      )
    }

    // Step 2: Not signed in — login page never blocked by backend connection
    if (!session) {
      return <LoginPage />
    }

    // Step 3: Signed in, backend not yet available for the first time
    if (!hasConnectedOnce && (!isConnected || isChecking)) {
      return <ConnectionModal isChecking={isChecking} error={error} onRetry={retry} />
    }

    // Step 4: Keep the app mounted after the first successful connection. If the
    // backend later becomes unavailable, show the reconnect UI as an overlay.
    return (
      <ConnectionProvider isConnected={isConnected}>
        <>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<HomePage />} />
                <Route path="scanner" element={<BarcodeScannerPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
          {(!isConnected || isChecking) && (
            <ConnectionModal isChecking={isChecking} error={error} onRetry={retry} />
          )}
        </>
      </ConnectionProvider>
    )
  }

  return (
    <>
      {/*
        ReloadPrompt is always at position 0 in the fragment — React never unmounts it
        across auth/connection state transitions. autoUpdate=true when there is no active
        session (login page), so updates apply immediately with no data-loss risk.
      */}
      <ReloadPrompt autoUpdate={!session} />
      {renderContent()}
    </>
  )
}

export default App
