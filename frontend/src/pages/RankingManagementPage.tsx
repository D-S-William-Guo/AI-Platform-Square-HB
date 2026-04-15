import { useState, useEffect, useMemo } from 'react'
import type { RankingConfigRecord, RankingDimension, AppItem } from '../types'
import {
  fetchRankingDimensions,
  createRankingDimension,
  updateRankingDimension,
  deleteRankingDimension,
  fetchRankingAuditLogs,
  publishRankings,
  fetchAdminRankingConfigs,
  fetchRankingConfigs,
  createRankingConfig,
  updateRankingConfig,
  deleteRankingConfig,
  fetchAllAppRankingSettings,
  fetchAppDimensionScores,
  deleteAppRankingSetting,
  saveAppRankingSetting,
  createGroupApp,
  fetchAdminApps,
  updateAdminAppStatus,
  isMissingAdminTokenError,
  getAdminTokenSetupHint
} from '../api/client'
import Pagination from '../components/Pagination'
import { buildAppPath } from '../utils/basePath'

type RankingConfig = RankingConfigRecord

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

function resolveAdminError(err: unknown, fallback: string): string {
  if (isMissingAdminTokenError(err)) {
    return `缺少管理员认证信息。${getAdminTokenSetupHint()}`
  }

  const status = (err as { response?: { status?: number } })?.response?.status
  if (status === 401) {
    return `登录状态已失效。${getAdminTokenSetupHint()}`
  }
  if (status === 403) {
    return '当前账号不是管理员，无法访问该页面。'
  }
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (detail && typeof detail === 'object') {
    const message = (detail as { message?: string }).message || fallback
    const fieldErrors = (detail as { field_errors?: Array<{ field?: string; message?: string }> }).field_errors || []
    if (fieldErrors.length > 0) {
      const rendered = fieldErrors
        .map((item) => `${item.field || '字段'}: ${item.message || '参数无效'}`)
        .join('；')
      return `${message}（${rendered}）`
    }
    return message
  }
  return fallback
}

const RankingManagementPage = ({
  appCategories,
  categoryOptionsLoading,
  categoryOptionsError,
  defaultAppCategory,
}: {
  appCategories: string[]
  categoryOptionsLoading: boolean
  categoryOptionsError: string | null
  defaultAppCategory: string
}) => {
  // 维度管理状态
  const [dimensions, setDimensions] = useState<RankingDimension[]>([])
  const [logs, setLogs] = useState<any[]>([])

  // 榜单配置管理状态
  const [rankingConfigs, setRankingConfigs] = useState<RankingConfig[]>([])
  const [allRankingConfigs, setAllRankingConfigs] = useState<RankingConfig[]>([])
  const [configPage, setConfigPage] = useState(1)
  const [configPageSize, setConfigPageSize] = useState(6)
  const [configTotal, setConfigTotal] = useState(0)
  const [configTotalPages, setConfigTotalPages] = useState(0)
  const [configLoading, setConfigLoading] = useState(false)
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
  const [appsPage, setAppsPage] = useState(1)
  const [appsPageSize, setAppsPageSize] = useState(10)
  const [appsTotal, setAppsTotal] = useState(0)
  const [appsTotalPages, setAppsTotalPages] = useState(0)
  const [appSettingsLoading, setAppSettingsLoading] = useState(false)
  const [adminApps, setAdminApps] = useState<AppItem[]>([])
  const [adminAppsPage, setAdminAppsPage] = useState(1)
  const [adminAppsPageSize, setAdminAppsPageSize] = useState(10)
  const [adminAppsTotal, setAdminAppsTotal] = useState(0)
  const [adminAppsTotalPages, setAdminAppsTotalPages] = useState(0)
  const [appManagementLoading, setAppManagementLoading] = useState(false)
  const [appSettings, setAppSettings] = useState<Record<number, AppRankingSettingItem[]>>({})
  const [selectedAppForConfig, setSelectedAppForConfig] = useState<AppItem | null>(null)
  const [editingAppSetting, setEditingAppSetting] = useState<AppRankingSettingItem | null>(null)
  const [showAppSettingModal, setShowAppSettingModal] = useState(false)
  const [appSettingForm, setAppSettingForm] = useState({
    ranking_config_id: '',
    is_enabled: true,
    weight_factor: 1.0,
    custom_tags: ''
  })
  const [dimensionScores, setDimensionScores] = useState<Record<number, number>>({})
  const [loadingDimensionScores, setLoadingDimensionScores] = useState(false)

  // 通用状态
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [syncMessage, setSyncMessage] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'configs' | 'app-settings' | 'app-management' | 'group-apps' | 'dimensions' | 'logs'>('configs')
  const [appManagementMessage, setAppManagementMessage] = useState<string | null>(null)
  const [statusUpdatingAppId, setStatusUpdatingAppId] = useState<number | null>(null)
  const [manageSectionFilter, setManageSectionFilter] = useState<'all' | 'group' | 'province'>('all')
  const [manageStatusFilter, setManageStatusFilter] = useState<'all' | 'available' | 'approval' | 'beta' | 'offline'>('all')
  const [manageCompanyFilter, setManageCompanyFilter] = useState('all')
  const [manageKeyword, setManageKeyword] = useState('')

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
  const [groupAppSubmitting, setGroupAppSubmitting] = useState(false)
  const [groupAppMessage, setGroupAppMessage] = useState<string | null>(null)
  const [groupAppForm, setGroupAppForm] = useState({
    name: '',
    org: '',
    category: defaultAppCategory,
    description: '',
    status: 'available',
    monthly_calls: 0,
    api_open: false,
    difficulty: 'Low',
    contact_name: '',
    highlight: '',
    access_mode: 'direct',
    access_url: '',
    target_system: '',
    target_users: '',
    problem_statement: '',
    effectiveness_type: 'efficiency_gain',
    effectiveness_metric: '',
    cover_image_url: ''
  })

  const companyFilterOptions = useMemo(() => {
    const values = adminApps
      .filter((app) => app.section === 'province')
      .map((app) => app.company || app.org)
      .filter(Boolean)
    return ['all', ...Array.from(new Set(values))]
  }, [adminApps])

  useEffect(() => {
    loadBaseData()
  }, [])

  useEffect(() => {
    loadRankingConfigsPage()
  }, [configPage, configPageSize])

  useEffect(() => {
    loadAppSettingsPage()
  }, [appsPage, appsPageSize])

  useEffect(() => {
    loadAdminAppsPage()
  }, [adminAppsPage, adminAppsPageSize, manageSectionFilter, manageStatusFilter, manageCompanyFilter, manageKeyword])

  useEffect(() => {
    if (!defaultAppCategory) return
    setGroupAppForm((prev) => {
      if (appCategories.includes(prev.category)) return prev
      return { ...prev, category: defaultAppCategory }
    })
  }, [appCategories, defaultAppCategory])

  const loadBaseData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dimensionsData, logsData, allConfigsData] = await Promise.all([
        fetchRankingDimensions(),
        fetchRankingAuditLogs(),
        fetchRankingConfigs(),
      ])
      setDimensions(dimensionsData)
      setLogs(logsData)
      setAllRankingConfigs(allConfigsData)

      // 加载所有应用榜单设置
      const allSettings = await fetchAllAppRankingSettings()
      const settingsMap: Record<number, AppRankingSettingItem[]> = {}
      for (const setting of allSettings) {
        if (!setting.ranking_config_id) {
          continue
        }
        if (!settingsMap[setting.app_id]) {
          settingsMap[setting.app_id] = []
        }
        settingsMap[setting.app_id].push(setting)
      }
      setAppSettings(settingsMap)
    } catch (err) {
      setError(resolveAdminError(err, '加载数据失败'))
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadRankingConfigsPage = async () => {
    setConfigLoading(true)
    setError(null)
    try {
      const data = await fetchAdminRankingConfigs({
        page: configPage,
        page_size: configPageSize,
      })
      setRankingConfigs(data.items)
      setConfigTotal(data.total)
      setConfigTotalPages(data.total_pages)
      if (data.total_pages > 0 && configPage > data.total_pages) {
        setConfigPage(data.total_pages)
      }
    } catch (err) {
      setError(resolveAdminError(err, '加载榜单配置失败'))
    } finally {
      setConfigLoading(false)
    }
  }

  const loadAppSettingsPage = async () => {
    setAppSettingsLoading(true)
    setError(null)
    try {
      const data = await fetchAdminApps({
        section: 'province',
        page: appsPage,
        page_size: appsPageSize,
      })
      setApps(data.items)
      setAppsTotal(data.total)
      setAppsTotalPages(data.total_pages)
      if (data.total_pages > 0 && appsPage > data.total_pages) {
        setAppsPage(data.total_pages)
      }
    } catch (err) {
      setError(resolveAdminError(err, '加载应用参与列表失败'))
    } finally {
      setAppSettingsLoading(false)
    }
  }

  const loadAdminAppsPage = async () => {
    setAppManagementLoading(true)
    setError(null)
    try {
      const data = await fetchAdminApps({
        ...(manageSectionFilter !== 'all' ? { section: manageSectionFilter } : {}),
        ...(manageStatusFilter !== 'all' ? { status: manageStatusFilter } : {}),
        ...(manageCompanyFilter !== 'all' ? { company: manageCompanyFilter } : {}),
        ...(manageKeyword.trim() ? { q: manageKeyword.trim() } : {}),
        page: adminAppsPage,
        page_size: adminAppsPageSize,
      })
      setAdminApps(data.items)
      setAdminAppsTotal(data.total)
      setAdminAppsTotalPages(data.total_pages)
      if (data.total_pages > 0 && adminAppsPage > data.total_pages) {
        setAdminAppsPage(data.total_pages)
      }
    } catch (err) {
      setError(resolveAdminError(err, '加载应用管理列表失败'))
    } finally {
      setAppManagementLoading(false)
    }
  }

  const loadData = async () => {
    await Promise.all([
      loadBaseData(),
      loadRankingConfigsPage(),
      loadAppSettingsPage(),
      loadAdminAppsPage(),
    ])
  }

  const loadDimensionScoresForConfig = async (appId: number, rankingConfigId: string) => {
    setLoadingDimensionScores(true)
    try {
      const scoreData = await fetchAppDimensionScores(appId, undefined, rankingConfigId || undefined)
      const scoreMap: Record<number, number> = {}
      for (const item of scoreData) {
        if (typeof item.dimension_id === 'number') {
          scoreMap[item.dimension_id] = Number(item.score || 0)
        }
      }
      setDimensionScores(scoreMap)
    } catch (err) {
      console.error('Failed to fetch app dimension scores:', err)
      setDimensionScores({})
    } finally {
      setLoadingDimensionScores(false)
    }
  }

  useEffect(() => {
    if (!showAppSettingModal || !selectedAppForConfig) {
      return
    }
    if (!appSettingForm.ranking_config_id) {
      setDimensionScores({})
      return
    }
    loadDimensionScoresForConfig(selectedAppForConfig.id, appSettingForm.ranking_config_id)
  }, [showAppSettingModal, selectedAppForConfig, appSettingForm.ranking_config_id])

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
      setError(resolveAdminError(err, '保存榜单配置失败'))
      console.error('Failed to save config:', err)
    }
  }

  const handleDeleteConfig = async (id: string, name: string) => {
    if (!confirm(`确定要删除榜单配置 "${name}" 吗？`)) return

    try {
      await deleteRankingConfig(id)
      loadData()
    } catch (err) {
      setError(resolveAdminError(err, '删除榜单配置失败'))
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
      if (!appSettingForm.ranking_config_id) {
        setError('请选择榜单后再保存')
        return
      }

      const sameConfigSetting = appSettings[selectedAppForConfig.id]?.find(
        s =>
          s.ranking_config_id === appSettingForm.ranking_config_id
          && s.id !== editingAppSetting?.id
      )
      if (sameConfigSetting) {
        setError('该应用已参与所选榜单，请直接编辑已有配置')
        return
      }

      const scoreUpdates = Object.entries(dimensionScores).map(([dimensionId, score]) => ({
        dimension_id: Number(dimensionId),
        score: Math.max(0, Math.min(100, Number(score)))
      }))

      await saveAppRankingSetting(selectedAppForConfig.id, {
        setting_id: editingAppSetting?.id,
        ranking_config_id: appSettingForm.ranking_config_id,
        is_enabled: appSettingForm.is_enabled,
        weight_factor: appSettingForm.weight_factor,
        custom_tags: appSettingForm.custom_tags,
        dimension_scores: scoreUpdates
      })

      setShowAppSettingModal(false)
      setEditingAppSetting(null)
      loadData()
    } catch (err) {
      setError(resolveAdminError(err, '保存应用榜单设置失败'))
      console.error('Failed to save app setting:', err)
    }
  }

  const handleDeleteAppSetting = async (appId: number, settingId: number) => {
    if (!confirm('确定要删除此榜单设置吗？')) return

    try {
      await deleteAppRankingSetting(appId, settingId)
      loadData()
    } catch (err) {
      setError(resolveAdminError(err, '删除应用榜单设置失败'))
      console.error('Failed to delete app setting:', err)
    }
  }

  const openAppSettingModal = (app: AppItem, existingSetting?: AppRankingSettingItem) => {
    setSelectedAppForConfig(app)
    setEditingAppSetting(existingSetting || null)
    const defaultConfigId = existingSetting?.ranking_config_id || allRankingConfigs[0]?.id || ''
    if (existingSetting) {
      setAppSettingForm({
        ranking_config_id: existingSetting.ranking_config_id,
        is_enabled: existingSetting.is_enabled,
        weight_factor: existingSetting.weight_factor,
        custom_tags: existingSetting.custom_tags
      })
    } else {
      setAppSettingForm({
        ranking_config_id: defaultConfigId,
        is_enabled: true,
        weight_factor: 1.0,
        custom_tags: ''
      })
    }

    setDimensionScores({})
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
      setError(resolveAdminError(err, '保存维度失败'))
      console.error('Failed to save dimension:', err)
    }
  }

  const handleDeleteDimension = async (id: number, name: string) => {
    if (!confirm(`确定要删除维度 "${name}" 吗？`)) return

    try {
      await deleteRankingDimension(id)
      loadData()
    } catch (err) {
      setError(resolveAdminError(err, '删除维度失败'))
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

  // ==================== 集团应用录入 ====================

  const resetGroupAppForm = () => {
    setGroupAppForm({
      name: '',
      org: '',
      category: defaultAppCategory,
      description: '',
      status: 'available',
      monthly_calls: 0,
      api_open: false,
      difficulty: 'Low',
      contact_name: '',
      highlight: '',
      access_mode: 'direct',
      access_url: '',
      target_system: '',
      target_users: '',
      problem_statement: '',
      effectiveness_type: 'efficiency_gain',
      effectiveness_metric: '',
      cover_image_url: ''
    })
  }

  const handleSaveGroupApp = async () => {
    if (categoryOptionsLoading || categoryOptionsError || appCategories.length === 0) {
      setError(categoryOptionsError || '分类配置加载中，请稍后重试')
      return
    }
    const name = groupAppForm.name.trim()
    const org = groupAppForm.org.trim()
    const category = groupAppForm.category.trim()
    const description = groupAppForm.description.trim()
    if (!name || !org || !category || !description) {
      setError('请先填写集团应用录入的必填项')
      return
    }

    try {
      setGroupAppSubmitting(true)
      setGroupAppMessage(null)
      setError(null)
      await createGroupApp({
        ...groupAppForm,
        name,
        org,
        category,
        description,
        monthly_calls: Number(groupAppForm.monthly_calls || 0),
        access_url: groupAppForm.access_url.trim(),
        target_system: groupAppForm.target_system.trim(),
        target_users: groupAppForm.target_users.trim(),
        problem_statement: groupAppForm.problem_statement.trim(),
        effectiveness_metric: groupAppForm.effectiveness_metric.trim(),
        cover_image_url: groupAppForm.cover_image_url.trim(),
        contact_name: groupAppForm.contact_name.trim(),
        highlight: groupAppForm.highlight.trim()
      })
      setGroupAppMessage('集团应用录入成功')
      resetGroupAppForm()
      await loadData()
    } catch (err) {
      setError(resolveAdminError(err, '集团应用录入失败'))
    } finally {
      setGroupAppSubmitting(false)
    }
  }

  // ==================== 排行榜同步 ====================

  const handleSyncRankings = async () => {
    setSyncing(true)
    setSyncMessage(null)
    try {
      const result = await publishRankings()
      setSyncMessage(`发布成功！更新了 ${result.updated_count} 条榜单数据（run_id: ${result.run_id}）`)
      loadData()
    } catch (err) {
      console.error('同步失败:', err)
      setSyncMessage(resolveAdminError(err, '发布失败，请重试'))
    } finally {
      setSyncing(false)
    }
  }

  const handleUpdateAppStatus = async (app: AppItem, nextStatus: 'available' | 'approval' | 'beta' | 'offline') => {
    const actionText = nextStatus === 'offline' ? '下架' : '上架'
    if (!confirm(`确定要将应用「${app.name}」${actionText}为 ${nextStatus} 吗？`)) {
      return
    }
    try {
      setStatusUpdatingAppId(app.id)
      setAppManagementMessage(null)
      await updateAdminAppStatus(app.id, nextStatus)
      setAppManagementMessage(`应用「${app.name}」状态已更新为 ${nextStatus}`)
      await Promise.all([loadAppSettingsPage(), loadAdminAppsPage()])
    } catch (err) {
      setError(resolveAdminError(err, '更新应用状态失败'))
    } finally {
      setStatusUpdatingAppId(null)
    }
  }

  const selectedConfigDimensions = (() => {
    const activeDimensions = dimensions.filter(d => d.is_active)
    if (!appSettingForm.ranking_config_id) {
      return activeDimensions
    }
    const selectedConfig = allRankingConfigs.find(config => config.id === appSettingForm.ranking_config_id)
    if (!selectedConfig) {
      return activeDimensions
    }
    try {
      const parsed = JSON.parse(selectedConfig.dimensions_config || '[]')
      const ids = new Set<number>(
        Array.isArray(parsed)
          ? parsed
              .map((item: DimensionConfig) => Number(item.dim_id))
              .filter((id: number) => !Number.isNaN(id))
          : []
      )
      if (ids.size === 0) {
        return activeDimensions
      }
      return activeDimensions.filter(d => ids.has(d.id))
    } catch (_err) {
      return activeDimensions
    }
  })()

  // ==================== 渲染 ====================

  return (
    <div className="page ranking-management-page">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
        <div className="header-actions">
          <button className="primary" onClick={() => window.location.href = buildAppPath('/')}>
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
              className={`tab-button ${activeTab === 'app-management' ? 'active' : ''}`}
              onClick={() => setActiveTab('app-management')}
            >
              <span>🗂️</span>
              <span>应用管理</span>
            </button>
            <button
              className={`tab-button ${activeTab === 'group-apps' ? 'active' : ''}`}
              onClick={() => setActiveTab('group-apps')}
            >
              <span>🏢</span>
              <span>集团应用录入</span>
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

              {loading || configLoading ? (
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
                  <Pagination
                    page={configPage}
                    pageSize={configPageSize}
                    total={configTotal}
                    totalPages={configTotalPages}
                    disabled={configLoading}
                    onPageChange={setConfigPage}
                    pageSizeOptions={[6, 12]}
                    onPageSizeChange={(nextPageSize) => {
                      setConfigPage(1)
                      setConfigPageSize(nextPageSize)
                    }}
                  />
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
                  {syncing ? '🔄 发布中...' : '🚀 发布榜单'}
                </button>
              </div>
              <p className="section-note">
                评分来源说明：榜单最终分数 = 各维度评分 × 维度权重 × 应用权重系数。维度评分可在“添加参与/编辑”弹窗中维护。
              </p>

              {syncMessage && (
                <div className={`sync-message ${syncMessage.includes('成功') ? 'success' : 'error'}`}>
                  {syncMessage}
                </div>
              )}

              {loading || appSettingsLoading ? (
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
                  <Pagination
                    page={appsPage}
                    pageSize={appsPageSize}
                    total={appsTotal}
                    totalPages={appsTotalPages}
                    disabled={appSettingsLoading}
                    onPageChange={setAppsPage}
                    onPageSizeChange={(nextPageSize) => {
                      setAppsPage(1)
                      setAppsPageSize(nextPageSize)
                    }}
                  />
                </div>
              )}
            </section>
          )}

          {activeTab === 'app-management' && (
            <section className="app-management-section">
              <div className="section-header">
                <h2>应用上下架管理</h2>
                <button className="secondary-button" onClick={loadData} disabled={loading}>
                  刷新
                </button>
              </div>
              <p className="section-note">
                下架后应用不在首页展示；省内应用下架后将自动失去当前榜单参与资格（历史榜单保留）。
              </p>

              {appManagementMessage ? (
                <div className="sync-message success">{appManagementMessage}</div>
              ) : null}

              <div className="app-management-filters">
                <select
                  value={manageSectionFilter}
                  onChange={(e) => {
                    setManageSectionFilter(e.target.value as 'all' | 'group' | 'province')
                    setAdminAppsPage(1)
                  }}
                >
                  <option value="all">全部分区</option>
                  <option value="province">省内应用</option>
                  <option value="group">集团应用</option>
                </select>
                <select
                  value={manageStatusFilter}
                  onChange={(e) => {
                    setManageStatusFilter(e.target.value as 'all' | 'available' | 'approval' | 'beta' | 'offline')
                    setAdminAppsPage(1)
                  }}
                >
                  <option value="all">全部状态</option>
                  <option value="available">可用</option>
                  <option value="approval">需申请</option>
                  <option value="beta">试运行</option>
                  <option value="offline">已下线</option>
                </select>
                <select
                  value={manageCompanyFilter}
                  onChange={(e) => {
                    setManageCompanyFilter(e.target.value)
                    setAdminAppsPage(1)
                  }}
                >
                  {companyFilterOptions.map((item) => (
                    <option key={item} value={item}>
                      {item === 'all' ? '全部公司' : item}
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  value={manageKeyword}
                  onChange={(e) => {
                    setManageKeyword(e.target.value)
                    setAdminAppsPage(1)
                  }}
                  placeholder="搜索应用名/公司/部门/分类"
                />
              </div>

              {loading || appManagementLoading ? (
                <div className="loading">加载中...</div>
              ) : (
                <div className="app-management-list">
                  {adminApps.length === 0 ? (
                    <div className="empty-state">
                      <span>🗂️</span>
                      <p>暂无匹配应用</p>
                    </div>
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
                            <td>
                              <div className="app-name">{app.name}</div>
                              <div className="app-org">{app.company || app.org}</div>
                            </td>
                            <td>{app.section === 'province' ? '省内应用' : '集团应用'}</td>
                            <td>
                              <div>{app.company || app.org}</div>
                              <div className="app-org">{app.department || '未设置'}</div>
                            </td>
                            <td>{app.category}</td>
                            <td>
                              <span className={`status-chip ${app.status}`}>{app.status}</span>
                            </td>
                            <td>
                              {app.status === 'offline' ? (
                                <button
                                  className="edit-button secondary"
                                  disabled={statusUpdatingAppId === app.id}
                                  onClick={() => handleUpdateAppStatus(app, 'available')}
                                >
                                  {statusUpdatingAppId === app.id ? '处理中...' : '重新上架'}
                                </button>
                              ) : (
                                <button
                                  className="delete-button"
                                  disabled={statusUpdatingAppId === app.id}
                                  onClick={() => handleUpdateAppStatus(app, 'offline')}
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
                    page={adminAppsPage}
                    pageSize={adminAppsPageSize}
                    total={adminAppsTotal}
                    totalPages={adminAppsTotalPages}
                    disabled={appManagementLoading}
                    onPageChange={setAdminAppsPage}
                    onPageSizeChange={(nextPageSize) => {
                      setAdminAppsPage(1)
                      setAdminAppsPageSize(nextPageSize)
                    }}
                  />
                </div>
              )}
            </section>
          )}

          {/* 集团应用录入 */}
          {activeTab === 'group-apps' && (
            <section className="group-app-section">
              <div className="section-header">
                <h2>集团应用录入</h2>
                <button
                  className="primary-button"
                  onClick={handleSaveGroupApp}
                  disabled={groupAppSubmitting || categoryOptionsLoading || Boolean(categoryOptionsError)}
                >
                  {groupAppSubmitting ? '保存中...' : '保存集团应用'}
                </button>
              </div>
              <p className="section-note">
                集团应用与省内应用保持同构字段，但仅管理员录入，不进入省内申报审核链路。
              </p>

              {groupAppMessage && (
                <div className="sync-message success">{groupAppMessage}</div>
              )}
              {categoryOptionsError && (
                <div className="sync-message">{categoryOptionsError}</div>
              )}

              <form className="group-app-form">
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="group-name">应用名称 *</label>
                    <input
                      id="group-name"
                      type="text"
                      value={groupAppForm.name}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="请输入集团应用名称"
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="group-org">所属单位 *</label>
                    <input
                      id="group-org"
                      type="text"
                      value={groupAppForm.org}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, org: e.target.value }))}
                      placeholder="请输入所属单位"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="group-category">分类 *</label>
                    <select
                      id="group-category"
                      value={groupAppForm.category}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, category: e.target.value }))}
                      disabled={categoryOptionsLoading || Boolean(categoryOptionsError)}
                    >
                      {appCategories.map((category) => (
                        <option key={category} value={category}>{category}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label htmlFor="group-status">状态</label>
                    <select
                      id="group-status"
                      value={groupAppForm.status}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, status: e.target.value }))}
                    >
                      <option value="available">可用</option>
                      <option value="beta">试运行</option>
                      <option value="approval">需申请</option>
                      <option value="offline">已下线</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="group-description">应用描述 *</label>
                  <textarea
                    id="group-description"
                    rows={4}
                    value={groupAppForm.description}
                    onChange={(e) => setGroupAppForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="请输入应用描述（不少于10字）"
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="group-access-mode">接入方式</label>
                    <select
                      id="group-access-mode"
                      value={groupAppForm.access_mode}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, access_mode: e.target.value }))}
                    >
                      <option value="direct">直接接入</option>
                      <option value="profile">介绍页跳转</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label htmlFor="group-access-url">访问地址</label>
                    <input
                      id="group-access-url"
                      type="text"
                      value={groupAppForm.access_url}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, access_url: e.target.value }))}
                      placeholder="https://..."
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="group-monthly-calls">月调用量</label>
                    <input
                      id="group-monthly-calls"
                      type="number"
                      min="0"
                      step="1"
                      value={groupAppForm.monthly_calls}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, monthly_calls: Number(e.target.value || 0) }))}
                    />
                  </div>
                  <div className="form-group checkbox-group">
                    <input
                      id="group-api-open"
                      type="checkbox"
                      checked={groupAppForm.api_open}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, api_open: e.target.checked }))}
                    />
                    <label htmlFor="group-api-open">开放API</label>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="group-target-system">接入系统</label>
                    <input
                      id="group-target-system"
                      type="text"
                      value={groupAppForm.target_system}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, target_system: e.target.value }))}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="group-target-users">适用人群</label>
                    <input
                      id="group-target-users"
                      type="text"
                      value={groupAppForm.target_users}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, target_users: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="group-effectiveness-type">成效类型</label>
                    <select
                      id="group-effectiveness-type"
                      value={groupAppForm.effectiveness_type}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, effectiveness_type: e.target.value }))}
                    >
                      <option value="cost_reduction">降本</option>
                      <option value="efficiency_gain">增效</option>
                      <option value="perception_uplift">感知提升</option>
                      <option value="revenue_growth">拉动收入</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label htmlFor="group-effectiveness-metric">成效指标</label>
                    <input
                      id="group-effectiveness-metric"
                      type="text"
                      value={groupAppForm.effectiveness_metric}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, effectiveness_metric: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="group-problem">解决问题</label>
                  <textarea
                    id="group-problem"
                    rows={3}
                    value={groupAppForm.problem_statement}
                    onChange={(e) => setGroupAppForm(prev => ({ ...prev, problem_statement: e.target.value }))}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="group-contact-name">联系人</label>
                    <input
                      id="group-contact-name"
                      type="text"
                      value={groupAppForm.contact_name}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, contact_name: e.target.value }))}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="group-difficulty">接入难度</label>
                    <select
                      id="group-difficulty"
                      value={groupAppForm.difficulty}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, difficulty: e.target.value }))}
                    >
                      <option value="Low">低</option>
                      <option value="Medium">中</option>
                      <option value="High">高</option>
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="group-highlight">亮点标签</label>
                    <input
                      id="group-highlight"
                      type="text"
                      value={groupAppForm.highlight}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, highlight: e.target.value }))}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="group-cover-url">封面图 URL</label>
                    <input
                      id="group-cover-url"
                      type="text"
                      value={groupAppForm.cover_image_url}
                      onChange={(e) => setGroupAppForm(prev => ({ ...prev, cover_image_url: e.target.value }))}
                    />
                  </div>
                </div>
              </form>
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
                            <span
                              className={`action-badge ${
                                String(log.action || '').includes('created')
                                  ? 'create'
                                  : String(log.action || '').includes('deleted')
                                    ? 'delete'
                                    : 'update'
                              }`}
                            >
                              {String(log.action || '').includes('created')
                                ? '创建'
                                : String(log.action || '').includes('deleted')
                                  ? '删除'
                                  : String(log.action || '').includes('sync')
                                    ? '同步'
                                    : '更新'}
                            </span>
                          </td>
                          <td className="log-dimension">{log.ranking_config_id || log.ranking_type || '-'}</td>
                          <td className="log-changes">{log.payload_summary || '-'}</td>
                          <td className="log-operator">{log.actor || '-'}</td>
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
        <div
          className="modal-overlay"
          onClick={() => {
            setShowAppSettingModal(false)
            setEditingAppSetting(null)
          }}
        >
          <div className="modal-container" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingAppSetting ? '编辑应用参与' : '配置应用参与'} - {selectedAppForConfig.name}</h3>
              <button
                className="modal-close"
                onClick={() => {
                  setShowAppSettingModal(false)
                  setEditingAppSetting(null)
                }}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <form className="app-setting-form">
                <div className="form-group">
                  <label htmlFor="setting-config">选择榜单 *</label>
                  <select
                    id="setting-config"
                    value={appSettingForm.ranking_config_id}
                    onChange={(e) => setAppSettingForm(prev => ({ ...prev, ranking_config_id: e.target.value }))}
                  >
                    <option value="">请选择榜单</option>
                    {allRankingConfigs.map(config => (
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

                <div className="form-group">
                  <label>维度评分（0-100）</label>
                  <p className="form-hint">
                    应用最终分数由“榜单维度权重 × 应用维度评分 × 权重系数”计算，未填写时默认沿用当前评分。
                  </p>
                  {loadingDimensionScores ? (
                    <div className="loading">加载维度评分中...</div>
                  ) : selectedConfigDimensions.length === 0 ? (
                    <div className="empty-state">
                      <p>当前榜单未配置有效维度</p>
                    </div>
                  ) : (
                    <div className="dimension-score-grid">
                      {selectedConfigDimensions.map((dimension) => (
                        <div key={dimension.id} className="dimension-score-item">
                          <span className="dimension-score-name">{dimension.name}</span>
                          <input
                            type="number"
                            min="0"
                            max="100"
                            step="1"
                            value={dimensionScores[dimension.id] ?? 0}
                            onChange={(e) => {
                              const nextValue = Math.max(0, Math.min(100, Number(e.target.value || 0)))
                              setDimensionScores(prev => ({ ...prev, [dimension.id]: nextValue }))
                            }}
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </form>
            </div>
            <div className="modal-footer">
              <button
                className="secondary-button"
                onClick={() => {
                  setShowAppSettingModal(false)
                  setEditingAppSetting(null)
                }}
              >
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
