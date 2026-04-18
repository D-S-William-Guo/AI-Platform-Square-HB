import { useState } from 'react'

const GuidePage = () => {
  const [activeSection, setActiveSection] = useState('precheck')

  const sections = [
    { id: 'precheck', title: '申报前确认' },
    { id: 'submit', title: '如何提交申报' },
    { id: 'update-withdraw', title: '如何修改/撤回' },
    { id: 'status', title: '审核状态说明' },
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
                <h3>账号与权限</h3>
                <ul>
                  <li>未登录可浏览首页、详情和榜单。</li>
                  <li>要提交申报，需先登录账号。</li>
                  <li>管理员功能需要管理员账号登录后访问。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>关键字段准备</h3>
                <ul>
                  <li>应用名称、联系人、应用场景、嵌入系统、问题描述、预期收益等必填字段。</li>
                  <li>封面图片与详细文档可按需要上传，建议准备好后一次提交。</li>
                  <li>所属公司来自当前账号信息，页面会自动带入。</li>
                </ul>
              </div>
              <div className="guide-card">
                <h3>分类口径</h3>
                <p>
                  应用分类由系统统一配置维护，当前使用：前端市场类、客户服务类、云网运营类、管理支撑类。提交时只能选择系统当前可选项。
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
                  <li>按页面分组填写基础信息、应用信息、成效相关信息。</li>
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
                  <li>进入“我的申报”，定位目标记录。</li>
                  <li>仅 `pending` 状态支持修改与撤回。</li>
                  <li>修改保存后记录继续进入待审核流转。</li>
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
                <p>A: 当前通常是未登录状态。登录后会显示“我要申报”和“我的申报”。</p>
              </div>
              <div className="guide-card">
                <h3>Q: 提交后发现写错了怎么办？</h3>
                <p>A: 只要状态还是 `pending`，可以在“我的申报”中修改。</p>
              </div>
              <div className="guide-card">
                <h3>Q: 分类为什么和以前不一样？</h3>
                <p>A: 分类由系统统一配置维护，页面会自动读取当前生效分类列表。</p>
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
