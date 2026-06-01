import Pagination from '../../../components/Pagination'
import LoadingState from '../../../components/LoadingState'
import EmptyState from '../../../components/EmptyState'
import ErrorState from '../../../components/ErrorState'
import type { AppItem } from '../../../types'

interface AppManagementTabProps {
  adminApps: AppItem[]
  appManagementLoading: boolean
  loading: boolean
  error: string | null
  adminAppsPage: number
  adminAppsPageSize: number
  adminAppsTotal: number
  adminAppsTotalPages: number
  appManagementMessage: string | null
  manageSectionFilter: string
  manageStatusFilter: string
  manageCompanyFilter: string
  manageKeyword: string
  companyFilterOptions: string[]
  statusUpdatingAppId: number | null
  onFilterChange: (field: string, value: string) => void
  onUpdateAppStatus: (app: AppItem, nextStatus: 'available' | 'approval' | 'beta' | 'offline') => void
  onRefresh: () => void
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

export default function AppManagementTab({
  adminApps, appManagementLoading, loading, error,
  adminAppsPage, adminAppsPageSize, adminAppsTotal, adminAppsTotalPages,
  appManagementMessage,
  manageSectionFilter, manageStatusFilter, manageCompanyFilter, manageKeyword,
  companyFilterOptions, statusUpdatingAppId,
  onFilterChange, onUpdateAppStatus, onRefresh,
  onPageChange, onPageSizeChange,
}: AppManagementTabProps) {
  return (
    <section className="app-management-section">
      <div className="section-header">
        <h2>应用上下架管理</h2>
        <button className="secondary-button" onClick={onRefresh} disabled={loading}>刷新</button>
      </div>
      <p className="section-note">
        下架后应用不在首页展示；省内应用下架后将自动失去当前榜单参与资格（历史榜单保留）。
      </p>

      {appManagementMessage && (
        <div className="sync-message success">{appManagementMessage}</div>
      )}

      <div className="app-management-filters">
        <select value={manageSectionFilter} onChange={(e) => onFilterChange('section', e.target.value)}>
          <option value="all">全部分区</option>
          <option value="province">省内应用</option>
          <option value="group">集团应用</option>
        </select>
        <select value={manageStatusFilter} onChange={(e) => onFilterChange('status', e.target.value)}>
          <option value="all">全部状态</option>
          <option value="available">可用</option>
          <option value="approval">需申请</option>
          <option value="beta">试运行</option>
          <option value="offline">已下线</option>
        </select>
        <select value={manageCompanyFilter} onChange={(e) => onFilterChange('company', e.target.value)}>
          {companyFilterOptions.map((item) => (
            <option key={item} value={item}>{item === 'all' ? '全部公司' : item}</option>
          ))}
        </select>
        <input
          type="text"
          value={manageKeyword}
          onChange={(e) => onFilterChange('keyword', e.target.value)}
          placeholder="搜索应用名/公司/部门/分类"
        />
      </div>

      {loading || appManagementLoading ? (
        <LoadingState message="加载中..." />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <div className="app-management-list">
          {adminApps.length === 0 ? (
            <EmptyState
              icon="history"
              title="暂无匹配应用"
              description="请调整筛选条件，或先完成应用申报审核/集团应用录入。"
            />
          ) : (
            <table className="app-management-table">
              <thead>
                <tr>
                  <th>应用名称</th>
                  <th>分区</th>
                  <th>公司 / 部门</th>
                  <th>分类</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {adminApps.map((app) => (
                  <tr key={app.id}>
                    <td><div className="app-name">{app.name}</div></td>
                    <td>{app.section === 'province' ? '省内应用' : '集团应用'}</td>
                    <td>
                      <div>{app.company || app.org}</div>
                      <div className="app-org">{app.department || '未设置'}</div>
                    </td>
                    <td>{app.category}</td>
                    <td><span className={`status-chip ${app.status}`}>{app.status}</span></td>
                    <td>
                      {app.status === 'offline' ? (
                        <button
                          className="edit-button secondary"
                          disabled={statusUpdatingAppId === app.id}
                          onClick={() => onUpdateAppStatus(app, 'available')}
                        >
                          {statusUpdatingAppId === app.id ? '处理中...' : '重新上架'}
                        </button>
                      ) : (
                        <button
                          className="delete-button"
                          disabled={statusUpdatingAppId === app.id}
                          onClick={() => onUpdateAppStatus(app, 'offline')}
                        >
                          {statusUpdatingAppId === app.id ? '处理中...' : '下架'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <Pagination
            page={adminAppsPage} pageSize={adminAppsPageSize} total={adminAppsTotal} totalPages={adminAppsTotalPages}
            disabled={appManagementLoading} onPageChange={onPageChange}
            onPageSizeChange={(nextPageSize) => { onPageChange(1); onPageSizeChange(nextPageSize) }}
          />
        </div>
      )}
    </section>
  )
}
