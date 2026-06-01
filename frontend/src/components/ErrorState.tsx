import UiIcon from './UiIcon'

interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <section className="state-panel">
      <span className="state-icon"><UiIcon name="error" /></span>
      <span>{message}</span>
      {onRetry && (
        <button className="retry-button" onClick={onRetry}>
          重试
        </button>
      )}
    </section>
  )
}
