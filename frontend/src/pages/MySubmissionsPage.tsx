import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchMySubmissions, updateMySubmission, withdrawMySubmission } from '../api/client'
import type { Submission, SubmissionPayload, ValueDimension } from '../types'

const defaultForm: SubmissionPayload = {
  app_name: '',
  unit_name: '',
  contact: '',
  contact_phone: '',
  contact_email: '',
  category: '办公类',
  scenario: '',
  embedded_system: '',
  problem_statement: '',
  effectiveness_type: 'efficiency_gain',
  effectiveness_metric: '',
  data_level: 'L2',
  expected_benefit: '',
  cover_image_url: '',
  detail_doc_url: '',
  detail_doc_name: '',
}

const statusLabel: Record<Submission['status'], string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝',
  withdrawn: '已撤回',
}

const valueDimensionLabel: Record<ValueDimension, string> = {
  cost_reduction: '降本',
  efficiency_gain: '增效',
  perception_uplift: '感知提升',
  revenue_growth: '拉动收入',
}

export default function MySubmissionsPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [activeFilter, setActiveFilter] = useState<'all' | Submission['status']>('all')
  const [editing, setEditing] = useState<Submission | null>(null)
  const [form, setForm] = useState<SubmissionPayload>(defaultForm)

  const loadMySubmissions = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchMySubmissions()
      setSubmissions(data)
    } catch (err) {
      console.error('Failed to fetch my submissions:', err)
      setError('获取我的申报失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMySubmissions()
  }, [loadMySubmissions])

  const filtered = useMemo(() => {
    if (activeFilter === 'all') return submissions
    return submissions.filter((item) => item.status === activeFilter)
  }, [submissions, activeFilter])

  function openEdit(target: Submission) {
    if (target.status !== 'pending') {
      return
    }
    setEditing(target)
    setForm({
      app_name: target.app_name,
      unit_name: target.unit_name,
      contact: target.contact,
      contact_phone: target.contact_phone,
      contact_email: target.contact_email,
      category: target.category,
      scenario: target.scenario,
      embedded_system: target.embedded_system,
      problem_statement: target.problem_statement,
      effectiveness_type: target.effectiveness_type,
      effectiveness_metric: target.effectiveness_metric,
      data_level: target.data_level,
      expected_benefit: target.expected_benefit,
      cover_image_url: target.cover_image_url || '',
      detail_doc_url: target.detail_doc_url || '',
      detail_doc_name: target.detail_doc_name || '',
    })
  }

  async function onSave() {
    if (!editing) return
    try {
      setSaving(true)
      await updateMySubmission(editing.id, form)
      setEditing(null)
      await loadMySubmissions()
    } catch (err) {
      console.error('Failed to update submission:', err)
      alert('保存失败，请稍后重试')
    } finally {
      setSaving(false)
    }
  }

  async function onWithdraw(target: Submission) {
    if (target.status !== 'pending') return
    if (!confirm('确认撤回该申报吗？')) {
      return
    }
    try {
      setSaving(true)
      await withdrawMySubmission(target.id)
      await loadMySubmissions()
    } catch (err) {
      console.error('Failed to withdraw submission:', err)
      alert('撤回失败，请稍后重试')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page my-submissions-page">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
        <div className="header-actions">
          <Link to="/" className="primary">
            <span>←</span>
            <span>返回首页</span>
          </Link>
        </div>
      </header>

      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">我的申报</h1>
          <p className="page-subtitle">查看本人申报状态，并对待审核记录进行修改或撤回</p>
        </div>

        <div className="filter-bar">
          <button className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`} onClick={() => setActiveFilter('all')}>
            全部 ({submissions.length})
          </button>
          <button className={`filter-btn ${activeFilter === 'pending' ? 'active' : ''}`} onClick={() => setActiveFilter('pending')}>
            待审核 ({submissions.filter((item) => item.status === 'pending').length})
          </button>
          <button className={`filter-btn ${activeFilter === 'approved' ? 'active' : ''}`} onClick={() => setActiveFilter('approved')}>
            已通过 ({submissions.filter((item) => item.status === 'approved').length})
          </button>
          <button className={`filter-btn ${activeFilter === 'rejected' ? 'active' : ''}`} onClick={() => setActiveFilter('rejected')}>
            已拒绝 ({submissions.filter((item) => item.status === 'rejected').length})
          </button>
          <button className={`filter-btn ${activeFilter === 'withdrawn' ? 'active' : ''}`} onClick={() => setActiveFilter('withdrawn')}>
            已撤回 ({submissions.filter((item) => item.status === 'withdrawn').length})
          </button>
        </div>

        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <span>加载中...</span>
          </div>
        ) : error ? (
          <div className="error-container">{error}</div>
        ) : filtered.length === 0 ? (
          <div className="empty-container">暂无申报记录</div>
        ) : (
          <div className="submission-list">
            {filtered.map((item) => (
              <article key={item.id} className={`submission-card ${item.status}`}>
                <div className="submission-header">
                  <h3>{item.app_name}</h3>
                  <span className={`status-chip ${item.status}`}>{statusLabel[item.status]}</span>
                </div>
                <div className="submission-meta">
                  <span>申报单位：{item.unit_name}</span>
                  <span>成效类型：{valueDimensionLabel[item.effectiveness_type]}</span>
                  <span>提交时间：{new Date(item.created_at).toLocaleString()}</span>
                </div>
                {item.status === 'rejected' && item.rejected_reason ? (
                  <div className="rejected-reason">拒绝原因：{item.rejected_reason}</div>
                ) : null}
                <div className="submission-actions">
                  <button
                    className="secondary"
                    onClick={() => openEdit(item)}
                    disabled={item.status !== 'pending' || saving}
                  >
                    修改
                  </button>
                  <button
                    className="secondary"
                    onClick={() => onWithdraw(item)}
                    disabled={item.status !== 'pending' || saving}
                  >
                    撤回
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal-container my-submission-edit" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">修改申报</h3>
              <button className="modal-close" onClick={() => setEditing(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-section">
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">应用名称</label>
                    <input className="form-input" value={form.app_name} onChange={(e) => setForm((prev) => ({ ...prev, app_name: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">申报单位</label>
                    <input className="form-input" value={form.unit_name} onChange={(e) => setForm((prev) => ({ ...prev, unit_name: e.target.value }))} />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">联系人</label>
                    <input className="form-input" value={form.contact} onChange={(e) => setForm((prev) => ({ ...prev, contact: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">联系电话</label>
                    <input className="form-input" value={form.contact_phone} onChange={(e) => setForm((prev) => ({ ...prev, contact_phone: e.target.value }))} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">联系邮箱</label>
                  <input className="form-input" value={form.contact_email} onChange={(e) => setForm((prev) => ({ ...prev, contact_email: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">应用场景</label>
                  <textarea className="form-textarea" value={form.scenario} onChange={(e) => setForm((prev) => ({ ...prev, scenario: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">嵌入系统</label>
                  <input className="form-input" value={form.embedded_system} onChange={(e) => setForm((prev) => ({ ...prev, embedded_system: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">问题描述</label>
                  <textarea className="form-textarea" value={form.problem_statement} onChange={(e) => setForm((prev) => ({ ...prev, problem_statement: e.target.value }))} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">成效类型</label>
                    <select className="form-select" value={form.effectiveness_type} onChange={(e) => setForm((prev) => ({ ...prev, effectiveness_type: e.target.value as ValueDimension }))}>
                      <option value="cost_reduction">降本</option>
                      <option value="efficiency_gain">增效</option>
                      <option value="perception_uplift">感知提升</option>
                      <option value="revenue_growth">拉动收入</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">数据级别</label>
                    <select className="form-select" value={form.data_level} onChange={(e) => setForm((prev) => ({ ...prev, data_level: e.target.value as SubmissionPayload['data_level'] }))}>
                      <option value="L1">L1</option>
                      <option value="L2">L2</option>
                      <option value="L3">L3</option>
                      <option value="L4">L4</option>
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">成效指标</label>
                  <input className="form-input" value={form.effectiveness_metric} onChange={(e) => setForm((prev) => ({ ...prev, effectiveness_metric: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">预期收益</label>
                  <textarea className="form-textarea" value={form.expected_benefit} onChange={(e) => setForm((prev) => ({ ...prev, expected_benefit: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">封面图片 URL</label>
                  <input className="form-input" value={form.cover_image_url} onChange={(e) => setForm((prev) => ({ ...prev, cover_image_url: e.target.value }))} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">详细文档 URL</label>
                    <input className="form-input" value={form.detail_doc_url} onChange={(e) => setForm((prev) => ({ ...prev, detail_doc_url: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">详细文档名称</label>
                    <input className="form-input" value={form.detail_doc_name} onChange={(e) => setForm((prev) => ({ ...prev, detail_doc_name: e.target.value }))} />
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="secondary" onClick={() => setEditing(null)}>取消</button>
              <button className="primary" onClick={onSave} disabled={saving}>{saving ? '保存中...' : '保存'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

