import { useState, useEffect } from 'react'
import type { RankingDimension } from '../types'
import { fetchRankingDimensions, createRankingDimension, updateRankingDimension, deleteRankingDimension, fetchRankingLogs, syncRankings, batchUpdateRankingParams } from '../api/client'

const RankingManagementPage = () => {
  const [dimensions, setDimensions] = useState<RankingDimension[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingDimension, setEditingDimension] = useState<RankingDimension | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    calculation_method: '',
    weight: 1.0,
    is_active: true
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [syncing, setSyncing] = useState(false)
  const [syncMessage, setSyncMessage] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'dimensions' | 'settings' | 'logs'>('dimensions')
  const [batchUpdateData, setBatchUpdateData] = useState({
    apps: [] as number[],
    ranking_weight: 1.0,
    ranking_enabled: true,
    ranking_tags: ''
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dimensionsData, logsData] = await Promise.all([
        fetchRankingDimensions(),
        fetchRankingLogs()
      ])
      setDimensions(dimensionsData)
      setLogs(logsData)
    } catch (err) {
      setError('加载数据失败')
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const validateForm = () => {
    const errors: Record<string, string> = {}
    if (!formData.name.trim()) {
      errors.name = '名称不能为空'
    }
    if (!formData.description.trim()) {
      errors.description = '描述不能为空'
    }
    if (!formData.calculation_method.trim()) {
      errors.calculation_method = '计算方法不能为空'
    }
    if (formData.weight < 0.1 || formData.weight > 10.0) {
      errors.weight = '权重必须在0.1到10.0之间'
    }
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleCreate = async () => {
    if (!validateForm()) return

    try {
      await createRankingDimension(formData)
      setShowCreateModal(false)
      resetForm()
      loadData()
    } catch (err) {
      setError('创建排行维度失败')
      console.error('Failed to create dimension:', err)
    }
  }

  const handleUpdate = async () => {
    if (!validateForm() || !editingDimension) return

    try {
      await updateRankingDimension(editingDimension.id, formData)
      setShowEditModal(false)
      resetForm()
      loadData()
    } catch (err) {
      setError('更新排行维度失败')
      console.error('Failed to update dimension:', err)
    }
  }

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`确定要删除排行维度 "${name}" 吗？`)) return

    try {
      await deleteRankingDimension(id)
      loadData()
    } catch (err) {
      setError('删除排行维度失败')
      console.error('Failed to delete dimension:', err)
    }
  }

  const handleEdit = (dimension: RankingDimension) => {
    setEditingDimension(dimension)
    setFormData({
      name: dimension.name,
      description: dimension.description,
      calculation_method: dimension.calculation_method,
      weight: dimension.weight,
      is_active: dimension.is_active
    })
    setShowEditModal(true)
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      calculation_method: '',
      weight: 1.0,
      is_active: true
    })
    setFormErrors({})
    setEditingDimension(null)
  }

  const handleSyncRankings = async () => {
    setSyncing(true)
    setSyncMessage(null)
    try {
      const result = await syncRankings()
      setSyncMessage(`同步成功！更新了 ${result.updated_count} 个应用的排行榜数据`)
      // 重新加载数据
      loadData()
    } catch (err) {
      console.error('同步失败:', err)
      setSyncMessage('同步失败，请重试')
    } finally {
      setSyncing(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const target = e.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    const { name, value, type } = target
    const checked = 'checked' in target ? target.checked : false
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseFloat(value) : value
    }))
    // Clear error when user starts typing
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  return (
    <div className="ranking-management-page">
      <header className="page-header">
        <h1>排行榜管理</h1>
        <p>配置排行维度、计算方法和规则，管理排行榜参数</p>
      </header>

      <div className="page-content">
        {/* 标签页导航 */}
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'dimensions' ? 'active' : ''}`}
            onClick={() => setActiveTab('dimensions')}
          >
            <span>📊</span>
            <span>排行维度管理</span>
          </button>
          <button 
            className={`tab-button ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <span>⚙️</span>
            <span>参数配置</span>
          </button>
          <button 
            className={`tab-button ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            <span>📋</span>
            <span>变更日志</span>
          </button>
        </div>

        {/* 排行维度管理标签页 */}
        {activeTab === 'dimensions' && (
          <section className="dimension-section">
            <div className="section-header">
              <h2>排行维度管理</h2>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button 
                  className="primary-button" 
                  onClick={handleSyncRankings}
                  disabled={syncing}
                >
                  {syncing ? (
                    <>
                      <span>🔄</span>
                      <span>同步中...</span>
                    </>
                  ) : (
                    <>
                      <span>🔄</span>
                      <span>同步排行榜数据</span>
                    </>
                  )}
                </button>
                <button className="primary-button" onClick={() => setShowCreateModal(true)}>
                  <span>+</span>
                  <span>新增排行维度</span>
                </button>
              </div>
            </div>
            {syncMessage && (
              <div className={`sync-message ${syncMessage.includes('成功') ? 'success' : 'error'}`}>
                {syncMessage}
              </div>
            )}

            {loading ? (
              <div className="loading">加载中...</div>
            ) : error ? (
              <div className="error-message">{error}</div>
            ) : (
              <div className="dimension-list">
                {dimensions.length === 0 ? (
                  <div className="empty-state">
                    <span>📊</span>
                    <p>暂无排行维度</p>
                    <p>点击上方按钮添加第一个排行维度</p>
                  </div>
                ) : (
                  <table className="dimension-table">
                    <thead>
                      <tr>
                        <th>名称</th>
                        <th>描述</th>
                        <th>计算方法</th>
                        <th>权重</th>
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
                            <div className="calculation-preview">
                              {dimension.calculation_method.length > 50
                                ? `${dimension.calculation_method.substring(0, 50)}...`
                                : dimension.calculation_method}
                            </div>
                          </td>
                          <td className="dimension-weight">{dimension.weight}</td>
                          <td className="dimension-status">
                            <span className={`status-badge ${dimension.is_active ? 'active' : 'inactive'}`}>
                              {dimension.is_active ? '启用' : '禁用'}
                            </span>
                          </td>
                          <td className="dimension-actions">
                            <button 
                              className="edit-button" 
                              onClick={() => handleEdit(dimension)}
                            >
                              编辑
                            </button>
                            <button 
                              className="delete-button" 
                              onClick={() => handleDelete(dimension.id, dimension.name)}
                            >
                              删除
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </section>
        )}

        {/* 参数配置标签页 */}
        {activeTab === 'settings' && (
          <section className="settings-section">
            <div className="section-header">
              <h2>参数配置</h2>
              <p>配置排行榜相关参数和规则</p>
            </div>

            <div className="settings-grid">
              <div className="settings-card">
                <h3>批量更新排行榜参数</h3>
                <form className="batch-update-form">
                  <div className="form-group">
                    <label htmlFor="app-ids">应用ID列表（逗号分隔）</label>
                    <input
                      type="text"
                      id="app-ids"
                      placeholder="请输入应用ID，多个ID用逗号分隔"
                      onChange={(e) => {
                        const ids = e.target.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
                        setBatchUpdateData(prev => ({ ...prev, apps: ids }))
                      }}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="ranking-weight">排行权重</label>
                    <input
                      type="number"
                      id="ranking-weight"
                      min="0.1"
                      max="10.0"
                      step="0.1"
                      value={batchUpdateData.ranking_weight}
                      onChange={(e) => setBatchUpdateData(prev => ({ ...prev, ranking_weight: parseFloat(e.target.value) || 1.0 }))}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="ranking-enabled">参与排行</label>
                    <input
                      type="checkbox"
                      id="ranking-enabled"
                      checked={batchUpdateData.ranking_enabled}
                      onChange={(e) => setBatchUpdateData(prev => ({ ...prev, ranking_enabled: e.target.checked }))}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="ranking-tags">排行标签</label>
                    <input
                      type="text"
                      id="ranking-tags"
                      placeholder="请输入标签，多个标签用逗号分隔"
                      value={batchUpdateData.ranking_tags}
                      onChange={(e) => setBatchUpdateData(prev => ({ ...prev, ranking_tags: e.target.value }))}
                    />
                  </div>
                  <button 
                    type="button"
                    className="primary-button"
                    onClick={async () => {
                      if (batchUpdateData.apps.length === 0) {
                        alert('请输入至少一个应用ID');
                        return;
                      }
                      try {
                        await batchUpdateRankingParams(batchUpdateData.apps, {
                          ranking_weight: batchUpdateData.ranking_weight,
                          ranking_enabled: batchUpdateData.ranking_enabled,
                          ranking_tags: batchUpdateData.ranking_tags
                        });
                        alert('批量更新成功');
                      } catch (error) {
                        alert('批量更新失败，请重试');
                        console.error('Batch update failed:', error);
                      }
                    }}
                  >
                    批量更新
                  </button>
                </form>
              </div>

              <div className="settings-card">
                <h3>排行榜规则设置</h3>
                <div className="rule-settings">
                  <div className="rule-item">
                    <h4>排名计算方式</h4>
                    <p>基于加权评分体系，综合考虑多个维度的得分</p>
                    <p><strong>综合得分 = Σ(各维度得分 × 权重)</strong></p>
                  </div>
                  <div className="rule-item">
                    <h4>数据同步频率</h4>
                    <p>建议每天同步一次排行榜数据，确保数据的及时性和准确性</p>
                  </div>
                  <div className="rule-item">
                    <h4>异常值处理</h4>
                    <p>对异常数据采用移动平均法进行平滑处理，确保排名的稳定性</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* 变更日志标签页 */}
        {activeTab === 'logs' && (
          <section className="logs-section">
            <h2>变更日志</h2>
            <div className="logs-list">
              {logs.length === 0 ? (
                <div className="empty-state">
                  <span>📋</span>
                  <p>暂无变更日志</p>
                </div>
              ) : (
                <table className="logs-table">
                  <thead>
                    <tr>
                      <th>时间</th>
                      <th>操作</th>
                      <th>维度名称</th>
                      <th>变更内容</th>
                      <th>操作人</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map(log => (
                      <tr key={log.id}>
                        <td className="log-time">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="log-action">
                          <span className={`action-badge ${log.action}`}>
                            {log.action === 'create' ? '创建' : log.action === 'update' ? '更新' : '删除'}
                          </span>
                        </td>
                        <td className="log-dimension">{log.dimension_name}</td>
                        <td className="log-changes">{log.changes}</td>
                        <td className="log-operator">{log.operator}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        )}
      </div>

      {/* 创建模态框 */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-container" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>新增排行维度</h3>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <form className="dimension-form">
                <div className="form-group">
                  <label htmlFor="name">维度名称 *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className={formErrors.name ? 'error' : ''}
                    placeholder="请输入排行维度名称"
                  />
                  {formErrors.name && <span className="error-text">{formErrors.name}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="description">维度描述 *</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    className={formErrors.description ? 'error' : ''}
                    placeholder="请输入排行维度描述"
                    rows={3}
                  />
                  {formErrors.description && <span className="error-text">{formErrors.description}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="calculation_method">计算方法 *</label>
                  <textarea
                    id="calculation_method"
                    name="calculation_method"
                    value={formData.calculation_method}
                    onChange={handleInputChange}
                    className={formErrors.calculation_method ? 'error' : ''}
                    placeholder="请输入排行维度计算方法"
                    rows={4}
                  />
                  {formErrors.calculation_method && <span className="error-text">{formErrors.calculation_method}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="weight">权重 *</label>
                  <input
                    type="number"
                    id="weight"
                    name="weight"
                    value={formData.weight}
                    onChange={handleInputChange}
                    className={formErrors.weight ? 'error' : ''}
                    min="0.1"
                    max="10.0"
                    step="0.1"
                    placeholder="请输入权重"
                  />
                  {formErrors.weight && <span className="error-text">{formErrors.weight}</span>}
                </div>

                <div className="form-group checkbox-group">
                  <input
                    type="checkbox"
                    id="is_active"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleInputChange}
                  />
                  <label htmlFor="is_active">启用此维度</label>
                </div>
              </form>
            </div>
            <div className="modal-footer">
              <button className="secondary-button" onClick={() => setShowCreateModal(false)}>
                取消
              </button>
              <button className="primary-button" onClick={handleCreate}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑模态框 */}
      {showEditModal && editingDimension && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-container" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>编辑排行维度</h3>
              <button className="modal-close" onClick={() => setShowEditModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <form className="dimension-form">
                <div className="form-group">
                  <label htmlFor="name">维度名称 *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className={formErrors.name ? 'error' : ''}
                    placeholder="请输入排行维度名称"
                  />
                  {formErrors.name && <span className="error-text">{formErrors.name}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="description">维度描述 *</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    className={formErrors.description ? 'error' : ''}
                    placeholder="请输入排行维度描述"
                    rows={3}
                  />
                  {formErrors.description && <span className="error-text">{formErrors.description}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="calculation_method">计算方法 *</label>
                  <textarea
                    id="calculation_method"
                    name="calculation_method"
                    value={formData.calculation_method}
                    onChange={handleInputChange}
                    className={formErrors.calculation_method ? 'error' : ''}
                    placeholder="请输入排行维度计算方法"
                    rows={4}
                  />
                  {formErrors.calculation_method && <span className="error-text">{formErrors.calculation_method}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="weight">权重 *</label>
                  <input
                    type="number"
                    id="weight"
                    name="weight"
                    value={formData.weight}
                    onChange={handleInputChange}
                    className={formErrors.weight ? 'error' : ''}
                    min="0.1"
                    max="10.0"
                    step="0.1"
                    placeholder="请输入权重"
                  />
                  {formErrors.weight && <span className="error-text">{formErrors.weight}</span>}
                </div>

                <div className="form-group checkbox-group">
                  <input
                    type="checkbox"
                    id="is_active"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleInputChange}
                  />
                  <label htmlFor="is_active">启用此维度</label>
                </div>
              </form>
            </div>
            <div className="modal-footer">
              <button className="secondary-button" onClick={() => setShowEditModal(false)}>
                取消
              </button>
              <button className="primary-button" onClick={handleUpdate}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RankingManagementPage