import type { AppItem } from '../../types'
import { resolveMediaUrl } from '../../utils/media'
import UiIcon from '../../components/UiIcon'
import { getGradient, monthlyCallsText, statusOptions } from '../homeUtils'

interface AppGridProps {
  apps: AppItem[]
  onAppClick: (app: AppItem) => void
}

export default function AppGrid({ apps, onAppClick }: AppGridProps) {
  return (
    <section className="grid">
      {apps.map((app) => (
        <article className="card" key={app.id} onClick={() => onAppClick(app)}>
          <div
            className="card-image"
            style={{ background: app.cover_image_url ? `url(${resolveMediaUrl(app.cover_image_url)}) center/cover` : getGradient(app.id) }}
          >
            <span className={`status-badge ${app.status}`}>
              {statusOptions.find((x) => x.value === app.status)?.label}
            </span>
          </div>
          <div className="card-content">
            <h3 className="card-title">{app.name}</h3>
            <div className="card-meta">
              <span className="card-org">{app.company || app.org}</span>
              {app.department ? (
                <>
                  <span>·</span>
                  <span>{app.department}</span>
                </>
              ) : null}
              <span>·</span>
              <span className="card-category">{app.category}</span>
            </div>
            <p className="card-desc">{app.description}</p>
            <div className="card-footer">
              <div className="card-metrics">
                <span><UiIcon name="calls" /> {monthlyCallsText(app)}</span>
                <span><UiIcon name="date" /> {app.release_date}</span>
              </div>
            </div>
          </div>
        </article>
      ))}
    </section>
  )
}
