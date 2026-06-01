import { Link } from 'react-router-dom'
import type { AuthUser, Stats } from '../../types'
import UiIcon from '../../components/UiIcon'
import StatCard from '../../components/StatCard'
import { HomeView } from '../homeUtils'

interface HomeSidebarProps {
  rankingConfigs: Array<{ id: string; name: string }>
  activeNav: HomeView
  rankingType: string
  onNavChange: (nav: HomeView, type?: string) => void
  canAccessMySubmissions: boolean
  isAdmin: boolean
  currentUser: AuthUser | null
  stats: Stats
  statsLoading: boolean
  statsError: string | null
  onStatsRetry: () => void
}

export default function HomeSidebar({
  rankingConfigs,
  activeNav,
  rankingType,
  onNavChange,
  canAccessMySubmissions,
  isAdmin,
  currentUser,
  stats,
  statsLoading,
  statsError,
  onStatsRetry,
}: HomeSidebarProps) {
  return (
    <aside className="left">
      <div className="side-panel">
        <div className="side-section">
          <div className="nav-section-title">核心视图</div>
          {rankingConfigs.map((config) => (
            <button
              key={config.id}
              className={`nav-item ${activeNav === 'ranking' && rankingType === config.id ? 'active' : ''}`}
              onClick={() => onNavChange('ranking', config.id)}
            >
              <span className="nav-icon">
                {config.id === 'excellent' ? <UiIcon name="trophy" /> : config.id === 'trend' ? <UiIcon name="trend" /> : <UiIcon name="medal" />}
              </span>
              <span>{config.name}</span>
            </button>
          ))}
          <button
            className={`nav-item ${activeNav === 'library' ? 'active' : ''}`}
            onClick={() => onNavChange('library')}
          >
            <span className="nav-icon"><UiIcon name="platform" /></span>
            <span>应用视图</span>
          </button>
        </div>

        <div className="side-section">
          <div className="nav-section-title">常用功能</div>
          <Link to="/platform-intro" className="quick-link">
            <UiIcon name="platform" />
            <span>平台介绍</span>
          </Link>
          <Link to="/guide" className="quick-link">
            <UiIcon name="guide" />
            <span>申报指南</span>
          </Link>
          <Link to="/rule" className="quick-link">
            <UiIcon name="rule" />
            <span>榜单规则</span>
          </Link>
          <Link to="/historical-ranking" className="quick-link">
            <UiIcon name="history" />
            <span>历史榜单</span>
          </Link>
          {canAccessMySubmissions && (
            <Link to="/my-submissions" className="quick-link">
              <UiIcon name="my" />
              <span>我的申报</span>
            </Link>
          )}
          {isAdmin && (
            <Link to="/submission-review" className="quick-link">
              <UiIcon name="review" />
              <span>申报审核</span>
            </Link>
          )}
          {isAdmin && (
            <Link to="/ranking-management" className="quick-link">
              <UiIcon name="ranking" />
              <span>排行榜管理</span>
            </Link>
          )}
          {isAdmin && (
            <Link to="/user-management" className="quick-link">
              <UiIcon name="user" />
              <span>用户管理</span>
            </Link>
          )}
          {!currentUser && (
            <div className="quick-link-note">登录后可提交申报并查看我的申报</div>
          )}
        </div>

        <div className="side-section stats-panel">
          <div className="nav-section-title">申报统计</div>
          <div className="stats-grid">
            {statsLoading ? (
              <div className="stats-loading">
                <div className="loading-spinner"></div>
                <span>加载中...</span>
              </div>
            ) : statsError ? (
              <div className="stats-error">
                <span className="error-icon"><UiIcon name="error" /></span>
                <span>{statsError}</span>
                <button className="retry-button" onClick={onStatsRetry}>重试</button>
              </div>
            ) : (
              <>
                <StatCard label="待审核" value={stats.pending} valueClassName="pending" />
                <StatCard label="本期通过" value={stats.approved_period} valueClassName="approved" />
                <StatCard label="累计应用" value={stats.total_apps} valueClassName="total" />
              </>
            )}
          </div>
        </div>
      </div>
    </aside>
  )
}
