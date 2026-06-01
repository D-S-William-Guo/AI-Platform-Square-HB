import Pagination from '../../../components/Pagination'
import LoadingState from '../../../components/LoadingState'
import EmptyState from '../../../components/EmptyState'
import ErrorState from '../../../components/ErrorState'
import UiIcon from '../../../components/UiIcon'
import type { AppItem } from '../../../types'
import type { AppRankingSettingItem } from '../../rankingUtils'

interface RankingConfig {
  id: string; name: string
}

interface AppSettingsTabProps {
  apps: AppItem[]
  appSettings: Record<number, AppRankingSettingItem[]>
  allRankingConfigs: RankingConfig[]
  appsPage: number
  appsPageSize: number
  appsTotal: number
  appsTotalPages: number
  appSettingsLoading: boolean
  loading: boolean
  error: string | null
  syncing: boolean
  syncMessage: string | null
  onSync: () => void
  onAddParticipation: (app: AppItem) => void
  onEditParticipation: (app: AppItem, setting: AppRankingSettingItem) => void
  onDeleteAppSetting: (appId: number, settingId: number) => void
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

export default function AppSettingsTab({
  apps, appSettings, allRankingConfigs,
  appsPage, appsPageSize, appsTotal, appsTotalPages,
  appSettingsLoading, loading, error,
  syncing, syncMessage,
  onSync, onAddParticipation, onEditParticipation, onDeleteAppSetting,
  onPageChange, onPageSizeChange,
}: AppSettingsTabProps) {
  return (
    <section className="app-settings-section">
      <div className="section-header">
        <h2>应用榜单参与管理</h2>
        <button className="primary-button" onClick={onSync} disabled={syncing}>
          {syncing ? <><UiIcon name="sync" /> 发布中...</> : <><UiIcon name="trial" /> 发布榜单</>}
        </button>
      </div>
      <p className="section-note">
        评分来源说明：榜单最终分数 = 各维度评分 × 维度权重 × 应用权重系数。维度评分可在"添加参与/编辑"弹窗中维护。
      </p>

      {syncMessage && (
        <div className={`sync-message ${syncMessage.includes('成功') ? 'success' : 'error'}`}>
          {syncMessage}
        </div>
      )}

      {loading || appSettingsLoading ? (
        <LoadingState message="加载中..." />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <div className="app-settings-list">
          {apps.length === 0 ? (
            <EmptyState
              icon="platform"
              title="暂无应用数据"
              description="申报审核通过或录入集团应用后，可在这里维护应用参与设置。"
            />
          ) : (
            <table className="app-settings-table">
              <thead>
                <tr>
                  <th>应用名称</th>
                  <th>所属公司</th>
                  <th>所属部门</th>
                  <th>参与的榜单</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {apps.map(app => {
                  const settings = appSettings[app.id] || []
                  return (
                    <tr key={app.id}>
                      <td className="app-name">{app.name}</td>
                      <td className="app-org">{app.company || app.org}</td>
                      <td>{app.department || '未设置'}</td>
                      <td className="app-participation">
                        {settings.length === 0 ? (
                          <span className="no-participation">未参与任何榜单</span>
                        ) : (
                          <div className="participation-tags">
                            {settings.map(setting => {
                              const config = allRankingConfigs.find(c => c.id === setting.ranking_config_id)
                              return (
                                <span
                                  key={setting.id}
                                  className={`participation-tag ${setting.is_enabled ? 'enabled' : 'disabled'}`}
                                >
                                  {config?.name || setting.ranking_config_id}
                                  {setting.weight_factor !== 1.0 && ` (×${setting.weight_factor})`}
                                  <button className="remove-tag" onClick={() => onDeleteAppSetting(app.id, setting.id)}>×</button>
                                </span>
                              )
                            })}
                          </div>
                        )}
                      </td>
                      <td className="app-actions">
                        <button className="edit-button" onClick={() => onAddParticipation(app)}>添加参与</button>
                        {settings.map(setting => (
                          <button key={setting.id} className="edit-button secondary" onClick={() => onEditParticipation(app, setting)}>编辑</button>
                        ))}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
          <Pagination
            page={appsPage} pageSize={appsPageSize} total={appsTotal} totalPages={appsTotalPages}
            disabled={appSettingsLoading} onPageChange={onPageChange}
            onPageSizeChange={(nextPageSize) => { onPageChange(1); onPageSizeChange(nextPageSize) }}
          />
        </div>
      )}
    </section>
  )
}
