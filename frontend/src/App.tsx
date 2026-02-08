import { useEffect, useMemo, useState } from 'react'
import { fetchApps, fetchRankings, fetchRecommendations, fetchRules, fetchStats, submitApp } from './api/client'
import type { AppItem, RankingItem, Recommendation, RuleLink, Stats, SubmissionPayload, ValueDimension } from './types'

const categories = ['全部', '办公类', '业务前台', '运维后台', '企业管理']
const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'available', label: '可用' },
  { value: 'approval', label: '需申请' },
  { value: 'beta', label: '试运行' },
  { value: 'offline', label: '已下线' }
]
const valueDimensionLabel: Record<ValueDimension, string> = {
  cost_reduction: '降本',
  efficiency_gain: '增效',
  perception_uplift: '感知提升',
  revenue_growth: '拉动收入'
}

const defaultSubmission: SubmissionPayload = {
  app_name: '',
  unit_name: '',
  contact: '',
  scenario: '',
  embedded_system: '',
  problem_statement: '',
  effectiveness_type: 'efficiency_gain',
  effectiveness_metric: '',
  data_level: 'L2',
  expected_benefit: ''
}

function rankingMetricText(row: RankingItem) {
  if (row.metric_type === 'likes') return `点赞 ${row.likes ?? 0}`
  if (row.metric_type === 'growth_rate') return `增速 +${row.score}%`
  return `综合分 ${row.score}`
}

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
  const [showSubmission, setShowSubmission] = useState(false)
  const [submission, setSubmission] = useState<SubmissionPayload>(defaultSubmission)

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

  async function onSubmit() {
    await submitApp(submission)
    setShowSubmission(false)
    setSubmission(defaultSubmission)
    alert('申报已提交，等待审核。')
  }

  return (
    <div className="page">
      <header className="header">
        <div className="brand">H E B E I · AI 应用广场</div>
        <input className="search" placeholder="搜索应用 / 场景 / 关键词" value={keyword} onChange={(e) => setKeyword(e.target.value)} />
        <div className="header-actions">
          <button className="primary" onClick={() => setShowSubmission(true)}>我要申报</button>
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
                  {statusOptions.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
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
                    <span className={`tag ${app.status}`}>{statusOptions.find((x) => x.value === app.status)?.label}</span>
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
                  <span>{valueDimensionLabel[row.value_dimension]}</span>
                  <span>{row.tag}</span>
                  <span>{rankingMetricText(row)}</span>
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
            <a key={rule.title} href={rule.href} target="_blank" rel="noreferrer">{rule.title}</a>
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
            <p>接入系统：{selectedApp.target_system}</p>
            <p>适用人群：{selectedApp.target_users}</p>
            <p>解决问题：{selectedApp.problem_statement}</p>
            <p>成效类型：{valueDimensionLabel[selectedApp.effectiveness_type]}</p>
            <p>指标评估：{selectedApp.effectiveness_metric}</p>
            <p>接入难度：{selectedApp.difficulty}</p>
            {selectedApp.access_mode === 'direct' ? (
              <p><a href={selectedApp.access_url} target="_blank" rel="noreferrer">直达使用入口</a></p>
            ) : (
              <p>该应用当前为介绍页模式，请先查看说明后申请接入。</p>
            )}
          </aside>
        </div>
      )}

      {showSubmission && (
        <div className="drawer-mask" onClick={() => setShowSubmission(false)}>
          <aside className="drawer form-drawer" onClick={(e) => e.stopPropagation()}>
            <h3>应用申报</h3>
            <input placeholder="应用名称" value={submission.app_name} onChange={(e) => setSubmission({ ...submission, app_name: e.target.value })} />
            <input placeholder="申报单位" value={submission.unit_name} onChange={(e) => setSubmission({ ...submission, unit_name: e.target.value })} />
            <input placeholder="联系人" value={submission.contact} onChange={(e) => setSubmission({ ...submission, contact: e.target.value })} />
            <input placeholder="嵌入系统" value={submission.embedded_system} onChange={(e) => setSubmission({ ...submission, embedded_system: e.target.value })} />
            <textarea placeholder="应用场景" value={submission.scenario} onChange={(e) => setSubmission({ ...submission, scenario: e.target.value })} />
            <textarea placeholder="解决的问题" value={submission.problem_statement} onChange={(e) => setSubmission({ ...submission, problem_statement: e.target.value })} />
            <select value={submission.effectiveness_type} onChange={(e) => setSubmission({ ...submission, effectiveness_type: e.target.value as ValueDimension })}>
              <option value="cost_reduction">降本</option>
              <option value="efficiency_gain">增效</option>
              <option value="perception_uplift">感知提升</option>
              <option value="revenue_growth">拉动收入</option>
            </select>
            <input placeholder="成效指标（如：工时下降30%）" value={submission.effectiveness_metric} onChange={(e) => setSubmission({ ...submission, effectiveness_metric: e.target.value })} />
            <select value={submission.data_level} onChange={(e) => setSubmission({ ...submission, data_level: e.target.value as 'L1' | 'L2' | 'L3' | 'L4' })}>
              <option value="L1">L1</option>
              <option value="L2">L2</option>
              <option value="L3">L3</option>
              <option value="L4">L4</option>
            </select>
            <textarea placeholder="预期收益" value={submission.expected_benefit} onChange={(e) => setSubmission({ ...submission, expected_benefit: e.target.value })} />
            <button className="primary" onClick={onSubmit}>提交申报</button>
          </aside>
        </div>
      )}
    </div>
  )
}

export default App
