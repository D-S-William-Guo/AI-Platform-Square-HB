import UiIcon from './UiIcon'

interface LoadingStateProps {
  message?: string
}

export default function LoadingState({ message = '加载中...' }: LoadingStateProps) {
  return (
    <section className="state-panel">
      <div className="loading-spinner"></div>
      <span>{message}</span>
    </section>
  )
}
