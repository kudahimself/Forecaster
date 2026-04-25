import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { PermDistribution } from '../lib/api'

interface Props {
  dist: PermDistribution
  height?: number
  bins?: number
}

export default function PermHistogram({ dist, height = 260, bins = 24 }: Props) {
  const values = dist.metrics
  if (values.length === 0) {
    return (
      <div
        style={{
          height,
          border: '1px dashed var(--border)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--muted)',
          fontSize: 12,
        }}
      >
        no permutation metrics recorded
      </div>
    )
  }

  const min = Math.min(...values, dist.baseline_metric)
  const max = Math.max(...values, dist.baseline_metric)
  const span = max - min || 1
  const pad = span * 0.05
  const lo = min - pad
  const hi = max + pad
  const step = (hi - lo) / bins

  const histo = Array.from({ length: bins }, (_, i) => ({
    binStart: lo + i * step,
    binEnd: lo + (i + 1) * step,
    binMid: lo + (i + 0.5) * step,
    count: 0,
  }))
  for (const v of values) {
    let idx = Math.floor((v - lo) / step)
    if (idx >= bins) idx = bins - 1
    if (idx < 0) idx = 0
    histo[idx].count += 1
  }

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <BarChart data={histo} margin={{ top: 20, right: 20, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="2 4" stroke="var(--chart-grid)" />
          <XAxis
            dataKey="binMid"
            type="number"
            domain={[lo, hi]}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            tickFormatter={(v) => v.toFixed(4)}
            stroke="var(--chart-axis)"
          />
          <YAxis
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            stroke="var(--chart-axis)"
            allowDecimals={false}
            width={36}
          />
          <Tooltip
            cursor={{ fill: 'var(--bg-hover)' }}
            contentStyle={{
              background: 'var(--bg-2)',
              border: '1px solid var(--border-strong)',
              borderRadius: 6,
              fontSize: 12,
              padding: '8px 12px',
            }}
            labelStyle={{ color: 'var(--text-dim)', marginBottom: 4 }}
            itemStyle={{ color: 'var(--text)' }}
            labelFormatter={(v) => `bin mid ${Number(v).toFixed(5)}`}
            formatter={(v) => [Number(v), 'count']}
          />
          <Bar dataKey="count" fill="#4a5368" radius={[2, 2, 0, 0]} />
          <ReferenceLine
            x={dist.baseline_metric}
            stroke="#ef6363"
            strokeWidth={2}
            label={{ value: 'baseline', position: 'top', fill: '#ef6363', fontSize: 11, fontWeight: 600 }}
          />
          {dist.median_perm != null && (
            <ReferenceLine
              x={dist.median_perm}
              stroke="#6ea6ff"
              strokeDasharray="4 4"
              label={{ value: 'median', position: 'top', fill: '#6ea6ff', fontSize: 11 }}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
