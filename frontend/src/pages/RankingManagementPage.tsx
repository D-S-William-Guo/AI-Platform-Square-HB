import { useState, useEffect } from 'react'
import type { RankingDimension, AppItem } from '../types'
import { 
  fetchRankingDimensions, 
  createRankingDimension, 
  updateRankingDimension, 
  deleteRankingDimension, 
  fetchRankingLogs, 
  syncRankings, 
  updateAppRankingParams,
  fetchApps,
  updateAppDimensionScore
} from '../api/client'

// 应用排行榜配置类型
interface AppRankingConfig {
  app_id: number
  app_name: string
  app_org: string
  section: 'group' | 'province'
  
  // 优秀应用榜配置
  excellent_enabled: boolean
  excellent_weight: number
  excellent_tags: string
  excellent_dimensions: number[]  // 参与评分的维度ID列表
  
  // 趋势榜配置
  trend_enabled: boolean
  trend_weight: number
  trend_tags: string
  trend_dimensions: number[]
  
  // 维度评分（可手动调整）
  dimension_scores: Record<number, number>  // dimension_id -> score
}

const RankingManagementPage = () => {
  const [dimensions, setDimensions] = useState<RankingDimension[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [apps, setApps] = useState<AppItem[]>([])
  const [appConfigs, setAppConfigs] = useState<AppRankingConfig[]>([])
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
  const [activeTab, setActiveTab] = useState<'dimensions' | 'app-config' | 'excellent' | 'trend' | 'logs'>('dimensions')
  const [selectedApp, setSelectedApp] = useState<AppRankingConfig | null>(null)
  const [showAppConfigModal, setShowAppConfigModal] = useState(false)
  const [configFilter, setConfigFilter] = useState<'all' | 'group' | 'province'>('all')
  const [searchKeyword, setSearchKeyword] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dimensionsData, logsData, appsData] = await Promise.all([
        fetchRankingDimensions(),
        fetchRankingLogs(),
        fetchApps()
      ])
      setDimensions(dimensionsData)
      setLogs(logsData)
      setApps(appsData)
      
      // 转换应用数据为配置格式（只包含省内应用）
      const configs: AppRankingConfig[] = appsData
        .filter(app => app.section === 'province')
        .map(app => ({
          app_id: app.id,
          app_name: app.name,
          app_org: app.org,
          section: app.section as 'group' | 'province',
          excellent_enabled: app.ranking_enabled ?? true,
          excellent_weight: app.ranking_weight ?? 1.0,
          excellent_tags: app.ranking_tags ?? '',
          excellent_dimensions: dimensionsData.filter(d => d.is_active).map(d => d.id),
          trend_enabled: app.ranking_enabled ?? true,
          trend_weight: app.ranking_weight ?? 1.0,
          trend_tags: app.ranking_tags ?? '',
          trend_dimensions: dimensionsData.filter(d => d.is_active).map(d => d.id),
          dimension_scores: {}
        }))
      setAppConfigs(configs)
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
      loadData()
    } catch (err) {
      console.error('同步失败:', err)
      setSyncMessage('同步失败，请重试')
    } finally {
      setSyncing(false)
    }
  }

  const handleSaveAppConfig = async (config: AppRankingConfig) => {
    try {
      // 保存优秀应用榜配置
      await updateAppRankingParams(config.app_id, {
        ranking_enabled: config.excellent_enabled,
        ranking_weight: config.excellent_weight,
        ranking_tags: config.excellent_tags
      })
      
      // 保存维度评分
      for (const [dimensionId, score] of Object.entries(config.dimension_scores)) {
        await updateAppDimensionScore(config.app_id, parseInt(dimensionId), score)
      }
      
      alert('配置保存成功！')
      setShowAppConfigModal(false)
      loadData()
    } catch (err) {
      alert('保存失败，请重试')
      console.error('Failed to save config:', err)
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
    if (formErrors[name]) {
      setFormErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  // 过滤应用配置
  const filteredConfigs = appConfigs.filter(config => {
    if (configFilter !== 'all' && config.section !== configFilter) return false
    if (searchKeyword && !config.app_name.toLowerCase().includes(searchKeyword.toLowerCase())) return false
    return true
  })

  // 渲染应用配置列表
  const renderAppConfigList = (rankingType: 'excellent' | 'trend') => {
    const isExcellent = rankingType === 'excellent'
    
    return (
      <section className="app-config-section">
        <div className="section-header">
          <h2>{isExcellent ? '优秀应用榜' : '趋势榜'} - 应用配置</h2>
          <div className="header-actions">
            <button 
              className="primary-button" 
              onClick={handleSyncRankings}
              disabled={syncing}
            >
              {syncing ? '🔄 同步中...' : '🔄 同步排行榜数据'}
            </button>
          </div>
        </div>
        
        {syncMessage && (
          <div className={`sync-message ${syncMessage.includes('成功') ? 'success' : 'error'}`}>
            {syncMessage}
          </div>
        )}

        {/* 筛选栏 */}
        <div className="filter-bar">
          <div className="filter-group">
            <span className="filter-label">应用类型：</span>
            <select 
              className="filter-select"
              value={configFilter}
              onChange={(e) => setConfigFilter(e.target.value as 'all' | 'group' | 'province')}
            >
              <option value="all">全部应用</option>
              <option value="group">集团应用</option>
              <option value="province">省内应用</option>
            </select>
          </div>
          <div className="filter-group">
            <span className="filter-label">搜索：</span>
            <input
              type="text"
              className="filter-input"
              placeholder="搜索应用名称..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
            />
          </div>
        </div>

        {/* 应用列表 */}
        <div className="app-config-list">
          {filteredConfigs.length === 0 ? (
            <div className="empty-state">
              <span>📱</span>
              <p>暂无应用数据</p>
            </div>
          ) : (
            <table className="app-config-table">
              <thead>
                <tr>
                  <th>应用名称</th>
                  <th>所属单位</th>
                  <th>类型</th>
                  <th>参与排行</th>
                  <th>排行权重</th>
                  <th>标签</th>
                  <th>参与维度</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredConfigs.map(config => (
                  <tr key={config.app_id}>
                    <td className="app-name">{config.app_name}</td>
                    <td className="app-org">{config.app_org}</td>
                    <td className="app-section">
                      <span className={`section-badge ${config.section}`}>
                        {config.section === 'group' ? '集团' : '省内'}
                      </span>
                    </td>
                    <td className="app-enabled">
                      <span className={`status-badge ${isExcellent ? config.excellent_enabled : config.trend_enabled ? 'active' : 'inactive'}`}>
                        {isExcellent ? (config.excellent_enabled ? '是' : '否') : (config.trend_enabled ? '是' : '否')}
                      </span>
                    </td>
                    <td className="app-weight">
                      {isExcellent ? config.excellent_weight : config.trend_weight}
                    </td>
                    <td className="app-tags">
                      <div className="tags-preview">
                        {(isExcellent ? config.excellent_tags : config.trend_tags)?.split(',').filter(Boolean).map((tag, idx) => (
                          <span key={idx} className="tag-badge">{tag.trim()}</span>
                        )) || '-'}
                      </div>
                    </td>
                    <td className="app-dimensions">
                      {(isExcellent ? config.excellent_dimensions : config.trend_dimensions)?.length || 0} 个维度
                    </td>
                    <td className="app-actions">
                      <button 
                        className="edit-button"
                        onClick={() => {
                          setSelectedApp(config)
                          setShowAppConfigModal(true)
                        }}
                      >
                        配置
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    )
  }

  return (
    <div className="page">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
        <div className="header-actions">
          <button className="primary" onClick={() => window.location.href = '/'}>
            <span>←</span>
            <span>返回首页</span>
          </button>
        </div>
      </header>

      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">排行榜管理</h1>
          <p className="page-subtitle">配置排行维度、管理应用榜单参数、调整维度评分</p>
        </div>

        <div className="page-content">
          {/* 标签页导航 */}
          <div className="tab-navigation">
            <button 
              className={`tab-button ${activeTab === 'dimensions' ? 'active' : ''}`}
              onClick={() => setActiveTab('dimensions')}
            >
              <span>📊</span>
              <span>排行维度</span>
            </button>
            <button 
              className={`tab-button ${activeTab === 'excellent' ? 'active' : ''}`}
              onClick={() => setActiveTab('excellent')}
            >
              <span>🏆</span>
              <span>优秀应用榜</span>
            </button>
            <button 
              className={`tab-button ${activeTab === 'trend' ? 'active' : ''}`}
              onClick={() => setActiveTab('trend')}
            >
              <span>📈</span>
              <span>趋势榜</span>
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
                <button className="primary-button" onClick={() => setShowCreateModal(true)}>
                  <span>+</span>
                  <span>新增维度</span>
                </button>
              </div>

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

          {/* 优秀应用榜配置 */}
          {activeTab === 'excellent' && renderAppConfigList('excellent')}

          {/* 趋势榜配置 */}
          {activeTab === 'trend' && renderAppConfigList('trend')}

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
      </div>

      {/* 创建维度模态框 */}
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

      {/* 编辑维度模态框 */}
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

      {/* 应用配置模态框 */}
      {showAppConfigModal && selectedApp && (
        <div className="modal-overlay" onClick={() => setShowAppConfigModal(false)}>
          <div className="modal-container large" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>配置应用排行参数 - {selectedApp.app_name}</h3>
              <button className="modal-close" onClick={() => setShowAppConfigModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="app-config-form">
                {/* 优秀应用榜配置 */}
                <div className="config-section">
                  <h4>🏆 优秀应用榜配置</h4>
                  <div className="form-row">
                    <div className="form-group">
                      <label>参与排行</label>
                      <input
                        type="checkbox"
                        checked={selectedApp.excellent_enabled}
                        onChange={(e) => setSelectedApp({...selectedApp, excellent_enabled: e.target.checked})}
                      />
                    </div>
                    <div className="form-group">
                      <label>排行权重</label>
                      <input
                        type="number"
                        min="0.1"
                        max="10.0"
                        step="0.1"
                        value={selectedApp.excellent_weight}
                        onChange={(e) => setSelectedApp({...selectedApp, excellent_weight: parseFloat(e.target.value)})}
                      />
                    </div>
                    <div className="form-group">
                      <label>标签</label>
                      <input
                        type="text"
                        value={selectedApp.excellent_tags}
                        onChange={(e) => setSelectedApp({...selectedApp, excellent_tags: e.target.value})}
                        placeholder="多个标签用逗号分隔"
                      />
                    </div>
                  </div>
                </div>

                {/* 趋势榜配置 */}
                <div className="config-section">
                  <h4>📈 趋势榜配置</h4>
                  <div className="form-row">
                    <div className="form-group">
                      <label>参与排行</label>
                      <input
                        type="checkbox"
                        checked={selectedApp.trend_enabled}
                        onChange={(e) => setSelectedApp({...selectedApp, trend_enabled: e.target.checked})}
                      />
                    </div>
                    <div className="form-group">
                      <label>排行权重</label>
                      <input
                        type="number"
                        min="0.1"
                        max="10.0"
                        step="0.1"
                        value={selectedApp.trend_weight}
                        onChange={(e) => setSelectedApp({...selectedApp, trend_weight: parseFloat(e.target.value)})}
                      />
                    </div>
                    <div className="form-group">
                      <label>标签</label>
                      <input
                        type="text"
                        value={selectedApp.trend_tags}
                        onChange={(e) => setSelectedApp({...selectedApp, trend_tags: e.target.value})}
                        placeholder="多个标签用逗号分隔"
                      />
                    </div>
                  </div>
                </div>

                {/* 维度评分配置 */}
                <div className="config-section">
                  <h4>📊 维度评分调整（可选）</h4>
                  <p className="section-tip">不填写则使用系统自动计算的评分</p>
                  <div className="dimension-scores">
                    {dimensions.filter(d => d.is_active).map(dimension => (
                      <div key={dimension.id} className="dimension-score-item">
                        <label>{dimension.name}</label>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={selectedApp.dimension_scores[dimension.id] || ''}
                          onChange={(e) => setSelectedApp({
                            ...selectedApp,
                            dimension_scores: {
                              ...selectedApp.dimension_scores,
                              [dimension.id]: parseInt(e.target.value) || 0
                            }
                          })}
                          placeholder="自动计算"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="secondary-button" onClick={() => setShowAppConfigModal(false)}>
                取消
              </button>
              <button className="primary-button" onClick={() => handleSaveAppConfig(selectedApp)}>
                保存配置
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RankingManagementPage
