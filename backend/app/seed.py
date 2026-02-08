from datetime import date

from sqlalchemy.orm import Session

from .models import App, Ranking


APPS = [
    dict(
        name="智能客服助手",
        org="河北移动",
        section="group",
        category="办公类",
        description="基于大模型的智能客服系统，支持多轮对话和自动工单创建",
        status="available",
        monthly_calls=15.4,
        release_date=date(2024, 3, 1),
        api_open=True,
        difficulty="Low",
        contact_name="李静",
        highlight="7×24 自动应答",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/customer-service",
        target_system="客服工单系统",
        target_users="客服代表、班组长",
        problem_statement="人工应答效率低、高峰时段排队严重",
        effectiveness_type="efficiency_gain",
        effectiveness_metric="平均应答时长下降 42%",
    ),
    dict(
        name="文档智能分析",
        org="河北联通",
        section="group",
        category="业务前台",
        description="自动识别和提取文档关键信息，支持合同与报告",
        status="approval",
        monthly_calls=8.8,
        release_date=date(2024, 5, 1),
        api_open=True,
        difficulty="Medium",
        contact_name="王晨",
        highlight="合同解析提速 65%",
        access_mode="profile",
        access_url="",
        target_system="合同管理系统",
        target_users="法务、业务经理",
        problem_statement="合同审核周期长，人工抽取字段易遗漏",
        effectiveness_type="cost_reduction",
        effectiveness_metric="人均审核工时降低 35%",
    ),
    dict(
        name="运维监控大屏",
        org="河北电信",
        section="group",
        category="运维后台",
        description="实时监控系统状态，智能预警和故障诊断",
        status="beta",
        monthly_calls=23.1,
        release_date=date(2024, 1, 1),
        api_open=False,
        difficulty="Medium",
        contact_name="赵岩",
        highlight="故障定位时间缩短",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/ops-monitor",
        target_system="统一运维平台",
        target_users="NOC 值班工程师",
        problem_statement="故障排查依赖人工经验，定位慢",
        effectiveness_type="efficiency_gain",
        effectiveness_metric="MTTR 降低 28%",
    ),
    dict(
        name="AI会议助手",
        org="河北移动",
        section="province",
        category="办公类",
        description="自动生成会议纪要、待办事项与行动计划",
        status="available",
        monthly_calls=12.3,
        release_date=date(2024, 4, 1),
        api_open=True,
        difficulty="Low",
        contact_name="孙薇",
        highlight="纪要自动化",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/meeting-assistant",
        target_system="OA 会议管理",
        target_users="项目经理、秘书",
        problem_statement="会后纪要整理耗时且遗漏风险高",
        effectiveness_type="perception_uplift",
        effectiveness_metric="会议满意度提升 18%",
    ),
    dict(
        name="智能数据分析",
        org="河北电信",
        section="province",
        category="企业管理",
        description="一键生成分析报告，支持多维可视化",
        status="approval",
        monthly_calls=6.6,
        release_date=date(2024, 6, 1),
        api_open=True,
        difficulty="High",
        contact_name="周凡",
        highlight="经营洞察实时化",
        access_mode="profile",
        access_url="",
        target_system="经营分析平台",
        target_users="经营分析师、部门负责人",
        problem_statement="跨系统取数慢，报表产出周期长",
        effectiveness_type="revenue_growth",
        effectiveness_metric="营销转化率提升 6.5%",
    ),
    dict(
        name="流程自动化引擎",
        org="河北联通",
        section="province",
        category="企业管理",
        description="低代码流程编排，快速实现业务自动化",
        status="offline",
        monthly_calls=9.9,
        release_date=date(2024, 2, 1),
        api_open=True,
        difficulty="Medium",
        contact_name="陈涛",
        highlight="流程上线周期缩短",
        access_mode="profile",
        access_url="",
        target_system="BPM 流程引擎",
        target_users="流程管理员、业务运营",
        problem_statement="跨部门流程编排复杂，改动上线慢",
        effectiveness_type="cost_reduction",
        effectiveness_metric="流程搭建成本降低 30%",
    ),
]


RANKINGS = [
    dict(ranking_type="excellent", position=1, app_name="智能客服助手", tag="历史优秀", score=96, likes=328, metric_type="composite", value_dimension="efficiency_gain", usage_30d=15400, declared_at=date(2024, 12, 1)),
    dict(ranking_type="excellent", position=2, app_name="运维监控大屏", tag="推荐", score=91, likes=255, metric_type="composite", value_dimension="cost_reduction", usage_30d=23100, declared_at=date(2024, 11, 20)),
    dict(ranking_type="excellent", position=3, app_name="AI会议助手", tag="新星", score=88, likes=287, metric_type="composite", value_dimension="perception_uplift", usage_30d=12300, declared_at=date(2024, 11, 3)),
    dict(ranking_type="trend", position=1, app_name="智能数据分析", tag="新星", score=76, likes=198, metric_type="growth_rate", value_dimension="revenue_growth", usage_30d=6600, declared_at=date(2024, 12, 9)),
    dict(ranking_type="trend", position=2, app_name="文档智能分析", tag="推荐", score=65, likes=176, metric_type="likes", value_dimension="efficiency_gain", usage_30d=8800, declared_at=date(2024, 12, 10)),
]


def seed_data(db: Session):
    if db.query(App).count() > 0:
        return

    for app in APPS:
        db.add(App(**app))
    db.commit()

    app_map = {a.name: a.id for a in db.query(App).all()}
    for item in RANKINGS:
        db.add(
            Ranking(
                ranking_type=item["ranking_type"],
                position=item["position"],
                app_id=app_map[item["app_name"]],
                tag=item["tag"],
                score=item["score"],
                likes=item["likes"],
                metric_type=item["metric_type"],
                value_dimension=item["value_dimension"],
                usage_30d=item["usage_30d"],
                declared_at=item["declared_at"],
            )
        )
    db.commit()
