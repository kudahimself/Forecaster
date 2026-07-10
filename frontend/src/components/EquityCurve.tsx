import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { PortfolioPoint } from '../lib/api'

interface Props {
  series: { id: string; label: string; color: string; points: PortfolioPoint[] }[]
  height?: number
}

type MergedRow = { date: string; [runId: string]: number | string }

export default function EquityCurve({ series, height = 320 }: Props) {
  if (series.length === 0 || series.every((s) => s.points.length === 0)) {
    return <EmptyChart height={height} note="no portfolio returns for this run — run `portfolio_backtest`" />
  }

  // Merge multiple series on date.
  const byDate: Record<string, MergedRow> = {}
  for (const s of series) {
    for (const p of s.points) {
      if (!byDate[p.date]) byDate[p.date] = { date: p.date }
      byDate[p.date][s.id] = p.cum_return
    }
  }
  const data = Object.values(byDate).sort((a, b) => (a.date < b.date ? -1 : 1))

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="2 4" stroke="var(--chart-grid)" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            stroke="var(--chart-axis)"
            minTickGap={60}
          />
          <YAxis
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            stroke="var(--chart-axis)"
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            width={54}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-2)',
              border: '1px solid var(--border-strong)',
              borderRadius: 6,
              fontSize: 12,
              padding: '8px 12px',
            }}
            labelStyle={{ color: 'var(--text-dim)', marginBottom: 4 }}
            itemStyle={{ color: 'var(--text)' }}
            formatter={(v) => `${(Number(v) * 100).toFixed(2)}%`}
          />
          {series.length > 1 && (
            <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-dim)' }} />
          )}
          {series.map((s) => (
            <Line
              key={s.id}
              type="monotone"
              dataKey={s.id}
              name={s.label}
              stroke={s.color}
              dot={false}
              strokeWidth={2}
              isAnimationActive={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function EmptyChart({ height, note }: { height: number; note: string }) {
  return (
    <div
      style={{
        height,
        border: '1px dashed var(--border-strong)',
        borderRadius: 'var(--r-md)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-muted)',
        fontSize: 12,
      }}
    >
      {note}
    </div>
  )
}
