import { useEffect, useMemo, useState, useCallback } from 'react'
import { Navigate, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import {
  auditEvent,
  clearAuthToken,
  fetchAuthMe,
  fetchAppDetail,
  fetchApps,
  fetchHistoricalRankings,
  fetchStats,
  logout,
  submitApp,
  uploadImage,
  uploadDocument,
  fetchRankingDimensions,
  fetchDimensionScores,
  fetchRankingConfigs,
  fetchMetaEnums,
} from '../api/client'
import type { AppItem, AuthUser, RankingItem, Stats, SubmissionPayload, ValueDimension, FormErrors, RankingDimension, HistoricalRanking } from '../types'
import { resolveMediaUrl } from '../utils/media'
import UiIcon from '../components/UiIcon'

const DEFAULT_APP_CATEGORIES = ['前端市场类', '客户服务类', '云网运营类', '管理支撑类'] as const
const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'available', label: '可用' },
  { value: 'approval', label: '需申请' },
  { value: 'beta', label: '试运行' },
  { value: 'offline', label: '已下线' }
]
const appSourceOptions = [
  { value: 'all', label: '全部应用' },
  { value: 'group', label: '集团应用' },
  { value: 'province', label: '省内应用' },
] as const

type HomeView = 'ranking' | 'library'
type AppSource = typeof appSourceOptions[number]['value']

const valueDimensionLabel: Record<ValueDimension, string> = {
  cost_reduction: '降本',
  efficiency_gain: '增效',
  perception_uplift: '感知提升',
  revenue_growth: '拉动收入'
}

function createSubmissionDraft(
  currentUser: AuthUser | null,
  defaultCategory: string,
  overrides?: Partial<SubmissionPayload>,
): SubmissionPayload {
  const company = currentUser?.company || ''
  const draft: SubmissionPayload = {
    app_name: '',
    unit_name: '',
    contact: '',
    contact_phone: '',
    contact_email: '',
    category: defaultCategory,
    scenario: '',
    embedded_system: '',
    problem_statement: '',
    effectiveness_type: 'efficiency_gain',
    effectiveness_metric: '',
    data_level: 'L2',
    expected_benefit: '',
    monthly_calls: 0,
    difficulty: 'Medium',
    cover_image_url: '',
    detail_doc_url: '',
    detail_doc_name: '',
    ...overrides,
  }
  draft.unit_name = company || overrides?.unit_name || ''
  return draft
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

function monthlyCallsText(app: AppItem) {
  if (app.monthly_calls > 0) {
    return `${app.monthly_calls}k/月`
  }
  return app.section === 'province' ? '展示应用' : '0k/月'
}

function appCompanyLabel(app: AppItem) {
  return app.company || app.org
}

function appFromHistoricalRanking(row: HistoricalRanking): AppItem {
  return {
    id: row.app_id,
    name: row.app_name,
    org: row.app_org,
    company: row.company || row.app_org,
    department: row.department || '',
    section: 'province',
    category: '',
    description: '该应用来自最新一次正式发布榜单，可进入详情查看已沉淀的展示信息。',
    status: 'available',
    monthly_calls: row.usage_30d,
    release_date: row.period_date,
    api_open: false,
    difficulty: '',
    contact_name: '',
    highlight: '',
    access_mode: 'profile',
    access_url: '',
    detail_doc_url: '',
    detail_doc_name: '',
    target_system: '',
    target_users: '',
    problem_statement: '',
    effectiveness_type: row.value_dimension,
    effectiveness_metric: `综合得分 ${row.score}`,
    cover_image_url: '',
    ranking_enabled: true,
    ranking_weight: 1,
    ranking_tags: row.tag,
    last_ranking_update: row.created_at,
  }
}

function rankingItemFromHistorical(row: HistoricalRanking, appDetail?: AppItem): RankingItem {
  return {
    ranking_config_id: row.ranking_type,
    position: row.position,
    tag: row.tag,
    score: row.score,
    likes: null,
    metric_type: row.metric_type,
    value_dimension: row.value_dimension,
    usage_30d: row.usage_30d,
    declared_at: row.period_date,
    updated_at: row.created_at,
    app: appDetail
      ? {
          ...appDetail,
          name: row.app_name,
          org: row.app_org,
          company: row.company || row.app_org,
          department: row.department || appDetail.department,
          ranking_enabled: true,
          ranking_tags: row.tag,
          last_ranking_update: row.created_at,
        }
      : appFromHistoricalRanking(row),
  }
}

async function enrichHistoricalRankingApps(rows: HistoricalRanking[]) {
  const appDetails = await Promise.all(
    rows.map(async (row) => {
      try {
        const app = await fetchAppDetail(row.app_id)
        return [row.app_id, app] as const
      } catch (error) {
        console.warn(`Failed to fetch app detail for historical ranking app ${row.app_id}:`, error)
        return [row.app_id, null] as const
      }
    })
  )
  return new Map(appDetails.filter(([, app]) => app !== null) as Array<readonly [number, AppItem]>)
}

// 表单验证规则类型定义
type ValidationRule = {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: RegExp;
  message: string;
};

// 表单验证规则
const validationRules: Record<string, ValidationRule> = {
  app_name: { required: true, minLength: 2, maxLength: 120, message: '应用名称需在2-120个字符之间' },
  unit_name: { required: true, minLength: 2, maxLength: 120, message: '当前账号未配置所属公司，请联系管理员补全信息' },
  contact: { required: true, minLength: 2, maxLength: 80, message: '联系人需在2-80个字符之间' },
  contact_phone: { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' },
  contact_email: { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '请输入有效的邮箱地址' },
  scenario: { required: true, minLength: 20, maxLength: 500, message: '应用场景需在20-500个字符之间' },
  embedded_system: { required: true, minLength: 2, maxLength: 120, message: '嵌入系统需在2-120个字符之间' },
  problem_statement: { required: true, minLength: 10, maxLength: 255, message: '问题描述需在10-255个字符之间' },
  effectiveness_metric: { required: true, minLength: 2, maxLength: 120, message: '成效指标需在2-120个字符之间' },
  expected_benefit: { required: true, minLength: 10, maxLength: 300, message: '预期收益需在10-300个字符之间' },
  monthly_calls: { min: 0, max: 1000000, message: '月调用量必须为非负数' },
}

// 主页面组件
function HomePage({
  currentUser,
  onLogout,
  appCategories,
  categoryOptionsLoading,
  categoryOptionsError,
}: {
  currentUser: AuthUser | null
  onLogout: (() => Promise<void>) | null
  appCategories: string[]
  categoryOptionsLoading: boolean
  categoryOptionsError: string | null
}) {
  const navigate = useNavigate()
  const location = useLocation()
  const routeState = (location.state || {}) as {
    noAdminPermission?: boolean
    openSubmission?: boolean
  }
  const canUseSubmission = Boolean(currentUser)
  const canAccessMySubmissions = Boolean(currentUser)
  const isAdmin = currentUser?.role === 'admin'
  const defaultCategory = appCategories[0] || ''
  const categories = useMemo(() => ['全部', ...appCategories], [appCategories])
  const submissionCategoryUnavailable =
    categoryOptionsLoading || Boolean(categoryOptionsError) || appCategories.length === 0
  const [activeNav, setActiveNav] = useState<HomeView>('ranking')
  const [appSource, setAppSource] = useState<AppSource>('all')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('全部')
  const [companyFilter, setCompanyFilter] = useState<string>('全部')
  const [keyword, setKeyword] = useState('')
  const [apps, setApps] = useState<AppItem[]>([])
  const [rankings, setRankings] = useState<RankingItem[]>([])
  const [rankingCompanyOptions, setRankingCompanyOptions] = useState<string[]>(['全部'])
  const [rankingLoading, setRankingLoading] = useState(false)
  const [rankingError, setRankingError] = useState<string | null>(null)
  const [rankingPublishedDate, setRankingPublishedDate] = useState<string>('')
  const [rankingType, setRankingType] = useState<'excellent' | 'trend'>('excellent')
  const [rankingDimension, setRankingDimension] = useState<string>('overall')
  const [rankingDimensions, setRankingDimensions] = useState<RankingDimension[]>([])
  const [rankingConfigs, setRankingConfigs] = useState<any[]>([])
  const [stats, setStats] = useState<Stats>({ pending: 12, approved_period: 7, total_apps: 86 })
  const [statsLoading, setStatsLoading] = useState(true)
  const [statsError, setStatsError] = useState<string | null>(null)
  const [selectedApp, setSelectedApp] = useState<AppItem | null>(null)
  const [showSubmission, setShowSubmission] = useState(false)
  const [submission, setSubmission] = useState<SubmissionPayload>(() => createSubmissionDraft(currentUser, defaultCategory))
  const [errors, setErrors] = useState<FormErrors>({})
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [documentUploading, setDocumentUploading] = useState(false)
  const [documentMeta, setDocumentMeta] = useState<{
    url: string
    name: string
    size: number
    mimeType: string
  } | null>(null)

  const companyOptions = useMemo(() => {
    if (activeNav === 'ranking') return rankingCompanyOptions

    const values =
      apps
        .filter((app) => app.section === 'province')
        .map(appCompanyLabel)
        .filter(Boolean)
    return ['全部', ...Array.from(new Set(values))]
  }, [activeNav, apps, rankingCompanyOptions])

  useEffect(() => {
    fetchRankingDimensions()
      .then((data) => setRankingDimensions(data.filter((item) => item.is_active)))
      .catch((error) => console.error('Failed to fetch ranking dimensions:', error))
    
    // 加载榜单配置
    fetchRankingConfigs(true)
      .then((data) => setRankingConfigs(data))
      .catch((error) => console.error('Failed to fetch ranking configs:', error))
    
    // 获取统计数据，添加加载状态和错误处理
    const loadStats = async () => {
      try {
        setStatsLoading(true)
        setStatsError(null)
        const data = await fetchStats()
        setStats(data)
      } catch (error) {
        console.error('Failed to fetch stats:', error)
        setStatsError('获取统计数据失败')
      } finally {
        setStatsLoading(false)
      }
    }
    
    loadStats()
  }, [])

  useEffect(() => {
    setSubmission((prev) => ({ ...prev, unit_name: currentUser?.company || prev.unit_name }))
  }, [currentUser?.company])

  useEffect(() => {
    if (!defaultCategory) return
    setSubmission((prev) => {
      if (appCategories.includes(prev.category)) return prev
      return { ...prev, category: defaultCategory }
    })
  }, [appCategories, defaultCategory])

  useEffect(() => {
    if (!routeState.openSubmission) return
    if (!currentUser) return
    if (!canUseSubmission) return
    setSubmission(createSubmissionDraft(currentUser, defaultCategory))
    setShowSubmission(true)
    auditEvent({
      event_name: 'submission.modal.auto_open',
      intent: 'submit',
      result: 'success',
      return_to: '/',
      context: 'home.route_state.open_submission',
    })
  }, [routeState.openSubmission, currentUser, canUseSubmission, defaultCategory])

  useEffect(() => {
    if (!routeState.noAdminPermission) return
    auditEvent({
      event_name: 'route.guard.denied_admin',
      intent: 'admin',
      result: 'denied_role',
      return_to: location.pathname,
      context: 'home.route_state.no_admin_permission',
    })
  }, [routeState.noAdminPermission, location.pathname])

  useEffect(() => {
    if (appSource === 'group' && companyFilter !== '全部') {
      setCompanyFilter('全部')
    }
  }, [appSource, companyFilter])

  useEffect(() => {
    if (activeNav === 'ranking') {
      const loadPublishedRankings = async () => {
        try {
          setRankingLoading(true)
          setRankingError(null)
          const snapshot = await fetchHistoricalRankings(rankingType)
          const appDetailMap = await enrichHistoricalRankingApps(snapshot)
          let processedRankings = snapshot.map((row) =>
            rankingItemFromHistorical(row, appDetailMap.get(row.app_id))
          )
          const latestDate = snapshot[0]?.period_date || ''
          setRankingPublishedDate(latestDate)
          setRankingCompanyOptions([
            '全部',
            ...Array.from(new Set(processedRankings.map((row) => appCompanyLabel(row.app)).filter(Boolean))),
          ])

          if (companyFilter !== '全部') {
            processedRankings = processedRankings.filter((row) => appCompanyLabel(row.app) === companyFilter)
          }

          if (rankingDimension !== 'overall' && latestDate) {
            const dimensionId = parseInt(rankingDimension.replace('dimension-', ''))
            if (!isNaN(dimensionId)) {
              try {
                const dimensionScores = await fetchDimensionScores(dimensionId, latestDate, rankingType)
                const scoreMap = new Map(dimensionScores.map(ds => [ds.app_id, ds.score]))
                processedRankings = processedRankings.map(row => ({
                  ...row,
                  dimensionScore: scoreMap.get(row.app.id) || 0
                }))
                processedRankings.sort((a, b) => (b.dimensionScore || 0) - (a.dimensionScore || 0))
                processedRankings = processedRankings.map((row, index) => ({
                  ...row,
                  position: index + 1
                }))
              } catch (error) {
                console.error('Failed to fetch dimension scores:', error)
              }
            }
          }

          if (keyword.trim()) {
            processedRankings = processedRankings.filter((row) =>
              row.app.name.toLowerCase().includes(keyword.toLowerCase())
            )
          }

          setRankings(processedRankings)
        } catch (error) {
          console.error('Failed to fetch published rankings:', error)
          setRankingError('获取最新发布榜单失败')
          setRankings([])
          setRankingPublishedDate('')
          setRankingCompanyOptions(['全部'])
        } finally {
          setRankingLoading(false)
        }
      }

      loadPublishedRankings()
      return
    }

    const params: Record<string, string> = {}
    if (appSource !== 'all') params.section = appSource
    if (statusFilter) params.status = statusFilter
    if (categoryFilter && categoryFilter !== '全部') params.category = categoryFilter
    if (appSource !== 'group' && companyFilter !== '全部') params.company = companyFilter
    if (keyword) params.q = keyword

    fetchApps(params).then((data) => {
      // 客户端按应用名称关键字过滤
      if (keyword.trim()) {
        const filtered = data.filter((app) =>
          app.name.toLowerCase().includes(keyword.toLowerCase())
        )
        setApps(filtered)
      } else {
        setApps(data)
      }
    })
  }, [activeNav, appSource, statusFilter, categoryFilter, companyFilter, keyword, rankingType, rankingDimension])

  const blockTitle = useMemo(() => {
    if (activeNav === 'library') return 'AI 应用视图'
    return 'AI 应用龙虎榜'
  }, [activeNav])

  const blockSubtitle = useMemo(() => {
    if (activeNav === 'library') return '统一展示集团应用与省内应用，支持按来源、分类、单位和关键词检索'
    return '展示省内应用总榜与增长趋势榜，帮助运营发现值得推广的 AI 应用'
  }, [activeNav])

  // 表单验证
  const validateField = useCallback((name: keyof SubmissionPayload, value: string | number | boolean): string => {
    const rule = validationRules[name as keyof typeof validationRules]
    if (!rule) return ''

    // 检查是否是 pattern 类型的规则
    if ('pattern' in rule && rule.pattern) {
      const stringValue = String(value)
      if (stringValue && !rule.pattern.test(stringValue)) {
        return rule.message
      }
      return ''
    }

    // 检查 required
    if (rule.required) {
      if (typeof value === 'string' && !value.trim()) {
        return '此字段为必填项'
      }
      if (value === null || value === undefined) {
        return '此字段为必填项'
      }
    }

    // 检查数字类型的字段
    if (typeof value === 'number') {
      if (rule.min !== undefined && value < rule.min) {
        return rule.message
      }
      if (rule.max !== undefined && value > rule.max) {
        return rule.message
      }
      return ''
    }

    // 检查字符串类型的字段
    if (typeof value === 'string' && value) {
      if (rule.minLength !== undefined && value.length < rule.minLength) {
        return `最少需要 ${rule.minLength} 个字符`
      }
      if (rule.maxLength !== undefined && value.length > rule.maxLength) {
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
      const value = submission[fieldName]
      const error = validateField(fieldName, value)
      if (error) {
        newErrors[key] = error
        isValid = false
      }
    })

    setErrors(newErrors)
    return isValid
  }, [submission, validateField])

  const handleFieldChange = useCallback((field: keyof SubmissionPayload, value: string | number) => {
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
      const result = await uploadImage(file, 'submission')
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

  const handleDocumentUpload = useCallback(async (file: File) => {
    const allowedExt = ['pdf', 'doc', 'docx', 'txt', 'md']
    const ext = (file.name.split('.').pop() || '').toLowerCase()
    if (!allowedExt.includes(ext)) {
      alert('详细文档仅支持 PDF/DOC/DOCX/TXT/MD')
      return
    }

    setDocumentUploading(true)
    try {
      const result = await uploadDocument(file)
      if (!result.success) {
        alert(result.message || '文档上传失败')
        return
      }
      setDocumentMeta({
        url: result.file_url,
        name: result.original_name,
        size: result.file_size,
        mimeType: file.type || ''
      })
      setSubmission(prev => ({
        ...prev,
        detail_doc_url: result.file_url,
        detail_doc_name: result.original_name
      }))
    } catch (_error) {
      alert('文档上传失败，请重试')
    } finally {
      setDocumentUploading(false)
    }
  }, [])

  const handleDocumentSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleDocumentUpload(file)
    }
  }, [handleDocumentUpload])

  async function onSubmit() {
    if (!currentUser) {
      auditEvent({
        event_name: 'auth.intent.submit.click',
        intent: 'submit',
        result: 'redirect_login',
        return_to: '/',
        context: 'home.submit.modal.submit',
      })
      navigate('/login', { state: { intent: 'submit', returnTo: '/' } })
      return
    }
    if (submissionCategoryUnavailable) {
      alert(categoryOptionsError || '分类配置加载中，请稍后重试')
      return
    }
    if (!validateForm()) {
      alert('请检查表单填写是否正确')
      return
    }

    try {
      await submitApp(submission)
      alert('申报已提交，等待审核。')
      setShowSubmission(false)
      setSubmission(createSubmissionDraft(currentUser, defaultCategory))
      setImagePreview(null)
      setDocumentMeta(null)
      setErrors({})
    } catch (error) {
      alert('提交失败，请重试')
    }
  }

  function closeSubmission() {
    setShowSubmission(false)
    setSubmission(createSubmissionDraft(currentUser, defaultCategory))
    setImagePreview(null)
    setDocumentMeta(null)
    setErrors({})
  }

  return (
    <div className="page home-page">
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
            onChange={(e) => setKeyword(e.target.value)} 
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
            onClick={() => {
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
              setSubmission(createSubmissionDraft(currentUser, defaultCategory))
              setShowSubmission(true)
            }}
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

      <div className="body">
        <aside className="left">
          <div className="side-panel">
            <div className="side-section">
              <div className="nav-section-title">核心视图</div>
              {rankingConfigs.map((config) => (
                <button
                  key={config.id}
                  className={`nav-item ${activeNav === 'ranking' && rankingType === config.id ? 'active' : ''}`}
                  onClick={() => {
                    setActiveNav('ranking')
                    setRankingType(config.id as 'excellent' | 'trend')
                  }}
                >
                  <span className="nav-icon">
                    {config.id === 'excellent' ? <UiIcon name="trophy" /> : config.id === 'trend' ? <UiIcon name="trend" /> : <UiIcon name="medal" />}
                  </span>
                  <span>{config.name}</span>
                </button>
              ))}
              <button 
                className={`nav-item ${activeNav === 'library' ? 'active' : ''}`} 
                onClick={() => setActiveNav('library')}
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
                    <button
                      className="retry-button"
                      onClick={async () => {
                        try {
                          setStatsLoading(true)
                          setStatsError(null)
                          const data = await fetchStats()
                          setStats(data)
                        } catch (error) {
                          console.error('Failed to fetch stats:', error)
                          setStatsError('获取统计数据失败')
                        } finally {
                          setStatsLoading(false)
                        }
                      }}
                    >
                      重试
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="stat-item">
                      <span className="stat-value pending">{stats.pending}</span>
                      <span className="stat-label">待审核</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value approved">{stats.approved_period}</span>
                      <span className="stat-label">本期通过</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value total">{stats.total_apps}</span>
                      <span className="stat-label">累计应用</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </aside>

        <main className="main">
          <section className="block-header">
            <div>
              <h2 className="block-title">{blockTitle}</h2>
              <p className="block-subtitle">{blockSubtitle}</p>
              {activeNav === 'ranking' && rankingPublishedDate && (
                <p className="block-hint">最新发布：{rankingPublishedDate}</p>
              )}
              {activeNav === 'library' && (
                <p className="block-hint">集团应用和省内应用均为展示内容，可通过应用来源筛选查看，不提供平台内跳转使用。</p>
              )}
            </div>
            {activeNav === 'library' && (
              <div className="filters">
                <select
                  className="filter-select"
                  value={appSource}
                  onChange={(e) => setAppSource(e.target.value as AppSource)}
                >
                  {appSourceOptions.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
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
                {appSource !== 'group' && (
                  <select
                    className="filter-select"
                    value={companyFilter}
                    onChange={(e) => setCompanyFilter(e.target.value)}
                  >
                    {companyOptions.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            )}
            {activeNav === 'ranking' && (
              <div className="filters">
                <div className="filter-group">
                  <button 
                    className={`filter-btn ${rankingType === 'excellent' ? 'active' : ''}`} 
                    onClick={() => setRankingType('excellent')}
                  >
                    总应用榜
                  </button>
                  <button 
                    className={`filter-btn ${rankingType === 'trend' ? 'active' : ''}`} 
                    onClick={() => setRankingType('trend')}
                  >
                    增长趋势榜
                  </button>
                </div>
                <div className="filter-group">
                  <span className="filter-label">排行维度：</span>
                  <select 
                    className="filter-select"
                    value={rankingDimension}
                    onChange={(e) => setRankingDimension(e.target.value)}
                  >
                    <option value="overall">综合排名</option>
                    {rankingDimensions.map((dimension) => (
                      <option key={dimension.id} value={`dimension-${dimension.id}`}>
                        {dimension.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="filter-group">
                  <span className="filter-label">公司：</span>
                  <select
                    className="filter-select"
                    value={companyFilter}
                    onChange={(e) => setCompanyFilter(e.target.value)}
                  >
                    {companyOptions.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </section>

          {activeNav === 'library' && (
            <section className="grid">
              {apps.map((app) => (
                <article className="card" key={app.id} onClick={() => setSelectedApp(app)}>
                  <div
                    className="card-image"
                    style={{ background: app.cover_image_url ? `url(${resolveMediaUrl(app.cover_image_url)}) center/cover` : getGradient(app.id) }}
                  >
                    <span className={`status-badge ${app.status}`}>
                      {statusOptions.find((x) => x.value === app.status)?.label}
                    </span>
                  </div>
                  <div className="card-content">
                    <h3 className="card-title">{app.name}</h3>
                    <div className="card-meta">
                      <span className="card-org">{app.company || app.org}</span>
                      {app.department ? (
                        <>
                          <span>·</span>
                          <span>{app.department}</span>
                        </>
                      ) : null}
                      <span>·</span>
                      <span className="card-category">{app.category}</span>
                    </div>
                    <p className="card-desc">{app.description}</p>
                    <div className="card-footer">
                      <div className="card-metrics">
                        <span><UiIcon name="calls" /> {monthlyCallsText(app)}</span>
                        <span><UiIcon name="date" /> {app.release_date}</span>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </section>
          )}

          {activeNav === 'ranking' && (
            rankingLoading ? (
              <section className="state-panel">
                <div className="loading-spinner"></div>
                <span>正在加载最新发布榜单...</span>
              </section>
            ) : rankingError ? (
              <section className="state-panel">
                <span className="state-icon"><UiIcon name="error" /></span>
                <span>{rankingError}</span>
              </section>
            ) : rankings.length === 0 ? (
              <section className="state-panel">
                <span className="state-icon"><UiIcon name="empty" /></span>
                <strong>暂无已发布榜单</strong>
                <span>管理员发布榜单后，这里会展示最新一次正式发布结果。</span>
                {isAdmin && (
                  <Link to="/ranking-management" className="state-action">
                    前往排行榜管理
                  </Link>
                )}
              </section>
            ) : (
              <section className="ranking-list">
                {rankings.map((row, index) => (
                  <div className="ranking-row" key={`${row.position}-${row.app.id}`} onClick={() => setSelectedApp(row.app)}>
                    <span className={`rank-number ${index < 3 ? 'top3' : ''}`}>#{row.position}</span>
                    <span className="rank-app-name">{row.app.name}</span>
                    <span className="rank-dimension">
                      {rankingDimension === 'overall' 
                        ? valueDimensionLabel[row.value_dimension] 
                        : `维度评分: ${(row as any).dimensionScore || 0}分`
                      }
                    </span>
                    <span className={`rank-tag ${row.tag === '推荐' ? 'recommended' : row.tag === '历史优秀' ? 'excellent' : 'new'}`}>
                      {row.tag}
                    </span>
                    <span className="rank-metric">{rankingMetricText(row)}</span>
                  </div>
                ))}
              </section>
            )
          )}
        </main>

      </div>

      <footer className="footer">
        <div>最近更新时间：2026-04-18 · 联系邮箱：aiapps@chinatelecom.cn</div>
        <div style={{ marginTop: '4px', fontSize: '12px' }}>数据来源于省公司各单位申报与集团应用目录</div>
      </footer>

      {selectedApp && (
        <div className="modal-overlay" onClick={() => setSelectedApp(null)}>
          <div className="modal-container" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-section">
                <h3 className="modal-title">{selectedApp.name}</h3>
                <div className="modal-subtitle">
                  <span className="modal-org">{selectedApp.company || selectedApp.org}</span>
                  {selectedApp.department ? <span className="modal-org">· {selectedApp.department}</span> : null}
                </div>
              </div>
              <button className="modal-close" onClick={() => setSelectedApp(null)}>×</button>
            </div>
            
            <div className="modal-body">
              <div
                className="modal-cover"
                style={{ background: selectedApp.cover_image_url ? `url(${resolveMediaUrl(selectedApp.cover_image_url)}) center/cover` : getGradient(selectedApp.id) }}
              >
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
                  <div className="modal-metric-icon"><UiIcon name="calls" /></div>
                  <div className="modal-metric-label">月调用量</div>
                  <div className="modal-metric-value">{monthlyCallsText(selectedApp)}</div>
                </div>
                <div className="modal-metric-item">
                  <div className="modal-metric-icon"><UiIcon name="date" /></div>
                  <div className="modal-metric-label">上线时间</div>
                  <div className="modal-metric-value">{selectedApp.release_date}</div>
                </div>
              </div>

              <div className="modal-section">
                <div className="modal-section-title">基本信息</div>
                <div className="modal-info-grid">
                  <div className="modal-info-item">
                    <span className="modal-info-label">所属公司</span>
                    <span className="modal-info-value">{selectedApp.company || selectedApp.org}</span>
                  </div>
                  <div className="modal-info-item">
                    <span className="modal-info-label">所属部门</span>
                    <span className="modal-info-value">{selectedApp.department || '未设置'}</span>
                  </div>
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
            </div>

            {selectedApp.detail_doc_url && (
              <div className="modal-footer">
                <a href={resolveMediaUrl(selectedApp.detail_doc_url)} target="_blank" rel="noreferrer" className="modal-btn secondary">
                  <UiIcon name="doc" />
                  <span>{selectedApp.detail_doc_name || '详细文档'}</span>
                </a>
              </div>
            )}
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
                      <button
                        type="button"
                        className="remove-image"
                        aria-label="移除封面图"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          removeImage()
                        }}
                      >
                        ×
                      </button>
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

              {/* 详细文档上传 */}
              <div className="form-group">
                <label className="form-label">详细文档（可选）</label>
                <div className="doc-upload-area">
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.txt,.md"
                    onChange={handleDocumentSelect}
                    className="doc-file-input"
                  />
                  {documentUploading ? (
                    <span className="doc-upload-status">文档上传中...</span>
                  ) : documentMeta ? (
                    <div className="doc-uploaded">
                      <span className="doc-name">{documentMeta.name}</span>
                      <button
                        type="button"
                        className="doc-remove-btn"
                        onClick={() => {
                          setDocumentMeta(null)
                          setSubmission(prev => ({ ...prev, detail_doc_url: '', detail_doc_name: '' }))
                        }}
                      >
                        移除
                      </button>
                    </div>
                  ) : (
                    <span className="doc-upload-status">点击上传文档，支持 PDF/DOC/DOCX/TXT/MD</span>
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
                    <label className="form-label">所属公司 *</label>
                    <input 
                      className={`form-input ${errors.unit_name ? 'error' : ''}`}
                      value={submission.unit_name} 
                      readOnly
                    />
                    {errors.unit_name && <span className="error-message">{errors.unit_name}</span>}
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">所属部门</label>
                    <input
                      className="form-input"
                      value={currentUser?.department || '未设置'}
                      readOnly
                    />
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
                  {categoryOptionsError && (
                    <div className="form-group">
                      <span className="error-message">{categoryOptionsError}</span>
                    </div>
                  )}
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
                      disabled={submissionCategoryUnavailable}
                    >
                      {appCategories.length === 0 ? (
                        <option value="">分类配置不可用</option>
                      ) : (
                        appCategories.map((category) => (
                          <option key={category} value={category}>{category}</option>
                        ))
                      )}
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">月调用量（k）</label>
                    <input
                      className={`form-input ${errors.monthly_calls ? 'error' : ''}`}
                      type="number"
                      min="0"
                      step="0.1"
                      value={submission.monthly_calls}
                      onChange={(e) => handleFieldChange('monthly_calls', Math.max(0, Number(e.target.value || 0)))}
                    />
                    {errors.monthly_calls && <span className="error-message">{errors.monthly_calls}</span>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">接入难度</label>
                    <select
                      className="form-select"
                      value={submission.difficulty}
                      onChange={(e) => handleFieldChange('difficulty', e.target.value as SubmissionPayload['difficulty'])}
                    >
                      <option value="Low">低</option>
                      <option value="Medium">中</option>
                      <option value="High">高</option>
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
              <button
                className="modal-btn primary"
                onClick={onSubmit}
                disabled={uploading || submissionCategoryUnavailable}
              >
                {uploading ? '上传中...' : '提交申报'}
              </button>
            </div>
          </div>
        </div>
      )}
      {routeState.noAdminPermission && (
        <div className="route-permission-banner">当前账号不是管理员，无法访问管理功能。</div>
      )}
    </div>
  )
}

export default HomePage
