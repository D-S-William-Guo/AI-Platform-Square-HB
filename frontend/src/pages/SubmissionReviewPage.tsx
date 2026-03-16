import { useEffect, useState, useCallback } from 'react'
import {
  fetchSubmissions,
  approveSubmissionAndCreateApp,
  rejectSubmission,
  syncRankings,
  isMissingAdminTokenError,
  getAdminTokenSetupHint
} from '../api/client'
import type { Submission } from '../types'
import { resolveMediaUrl } from '../utils/media'

const statusMap: Record<string, { label: string; color: string }> = {
  pending: { label: '待审核', color: '#f59e0b' },
  approved: { label: '已通过', color: '#10b981' },
  rejected: { label: '已拒绝', color: '#ef4444' },
  withdrawn: { label: '已撤回', color: '#6b7280' }
}

const valueDimensionLabel: Record<string, string> = {
  cost_reduction: '降本',
  efficiency_gain: '增效',
  perception_uplift: '感知提升',
  revenue_growth: '拉动收入'
}

function resolveAdminError(err: unknown, fallback: string): string {
  if (isMissingAdminTokenError(err)) {
    return `缺少管理员令牌。${getAdminTokenSetupHint()}`
  }

  const status = (err as { response?: { status?: number } })?.response?.status
  if (status === 401) {
    return `管理员令牌无效或未生效。${getAdminTokenSetupHint()}`
  }
  if (status === 403) {
    return '管理员令牌已识别，但无权限执行该操作。'
  }

  return fallback
}

export default function SubmissionReviewPage() {
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null)
  const [approvalForm, setApprovalForm] = useState({
    status: 'available' as 'available' | 'approval' | 'beta' | 'offline',
    monthly_calls: 0,
    difficulty: 'Medium',
    target_users: '',
    target_system: '',
    access_mode: 'profile' as 'direct' | 'profile',
    access_url: ''
  })
  const [processing, setProcessing] = useState(false)
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected' | 'withdrawn'>('all')

  const loadSubmissions = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchSubmissions()
      setSubmissions(data)
    } catch (err) {
      setError(resolveAdminError(err, '获取申报列表失败'))
      console.error('Failed to fetch submissions:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSubmissions()
  }, [loadSubmissions])

  const openSubmissionDetail = (submission: Submission) => {
    setSelectedSubmission(submission)
    setApprovalForm({
      status: 'available',
      monthly_calls: 0,
      difficulty: 'Medium',
      target_users: '',
      target_system: submission.embedded_system || '',
      access_mode: 'profile',
      access_url: ''
    })
  }

  const handleApprove = async (id: number, useFormSettings: boolean = false) => {
    if (!confirm('确定要通过此申报吗？通过后应用将进入排行榜评估体系。')) {
      return
    }

    try {
      setProcessing(true)
      await approveSubmissionAndCreateApp(
        id,
        useFormSettings
          ? {
              status: approvalForm.status,
              monthly_calls: approvalForm.monthly_calls,
              difficulty: approvalForm.difficulty,
              target_system: approvalForm.target_system,
              target_users: approvalForm.target_users,
              access_mode: approvalForm.access_mode,
              access_url: approvalForm.access_url
            }
          : undefined
      )
      await syncRankings() // 同步排行榜数据
      alert('审核通过！应用已创建并同步到排行榜。')
      setSelectedSubmission(null)
      loadSubmissions() // 刷新列表
    } catch (err) {
      alert(resolveAdminError(err, '审核失败，请重试'))
      console.error('Failed to approve submission:', err)
    } finally {
      setProcessing(false)
    }
  }

  const handleReject = async (id: number) => {
    if (!confirm('确定要拒绝此申报吗？')) {
      return
    }
    try {
      setProcessing(true)
      await rejectSubmission(id)
      alert('已拒绝该申报。')
      setSelectedSubmission(null)
      loadSubmissions()
    } catch (err) {
      alert(resolveAdminError(err, '拒绝失败，请重试'))
      console.error('Failed to reject submission:', err)
    } finally {
      setProcessing(false)
    }
  }

  const filteredSubmissions = submissions.filter(sub => {
    if (filter === 'all') return true
    return sub.status === filter
  })

  const stats = {
    total: submissions.length,
    pending: submissions.filter(s => s.status === 'pending').length,
    approved: submissions.filter(s => s.status === 'approved').length,
    rejected: submissions.filter(s => s.status === 'rejected').length,
    withdrawn: submissions.filter(s => s.status === 'withdrawn').length
  }

  return (
    <div className="page submission-review-page">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
        <div className="header-actions">
          <button className="primary" onClick={() => window.location.href = '/'}>
            <span>←</span>
            <span>返回首页</span>
          </button>
        </div>
      </header>

      <div className="page-container submission-review-page">
        <div className="page-header">
          <h1 className="page-title">省内应用申报审核</h1>
          <p className="page-subtitle">审核省内应用申报，通过审核的应用将进入排行榜评估体系</p>
        </div>

        {/* 统计卡片 */}
        <div className="stats-cards">
          <div className="stat-card">
            <div className="stat-card-value">{stats.total}</div>
            <div className="stat-card-label">申报总数</div>
          </div>
          <div className="stat-card pending">
            <div className="stat-card-value">{stats.pending}</div>
            <div className="stat-card-label">待审核</div>
          </div>
          <div className="stat-card approved">
            <div className="stat-card-value">{stats.approved}</div>
            <div className="stat-card-label">已通过</div>
          </div>
          <div className="stat-card rejected">
            <div className="stat-card-value">{stats.rejected}</div>
            <div className="stat-card-label">已拒绝</div>
          </div>
        </div>

        {/* 筛选器 */}
        <div className="filter-bar">
          <div className="filter-group">
            <button 
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              全部 ({stats.total})
            </button>
            <button 
              className={`filter-btn ${filter === 'pending' ? 'active' : ''}`}
              onClick={() => setFilter('pending')}
            >
              待审核 ({stats.pending})
            </button>
            <button 
              className={`filter-btn ${filter === 'approved' ? 'active' : ''}`}
              onClick={() => setFilter('approved')}
            >
              已通过 ({stats.approved})
            </button>
            <button 
              className={`filter-btn ${filter === 'rejected' ? 'active' : ''}`}
              onClick={() => setFilter('rejected')}
            >
              已拒绝 ({stats.rejected})
            </button>
            <button
              className={`filter-btn ${filter === 'withdrawn' ? 'active' : ''}`}
              onClick={() => setFilter('withdrawn')}
            >
              已撤回 ({stats.withdrawn})
            </button>
          </div>
          <button className="refresh-btn" onClick={loadSubmissions} disabled={loading}>
            {loading ? '刷新中...' : '刷新列表'}
          </button>
        </div>

        {/* 申报列表 */}
        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <span>加载中...</span>
          </div>
        ) : error ? (
          <div className="error-container">
            <span className="error-icon">❌</span>
            <span>{error}</span>
            <button className="retry-btn" onClick={loadSubmissions}>重试</button>
          </div>
        ) : filteredSubmissions.length === 0 ? (
          <div className="empty-container">
            <span className="empty-icon">📋</span>
            <span>暂无申报数据</span>
          </div>
        ) : (
          <div className="submission-list">
            {filteredSubmissions.map((submission) => (
              <div 
                key={submission.id} 
                className={`submission-card ${submission.status}`}
                onClick={() => openSubmissionDetail(submission)}
              >
                <div className="submission-header">
                  <div className="submission-title">
                    <h3>{submission.app_name}</h3>
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: statusMap[submission.status]?.color }}
                    >
                      {statusMap[submission.status]?.label}
                    </span>
                  </div>
                  <div className="submission-meta">
                    <span>申报单位：{submission.unit_name}</span>
                    <span>联系人：{submission.contact}</span>
                    <span>申报时间：{new Date(submission.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="submission-content">
                  <div className="info-row">
                    <span className="info-label">应用分类：</span>
                    <span className="info-value">{submission.category}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">嵌入系统：</span>
                    <span className="info-value">{submission.embedded_system}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">成效类型：</span>
                    <span className="info-value">{valueDimensionLabel[submission.effectiveness_type]}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">数据级别：</span>
                    <span className="info-value">{submission.data_level}</span>
                  </div>
                </div>

                <div className="submission-preview">
                  <p><strong>应用场景：</strong>{submission.scenario.substring(0, 100)}...</p>
                </div>

                {submission.status === 'pending' && (
                  <div className="submission-actions">
                    <button 
                      className="btn-primary"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleApprove(submission.id)
                      }}
                      disabled={processing}
                    >
                      {processing ? '处理中...' : '通过审核'}
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleReject(submission.id)
                      }}
                      disabled={processing}
                    >
                      拒绝
                    </button>
                    <button className="btn-secondary">查看详情</button>
                  </div>
                )}

                {submission.status === 'approved' && (
                  <div className="submission-actions">
                    <span className="approved-text">✅ 已通过审核，已创建应用</span>
                    <button className="btn-secondary">查看详情</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 详情弹窗 */}
      {selectedSubmission && (
        <div className="modal-overlay" onClick={() => setSelectedSubmission(null)}>
          <div className="modal-container detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">申报详情</h3>
              <button className="modal-close" onClick={() => setSelectedSubmission(null)}>×</button>
            </div>

            <div className="modal-body">
              <div className="detail-section">
                <h4>基础信息</h4>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">应用名称</span>
                    <span className="detail-value">{selectedSubmission.app_name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">申报单位</span>
                    <span className="detail-value">{selectedSubmission.unit_name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">联系人</span>
                    <span className="detail-value">{selectedSubmission.contact}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">联系电话</span>
                    <span className="detail-value">{selectedSubmission.contact_phone || '-'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">联系邮箱</span>
                    <span className="detail-value">{selectedSubmission.contact_email || '-'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">应用分类</span>
                    <span className="detail-value">{selectedSubmission.category}</span>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h4>应用信息</h4>
                <div className="detail-item full-width">
                  <span className="detail-label">应用场景</span>
                  <p className="detail-value">{selectedSubmission.scenario}</p>
                </div>
                <div className="detail-item full-width">
                  <span className="detail-label">嵌入系统</span>
                  <span className="detail-value">{selectedSubmission.embedded_system}</span>
                </div>
                <div className="detail-item full-width">
                  <span className="detail-label">问题描述</span>
                  <p className="detail-value">{selectedSubmission.problem_statement}</p>
                </div>
              </div>

              {selectedSubmission.status === 'pending' && (
                <div className="detail-section">
                  <h4>审批设置</h4>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <span className="detail-label">上线状态</span>
                      <select
                        className="form-select"
                        value={approvalForm.status}
                        onChange={(e) => setApprovalForm(prev => ({
                          ...prev,
                          status: e.target.value as 'available' | 'approval' | 'beta' | 'offline'
                        }))}
                      >
                        <option value="available">可用</option>
                        <option value="approval">需申请</option>
                        <option value="beta">试运行</option>
                        <option value="offline">已下线</option>
                      </select>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">月调用量（k）</span>
                      <input
                        className="form-input"
                        type="number"
                        min={0}
                        step={0.1}
                        value={approvalForm.monthly_calls}
                        onChange={(e) => setApprovalForm(prev => ({
                          ...prev,
                          monthly_calls: Math.max(0, Number(e.target.value || 0))
                        }))}
                      />
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">接入难度</span>
                      <select
                        className="form-select"
                        value={approvalForm.difficulty}
                        onChange={(e) => setApprovalForm(prev => ({ ...prev, difficulty: e.target.value }))}
                      >
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                      </select>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">适用人群</span>
                      <input
                        className="form-input"
                        value={approvalForm.target_users}
                        onChange={(e) => setApprovalForm(prev => ({ ...prev, target_users: e.target.value }))}
                        placeholder="如：客服代表、运维工程师"
                      />
                    </div>
                    <div className="detail-item full-width">
                      <span className="detail-label">接入系统</span>
                      <input
                        className="form-input"
                        value={approvalForm.target_system}
                        onChange={(e) => setApprovalForm(prev => ({ ...prev, target_system: e.target.value }))}
                      />
                    </div>
                  </div>
                </div>
              )}

              <div className="detail-section">
                <h4>成效评估</h4>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">成效类型</span>
                    <span className="detail-value">{valueDimensionLabel[selectedSubmission.effectiveness_type]}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">数据级别</span>
                    <span className="detail-value">{selectedSubmission.data_level}</span>
                  </div>
                  <div className="detail-item full-width">
                    <span className="detail-label">成效指标</span>
                    <span className="detail-value">{selectedSubmission.effectiveness_metric}</span>
                  </div>
                  <div className="detail-item full-width">
                    <span className="detail-label">预期收益</span>
                    <p className="detail-value">{selectedSubmission.expected_benefit}</p>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h4>排行榜配置</h4>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">参与排行</span>
                    <span className="detail-value">{selectedSubmission.ranking_enabled ? '是' : '否'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">排行权重</span>
                    <span className="detail-value">{selectedSubmission.ranking_weight}</span>
                  </div>
                  <div className="detail-item full-width">
                    <span className="detail-label">排行标签</span>
                    <span className="detail-value">{selectedSubmission.ranking_tags || '-'}</span>
                  </div>
                </div>
              </div>

              {selectedSubmission.cover_image_url && (
                <div className="detail-section">
                  <h4>封面图片</h4>
                  <img 
                    src={resolveMediaUrl(selectedSubmission.cover_image_url)}
                    alt="应用封面" 
                    className="cover-image"
                  />
                </div>
              )}
            </div>

            <div className="modal-footer">
              {selectedSubmission.status === 'pending' && (
                <>
                  <button
                    className="btn-secondary"
                    onClick={() => handleReject(selectedSubmission.id)}
                    disabled={processing}
                  >
                    拒绝
                  </button>
                  <button
                    className="btn-primary"
                    onClick={() => handleApprove(selectedSubmission.id, true)}
                    disabled={processing}
                  >
                    {processing ? '处理中...' : '通过审核'}
                  </button>
                </>
              )}
              <button className="btn-secondary" onClick={() => setSelectedSubmission(null)}>
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      <footer className="footer">
        <div>最近更新时间：2024-12-11 · 联系邮箱：aiapps@hebei.cn</div>
      </footer>
    </div>
  )
}
