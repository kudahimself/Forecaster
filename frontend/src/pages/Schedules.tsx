import { Calendar, Clock } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import EmptyState from '../components/EmptyState'
import PageHeader from '../components/PageHeader'
import Skeleton from '../components/Skeleton'
import { getSchedulerRuns } from '../lib/api'
import type { IngestHistoryRow } from '../lib/api'

export default function Schedules() {
  const [rows, setRows] = useState<IngestHistoryRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getSchedulerRuns().then(setRows).catch((e) => setError(String(e)))
  }, [])

  const byJob = useMemo(() => {
    if (!rows) return new Map<string, IngestHistoryRow[]>()
    const m = new Map<string, IngestHistoryRow[]>()
    for (const r of rows) {
      const arr = m.get(r.job_name) || []
      arr.push(r)
      m.set(r.job_name, arr)
    }
    return m
  }, [rows])

  const summary = useMemo(() => {
    if (!rows) return null
    const total = rows.length
    const pass = rows.filter((r) => r.status === 'completed').length
    const fail = rows.filter((r) => r.status === 'failed').length
    const running = rows.filter((r) => r.status === 'running').length
    const lastSuccess = rows.find((r) => r.status === 'completed')?.started_at ?? null
    return { total, pass, fail, running, lastSuccess }
  }, [rows])

  return (
    <>
      <PageHeader
        title="Schedules"
        subtitle="History of scheduled ingest jobs. Every execution leaves a row, good or bad."
      />
      <div className="page-body">
        {error && <div className="error-box">Error: {error}</div>}

        {!rows ? (
          <Skeleton rows={6} />
        ) : rows.length === 0 ? (
          <EmptyState
            icon={<Calendar size={32} />}
            title="No scheduled runs yet"
            description={
              <>
                Trigger one with{' '}
                <code>python manage.py run_scheduled_ingest --job all</code>.
              </>
            }
          />
        ) : (
          <>
            {summary && (
              <div className="stat-grid">
                <Stat label="total runs" value={summary.total} />
                <Stat label="completed" value={summary.pass} valueClass="pass" />
                <Stat label="failed" value={summary.fail} valueClass="fail" />
                <Stat label="running" value={summary.running} valueClass="warn" />
                <Stat
                  label="last success"
                  value={summary.lastSuccess ? fmtTs(summary.lastSuccess) : '—'}
                />
                <Stat label="jobs registered" value={byJob.size} />
              </div>
            )}

            {[...byJob.entries()].map(([job, jobRows]) => (
              <JobTable key={job} job={job} rows={jobRows} />
            ))}
          </>
        )}
      </div>
    </>
  )
}

function JobTable({ job, rows }: { job: string; rows: IngestHistoryRow[] }) {
  return (
    <>
      <div className="card-title">
        <Clock size={12} strokeWidth={2.5} style={{ marginRight: 4 }} />
        {job}
        <span className="note">{rows.length} runs</span>
      </div>
      <div className="table-wrap" style={{ marginBottom: 20 }}>
        <table className="runs">
          <thead>
            <tr>
              <th>run_id</th>
              <th>started</th>
              <th>finished</th>
              <th className="num">duration</th>
              <th>status</th>
              <th className="num">rows ingested</th>
              <th>details</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.run_id}>
                <td className="id">{r.run_id.slice(0, 8)}</td>
                <td>{fmtTs(r.started_at)}</td>
                <td>{r.finished_at ? fmtTs(r.finished_at) : '—'}</td>
                <td className="num">
                  {r.duration_seconds != null ? `${r.duration_seconds.toFixed(1)}s` : '—'}
                </td>
                <td>
                  <span className={`pill status-${statusClass(r.status)}`}>{r.status}</span>
                </td>
                <td className="num">{r.rows_ingested.toLocaleString()}</td>
                <td
                  style={{
                    maxWidth: 420,
                    whiteSpace: 'normal',
                    fontSize: 11,
                    color: 'var(--text-muted)',
                  }}
                >
                  {r.error ? (
                    <span style={{ color: 'var(--fail)' }}>{r.error.slice(0, 120)}</span>
                  ) : (
                    renderSummary(r.summary)
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function Stat({
  label,
  value,
  valueClass,
}: {
  label: string
  value: React.ReactNode
  valueClass?: string
}) {
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
  if (s === 'completed') return 'completed'
  if (s === 'failed') return 'failed'
  return 'running'
}

function renderSummary(s: Record<string, unknown>): React.ReactNode {
  if (!s || Object.keys(s).length === 0) return '—'
  const entries = Object.entries(s)
  return (
    <>
      {entries.slice(0, 4).map(([k, v]) => (
        <span key={k} style={{ marginRight: 10 }}>
          <b style={{ color: 'var(--text-dim)' }}>{k}</b>={String(v)}
        </span>
      ))}
    </>
  )
}
