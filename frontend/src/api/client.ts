import axios from 'axios'
import type { AppItem, RankingItem, Recommendation, RuleLink, Stats } from '../types'

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
