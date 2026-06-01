import Pagination from '../../../components/Pagination'
import LoadingState from '../../../components/LoadingState'
import EmptyState from '../../../components/EmptyState'
import ErrorState from '../../../components/ErrorState'
import UiIcon from '../../../components/UiIcon'

interface RankingConfigRecord {
  id: string; name: string; description: string
  calculation_method: string; is_active: boolean; dimensions?: Array<{dim_id: number; weight: number}>
}

interface RankingConfigsTabProps {
  rankingConfigs: RankingConfigRecord[]
  loading: boolean
  configLoading: boolean
  error: string | null
  configPage: number
  configPageSize: number
  configTotal: number
  configTotalPages: number
  syncing: boolean
  syncMessage: string | null
  onSync: () => void
  onEdit: (config: RankingConfigRecord) => void
  onDelete: (id: string, name: string) => void
  onNewConfig: () => void
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

export default function RankingConfigsTab({
  rankingConfigs, loading, configLoading, error,
  configPage, configPageSize, configTotal, configTotalPages,
  syncing, syncMessage,
  onSync, onEdit, onDelete, onNewConfig,
  onPageChange, onPageSizeChange,
}: RankingConfigsTabProps) {
  return (
    <section className="config-section">
      <div className="section-header">
        <h2>榜单配置管理</h2>
        <button className="primary-button" onClick={onNewConfig}>
          <span>+</span><span>新增榜单</span>
        </button>
      </div>

      {syncMessage && (
        <div className={`sync-message ${syncMessage.includes('成功') ? 'success' : 'error'}`}>
          {syncMessage}
        </div>
      )}

      {loading || configLoading ? (
        <LoadingState message="加载中..." />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <div className="config-list">
          {rankingConfigs.length === 0 ? (
            <EmptyState
              icon="trophy"
              title="暂无榜单配置"
              description="请先新增总应用榜或增长趋势榜配置，再维护应用参与并发布榜单。"
            />
          ) : (
            <div className="config-cards">
              {rankingConfigs.map(config => {
                const dimCount = config.dimensions?.length || 0

                return (
                  <div key={config.id} className={`config-card ${config.is_active ? 'active' : 'inactive'}`}>
                    <div className="config-card-header">
                      <h3 className="config-card-title">
                        {config.id === 'excellent' ? <UiIcon name="trophy" /> : config.id === 'trend' ? <UiIcon name="trend" /> : <UiIcon name="medal" />}
                        {config.name}
                      </h3>
                      <span className={`config-status ${config.is_active ? 'active' : 'inactive'}`}>
                        {config.is_active ? '启用' : '停用'}
                      </span>
                    </div>
                    <p className="config-card-description">{config.description}</p>
                    <div className="config-card-meta">
                      <span>计算公式: {config.calculation_method === 'composite' ? '综合评分' : '增长率'}</span>
                      <span>参与维度: {dimCount} 个</span>
                    </div>
                    <div className="config-card-actions">
                      <button className="edit-button" onClick={() => onEdit(config)}>编辑</button>
                      <button className="sync-button" onClick={onSync} disabled={syncing}>
                        {syncing ? '同步中...' : '同步排名'}
                      </button>
                      <button className="delete-button" onClick={() => onDelete(config.id, config.name)}>删除</button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
          <Pagination
            page={configPage} pageSize={configPageSize} total={configTotal} totalPages={configTotalPages}
            disabled={configLoading} onPageChange={onPageChange}
            pageSizeOptions={[6, 12]}
            onPageSizeChange={(nextPageSize) => { onPageChange(1); onPageSizeChange(nextPageSize) }}
          />
        </div>
      )}
    </section>
  )
}
