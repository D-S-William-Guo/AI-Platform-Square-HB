import { useState } from 'react'
import { Link } from 'react-router-dom'

const RulePage = () => {
  const [activeSection, setActiveSection] = useState('overview')

  const sections = [
    { id: 'overview', title: '先看结论' },
    { id: 'dimensions', title: '两个榜单怎么看' },
    { id: 'truth-source', title: '数据从哪里来' },
    { id: 'boundary', title: '没有榜单怎么办' },
    { id: 'updates', title: '管理员怎么发布' },
  ]

  return (
    <div className="page">
      <header className="header">
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
        <div className="header-actions">
          <button className="primary" onClick={() => window.history.back()}>
            <span>←</span>
            <span>返回首页</span>
          </button>
        </div>
      </header>

      <div className="body guide-page">
        <aside className="guide-sidebar">
          <h3 className="guide-title">榜单规则</h3>
          <nav className="guide-nav">
            {sections.map((section) => (
              <button
                key={section.id}
                className={`guide-nav-item ${activeSection === section.id ? 'active' : ''}`}
                onClick={() => setActiveSection(section.id)}
              >
                {section.title}
              </button>
            ))}
          </nav>
        </aside>

        <main className="guide-content">
          {activeSection === 'overview' && (
            <section className="guide-section">
              <h2>规则总览</h2>
              <p>首页展示的是最新一次正式发布的榜单快照，不展示未发布的实时计算结果。这样首页、历史榜单和运营汇报看到的是同一套口径。</p>
              <div className="guide-card">
                <h3>当前固定两张榜</h3>
                <ul>
                  <li><strong>excellent</strong>：总应用榜</li>
                  <li><strong>trend</strong>：增长趋势榜</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>展示范围</h3>
                <ul>
                  <li>当前榜单只展示省内应用表现。</li>
                  <li>集团应用进入应用视图展示，不参与当前榜单。</li>
                  <li>匿名用户可浏览榜单；管理员负责配置与发布。</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'dimensions' && (
            <section className="guide-section">
              <h2>两个榜单怎么看</h2>
              <div className="guide-card">
                <h3>总应用榜</h3>
                <ul>
                  <li>用于看综合表现更好的省内应用。</li>
                  <li>适合做优秀案例推荐、阶段性通报和重点应用观察。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>增长趋势榜</h3>
                <ul>
                  <li>用于看近期活跃、增长或用户变化更明显的省内应用。</li>
                  <li>适合发现新增长点和需要继续跟进的应用。</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'truth-source' && (
            <section className="guide-section">
              <h2>数据从哪里来</h2>
              <div className="guide-card">
                <h3>首页读取</h3>
                <p>首页读取最新一次正式发布的 <code>HistoricalRanking</code> 快照。</p>
              </div>
              <div className="guide-card">
                <h3>参与控制</h3>
                <p>哪些应用参与哪张榜，以 <code>AppRankingSetting</code> 为准。</p>
              </div>
              <div className="guide-card">
                <h3>历史追溯</h3>
                <p>历史榜单页面默认展示最新日期，也可以切换查看过去发布的榜单快照。</p>
              </div>
            </section>
          )}

          {activeSection === 'boundary' && (
            <section className="guide-section">
              <h2>没有榜单怎么办</h2>
              <div className="guide-card">
                <h3>普通用户看到空态</h3>
                <ul>
                  <li>说明当前还没有正式发布过榜单。</li>
                  <li>不是页面故障，也不是没有应用数据。</li>
                  <li>等待管理员完成榜单发布后，首页会自动展示最新结果。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>管理员处理方式</h3>
                <ul>
                  <li>进入排行榜管理，确认应用参与和维度分值。</li>
                  <li>确认无误后执行发布。</li>
                  <li>发布后首页和历史榜单会读取这次正式快照。</li>
                </ul>
                <Link to="/ranking-management" className="btn-primary">
                  前往排行榜管理
                </Link>
              </div>
            </section>
          )}

          {activeSection === 'updates' && (
            <section className="guide-section">
              <h2>管理员怎么发布</h2>
              <div className="guide-card">
                <h3>推荐流程</h3>
                <ol className="process-steps">
                  <li>进入“排行榜管理”。</li>
                  <li>维护榜单配置、应用参与和维度分值。</li>
                  <li>检查总应用榜和增长趋势榜结果。</li>
                  <li>执行发布，形成正式历史快照。</li>
                </ol>
              </div>
            </section>
          )}
        </main>
      </div>

      <footer className="footer">
        <div>最近更新时间：2026-04-18 · 榜单规则按治理基线维护</div>
      </footer>
    </div>
  )
}

export default RulePage
