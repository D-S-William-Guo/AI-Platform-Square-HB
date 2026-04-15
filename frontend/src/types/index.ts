export type AppStatus = 'available' | 'approval' | 'beta' | 'offline'
export type MetricType = 'composite' | 'growth_rate' | 'likes'
export type ValueDimension = 'cost_reduction' | 'efficiency_gain' | 'perception_uplift' | 'revenue_growth'

export type AppItem = {
  id: number
  name: string
  org: string
  company: string
  department: string
  section: 'group' | 'province'
  category: string
  description: string
  status: AppStatus
  monthly_calls: number
  release_date: string
  api_open: boolean
  difficulty: string
  contact_name: string
  highlight: string
  access_mode: 'direct' | 'profile'
  access_url: string
  detail_doc_url: string
  detail_doc_name: string
  target_system: string
  target_users: string
  problem_statement: string
  effectiveness_type: ValueDimension
  effectiveness_metric: string
  cover_image_url: string
  // 排行榜相关字段
  ranking_enabled: boolean
  ranking_weight: number
  ranking_tags: string
  last_ranking_update: string | null
}

export type RankingItem = {
  ranking_config_id?: string | null
  position: number
  tag: string
  score: number
  likes: number | null
  metric_type: MetricType
  value_dimension: ValueDimension
  usage_30d: number
  declared_at: string
  updated_at?: string | null
  app: AppItem
  dimensionScore?: number  // 用于维度筛选排序
}

export type Recommendation = {
  title: string
  scene: string
}

export type Stats = {
  pending: number
  approved_period: number
  total_apps: number
}

export type RuleLink = {
  title: string
  href: string
}

export type MetaEnums = {
  app_status: string[]
  app_category: string[]
  app_difficulty: string[]
  ranking_metric_type: string[]
  value_dimension: string[]
  data_level: string[]
}

export type PaginatedResponse<T> = {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export type UserRole = 'user' | 'admin'

export type AuthUser = {
  id: number
  username: string
  chinese_name: string
  role: UserRole
  phone: string
  email: string
  company: string
  department: string
  is_active: boolean
  can_submit: boolean
}

export type AdminUserCreatePayload = {
  username: string
  chinese_name: string
  company: string
  department: string
  password?: string
  phone?: string
  email?: string
  role?: UserRole
  is_active?: boolean
  can_submit?: boolean
}

export type AdminUserUpdatePayload = {
  chinese_name: string
  company: string
  department: string
  password?: string
  phone?: string
  email?: string
  role?: UserRole
  is_active?: boolean
  can_submit?: boolean
}

export type AuthLoginResponse = {
  access_token: string
  token_type: 'bearer'
  expires_at: string
  user: AuthUser
}

export type AuthMeResponse = {
  expires_at: string
  user: AuthUser
}

export type AuthProviderMode = 'local' | 'oa' | 'external_sso'

export type AuthProviderInfo = {
  mode: AuthProviderMode
  display_name: string
  login_url: string
  local_login_enabled: boolean
  configured: boolean
  message: string
}

// 申报数据
export type Submission = {
  id: number
  app_name: string
  unit_name: string
  company: string
  department: string
  contact: string
  contact_phone: string
  contact_email: string
  category: string
  scenario: string
  embedded_system: string
  problem_statement: string
  effectiveness_type: ValueDimension
  effectiveness_metric: string
  data_level: 'L1' | 'L2' | 'L3' | 'L4'
  expected_benefit: string
  monthly_calls: number
  difficulty: 'Low' | 'Medium' | 'High'
  status: 'pending' | 'approved' | 'rejected' | 'withdrawn'
  submitter_user_id: number | null
  approved_by_user_id: number | null
  approved_at: string | null
  rejected_by_user_id: number | null
  rejected_at: string | null
  rejected_reason: string
  manage_token: string
  cover_image_id: number | null
  cover_image_url: string
  detail_doc_url: string
  detail_doc_name: string
  created_at: string
  updated_at: string | null
  // 排行榜相关字段
  ranking_enabled: boolean
  ranking_weight: number
  ranking_tags: string
  ranking_dimensions: string
}

export type SubmissionPayload = {
  app_name: string
  unit_name: string
  contact: string
  contact_phone: string
  contact_email: string
  category: string
  scenario: string
  embedded_system: string
  problem_statement: string
  effectiveness_type: ValueDimension
  effectiveness_metric: string
  data_level: 'L1' | 'L2' | 'L3' | 'L4'
  expected_benefit: string
  monthly_calls: number
  difficulty: 'Low' | 'Medium' | 'High'
  cover_image_url: string
  detail_doc_url: string
  detail_doc_name: string
}

export type ImageUploadResponse = {
  success: boolean
  image_url: string
  thumbnail_url: string
  original_name: string
  file_size: number
  message: string
}

export type DocumentUploadResponse = {
  success: boolean
  file_url: string
  original_name: string
  file_size: number
  message: string
}

export type FormErrors = {
  [key: string]: string
}

export type ValidationRule =
  | { required: true; minLength?: number; maxLength?: number; message: string }
  | { required?: boolean; minLength: number; maxLength?: number; message: string }
  | { required?: boolean; minLength?: number; maxLength: number; message: string }
  | { pattern: RegExp; message: string }


export type RankingDimension = {
  id: number
  name: string
  description: string
  calculation_method: string
  weight: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type RankingConfigRecord = {
  id: string
  name: string
  description: string
  dimensions_config: string
  calculation_method: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// 应用维度评分
export type AppDimensionScore = {
  id: number
  app_id: number
  ranking_config_id: string | null
  dimension_id: number
  dimension_name: string
  score: number
  weight: number
  calculation_detail: string
  period_date: string
  created_at: string
  updated_at: string
}

// 历史榜单
export type HistoricalRanking = {
  id: number
  ranking_type: 'excellent' | 'trend'
  period_date: string
  position: number
  app_id: number
  app_name: string
  app_org: string
  company: string
  department: string
  tag: string
  score: number
  metric_type: MetricType
  value_dimension: ValueDimension
  usage_30d: number
  created_at: string
}
