from datetime import date

from sqlalchemy.orm import Session

from .models import App, Ranking, RankingDimension


APPS = [
    # 集团应用 (至少5个)
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
        name="智能营销助手",
        org="河北移动",
        section="group",
        category="业务前台",
        description="基于用户画像的智能营销方案生成系统",
        status="available",
        monthly_calls=18.7,
        release_date=date(2024, 2, 15),
        api_open=True,
        difficulty="Medium",
        contact_name="张旭",
        highlight="精准营销推荐",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/marketing-assistant",
        target_system="营销支撑系统",
        target_users="营销经理、渠道管理员",
        problem_statement="营销方案制定依赖经验，精准度不足",
        effectiveness_type="revenue_growth",
        effectiveness_metric="营销转化率提升 25%",
    ),
    dict(
        name="网络优化专家",
        org="河北电信",
        section="group",
        category="运维后台",
        description="基于AI的网络参数自动优化系统",
        status="beta",
        monthly_calls=12.5,
        release_date=date(2024, 4, 10),
        api_open=False,
        difficulty="High",
        contact_name="刘阳",
        highlight="网络质量自动优化",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/network-optimizer",
        target_system="网络管理系统",
        target_users="网络优化工程师",
        problem_statement="网络优化依赖人工分析，效率低下",
        effectiveness_type="cost_reduction",
        effectiveness_metric="网络优化成本降低 40%",
    ),
    dict(
        name="人力资源智能助手",
        org="河北联通",
        section="group",
        category="企业管理",
        description="智能招聘、培训和绩效分析系统",
        status="available",
        monthly_calls=9.2,
        release_date=date(2024, 1, 20),
        api_open=True,
        difficulty="Low",
        contact_name="陈明",
        highlight="人才管理智能化",
        access_mode="profile",
        access_url="",
        target_system="HR 管理系统",
        target_users="HR 专员、部门经理",
        problem_statement="人力资源管理流程繁琐，数据分析困难",
        effectiveness_type="efficiency_gain",
        effectiveness_metric="招聘周期缩短 35%",
    ),
    
    # 省内应用 (至少8个)
    dict(
        name="AI会议助手",
        org="石家庄移动",
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
        org="唐山电信",
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
        org="邯郸联通",
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
    dict(
        name="智慧校园助手",
        org="保定移动",
        section="province",
        category="业务前台",
        description="面向高校的智能校园服务系统",
        status="available",
        monthly_calls=15.8,
        release_date=date(2024, 3, 15),
        api_open=True,
        difficulty="Medium",
        contact_name="王丽",
        highlight="校园服务一站式",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/campus-assistant",
        target_system="校园管理系统",
        target_users="学生、教职工",
        problem_statement="校园服务分散，用户体验差",
        effectiveness_type="perception_uplift",
        effectiveness_metric="校园服务满意度提升 40%",
    ),
    dict(
        name="工业互联网平台",
        org="沧州电信",
        section="province",
        category="业务前台",
        description="面向制造业的智能生产管理平台",
        status="beta",
        monthly_calls=8.3,
        release_date=date(2024, 5, 20),
        api_open=True,
        difficulty="High",
        contact_name="李强",
        highlight="生产效率提升",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/industry-platform",
        target_system="工业控制系统",
        target_users="工厂管理员、生产主管",
        problem_statement="生产管理信息化水平低，效率不高",
        effectiveness_type="efficiency_gain",
        effectiveness_metric="生产效率提升 30%",
    ),
    dict(
        name="乡村振兴服务平台",
        org="邢台移动",
        section="province",
        category="业务前台",
        description="面向农村的信息化服务平台",
        status="available",
        monthly_calls=7.2,
        release_date=date(2024, 6, 5),
        api_open=True,
        difficulty="Low",
        contact_name="赵芳",
        highlight="乡村服务数字化",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/rural-service",
        target_system="农业农村信息系统",
        target_users="农民、乡镇干部",
        problem_statement="农村信息化水平低，服务获取困难",
        effectiveness_type="perception_uplift",
        effectiveness_metric="农村服务满意度提升 25%",
    ),
    dict(
        name="金融科技助手",
        org="衡水联通",
        section="province",
        category="企业管理",
        description="面向金融机构的智能风控和营销系统",
        status="approval",
        monthly_calls=10.5,
        release_date=date(2024, 4, 25),
        api_open=True,
        difficulty="High",
        contact_name="吴强",
        highlight="金融服务智能化",
        access_mode="profile",
        access_url="",
        target_system="金融核心系统",
        target_users="银行员工、金融分析师",
        problem_statement="金融风控依赖人工，效率和准确率低",
        effectiveness_type="revenue_growth",
        effectiveness_metric="风控准确率提升 35%",
    ),
    dict(
        name="文旅智能导览",
        org="承德电信",
        section="province",
        category="业务前台",
        description="面向旅游景区的智能导览和推荐系统",
        status="available",
        monthly_calls=14.2,
        release_date=date(2024, 3, 30),
        api_open=True,
        difficulty="Medium",
        contact_name="郑华",
        highlight="个性化旅游体验",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/tourism-guide",
        target_system="旅游管理系统",
        target_users="游客、景区管理员",
        problem_statement="旅游导览同质化，游客体验单一",
        effectiveness_type="perception_uplift",
        effectiveness_metric="游客满意度提升 30%",
    ),
    dict(
        name="医疗健康助手",
        org="秦皇岛移动",
        section="province",
        category="业务前台",
        description="智能问诊、健康管理和医疗资源调度系统",
        status="beta",
        monthly_calls=9.8,
        release_date=date(2024, 5, 15),
        api_open=True,
        difficulty="Medium",
        contact_name="孙医生",
        highlight="医疗服务智能化",
        access_mode="direct",
        access_url="https://aiapps.hebei.cn/health-assistant",
        target_system="医院信息系统",
        target_users="患者、医护人员",
        problem_statement="医疗资源分配不均，患者就医体验差",
        effectiveness_type="efficiency_gain",
        effectiveness_metric="患者等待时间减少 45%",
    ),
]


RANKINGS = [
    # 优秀应用榜
    dict(ranking_type="excellent", position=1, app_name="智能客服助手", tag="历史优秀", score=96, likes=328, metric_type="composite", value_dimension="efficiency_gain", usage_30d=15400, declared_at=date(2024, 12, 1)),
    dict(ranking_type="excellent", position=2, app_name="运维监控大屏", tag="推荐", score=91, likes=255, metric_type="composite", value_dimension="cost_reduction", usage_30d=23100, declared_at=date(2024, 11, 20)),
    dict(ranking_type="excellent", position=3, app_name="智能营销助手", tag="推荐", score=89, likes=302, metric_type="composite", value_dimension="revenue_growth", usage_30d=18700, declared_at=date(2024, 11, 25)),
    dict(ranking_type="excellent", position=4, app_name="AI会议助手", tag="新星", score=88, likes=287, metric_type="composite", value_dimension="perception_uplift", usage_30d=12300, declared_at=date(2024, 11, 3)),
    dict(ranking_type="excellent", position=5, app_name="智慧校园助手", tag="新星", score=87, likes=265, metric_type="composite", value_dimension="perception_uplift", usage_30d=15800, declared_at=date(2024, 11, 15)),
    dict(ranking_type="excellent", position=6, app_name="文旅智能导览", tag="推荐", score=85, likes=248, metric_type="composite", value_dimension="perception_uplift", usage_30d=14200, declared_at=date(2024, 11, 10)),
    dict(ranking_type="excellent", position=7, app_name="人力资源智能助手", tag="推荐", score=83, likes=215, metric_type="composite", value_dimension="efficiency_gain", usage_30d=9200, declared_at=date(2024, 11, 5)),
    dict(ranking_type="excellent", position=8, app_name="网络优化专家", tag="新星", score=82, likes=198, metric_type="composite", value_dimension="cost_reduction", usage_30d=12500, declared_at=date(2024, 11, 28)),
    
    # 趋势榜
    dict(ranking_type="trend", position=1, app_name="智能数据分析", tag="新星", score=76, likes=198, metric_type="growth_rate", value_dimension="revenue_growth", usage_30d=6600, declared_at=date(2024, 12, 9)),
    dict(ranking_type="trend", position=2, app_name="文档智能分析", tag="推荐", score=65, likes=176, metric_type="likes", value_dimension="efficiency_gain", usage_30d=8800, declared_at=date(2024, 12, 10)),
    dict(ranking_type="trend", position=3, app_name="乡村振兴服务平台", tag="新星", score=72, likes=185, metric_type="growth_rate", value_dimension="perception_uplift", usage_30d=7200, declared_at=date(2024, 12, 8)),
    dict(ranking_type="trend", position=4, app_name="医疗健康助手", tag="新星", score=68, likes=165, metric_type="growth_rate", value_dimension="efficiency_gain", usage_30d=9800, declared_at=date(2024, 12, 7)),
    dict(ranking_type="trend", position=5, app_name="工业互联网平台", tag="推荐", score=63, likes=152, metric_type="growth_rate", value_dimension="efficiency_gain", usage_30d=8300, declared_at=date(2024, 12, 6)),
]


def seed_data(db: Session):
    try:
        if db.query(App).count() > 0:
            return
    except Exception as e:
        # 表结构可能不存在或不完整，直接返回
        print(f"Database error during seed: {e}")
        return

    try:
        for app in APPS:
            # 添加排行榜相关字段
            app.setdefault('ranking_enabled', True)
            app.setdefault('ranking_weight', 1.0)
            app.setdefault('ranking_tags', '')
            app.setdefault('last_ranking_update', None)
            db.add(App(**app))
        db.commit()
    except Exception as e:
        print(f"Error seeding apps: {e}")
        db.rollback()

    try:
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
    except Exception as e:
        print(f"Error seeding rankings: {e}")
        db.rollback()
    
    try:
        # 添加默认排行维度
        default_dimensions = [
            {
                "name": "用户满意度",
                "description": "基于用户反馈和使用数据评估应用的满意度",
                "calculation_method": "基于应用的月调用量和用户评分计算",
                "weight": 3.0,
                "is_active": True
            },
            {
                "name": "业务价值",
                "description": "评估应用对业务的提升作用",
                "calculation_method": "基于应用的成效类型和指标计算",
                "weight": 2.5,
                "is_active": True
            },
            {
                "name": "技术创新性",
                "description": "评估应用的技术方案和创新点",
                "calculation_method": "基于应用的难度等级计算",
                "weight": 2.0,
                "is_active": True
            },
            {
                "name": "使用活跃度",
                "description": "评估应用的使用频率和用户活跃度",
                "calculation_method": "基于应用的月调用量计算",
                "weight": 1.5,
                "is_active": True
            },
            {
                "name": "稳定性和安全性",
                "description": "评估应用的可靠性和安全性",
                "calculation_method": "基于应用的状态和错误率计算",
                "weight": 1.0,
                "is_active": True
            }
        ]
        
        if db.query(RankingDimension).count() == 0:
            for dimension in default_dimensions:
                db.add(RankingDimension(**dimension))
            db.commit()
    except Exception as e:
        print(f"Error seeding ranking dimensions: {e}")
        db.rollback()
