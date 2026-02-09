import { useEffect, useMemo, useState, useCallback } from 'react'
import { fetchApps, fetchRankings, fetchRecommendations, fetchRules, fetchStats, submitApp, uploadImage } from './api/client'
import type { AppItem, RankingItem, Recommendation, RuleLink, Stats, SubmissionPayload, ValueDimension, FormErrors } from './types'

const categories = ['全部', '办公类', '业务前台', '运维后台', '企业管理']
const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'available', label: '可用' },
  { value: 'approval', label: '需申请' },
  { value: 'beta', label: '试运行' },
  { value: 'offline', label: '已下线' }
]
const valueDimensionLabel: Record<ValueDimension, string> = {
  cost_reduction: '降本',
  efficiency_gain: '增效',
  perception_uplift: '感知提升',
  revenue_growth: '拉动收入'
}

const defaultSubmission: SubmissionPayload = {
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
  cover_image_url: ''
}

// 生成渐变色
function getGradient(id: number) {
  const gradients = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
    'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
    'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
  ]
  return gradients[id % gradients.length]
}

function rankingMetricText(row: RankingItem) {
  if (row.metric_type === 'likes') return `点赞 ${row.likes ?? 0}`
  if (row.metric_type === 'growth_rate') return `增速 +${row.score}%`
  return `综合分 ${row.score}`
}

// 表单验证规则
const validationRules = {
  app_name: { required: true, minLength: 2, maxLength: 120, message: '应用名称需在2-120个字符之间' },
  unit_name: { required: true, minLength: 2, maxLength: 120, message: '申报单位需在2-120个字符之间' },
  contact: { required: true, minLength: 2, maxLength: 80, message: '联系人需在2-80个字符之间' },
  contact_phone: { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' },
  contact_email: { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '请输入有效的邮箱地址' },
  scenario: { required: true, minLength: 20, maxLength: 500, message: '应用场景需在20-500个字符之间' },
  embedded_system: { required: true, minLength: 2, maxLength: 120, message: '嵌入系统需在2-120个字符之间' },
  problem_statement: { required: true, minLength: 10, maxLength: 255, message: '问题描述需在10-255个字符之间' },
  effectiveness_metric: { required: true, minLength: 2, maxLength: 120, message: '成效指标需在2-120个字符之间' },
  expected_benefit: { required: true, minLength: 10, maxLength: 300, message: '预期收益需在10-300个字符之间' },
}

function App() {
  const [activeNav, setActiveNav] = useState<'group' | 'province' | 'ranking'>('group')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('全部')
  const [keyword, setKeyword] = useState('')
  const [apps, setApps] = useState<AppItem[]>([])
  const [rankings, setRankings] = useState<RankingItem[]>([])
  const [rankingType, setRankingType] = useState<'excellent' | 'trend'>('excellent')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [rules, setRules] = useState<RuleLink[]>([])
  const [stats, setStats] = useState<Stats>({ pending: 12, approved_period: 7, total_apps: 86 })
  const [selectedApp, setSelectedApp] = useState<AppItem | null>(null)
  const [showSubmission, setShowSubmission] = useState(false)
  const [submission, setSubmission] = useState<SubmissionPayload>(defaultSubmission)
  const [errors, setErrors] = useState<FormErrors>({})
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [imagePreview, setImagePreview] = useState<string | null>(null)

  useEffect(() => {
    fetchRecommendations().then(setRecommendations)
    fetchRules().then(setRules)
    fetchStats().then(setStats)
  }, [])

  useEffect(() => {
    if (activeNav === 'ranking') {
      fetchRankings(rankingType).then(setRankings)
      return
    }

    const params: Record<string, string> = { section: activeNav }
    if (statusFilter) params.status = statusFilter
    if (categoryFilter && categoryFilter !== '全部') params.category = categoryFilter
    if (keyword) params.q = keyword

    fetchApps(params).then(setApps)
  }, [activeNav, statusFilter, categoryFilter, keyword, rankingType])

  const blockTitle = useMemo(() => {
    if (activeNav === 'group') return '集团应用整合'
    if (activeNav === 'province') return '河北省自研应用 / 可调用应用'
    return 'AI 应用龙虎榜'
  }, [activeNav])

  const blockSubtitle = useMemo(() => {
    if (activeNav === 'group') return '汇聚集团内各单位优质 AI 应用，一站式查看和申请使用'
    if (activeNav === 'province') return '省内各单位自研 AI 应用，支持 API 调用和系统集成'
    return '展示优秀应用和增长趋势，发现最具价值的 AI 应用'
  }, [activeNav])

  // 表单验证
  const validateField = useCallback((name: keyof SubmissionPayload, value: string): string => {
    const rule = validationRules[name as keyof typeof validationRules]
    if (!rule) return ''

    // 检查是否是 pattern 类型的规则
    if ('pattern' in rule) {
      if (value && !rule.pattern.test(value)) {
        return rule.message
      }
      return ''
    }

    // 检查 required
    if (rule.required && !value.trim()) {
      return '此字段为必填项'
    }

    if (value) {
      if (rule.minLength && value.length < rule.minLength) {
        return `最少需要 ${rule.minLength} 个字符`
      }
      if (rule.maxLength && value.length > rule.maxLength) {
        return `最多允许 ${rule.maxLength} 个字符`
      }
    }

    return ''
  }, [])

  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {}
    let isValid = true

    Object.keys(validationRules).forEach((key) => {
      const fieldName = key as keyof SubmissionPayload
      const error = validateField(fieldName, submission[fieldName] as string)
      if (error) {
        newErrors[key] = error
        isValid = false
      }
    })

    setErrors(newErrors)
    return isValid
  }, [submission, validateField])

  const handleFieldChange = useCallback((field: keyof SubmissionPayload, value: string) => {
    setSubmission(prev => ({ ...prev, [field]: value }))
    // 实时验证
    const error = validateField(field, value)
    setErrors(prev => ({ ...prev, [field]: error }))
  }, [validateField])

  // 图片上传处理
  const handleImageUpload = useCallback(async (file: File) => {
    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']
    if (!allowedTypes.includes(file.type)) {
      alert('仅支持 JPG、PNG 格式的图片')
      return
    }

    // 验证文件大小 (5MB)
    const maxSize = 5 * 1024 * 1024
    if (file.size > maxSize) {
      alert('图片大小不能超过 5MB')
      return
    }

    // 预览图片
    const reader = new FileReader()
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string)
    }
    reader.readAsDataURL(file)

    // 上传图片
    setUploading(true)
    setUploadProgress(0)

    try {
      const result = await uploadImage(file)
      if (result.success) {
        setSubmission(prev => ({ ...prev, cover_image_url: result.image_url }))
        setUploadProgress(100)
      } else {
        alert(result.message)
        setImagePreview(null)
      }
    } catch (error) {
      alert('图片上传失败，请重试')
      setImagePreview(null)
    } finally {
      setUploading(false)
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleImageUpload(file)
    }
  }, [handleImageUpload])

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleImageUpload(file)
    }
  }, [handleImageUpload])

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
  }, [])

  const removeImage = useCallback(() => {
    setImagePreview(null)
    setSubmission(prev => ({ ...prev, cover_image_url: '' }))
  }, [])

  async function onSubmit() {
    if (!validateForm()) {
      alert('请检查表单填写是否正确')
      return
    }

    try {
      await submitApp(submission)
      setShowSubmission(false)
      setSubmission(defaultSubmission)
      setImagePreview(null)
      setErrors({})
      alert('申报已提交，等待审核。')
    } catch (error) {
      alert('提交失败，请重试')
    }
  }

  function closeSubmission() {
    setShowSubmission(false)
    setSubmission(defaultSubmission)
    setImagePreview(null)
    setErrors({})
  }

  return (
    <div className="page">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
        <div className="search-wrapper">
          <span className="search-icon">🔍</span>
          <input 
            className="search" 
            placeholder="搜索应用名称、分类或关键词..." 
            value={keyword} 
            onChange={(e) => setKeyword(e.target.value)} 
          />
        </div>
        <div className="header-actions">
          <button className="primary" onClick={() => setShowSubmission(true)}>
            <span>+</span>
            <span>我要申报</span>
          </button>
          <div className="avatar">张</div>
        </div>
      </header>

      <div className="body">
        <aside className="left">
          <div className="nav-section">
            <div className="nav-section-title">导航</div>
            <button 
              className={`nav-item ${activeNav === 'group' ? 'active' : ''}`} 
              onClick={() => setActiveNav('group')}
            >
              <span className="nav-icon">🏢</span>
              <span>集团应用</span>
            </button>
            <button 
              className={`nav-item ${activeNav === 'province' ? 'active' : ''}`} 
              onClick={() => setActiveNav('province')}
            >
              <span className="nav-icon">📍</span>
              <span>省内应用</span>
            </button>
            <button 
              className={`nav-item ${activeNav === 'ranking' ? 'active' : ''}`} 
              onClick={() => setActiveNav('ranking')}
            >
              <span className="nav-icon">🏆</span>
              <span>应用榜单</span>
            </button>
          </div>

          <div className="filter-section">
            <div className="nav-section-title">分类筛选</div>
            {categories.map((item) => (
              <div 
                key={item} 
                className={`filter-item ${categoryFilter === item ? 'active' : ''}`}
                onClick={() => setCategoryFilter(item)}
              >
                <div className="filter-checkbox"></div>
                <span className="filter-label">{item}</span>
              </div>
            ))}
          </div>

          <div className="quick-links">
            <div className="nav-section-title">快速入口</div>
            <a href="#" className="quick-link">
              <span>📋</span>
              <span>申报指南</span>
            </a>
            <a href="#" className="quick-link">
              <span>📜</span>
              <span>榜单规则</span>
            </a>
          </div>
        </aside>

        <main className="main">
          <section className="block-header">
            <div>
              <h2 className="block-title">{blockTitle}</h2>
              <p className="block-subtitle">{blockSubtitle}</p>
            </div>
            {activeNav !== 'ranking' && (
              <div className="filters">
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
              </div>
            )}
            {activeNav === 'ranking' && (
              <div className="filters">
                <button 
                  className={`filter-btn ${rankingType === 'excellent' ? 'active' : ''}`} 
                  onClick={() => setRankingType('excellent')}
                >
                  优秀应用榜
                </button>
                <button 
                  className={`filter-btn ${rankingType === 'trend' ? 'active' : ''}`} 
                  onClick={() => setRankingType('trend')}
                >
                  趋势榜
                </button>
              </div>
            )}
          </section>

          {activeNav !== 'ranking' && (
            <section className="grid">
              {apps.map((app) => (
                <article className="card" key={app.id} onClick={() => setSelectedApp(app)}>
                  <div className="card-image" style={{ background: app.cover_image_url ? `url(${app.cover_image_url}) center/cover` : getGradient(app.id) }}>
                    <span className={`status-badge ${app.status}`}>
                      {statusOptions.find((x) => x.value === app.status)?.label}
                    </span>
                  </div>
                  <div className="card-content">
                    <h3 className="card-title">{app.name}</h3>
                    <div className="card-meta">
                      <span className="card-org">{app.org}</span>
                      <span>·</span>
                      <span className="card-category">{app.category}</span>
                    </div>
                    <p className="card-desc">{app.description}</p>
                    <div className="card-footer">
                      <div className="card-metrics">
                        <span>📊 {app.monthly_calls}k/月</span>
                        <span>📅 {app.release_date}</span>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </section>
          )}

          {activeNav === 'ranking' && (
            <section className="ranking-list">
              {rankings.map((row, index) => (
                <div className="ranking-row" key={`${row.position}-${row.app.id}`} onClick={() => setSelectedApp(row.app)}>
                  <span className={`rank-number ${index < 3 ? 'top3' : ''}`}>#{row.position}</span>
                  <span className="rank-app-name">{row.app.name}</span>
                  <span className="rank-dimension">{valueDimensionLabel[row.value_dimension]}</span>
                  <span className={`rank-tag ${row.tag === '推荐' ? 'recommended' : row.tag === '历史优秀' ? 'excellent' : 'new'}`}>
                    {row.tag}
                  </span>
                  <span className="rank-metric">{rankingMetricText(row)}</span>
                </div>
              ))}
            </section>
          )}
        </main>

        <aside className="right">
          <div className="section-card">
            <h4 className="section-title">
              <span className="section-icon">⭐</span>
              <span>本期推荐</span>
            </h4>
            {recommendations.map((item, index) => (
              <div className="mini-card" key={item.title}>
                <div className="mini-card-icon" style={{ background: getGradient(index) }}>
                  {['🤖', '💼', '📊'][index % 3]}
                </div>
                <div className="mini-card-content">
                  <div className="mini-card-title">{item.title}</div>
                  <p className="mini-card-desc">{item.scene}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="section-card">
            <h4 className="section-title">
              <span className="section-icon">📈</span>
              <span>申报统计</span>
            </h4>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">待审核</span>
                <span className="stat-value pending">{stats.pending}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">本期已通过</span>
                <span className="stat-value approved">{stats.approved_period}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">累计应用</span>
                <span className="stat-value total">{stats.total_apps}</span>
              </div>
            </div>
          </div>

          <div className="section-card">
            <h4 className="section-title">
              <span className="section-icon">⚡</span>
              <span>快速规则</span>
            </h4>
            <div className="rule-list">
              {rules.map((rule) => (
                <a key={rule.title} href={rule.href} target="_blank" rel="noreferrer" className="rule-item">
                  <span className="rule-icon">📄</span>
                  <span>{rule.title}</span>
                </a>
              ))}
            </div>
          </div>
        </aside>
      </div>

      <footer className="footer">
        <div>最近更新时间：2024-12-11 · 联系邮箱：aiapps@hebei.cn</div>
        <div style={{ marginTop: '4px', fontSize: '12px' }}>数据来源于省公司各单位申报与集团应用目录</div>
      </footer>

      {selectedApp && (
        <div className="modal-overlay" onClick={() => setSelectedApp(null)}>
          <div className="modal-container" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-section">
                <h3 className="modal-title">{selectedApp.name}</h3>
                <div className="modal-subtitle">
                  <span className="modal-org">{selectedApp.org}</span>
                </div>
              </div>
              <button className="modal-close" onClick={() => setSelectedApp(null)}>×</button>
            </div>
            
            <div className="modal-cover" style={{ background: selectedApp.cover_image_url ? `url(${selectedApp.cover_image_url}) center/cover` : getGradient(selectedApp.id) }}>
              <span className={`modal-status-badge ${selectedApp.status}`}>
                {statusOptions.find((x) => x.value === selectedApp.status)?.label}
              </span>
            </div>

            <div className="modal-tags">
              <span className="modal-tag primary">{selectedApp.category}</span>
              <span className="modal-tag">{valueDimensionLabel[selectedApp.effectiveness_type]}</span>
            </div>

            <div className="modal-section">
              <div className="modal-section-title">场景介绍</div>
              <p className="modal-content">{selectedApp.description}</p>
            </div>

            <div className="modal-metrics">
              <div className="modal-metric-item">
                <div className="modal-metric-icon">📊</div>
                <div className="modal-metric-label">月调用量</div>
                <div className="modal-metric-value">{selectedApp.monthly_calls}k</div>
              </div>
              <div className="modal-metric-item">
                <div className="modal-metric-icon">📅</div>
                <div className="modal-metric-label">上线时间</div>
                <div className="modal-metric-value">{selectedApp.release_date}</div>
              </div>
            </div>

            <div className="modal-section">
              <div className="modal-section-title">基本信息</div>
              <div className="modal-info-grid">
                <div className="modal-info-item">
                  <span className="modal-info-label">接入系统</span>
                  <span className="modal-info-value">{selectedApp.target_system}</span>
                </div>
                <div className="modal-info-item">
                  <span className="modal-info-label">适用人群</span>
                  <span className="modal-info-value">{selectedApp.target_users}</span>
                </div>
                <div className="modal-info-item">
                  <span className="modal-info-label">解决问题</span>
                  <span className="modal-info-value">{selectedApp.problem_statement}</span>
                </div>
                <div className="modal-info-item">
                  <span className="modal-info-label">接入难度</span>
                  <span className="modal-info-value">{selectedApp.difficulty}</span>
                </div>
              </div>
            </div>

            <div className="modal-section">
              <div className="modal-section-title">成效评估</div>
              <div className="modal-effectiveness">
                <div className="modal-effectiveness-item">
                  <span className="modal-effectiveness-label">成效类型</span>
                  <span className="modal-effectiveness-value">{valueDimensionLabel[selectedApp.effectiveness_type]}</span>
                </div>
                <div className="modal-effectiveness-item">
                  <span className="modal-effectiveness-label">指标评估</span>
                  <span className="modal-effectiveness-value highlight">{selectedApp.effectiveness_metric}</span>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              {selectedApp.access_mode === 'direct' ? (
                <a href={selectedApp.access_url} target="_blank" rel="noreferrer" className="modal-btn primary">
                  <span>🚀</span>
                  <span>申请试用</span>
                </a>
              ) : (
                <button className="modal-btn primary" disabled>
                  <span>🔒</span>
                  <span>需申请接入</span>
                </button>
              )}
              <button className="modal-btn secondary">
                <span>📄</span>
                <span>详细文档</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {showSubmission && (
        <div className="modal-overlay" onClick={closeSubmission}>
          <div className="modal-container submission-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-section">
                <h3 className="modal-title">应用申报</h3>
                <p className="modal-subtitle">请填写完整的应用信息，带 * 的为必填项</p>
              </div>
              <button className="modal-close" onClick={closeSubmission}>×</button>
            </div>

            <div className="modal-body">
              {/* 图片上传区域 */}
              <div className="form-group">
                <label className="form-label">应用封面图</label>
                <div 
                  className={`image-upload-area ${imagePreview ? 'has-image' : ''}`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                >
                  {imagePreview ? (
                    <div className="image-preview">
                      <img src={imagePreview} alt="预览" />
                      <button className="remove-image" onClick={removeImage}>×</button>
                    </div>
                  ) : (
                    <div className="upload-placeholder">
                      <div className="upload-icon">📷</div>
                      <p>点击或拖拽上传图片</p>
                      <p className="upload-hint">支持 JPG、PNG 格式，最大 5MB</p>
                    </div>
                  )}
                  <input 
                    type="file" 
                    accept="image/jpeg,image/png,image/jpg" 
                    onChange={handleFileSelect}
                    className="file-input"
                  />
                  {uploading && (
                    <div className="upload-progress">
                      <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
                      <span className="progress-text">{uploadProgress}%</span>
                    </div>
                  )}
                </div>
              </div>

              {/* 基础信息 */}
              <div className="form-section">
                <h4 className="form-section-title">基础信息</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">应用名称 *</label>
                    <input 
                      className={`form-input ${errors.app_name ? 'error' : ''}`}
                      placeholder="请输入应用名称"
                      value={submission.app_name} 
                      onChange={(e) => handleFieldChange('app_name', e.target.value)} 
                    />
                    {errors.app_name && <span className="error-message">{errors.app_name}</span>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">申报单位 *</label>
                    <input 
                      className={`form-input ${errors.unit_name ? 'error' : ''}`}
                      placeholder="请输入申报单位"
                      value={submission.unit_name} 
                      onChange={(e) => handleFieldChange('unit_name', e.target.value)} 
                    />
                    {errors.unit_name && <span className="error-message">{errors.unit_name}</span>}
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">联系人 *</label>
                    <input 
                      className={`form-input ${errors.contact ? 'error' : ''}`}
                      placeholder="请输入联系人姓名"
                      value={submission.contact} 
                      onChange={(e) => handleFieldChange('contact', e.target.value)} 
                    />
                    {errors.contact && <span className="error-message">{errors.contact}</span>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">联系电话</label>
                    <input 
                      className={`form-input ${errors.contact_phone ? 'error' : ''}`}
                      placeholder="请输入手机号码"
                      value={submission.contact_phone} 
                      onChange={(e) => handleFieldChange('contact_phone', e.target.value)} 
                    />
                    {errors.contact_phone && <span className="error-message">{errors.contact_phone}</span>}
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">联系邮箱</label>
                    <input 
                      className={`form-input ${errors.contact_email ? 'error' : ''}`}
                      placeholder="请输入邮箱地址"
                      value={submission.contact_email} 
                      onChange={(e) => handleFieldChange('contact_email', e.target.value)} 
                    />
                    {errors.contact_email && <span className="error-message">{errors.contact_email}</span>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">应用分类 *</label>
                    <select 
                      className="form-select"
                      value={submission.category} 
                      onChange={(e) => handleFieldChange('category', e.target.value)}
                    >
                      <option value="办公类">办公类</option>
                      <option value="业务前台">业务前台</option>
                      <option value="运维后台">运维后台</option>
                      <option value="企业管理">企业管理</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* 应用信息 */}
              <div className="form-section">
                <h4 className="form-section-title">应用信息</h4>
                <div className="form-group">
                  <label className="form-label">应用场景 *</label>
                  <textarea 
                    className={`form-textarea ${errors.scenario ? 'error' : ''}`}
                    placeholder="请详细描述应用场景（至少20字）..."
                    value={submission.scenario} 
                    onChange={(e) => handleFieldChange('scenario', e.target.value)} 
                  />
                  {errors.scenario && <span className="error-message">{errors.scenario}</span>}
                  <span className="char-count">{submission.scenario.length}/500</span>
                </div>

                <div className="form-group">
                  <label className="form-label">嵌入系统 *</label>
                  <input 
                    className={`form-input ${errors.embedded_system ? 'error' : ''}`}
                    placeholder="请输入嵌入系统名称"
                    value={submission.embedded_system} 
                    onChange={(e) => handleFieldChange('embedded_system', e.target.value)} 
                  />
                  {errors.embedded_system && <span className="error-message">{errors.embedded_system}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">解决的问题 *</label>
                  <textarea 
                    className={`form-textarea ${errors.problem_statement ? 'error' : ''}`}
                    placeholder="请描述解决的问题（至少10字）..."
                    value={submission.problem_statement} 
                    onChange={(e) => handleFieldChange('problem_statement', e.target.value)} 
                  />
                  {errors.problem_statement && <span className="error-message">{errors.problem_statement}</span>}
                  <span className="char-count">{submission.problem_statement.length}/255</span>
                </div>
              </div>

              {/* 成效评估 */}
              <div className="form-section">
                <h4 className="form-section-title">成效评估</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">成效类型 *</label>
                    <select 
                      className="form-select"
                      value={submission.effectiveness_type} 
                      onChange={(e) => handleFieldChange('effectiveness_type', e.target.value as ValueDimension)}
                    >
                      <option value="cost_reduction">降本</option>
                      <option value="efficiency_gain">增效</option>
                      <option value="perception_uplift">感知提升</option>
                      <option value="revenue_growth">拉动收入</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">数据级别 *</label>
                    <select 
                      className="form-select"
                      value={submission.data_level} 
                      onChange={(e) => handleFieldChange('data_level', e.target.value)}
                    >
                      <option value="L1">L1 - 公开数据</option>
                      <option value="L2">L2 - 内部数据</option>
                      <option value="L3">L3 - 敏感数据</option>
                      <option value="L4">L4 - 机密数据</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">成效指标 *</label>
                  <input 
                    className={`form-input ${errors.effectiveness_metric ? 'error' : ''}`}
                    placeholder="如：工时下降30%、效率提升50%..."
                    value={submission.effectiveness_metric} 
                    onChange={(e) => handleFieldChange('effectiveness_metric', e.target.value)} 
                  />
                  {errors.effectiveness_metric && <span className="error-message">{errors.effectiveness_metric}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">预期收益 *</label>
                  <textarea 
                    className={`form-textarea ${errors.expected_benefit ? 'error' : ''}`}
                    placeholder="请描述预期收益（至少10字）..."
                    value={submission.expected_benefit} 
                    onChange={(e) => handleFieldChange('expected_benefit', e.target.value)} 
                  />
                  {errors.expected_benefit && <span className="error-message">{errors.expected_benefit}</span>}
                  <span className="char-count">{submission.expected_benefit.length}/300</span>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="modal-btn secondary" onClick={closeSubmission}>取消</button>
              <button className="modal-btn primary" onClick={onSubmit} disabled={uploading}>
                {uploading ? '上传中...' : '提交申报'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
