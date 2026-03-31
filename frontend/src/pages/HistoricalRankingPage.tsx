import { useEffect, useState, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { fetchHistoricalRankings, fetchAvailableRankingDates, fetchRankingDimensions, fetchDimensionScores } from '../api/client'
import type { HistoricalRanking, RankingDimension } from '../types'

const valueDimensionLabel: Record<string, string> = {
  cost_reduction: '降本',
  efficiency_gain: '增效',
  perception_uplift: '感知提升',
  revenue_growth: '拉动收入'
}

export default function HistoricalRankingPage() {
  const [rankings, setRankings] = useState<HistoricalRanking[]>([])
  const [availableDates, setAvailableDates] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rankingType, setRankingType] = useState<'excellent' | 'trend'>('excellent')
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [rankingDimension, setRankingDimension] = useState<string>('overall')
  const [companyFilter, setCompanyFilter] = useState<string>('全部')
  const [rankingDimensions, setRankingDimensions] = useState<RankingDimension[]>([])

  const companyOptions = useMemo(() => {
    const values = rankings
      .map((item) => item.company || item.app_org)
      .filter(Boolean)
    return ['全部', ...Array.from(new Set(values))]
  }, [rankings])

  // 获取可用日期列表
  const loadAvailableDates = useCallback(async () => {
    try {
      const data = await fetchAvailableRankingDates(rankingType)
      setAvailableDates(data.dates)
      // 默认选择最新的日期
      if (data.dates.length > 0 && !selectedDate) {
        setSelectedDate(data.dates[0])
      }
    } catch (err) {
      console.error('Failed to fetch available dates:', err)
    }
  }, [rankingType, selectedDate])

  // 获取历史榜单
  const loadRankings = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      let data = await fetchHistoricalRankings(
        rankingType,
        selectedDate || undefined,
        companyFilter !== '全部' ? companyFilter : undefined
      )
      
      // 如果选择了特定维度，获取该维度的评分并重新排序
      if (rankingDimension !== 'overall') {
        const dimensionId = parseInt(rankingDimension.replace('dimension-', ''))
        if (!isNaN(dimensionId)) {
          try {
            // 获取该维度的所有应用评分
            const dimensionScores = await fetchDimensionScores(dimensionId, selectedDate, rankingType)
            // 创建应用名称到维度评分的映射（历史榜单用app_name关联）
            const scoreMap = new Map(dimensionScores.map(ds => [ds.app_id, ds.score]))
            
            // 为每个榜单项添加维度评分
            data = data.map(row => ({
              ...row,
              dimensionScore: scoreMap.get(row.app_id) || 0
            }))
            
            // 按维度评分重新排序
            data.sort((a, b) => ((b as any).dimensionScore || 0) - ((a as any).dimensionScore || 0))
            
            // 重新分配排名位置
            data = data.map((row, index) => ({
              ...row,
              position: index + 1
            }))
          } catch (error) {
            console.error('Failed to fetch dimension scores:', error)
          }
        }
      }
      
      setRankings(data)
    } catch (err) {
      setError('获取历史榜单失败')
      console.error('Failed to fetch historical rankings:', err)
    } finally {
      setLoading(false)
    }
  }, [rankingType, selectedDate, rankingDimension, companyFilter])

  useEffect(() => {
    loadAvailableDates()
    // 获取排行榜维度列表
    fetchRankingDimensions()
      .then((data) => setRankingDimensions(data.filter((item) => item.is_active)))
      .catch((error) => console.error('Failed to fetch ranking dimensions:', error))
  }, [loadAvailableDates])

  useEffect(() => {
    if (selectedDate) {
      loadRankings()
    }
  }, [loadRankings, selectedDate, rankingDimension])

  const handleDateChange = (date: string) => {
    setSelectedDate(date)
  }

  const handleTypeChange = (type: 'excellent' | 'trend') => {
    setRankingType(type)
    setSelectedDate('') // 重置日期选择
    setRankingDimension('overall') // 重置维度选择
    setCompanyFilter('全部')
  }

  return (
    <div className="page">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
        <div className="header-actions">
          <button className="primary" onClick={() => window.location.href = '/'}>
            <span>←</span>
            <span>返回首页</span>
          </button>
        </div>
      </header>

      <div className="page-container historical-ranking-page">
        <div className="page-header">
          <h1 className="page-title">历史榜单查询</h1>
          <p className="page-subtitle">查看历史榜单数据，追溯应用排名变化趋势</p>
        </div>

        {/* 筛选器 */}
        <div className="filter-bar">
          <div className="filter-group">
            <span className="filter-label">榜单类型：</span>
            <button 
              className={`filter-btn ${rankingType === 'excellent' ? 'active' : ''}`}
              onClick={() => handleTypeChange('excellent')}
            >
              总应用榜
            </button>
            <button 
              className={`filter-btn ${rankingType === 'trend' ? 'active' : ''}`}
              onClick={() => handleTypeChange('trend')}
            >
              增长趋势榜
            </button>
          </div>

          <div className="filter-group">
            <span className="filter-label">选择日期：</span>
            <select 
              className="filter-select"
              value={selectedDate}
              onChange={(e) => handleDateChange(e.target.value)}
            >
              <option value="">请选择日期</option>
              {availableDates.map((date) => (
                <option key={date} value={date}>
                  {date}
                </option>
              ))}
            </select>
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
            <span className="filter-label">公司筛选：</span>
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

          <button className="refresh-btn" onClick={loadRankings} disabled={loading}>
            {loading ? '刷新中...' : '刷新'}
          </button>
        </div>

        {/* 榜单信息 */}
        {selectedDate && (
          <div className="ranking-info">
            <h2>
              {rankingType === 'excellent' ? '总应用榜' : '增长趋势榜'} 
              <span className="date-tag">{selectedDate}</span>
            </h2>
            <p className="ranking-desc">
              共 {rankings.length} 个应用上榜
            </p>
          </div>
        )}

        {/* 榜单列表 */}
        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <span>加载中...</span>
          </div>
        ) : error ? (
          <div className="error-container">
            <span className="error-icon">❌</span>
            <span>{error}</span>
            <button className="retry-btn" onClick={loadRankings}>重试</button>
          </div>
        ) : !selectedDate ? (
          <div className="empty-container">
            <span className="empty-icon">📅</span>
            <span>请选择要查看的榜单日期</span>
          </div>
        ) : rankings.length === 0 ? (
          <div className="empty-container">
            <span className="empty-icon">📊</span>
            <span>该日期暂无榜单数据</span>
          </div>
        ) : (
          <div className="historical-ranking-list">
            {/* 表头 */}
            <div className="ranking-header">
              <span className="rank-col">排名</span>
              <span className="name-col">应用名称</span>
              <span className="org-col">所属公司 / 部门</span>
              <span className="tag-col">标签</span>
              <span className="dimension-col">价值维度</span>
              <span className="score-col">综合得分</span>
              <span className="usage-col">30日用量</span>
            </div>

            {/* 榜单数据 */}
            {rankings.map((ranking, index) => (
              <div 
                key={`${ranking.period_date}-${ranking.position}`}
                className={`ranking-row ${index < 3 ? 'top3' : ''}`}
              >
                <span className="rank-col">
                  <span className={`rank-number ${index < 3 ? 'top' : ''}`}>
                    #{ranking.position}
                  </span>
                </span>
                <span className="name-col">
                  <div className="app-name">{ranking.app_name}</div>
                </span>
                <span className="org-col">
                  <div className="app-org">{ranking.company || ranking.app_org}</div>
                  <div className="app-org">{ranking.department || '未设置'}</div>
                </span>
                <span className="tag-col">
                  <span className={`tag-badge ${ranking.tag === '推荐' ? 'recommended' : ranking.tag === '历史优秀' ? 'excellent' : 'new'}`}>
                    {ranking.tag}
                  </span>
                </span>
                <span className="dimension-col">
                  {rankingDimension === 'overall' 
                    ? (valueDimensionLabel[ranking.value_dimension] || ranking.value_dimension)
                    : `维度评分: ${(ranking as any).dimensionScore || 0}分`
                  }
                </span>
                <span className="score-col">
                  <span className="score-value">{ranking.score}</span>
                </span>
                <span className="usage-col">{ranking.usage_30d.toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}

        {/* 榜单说明 */}
        <div className="ranking-note">
          <h4>榜单说明</h4>
          <ul>
            <li>历史榜单数据每日自动保存，可查询任意日期的榜单排名</li>
            <li>榜单仅包含省内应用，集团应用不参与排名</li>
            <li>综合得分基于各维度评分加权计算得出</li>
            <li>30日用量为统计周期内的应用调用次数</li>
          </ul>
        </div>
      </div>

      <footer className="footer">
        <div>最近更新时间：2024-12-11 · 联系邮箱：aiapps@hebei.cn</div>
      </footer>
    </div>
  )
}
