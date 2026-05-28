import { FormEvent, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { changePassword } from '../api/client'
import type { AuthUser } from '../types'

type ChangePasswordPageProps = {
  currentUser: AuthUser
  onPasswordChanged: (user: AuthUser) => void
}

function resolveError(err: unknown): string {
  const response = (err as { response?: { status?: number; data?: { detail?: unknown } } })?.response
  const detail = response?.data?.detail
  if (typeof detail === 'string') return detail
  if (response?.status === 401) return '当前密码错误'
  return '修改密码失败，请稍后重试'
}

export default function ChangePasswordPage({ currentUser, onPasswordChanged }: ChangePasswordPageProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { returnTo?: string; intent?: 'submit' | 'admin' } | null
  const returnTo = useMemo(() => {
    if (state?.returnTo && state.returnTo !== '/login' && state.returnTo !== '/change-password') {
      return state.returnTo
    }
    return '/'
  }, [state?.returnTo])
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pageIntro = currentUser.must_change_password
    ? '请先设置个人强口令后继续使用系统。'
    : '你可以在这里修改当前账号密码。'

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('请填写当前密码、新密码和确认密码')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('两次输入的新密码不一致')
      return
    }

    try {
      setSubmitting(true)
      const data = await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      onPasswordChanged(data.user)
      if (state?.intent === 'submit') {
        navigate(returnTo, { replace: true, state: { openSubmission: true } })
        return
      }
      navigate(returnTo, { replace: true })
    } catch (err) {
      setError(resolveError(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page login-page">
      <div className="login-shell">
        <div className="login-brand-panel">
          <h1>修改密码</h1>
          <p>{currentUser.chinese_name || currentUser.username}，{pageIntro}</p>
          <div className="login-default-hint">
            密码至少10位，且需包含大写字母、小写字母、数字、符号中的至少三类。
          </div>
        </div>
        <form className="login-card" onSubmit={onSubmit}>
          <h2>设置新密码</h2>
          <label className="login-label">
            当前密码
            <input
              className="login-input"
              type="password"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
          </label>
          <label className="login-label">
            新密码
            <input
              className="login-input"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
          </label>
          <label className="login-label">
            确认新密码
            <input
              className="login-input"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
            />
          </label>
          {error ? <div className="login-error">{error}</div> : null}
          <button className="login-submit" type="submit" disabled={submitting}>
            {submitting ? '提交中...' : '确认修改'}
          </button>
        </form>
      </div>
    </div>
  )
}
