import EmptyState from '../../../components/EmptyState'
import UiIcon from '../../../components/UiIcon'

interface AuditLogsTabProps {
  logs: Array<{
    id: number
    action: string
    ranking_config_id?: string
    payload_summary?: string
    actor?: string
    created_at: string
  }>
}

export default function AuditLogsTab({ logs }: AuditLogsTabProps) {
  return (
    <section className="logs-section">
      <div className="section-header">
        <h2>变更日志</h2>
      </div>
      <div className="logs-list">
        {logs.length === 0 ? (
          <EmptyState
            icon="history"
            title="暂无变更日志"
            description="完成榜单配置、应用参与、维度维护或发布后，这里会记录操作痕迹。"
          />
        ) : (
          <table className="logs-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>操作</th>
                <th>对象</th>
                <th>变更内容</th>
                <th>操作人</th>
              </tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <tr key={log.id}>
                  <td className="log-time">{new Date(log.created_at).toLocaleString()}</td>
                  <td className="log-action">
                    <span className={`action-badge ${
                      String(log.action || '').includes('created') ? 'create'
                        : String(log.action || '').includes('deleted') ? 'delete'
                        : 'update'
                    }`}>
                      {String(log.action || '').includes('created') ? '创建'
                        : String(log.action || '').includes('deleted') ? '删除'
                        : String(log.action || '').includes('sync') ? '同步'
                        : '更新'}
                    </span>
                  </td>
                  <td className="log-dimension">{log.ranking_config_id || '-'}</td>
                  <td className="log-changes">{log.payload_summary || '-'}</td>
                  <td className="log-operator">{log.actor || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}
