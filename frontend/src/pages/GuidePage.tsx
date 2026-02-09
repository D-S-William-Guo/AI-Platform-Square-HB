import { useState } from 'react'

const GuidePage = () => {
  const [activeSection, setActiveSection] = useState('overview')

  const sections = [
    { id: 'overview', title: '指南概览' },
    { id: 'preparation', title: '申报准备' },
    { id: 'submission', title: '申报流程' },
    { id: 'review', title: '审核流程' },
    { id: 'deployment', title: '上线部署' },
    { id: 'faq', title: '常见问题' }
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
          {activeSection === 'overview' && (
            <section className="guide-section">
              <h2>指南概览</h2>
              <p>欢迎使用 AI 应用广场的应用申报系统。本指南旨在帮助您了解完整的申报流程，确保您的 AI 应用能够顺利通过审核并上线。</p>
              
              <div className="guide-card">
                <h3>申报流程总览</h3>
                <ol className="process-steps">
                  <li>准备申报材料</li>
                  <li>填写申报表单</li>
                  <li>提交审核</li>
                  <li>等待审核结果</li>
                  <li>应用上线部署</li>
                </ol>
              </div>

              <div className="guide-card">
                <h3>申报要求</h3>
                <ul>
                  <li>应用必须符合国家相关法律法规和公司内部规定</li>
                  <li>应用必须具有明确的应用场景和业务价值</li>
                  <li>应用必须经过充分的测试和验证</li>
                  <li>申报材料必须真实、完整、准确</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'preparation' && (
            <section className="guide-section">
              <h2>申报准备</h2>
              <p>在开始申报前，请确保您已准备好以下材料和信息：</p>
              
              <div className="guide-card">
                <h3>必备材料</h3>
                <ul>
                  <li>应用名称和简介</li>
                  <li>应用场景详细描述</li>
                  <li>技术架构说明</li>
                  <li>应用截图或演示视频</li>
                  <li>安全性评估报告</li>
                  <li>性能测试报告</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>信息准备</h3>
                <ul>
                  <li>申报单位信息</li>
                  <li>联系人姓名和联系方式</li>
                  <li>应用分类和标签</li>
                  <li>预期用户群体</li>
                  <li>预期效益和影响</li>
                  <li>数据使用说明</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>技术要求</h3>
                <ul>
                  <li>应用必须符合公司技术规范</li>
                  <li>必须提供完整的API文档</li>
                  <li>必须支持标准的集成方式</li>
                  <li>必须具备完善的错误处理机制</li>
                  <li>必须符合安全性要求</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'submission' && (
            <section className="guide-section">
              <h2>申报流程</h2>
              <p>以下是详细的申报流程：</p>
              
              <div className="guide-card">
                <h3>步骤 1：登录系统</h3>
                <p>使用您的公司账号登录 AI 应用广场系统。</p>
              </div>

              <div className="guide-card">
                <h3>步骤 2：填写申报表单</h3>
                <p>点击首页的"我要申报"按钮，进入申报表单页面，填写以下信息：</p>
                <ul>
                  <li>基本信息：应用名称、申报单位、联系人等</li>
                  <li>应用信息：应用场景、嵌入系统、解决的问题等</li>
                  <li>成效评估：成效类型、数据级别、成效指标等</li>
                  <li>上传应用封面图</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>步骤 3：提交审核</h3>
                <p>确认所有信息填写完整后，点击"提交申报"按钮，系统将自动生成申报编号。</p>
              </div>

              <div className="guide-card">
                <h3>步骤 4：查看申报状态</h3>
                <p>提交后，您可以在系统中查看申报的审核状态和进度。</p>
              </div>
            </section>
          )}

          {activeSection === 'review' && (
            <section className="guide-section">
              <h2>审核流程</h2>
              <p>申报提交后，将进入以下审核流程：</p>
              
              <div className="guide-card">
                <h3>审核阶段</h3>
                <ol className="process-steps">
                  <li>
                    <strong>初步审核</strong>
                    <p>审核申报材料的完整性和合规性，预计耗时 1-2 个工作日。</p>
                  </li>
                  <li>
                    <strong>技术审核</strong>
                    <p>由技术专家评估应用的技术架构、安全性和可靠性，预计耗时 2-3 个工作日。</p>
                  </li>
                  <li>
                    <strong>业务审核</strong>
                    <p>评估应用的业务价值和可行性，预计耗时 2-3 个工作日。</p>
                  </li>
                  <li>
                    <strong>合规审核</strong>
                    <p>审核应用是否符合相关法律法规和公司政策，预计耗时 1-2 个工作日。</p>
                  </li>
                  <li>
                    <strong>最终审批</strong>
                    <p>由相关领导进行最终审批，预计耗时 1-2 个工作日。</p>
                  </li>
                </ol>
              </div>

              <div className="guide-card">
                <h3>审核结果</h3>
                <ul>
                  <li><strong>通过</strong>：应用符合所有要求，可以进入上线部署阶段。</li>
                  <li><strong>退回修改</strong>：应用需要进行部分修改后重新提交审核。</li>
                  <li><strong>不通过</strong>：应用不符合要求，无法上线。</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>审核反馈</h3>
                <p>无论审核结果如何，我们都会提供详细的审核反馈，帮助您了解审核过程中发现的问题和改进建议。</p>
              </div>
            </section>
          )}

          {activeSection === 'deployment' && (
            <section className="guide-section">
              <h2>上线部署</h2>
              <p>审核通过后，应用将进入上线部署阶段：</p>
              
              <div className="guide-card">
                <h3>部署流程</h3>
                <ol className="process-steps">
                  <li>
                    <strong>部署准备</strong>
                    <p>准备部署环境和相关配置，预计耗时 1-2 个工作日。</p>
                  </li>
                  <li>
                    <strong>应用部署</strong>
                    <p>将应用部署到生产环境，预计耗时 1 个工作日。</p>
                  </li>
                  <li>
                    <strong>测试验证</strong>
                    <p>进行上线前的最终测试和验证，预计耗时 1-2 个工作日。</p>
                  </li>
                  <li>
                    <strong>正式上线</strong>
                    <p>应用正式上线，对所有用户开放。</p>
                  </li>
                </ol>
              </div>

              <div className="guide-card">
                <h3>上线后管理</h3>
                <ul>
                  <li>应用将在 AI 应用广场中展示</li>
                  <li>您需要定期更新应用信息和维护应用</li>
                  <li>您需要收集和反馈用户使用情况</li>
                  <li>您需要根据用户反馈持续优化应用</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>应用监控</h3>
                <p>上线后，系统将对应用进行实时监控，包括：</p>
                <ul>
                  <li>性能监控</li>
                  <li>可用性监控</li>
                  <li>安全性监控</li>
                  <li>用户使用情况监控</li>
                </ul>
              </div>
            </section>
          )}

          {activeSection === 'faq' && (
            <section className="guide-section">
              <h2>常见问题</h2>
              
              <div className="guide-card">
                <h3>申报相关问题</h3>
                <div className="faq-item">
                  <h4>Q: 哪些类型的应用可以申报？</h4>
                  <p>A: 所有符合公司业务需求、技术规范和法律法规的 AI 应用都可以申报，包括但不限于办公类、业务前台、运维后台和企业管理类应用。</p>
                </div>
                <div className="faq-item">
                  <h4>Q: 申报需要多长时间才能完成审核？</h4>
                  <p>A: 完整的审核流程预计需要 7-14 个工作日，具体时间可能会因应用复杂度和审核队列情况而有所不同。</p>
                </div>
                <div className="faq-item">
                  <h4>Q: 申报过程中需要技术支持怎么办？</h4>
                  <p>A: 您可以通过系统中的技术支持渠道获取帮助，或联系 AI 应用广场的管理员。</p>
                </div>
              </div>

              <div className="guide-card">
                <h3>技术相关问题</h3>
                <div className="faq-item">
                  <h4>Q: 应用需要满足哪些技术要求？</h4>
                  <p>A: 应用需要符合公司的技术规范，包括安全性、性能、可靠性等方面的要求，具体要求可以参考技术文档。</p>
                </div>
                <div className="faq-item">
                  <h4>Q: 应用如何与公司现有系统集成？</h4>
                  <p>A: 应用需要提供标准的 API 接口，支持与公司现有系统的集成，具体集成方式可以参考集成文档。</p>
                </div>
                <div className="faq-item">
                  <h4>Q: 应用的数据安全如何保障？</h4>
                  <p>A: 应用需要符合公司的数据安全要求，包括数据加密、访问控制、审计日志等方面的措施。</p>
                </div>
              </div>

              <div className="guide-card">
                <h3>其他问题</h3>
                <div className="faq-item">
                  <h4>Q: 应用上线后如何获取用户反馈？</h4>
                  <p>A: 系统会提供用户反馈渠道，您可以通过这些渠道收集和分析用户反馈，持续优化应用。</p>
                </div>
                <div className="faq-item">
                  <h4>Q: 应用上线后可以修改吗？</h4>
                  <p>A: 可以，您可以通过系统提交应用更新申请，经过审核后可以对应用进行修改和更新。</p>
                </div>
                <div className="faq-item">
                  <h4>Q: 应用的知识产权如何保护？</h4>
                  <p>A: 应用的知识产权归申报单位所有，公司会采取相应措施保护应用的知识产权。</p>
                </div>
              </div>
            </section>
          )}
        </main>
      </div>

      <footer className="footer">
        <div>最近更新时间：2024-12-11 · 联系邮箱：aiapps@hebei.cn</div>
      </footer>
    </div>
  )
}

export default GuidePage
