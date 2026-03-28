import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { fetchAuthProviderInfo, login } from '../api/client'
import type { AuthProviderInfo, AuthUser } from '../types'

type LoginPageProps = {
  onLoginSuccess: (user: AuthUser) => void
}

export default function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const fromPath = useMemo(() => {
    const state = location.state as { from?: string } | null
    return state?.from && state.from !== '/login' ? state.from : '/'
  }, [location.state])

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [providerLoading, setProviderLoading] = useState(true)
  const [provider, setProvider] = useState<AuthProviderInfo | null>(null)

  useEffect(() => {
    let active = true
    setProviderLoading(true)
    fetchAuthProviderInfo()
      .then((data) => {
        if (active) {
          setProvider(data)
        }
      })
      .catch(() => {
        if (active) {
          setProvider(null)
        }
      })
      .finally(() => {
        if (active) {
          setProviderLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [])

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    if (provider && !provider.local_login_enabled) {
      setError('当前环境已切换到统一登录，请使用外部入口进入。')
      return
    }
    if (!username.trim() || !password.trim()) {
      setError('请输入用户名和密码')
      return
    }

    try {
      setSubmitting(true)
      const data = await login(username.trim(), password)
      onLoginSuccess(data.user)
      navigate(fromPath, { replace: true })
    } catch (err) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 401) {
        setError('用户名或密码错误')
      } else if (status === 403) {
        setError('当前用户不可用，请联系管理员')
      } else {
        setError('登录失败，请稍后重试')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const renderExternalProviderCard = () => {
    const loginUrl = provider?.login_url?.trim() ?? ''
    const message = provider?.message || '当前环境已切换到统一登录。'

    return (
      <div className="login-card">
        <h2>{provider?.display_name || '统一登录'}</h2>
        <p>{message}</p>
        {loginUrl ? (
          <a className="login-submit" href={loginUrl}>
            前往统一登录
          </a>
        ) : (
          <div className="login-error">统一登录入口尚未配置，请联系管理员。</div>
        )}
      </div>
    )
  }

  if (providerLoading) {
    return (
      <div className="page login-page">
        <div className="login-loading">登录方式加载中...</div>
      </div>
    )
  }

  return (
    <div className="page login-page">
      <div className="login-shell">
        <div className="login-brand-panel">
          <div className="brand-icon">河</div>
          <h1>HEBEI · AI 应用广场</h1>
          <p>
            {provider?.local_login_enabled
              ? '请先登录后访问应用首页、申报链路与排行榜能力。'
              : '当前环境已切换到统一登录入口，本地账号仅保留为兼容兜底能力。'}
          </p>
          {provider?.local_login_enabled ? (
            <div className="login-default-hint">
              <div>默认测试用户：zhangsan / lisi</div>
              <div>密码以服务端环境变量配置为准</div>
            </div>
          ) : null}
        </div>
        {provider?.local_login_enabled ? (
          <form className="login-card" onSubmit={onSubmit}>
            <h2>账号登录</h2>
            <label className="login-label">
              用户名
              <input
                className="login-input"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="请输入用户名"
                disabled={submitting}
              />
            </label>
            <label className="login-label">
              密码
              <input
                className="login-input"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入密码"
                disabled={submitting}
              />
            </label>
            {error ? <div className="login-error">{error}</div> : null}
            <button className="login-submit" type="submit" disabled={submitting}>
              {submitting ? '登录中...' : '登录'}
            </button>
          </form>
        ) : (
          renderExternalProviderCard()
        )}
      </div>
    </div>
  )
}
