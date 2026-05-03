import { useState } from 'react'

const GuidePage = () => {
  const [activeSection, setActiveSection] = useState('precheck')

  const sections = [
    { id: 'precheck', title: '先准备什么' },
    { id: 'submit', title: '怎么提交' },
    { id: 'update-withdraw', title: '提交后怎么管' },
    { id: 'status', title: '状态怎么看' },
    { id: 'faq', title: '常见问题' },
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
          <h3 className="guide-title">申报指南</h3>
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
          {activeSection === 'precheck' && (
            <section className="guide-section">
              <h2>申报前确认</h2>
              <div className="guide-card">
                <h3>先确认账号</h3>
                <ul>
                  <li>未登录可以浏览首页榜单、应用视图和应用详情。</li>
                  <li>提交申报和查看“我的申报”需要先登录。</li>
                  <li>如果登录后仍不能申报，请联系管理员确认账号权限。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>准备好应用信息</h3>
                <ul>
                  <li>应用名称、联系人、应用场景、嵌入系统、问题描述和预期收益。</li>
                  <li>建议提前准备封面图和详细文档，方便一次提交完整。</li>
                  <li>所属公司会优先使用当前账号信息自动带入。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>理解展示定位</h3>
                <p>
                  申报通过后的应用会进入应用视图作为展示内容。平台展示应用信息和成效，不承诺在首页或详情中提供跳转使用入口。
                </p>
              </div>
            </section>
          )}

          {activeSection === 'submit' && (
            <section className="guide-section">
              <h2>如何提交申报</h2>
              <div className="guide-card">
                <h3>操作步骤</h3>
                <ol className="process-steps">
                  <li>在首页右上角点击“我要申报”。</li>
                  <li>若未登录，系统会自动跳转到登录页；登录成功后自动回首页并打开申报弹窗。</li>
                  <li>按页面分组填写基础信息、应用信息和成效评估。</li>
                  <li>确认必填项无误后点击“提交申报”。</li>
                </ol>
              </div>
              <div className="guide-card">
                <h3>提交后去哪里看</h3>
                <ul>
                  <li>可在“我的申报”查看本人记录。</li>
                  <li>支持在“我的申报”中继续修改或撤回待审核记录。</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'update-withdraw' && (
            <section className="guide-section">
              <h2>如何修改/撤回</h2>
              <div className="guide-card">
                <h3>通过“我的申报”</h3>
                <ul>
                  <li>登录后进入“我的申报”，定位自己的申报记录。</li>
                  <li>仅 <strong>pending</strong> 状态支持修改与撤回。</li>
                  <li>修改保存后记录继续进入待审核流转；撤回后不再进入本轮审核。</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'status' && (
            <section className="guide-section">
              <h2>审核状态说明</h2>
              <div className="guide-card">
                <h3>状态与含义</h3>
                <ul>
                  <li><strong>pending</strong>：待审核，可修改/撤回。</li>
                  <li><strong>approved</strong>：审核通过，记录转为正式应用。</li>
                  <li><strong>rejected</strong>：审核未通过，请按反馈调整后重新申报。</li>
                  <li><strong>withdrawn</strong>：已由申报人撤回，不再进入本轮审核。</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'faq' && (
            <section className="guide-section">
              <h2>常见问题</h2>
              <div className="guide-card">
                <h3>Q: 为什么看不到“我要申报”？</h3>
                <p>A: 请先确认是否已登录。登录后仍不可用时，请联系管理员确认账号是否允许申报。</p>
              </div>
              <div className="guide-card">
                <h3>Q: 提交后发现写错了怎么办？</h3>
                <p>A: 只要状态还是 <strong>pending</strong>，可以在“我的申报”中修改。</p>
              </div>
              <div className="guide-card">
                <h3>Q: 申报通过后能直接使用应用吗？</h3>
                <p>A: 当前平台定位是展示和运营管理，不提供平台内跳转使用入口。具体使用方式请按业务侧安排执行。</p>
              </div>
            </section>
          )}
        </main>
      </div>

      <footer className="footer">
        <div>最近更新时间：2026-04-18 · 申报指南按现网能力维护</div>
      </footer>
    </div>
  )
}

export default GuidePage
