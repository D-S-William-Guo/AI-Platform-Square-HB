import axios from 'axios'
import type {
  AdminUserCreatePayload,
  AppItem,
  AuthProviderInfo,
  AuthLoginResponse,
  AuthMeResponse,
  AuthUser,
  RankingItem,
  Recommendation,
  RuleLink,
  Stats,
  SubmissionPayload,
  ImageUploadResponse,
  DocumentUploadResponse,
  RankingDimension,
  PaginatedResponse,
  RankingConfigRecord,
  Submission,
  HistoricalRanking
} from '../types'

const client = axios.create({ baseURL: '/', withCredentials: true })
const MISSING_ADMIN_TOKEN_ERROR_CODE = 'MISSING_ADMIN_TOKEN'

export class MissingAdminTokenError extends Error {
  code = MISSING_ADMIN_TOKEN_ERROR_CODE

  constructor() {
    super('Missing admin auth. Login as an admin user.')
    this.name = 'MissingAdminTokenError'
  }
}

export function isMissingAdminTokenError(error: unknown): boolean {
  void error
  return false
}

export function getAdminTokenSetupHint(): string {
  return '请先登录管理员账号。'
}

export function getAuthToken() {
  return ''
}

export function setAuthToken(token: string) {
  void token
}

export function clearAuthToken() {
}

export async function login(username: string, password: string) {
  const { data } = await client.post<AuthLoginResponse>('/api/auth/login', { username, password })
  return data
}

export async function fetchAuthMe() {
  const { data } = await client.get<AuthMeResponse>('/api/auth/me')
  return data
}

export async function fetchAuthProviderInfo() {
  const { data } = await client.get<AuthProviderInfo>('/api/auth/provider')
  return data
}

export async function logout() {
  await client.post('/api/auth/logout')
}

export async function fetchApps(params?: Record<string, string>) {
  const { data } = await client.get<AppItem[]>('/api/apps', { params })
  return data
}

export async function fetchRankings(
  ranking_type: 'excellent' | 'trend',
  company?: string
) {
  const { data } = await client.get<RankingItem[]>('/api/rankings', {
    params: { ranking_type, ...(company ? { company } : {}) },
  })
  return data
}

export async function fetchRecommendations() {
  const { data } = await client.get<Recommendation[]>('/api/recommendations')
  return data
}

export async function fetchStats() {
  const { data } = await client.get<Stats>('/api/stats')
  return data
}

export async function fetchRules() {
  const { data } = await client.get<RuleLink[]>('/api/rules')
  return data
}

export async function submitApp(payload: SubmissionPayload) {
  const { data } = await client.post<Submission>('/api/submissions', payload)
  return data
}

export async function fetchSubmissionSelf(manageToken: string) {
  const { data } = await client.get<Submission>('/api/submissions/self', {
    params: { manage_token: manageToken }
  })
  return data
}

export async function fetchMySubmissions() {
  const { data } = await client.get<Submission[]>('/api/submissions/mine')
  return data
}

export async function updateSubmissionSelf(
  submissionId: number,
  payload: SubmissionPayload & { manage_token: string }
) {
  const { data } = await client.put<Submission>(`/api/submissions/${submissionId}/self`, payload)
  return data
}

export async function updateMySubmission(submissionId: number, payload: SubmissionPayload) {
  const { data } = await client.put<Submission>(`/api/submissions/${submissionId}/mine`, payload)
  return data
}

export async function withdrawSubmissionSelf(submissionId: number, manageToken: string) {
  const { data } = await client.post(`/api/submissions/${submissionId}/withdraw`, {
    manage_token: manageToken
  })
  return data
}

export async function withdrawMySubmission(submissionId: number) {
  const { data } = await client.post(`/api/submissions/${submissionId}/mine/withdraw`)
  return data
}

// Image upload API
export async function uploadImage(file: File): Promise<ImageUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  
  const { data } = await client.post<ImageUploadResponse>('/api/upload/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await client.post<DocumentUploadResponse>('/api/upload/document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function associateImageWithSubmission(
  submissionId: number,
  imageData: {
    image_url: string
    thumbnail_url: string
    original_name: string
    file_size: number
    mime_type?: string
    is_cover?: boolean
  }
) {
  const { data } = await client.post(`/api/submissions/${submissionId}/images`, imageData)
  return data
}

export async function getSubmissionImages(submissionId: number) {
  const { data } = await client.get(`/api/submissions/${submissionId}/images`)
  return data
}

// 排行维度管理 API
export async function fetchRankingDimensions() {
  const { data } = await client.get<RankingDimension[]>('/api/ranking-dimensions')
  return data
}

export async function createRankingDimension(payload: {
  name: string
  description: string
  calculation_method: string
  weight: number
  is_active: boolean
}) {
  const { data } = await client.post<RankingDimension>('/api/ranking-dimensions', payload, {
  })
  return data
}

export async function updateRankingDimension(
  dimensionId: number,
  payload: {
    name?: string
    description?: string
    calculation_method?: string
    weight?: number
    is_active?: boolean
  }
) {
  const { data } = await client.put<RankingDimension>(`/api/ranking-dimensions/${dimensionId}`, payload, {
  })
  return data
}

export async function deleteRankingDimension(dimensionId: number) {
  const { data } = await client.delete(`/api/ranking-dimensions/${dimensionId}`)
  return data
}

export async function fetchRankingLogs() {
  const { data } = await client.get<any[]>('/api/ranking-logs')
  return data
}

export async function fetchRankingAuditLogs() {
  const { data } = await client.get<any[]>('/api/ranking-audit-logs')
  return data
}

// 数据联动 API
export async function syncRankings() {
  const { data } = await client.post('/api/rankings/sync')
  return data
}

export async function publishRankings() {
  const { data } = await client.post('/api/rankings/publish')
  return data
}

export async function batchUpdateRankingParams(
  apps: number[],
  params: {
    ranking_weight?: number
    ranking_enabled?: boolean
    ranking_tags?: string
  }
) {
  const { data } = await client.post('/api/apps/batch-update-ranking-params', {
    apps,
    ...params
  })
  return data
}

export async function fetchSubmissions() {
  const { data } = await client.get<Submission[]>('/api/submissions')
  return data
}

export async function approveSubmissionAndCreateApp(
  submissionId: number,
  payload?: {
    status?: 'available' | 'approval' | 'beta' | 'offline'
    monthly_calls?: number
    difficulty?: string
    target_system?: string
    target_users?: string
    access_mode?: 'direct' | 'profile'
    access_url?: string
  }
) {
  const { data } = await client.post(`/api/submissions/${submissionId}/approve-and-create-app`, payload)
  return data
}

export async function rejectSubmission(submissionId: number, reason: string) {
  const { data } = await client.post(`/api/submissions/${submissionId}/reject`, { reason })
  return data
}

// 历史榜单查询 API
export async function fetchHistoricalRankings(
  ranking_type: 'excellent' | 'trend',
  period_date?: string,
  company?: string
) {
  const { data } = await client.get<HistoricalRanking[]>('/api/rankings/historical', {
    params: { ranking_type, period_date, ...(company ? { company } : {}) }
  })
  return data
}

export async function fetchAdminUsers(params?: {
  q?: string
  role?: 'user' | 'admin'
  is_active?: boolean
  page?: number
  page_size?: number
}) {
  const { data } = await client.get<PaginatedResponse<AuthUser>>('/api/admin/users', { params })
  return data
}

export async function createAdminUser(payload: AdminUserCreatePayload) {
  const { data } = await client.post<AuthUser>('/api/admin/users', payload)
  return data
}

export async function updateAdminUserRole(userId: number, role: 'user' | 'admin') {
  const { data } = await client.put<AuthUser>(`/api/admin/users/${userId}/role`, { role })
  return data
}

export async function updateAdminUserStatus(userId: number, is_active: boolean) {
  const { data } = await client.put<AuthUser>(`/api/admin/users/${userId}/status`, { is_active })
  return data
}

export async function updateAdminUserSubmitPermission(userId: number, can_submit: boolean) {
  const { data } = await client.put<AuthUser>(`/api/admin/users/${userId}/submit-permission`, { can_submit })
  return data
}

export async function fetchAvailableRankingDates(ranking_type: 'excellent' | 'trend') {
  const { data } = await client.get<{ dates: string[] }>('/api/rankings/available-dates', {
    params: { ranking_type }
  })
  return data
}

// 应用维度评分 API
export async function fetchAppDimensionScores(
  appId: number,
  period_date?: string,
  ranking_config_id?: string
) {
  const { data } = await client.get<any[]>(`/api/apps/${appId}/dimension-scores`, {
    params: { period_date, ranking_config_id }
  })
  return data
}

export async function fetchDimensionScores(
  dimensionId: number,
  period_date?: string,
  ranking_config_id?: string
) {
  const { data } = await client.get<any[]>(`/api/ranking-dimensions/${dimensionId}/scores`, {
    params: { period_date, ranking_config_id }
  })
  return data
}

// 更新应用排行参数 API
export async function updateAppRankingParams(
  appId: number,
  params: {
    ranking_enabled?: boolean
    ranking_weight?: number
    ranking_tags?: string
  }
) {
  const { data } = await client.put(`/api/apps/${appId}/ranking-params`, params)
  return data
}

// 更新应用维度评分 API
export async function updateAppDimensionScore(
  appId: number,
  dimensionId: number,
  score: number,
  ranking_config_id?: string
) {
  const { data } = await client.put(`/api/apps/${appId}/dimension-scores/${dimensionId}`, { score }, {
    params: ranking_config_id ? { ranking_config_id } : {},
  })
  return data
}

// 集团应用录入 API（管理员专用）
export async function createGroupApp(
  payload: {
    name: string
    org: string
    category: string
    description: string
    status?: string
    monthly_calls?: number
    api_open?: boolean
    difficulty?: string
    contact_name?: string
    highlight?: string
    access_mode?: string
    access_url?: string
    target_system?: string
    target_users?: string
    problem_statement?: string
    effectiveness_type?: string
    effectiveness_metric?: string
    cover_image_url?: string
    ranking_enabled?: boolean
    ranking_weight?: number
    ranking_tags?: string
  }
) {
  const { data } = await client.post('/api/admin/group-apps', payload)
  return data
}

export async function fetchAdminApps(params?: {
  section?: 'group' | 'province'
  status?: 'available' | 'approval' | 'beta' | 'offline'
  company?: string
  q?: string
  page?: number
  page_size?: number
}) {
  const { data } = await client.get<PaginatedResponse<AppItem>>('/api/admin/apps', {
    params: params || {},
  })
  return data
}

export async function fetchAdminRankingConfigs(params?: {
  is_active?: boolean
  q?: string
  page?: number
  page_size?: number
}) {
  const { data } = await client.get<PaginatedResponse<RankingConfigRecord>>('/api/admin/ranking-configs', {
    params: params || {},
  })
  return data
}

export async function updateAdminAppStatus(
  appId: number,
  status: 'available' | 'approval' | 'beta' | 'offline'
) {
  const { data } = await client.put(
    `/api/admin/apps/${appId}/status`,
    { status },
    {}
  )
  return data
}

// ==================== 三层架构排行榜系统 API ====================

// 榜单配置 API
export async function fetchRankingConfigs(is_active?: boolean) {
  const { data } = await client.get<RankingConfigRecord[]>('/api/ranking-configs', {
    params: is_active !== undefined ? { is_active } : {},
  })
  return data
}

export async function fetchRankingConfig(configId: string) {
  const { data } = await client.get<any>(`/api/ranking-configs/${configId}`)
  return data
}

export async function fetchRankingConfigWithDimensions(configId: string) {
  const { data } = await client.get<any>(`/api/ranking-configs/${configId}/with-dimensions`)
  return data
}

export async function createRankingConfig(payload: {
  id: string
  name: string
  description?: string
  dimensions_config?: string
  calculation_method?: string
  is_active?: boolean
}) {
  const { data } = await client.post('/api/ranking-configs', payload)
  return data
}

export async function updateRankingConfig(
  configId: string,
  payload: {
    name?: string
    description?: string
    dimensions_config?: string
    calculation_method?: string
    is_active?: boolean
  }
) {
  const { data } = await client.put(`/api/ranking-configs/${configId}`, payload)
  return data
}

export async function deleteRankingConfig(configId: string) {
  const { data } = await client.delete(`/api/ranking-configs/${configId}`)
  return data
}

// 应用榜单设置 API
export async function fetchAppRankingSettings(appId: number) {
  const { data } = await client.get<any[]>(`/api/apps/${appId}/ranking-settings`)
  return data
}

// 获取所有应用榜单设置（支持按榜单配置筛选）
export async function fetchAllAppRankingSettings(rankingConfigId?: string) {
  const { data } = await client.get<any[]>('/api/app-ranking-settings', {
    params: rankingConfigId ? { ranking_config_id: rankingConfigId } : {},
  })
  return data
}

export async function createAppRankingSetting(
  appId: number,
  payload: {
    ranking_config_id: string
    is_enabled?: boolean
    weight_factor?: number
    custom_tags?: string
  }
) {
  const { data } = await client.post(`/api/apps/${appId}/ranking-settings`, payload)
  return data
}

export async function updateAppRankingSetting(
  appId: number,
  settingId: number,
  payload: {
    ranking_config_id?: string
    is_enabled?: boolean
    weight_factor?: number
    custom_tags?: string
  }
) {
  const { data } = await client.put(`/api/apps/${appId}/ranking-settings/${settingId}`, payload)
  return data
}

export async function deleteAppRankingSetting(appId: number, settingId: number) {
  const { data } = await client.delete(`/api/apps/${appId}/ranking-settings/${settingId}`)
  return data
}

export async function saveAppRankingSetting(
  appId: number,
  payload: {
    setting_id?: number
    ranking_config_id: string
    is_enabled: boolean
    weight_factor: number
    custom_tags: string
    dimension_scores: Array<{ dimension_id: number; score: number }>
  }
) {
  const { data } = await client.post(`/api/apps/${appId}/ranking-settings/save`, payload)
  return data
}

// 获取榜单排名数据（新API - 支持按榜单配置ID查询）
export async function fetchRankingsByConfig(configId: string, company?: string) {
  const { data } = await client.get<RankingItem[]>('/api/rankings', {
    params: { ranking_config_id: configId, ...(company ? { company } : {}) },
  })
  return data
}

// 获取应用在各维度的得分（用于榜单详情页展示）
export async function fetchAppDimensionScoresForConfig(
  appId: number,
  configId: string
) {
  const { data } = await client.get<any[]>(`/api/apps/${appId}/dimension-scores`, {
    params: { ranking_config_id: configId }
  })
  return data
}
