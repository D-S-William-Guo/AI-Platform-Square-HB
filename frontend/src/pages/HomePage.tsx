import { useEffect, useMemo, useState, useCallback } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  auditEvent,
  fetchApps,
  fetchHistoricalRankings,
  fetchStats,
  fetchRankingDimensions,
  fetchDimensionScores,
  fetchRankingConfigs,
} from '../api/client'
import type { AppItem, AuthUser, RankingItem, Stats, RankingDimension } from '../types'
import {
  appSourceOptions,
  enrichHistoricalRankingApps,
  rankingItemFromHistorical,
  appCompanyLabel,
  statusOptions,
  type HomeView,
  type AppSource,
} from './homeUtils'
import HomeHeader from './components/HomeHeader'
import HomeSidebar from './components/HomeSidebar'
import AppGrid from './components/AppGrid'
import RankingList from './components/RankingList'
import AppDetailModal from './components/AppDetailModal'
import SubmissionModal from './components/SubmissionModal'

// 主页面组件
function HomePage({
  currentUser,
  onLogout,
  appCategories,
  categoryOptionsLoading,
  categoryOptionsError,
}: {
  currentUser: AuthUser | null
  onLogout: (() => Promise<void>) | null
  appCategories: string[]
  categoryOptionsLoading: boolean
  categoryOptionsError: string | null
}) {
  const navigate = useNavigate()
  const location = useLocation()
  const routeState = (location.state || {}) as {
    noAdminPermission?: boolean
    openSubmission?: boolean
  }
  const canUseSubmission = Boolean(currentUser)
  const canAccessMySubmissions = Boolean(currentUser)
  const isAdmin = currentUser?.role === 'admin'
  const defaultCategory = appCategories[0] || ''
  const categories = useMemo(() => ['全部', ...appCategories], [appCategories])
  const submissionCategoryUnavailable =
    categoryOptionsLoading || Boolean(categoryOptionsError) || appCategories.length === 0

  const [activeNav, setActiveNav] = useState<HomeView>('ranking')
  const [appSource, setAppSource] = useState<AppSource>('all')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('全部')
  const [companyFilter, setCompanyFilter] = useState<string>('全部')
  const [keyword, setKeyword] = useState('')
  const [apps, setApps] = useState<AppItem[]>([])
  const [rankings, setRankings] = useState<RankingItem[]>([])
  const [rankingCompanyOptions, setRankingCompanyOptions] = useState<string[]>(['全部'])
  const [rankingLoading, setRankingLoading] = useState(false)
  const [rankingError, setRankingError] = useState<string | null>(null)
  const [rankingPublishedDate, setRankingPublishedDate] = useState<string>('')
  const [rankingType, setRankingType] = useState<string>('excellent')
  const [rankingDimension, setRankingDimension] = useState<string>('overall')
  const [rankingDimensions, setRankingDimensions] = useState<RankingDimension[]>([])
  const [rankingConfigs, setRankingConfigs] = useState<any[]>([])
  const [stats, setStats] = useState<Stats>({ pending: 12, approved_period: 7, total_apps: 86 })
  const [statsLoading, setStatsLoading] = useState(true)
  const [statsError, setStatsError] = useState<string | null>(null)
  const [selectedApp, setSelectedApp] = useState<AppItem | null>(null)
  const [showSubmission, setShowSubmission] = useState(false)

  const companyOptions = useMemo(() => {
    if (activeNav === 'ranking') return rankingCompanyOptions

    const values =
      apps
        .filter((app) => app.section === 'province')
        .map(appCompanyLabel)
        .filter(Boolean)
    return ['全部', ...Array.from(new Set(values))]
  }, [activeNav, apps, rankingCompanyOptions])

  // 加载榜单维度、配置、统计数据
  useEffect(() => {
    fetchRankingDimensions()
      .then((data) => setRankingDimensions(data.filter((item) => item.is_active)))
      .catch((error) => console.error('Failed to fetch ranking dimensions:', error))

    fetchRankingConfigs(true)
      .then((data) => setRankingConfigs(data))
      .catch((error) => console.error('Failed to fetch ranking configs:', error))

    const loadStats = async () => {
      try {
        setStatsLoading(true)
        setStatsError(null)
        const data = await fetchStats()
        setStats(data)
      } catch (error) {
        console.error('Failed to fetch stats:', error)
        setStatsError('获取统计数据失败')
      } finally {
        setStatsLoading(false)
      }
    }

    loadStats()
  }, [])

  // 自动打开申报弹窗
  useEffect(() => {
    if (!routeState.openSubmission) return
    if (!currentUser) return
    if (!canUseSubmission) return
    setShowSubmission(true)
    auditEvent({
      event_name: 'submission.modal.auto_open',
      intent: 'submit',
      result: 'success',
      return_to: '/',
      context: 'home.route_state.open_submission',
    })
  }, [routeState.openSubmission, currentUser, canUseSubmission])

  // 无权限提示
  useEffect(() => {
    if (!routeState.noAdminPermission) return
    auditEvent({
      event_name: 'route.guard.denied_admin',
      intent: 'admin',
      result: 'denied_role',
      return_to: location.pathname,
      context: 'home.route_state.no_admin_permission',
    })
  }, [routeState.noAdminPermission, location.pathname])

  // 切换appSource时重置companyFilter
  useEffect(() => {
    if (appSource === 'group' && companyFilter !== '全部') {
      setCompanyFilter('全部')
    }
  }, [appSource, companyFilter])

  // 加载榜单/应用数据
  useEffect(() => {
    if (activeNav === 'ranking') {
      const loadPublishedRankings = async () => {
        try {
          setRankingLoading(true)
          setRankingError(null)
          const snapshot = await fetchHistoricalRankings(rankingType as 'excellent' | 'trend')
          const appDetailMap = await enrichHistoricalRankingApps(snapshot)
          let processedRankings = snapshot.map((row) =>
            rankingItemFromHistorical(row, appDetailMap.get(row.app_id))
          )
          const latestDate = snapshot[0]?.period_date || ''
          setRankingPublishedDate(latestDate)
          setRankingCompanyOptions([
            '全部',
            ...Array.from(new Set(processedRankings.map((row) => appCompanyLabel(row.app)).filter(Boolean))),
          ])

          if (companyFilter !== '全部') {
            processedRankings = processedRankings.filter((row) => appCompanyLabel(row.app) === companyFilter)
          }

          if (rankingDimension !== 'overall' && latestDate) {
            const dimensionId = parseInt(rankingDimension.replace('dimension-', ''))
            if (!isNaN(dimensionId)) {
              try {
                const dimensionScores = await fetchDimensionScores(dimensionId, latestDate, rankingType)
                const scoreMap = new Map(dimensionScores.map(ds => [ds.app_id, ds.score]))
                processedRankings = processedRankings.map(row => ({
                  ...row,
                  dimensionScore: scoreMap.get(row.app.id) || 0
                }))
                processedRankings.sort((a, b) => (b.dimensionScore || 0) - (a.dimensionScore || 0))
                processedRankings = processedRankings.map((row, index) => ({
                  ...row,
                  position: index + 1
                }))
              } catch (error) {
                console.error('Failed to fetch dimension scores:', error)
              }
            }
          }

          if (keyword.trim()) {
            processedRankings = processedRankings.filter((row) =>
              row.app.name.toLowerCase().includes(keyword.toLowerCase())
            )
          }

          setRankings(processedRankings)
        } catch (error) {
          console.error('Failed to fetch published rankings:', error)
          setRankingError('获取最新发布榜单失败')
          setRankings([])
          setRankingPublishedDate('')
          setRankingCompanyOptions(['全部'])
        } finally {
          setRankingLoading(false)
        }
      }

      loadPublishedRankings()
      return
    }

    // 加载应用视图
    const params: Record<string, string> = {}
    if (appSource !== 'all') params.section = appSource
    if (statusFilter) params.status = statusFilter
    if (categoryFilter && categoryFilter !== '全部') params.category = categoryFilter
    if (appSource !== 'group' && companyFilter !== '全部') params.company = companyFilter
    if (keyword) params.q = keyword

    fetchApps(params).then((data) => {
      if (keyword.trim()) {
        const filtered = data.filter((app) =>
          app.name.toLowerCase().includes(keyword.toLowerCase())
        )
        setApps(filtered)
      } else {
        setApps(data)
      }
    })
  }, [activeNav, appSource, statusFilter, categoryFilter, companyFilter, keyword, rankingType, rankingDimension])

  const blockTitle = useMemo(() => {
    if (activeNav === 'library') return 'AI 应用视图'
    return 'AI 应用龙虎榜'
  }, [activeNav])

  const blockSubtitle = useMemo(() => {
    if (activeNav === 'library') return '统一展示集团应用与省内应用，支持按来源、分类、单位和关键词检索'
    return '展示省内应用总榜与增长趋势榜，帮助运营发现值得推广的 AI 应用'
  }, [activeNav])

  const handleOpenSubmission = useCallback(() => {
    setShowSubmission(true)
  }, [])

  const handleCloseSubmission = useCallback(() => {
    setShowSubmission(false)
  }, [])

  const handleNavChange = useCallback((nav: HomeView, type?: string) => {
    setActiveNav(nav)
    if (type) setRankingType(type)
  }, [])

  const handleStatsRetry = useCallback(async () => {
    try {
      setStatsLoading(true)
      setStatsError(null)
      const data = await fetchStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      setStatsError('获取统计数据失败')
    } finally {
      setStatsLoading(false)
    }
  }, [])

  return (
    <div className="page home-page">
      <HomeHeader
        currentUser={currentUser}
        onLogout={onLogout}
        canAccessMySubmissions={canAccessMySubmissions}
        isAdmin={isAdmin}
        keyword={keyword}
        onKeywordChange={setKeyword}
        submissionCategoryUnavailable={submissionCategoryUnavailable}
        categoryOptionsError={categoryOptionsError}
        categoryOptionsLoading={categoryOptionsLoading}
        defaultCategory={defaultCategory}
        onOpenSubmission={handleOpenSubmission}
      />

      <div className="body">
        <HomeSidebar
          rankingConfigs={rankingConfigs}
          activeNav={activeNav}
          rankingType={rankingType}
          onNavChange={handleNavChange}
          canAccessMySubmissions={canAccessMySubmissions}
          isAdmin={isAdmin}
          currentUser={currentUser}
          stats={stats}
          statsLoading={statsLoading}
          statsError={statsError}
          onStatsRetry={handleStatsRetry}
        />

        <main className="main">
          <section className="block-header">
            <div>
              <h2 className="block-title">{blockTitle}</h2>
              <p className="block-subtitle">{blockSubtitle}</p>
              {activeNav === 'ranking' && rankingPublishedDate && (
                <p className="block-hint">最新发布：{rankingPublishedDate}</p>
              )}
              {activeNav === 'library' && (
                <p className="block-hint">集团应用和省内应用均为展示内容，可通过应用来源筛选查看，不提供平台内跳转使用。</p>
              )}
            </div>
            {activeNav === 'library' && (
              <div className="filters">
                <select
                  className="filter-select"
                  value={appSource}
                  onChange={(e) => setAppSource(e.target.value as AppSource)}
                >
                  {appSourceOptions.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
                <select
                  className="filter-select"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  {statusOptions.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
                <select
                  className="filter-select"
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  {categories.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
                {appSource !== 'group' && (
                  <select
                    className="filter-select"
                    value={companyFilter}
                    onChange={(e) => setCompanyFilter(e.target.value)}
                  >
                    {companyOptions.map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                )}
              </div>
            )}
            {activeNav === 'ranking' && (
              <div className="filters">
                <div className="filter-group">
                  <button
                    className={`filter-btn ${rankingType === 'excellent' ? 'active' : ''}`}
                    onClick={() => setRankingType('excellent')}
                  >
                    总应用榜
                  </button>
                  <button
                    className={`filter-btn ${rankingType === 'trend' ? 'active' : ''}`}
                    onClick={() => setRankingType('trend')}
                  >
                    增长趋势榜
                  </button>
                </div>
                <div className="filter-group">
                  <span className="filter-label">排行维度：</span>
                  <select
                    className="filter-select"
                    value={rankingDimension}
                    onChange={(e) => setRankingDimension(e.target.value)}
                  >
                    <option value="overall">综合排名</option>
                    {rankingDimensions.map((dimension) => (
                      <option key={dimension.id} value={`dimension-${dimension.id}`}>
                        {dimension.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="filter-group">
                  <span className="filter-label">公司：</span>
                  <select
                    className="filter-select"
                    value={companyFilter}
                    onChange={(e) => setCompanyFilter(e.target.value)}
                  >
                    {companyOptions.map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </section>

          {activeNav === 'library' && (
            <AppGrid apps={apps} onAppClick={setSelectedApp} />
          )}

          {activeNav === 'ranking' && (
            <RankingList
              rankings={rankings}
              loading={rankingLoading}
              error={rankingError}
              isAdmin={isAdmin}
              rankingDimension={rankingDimension}
              onAppClick={setSelectedApp}
            />
          )}
        </main>
      </div>

      <footer className="footer">
        <div>最近更新时间：2026-04-18 · 联系邮箱：aiapps@chinatelecom.cn</div>
        <div style={{ marginTop: '4px', fontSize: '12px' }}>数据来源于省公司各单位申报与集团应用目录</div>
      </footer>

      <AppDetailModal app={selectedApp} onClose={() => setSelectedApp(null)} />

      <SubmissionModal
        open={showSubmission}
        onClose={handleCloseSubmission}
        currentUser={currentUser}
        appCategories={appCategories}
        defaultCategory={defaultCategory}
        submissionCategoryUnavailable={submissionCategoryUnavailable}
        categoryOptionsError={categoryOptionsError}
      />

      {routeState.noAdminPermission && (
        <div className="route-permission-banner">当前账号不是管理员，无法访问管理功能。</div>
      )}
    </div>
  )
}

export default HomePage
