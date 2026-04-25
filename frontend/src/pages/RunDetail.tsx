import { ArrowLeft } from 'lucide-react'
import { Fragment, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import EquityCurve from '../components/EquityCurve'
import PageHeader from '../components/PageHeader'
import PermHistogram from '../components/PermHistogram'
import Skeleton from '../components/Skeleton'
import { getPermMetrics, getPortfolioReturns, getRun } from '../lib/api'
import type {
  PermDistribution,
  PortfolioSeries,
  RunDetail as RunDetailType,
} from '../lib/api'

export default function RunDetail() {
  const { runId = '' } = useParams()
  const [run, setRun] = useState<RunDetailType | null>(null)
  const [series, setSeries] = useState<PortfolioSeries | null>(null)
  const [perm, setPerm] = useState<PermDistribution | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getRun(runId).then(setRun).catch((e) => setError(String(e)))
    getPortfolioReturns(runId).then(setSeries).catch(() => setSeries({ run_id: runId, points: [] }))
    getPermMetrics(runId).then(setPerm).catch(() => setPerm(null))
  }, [runId])

  if (error)
    return (
      <>
        <PageHeader title="Run" />
        <div className="page-body"><div className="error-box">Error: {error}</div></div>
      </>
    )

  if (!run)
    return (
      <>
        <PageHeader title="Run" />
        <div className="page-body"><Skeleton rows={8} /></div>
      </>
    )

  const paramEntries = Object.entries(run.params).sort(([a], [b]) => a.localeCompare(b))
  const metricEntries = Object.entries(run.metrics).sort(([a], [b]) => a.localeCompare(b))

  return (
    <>
      <PageHeader
        title={
          <span>
            <span className="id" style={{ color: 'var(--accent)' }}>{run.run_id.slice(0, 8)}</span>
            {run.name && (
              <>
                <span style={{ color: 'var(--text-muted)' }}> · </span>
                {run.name}
              </>
            )}
          </span>
        }
        subtitle={
          <>
            {run.experiment} · <span className={`pill status-${run.status}`}>{run.status}</span>
            {run.tags.map((t) => <span key={t} className="pill" style={{ marginLeft: 4 }}>{t}</span>)}
          </>
        }
        actions={
          <Link to="/" className="btn btn-ghost">
            <ArrowLeft size={13} />
            All runs
          </Link>
        }
      />

      <div className="page-body">
        <div className="stat-grid">
          <Stat label="run_id" value={run.run_id} />
          <Stat label="experiment" value={run.experiment} />
          <Stat label="git sha" value={run.git_sha || '—'} />
          <Stat label="started" value={fmtTs(run.started_at)} />
          <Stat label="finished" value={run.finished_at ? fmtTs(run.finished_at) : '—'} />
          <Stat
            label="status"
            value={<span className={`pill status-${run.status}`}>{run.status}</span>}
          />
        </div>

        {run.error && (
          <>
            <div className="card-title">error</div>
            <div className="error-box">{run.error}</div>
          </>
        )}

        <div className="row-2">
          <section>
            <div className="card-title">
              Cumulative portfolio return
              {series && (
                <span className="note">
                  {series.points.length > 0
                    ? `${series.points.length.toLocaleString()} daily returns`
                    : 'no backtest yet'}
                </span>
              )}
            </div>
            <div className="chart-card">
              <EquityCurve
                series={[
                  {
                    id: 'this',
                    label: run.name || run.run_id.slice(0, 8),
                    color: 'var(--accent)',
                    points: series?.points ?? [],
                  },
                ]}
                height={360}
              />
            </div>
          </section>

          {perm && (
            <section>
              <div className="card-title">
                Permutation distribution
                <span className="note">
                  baseline={perm.baseline_metric.toFixed(5)} · median_perm=
                  {perm.median_perm?.toFixed(5) ?? '—'} · p_two_sided=
                  {perm.p_two_sided?.toFixed(3) ?? '—'} · n={perm.n_valid}/{perm.n_permutations}
                </span>
              </div>
              <div className="chart-card">
                <PermHistogram dist={perm} height={360} />
              </div>
            </section>
          )}
        </div>

        <div className="row-2">
          <section>
            <div className="card-title">
              Params <span className="note">{paramEntries.length} entries</span>
            </div>
            <div className="kv-grid">
              {paramEntries.map(([k, v]) => (
                <Fragment key={k}>
                  <div className="k">{k}</div>
                  <div className="v">{formatValue(v)}</div>
                </Fragment>
              ))}
            </div>
          </section>

          <section>
            <div className="card-title">
              Metrics <span className="note">{metricEntries.length} entries</span>
            </div>
            <div className="kv-grid">
              {metricEntries.map(([k, v]) => (
                <Fragment key={k}>
                  <div className="k">{k}</div>
                  <div className="v">{typeof v === 'number' ? v.toPrecision(6) : String(v)}</div>
                </Fragment>
              ))}
            </div>
          </section>
        </div>

        {run.feature_importance.length > 0 && (
          <>
            <div className="card-title">
              Feature importance
              <span className="note">top {Math.min(20, run.feature_importance.length)}</span>
            </div>
            <div className="table-wrap">
              <table className="runs">
                <thead>
                  <tr>
                    <th className="num" style={{ width: 60 }}>rank</th>
                    <th>feature</th>
                    <th className="num">importance</th>
                    <th style={{ width: 200 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {run.feature_importance.slice(0, 20).map((fi) => {
                    const max = run.feature_importance[0].importance || 1
                    const pct = (fi.importance / max) * 100
                    return (
                      <tr key={fi.feature}>
                        <td className="num">{fi.rank}</td>
                        <td>{fi.feature}</td>
                        <td className="num">{fi.importance.toFixed(5)}</td>
                        <td>
                          <div
                            style={{
                              height: 8,
                              width: 160,
                              background: 'var(--bg-2)',
                              borderRadius: 2,
                            }}
                          >
                            <div
                              style={{
                                width: `${Math.abs(pct)}%`,
                                height: '100%',
                                background: 'var(--accent)',
                                borderRadius: 2,
                              }}
                            />
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}

        {run.artifacts.length > 0 && (
          <>
            <div className="card-title">Artifacts</div>
            <div className="table-wrap">
              <table className="runs">
                <thead>
                  <tr><th>name</th><th>kind</th><th>path</th><th className="num">bytes</th></tr>
                </thead>
                <tbody>
                  {run.artifacts.map((a) => (
                    <tr key={a.name}>
                      <td>{a.name}</td>
                      <td>{a.kind || '—'}</td>
                      <td className="id">{a.path}</td>
                      <td className="num">{a.size_bytes.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </>
  )
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="stat">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  )
}

function fmtTs(ts: string): string {
  return new Date(ts).toISOString().slice(0, 19).replace('T', ' ')
}

function formatValue(v: unknown): React.ReactNode {
  if (v === null || v === undefined) return '—'
  if (Array.isArray(v)) {
    if (v.length > 10) return <>[{v.slice(0, 6).join(', ')}, …{v.length} items]</>
    return <>[{v.join(', ')}]</>
  }
  if (typeof v === 'object') return JSON.stringify(v)
  if (typeof v === 'boolean') return v ? 'true' : 'false'
  return String(v)
}
