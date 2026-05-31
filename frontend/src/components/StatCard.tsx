interface StatCardProps {
  label: string
  value: string | number
  valueClassName?: string
  loading?: boolean
  error?: string | null
  onRetry?: () => void
}

export default function StatCard({
  label,
  value,
  valueClassName,
  loading = false,
  error = null,
  onRetry,
}: StatCardProps) {
  return (
    <div className="stat-item">
      {loading ? (
        <div className="loading-spinner"></div>
      ) : error ? (
        <>
          <span className="stat-value error">{error}</span>
          {onRetry && <button className="retry-button" onClick={onRetry}>重试</button>}
        </>
      ) : (
        <span className={`stat-value ${valueClassName || ''}`}>{value}</span>
      )}
      <span className="stat-label">{label}</span>
    </div>
  )
}
