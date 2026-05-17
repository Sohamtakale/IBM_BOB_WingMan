import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Onboarding from './components/Onboarding'
import Dashboard from './components/Dashboard'
import AutoPilot from './components/AutoPilot'
import CoPilot from './components/CoPilot'
import CoachReport from './components/CoachReport'

export default function App() {
  const hasProfile = !!localStorage.getItem('wingman_profile')

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/dashboard" element={hasProfile ? <Dashboard /> : <Navigate to="/onboarding" replace />} />
        <Route path="/autopilot" element={hasProfile ? <AutoPilot /> : <Navigate to="/onboarding" replace />} />
        <Route path="/copilot" element={hasProfile ? <CoPilot /> : <Navigate to="/onboarding" replace />} />
        <Route path="/coach/:callId" element={hasProfile ? <CoachReport /> : <Navigate to="/onboarding" replace />} />
        <Route path="*" element={<Navigate to={hasProfile ? '/dashboard' : '/onboarding'} replace />} />
      </Routes>
    </BrowserRouter>
  )
}
