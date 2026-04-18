import { useState } from 'react'
import { Link } from 'react-router-dom'

const RulePage = () => {
  const [activeSection, setActiveSection] = useState('overview')

  const sections = [
    { id: 'overview', title: '规则总览' },
    { id: 'dimensions', title: '维度与权重' },
    { id: 'truth-source', title: '真相源说明' },
    { id: 'boundary', title: '管理边界' },
    { id: 'updates', title: '变更记录' },
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
              <p>当前榜单制度按治理基线执行，面向首页展示与管理端配置保持一致。</p>
              <div className="guide-card">
                <h3>固定榜单范围</h3>
                <ul>
                  <li><strong>excellent</strong>：总应用榜</li>
                  <li><strong>trend</strong>：增长趋势榜</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>当前制度边界</h3>
                <ul>
                  <li>一期聚焦双榜单，不扩展其他榜单类型。</li>
                  <li>榜单展示与管理能力通过统一管理页维护。</li>
                  <li>匿名用户可浏览榜单；管理员负责配置与发布。</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'dimensions' && (
            <section className="guide-section">
              <h2>维度与权重</h2>
              <div className="guide-card">
                <h3>默认核心维度</h3>
                <ul>
                  <li>总应用榜：用户满意度、业务价值、使用活跃度、稳定性和安全性。</li>
                  <li>增长趋势榜：使用活跃度、增长趋势、用户增长。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>权重口径</h3>
                <p>系统默认权重统一为 <strong>1.0</strong>，具体配置以管理端当前发布结果为准。</p>
              </div>
            </section>
          )}

          {activeSection === 'truth-source' && (
            <section className="guide-section">
              <h2>真相源说明</h2>
              <div className="guide-card">
                <h3>榜单参与与控制输入</h3>
                <p>唯一真相源：<code>AppRankingSetting</code>。</p>
              </div>
              <div className="guide-card">
                <h3>对外榜单读取</h3>
                <p>唯一真相源：<code>HistoricalRanking</code>。</p>
              </div>
              <div className="guide-card">
                <h3>兼容字段说明</h3>
                <p>
                  <code>App</code> / <code>Submission</code> 中的 <code>ranking_*</code> 字段仅保留兼容或展示用途，不作为榜单口径真相源。
                </p>
              </div>
            </section>
          )}

          {activeSection === 'boundary' && (
            <section className="guide-section">
              <h2>管理边界</h2>
              <div className="guide-card">
                <h3>匿名/登录用户</h3>
                <ul>
                  <li>可在首页与榜单详情查看榜单结果。</li>
                  <li>不可进入排行榜管理页。</li>
                  <li>登录后可申报，但榜单规则配置仍仅管理员可操作。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>管理员</h3>
                <ul>
                  <li>可进入排行榜管理页维护维度、配置、应用参与并执行发布。</li>
                  <li>可联动应用状态和审核流程维护榜单数据质量。</li>
                </ul>
                <Link to="/ranking-management" className="btn-primary">
                  前往排行榜管理
                </Link>
              </div>
            </section>
          )}

          {activeSection === 'updates' && (
            <section className="guide-section">
              <h2>变更记录</h2>
              <div className="guide-card">
                <h3>2026-04-18</h3>
                <ul>
                  <li>同步账号分层口径：匿名可读、登录可申报、管理员可管理。</li>
                  <li>保持双榜单与真相源说明与治理文档一致。</li>
                  <li>更新页面角色描述，避免历史权限文案歧义。</li>
                </ul>
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
