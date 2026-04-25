import { ArrowLeft, Columns3 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import EmptyState from '../components/EmptyState'
import EquityCurve from '../components/EquityCurve'
import PageHeader from '../components/PageHeader'
import Skeleton from '../components/Skeleton'
import { getPortfolioReturns, getRun } from '../lib/api'
import type { PortfolioSeries, RunDetail } from '../lib/api'

const PALETTE = ['#6ea6ff', '#f0b344', '#3ddba0', '#ef6363', '#b783ff', '#46c9d4']

export default function Compare() {
  const [params] = useSearchParams()
  const ids = useMemo(() => (params.get('runs') ?? '').split(',').filter(Boolean), [params])

  const [runs, setRuns] = useState<RunDetail[]>([])
  const [series, setSeries] = useState<PortfolioSeries[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (ids.length === 0) return
    Promise.all(ids.map((id) => getRun(id)))
      .then(setRuns)
      .catch((e) => setError(String(e)))
    Promise.all(
      ids.map((id) => getPortfolioReturns(id).catch(() => ({ run_id: id, points: [] }))),
    ).then(setSeries)
  }, [ids.join(',')])

  if (ids.length === 0) {
    return (
      <>
        <PageHeader
          title="Compare runs"
          subtitle="Pick 2+ runs from the leaderboard and hit Compare."
        />
        <div className="page-body">
          <EmptyState
            icon={<Columns3 size={32} />}
            title="No runs selected"
            description={
              <>
                Go to <Link to="/">Runs</Link>, tick two or more, then click Compare.
              </>
            }
          />
        </div>
      </>
    )
  }

  if (error) {
    return (
      <>
        <PageHeader title="Compare runs" />
        <div className="page-body"><div className="error-box">Error: {error}</div></div>
      </>
    )
  }

  if (runs.length === 0) {
    return (
      <>
        <PageHeader title="Compare runs" />
        <div className="page-body"><Skeleton rows={8} /></div>
      </>
    )
  }

  const chartSeries = runs.map((r, i) => ({
    id: r.run_id,
    label: r.name || r.run_id.slice(0, 8),
    color: PALETTE[i % PALETTE.length],
    points: series.find((s) => s.run_id === r.run_id.replace(/-/g, ''))?.points ?? [],
  }))

  const allParamKeys = Array.from(
    new Set(runs.flatMap((r) => Object.keys(r.params))),
  )
    .filter((k) => k !== 'features')
    .sort()

  const paramDiffers = (k: string) => {
    const vals = runs.map((r) => JSON.stringify(r.params[k] ?? null))
    return new Set(vals).size > 1
  }

  const allMetricKeys = Array.from(
    new Set(runs.flatMap((r) => Object.keys(r.metrics))),
  ).sort()

  return (
    <>
      <PageHeader
        title={`Comparing ${runs.length} runs`}
        subtitle="Amber rows are params that differ between the selected runs."
        actions={
          <Link to="/" className="btn btn-ghost">
            <ArrowLeft size={13} />
            Back
          </Link>
        }
      />
      <div className="page-body">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 8 }}>
          {chartSeries.map((s) => (
            <span key={s.id} className="pill" style={{ borderColor: s.color, color: s.color }}>
              <span className="swatch" style={{ background: s.color }} />
              {s.label}
            </span>
          ))}
        </div>

        <div className="card-title">Cumulative portfolio return</div>
        <div className="chart-card">
          <EquityCurve series={chartSeries} height={380} />
        </div>

        <div className="card-title">
          Params <span className="note">{allParamKeys.length} keys · amber = differs</span>
        </div>
        <div className="table-wrap">
          <table className="runs">
            <thead>
              <tr>
                <th>param</th>
                {runs.map((r) => (
                  <th key={r.run_id} title={r.run_id}>{r.name || r.run_id.slice(0, 8)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allParamKeys.map((k) => {
                const diff = paramDiffers(k)
                return (
                  <tr key={k} style={diff ? { background: 'var(--warn-weak)' } : {}}>
                    <td className="id">{k}</td>
                    {runs.map((r) => (
                      <td key={r.run_id} className="num">{formatValue(r.params[k])}</td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        <div className="card-title">
          Metrics <span className="note">{allMetricKeys.length} keys</span>
        </div>
        <div className="table-wrap">
          <table className="runs">
            <thead>
              <tr>
                <th>metric</th>
                {runs.map((r) => (
                  <th key={r.run_id}>{r.name || r.run_id.slice(0, 8)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allMetricKeys.map((k) => (
                <tr key={k}>
                  <td className="id">{k}</td>
                  {runs.map((r) => (
                    <td key={r.run_id} className="num">
                      {r.metrics[k] !== undefined ? r.metrics[k].toPrecision(5) : '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}

function formatValue(v: unknown): React.ReactNode {
  if (v === null || v === undefined) return '—'
  if (Array.isArray(v)) {
    if (v.length > 6) return <>[…{v.length} items]</>
    return <>[{v.join(', ')}]</>
  }
  if (typeof v === 'object') return JSON.stringify(v)
  if (typeof v === 'boolean') return v ? 'true' : 'false'
  return String(v)
}
