import { BarChart3 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import EmptyState from '../components/EmptyState'
import PageHeader from '../components/PageHeader'
import Skeleton from '../components/Skeleton'
import { getFeatureImportance } from '../lib/api'
import type { FeatureAggRow } from '../lib/api'

type SortDir = 'asc' | 'desc'

interface Col {
  key: keyof FeatureAggRow
  label: string
  numeric?: boolean
  fmt?: (v: unknown) => string
}

const fmtNum = (d = 5) => (v: unknown) =>
  v == null ? '—' : (typeof v === 'number' ? v.toFixed(d) : String(v))

const COLS: Col[] = [
  { key: 'feature', label: 'feature' },
  { key: 'n_runs', label: 'n_runs', numeric: true, fmt: fmtNum(0) },
  { key: 'mean_importance', label: 'mean', numeric: true, fmt: fmtNum(5) },
  { key: 'median_importance', label: 'median', numeric: true, fmt: fmtNum(5) },
  { key: 'std_importance', label: 'std', numeric: true, fmt: fmtNum(5) },
  { key: 'mean_rank', label: 'avg rank', numeric: true, fmt: fmtNum(2) },
  { key: 'best_rank', label: 'best', numeric: true, fmt: fmtNum(0) },
  { key: 'worst_rank', label: 'worst', numeric: true, fmt: fmtNum(0) },
]

export default function FeatureImportance() {
  const [rows, setRows] = useState<FeatureAggRow[] | null>(null)
  const [nRuns, setNRuns] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<keyof FeatureAggRow>('mean_importance')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  useEffect(() => {
    getFeatureImportance()
      .then((d) => {
        setRows(d.features)
        setNRuns(d.n_total_runs)
      })
      .catch((e) => setError(String(e)))
  }, [])

  const maxMean = useMemo(() => {
    if (!rows) return 1
    let m = 0
    for (const r of rows) {
      if (r.mean_importance != null && Math.abs(r.mean_importance) > m)
        m = Math.abs(r.mean_importance)
    }
    return m || 1
  }, [rows])

  const sorted = useMemo(() => {
    if (!rows) return []
    const mult = sortDir === 'asc' ? 1 : -1
    return [...rows].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * mult
      return String(av).localeCompare(String(bv)) * mult
    })
  }, [rows, sortKey, sortDir])

  const toggleSort = (k: keyof FeatureAggRow) => {
    if (sortKey === k) setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    else { setSortKey(k); setSortDir('desc') }
  }

  return (
    <>
      <PageHeader
        title="Feature importance"
        subtitle="Aggregated across every RF run that reported feature importances. Answers the 'which features consistently help' question."
      />
      <div className="page-body">
        {error && <div className="error-box">Error: {error}</div>}

        {!rows ? (
          <Skeleton rows={6} height={16} />
        ) : rows.length === 0 ? (
          <EmptyState
            icon={<BarChart3 size={32} />}
            title="No feature importance data yet"
            description={<>Run an RF training with <code>make rf-run</code> to populate.</>}
          />
        ) : (
          <>
            <div className="filters">
              <span className="count-note">
                {rows.length} features · {nRuns} runs aggregated
              </span>
            </div>

            <div className="table-wrap">
              <table className="runs">
                <thead>
                  <tr>
                    {COLS.map((c) => (
                      <th
                        key={String(c.key)}
                        className={(c.numeric ? 'num ' : '') + (sortKey === c.key ? 'sorted' : '')}
                        onClick={() => toggleSort(c.key)}
                      >
                        {c.label}
                        {sortKey === c.key && (sortDir === 'asc' ? ' ↑' : ' ↓')}
                      </th>
                    ))}
                    <th style={{ width: 200, cursor: 'default' }}>weight</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((r) => (
                    <tr key={r.feature}>
                      {COLS.map((c) => (
                        <td key={String(c.key)} className={c.numeric ? 'num' : ''}>
                          {c.fmt ? c.fmt(r[c.key]) : String(r[c.key] ?? '—')}
                        </td>
                      ))}
                      <td style={{ width: 200 }}>
                        <Bar value={r.mean_importance} max={maxMean} />
                      </td>
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

function Bar({ value, max }: { value: number | null; max: number }) {
  if (value == null) return <span style={{ color: 'var(--text-muted)' }}>—</span>
  const pct = Math.min(100, (Math.abs(value) / max) * 100)
  const pos = value >= 0
  return (
    <div
      style={{
        height: 6,
        background: 'var(--bg-2)',
        borderRadius: 3,
        width: 180,
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${pct}%`,
          background: pos ? 'var(--accent)' : 'var(--warn)',
          borderRadius: 3,
        }}
      />
    </div>
  )
}
