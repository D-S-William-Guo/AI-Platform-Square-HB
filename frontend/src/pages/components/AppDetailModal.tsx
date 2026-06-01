import type { AppItem } from '../../types'
import { resolveMediaUrl } from '../../utils/media'
import Modal from '../../components/Modal'
import UiIcon from '../../components/UiIcon'
import { getGradient, monthlyCallsText, statusOptions, valueDimensionLabel } from '../homeUtils'

interface AppDetailModalProps {
  app: AppItem | null
  onClose: () => void
}

export default function AppDetailModal({ app, onClose }: AppDetailModalProps) {
  if (!app) return null

  return (
    <Modal open={true} onClose={onClose} title={app.name} subtitle={`${app.company || app.org}${app.department ? ` · ${app.department}` : ''}`}>
      <div className="modal-body">
        <div
          className="modal-cover"
          style={{ background: app.cover_image_url ? `url(${resolveMediaUrl(app.cover_image_url)}) center/cover` : getGradient(app.id) }}
        >
          <span className={`modal-status-badge ${app.status}`}>
            {statusOptions.find((x) => x.value === app.status)?.label}
          </span>
        </div>

        <div className="modal-tags">
          <span className="modal-tag primary">{app.category}</span>
          <span className="modal-tag">{valueDimensionLabel[app.effectiveness_type]}</span>
        </div>

        <div className="modal-section">
          <div className="modal-section-title">场景介绍</div>
          <p className="modal-content">{app.description}</p>
        </div>

        <div className="modal-metrics">
          <div className="modal-metric-item">
            <div className="modal-metric-icon"><UiIcon name="calls" /></div>
            <div className="modal-metric-label">月调用量</div>
            <div className="modal-metric-value">{monthlyCallsText(app)}</div>
          </div>
          <div className="modal-metric-item">
            <div className="modal-metric-icon"><UiIcon name="date" /></div>
            <div className="modal-metric-label">上线时间</div>
            <div className="modal-metric-value">{app.release_date}</div>
          </div>
        </div>

        <div className="modal-section">
          <div className="modal-section-title">基本信息</div>
          <div className="modal-info-grid">
            <div className="modal-info-item">
              <span className="modal-info-label">所属公司</span>
              <span className="modal-info-value">{app.company || app.org}</span>
            </div>
            <div className="modal-info-item">
              <span className="modal-info-label">所属部门</span>
              <span className="modal-info-value">{app.department || '未设置'}</span>
            </div>
            <div className="modal-info-item">
              <span className="modal-info-label">接入系统</span>
              <span className="modal-info-value">{app.target_system}</span>
            </div>
            <div className="modal-info-item">
              <span className="modal-info-label">适用人群</span>
              <span className="modal-info-value">{app.target_users}</span>
            </div>
            <div className="modal-info-item">
              <span className="modal-info-label">解决问题</span>
              <span className="modal-info-value">{app.problem_statement}</span>
            </div>
            <div className="modal-info-item">
              <span className="modal-info-label">接入难度</span>
              <span className="modal-info-value">{app.difficulty}</span>
            </div>
          </div>
        </div>

        <div className="modal-section">
          <div className="modal-section-title">成效评估</div>
          <div className="modal-effectiveness">
            <div className="modal-effectiveness-item">
              <span className="modal-effectiveness-label">成效类型</span>
              <span className="modal-effectiveness-value">{valueDimensionLabel[app.effectiveness_type]}</span>
            </div>
            <div className="modal-effectiveness-item">
              <span className="modal-effectiveness-label">指标评估</span>
              <span className="modal-effectiveness-value highlight">{app.effectiveness_metric}</span>
            </div>
          </div>
        </div>
      </div>

      {app.detail_doc_url && (
        <div className="modal-footer">
          <a href={resolveMediaUrl(app.detail_doc_url)} target="_blank" rel="noreferrer" className="modal-btn secondary">
            <UiIcon name="doc" />
            <span>{app.detail_doc_name || '详细文档'}</span>
          </a>
        </div>
      )}
    </Modal>
  )
}
