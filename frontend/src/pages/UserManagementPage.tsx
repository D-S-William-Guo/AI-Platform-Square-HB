import { useEffect, useMemo, useState } from 'react'
import {
  createAdminUser,
  fetchAdminUsers,
  updateAdminUser,
  updateAdminUserRole,
  updateAdminUserStatus,
  updateAdminUserSubmitPermission,
} from '../api/client'
import type { AdminUserCreatePayload, AuthUser, UserRole } from '../types'
import Pagination from '../components/Pagination'

const defaultForm: AdminUserCreatePayload = {
  username: '',
  chinese_name: '',
  company: '',
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
  const [activeTab, setActiveTab] = useState<'users' | 'create'>('users')
  const [keyword, setKeyword] = useState('')
  const [appliedKeyword, setAppliedKeyword] = useState('')
  const [loading, setLoading] = useState(true)
  const [savingUserId, setSavingUserId] = useState<number | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState<AdminUserCreatePayload>(defaultForm)
  const [editingUser, setEditingUser] = useState<AuthUser | null>(null)
  const [editFormData, setEditFormData] = useState({
    chinese_name: '',
    company: '',
    department: '',
    password: '',
    phone: '',
    email: '',
    role: 'user' as UserRole,
    is_active: true,
    can_submit: false,
  })
  const [creating, setCreating] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

  const loadUsers = async (options?: { q?: string; page?: number; pageSize?: number }) => {
    const nextPage = options?.page ?? page
    const nextPageSize = options?.pageSize ?? pageSize
    const nextQuery = options?.q ?? appliedKeyword
    setLoading(true)
    setError(null)
    try {
      const data = await fetchAdminUsers({
        ...(nextQuery ? { q: nextQuery } : {}),
        page: nextPage,
        page_size: nextPageSize,
      })
      setUsers(data.items)
      setTotal(data.total)
      setTotalPages(data.total_pages)
      if (data.total_pages > 0 && nextPage > data.total_pages) {
        setPage(data.total_pages)
      }
    } catch (err) {
      setError(resolveError(err, '加载用户列表失败'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [page, pageSize, appliedKeyword])

  const visibleSummary = useMemo(() => {
    const activeCount = users.filter((user) => user.is_active).length
    const submitEnabledCount = users.filter((user) => user.can_submit).length
    const adminCount = users.filter((user) => user.role === 'admin').length
    return { activeCount, submitEnabledCount, adminCount }
  }, [users])

  const applySearch = () => {
    setPage(1)
    setAppliedKeyword(keyword.trim())
  }

  const resetSearch = () => {
    setKeyword('')
    setAppliedKeyword('')
    setPage(1)
  }

  const handleCreateUser = async () => {
    if (!formData.username?.trim() || !formData.chinese_name?.trim() || !formData.company?.trim() || !formData.department?.trim()) {
      setError('请填写用户名、姓名、公司和部门')
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
        company: formData.company.trim(),
        department: formData.department.trim(),
        phone: formData.phone?.trim() || '',
        email: formData.email?.trim() || '',
        password: formData.password?.trim() || undefined,
      })
      setFormData(defaultForm)
      setActiveTab('users')
      setMessage('用户创建成功')
      await loadUsers({
        q: appliedKeyword,
        page,
        pageSize,
      })
    } catch (err) {
      setError(resolveError(err, '创建用户失败'))
    } finally {
      setCreating(false)
    }
  }

  const openEditUser = (user: AuthUser) => {
    setEditingUser(user)
    setEditFormData({
      chinese_name: user.chinese_name,
      company: user.company || '',
      department: user.department || '',
      password: '',
      phone: user.phone || '',
      email: user.email || '',
      role: user.role,
      is_active: user.is_active,
      can_submit: user.can_submit,
    })
    setError(null)
    setMessage(null)
  }

  const closeEditUser = () => {
    setEditingUser(null)
    setEditFormData({
      chinese_name: '',
      company: '',
      department: '',
      password: '',
      phone: '',
      email: '',
      role: 'user',
      is_active: true,
      can_submit: false,
    })
  }

  const handleUpdateUser = async () => {
    if (!editingUser) return
    if (!editFormData.chinese_name.trim() || !editFormData.company.trim() || !editFormData.department.trim()) {
      setError('请填写姓名、公司和部门')
      return
    }
    setUpdating(true)
    setError(null)
    setMessage(null)
    try {
      await updateAdminUser(editingUser.id, {
        chinese_name: editFormData.chinese_name.trim(),
        company: editFormData.company.trim(),
        department: editFormData.department.trim(),
        password: editFormData.password.trim() || undefined,
        phone: editFormData.phone.trim(),
        email: editFormData.email.trim(),
        role: editFormData.role,
        is_active: editFormData.is_active,
        can_submit: editFormData.can_submit,
      })
      closeEditUser()
      setMessage('用户信息已更新')
      await loadUsers({
        q: appliedKeyword,
        page,
        pageSize,
      })
    } catch (err) {
      setError(resolveError(err, '更新用户失败'))
    } finally {
      setUpdating(false)
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
      await loadUsers({
        q: appliedKeyword,
        page,
        pageSize,
      })
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

          <div className="user-management-summary">
            <div className="summary-card">
              <span className="summary-label">用户总数</span>
              <strong>{total}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">当前页启用账号</span>
              <strong>{visibleSummary.activeCount}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">当前页可申报</span>
              <strong>{visibleSummary.submitEnabledCount}</strong>
            </div>
            <div className="summary-card">
              <span className="summary-label">当前页管理员</span>
              <strong>{visibleSummary.adminCount}</strong>
            </div>
          </div>

          <div className="user-management-tabs">
            <button
              className={`user-management-tab ${activeTab === 'users' ? 'active' : ''}`}
              onClick={() => setActiveTab('users')}
            >
              <span>用户列表 / 权限管理</span>
            </button>
            <button
              className={`user-management-tab ${activeTab === 'create' ? 'active' : ''}`}
              onClick={() => setActiveTab('create')}
            >
              <span>新增用户</span>
            </button>
          </div>

          {message ? <div className="page-message success">{message}</div> : null}
          {error ? <div className="page-message error">{error}</div> : null}

          {activeTab === 'users' ? (
            <>
              <div className="user-management-toolbar">
                <div className="toolbar-search-group">
                  <input
                    className="search"
                    placeholder="搜索用户名、姓名、公司、部门..."
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        applySearch()
                      }
                    }}
                  />
                  <button className="secondary" onClick={applySearch} disabled={loading}>
                    搜索
                  </button>
                  <button className="ghost" onClick={resetSearch} disabled={loading}>
                    重置
                  </button>
                </div>
                <button className="secondary" onClick={() => loadUsers()} disabled={loading}>
                  刷新列表
                </button>
              </div>

              <div className="user-table-wrapper">
                {loading ? (
                  <div className="loading-container">用户列表加载中...</div>
                ) : (
                  <>
                    <table className="user-table">
                      <thead>
                        <tr>
                          <th>用户名</th>
                          <th>姓名</th>
                          <th>公司</th>
                          <th>部门</th>
                          <th>角色</th>
                          <th>启用</th>
                          <th>可申报</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.length === 0 ? (
                          <tr>
                            <td colSpan={8}>
                              <div className="table-empty-state">
                                <strong>没有匹配用户</strong>
                                <span>请尝试调整搜索条件，或者切换到“新增用户”页签创建一个测试账号。</span>
                              </div>
                            </td>
                          </tr>
                        ) : (
                          users.map((user) => (
                            <tr key={user.id}>
                              <td>
                                <div className="user-cell-primary">{user.username}</div>
                                <div className="user-cell-secondary">{user.email || '未填写邮箱'}</div>
                              </td>
                              <td>{user.chinese_name}</td>
                              <td>{user.company || '-'}</td>
                              <td>{user.department || '-'}</td>
                              <td>
                                <span className={`user-role-badge ${user.role}`}>{user.role === 'admin' ? '管理员' : '普通用户'}</span>
                              </td>
                              <td>
                                <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                                  {user.is_active ? '启用' : '停用'}
                                </span>
                              </td>
                              <td>
                                <span className={`status-badge ${user.can_submit ? 'active' : 'inactive'}`}>
                                  {user.can_submit ? '允许申报' : '仅浏览'}
                                </span>
                              </td>
                              <td>
                                <div className="table-actions">
                                  <button
                                    className="secondary"
                                    disabled={savingUserId === user.id}
                                    onClick={() => openEditUser(user)}
                                  >
                                    编辑
                                  </button>
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
                          ))
                        )}
                      </tbody>
                    </table>
                    <Pagination
                      page={page}
                      pageSize={pageSize}
                      total={total}
                      totalPages={totalPages}
                      disabled={loading}
                      onPageChange={setPage}
                      onPageSizeChange={(nextPageSize) => {
                        setPage(1)
                        setPageSize(nextPageSize)
                      }}
                    />
                  </>
                )}
              </div>
            </>
          ) : (
            <div className="user-create-card">
              <div className="card-header-row">
                <div>
                  <h3>新增用户</h3>
                  <p>测试阶段可通过本地账号快速发放访问权限，后续也可作为单点登录的兜底入口。</p>
                </div>
              </div>
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
                  placeholder="公司"
                  value={formData.company}
                  onChange={(e) => setFormData((prev) => ({ ...prev, company: e.target.value }))}
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
          )}
        </section>
      </div>

      {editingUser ? (
        <div className="modal-overlay" onClick={closeEditUser}>
          <div className="modal-container user-management-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">编辑用户</h3>
                <p className="modal-subtitle">更新用户基础资料、权限和可申报状态。历史申报和已生成应用归属不会随之改动。</p>
              </div>
              <button className="modal-close" onClick={closeEditUser}>×</button>
            </div>
            <div className="modal-body user-edit-grid">
              <div className="form-group">
                <label className="form-label">用户名</label>
                <input className="form-input" value={editingUser.username} readOnly />
              </div>
              <div className="form-group">
                <label className="form-label">姓名</label>
                <input
                  className="form-input"
                  value={editFormData.chinese_name}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, chinese_name: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">公司</label>
                <input
                  className="form-input"
                  value={editFormData.company}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, company: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">部门</label>
                <input
                  className="form-input"
                  value={editFormData.department}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, department: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">手机号</label>
                <input
                  className="form-input"
                  value={editFormData.phone}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, phone: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">邮箱</label>
                <input
                  className="form-input"
                  value={editFormData.email}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, email: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">重置密码（可选）</label>
                <input
                  className="form-input"
                  type="password"
                  placeholder="不填写则保持原密码"
                  value={editFormData.password}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, password: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <label className="form-label">角色</label>
                <select
                  className="form-select"
                  value={editFormData.role}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, role: e.target.value as UserRole }))}
                >
                  <option value="user">普通用户</option>
                  <option value="admin">管理员</option>
                </select>
              </div>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={editFormData.is_active}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, is_active: e.target.checked }))}
                />
                <span>启用账号</span>
              </label>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={editFormData.can_submit}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, can_submit: e.target.checked }))}
                />
                <span>允许申报</span>
              </label>
            </div>
            <div className="modal-footer">
              <button className="ghost" onClick={closeEditUser} disabled={updating}>取消</button>
              <button className="primary" onClick={handleUpdateUser} disabled={updating}>
                {updating ? '保存中...' : '保存修改'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default UserManagementPage
