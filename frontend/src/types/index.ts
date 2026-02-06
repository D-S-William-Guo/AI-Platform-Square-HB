export type AppItem = {
  id: number
  name: string
  org: string
  section: 'group' | 'province'
  category: string
  description: string
  status: 'available' | 'approval'
  monthly_calls: number
  release_date: string
  api_open: boolean
  difficulty: string
  contact_name: string
  highlight: string
}

export type RankingItem = {
  position: number
  tag: string
  score: number
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
