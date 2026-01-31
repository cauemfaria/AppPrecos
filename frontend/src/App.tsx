import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ScannerPage from './pages/ScannerPage'
import MarketsPage from './pages/MarketsPage'
import ShoppingListPage from './pages/ShoppingListPage'
import SettingsPage from './pages/SettingsPage'
import QueueManager from './components/QueueManager'

function App() {
  return (
    <BrowserRouter>
      <QueueManager />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<ScannerPage />} />
          <Route path="markets" element={<MarketsPage />} />
          <Route path="shopping-list" element={<ShoppingListPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
