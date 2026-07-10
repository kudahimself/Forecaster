import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './App.css'
import Sidebar from './components/Sidebar'
import Compare from './pages/Compare'
import DqDashboard from './pages/DqDashboard'
import FeatureImportance from './pages/FeatureImportance'
import IngestStatus from './pages/IngestStatus'
import Leaderboard from './pages/Leaderboard'
import RunDetail from './pages/RunDetail'
import Schedules from './pages/Schedules'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Sidebar />
        <div className="main">
          <Routes>
            <Route path="/" element={<Leaderboard />} />
            <Route path="/runs/:runId" element={<RunDetail />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/features" element={<FeatureImportance />} />
            <Route path="/dq" element={<DqDashboard />} />
            <Route path="/ingest" element={<IngestStatus />} />
            <Route path="/schedules" element={<Schedules />} />
            <Route
              path="*"
              element={
                <div style={{ padding: 48, color: 'var(--text-muted)' }}>Not found.</div>
              }
            />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}
