import { useEffect, useState, useCallback } from 'react'
import { Navigate, Routes, Route, useLocation } from 'react-router-dom'
import {
  auditEvent,
  clearAuthToken,
  fetchAuthMe,
  logout,
  fetchMetaEnums,
} from './api/client'
import type { AuthUser, AppItem } from './types'
import HomePage from './pages/HomePage'
import GuidePage from './pages/GuidePage'
import RulePage from './pages/RulePage'
import PlatformIntroPage from './pages/PlatformIntroPage'
import RankingManagementPage from './pages/RankingManagementPage'
import SubmissionReviewPage from './pages/SubmissionReviewPage'
import MySubmissionsPage from './pages/MySubmissionsPage'
import HistoricalRankingPage from './pages/HistoricalRankingPage'
import RankingDetailPage from './pages/RankingDetailPage'
import LoginPage from './pages/LoginPage'
import ChangePasswordPage from './pages/ChangePasswordPage'
import UserManagementPage from './pages/UserManagementPage'

const DEFAULT_APP_CATEGORIES = ['前端市场类', '客户服务类', '云网运营类', '管理支撑类'] as const

function AuditRedirect({
  to,
  state,
  eventName,
  intent,
  returnTo,
  context,
}: {
  to: string
  state?: Record<string, unknown>
  eventName: string
  intent: 'submit' | 'admin'
  returnTo: string
  context: string
}) {
  useEffect(() => {
    auditEvent({
      event_name: eventName,
      intent,
      result: 'redirect_login',
      return_to: returnTo,
      context,
    })
  }, [eventName, intent, returnTo, context])

  return <Navigate to={to} replace state={state} />
}

// 主应用组件，包含路由配置
function App() {
  const location = useLocation()
  const [authLoading, setAuthLoading] = useState(true)
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [appCategories, setAppCategories] = useState<string[]>([])
  const [categoryOptionsLoading, setCategoryOptionsLoading] = useState(true)
  const [categoryOptionsError, setCategoryOptionsError] = useState<string | null>(null)

  const loadCurrentUser = useCallback(async () => {
    try {
      const me = await fetchAuthMe()
      setCurrentUser(me.user)
    } catch {
      clearAuthToken()
      setCurrentUser(null)
    } finally {
      setAuthLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCurrentUser()
  }, [loadCurrentUser])

  useEffect(() => {
    const loadMetaEnums = async () => {
      try {
        setCategoryOptionsLoading(true)
        setCategoryOptionsError(null)
        const data = await fetchMetaEnums()
        if (!Array.isArray(data.app_category) || data.app_category.length === 0) {
          throw new Error('category options empty')
        }
        setAppCategories(data.app_category)
      } catch (error) {
        console.error('Failed to fetch category options:', error)
        setAppCategories([])
        setCategoryOptionsError('分类配置加载失败，请稍后重试')
      } finally {
        setCategoryOptionsLoading(false)
      }
    }
    loadMetaEnums()
  }, [])

  const handleLogout = useCallback(async () => {
    await logout()
    setCurrentUser(null)
  }, [])

  const handleLoginSuccess = useCallback((user: AuthUser) => {
    setCurrentUser(user)
  }, [])

  const handlePasswordChanged = useCallback((user: AuthUser) => {
    setCurrentUser(user)
  }, [])

  if (authLoading) {
    return (
      <div className="page login-page">
        <div className="login-loading">登录状态校验中...</div>
      </div>
    )
  }

  if (currentUser?.must_change_password && location.pathname !== '/change-password') {
    const passwordChangeIntent = ['/ranking-management', '/submission-review', '/user-management'].includes(location.pathname)
      ? 'admin'
      : undefined
    return (
      <Navigate
        to="/change-password"
        replace
        state={{ returnTo: location.pathname, from: location.pathname, intent: passwordChangeIntent }}
      />
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage onLoginSuccess={handleLoginSuccess} />} />
      <Route
        path="/change-password"
        element={
          currentUser ? (
            <ChangePasswordPage currentUser={currentUser} onPasswordChanged={handlePasswordChanged} />
          ) : (
            <AuditRedirect
              to="/login"
              state={{ returnTo: '/change-password', from: location.pathname }}
              eventName="route.guard.redirect_login.submit"
              intent="submit"
              returnTo="/change-password"
              context="route.change_password.guard"
            />
          )
        }
      />
      <Route
        path="/"
        element={
          currentUser?.must_change_password ? (
            <Navigate to="/change-password" replace state={{ returnTo: '/', from: location.pathname }} />
          ) : (
          <HomePage
            currentUser={currentUser}
            onLogout={currentUser ? handleLogout : null}
            appCategories={appCategories}
            categoryOptionsLoading={categoryOptionsLoading}
            categoryOptionsError={categoryOptionsError}
          />
          )
        }
      />
      <Route path="/platform-intro" element={<PlatformIntroPage />} />
      <Route path="/guide" element={<GuidePage />} />
      <Route path="/rule" element={<RulePage />} />
      <Route
        path="/my-submissions"
        element={
          currentUser ? (
            currentUser.must_change_password ? (
              <Navigate to="/change-password" replace state={{ returnTo: '/my-submissions', from: location.pathname }} />
            ) : (
            <MySubmissionsPage />
            )
          ) : (
            <AuditRedirect
              to="/login"
              state={{ intent: 'submit', returnTo: '/my-submissions', from: location.pathname }}
              eventName="route.guard.redirect_login.submit"
              intent="submit"
              returnTo="/my-submissions"
              context="route.my_submissions.guard"
            />
          )
        }
      />
      <Route
        path="/ranking-management"
        element={
          currentUser ? (
            currentUser.must_change_password ? (
              <Navigate to="/change-password" replace state={{ returnTo: '/ranking-management', from: location.pathname, intent: 'admin' }} />
            ) :
            currentUser.role === 'admin' ? (
              <RankingManagementPage
                appCategories={appCategories}
                categoryOptionsLoading={categoryOptionsLoading}
                categoryOptionsError={categoryOptionsError}
                defaultAppCategory={appCategories[0] || DEFAULT_APP_CATEGORIES[0]}
              />
            ) : (
              <Navigate to="/" replace state={{ noAdminPermission: true }} />
            )
          ) : (
            <AuditRedirect
              to="/login"
              state={{ intent: 'admin', returnTo: '/ranking-management', from: location.pathname }}
              eventName="route.guard.redirect_login.admin"
              intent="admin"
              returnTo="/ranking-management"
              context="route.ranking_management.guard"
            />
          )
        }
      />
      <Route
        path="/submission-review"
        element={
          currentUser ? (
            currentUser.must_change_password ? (
              <Navigate to="/change-password" replace state={{ returnTo: '/submission-review', from: location.pathname, intent: 'admin' }} />
            ) :
            currentUser.role === 'admin' ? (
              <SubmissionReviewPage />
            ) : (
              <Navigate to="/" replace state={{ noAdminPermission: true }} />
            )
          ) : (
            <AuditRedirect
              to="/login"
              state={{ intent: 'admin', returnTo: '/submission-review', from: location.pathname }}
              eventName="route.guard.redirect_login.admin"
              intent="admin"
              returnTo="/submission-review"
              context="route.submission_review.guard"
            />
          )
        }
      />
      <Route
        path="/user-management"
        element={
          currentUser ? (
            currentUser.must_change_password ? (
              <Navigate to="/change-password" replace state={{ returnTo: '/user-management', from: location.pathname, intent: 'admin' }} />
            ) :
            currentUser.role === 'admin' ? (
              <UserManagementPage />
            ) : (
              <Navigate to="/" replace state={{ noAdminPermission: true }} />
            )
          ) : (
            <AuditRedirect
              to="/login"
              state={{ intent: 'admin', returnTo: '/user-management', from: location.pathname }}
              eventName="route.guard.redirect_login.admin"
              intent="admin"
              returnTo="/user-management"
              context="route.user_management.guard"
            />
          )
        }
      />
      <Route path="/historical-ranking" element={<HistoricalRankingPage />} />
      <Route path="/ranking/:configId" element={<RankingDetailPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
