import type { ReactNode } from 'react'

interface Props {
  icon?: ReactNode
  title: string
  description?: ReactNode
}

export default function EmptyState({ icon, title, description }: Props) {
  return (
    <div className="empty-state">
      {icon && <div className="icon">{icon}</div>}
      <h3>{title}</h3>
      {description && <p>{description}</p>}
    </div>
  )
}
