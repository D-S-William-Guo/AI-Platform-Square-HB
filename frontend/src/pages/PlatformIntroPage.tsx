import { useState } from 'react'

const PlatformIntroPage = () => {
  const [activeSection, setActiveSection] = useState('overview')

  const sections = [
    { id: 'overview', title: '平台定位' },
    { id: 'modules', title: '模块说明' },
    { id: 'roles', title: '角色与权限' },
    { id: 'paths', title: '典型路径' },
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
                AI 应用广场面向企业内部，聚焦“应用展示 + 申报管理 + 榜单展示”三类能力。首页当前对外聚焦集团应用、省内应用、双榜单与申报入口。
              </p>
              <div className="guide-card">
                <h3>当前边界</h3>
                <ul>
                  <li>应用来源：集团应用与省内申报应用</li>
                  <li>榜单范围：总应用榜（excellent）与增长趋势榜（trend）</li>
                  <li>申报入口：普通用户可发起申报，管理员负责审核与管理</li>
                  <li>管理员能力与普通用户能力严格隔离</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'modules' && (
            <section className="guide-section">
              <h2>模块说明</h2>
              <div className="guide-card">
                <h3>首页浏览</h3>
                <ul>
                  <li>查看集团应用、省内应用与双榜单</li>
                  <li>支持状态、分类、公司、关键词等筛选</li>
                  <li>查看应用详情与核心信息</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>申报模块</h3>
                <ul>
                  <li>开通申报权限后可见“我要申报”并提交应用信息</li>
                  <li>开通申报权限后可见“我的申报”并维护本人申报记录</li>
                  <li>支持待审核记录修改、撤回</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>管理员模块</h3>
                <ul>
                  <li>排行榜管理：榜单配置、应用参与、集团应用录入</li>
                  <li>申报审核：审批省内申报并创建应用</li>
                  <li>用户管理：维护用户角色与权限</li>
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
                  <li>可浏览首页应用与榜单</li>
                  <li>开通申报权限后可发起申报并查看“我的申报”</li>
                  <li>不可进入管理员页面</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>管理员</h3>
                <ul>
                  <li>拥有普通用户全部能力</li>
                  <li>可进入排行榜管理、申报审核、用户管理</li>
                  <li>对应用状态、榜单发布与申报审批负责</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'paths' && (
            <section className="guide-section">
              <h2>典型路径</h2>
              <div className="guide-card">
                <h3>普通用户路径</h3>
                <ol className="process-steps">
                  <li>首页浏览应用与榜单</li>
                  <li>联系管理员开通申报权限后重新登录</li>
                  <li>点击“我要申报”提交应用，并在“我的申报”跟进状态</li>
                </ol>
              </div>
              <div className="guide-card">
                <h3>管理员路径</h3>
                <ol className="process-steps">
                  <li>在“申报审核”处理待审记录</li>
                  <li>在“排行榜管理”维护应用与榜单</li>
                  <li>在“用户管理”维护账号权限</li>
                </ol>
              </div>
            </section>
          )}
        </main>
      </div>

      <footer className="footer">
        <div>最近更新时间：2026-04-15 · 平台内容按当前系统能力维护</div>
      </footer>
    </div>
  )
}

export default PlatformIntroPage
