import UiIcon from './UiIcon'

interface EmptyStateProps {
  icon?: string
  title: string
  description?: string
  action?: {
    label: string
    to?: string
    onClick?: () => void
  }
}

export default function EmptyState({ icon = 'empty', title, description, action }: EmptyStateProps) {
  return (
    <section className="state-panel">
      <span className="state-icon"><UiIcon name={icon as never} /></span>
      <strong>{title}</strong>
      {description && <span>{description}</span>}
      {action && (
        action.to ? (
          <a href={action.to} className="state-action">{action.label}</a>
        ) : (
          <button className="state-action" onClick={action.onClick}>{action.label}</button>
        )
      )}
    </section>
  )
}
