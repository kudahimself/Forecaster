import { Database } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import EmptyState from '../components/EmptyState'
import PageHeader from '../components/PageHeader'
import Skeleton from '../components/Skeleton'
import { getIngestStatus } from '../lib/api'
import type { IngestStatus as IngestStatusType } from '../lib/api'

export default function IngestStatusPage() {
  const [data, setData] = useState<IngestStatusType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'symbol' | 'last_date' | 'n_rows'>('symbol')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  useEffect(() => {
    getIngestStatus().then(setData).catch((e) => setError(String(e)))
  }, [])

  const stats = useMemo(() => {
    if (!data) return null
    const ps = data.symbols.per_symbol
    const lastIngest = ps.map((p) => p.last_ingest).filter((x): x is string => !!x).sort().at(-1) ?? null
    const latestCoverage = ps.map((p) => p.last_date).filter((x): x is string => !!x).sort().at(-1) ?? null
    return { lastIngest, latestCoverage }
  }, [data])

  const sorted = useMemo(() => {
    if (!data) return []
    const rows = [...data.symbols.per_symbol]
    const mult = sortDir === 'asc' ? 1 : -1
    rows.sort((a, b) => {
      const av = a[sortBy]
      const bv = b[sortBy]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * mult
      return String(av).localeCompare(String(bv)) * mult
    })
    return rows
  }, [data, sortBy, sortDir])

  const toggleSort = (key: 'symbol' | 'last_date' | 'n_rows') => {
    if (sortBy === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    else { setSortBy(key); setSortDir(key === 'symbol' ? 'asc' : 'desc') }
  }

  return (
    <>
      <PageHeader
        title="Ingest"
        subtitle="Warehouse freshness and per-symbol coverage pulled straight from raw_prices / raw_factors."
      />
      <div className="page-body">
        {error && <div className="error-box">Error: {error}</div>}

        {!data ? (
          <Skeleton rows={8} />
        ) : data.prices_total_rows === 0 ? (
          <EmptyState
            icon={<Database size={32} />}
            title="Empty warehouse"
            description={<>Populate with <code>make ingest</code> (full universe) or <code>make demo</code>.</>}
          />
        ) : (
          <>
            <div className="card-title">Freshness</div>
            <div className="stat-grid">
              <Stat label="symbols known" value={data.symbols.known_in_dim} />
              <Stat label="symbols ingested" value={data.symbols.ingested} />
              <Stat label="price rows" value={data.prices_total_rows.toLocaleString()} />
              <Stat label="factor rows" value={data.factors.n_rows.toLocaleString()} />
              <Stat label="latest price date" value={stats?.latestCoverage ?? '—'} />
              <Stat label="latest factor date" value={data.factors.last_date ?? '—'} />
              <Stat label="last price ingest" value={stats?.lastIngest ? fmtTs(stats.lastIngest) : '—'} />
              <Stat label="last factor ingest" value={data.factors.last_ingest ? fmtTs(data.factors.last_ingest) : '—'} />
            </div>

            <div className="card-title">
              Per-symbol coverage <span className="note">{sorted.length} symbols</span>
            </div>
            <div className="table-wrap">
              <table className="runs">
                <thead>
                  <tr>
                    <th onClick={() => toggleSort('symbol')} className={sortBy === 'symbol' ? 'sorted' : ''}>
                      symbol{sortBy === 'symbol' && (sortDir === 'asc' ? ' ↑' : ' ↓')}
                    </th>
                    <th>first_date</th>
                    <th onClick={() => toggleSort('last_date')} className={sortBy === 'last_date' ? 'sorted' : ''}>
                      last_date{sortBy === 'last_date' && (sortDir === 'asc' ? ' ↑' : ' ↓')}
                    </th>
                    <th className={'num ' + (sortBy === 'n_rows' ? 'sorted' : '')} onClick={() => toggleSort('n_rows')}>
                      n_rows{sortBy === 'n_rows' && (sortDir === 'asc' ? ' ↑' : ' ↓')}
                    </th>
                    <th>last_ingest</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((s) => (
                    <tr key={s.symbol}>
                      <td style={{ fontFamily: 'var(--mono)' }}>{s.symbol}</td>
                      <td>{s.first_date ?? '—'}</td>
                      <td>{s.last_date ?? '—'}</td>
                      <td className="num">{s.n_rows.toLocaleString()}</td>
                      <td>{s.last_ingest ? fmtTs(s.last_ingest) : '—'}</td>
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
