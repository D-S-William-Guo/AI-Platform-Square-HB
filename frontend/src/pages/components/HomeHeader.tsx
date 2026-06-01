import { Link, useNavigate } from 'react-router-dom'
import { auditEvent } from '../../api/client'
import type { AuthUser } from '../../types'
import UiIcon from '../../components/UiIcon'
import { createSubmissionDraft } from '../homeUtils'

interface HomeHeaderProps {
  currentUser: AuthUser | null
  onLogout: (() => Promise<void>) | null
  canAccessMySubmissions: boolean
  isAdmin: boolean
  keyword: string
  onKeywordChange: (value: string) => void
  submissionCategoryUnavailable: boolean
  categoryOptionsError: string | null
  categoryOptionsLoading: boolean
  defaultCategory: string
  onOpenSubmission: () => void
}

export default function HomeHeader({
  currentUser,
  onLogout,
  canAccessMySubmissions,
  isAdmin,
  keyword,
  onKeywordChange,
  submissionCategoryUnavailable,
  categoryOptionsError,
  categoryOptionsLoading,
  defaultCategory,
  onOpenSubmission,
}: HomeHeaderProps) {
  const navigate = useNavigate()

  const handleSubmitClick = () => {
    if (!currentUser) {
      auditEvent({
        event_name: 'auth.intent.submit.click',
        intent: 'submit',
        result: 'redirect_login',
        return_to: '/',
        context: 'home.header.submit_button',
      })
      navigate('/login', { state: { intent: 'submit', returnTo: '/' } })
      return
    }
    onOpenSubmission()
  }

  return (
    <header className="header">
      <div className="brand">
        <div className="brand-icon">河</div>
        <span>HEBEI · AI 应用广场</span>
      </div>
      <div className="search-wrapper">
        <span className="search-icon"><UiIcon name="search" size={14} /></span>
        <input
          className="search"
          placeholder="搜索应用名称..."
          value={keyword}
          onChange={(e) => onKeywordChange(e.target.value)}
        />
      </div>
      <div className="header-actions">
        <Link to="/platform-intro" className="secondary">
          <UiIcon name="platform" />
          <span>平台介绍</span>
        </Link>
        {canAccessMySubmissions && (
          <Link to="/my-submissions" className="secondary">
            <UiIcon name="my" />
            <span>我的申报</span>
          </Link>
        )}
        <button
          className="primary"
          onClick={handleSubmitClick}
          disabled={Boolean(currentUser) && submissionCategoryUnavailable}
          title={categoryOptionsError || (categoryOptionsLoading ? '分类配置加载中' : undefined)}
        >
          <span>+</span>
          <span>我要申报</span>
        </button>
        {!currentUser && (
          <button
            className="secondary"
            onClick={() => {
              auditEvent({
                event_name: 'auth.intent.admin.click',
                intent: 'admin',
                result: 'redirect_login',
                return_to: '/ranking-management',
                context: 'home.header.admin_login',
              })
              navigate('/login', { state: { intent: 'admin', returnTo: '/ranking-management' } })
            }}
          >
            <span>管理员登录</span>
          </button>
        )}
        {currentUser && onLogout && (
          <>
            <button className="secondary" onClick={onLogout}>
              <span>退出登录</span>
            </button>
            <button
              className="secondary"
              onClick={() => navigate('/change-password', { state: { returnTo: '/' } })}
            >
              <span>修改密码</span>
            </button>
            <div className="avatar" title={`${currentUser.chinese_name} (${currentUser.role === 'admin' ? '管理员' : '普通用户'})`}>
              {(currentUser.chinese_name || currentUser.username).slice(0, 1)}
            </div>
          </>
        )}
      </div>
    </header>
  )
}
