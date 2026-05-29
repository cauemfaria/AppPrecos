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

function App() {
  const { session, loading, initialize } = useAuthStore()
  const { isConnected, isChecking, error } = useBackendConnection()

  useEffect(() => {
    const unsubscribe = initialize()
    return unsubscribe
  }, [initialize])

  // ReloadPrompt (PWA updates) always mounts regardless of connection/auth state

  if (loading || !isConnected || isChecking) {
    return (
      <>
        <ReloadPrompt />
        <ConnectionModal isConnected={isConnected && !loading} isChecking={isChecking || loading} error={error} />
      </>
    )
  }

  if (!session) {
    return (
      <>
        <ReloadPrompt />
        <LoginPage />
      </>
    )
  }

  return (
    <BrowserRouter>
      <ReloadPrompt />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="scanner" element={<BarcodeScannerPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
