import { ShieldCheck } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import EmptyState from '../components/EmptyState'
import PageHeader from '../components/PageHeader'
import Skeleton from '../components/Skeleton'
import { getDqRunDetail, getDqRuns } from '../lib/api'
import type { DqRunDetail, DqRunSummary } from '../lib/api'

export default function DqDashboard() {
  const [runs, setRuns] = useState<DqRunSummary[] | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<DqRunDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDqRuns()
      .then((rs) => {
        setRuns(rs)
        if (rs.length > 0) setSelectedId((prev) => prev ?? rs[0].run_id)
      })
      .catch((e) => setError(String(e)))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    setDetail(null)
    getDqRunDetail(selectedId).then(setDetail).catch((e) => setError(String(e)))
  }, [selectedId])

  const latest = useMemo(() => runs?.[0], [runs])

  return (
    <>
      <PageHeader
        title="Data quality"
        subtitle="Schema, freshness, null%, duplicates, suspicious returns, universe coverage — run by run."
      />
      <div className="page-body">
        {error && <div className="error-box">Error: {error}</div>}

        {!runs ? (
          <Skeleton rows={6} />
        ) : runs.length === 0 ? (
          <EmptyState
            icon={<ShieldCheck size={32} />}
            title="No DQ runs yet"
            description={<>Seed with <code>make validate</code>.</>}
          />
        ) : (
          <>
            {latest && (
              <>
                <div className="card-title">Latest run</div>
                <div className="stat-grid">
                  <Stat label="started" value={fmtTs(latest.started_at)} />
                  <Stat label="total checks" value={latest.summary.total ?? '—'} />
                  <Stat label="pass" valueClass="pass" value={latest.summary.pass ?? 0} />
                  <Stat label="warn" valueClass="warn" value={latest.summary.warn ?? 0} />
                  <Stat label="fail" valueClass="fail" value={latest.summary.fail ?? 0} />
                  <Stat label="universe" value={latest.summary.universe ?? '—'} />
                </div>
              </>
            )}

            <div className="card-title">
              All runs <span className="note">click a row to inspect</span>
            </div>
            <div className="table-wrap" style={{ marginBottom: 4 }}>
              <table className="runs">
                <thead>
                  <tr>
                    <th>run_id</th>
                    <th>started</th>
                    <th className="num">total</th>
                    <th className="num">pass</th>
                    <th className="num">warn</th>
                    <th className="num">fail</th>
                    <th>universe</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((r) => (
                    <tr
                      key={r.run_id}
                      onClick={() => setSelectedId(r.run_id)}
                      style={{
                        cursor: 'pointer',
                        background: r.run_id === selectedId ? 'var(--bg-hover-strong)' : undefined,
                      }}
                    >
                      <td className="id">{r.run_id.slice(0, 8)}</td>
                      <td>{fmtTs(r.started_at)}</td>
                      <td className="num">{r.summary.total ?? '—'}</td>
                      <td className="num" style={{ color: 'var(--pass)' }}>{r.summary.pass ?? 0}</td>
                      <td className="num" style={{ color: 'var(--warn)' }}>{r.summary.warn ?? 0}</td>
                      <td className="num" style={{ color: 'var(--fail)' }}>{r.summary.fail ?? 0}</td>
                      <td>{r.summary.universe ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {detail && (
              <>
                <div className="card-title">
                  Checks
                  <span className="note">{detail.run_id.slice(0, 8)}</span>
                </div>
                <div className="table-wrap">
                  <table className="runs">
                    <thead>
                      <tr>
                        <th>check</th>
                        <th>status</th>
                        <th className="num">checked</th>
                        <th className="num">failed</th>
                        <th>details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.checks.map((c) => (
                        <tr key={c.check_name}>
                          <td style={{ fontFamily: 'var(--mono)' }}>{c.check_name}</td>
                          <td><span className={`pill status-${statusClass(c.status)}`}>{c.status}</span></td>
                          <td className="num">{c.rows_checked.toLocaleString()}</td>
                          <td className="num">{c.rows_failed.toLocaleString()}</td>
                          <td style={{ maxWidth: 560, whiteSpace: 'normal', fontSize: 11, color: 'var(--text-muted)' }}>
                            {renderDetails(c.details)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </>
  )
}

function Stat({ label, value, valueClass }: { label: string; value: React.ReactNode; valueClass?: string }) {
  return (
    <div className="stat">
      <div className="label">{label}</div>
      <div className={'value ' + (valueClass ?? '')}>{value}</div>
    </div>
  )
}

function fmtTs(ts: string): string {
  return new Date(ts).toISOString().slice(0, 19).replace('T', ' ')
}

function statusClass(s: string): string {
  if (s === 'pass') return 'completed'
  if (s === 'fail') return 'failed'
  return 'running'
}

function renderDetails(d: Record<string, unknown>): React.ReactNode {
  if (!d || Object.keys(d).length === 0) return '—'
  const entries = Object.entries(d)
  return (
    <>
      {entries.slice(0, 3).map(([k, v]) => (
        <span key={k} style={{ marginRight: 12 }}>
          <b style={{ color: 'var(--text-dim)' }}>{k}</b>={formatVal(v)}
        </span>
      ))}
      {entries.length > 3 && <span>+{entries.length - 3} more</span>}
    </>
  )
}

function formatVal(v: unknown): string {
  if (Array.isArray(v)) {
    if (v.length > 3) return `[…${v.length} items]`
    return `[${v.join(', ')}]`
  }
  if (typeof v === 'object' && v !== null) {
    const s = JSON.stringify(v)
    return s.length > 60 ? s.slice(0, 60) + '…' : s
  }
  return String(v)
}
