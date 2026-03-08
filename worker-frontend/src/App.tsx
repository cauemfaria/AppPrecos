import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import BarcodeScannerPage from './pages/BarcodeScannerPage'
import SettingsPage from './pages/SettingsPage'
import ReloadPrompt from './components/ReloadPrompt'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="scanner" element={<BarcodeScannerPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
      <ReloadPrompt />
    </BrowserRouter>
  )
}

export default App
