import {
  Activity,
  BarChart3,
  Calendar,
  Columns3,
  Database,
  ShieldCheck,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

const NAV = [
  { to: '/', label: 'Runs', Icon: Activity, end: true },
  { to: '/compare', label: 'Compare', Icon: Columns3 },
  { to: '/features', label: 'Features', Icon: BarChart3 },
  { to: '/dq', label: 'Data quality', Icon: ShieldCheck },
  { to: '/ingest', label: 'Ingest', Icon: Database },
  { to: '/schedules', label: 'Schedules', Icon: Calendar },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <NavLink to="/">
          Forecaster
          <span className="sidebar-brand-sub">research tracker</span>
        </NavLink>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-heading">Workbench</div>
        <nav className="sidebar-nav">
          {NAV.map(({ to, label, Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              <Icon size={15} strokeWidth={2} />
              {label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="sidebar-footer">
        local · sqlite · dev
      </div>
    </aside>
  )
}
