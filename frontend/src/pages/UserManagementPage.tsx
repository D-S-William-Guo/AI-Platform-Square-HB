import { useEffect, useMemo, useState } from 'react'
import {
  createAdminUser,
  fetchAdminUsers,
  updateAdminUserRole,
  updateAdminUserStatus,
  updateAdminUserSubmitPermission,
} from '../api/client'
import type { AdminUserCreatePayload, AuthUser, UserRole } from '../types'

const defaultForm: AdminUserCreatePayload = {
  username: '',
  chinese_name: '',
  department: '',
  password: '',
  phone: '',
  email: '',
  role: 'user',
  is_active: true,
  can_submit: false,
}

function resolveError(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  return fallback
}

const UserManagementPage = () => {
  const [users, setUsers] = useState<AuthUser[]>([])
  const [keyword, setKeyword] = useState('')
  const [loading, setLoading] = useState(true)
  const [savingUserId, setSavingUserId] = useState<number | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState<AdminUserCreatePayload>(defaultForm)
  const [creating, setCreating] = useState(false)

  const loadUsers = async (q?: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchAdminUsers(q ? { q } : undefined)
      setUsers(data)
    } catch (err) {
      setError(resolveError(err, '加载用户列表失败'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const filteredUsers = useMemo(() => {
    const normalized = keyword.trim().toLowerCase()
    if (!normalized) return users
    return users.filter((user) =>
      [user.username, user.chinese_name, user.department, user.email]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(normalized))
    )
  }, [users, keyword])

  const handleCreateUser = async () => {
    if (!formData.username?.trim() || !formData.chinese_name?.trim() || !formData.department?.trim()) {
      setError('请填写用户名、姓名和部门')
      return
    }
    setCreating(true)
    setError(null)
    setMessage(null)
    try {
      await createAdminUser({
        ...formData,
        username: formData.username.trim(),
        chinese_name: formData.chinese_name.trim(),
        department: formData.department.trim(),
        phone: formData.phone?.trim() || '',
        email: formData.email?.trim() || '',
        password: formData.password?.trim() || undefined,
      })
      setFormData(defaultForm)
      setMessage('用户创建成功')
      await loadUsers(keyword.trim() || undefined)
    } catch (err) {
      setError(resolveError(err, '创建用户失败'))
    } finally {
      setCreating(false)
    }
  }

  const mutateUser = async (
    userId: number,
    runner: () => Promise<unknown>,
    successMessage: string,
  ) => {
    setSavingUserId(userId)
    setError(null)
    setMessage(null)
    try {
      await runner()
      setMessage(successMessage)
      await loadUsers(keyword.trim() || undefined)
    } catch (err) {
      setError(resolveError(err, '保存失败'))
    } finally {
      setSavingUserId(null)
    }
  }

  return (
    <div className="page user-management-page">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
        <div className="header-actions">
          <button className="primary" onClick={() => window.history.back()}>
            返回首页
          </button>
        </div>
      </header>

      <div className="body user-management-body">
        <section className="user-management-panel">
          <div className="panel-header">
            <div>
              <h2>用户管理</h2>
              <p>管理员可创建测试账号，并配置哪些用户具备应用申报权限。</p>
            </div>
          </div>

          <div className="user-management-toolbar">
            <input
              className="search"
              placeholder="搜索用户名、姓名、部门..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
            <button className="secondary" onClick={() => loadUsers(keyword.trim() || undefined)} disabled={loading}>
              刷新
            </button>
          </div>

          {message ? <div className="page-message success">{message}</div> : null}
          {error ? <div className="page-message error">{error}</div> : null}

          <div className="user-create-card">
            <h3>新增用户</h3>
            <div className="user-create-grid">
              <input
                className="form-input"
                placeholder="用户名"
                value={formData.username}
                onChange={(e) => setFormData((prev) => ({ ...prev, username: e.target.value }))}
              />
              <input
                className="form-input"
                placeholder="姓名"
                value={formData.chinese_name}
                onChange={(e) => setFormData((prev) => ({ ...prev, chinese_name: e.target.value }))}
              />
              <input
                className="form-input"
                placeholder="部门"
                value={formData.department}
                onChange={(e) => setFormData((prev) => ({ ...prev, department: e.target.value }))}
              />
              <input
                className="form-input"
                placeholder="手机号（可选）"
                value={formData.phone}
                onChange={(e) => setFormData((prev) => ({ ...prev, phone: e.target.value }))}
              />
              <input
                className="form-input"
                placeholder="邮箱（可选）"
                value={formData.email}
                onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
              />
              <input
                className="form-input"
                placeholder="初始密码（可选，不填则用默认密码）"
                value={formData.password}
                onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
              />
              <select
                className="form-select"
                value={formData.role}
                onChange={(e) => setFormData((prev) => ({ ...prev, role: e.target.value as UserRole }))}
              >
                <option value="user">普通用户</option>
                <option value="admin">管理员</option>
              </select>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={Boolean(formData.is_active)}
                  onChange={(e) => setFormData((prev) => ({ ...prev, is_active: e.target.checked }))}
                />
                <span>启用账号</span>
              </label>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={Boolean(formData.can_submit)}
                  onChange={(e) => setFormData((prev) => ({ ...prev, can_submit: e.target.checked }))}
                />
                <span>允许申报</span>
              </label>
            </div>
            <div className="panel-actions">
              <button className="primary" onClick={handleCreateUser} disabled={creating}>
                {creating ? '创建中...' : '新增用户'}
              </button>
            </div>
          </div>

          <div className="user-table-wrapper">
            {loading ? (
              <div className="loading-container">用户列表加载中...</div>
            ) : (
              <table className="user-table">
                <thead>
                  <tr>
                    <th>用户名</th>
                    <th>姓名</th>
                    <th>部门</th>
                    <th>角色</th>
                    <th>启用</th>
                    <th>可申报</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id}>
                      <td>{user.username}</td>
                      <td>{user.chinese_name}</td>
                      <td>{user.department || '-'}</td>
                      <td>{user.role === 'admin' ? '管理员' : '普通用户'}</td>
                      <td>{user.is_active ? '是' : '否'}</td>
                      <td>{user.can_submit ? '是' : '否'}</td>
                      <td>
                        <div className="table-actions">
                          <button
                            className="secondary"
                            disabled={savingUserId === user.id}
                            onClick={() =>
                              mutateUser(
                                user.id,
                                () => updateAdminUserSubmitPermission(user.id, !user.can_submit),
                                user.can_submit ? '已关闭申报权限' : '已开启申报权限',
                              )
                            }
                          >
                            {user.can_submit ? '关闭申报' : '开启申报'}
                          </button>
                          <button
                            className="secondary"
                            disabled={savingUserId === user.id}
                            onClick={() =>
                              mutateUser(
                                user.id,
                                () => updateAdminUserStatus(user.id, !user.is_active),
                                user.is_active ? '已禁用账号' : '已启用账号',
                              )
                            }
                          >
                            {user.is_active ? '禁用' : '启用'}
                          </button>
                          <button
                            className="secondary"
                            disabled={savingUserId === user.id}
                            onClick={() =>
                              mutateUser(
                                user.id,
                                () => updateAdminUserRole(user.id, user.role === 'admin' ? 'user' : 'admin'),
                                user.role === 'admin' ? '已降为普通用户' : '已提升为管理员',
                              )
                            }
                          >
                            {user.role === 'admin' ? '降级管理员' : '设为管理员'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default UserManagementPage
