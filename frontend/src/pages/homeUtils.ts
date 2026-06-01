import type { AppItem, RankingItem, SubmissionPayload, ValueDimension, HistoricalRanking } from '../types'
import { fetchAppDetail } from '../api/client'

export const DEFAULT_APP_CATEGORIES = ['前端市场类', '客户服务类', '云网运营类', '管理支撑类'] as const

export const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'available', label: '可用' },
  { value: 'approval', label: '需申请' },
  { value: 'beta', label: '试运行' },
  { value: 'offline', label: '已下线' }
]

export const appSourceOptions = [
  { value: 'all', label: '全部应用' },
  { value: 'group', label: '集团应用' },
  { value: 'province', label: '省内应用' },
] as const

export type HomeView = 'ranking' | 'library'
export type AppSource = typeof appSourceOptions[number]['value']

export const valueDimensionLabel: Record<ValueDimension, string> = {
  cost_reduction: '降本',
  efficiency_gain: '增效',
  perception_uplift: '感知提升',
  revenue_growth: '拉动收入'
}

export type ValidationRule = {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: RegExp;
  message: string;
};

export const validationRules: Record<string, ValidationRule> = {
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

export function createSubmissionDraft(
  currentUser: { company?: string } | null,
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

export function getGradient(id: number) {
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

export function rankingMetricText(row: RankingItem) {
  if (row.metric_type === 'likes') return `点赞 ${row.likes ?? 0}`
  if (row.metric_type === 'growth_rate') return `增速 +${row.score}%`
  return `综合分 ${row.score}`
}

export function monthlyCallsText(app: AppItem) {
  if (app.monthly_calls > 0) {
    return `${app.monthly_calls}k/月`
  }
  return app.section === 'province' ? '展示应用' : '0k/月'
}

export function appCompanyLabel(app: AppItem) {
  return app.company || app.org
}

export function appFromHistoricalRanking(row: HistoricalRanking): AppItem {
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

export function rankingItemFromHistorical(row: HistoricalRanking, appDetail?: AppItem): RankingItem {
  return {
    ranking_config_id: row.ranking_config_id || row.ranking_type,
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

export async function enrichHistoricalRankingApps(rows: HistoricalRanking[]) {
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
