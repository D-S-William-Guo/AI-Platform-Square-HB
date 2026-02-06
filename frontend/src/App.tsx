import { useEffect, useMemo, useState } from 'react'
import { fetchApps, fetchRankings, fetchRecommendations, fetchRules, fetchStats } from './api/client'
import type { AppItem, RankingItem, Recommendation, RuleLink, Stats } from './types'

const categories = ['全部', '办公类', '业务前台', '运维后台', '企业管理']

function App() {
  const [activeNav, setActiveNav] = useState<'group' | 'province' | 'ranking'>('group')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('全部')
  const [keyword, setKeyword] = useState('')
  const [apps, setApps] = useState<AppItem[]>([])
  const [rankings, setRankings] = useState<RankingItem[]>([])
  const [rankingType, setRankingType] = useState<'excellent' | 'trend'>('excellent')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [rules, setRules] = useState<RuleLink[]>([])
  const [stats, setStats] = useState<Stats>({ pending: 12, approved_period: 7, total_apps: 86 })
  const [selectedApp, setSelectedApp] = useState<AppItem | null>(null)

  useEffect(() => {
    fetchRecommendations().then(setRecommendations)
    fetchRules().then(setRules)
    fetchStats().then(setStats)
  }, [])

  useEffect(() => {
    if (activeNav === 'ranking') {
      fetchRankings(rankingType).then(setRankings)
      return
    }

    const params: Record<string, string> = { section: activeNav }
    if (statusFilter) params.status = statusFilter
    if (categoryFilter && categoryFilter !== '全部') params.category = categoryFilter
    if (keyword) params.q = keyword

    fetchApps(params).then(setApps)
  }, [activeNav, statusFilter, categoryFilter, keyword, rankingType])

  const blockTitle = useMemo(() => {
    if (activeNav === 'group') return '集团应用整合'
    if (activeNav === 'province') return '河北省自研应用 / 可调用应用'
    return 'AI 应用龙虎榜'
  }, [activeNav])

  return (
    <div className="page">
      <header className="header">
        <div className="brand">H E B E I · AI 应用广场</div>
        <input className="search" placeholder="搜索应用 / 场景 / 关键词" value={keyword} onChange={(e) => setKeyword(e.target.value)} />
        <div className="header-actions">
          <button className="primary">我要申报</button>
          <div className="avatar">张</div>
        </div>
      </header>

      <div className="body">
        <aside className="left">
          <h4>导航</h4>
          <button className={activeNav === 'group' ? 'active' : ''} onClick={() => setActiveNav('group')}>集团应用</button>
          <button className={activeNav === 'province' ? 'active' : ''} onClick={() => setActiveNav('province')}>省内应用</button>
          <button className={activeNav === 'ranking' ? 'active' : ''} onClick={() => setActiveNav('ranking')}>应用榜单</button>

          <h4>分类筛选</h4>
          {categories.map((item) => (
            <button key={item} className={categoryFilter === item ? 'active' : ''} onClick={() => setCategoryFilter(item)}>{item}</button>
          ))}
        </aside>

        <main className="main">
          <section className="block-header">
            <div>
              <h2>{blockTitle}</h2>
              <p>汇聚集团内各单位优质 AI 应用，一站式查看和申请</p>
            </div>
            {activeNav !== 'ranking' && (
              <div className="filters">
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                  <option value="">全部状态</option>
                  <option value="available">可用</option>
                  <option value="approval">需申请</option>
                </select>
                <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
                  {categories.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </div>
            )}
            {activeNav === 'ranking' && (
              <div className="filters">
                <button className={rankingType === 'excellent' ? 'active' : ''} onClick={() => setRankingType('excellent')}>优秀应用榜</button>
                <button className={rankingType === 'trend' ? 'active' : ''} onClick={() => setRankingType('trend')}>趋势榜</button>
              </div>
            )}
          </section>

          {activeNav !== 'ranking' && (
            <section className="grid">
              {apps.map((app) => (
                <article className="card" key={app.id} onClick={() => setSelectedApp(app)}>
                  <div className="card-top">
                    <h3>{app.name}</h3>
                    <span className={`tag ${app.status}`}>{app.status === 'available' ? '可用' : '需申请'}</span>
                  </div>
                  <p className="org">{app.org} · {app.category}</p>
                  <p>{app.description}</p>
                  <div className="metrics">{app.monthly_calls}k/月 · {app.release_date}</div>
                </article>
              ))}
            </section>
          )}

          {activeNav === 'ranking' && (
            <section className="ranking-list">
              {rankings.map((row) => (
                <div className="ranking-row" key={`${row.position}-${row.app.id}`} onClick={() => setSelectedApp(row.app)}>
                  <strong>#{row.position}</strong>
                  <span>{row.app.name}</span>
                  <span>{row.app.org}</span>
                  <span>{row.tag}</span>
                  <span>+{row.score}%</span>
                </div>
              ))}
            </section>
          )}
        </main>

        <aside className="right">
          <h4>本期推荐</h4>
          {recommendations.map((item) => (
            <div className="mini-card" key={item.title}>
              <strong>{item.title}</strong>
              <p>{item.scene}</p>
            </div>
          ))}

          <h4>申报统计</h4>
          <div className="stats">待审核：{stats.pending}</div>
          <div className="stats">本期已通过：{stats.approved_period}</div>
          <div className="stats">累计应用：{stats.total_apps}</div>

          <h4>快速规则</h4>
          {rules.map((rule) => (
            <a key={rule.title} href={rule.href}>{rule.title}</a>
          ))}
        </aside>
      </div>

      <footer className="footer">最近更新时间：2024-12-11 · 联系邮箱：aiapps@hebei.cn</footer>

      {selectedApp && (
        <div className="drawer-mask" onClick={() => setSelectedApp(null)}>
          <aside className="drawer" onClick={(e) => e.stopPropagation()}>
            <h3>{selectedApp.name}</h3>
            <p>{selectedApp.description}</p>
            <p>所属单位：{selectedApp.org}</p>
            <p>接入难度：{selectedApp.difficulty}</p>
            <p>API 开放：{selectedApp.api_open ? '是' : '否'}</p>
            <p>联系人：{selectedApp.contact_name}</p>
          </aside>
        </div>
      )}
    </div>
  )
}

export default App
