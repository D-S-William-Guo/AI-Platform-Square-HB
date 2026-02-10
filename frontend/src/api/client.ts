import axios from 'axios'
import type { AppItem, RankingItem, Recommendation, RuleLink, Stats, SubmissionPayload, ImageUploadResponse, RankingDimension, Submission, HistoricalRanking } from '../types'

const client = axios.create({ baseURL: '/' })

export async function fetchApps(params?: Record<string, string>) {
  const { data } = await client.get<AppItem[]>('/api/apps', { params })
  return data
}

export async function fetchRankings(ranking_type: 'excellent' | 'trend') {
  const { data } = await client.get<RankingItem[]>('/api/rankings', { params: { ranking_type } })
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
  const { data } = await client.post('/api/submissions', payload)
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

export async function associateImageWithSubmission(
  submissionId: number,
  imageData: {
    image_url: string
    thumbnail_url: string
    original_name: string
    file_size: number
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
  const { data } = await client.post<RankingDimension>('/api/ranking-dimensions', payload)
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
  const { data } = await client.put<RankingDimension>(`/api/ranking-dimensions/${dimensionId}`, payload)
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

// 数据联动 API
export async function syncRankings() {
  const { data } = await client.post('/api/rankings/sync')
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

export async function approveSubmissionAndCreateApp(submissionId: number) {
  const { data } = await client.post(`/api/submissions/${submissionId}/approve-and-create-app`)
  return data
}

// 历史榜单查询 API
export async function fetchHistoricalRankings(
  ranking_type: 'excellent' | 'trend',
  period_date?: string
) {
  const { data } = await client.get<HistoricalRanking[]>('/api/rankings/historical', {
    params: { ranking_type, period_date }
  })
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
  period_date?: string
) {
  const { data } = await client.get<any[]>(`/api/apps/${appId}/dimension-scores`, {
    params: { period_date }
  })
  return data
}

export async function fetchDimensionScores(
  dimensionId: number,
  period_date?: string
) {
  const { data } = await client.get<any[]>(`/api/ranking-dimensions/${dimensionId}/scores`, {
    params: { period_date }
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
  score: number
) {
  const { data } = await client.put(`/api/apps/${appId}/dimension-scores/${dimensionId}`, { score })
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
  },
  adminToken: string
) {
  const { data } = await client.post('/api/admin/group-apps', payload, {
    params: { admin_token: adminToken }
  })
  return data
}
