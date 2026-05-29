import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import QRScannerPage from './pages/QRScannerPage'
import MarketsPage from './pages/MarketsPage'
import ShoppingListPage from './pages/ShoppingListPage'
import SettingsPage from './pages/SettingsPage'
import QueueManager from './components/QueueManager'
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
  // ConnectionModal renders as an overlay so it never blocks SW update logic

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
      <QueueManager />
      <ReloadPrompt />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="scanner" element={<QRScannerPage />} />
          <Route path="markets" element={<MarketsPage />} />
          <Route path="shopping-list" element={<ShoppingListPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
