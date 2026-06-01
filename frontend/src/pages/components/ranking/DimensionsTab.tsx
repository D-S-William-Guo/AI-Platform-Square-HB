import LoadingState from '../../../components/LoadingState'
import EmptyState from '../../../components/EmptyState'
import ErrorState from '../../../components/ErrorState'
import UiIcon from '../../../components/UiIcon'
import type { RankingDimension } from '../../../types'

interface DimensionsTabProps {
  dimensions: RankingDimension[]
  loading: boolean
  error: string | null
  onEdit: (dimension: RankingDimension) => void
  onDelete: (id: number, name: string) => void
  onNewDimension: () => void
}

export default function DimensionsTab({
  dimensions, loading, error,
  onEdit, onDelete, onNewDimension,
}: DimensionsTabProps) {
  return (
    <section className="dimension-section">
      <div className="section-header">
        <h2>评价维度管理</h2>
        <button className="primary-button" onClick={onNewDimension}>
          <span>+</span><span>新增维度</span>
        </button>
      </div>

      {loading ? (
        <LoadingState message="加载中..." />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <div className="dimension-list">
          {dimensions.length === 0 ? (
            <EmptyState
              icon="empty"
              title="暂无评价维度"
              description="请创建评价维度后，再将其配置到总应用榜或增长趋势榜。"
            />
          ) : (
            <table className="dimension-table">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>描述</th>
                  <th>计算方法</th>
                  <th>默认权重</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {dimensions.map(dimension => (
                  <tr key={dimension.id}>
                    <td className="dimension-name">{dimension.name}</td>
                    <td className="dimension-description">{dimension.description}</td>
                    <td className="dimension-calculation">
                      {dimension.calculation_method.length > 50
                        ? `${dimension.calculation_method.substring(0, 50)}...`
                        : dimension.calculation_method}
                    </td>
                    <td className="dimension-weight">{dimension.weight}</td>
                    <td className="dimension-status">
                      <span className={`status-badge ${dimension.is_active ? 'active' : 'inactive'}`}>
                        {dimension.is_active ? '启用' : '禁用'}
                      </span>
                    </td>
                    <td className="dimension-actions">
                      <button className="edit-button" onClick={() => onEdit(dimension)}>编辑</button>
                      <button className="delete-button" onClick={() => onDelete(dimension.id, dimension.name)}>删除</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </section>
  )
}
