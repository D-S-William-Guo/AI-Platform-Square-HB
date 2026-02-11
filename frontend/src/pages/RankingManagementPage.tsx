import { useState, useEffect } from 'react'
import type { RankingDimension, AppItem } from '../types'
import {
  fetchRankingDimensions,
  createRankingDimension,
  updateRankingDimension,
  deleteRankingDimension,
  fetchRankingLogs,
  syncRankings,
  fetchApps,
  fetchRankingConfigs,
  createRankingConfig,
  updateRankingConfig,
  deleteRankingConfig,
  fetchAppRankingSettings,
  fetchAllAppRankingSettings,
  createAppRankingSetting,
  updateAppRankingSetting,
  deleteAppRankingSetting
} from '../api/client'

// 榜单配置类型
interface RankingConfig {
  id: string
  name: string
  description: string
  dimensions_config: string
  calculation_method: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// 应用榜单设置类型
interface AppRankingSettingItem {
  id: number
  app_id: number
  ranking_config_id: string
  is_enabled: boolean
  weight_factor: number
  custom_tags: string
  created_at: string
  updated_at: string
}

// 维度配置项
interface DimensionConfig {
  dim_id: number
  weight: number
}

const RankingManagementPage = () => {
  // 维度管理状态
  const [dimensions, setDimensions] = useState<RankingDimension[]>([])
  const [logs, setLogs] = useState<any[]>([])

  // 榜单配置管理状态
  const [rankingConfigs, setRankingConfigs] = useState<RankingConfig[]>([])
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [editingConfig, setEditingConfig] = useState<RankingConfig | null>(null)
  const [configFormData, setConfigFormData] = useState({
    id: '',
    name: '',
    description: '',
    calculation_method: 'composite',
    is_active: true,
    selectedDimensions: [] as { dim_id: number; weight: number }[]
  })

  // 应用参与管理状态
  const [apps, setApps] = useState<AppItem[]>([])
  const [appSettings, setAppSettings] = useState<Record<number, AppRankingSettingItem[]>>({})
  const [selectedAppForConfig, setSelectedAppForConfig] = useState<AppItem | null>(null)
  const [showAppSettingModal, setShowAppSettingModal] = useState(false)
  const [appSettingForm, setAppSettingForm] = useState({
    ranking_config_id: '',
    is_enabled: true,
    weight_factor: 1.0,
    custom_tags: ''
  })

  // 通用状态
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [syncMessage, setSyncMessage] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'configs' | 'app-settings' | 'dimensions' | 'logs'>('configs')

  // 维度表单状态
  const [showDimensionModal, setShowDimensionModal] = useState(false)
  const [editingDimension, setEditingDimension] = useState<RankingDimension | null>(null)
  const [dimensionFormData, setDimensionFormData] = useState({
    name: '',
    description: '',
    calculation_method: '',
    weight: 1.0,
    is_active: true
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dimensionsData, logsData, appsData, configsData] = await Promise.all([
        fetchRankingDimensions(),
        fetchRankingLogs(),
        fetchApps(),
        fetchRankingConfigs()
      ])
      setDimensions(dimensionsData)
      setLogs(logsData)
      setApps(appsData.filter(app => app.section === 'province'))
      setRankingConfigs(configsData)

      // 加载所有应用榜单设置
      const allSettings = await fetchAllAppRankingSettings()
      const settingsMap: Record<number, AppRankingSettingItem[]> = {}
      for (const setting of allSettings) {
        if (!settingsMap[setting.app_id]) {
          settingsMap[setting.app_id] = []
        }
        settingsMap[setting.app_id].push(setting)
      }
      setAppSettings(settingsMap)
    } catch (err) {
      setError('加载数据失败')
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  // ==================== 榜单配置管理 ====================

  const handleSaveConfig = async () => {
    try {
      const payload = {
        id: configFormData.id,
        name: configFormData.name,
        description: configFormData.description,
        calculation_method: configFormData.calculation_method,
        is_active: configFormData.is_active,
        dimensions_config: JSON.stringify(configFormData.selectedDimensions)
      }

      if (editingConfig) {
        await updateRankingConfig(editingConfig.id, payload)
      } else {
        await createRankingConfig(payload)
      }

      setShowConfigModal(false)
      resetConfigForm()
      loadData()
    } catch (err) {
      setError('保存榜单配置失败')
      console.error('Failed to save config:', err)
    }
  }

  const handleDeleteConfig = async (id: string, name: string) => {
    if (!confirm(`确定要删除榜单配置 "${name}" 吗？`)) return

    try {
      await deleteRankingConfig(id)
      loadData()
    } catch (err) {
      setError('删除榜单配置失败')
      console.error('Failed to delete config:', err)
    }
  }

  const handleEditConfig = (config: RankingConfig) => {
    setEditingConfig(config)
    let selectedDims: { dim_id: number; weight: number }[] = []
    try {
      selectedDims = JSON.parse(config.dimensions_config) || []
    } catch (e) {
      selectedDims = []
    }
    setConfigFormData({
      id: config.id,
      name: config.name,
      description: config.description,
      calculation_method: config.calculation_method,
      is_active: config.is_active,
      selectedDimensions: selectedDims
    })
    setShowConfigModal(true)
  }

  const resetConfigForm = () => {
    setConfigFormData({
      id: '',
      name: '',
      description: '',
      calculation_method: 'composite',
      is_active: true,
      selectedDimensions: []
    })
    setEditingConfig(null)
  }

  const toggleDimensionInConfig = (dimId: number) => {
    const exists = configFormData.selectedDimensions.find(d => d.dim_id === dimId)
    if (exists) {
      setConfigFormData(prev => ({
        ...prev,
        selectedDimensions: prev.selectedDimensions.filter(d => d.dim_id !== dimId)
      }))
    } else {
      setConfigFormData(prev => ({
        ...prev,
        selectedDimensions: [...prev.selectedDimensions, { dim_id: dimId, weight: 1.0 }]
      }))
    }
  }

  const updateDimensionWeight = (dimId: number, weight: number) => {
    setConfigFormData(prev => ({
      ...prev,
      selectedDimensions: prev.selectedDimensions.map(d =>
        d.dim_id === dimId ? { ...d, weight } : d
      )
    }))
  }

  // ==================== 应用榜单设置管理 ====================

  const handleSaveAppSetting = async () => {
    if (!selectedAppForConfig) return

    try {
      const existingSetting = appSettings[selectedAppForConfig.id]?.find(
        s => s.ranking_config_id === appSettingForm.ranking_config_id
      )

      if (existingSetting) {
        await updateAppRankingSetting(selectedAppForConfig.id, existingSetting.id, {
          is_enabled: appSettingForm.is_enabled,
          weight_factor: appSettingForm.weight_factor,
          custom_tags: appSettingForm.custom_tags
        })
      } else {
        await createAppRankingSetting(selectedAppForConfig.id, {
          ranking_config_id: appSettingForm.ranking_config_id,
          is_enabled: appSettingForm.is_enabled,
          weight_factor: appSettingForm.weight_factor,
          custom_tags: appSettingForm.custom_tags
        })
      }

      setShowAppSettingModal(false)
      loadData()
    } catch (err) {
      setError('保存应用榜单设置失败')
      console.error('Failed to save app setting:', err)
    }
  }

  const handleDeleteAppSetting = async (appId: number, settingId: number) => {
    if (!confirm('确定要删除此榜单设置吗？')) return

    try {
      await deleteAppRankingSetting(appId, settingId)
      loadData()
    } catch (err) {
      setError('删除应用榜单设置失败')
      console.error('Failed to delete app setting:', err)
    }
  }

  const openAppSettingModal = (app: AppItem, existingSetting?: AppRankingSettingItem) => {
    setSelectedAppForConfig(app)
    if (existingSetting) {
      setAppSettingForm({
        ranking_config_id: existingSetting.ranking_config_id,
        is_enabled: existingSetting.is_enabled,
        weight_factor: existingSetting.weight_factor,
        custom_tags: existingSetting.custom_tags
      })
    } else {
      setAppSettingForm({
        ranking_config_id: rankingConfigs[0]?.id || '',
        is_enabled: true,
        weight_factor: 1.0,
        custom_tags: ''
      })
    }
    setShowAppSettingModal(true)
  }

  // ==================== 维度管理 ====================

  const handleSaveDimension = async () => {
    try {
      if (editingDimension) {
        await updateRankingDimension(editingDimension.id, dimensionFormData)
      } else {
        await createRankingDimension(dimensionFormData)
      }
      setShowDimensionModal(false)
      resetDimensionForm()
      loadData()
    } catch (err) {
      setError('保存维度失败')
      console.error('Failed to save dimension:', err)
    }
  }

  const handleDeleteDimension = async (id: number, name: string) => {
    if (!confirm(`确定要删除维度 "${name}" 吗？`)) return

    try {
      await deleteRankingDimension(id)
      loadData()
    } catch (err) {
      setError('删除维度失败')
      console.error('Failed to delete dimension:', err)
    }
  }

  const handleEditDimension = (dimension: RankingDimension) => {
    setEditingDimension(dimension)
    setDimensionFormData({
      name: dimension.name,
      description: dimension.description,
      calculation_method: dimension.calculation_method,
      weight: dimension.weight,
      is_active: dimension.is_active
    })
    setShowDimensionModal(true)
  }

  const resetDimensionForm = () => {
    setDimensionFormData({
      name: '',
      description: '',
      calculation_method: '',
      weight: 1.0,
      is_active: true
    })
    setEditingDimension(null)
  }

  // ==================== 排行榜同步 ====================

  const handleSyncRankings = async () => {
    setSyncing(true)
    setSyncMessage(null)
    try {
      const result = await syncRankings()
      setSyncMessage(`同步成功！更新了 ${result.updated_count} 条排名数据`)
      loadData()
    } catch (err) {
      console.error('同步失败:', err)
      setSyncMessage('同步失败，请重试')
    } finally {
      setSyncing(false)
    }
  }

  // ==================== 渲染 ====================

  return (
    <div className="page ranking-management-page">
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
          <p className="page-subtitle">配置榜单规则、管理应用参与、调整评价维度</p>
        </div>

        <div className="page-content">
          {/* 标签页导航 */}
          <div className="tab-navigation">
            <button
              className={`tab-button ${activeTab === 'configs' ? 'active' : ''}`}
              onClick={() => setActiveTab('configs')}
            >
              <span>🏆</span>
              <span>榜单配置</span>
            </button>
            <button
              className={`tab-button ${activeTab === 'app-settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('app-settings')}
            >
              <span>📱</span>
              <span>应用参与</span>
            </button>
            <button
              className={`tab-button ${activeTab === 'dimensions' ? 'active' : ''}`}
              onClick={() => setActiveTab('dimensions')}
            >
              <span>📊</span>
              <span>评价维度</span>
            </button>
            <button
              className={`tab-button ${activeTab === 'logs' ? 'active' : ''}`}
              onClick={() => setActiveTab('logs')}
            >
              <span>📋</span>
              <span>变更日志</span>
            </button>
          </div>

          {/* 榜单配置管理 */}
          {activeTab === 'configs' && (
            <section className="config-section">
              <div className="section-header">
                <h2>榜单配置管理</h2>
                <button
                  className="primary-button"
                  onClick={() => {
                    resetConfigForm()
                    setShowConfigModal(true)
                  }}
                >
                  <span>+</span>
                  <span>新增榜单</span>
                </button>
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
                <div className="config-list">
                  {rankingConfigs.length === 0 ? (
                    <div className="empty-state">
                      <span>🏆</span>
                      <p>暂无榜单配置</p>
                    </div>
                  ) : (
                    <div className="config-cards">
                      {rankingConfigs.map(config => {
                        let dimCount = 0
                        try {
                          const dims = JSON.parse(config.dimensions_config)
                          dimCount = Array.isArray(dims) ? dims.length : 0
                        } catch (e) {
                          dimCount = 0
                        }

                        return (
                          <div key={config.id} className={`config-card ${config.is_active ? 'active' : 'inactive'}`}>
                            <div className="config-card-header">
                              <h3 className="config-card-title">
                                {config.id === 'excellent' ? '🏆' : config.id === 'trend' ? '📈' : '🏅'}
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
                              <button
                                className="edit-button"
                                onClick={() => handleEditConfig(config)}
                              >
                                编辑
                              </button>
                              <button
                                className="sync-button"
                                onClick={() => handleSyncRankings()}
                                disabled={syncing}
                              >
                                {syncing ? '同步中...' : '同步排名'}
                              </button>
                              <button
                                className="delete-button"
                                onClick={() => handleDeleteConfig(config.id, config.name)}
                              >
                                删除
                              </button>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </section>
          )}

          {/* 应用参与管理 */}
          {activeTab === 'app-settings' && (
            <section className="app-settings-section">
              <div className="section-header">
                <h2>应用榜单参与管理</h2>
                <button
                  className="primary-button"
                  onClick={() => handleSyncRankings()}
                  disabled={syncing}
                >
                  {syncing ? '🔄 同步中...' : '🔄 同步所有榜单'}
                </button>
              </div>

              {syncMessage && (
                <div className={`sync-message ${syncMessage.includes('成功') ? 'success' : 'error'}`}>
                  {syncMessage}
                </div>
              )}

              {loading ? (
                <div className="loading">加载中...</div>
              ) : (
                <div className="app-settings-list">
                  {apps.length === 0 ? (
                    <div className="empty-state">
                      <span>📱</span>
                      <p>暂无应用数据</p>
                    </div>
                  ) : (
                    <table className="app-settings-table">
                      <thead>
                        <tr>
                          <th>应用名称</th>
                          <th>所属单位</th>
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
                              <td className="app-org">{app.org}</td>
                              <td className="app-participation">
                                {settings.length === 0 ? (
                                  <span className="no-participation">未参与任何榜单</span>
                                ) : (
                                  <div className="participation-tags">
                                    {settings.map(setting => {
                                      const config = rankingConfigs.find(c => c.id === setting.ranking_config_id)
                                      return (
                                        <span
                                          key={setting.id}
                                          className={`participation-tag ${setting.is_enabled ? 'enabled' : 'disabled'}`}
                                        >
                                          {config?.name || setting.ranking_config_id}
                                          {setting.weight_factor !== 1.0 && ` (×${setting.weight_factor})`}
                                          <button
                                            className="remove-tag"
                                            onClick={() => handleDeleteAppSetting(app.id, setting.id)}
                                          >
                                            ×
                                          </button>
                                        </span>
                                      )
                                    })}
                                  </div>
                                )}
                              </td>
                              <td className="app-actions">
                                <button
                                  className="edit-button"
                                  onClick={() => openAppSettingModal(app)}
                                >
                                  添加参与
                                </button>
                                {settings.map(setting => (
                                  <button
                                    key={setting.id}
                                    className="edit-button secondary"
                                    onClick={() => openAppSettingModal(app, setting)}
                                  >
                                    编辑
                                  </button>
                                ))}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </section>
          )}

          {/* 维度管理 */}
          {activeTab === 'dimensions' && (
            <section className="dimension-section">
              <div className="section-header">
                <h2>评价维度管理</h2>
                <button
                  className="primary-button"
                  onClick={() => {
                    resetDimensionForm()
                    setShowDimensionModal(true)
                  }}
                >
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
                      <p>暂无评价维度</p>
                    </div>
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
                              <button
                                className="edit-button"
                                onClick={() => handleEditDimension(dimension)}
                              >
                                编辑
                              </button>
                              <button
                                className="delete-button"
                                onClick={() => handleDeleteDimension(dimension.id, dimension.name)}
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

          {/* 变更日志 */}
          {activeTab === 'logs' && (
            <section className="logs-section">
              <div className="section-header">
                <h2>变更日志</h2>
              </div>
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
                        <th>对象</th>
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

      {/* 榜单配置模态框 */}
      {showConfigModal && (
        <div className="modal-overlay" onClick={() => setShowConfigModal(false)}>
          <div className="modal-container large" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingConfig ? '编辑榜单配置' : '新增榜单配置'}</h3>
              <button className="modal-close" onClick={() => setShowConfigModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <form className="config-form">
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="config-id">榜单ID *</label>
                    <input
                      type="text"
                      id="config-id"
                      value={configFormData.id}
                      onChange={(e) => setConfigFormData(prev => ({ ...prev, id: e.target.value }))}
                      placeholder="如: excellent, trend"
                      disabled={!!editingConfig}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="config-name">榜单名称 *</label>
                    <input
                      type="text"
                      id="config-name"
                      value={configFormData.name}
                      onChange={(e) => setConfigFormData(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="请输入榜单名称"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="config-description">榜单描述</label>
                  <textarea
                    id="config-description"
                    value={configFormData.description}
                    onChange={(e) => setConfigFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="请输入榜单描述"
                    rows={3}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="config-method">计算公式</label>
                    <select
                      id="config-method"
                      value={configFormData.calculation_method}
                      onChange={(e) => setConfigFormData(prev => ({ ...prev, calculation_method: e.target.value }))}
                    >
                      <option value="composite">综合评分</option>
                      <option value="growth_rate">增长率</option>
                    </select>
                  </div>
                  <div className="form-group checkbox-group">
                    <input
                      type="checkbox"
                      id="config-active"
                      checked={configFormData.is_active}
                      onChange={(e) => setConfigFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    />
                    <label htmlFor="config-active">启用此榜单</label>
                  </div>
                </div>

                <div className="form-group">
                  <label>选择评价维度</label>
                  <div className="dimensions-selector">
                    {dimensions.filter(d => d.is_active).map(dimension => {
                      const selected = configFormData.selectedDimensions.find(d => d.dim_id === dimension.id)
                      return (
                        <div key={dimension.id} className={`dimension-select-item ${selected ? 'selected' : ''}`}>
                          <label className="dimension-checkbox">
                            <input
                              type="checkbox"
                              checked={!!selected}
                              onChange={() => toggleDimensionInConfig(dimension.id)}
                            />
                            <span className="dimension-name">{dimension.name}</span>
                          </label>
                          {selected && (
                            <div className="dimension-weight-input">
                              <span>权重:</span>
                              <input
                                type="number"
                                min="0.1"
                                max="10"
                                step="0.1"
                                value={selected.weight}
                                onChange={(e) => updateDimensionWeight(dimension.id, parseFloat(e.target.value))}
                              />
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </form>
            </div>
            <div className="modal-footer">
              <button className="secondary-button" onClick={() => setShowConfigModal(false)}>
                取消
              </button>
              <button className="primary-button" onClick={handleSaveConfig}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 应用榜单设置模态框 */}
      {showAppSettingModal && selectedAppForConfig && (
        <div className="modal-overlay" onClick={() => setShowAppSettingModal(false)}>
          <div className="modal-container" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>配置应用参与 - {selectedAppForConfig.name}</h3>
              <button className="modal-close" onClick={() => setShowAppSettingModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <form className="app-setting-form">
                <div className="form-group">
                  <label htmlFor="setting-config">选择榜单 *</label>
                  <select
                    id="setting-config"
                    value={appSettingForm.ranking_config_id}
                    onChange={(e) => setAppSettingForm(prev => ({ ...prev, ranking_config_id: e.target.value }))}
                    disabled={appSettings[selectedAppForConfig.id]?.some(s => s.ranking_config_id === appSettingForm.ranking_config_id)}
                  >
                    <option value="">请选择榜单</option>
                    {rankingConfigs.map(config => (
                      <option key={config.id} value={config.id}>{config.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-row">
                  <div className="form-group checkbox-group">
                    <input
                      type="checkbox"
                      id="setting-enabled"
                      checked={appSettingForm.is_enabled}
                      onChange={(e) => setAppSettingForm(prev => ({ ...prev, is_enabled: e.target.checked }))}
                    />
                    <label htmlFor="setting-enabled">启用参与</label>
                  </div>
                  <div className="form-group">
                    <label htmlFor="setting-weight">权重系数</label>
                    <input
                      type="number"
                      id="setting-weight"
                      min="0.1"
                      max="10"
                      step="0.1"
                      value={appSettingForm.weight_factor}
                      onChange={(e) => setAppSettingForm(prev => ({ ...prev, weight_factor: parseFloat(e.target.value) }))}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="setting-tags">自定义标签</label>
                  <input
                    type="text"
                    id="setting-tags"
                    value={appSettingForm.custom_tags}
                    onChange={(e) => setAppSettingForm(prev => ({ ...prev, custom_tags: e.target.value }))}
                    placeholder="多个标签用逗号分隔"
                  />
                </div>
              </form>
            </div>
            <div className="modal-footer">
              <button className="secondary-button" onClick={() => setShowAppSettingModal(false)}>
                取消
              </button>
              <button className="primary-button" onClick={handleSaveAppSetting}>
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 维度管理模态框 */}
      {showDimensionModal && (
        <div className="modal-overlay" onClick={() => setShowDimensionModal(false)}>
          <div className="modal-container" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingDimension ? '编辑评价维度' : '新增评价维度'}</h3>
              <button className="modal-close" onClick={() => setShowDimensionModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <form className="dimension-form">
                <div className="form-group">
                  <label htmlFor="dim-name">维度名称 *</label>
                  <input
                    type="text"
                    id="dim-name"
                    value={dimensionFormData.name}
                    onChange={(e) => setDimensionFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="请输入维度名称"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="dim-description">维度描述 *</label>
                  <textarea
                    id="dim-description"
                    value={dimensionFormData.description}
                    onChange={(e) => setDimensionFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="请输入维度描述"
                    rows={3}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="dim-calculation">计算方法 *</label>
                  <textarea
                    id="dim-calculation"
                    value={dimensionFormData.calculation_method}
                    onChange={(e) => setDimensionFormData(prev => ({ ...prev, calculation_method: e.target.value }))}
                    placeholder="请输入计算方法"
                    rows={4}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="dim-weight">默认权重</label>
                    <input
                      type="number"
                      id="dim-weight"
                      min="0.1"
                      max="10"
                      step="0.1"
                      value={dimensionFormData.weight}
                      onChange={(e) => setDimensionFormData(prev => ({ ...prev, weight: parseFloat(e.target.value) }))}
                    />
                  </div>
                  <div className="form-group checkbox-group">
                    <input
                      type="checkbox"
                      id="dim-active"
                      checked={dimensionFormData.is_active}
                      onChange={(e) => setDimensionFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    />
                    <label htmlFor="dim-active">启用</label>
                  </div>
                </div>
              </form>
            </div>
            <div className="modal-footer">
              <button className="secondary-button" onClick={() => setShowDimensionModal(false)}>
                取消
              </button>
              <button className="primary-button" onClick={handleSaveDimension}>
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
