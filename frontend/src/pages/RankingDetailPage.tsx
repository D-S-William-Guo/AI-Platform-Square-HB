import { useEffect, useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchRankingConfigWithDimensions, fetchRankingsByConfig, fetchRankingDimensions } from '../api/client'
import type { RankingItem, RankingDimension } from '../types'

interface DimensionConfig {
  dim_id: number
  weight: number
}

interface RankingConfigDetail {
  id: string
  name: string
  description: string
  dimensions: DimensionConfig[]
  calculation_method: string
  is_active: boolean
  created_at: string
  updated_at: string
}

const valueDimensionLabel: Record<string, string> = {
  cost_reduction: '降本',
  efficiency_gain: '增效',
  perception_uplift: '感知提升',
  revenue_growth: '拉动收入'
}

// 生成渐变色
function getGradient(id: number) {
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

export default function RankingDetailPage() {
  const { configId } = useParams<{ configId: string }>()
  const [config, setConfig] = useState<RankingConfigDetail | null>(null)
  const [rankings, setRankings] = useState<RankingItem[]>([])
  const [dimensions, setDimensions] = useState<RankingDimension[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedApp, setSelectedApp] = useState<RankingItem | null>(null)

  useEffect(() => {
    if (!configId) return

    const loadData = async () => {
      try {
        setLoading(true)
        setError(null)

        // 并行加载数据
        const [configData, rankingsData, dimensionsData] = await Promise.all([
          fetchRankingConfigWithDimensions(configId),
          fetchRankingsByConfig(configId),
          fetchRankingDimensions()
        ])

        setConfig(configData)
        setRankings(rankingsData)
        setDimensions(dimensionsData.filter(d => d.is_active))
      } catch (err) {
        console.error('Failed to load ranking data:', err)
        setError('加载榜单数据失败')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [configId])

  // 获取该榜单配置的维度详情
  const configDimensions = useMemo(() => {
    if (!config || !dimensions.length) return []
    
    return config.dimensions
      .map(dimConfig => {
        const dimension = dimensions.find(d => d.id === dimConfig.dim_id)
        if (!dimension) return null
        return {
          ...dimension,
          weight: dimConfig.weight
        }
      })
      .filter(Boolean) as (RankingDimension & { weight: number })[]
  }, [config, dimensions])

  // 计算总分
  const totalWeight = useMemo(() => {
    return configDimensions.reduce((sum, d) => sum + d.weight, 0)
  }, [configDimensions])

  if (loading) {
    return (
      <div className="ranking-detail-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    )
  }

  if (error || !config) {
    return (
      <div className="ranking-detail-page">
        <div className="error-container">
          <span className="error-icon">❌</span>
          <p>{error || '榜单不存在'}</p>
          <Link to="/" className="back-link">返回首页</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="ranking-detail-page">
      {/* 头部 */}
      <header className="detail-header">
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
        <Link to="/" className="back-btn">
          <span>←</span>
          <span>返回首页</span>
        </Link>
      </header>

      {/* 榜单信息 */}
      <section className="config-info">
        <div className="config-header">
          <h1 className="config-title">
            <span className="config-icon">
              {config.id === 'excellent' ? '🏆' : config.id === 'trend' ? '📈' : '🏅'}
            </span>
            {config.name}
          </h1>
          <span className={`config-status ${config.is_active ? 'active' : 'inactive'}`}>
            {config.is_active ? '进行中' : '已停用'}
          </span>
        </div>
        
        <p className="config-description">{config.description}</p>
        
        <div className="config-meta">
          <span className="meta-item">
            <span className="meta-label">计算公式:</span>
            <span className="meta-value">
              {config.calculation_method === 'composite' ? '综合评分' : '增长率'}
            </span>
          </span>
          <span className="meta-item">
            <span className="meta-label">参与应用:</span>
            <span className="meta-value">{rankings.length} 个</span>
          </span>
        </div>

        {/* 维度配置 */}
        <div className="dimensions-section">
          <h3 className="section-title">评价维度</h3>
          <div className="dimensions-list">
            {configDimensions.map((dim, index) => (
              <div 
                key={dim.id} 
                className="dimension-item"
                style={{ '--weight-percent': `${(dim.weight / totalWeight) * 100}%` } as React.CSSProperties}
              >
                <div className="dimension-info">
                  <span className="dimension-name">{dim.name}</span>
                  <span className="dimension-weight">权重 {dim.weight}</span>
                </div>
                <div className="dimension-bar">
                  <div 
                    className="dimension-bar-fill"
                    style={{ width: `${(dim.weight / totalWeight) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 排名列表 */}
      <section className="rankings-section">
        <div className="rankings-header">
          <h2 className="section-title">最新排名</h2>
          <span className="update-time">更新时间: {new Date().toLocaleDateString()}</span>
        </div>

        {rankings.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">📊</span>
            <p>暂无排名数据</p>
          </div>
        ) : (
          <div className="rankings-list">
            {rankings.map((row, index) => (
              <div 
                className={`ranking-item ${index < 3 ? 'top3' : ''}`}
                key={row.app.id}
                onClick={() => setSelectedApp(row)}
              >
                <div className="rank-position">
                  <span className="rank-number">#{row.position}</span>
                  {index < 3 && <span className="rank-medal">{['🥇', '🥈', '🥉'][index]}</span>}
                </div>
                
                <div className="rank-app">
                  <div 
                    className="app-avatar"
                    style={{ background: getGradient(row.app.id) }}
                  >
                    {row.app.name.charAt(0)}
                  </div>
                  <div className="app-info">
                    <span className="app-name">{row.app.name}</span>
                    <span className="app-org">{row.app.org}</span>
                  </div>
                </div>

                <div className="rank-dimension">
                  {valueDimensionLabel[row.value_dimension] || row.value_dimension}
                </div>

                <span className={`rank-tag ${row.tag === '推荐' ? 'recommended' : row.tag === '历史优秀' ? 'excellent' : 'new'}`}>
                  {row.tag}
                </span>

                <div className="rank-score">
                  <span className="score-value">{row.score}</span>
                  <span className="score-label">综合分</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 应用详情弹窗 */}
      {selectedApp && (
        <div className="modal-overlay" onClick={() => setSelectedApp(null)}>
          <div className="modal-container ranking-app-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-section">
                <h3 className="modal-title">{selectedApp.app.name}</h3>
                <div className="modal-subtitle">
                  <span className="modal-rank">排名 #{selectedApp.position}</span>
                  <span className="modal-score">综合分 {selectedApp.score}</span>
                </div>
              </div>
              <button className="modal-close" onClick={() => setSelectedApp(null)}>×</button>
            </div>

            <div className="modal-body">
              <div className="app-detail-section">
                <h4 className="section-title">基本信息</h4>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">所属单位</span>
                    <span className="detail-value">{selectedApp.app.org}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">应用分类</span>
                    <span className="detail-value">{selectedApp.app.category}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">成效类型</span>
                    <span className="detail-value">{valueDimensionLabel[selectedApp.value_dimension]}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">30日调用</span>
                    <span className="detail-value">{selectedApp.usage_30d} 次</span>
                  </div>
                </div>
              </div>

              <div className="app-detail-section">
                <h4 className="section-title">榜单表现</h4>
                <div className="performance-stats">
                  <div className="stat-box">
                    <span className="stat-value">{selectedApp.position}</span>
                    <span className="stat-label">当前排名</span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-value">{selectedApp.score}</span>
                    <span className="stat-label">综合得分</span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-value">{selectedApp.tag}</span>
                    <span className="stat-label">榜单标签</span>
                  </div>
                </div>
              </div>

              <div className="app-detail-section">
                <h4 className="section-title">应用场景</h4>
                <p className="app-description">{selectedApp.app.description}</p>
              </div>
            </div>

            <div className="modal-footer">
              <button className="modal-btn secondary" onClick={() => setSelectedApp(null)}>
                关闭
              </button>
              <Link 
                to="/" 
                className="modal-btn primary"
                onClick={() => setSelectedApp(null)}
              >
                查看应用详情
              </Link>
            </div>
          </div>
        </div>
      )}

      <footer className="detail-footer">
        <div>最近更新时间：{new Date().toLocaleDateString()} · 联系邮箱：aiapps@hebei.cn</div>
      </footer>
    </div>
  )
}
