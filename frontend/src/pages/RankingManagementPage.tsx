import { useState, useEffect, useMemo } from 'react'
import type { RankingDimension, AppItem } from '../types'
import {
  fetchRankingDimensions,
  fetchRankingAuditLogs,
  publishRankings,
  fetchAdminRankingConfigs,
  fetchRankingConfigs,
  deleteRankingConfig,
  fetchAllAppRankingSettings,
  deleteAppRankingSetting,
  deleteRankingDimension,
  fetchAdminApps,
  updateAdminAppStatus,
} from '../api/client'
import { buildAppPath } from '../utils/basePath'
import UiIcon from '../components/UiIcon'
import { resolveAdminError, type AppRankingSettingItem } from './rankingUtils'
import RankingConfigsTab from './components/ranking/RankingConfigsTab'
import AppSettingsTab from './components/ranking/AppSettingsTab'
import AppManagementTab from './components/ranking/AppManagementTab'
import GroupAppsTab from './components/ranking/GroupAppsTab'
import DimensionsTab from './components/ranking/DimensionsTab'
import AuditLogsTab from './components/ranking/AuditLogsTab'
import RankingConfigModal from './components/ranking/RankingConfigModal'
import AppSettingModal from './components/ranking/AppSettingModal'
import DimensionModal from './components/ranking/DimensionModal'

type RankingConfig = {
  id: string; name: string; description: string
  calculation_method: string; is_active: boolean; dimensions_config: string
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
  // 基础数据
  const [dimensions, setDimensions] = useState<RankingDimension[]>([])
  const [logs, setLogs] = useState<any[]>([])

  // 榜单配置
  const [rankingConfigs, setRankingConfigs] = useState<RankingConfig[]>([])
  const [allRankingConfigs, setAllRankingConfigs] = useState<RankingConfig[]>([])
  const [configPage, setConfigPage] = useState(1)
  const [configPageSize, setConfigPageSize] = useState(6)
  const [configTotal, setConfigTotal] = useState(0)
  const [configTotalPages, setConfigTotalPages] = useState(0)
  const [configLoading, setConfigLoading] = useState(false)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [editingConfig, setEditingConfig] = useState<RankingConfig | null>(null)

  // 应用参与
  const [apps, setApps] = useState<AppItem[]>([])
  const [appsPage, setAppsPage] = useState(1)
  const [appsPageSize, setAppsPageSize] = useState(10)
  const [appsTotal, setAppsTotal] = useState(0)
  const [appsTotalPages, setAppsTotalPages] = useState(0)
  const [appSettingsLoading, setAppSettingsLoading] = useState(false)
  const [appSettings, setAppSettings] = useState<Record<number, AppRankingSettingItem[]>>({})
  const [selectedAppForConfig, setSelectedAppForConfig] = useState<AppItem | null>(null)
  const [editingAppSetting, setEditingAppSetting] = useState<AppRankingSettingItem | null>(null)
  const [showAppSettingModal, setShowAppSettingModal] = useState(false)

  // 应用管理
  const [adminApps, setAdminApps] = useState<AppItem[]>([])
  const [adminAppsPage, setAdminAppsPage] = useState(1)
  const [adminAppsPageSize, setAdminAppsPageSize] = useState(10)
  const [adminAppsTotal, setAdminAppsTotal] = useState(0)
  const [adminAppsTotalPages, setAdminAppsTotalPages] = useState(0)
  const [appManagementLoading, setAppManagementLoading] = useState(false)
  const [appManagementMessage, setAppManagementMessage] = useState<string | null>(null)
  const [statusUpdatingAppId, setStatusUpdatingAppId] = useState<number | null>(null)
  const [manageSectionFilter, setManageSectionFilter] = useState<'all' | 'group' | 'province'>('all')
  const [manageStatusFilter, setManageStatusFilter] = useState<'all' | 'available' | 'approval' | 'beta' | 'offline'>('all')
  const [manageCompanyFilter, setManageCompanyFilter] = useState('all')
  const [manageKeyword, setManageKeyword] = useState('')

  // 通用
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [syncMessage, setSyncMessage] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'configs' | 'app-settings' | 'app-management' | 'group-apps' | 'dimensions' | 'logs'>('configs')

  // 维度模态框
  const [showDimensionModal, setShowDimensionModal] = useState(false)
  const [editingDimension, setEditingDimension] = useState<RankingDimension | null>(null)

  const companyFilterOptions = useMemo(() => {
    const values = adminApps
      .filter((app) => app.section === 'province')
      .map((app) => app.company || app.org)
      .filter(Boolean)
    return ['all', ...Array.from(new Set(values))]
  }, [adminApps])

  // ==================== 数据加载 ====================

  useEffect(() => { loadBaseData() }, [])
  useEffect(() => { loadRankingConfigsPage() }, [configPage, configPageSize])
  useEffect(() => { loadAppSettingsPage() }, [appsPage, appsPageSize])
  useEffect(() => { loadAdminAppsPage() }, [adminAppsPage, adminAppsPageSize, manageSectionFilter, manageStatusFilter, manageCompanyFilter, manageKeyword])

  const loadBaseData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [dimensionsData, logsData, allConfigsData] = await Promise.all([
        fetchRankingDimensions(), fetchRankingAuditLogs(), fetchRankingConfigs(),
      ])
      setDimensions(dimensionsData)
      setLogs(logsData)
      setAllRankingConfigs(allConfigsData)

      const allSettings = await fetchAllAppRankingSettings()
      const settingsMap: Record<number, AppRankingSettingItem[]> = {}
      for (const setting of allSettings) {
        if (!setting.ranking_config_id) continue
        if (!settingsMap[setting.app_id]) settingsMap[setting.app_id] = []
        settingsMap[setting.app_id].push(setting)
      }
      setAppSettings(settingsMap)
    } catch (err) {
      setError(resolveAdminError(err, '加载数据失败'))
    } finally {
      setLoading(false)
    }
  }

  const loadRankingConfigsPage = async () => {
    setConfigLoading(true)
    setError(null)
    try {
      const data = await fetchAdminRankingConfigs({ page: configPage, page_size: configPageSize })
      setRankingConfigs(data.items)
      setConfigTotal(data.total)
      setConfigTotalPages(data.total_pages)
      if (data.total_pages > 0 && configPage > data.total_pages) setConfigPage(data.total_pages)
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
      const data = await fetchAdminApps({ section: 'province', page: appsPage, page_size: appsPageSize })
      setApps(data.items)
      setAppsTotal(data.total)
      setAppsTotalPages(data.total_pages)
      if (data.total_pages > 0 && appsPage > data.total_pages) setAppsPage(data.total_pages)
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
        page: adminAppsPage, page_size: adminAppsPageSize,
      })
      setAdminApps(data.items)
      setAdminAppsTotal(data.total)
      setAdminAppsTotalPages(data.total_pages)
      if (data.total_pages > 0 && adminAppsPage > data.total_pages) setAdminAppsPage(data.total_pages)
    } catch (err) {
      setError(resolveAdminError(err, '加载应用管理列表失败'))
    } finally {
      setAppManagementLoading(false)
    }
  }

  const reloadAll = () => Promise.all([loadBaseData(), loadRankingConfigsPage(), loadAppSettingsPage(), loadAdminAppsPage()])

  // ==================== 同步/发布 ====================

  const handleSyncRankings = async () => {
    setSyncing(true)
    setSyncMessage(null)
    try {
      const result = await publishRankings()
      setSyncMessage(`发布成功！更新了 ${result.updated_count} 条榜单数据（run_id: ${result.run_id}）`)
      reloadAll()
    } catch (err) {
      setSyncMessage(resolveAdminError(err, '发布失败，请重试'))
    } finally {
      setSyncing(false)
    }
  }

  // ==================== 榜单配置 ====================

  const handleDeleteConfig = async (id: string, name: string) => {
    if (!confirm(`确定要删除榜单配置 "${name}" 吗？`)) return
    try {
      await deleteRankingConfig(id)
      reloadAll()
    } catch (err) {
      setError(resolveAdminError(err, '删除榜单配置失败'))
    }
  }

  // ==================== 应用参与 ====================

  const handleDeleteAppSetting = async (appId: number, settingId: number) => {
    if (!confirm('确定要删除此榜单设置吗？')) return
    try {
      await deleteAppRankingSetting(appId, settingId)
      reloadAll()
    } catch (err) {
      setError(resolveAdminError(err, '删除应用榜单设置失败'))
    }
  }

  const openAppSettingModal = (app: AppItem, existingSetting?: AppRankingSettingItem) => {
    setSelectedAppForConfig(app)
    setEditingAppSetting(existingSetting || null)
    setShowAppSettingModal(true)
  }

  // ==================== 维度管理 ====================

  const handleDeleteDimension = async (id: number, name: string) => {
    if (!confirm(`确定要删除维度 "${name}" 吗？`)) return
    try {
      await deleteRankingDimension(id)
      reloadAll()
    } catch (err) {
      setError(resolveAdminError(err, '删除维度失败'))
    }
  }

  // ==================== 应用管理 ====================

  const handleUpdateAppStatus = async (app: AppItem, nextStatus: 'available' | 'approval' | 'beta' | 'offline') => {
    const actionText = nextStatus === 'offline' ? '下架' : '上架'
    if (!confirm(`确定要将应用「${app.name}」${actionText}为 ${nextStatus} 吗？`)) return
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

  const handleManageFilterChange = (field: string, value: string) => {
    setAdminAppsPage(1)
    switch (field) {
      case 'section': setManageSectionFilter(value as 'all' | 'group' | 'province'); break
      case 'status': setManageStatusFilter(value as 'all' | 'available' | 'approval' | 'beta' | 'offline'); break
      case 'company': setManageCompanyFilter(value); break
      case 'keyword': setManageKeyword(value); break
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
            {([
              ['configs', 'trophy', '榜单配置'],
              ['app-settings', 'platform', '应用参与'],
              ['app-management', 'history', '应用管理'],
              ['group-apps', 'group', '集团应用录入'],
              ['dimensions', 'empty', '评价维度'],
              ['logs', 'history', '变更日志'],
            ] as const).map(([tab, icon, label]) => (
              <button
                key={tab}
                className={`tab-button ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                <UiIcon name={icon} />
                <span>{label}</span>
              </button>
            ))}
          </div>

          {activeTab === 'configs' && (
            <RankingConfigsTab
              rankingConfigs={rankingConfigs}
              loading={loading}
              configLoading={configLoading}
              error={error}
              configPage={configPage}
              configPageSize={configPageSize}
              configTotal={configTotal}
              configTotalPages={configTotalPages}
              syncing={syncing}
              syncMessage={syncMessage}
              onSync={handleSyncRankings}
              onEdit={(config) => { setEditingConfig(config); setShowConfigModal(true) }}
              onDelete={handleDeleteConfig}
              onNewConfig={() => { setEditingConfig(null); setShowConfigModal(true) }}
              onPageChange={setConfigPage}
              onPageSizeChange={setConfigPageSize}
            />
          )}

          {activeTab === 'app-settings' && (
            <AppSettingsTab
              apps={apps}
              appSettings={appSettings}
              allRankingConfigs={allRankingConfigs}
              appsPage={appsPage}
              appsPageSize={appsPageSize}
              appsTotal={appsTotal}
              appsTotalPages={appsTotalPages}
              appSettingsLoading={appSettingsLoading}
              loading={loading}
              error={error}
              syncing={syncing}
              syncMessage={syncMessage}
              onSync={handleSyncRankings}
              onAddParticipation={(app) => openAppSettingModal(app)}
              onEditParticipation={(app, setting) => openAppSettingModal(app, setting)}
              onDeleteAppSetting={handleDeleteAppSetting}
              onPageChange={setAppsPage}
              onPageSizeChange={setAppsPageSize}
            />
          )}

          {activeTab === 'app-management' && (
            <AppManagementTab
              adminApps={adminApps}
              appManagementLoading={appManagementLoading}
              loading={loading}
              error={error}
              adminAppsPage={adminAppsPage}
              adminAppsPageSize={adminAppsPageSize}
              adminAppsTotal={adminAppsTotal}
              adminAppsTotalPages={adminAppsTotalPages}
              appManagementMessage={appManagementMessage}
              manageSectionFilter={manageSectionFilter}
              manageStatusFilter={manageStatusFilter}
              manageCompanyFilter={manageCompanyFilter}
              manageKeyword={manageKeyword}
              companyFilterOptions={companyFilterOptions}
              statusUpdatingAppId={statusUpdatingAppId}
              onFilterChange={handleManageFilterChange}
              onUpdateAppStatus={handleUpdateAppStatus}
              onRefresh={reloadAll}
              onPageChange={setAdminAppsPage}
              onPageSizeChange={setAdminAppsPageSize}
            />
          )}

          {activeTab === 'group-apps' && (
            <GroupAppsTab
              appCategories={appCategories}
              defaultAppCategory={defaultAppCategory}
              categoryOptionsLoading={categoryOptionsLoading}
              categoryOptionsError={categoryOptionsError}
              onError={setError}
              onSaved={reloadAll}
            />
          )}

          {activeTab === 'dimensions' && (
            <DimensionsTab
              dimensions={dimensions}
              loading={loading}
              error={error}
              onEdit={(dim) => { setEditingDimension(dim); setShowDimensionModal(true) }}
              onDelete={handleDeleteDimension}
              onNewDimension={() => { setEditingDimension(null); setShowDimensionModal(true) }}
            />
          )}

          {activeTab === 'logs' && (
            <AuditLogsTab logs={logs} />
          )}
        </div>
      </div>

      {/* 模态框 */}
      <RankingConfigModal
        open={showConfigModal}
        editingConfig={editingConfig}
        dimensions={dimensions}
        onClose={() => setShowConfigModal(false)}
        onSaved={reloadAll}
        onError={setError}
      />

      <DimensionModal
        open={showDimensionModal}
        editingDimension={editingDimension}
        onClose={() => setShowDimensionModal(false)}
        onSaved={reloadAll}
        onError={setError}
      />

      {selectedAppForConfig && (
        <AppSettingModal
          open={showAppSettingModal}
          app={selectedAppForConfig}
          allRankingConfigs={allRankingConfigs}
          dimensions={dimensions}
          editingSetting={editingAppSetting}
          existingSettings={appSettings[selectedAppForConfig.id] || []}
          onClose={() => { setShowAppSettingModal(false); setEditingAppSetting(null) }}
          onSaved={reloadAll}
          onError={setError}
        />
      )}
    </div>
  )
}

export default RankingManagementPage
