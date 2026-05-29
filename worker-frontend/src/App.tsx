import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import BarcodeScannerPage from './pages/BarcodeScannerPage'
import SettingsPage from './pages/SettingsPage'
import ReloadPrompt from './components/ReloadPrompt'
import LoginPage from './pages/LoginPage'
import { useAuthStore } from './store/useAuthStore'

function App() {
  const { session, loading, initialize } = useAuthStore()

  useEffect(() => {
    const unsubscribe = initialize()
    return unsubscribe
  }, [initialize])

  if (loading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: 'var(--color-background)' }}
      >
        <div className="flex flex-col items-center gap-3">
          <span
            className="w-8 h-8 border-4 rounded-full animate-spin"
            style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }}
          />
          <p className="text-sm" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-body)' }}>
            Carregando...
          </p>
        </div>
      </div>
    )
  }

  if (!session) {
    return <LoginPage />
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
