import { useState } from 'react'
import { Link } from 'react-router-dom'

const RulePage = () => {
  const [activeSection, setActiveSection] = useState('overview')

  const sections = [
    { id: 'overview', title: '规则概览' },
    { id: 'ranking', title: '排行榜规则' },
    { id: 'evaluation', title: '评估标准' },
    { id: 'updates', title: '规则更新' }
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
              <h2>规则概览</h2>
              <p>AI 应用广场榜单规则旨在公平、公正、公开地评估和展示平台上的优秀 AI 应用，为用户提供参考，促进应用质量的提升。</p>
              
              <div className="guide-card">
                <h3>榜单目的</h3>
                <ul>
                  <li>识别和推广优秀的 AI 应用</li>
                  <li>为用户提供应用选择的参考依据</li>
                  <li>激励开发者持续优化应用</li>
                  <li>促进 AI 技术在公司内部的应用和创新</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>适用范围</h3>
                <p>本规则适用于 AI 应用广场上所有已上线的 AI 应用，包括集团应用和省内应用。</p>
              </div>

              <div className="guide-card">
                <h3>更新频率</h3>
                <p>榜单数据每周更新一次，确保数据的及时性和准确性。</p>
              </div>
            </section>
          )}

          {activeSection === 'ranking' && (
            <section className="guide-section">
              <h2>排行榜规则</h2>
              <p>AI 应用广场设有多个排行榜，每个排行榜有其特定的评估标准和规则。</p>
              
              <div className="guide-card">
                <h3>排行榜类型</h3>
                <ul>
                  <li><strong>优秀应用榜</strong>：综合评估应用的质量、用户满意度、技术创新性等因素</li>
                  <li><strong>趋势榜</strong>：评估应用的增长速度、近期活跃度等因素</li>
                  <li><strong>分类榜单</strong>：按应用分类进行排名，如办公类、业务前台类等</li>
                  <li><strong>月度之星</strong>：每月评选出的表现最突出的应用</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>上榜条件</h3>
                <ul>
                  <li>应用必须已正式上线</li>
                  <li>应用必须通过安全性和合规性审核</li>
                  <li>应用必须有一定的用户基础和使用数据</li>
                  <li>应用必须符合相关法律法规和公司政策</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>榜单展示</h3>
                <p>榜单将在 AI 应用广场首页展示，用户可以点击查看详细排名和评估数据。</p>
              </div>
            </section>
          )}

          {activeSection === 'evaluation' && (
            <section className="guide-section">
              <h2>评估标准</h2>
              <p>应用评估基于多个维度的综合考量，确保评估结果的全面性和客观性。</p>
              
              <div className="guide-card">
                <h3>核心评估指标</h3>
                <ul>
                  <li><strong>用户满意度</strong>：基于用户反馈和评分</li>
                  <li><strong>技术创新性</strong>：评估应用的技术方案和创新点</li>
                  <li><strong>业务价值</strong>：评估应用对业务的提升作用</li>
                  <li><strong>使用活跃度</strong>：基于应用的使用频率和用户数</li>
                  <li><strong>稳定性和安全性</strong>：评估应用的可靠性和安全性</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>数据来源</h3>
                <ul>
                  <li>用户使用数据和反馈</li>
                  <li>技术专家评估</li>
                  <li>业务部门反馈</li>
                  <li>系统监控数据</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>评估流程</h3>
                <ol className="process-steps">
                  <li>数据收集：收集应用的各项指标数据</li>
                  <li>数据处理：对收集到的数据进行标准化处理</li>
                  <li>综合评估：根据评估模型进行综合评分</li>
                  <li>结果审核：由专家团队对评估结果进行审核</li>
                  <li>榜单发布：在平台上发布最终的排行榜</li>
                </ol>
              </div>
            </section>
          )}

          {/* 排行维度和计算方法已整合到排行榜管理页面 */}
          {activeSection === 'ranking' && (
            <section className="guide-section">
              <h2>排行榜规则</h2>
              <p>AI 应用广场设有多个排行榜，每个排行榜有其特定的评估标准和规则。</p>
              
              <div className="guide-card">
                <h3>排行榜类型</h3>
                <ul>
                  <li><strong>优秀应用榜</strong>：综合评估应用的质量、用户满意度、技术创新性等因素</li>
                  <li><strong>趋势榜</strong>：评估应用的增长速度、近期活跃度等因素</li>
                  <li><strong>分类榜单</strong>：按应用分类进行排名，如办公类、业务前台类等</li>
                  <li><strong>月度之星</strong>：每月评选出的表现最突出的应用</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>上榜条件</h3>
                <ul>
                  <li>应用必须已正式上线</li>
                  <li>应用必须通过安全性和合规性审核</li>
                  <li>应用必须有一定的用户基础和使用数据</li>
                  <li>应用必须符合相关法律法规和公司政策</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>榜单展示</h3>
                <p>榜单将在 AI 应用广场首页展示，用户可以点击查看详细排名和评估数据。</p>
              </div>

              <div className="guide-card">
                <h3>维度管理</h3>
                <p>排行维度和计算方法已整合到统一的排行榜管理系统中，您可以通过以下链接访问：</p>
                <Link to="/ranking-management" className="btn-primary">
                  前往排行榜管理
                </Link>
              </div>
            </section>
          )}

          {activeSection === 'updates' && (
            <section className="guide-section">
              <h2>规则更新</h2>
              <p>为适应技术发展和业务需求的变化，榜单规则会定期进行评估和更新。</p>
              
              <div className="guide-card">
                <h3>更新机制</h3>
                <ul>
                  <li>每季度评估一次规则的适用性</li>
                  <li>根据业务需求和技术发展进行调整</li>
                  <li>广泛征求用户和专家的意见</li>
                  <li>发布规则更新公告</li>
                </ul>
              </div>

              <div className="guide-card">
                <h3>历史更新记录</h3>
                <div className="faq-item">
                  <h4>2024年12月</h4>
                  <p>首次发布榜单规则，建立基本的评估体系</p>
                </div>
                <div className="faq-item">
                  <h4>2025年3月</h4>
                  <p>调整权重分配，增加业务价值的权重</p>
                </div>
                <div className="faq-item">
                  <h4>2025年6月</h4>
                  <p>新增技术创新性维度的评估标准</p>
                </div>
              </div>

              <div className="guide-card">
                <h3>反馈渠道</h3>
                <p>如果您对榜单规则有任何建议或意见，欢迎通过以下渠道反馈：</p>
                <ul>
                  <li>邮箱：aiapps@hebei.cn</li>
                  <li>系统内反馈功能</li>
                  <li>定期举办的用户座谈会</li>
                </ul>
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

export default RulePage
