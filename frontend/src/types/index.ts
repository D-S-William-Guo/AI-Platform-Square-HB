export type AppStatus = 'available' | 'approval' | 'beta' | 'offline'
export type MetricType = 'composite' | 'growth_rate' | 'likes'
export type ValueDimension = 'cost_reduction' | 'efficiency_gain' | 'perception_uplift' | 'revenue_growth'

export type AppItem = {
  id: number
  name: string
  org: string
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
  position: number
  tag: string
  score: number
  likes: number | null
  metric_type: MetricType
  value_dimension: ValueDimension
  usage_30d: number
  declared_at: string
  app: AppItem
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
  cover_image_url: string
  // 排行榜相关字段
  ranking_enabled: boolean
  ranking_weight: number
  ranking_tags: string
  ranking_dimensions: string
}

export type ImageUploadResponse = {
  success: boolean
  image_url: string
  thumbnail_url: string
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
