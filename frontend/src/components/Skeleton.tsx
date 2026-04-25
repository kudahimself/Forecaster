interface Props {
  rows?: number
  height?: number
}

export default function Skeleton({ rows = 5, height = 14 }: Props) {
  return (
    <div className="card" style={{ padding: 16 }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="skeleton skeleton-row"
          style={{ height, width: `${60 + ((i * 13) % 40)}%` }}
        />
      ))}
    </div>
  )
}
