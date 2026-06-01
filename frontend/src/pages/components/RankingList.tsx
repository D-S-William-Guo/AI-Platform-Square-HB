import { Link } from 'react-router-dom'
import type { AppItem, RankingItem } from '../../types'
import LoadingState from '../../components/LoadingState'
import EmptyState from '../../components/EmptyState'
import ErrorState from '../../components/ErrorState'
import { valueDimensionLabel, rankingMetricText, appCompanyLabel } from '../homeUtils'

interface RankingListProps {
  rankings: RankingItem[]
  loading: boolean
  error: string | null
  isAdmin: boolean
  rankingDimension: string
  onAppClick: (app: AppItem) => void
}

export default function RankingList({
  rankings,
  loading,
  error,
  isAdmin,
  rankingDimension,
  onAppClick,
}: RankingListProps) {
  if (loading) {
    return <LoadingState message="正在加载最新发布榜单..." />
  }

  if (error) {
    return <ErrorState message={error} />
  }

  if (rankings.length === 0) {
    return (
      <EmptyState
        title="暂无已发布榜单"
        description="管理员发布榜单后，这里会展示最新一次正式发布结果。"
        action={
          isAdmin
            ? { label: '前往排行榜管理', to: '/ranking-management' }
            : undefined
        }
      />
    )
  }

  return (
    <section className="ranking-list">
      {rankings.map((row, index) => (
        <div className="ranking-row" key={`${row.position}-${row.app.id}`} onClick={() => onAppClick(row.app)}>
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
}
