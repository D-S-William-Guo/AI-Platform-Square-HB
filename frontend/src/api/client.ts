import axios from 'axios'
import type { AppItem, RankingItem, Recommendation, RuleLink, Stats, SubmissionPayload, ImageUploadResponse } from '../types'

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
