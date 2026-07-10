import { Activity, Search, SlidersHorizontal } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import EmptyState from '../components/EmptyState'
import PageHeader from '../components/PageHeader'
import Skeleton from '../components/Skeleton'
import { listRuns } from '../lib/api'
import type { RunSummary } from '../lib/api'

type SortDir = 'asc' | 'desc'
type SortKey = string

interface Column {
  key: SortKey
  label: string
  get: (r: RunSummary) => unknown
  render: (r: RunSummary) => React.ReactNode
  numeric?: boolean
}

const fmt = (v: unknown, digits = 4): string => {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'number') {
    if (Number.isNaN(v)) return '—'
    return v.toFixed(digits)
  }
  return String(v)
}

const pctColor = (v: unknown): string | undefined => {
  if (typeof v !== 'number' || Number.isNaN(v)) return undefined
  if (v > 0) return 'var(--pass)'
  if (v < 0) return 'var(--fail)'
  return undefined
}

const COLUMNS: Column[] = [
  {
    key: 'run_id',
    label: 'run_id',
    get: (r) => r.run_id,
    render: (r) => (
      <Link to={`/runs/${r.run_id}`} className="id">
        {r.run_id.slice(0, 8)}
      </Link>
    ),
  },
  {
    key: 'experiment',
    label: 'experiment',
    get: (r) => r.experiment,
    render: (r) => r.experiment,
  },
  {
    key: 'name',
    label: 'name',
    get: (r) => r.name || '',
    render: (r) => r.name || <span style={{ color: 'var(--text-muted)' }}>—</span>,
  },
  {
    key: 'status',
    label: 'status',
    get: (r) => r.status,
    render: (r) => <span className={`pill status-${r.status}`}>{r.status}</span>,
  },
  {
    key: 'started_at',
    label: 'started',
    get: (r) => r.started_at,
    render: (r) => new Date(r.started_at).toISOString().slice(0, 16).replace('T', ' '),
  },
  {
    key: 'tags',
    label: 'tags',
    get: (r) => r.tags.join(','),
    render: (r) => (
      <>
        {r.tags.slice(0, 3).map((t) => (
          <span key={t} className="pill">{t}</span>
        ))}
      </>
    ),
  },
  {
    key: 'params.top_k',
    label: 'top_k',
    get: (r) => r.params.top_k,
    render: (r) => <>{fmt(r.params.top_k, 0)}</>,
    numeric: true,
  },
  {
    key: 'params.top_k_short',
    label: 'short_k',
    get: (r) => r.params.top_k_short,
    render: (r) => <>{fmt(r.params.top_k_short, 0)}</>,
    numeric: true,
  },
  {
    key: 'params.max_per_sector',
    label: 'max/sec',
    get: (r) => r.params.max_per_sector,
    render: (r) => <>{r.params.max_per_sector == null ? '—' : String(r.params.max_per_sector)}</>,
    numeric: true,
  },
  {
    key: 'metrics.realized_mean_avg',
    label: 'realized_mean',
    get: (r) => r.metrics.realized_mean_avg,
    render: (r) => (
      <span style={{ color: pctColor(r.metrics.realized_mean_avg) }}>
        {fmt(r.metrics.realized_mean_avg)}
      </span>
    ),
    numeric: true,
  },
  {
    key: 'metrics.portfolio_ann_sharpe',
    label: 'ann_sharpe',
    get: (r) => r.metrics.portfolio_ann_sharpe,
    render: (r) => (
      <span style={{ color: pctColor(r.metrics.portfolio_ann_sharpe) }}>
        {fmt(r.metrics.portfolio_ann_sharpe, 3)}
      </span>
    ),
    numeric: true,
  },
  {
    key: 'metrics.portfolio_cum_return',
    label: 'cum_return',
    get: (r) => r.metrics.portfolio_cum_return,
    render: (r) => (
      <span style={{ color: pctColor(r.metrics.portfolio_cum_return) }}>
        {fmt(r.metrics.portfolio_cum_return, 3)}
      </span>
    ),
    numeric: true,
  },
  {
    key: 'metrics.portfolio_max_drawdown',
    label: 'max_dd',
    get: (r) => r.metrics.portfolio_max_drawdown,
    render: (r) => (
      <span style={{ color: 'var(--fail)' }}>
        {fmt(r.metrics.portfolio_max_drawdown, 3)}
      </span>
    ),
    numeric: true,
  },
  {
    key: 'metrics.perm_p_two_sided',
    label: 'p_two_sided',
    get: (r) => r.metrics.perm_p_two_sided,
    render: (r) => {
      const p = r.metrics.perm_p_two_sided
      if (p === undefined) return <>—</>
      const color = p < 0.05 ? 'var(--pass)' : p < 0.2 ? 'var(--warn)' : 'var(--text-muted)'
      return <span style={{ color }}>{p.toFixed(3)}</span>
    },
    numeric: true,
  },
  {
    key: 'metrics.perm_n_valid',
    label: 'n_perms',
    get: (r) => r.metrics.perm_n_valid,
    render: (r) => <>{fmt(r.metrics.perm_n_valid, 0)}</>,
    numeric: true,
  },
]

export default function Leaderboard() {
  const [runs, setRuns] = useState<RunSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('started_at')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const navigate = useNavigate()

  useEffect(() => {
    listRuns().then(setRuns).catch((e) => setError(String(e)))
  }, [])

  const toggleSelected = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const compareSelected = () => {
    if (selected.size === 0) return
    navigate(`/compare?runs=${Array.from(selected).join(',')}`)
  }

  const filtered = useMemo(() => {
    if (!runs) return []
    const needle = filter.trim().toLowerCase()
    if (!needle) return runs
    return runs.filter((r) => {
      const hay = [r.run_id, r.experiment, r.name, ...r.tags].join(' ').toLowerCase()
      return hay.includes(needle)
    })
  }, [runs, filter])

  const sorted = useMemo(() => {
    const col = COLUMNS.find((c) => c.key === sortKey)
    if (!col) return filtered
    const mult = sortDir === 'asc' ? 1 : -1
    return [...filtered].sort((a, b) => {
      const av = col.get(a)
      const bv = col.get(b)
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * mult
      return String(av).localeCompare(String(bv)) * mult
    })
  }, [filtered, sortKey, sortDir])

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  return (
    <>
      <PageHeader
        title="Runs"
        subtitle="Every tracked experiment. Sort by any column. Tick two or more to compare."
      />
      <div className="page-body">
        {error && <div className="error-box">Error: {error}</div>}

        {runs && runs.length === 0 ? (
          <EmptyState
            icon={<Activity size={32} />}
            title="No runs yet"
            description={
              <>
                Fire off a run from a notebook or <code>make demo</code>{' '}
                to populate the tracker.
              </>
            }
          />
        ) : (
          <>
            <div className="filters">
              <div style={{ position: 'relative' }}>
                <Search
                  size={14}
                  style={{
                    position: 'absolute',
                    left: 10,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted)',
                    pointerEvents: 'none',
                  }}
                />
                <input
                  type="text"
                  placeholder="filter by id · experiment · name · tag"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  style={{ paddingLeft: 30 }}
                />
              </div>
              <span className="count-note">
                {runs ? `${sorted.length} of ${runs.length}` : '…'}
              </span>
              <button
                type="button"
                className="btn btn-primary btn-compare"
                onClick={compareSelected}
                disabled={selected.size < 2}
                title={selected.size < 2 ? 'Select at least 2 runs to compare' : undefined}
              >
                <SlidersHorizontal size={13} />
                Compare{selected.size > 0 ? ` (${selected.size})` : ''}
              </button>
            </div>

            {!runs ? (
              <Skeleton rows={6} height={16} />
            ) : (
              <div className="table-wrap">
                <table className="runs">
                  <thead>
                    <tr>
                      <th style={{ width: 32, cursor: 'default' }} />
                      {COLUMNS.map((c) => (
                        <th
                          key={c.key}
                          className={(c.numeric ? 'num ' : '') + (sortKey === c.key ? 'sorted' : '')}
                          onClick={() => toggleSort(c.key)}
                        >
                          {c.label}
                          {sortKey === c.key && (sortDir === 'asc' ? ' ↑' : ' ↓')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sorted.map((r) => (
                      <tr key={r.run_id}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selected.has(r.run_id)}
                            onChange={() => toggleSelected(r.run_id)}
                          />
                        </td>
                        {COLUMNS.map((c) => (
                          <td
                            key={c.key}
                            className={(c.numeric ? 'num ' : '') + (c.key === 'run_id' ? 'id' : '')}
                          >
                            {c.render(r)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}
