import { useState } from 'react'

const PlatformIntroPage = () => {
  const [activeSection, setActiveSection] = useState('overview')

  const sections = [
    { id: 'overview', title: '这是做什么的' },
    { id: 'home', title: '首页怎么看' },
    { id: 'roles', title: '谁能做什么' },
    { id: 'paths', title: '第一次怎么用' },
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
          <h3 className="guide-title">平台介绍</h3>
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
              <h2>平台定位</h2>
              <p>
                AI 应用广场是企业内部 AI 应用的集中展示、申报审核和榜单运营入口。它帮助大家先看到已发布的优秀应用榜单，再按需查看集团应用和省内应用展示信息。
              </p>
              <div className="guide-card">
                <h3>你可以用它做什么</h3>
                <ul>
                  <li>看最新发布的总应用榜和增长趋势榜。</li>
                  <li>在应用视图中查看集团应用和省内应用展示信息。</li>
                  <li>登录后提交新的 AI 应用申报，并跟进审核状态。</li>
                  <li>管理员可审核申报、发布榜单和管理用户。</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'home' && (
            <section className="guide-section">
              <h2>首页怎么看</h2>
              <div className="guide-card">
                <h3>先看榜单</h3>
                <ul>
                  <li>首页默认展示最新一次正式发布的榜单结果。</li>
                  <li>总应用榜用于看综合表现好的省内应用。</li>
                  <li>增长趋势榜用于看近期增长和活跃变化更明显的省内应用。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>再看应用视图</h3>
                <ul>
                  <li>应用视图统一展示集团应用和省内应用。</li>
                  <li>可通过应用来源、状态、分类、公司和关键词筛选。</li>
                  <li>应用详情只做信息展示，不提供平台内跳转使用。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>需要更多说明时</h3>
                <ul>
                  <li>看“申报指南”了解如何提交应用。</li>
                  <li>看“榜单规则”了解榜单口径和发布逻辑。</li>
                  <li>看“历史榜单”追溯过去发布的榜单快照。</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'roles' && (
            <section className="guide-section">
              <h2>角色与权限</h2>
              <div className="guide-card">
                <h3>普通用户</h3>
                <ul>
                  <li>未登录可浏览首页榜单、应用视图、应用详情和历史榜单。</li>
                  <li>登录后可发起申报，并在“我的申报”查看状态。</li>
                  <li>普通用户不可进入管理员页面。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>管理员</h3>
                <ul>
                  <li>拥有普通用户全部浏览和申报能力。</li>
                  <li>可进入申报审核、排行榜管理和用户管理。</li>
                  <li>负责申报审批、榜单发布和账号权限维护。</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'paths' && (
            <section className="guide-section">
              <h2>典型路径</h2>
              <div className="guide-card">
                <h3>只想了解应用</h3>
                <ol className="process-steps">
                  <li>打开首页，先看总应用榜和增长趋势榜。</li>
                  <li>进入应用视图，按来源或关键词查找应用。</li>
                  <li>点击应用卡片查看详情。</li>
                </ol>
              </div>
              <div className="guide-card">
                <h3>想提交应用</h3>
                <ol className="process-steps">
                  <li>点击“我要申报”，未登录时先完成登录。</li>
                  <li>填写应用信息、场景、成效和附件。</li>
                  <li>提交后在“我的申报”跟进审核状态。</li>
                </ol>
              </div>
            </section>
          )}
        </main>
      </div>

      <footer className="footer">
        <div>最近更新时间：2026-04-18 · 平台内容按当前系统能力维护</div>
      </footer>
    </div>
  )
}

export default PlatformIntroPage
