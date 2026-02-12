import json
from datetime import date, datetime

from sqlalchemy.orm import Session

from .models import App, Ranking, RankingConfig, RankingDimension, Submission, AppRankingSetting

VALUE_DIMENSIONS = {"cost_reduction", "efficiency_gain", "perception_uplift", "revenue_growth"}
DATA_LEVEL_VALUES = {"L1", "L2", "L3", "L4"}
DEFAULT_RANKING_TAG = "推荐"


GROUP_APPS = [
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
]

PROVINCE_SUBMISSIONS = [
    dict(
        app_name="AI会议助手",
        unit_name="石家庄移动",
        contact="孙薇",
        contact_phone="13800000001",
        contact_email="sunwei@example.com",
        category="办公类",
        scenario="自动生成会议纪要、待办事项与行动计划，提升会议效率并减少人工记录负担。",
        embedded_system="OA 会议管理",
        problem_statement="会后纪要整理耗时且遗漏风险高",
        effectiveness_type="perception_uplift",
        effectiveness_metric="会议满意度提升 18%",
        data_level="L2",
        expected_benefit="缩短会议整理时间并提高执行效率",
        ranking_tags="新星",
        ranking_dimensions="1,2",
    ),
    dict(
        app_name="智能数据分析",
        unit_name="唐山电信",
        contact="周凡",
        contact_phone="13800000002",
        contact_email="zhoufan@example.com",
        category="企业管理",
        scenario="一键生成分析报告，支持多维可视化，帮助管理层快速决策。",
        embedded_system="经营分析平台",
        problem_statement="跨系统取数慢，报表产出周期长",
        effectiveness_type="revenue_growth",
        effectiveness_metric="营销转化率提升 6.5%",
        data_level="L3",
        expected_benefit="缩短报表出具时间并提升决策效率",
        ranking_tags="推荐",
        ranking_dimensions="2,4",
    ),
    dict(
        app_name="流程自动化引擎",
        unit_name="邯郸联通",
        contact="陈涛",
        contact_phone="13800000003",
        contact_email="chentao@example.com",
        category="企业管理",
        scenario="低代码流程编排，快速实现跨部门业务自动化与审批流转。",
        embedded_system="BPM 流程引擎",
        problem_statement="跨部门流程编排复杂，改动上线慢",
        effectiveness_type="cost_reduction",
        effectiveness_metric="流程搭建成本降低 30%",
        data_level="L2",
        expected_benefit="缩短流程上线周期并降低改造成本",
        ranking_tags="推荐",
        ranking_dimensions="3,4",
    ),
    dict(
        app_name="智慧校园助手",
        unit_name="保定移动",
        contact="王丽",
        contact_phone="13800000004",
        contact_email="wangli@example.com",
        category="业务前台",
        scenario="面向高校的智能校园服务系统，提供一站式服务与智能问答。",
        embedded_system="校园管理系统",
        problem_statement="校园服务分散，用户体验差",
        effectiveness_type="perception_uplift",
        effectiveness_metric="校园服务满意度提升 40%",
        data_level="L1",
        expected_benefit="提升校园服务体验与学生满意度",
        ranking_tags="新星",
        ranking_dimensions="1,5",
    ),
    dict(
        app_name="工业互联网平台",
        unit_name="沧州电信",
        contact="李强",
        contact_phone="13800000005",
        contact_email="liqiang@example.com",
        category="业务前台",
        scenario="面向制造业的智能生产管理平台，辅助生产排程与质量监控。",
        embedded_system="工业控制系统",
        problem_statement="生产管理信息化水平低，效率不高",
        effectiveness_type="efficiency_gain",
        effectiveness_metric="生产效率提升 30%",
        data_level="L3",
        expected_benefit="提升生产效率并减少工序损耗",
        ranking_tags="推荐",
        ranking_dimensions="2,4",
    ),
    dict(
        app_name="乡村振兴服务平台",
        unit_name="邢台移动",
        contact="赵芳",
        contact_phone="13800000006",
        contact_email="zhaofang@example.com",
        category="业务前台",
        scenario="面向农村的信息化服务平台，提供政策、培训和服务指引。",
        embedded_system="农业农村信息系统",
        problem_statement="农村信息化水平低，服务获取困难",
        effectiveness_type="perception_uplift",
        effectiveness_metric="农村服务满意度提升 25%",
        data_level="L1",
        expected_benefit="提升农村信息服务覆盖率",
        ranking_tags="新星",
        ranking_dimensions="1,5",
    ),
    dict(
        app_name="金融科技助手",
        unit_name="衡水联通",
        contact="吴强",
        contact_phone="13800000007",
        contact_email="wuqiang@example.com",
        category="企业管理",
        scenario="面向金融机构的智能风控和营销系统，提升审批效率与风控能力。",
        embedded_system="金融核心系统",
        problem_statement="金融风控依赖人工，效率和准确率低",
        effectiveness_type="revenue_growth",
        effectiveness_metric="风控准确率提升 35%",
        data_level="L4",
        expected_benefit="提高风控准确率并降低风险成本",
        ranking_tags="推荐",
        ranking_dimensions="2,3",
    ),
    dict(
        app_name="文旅智能导览",
        unit_name="承德电信",
        contact="郑华",
        contact_phone="13800000008",
        contact_email="zhenghua@example.com",
        category="业务前台",
        scenario="面向旅游景区的智能导览和推荐系统，支持多语言与个性化推荐。",
        embedded_system="旅游管理系统",
        problem_statement="旅游导览同质化，游客体验单一",
        effectiveness_type="perception_uplift",
        effectiveness_metric="游客满意度提升 30%",
        data_level="L2",
        expected_benefit="提升游客体验并带动二次消费",
        ranking_tags="推荐",
        ranking_dimensions="1,2",
    ),
    dict(
        app_name="医疗健康助手",
        unit_name="秦皇岛移动",
        contact="孙医生",
        contact_phone="13800000009",
        contact_email="sunyi@example.com",
        category="业务前台",
        scenario="智能问诊、健康管理和医疗资源调度系统，缓解就医高峰。",
        embedded_system="医院信息系统",
        problem_statement="医疗资源分配不均，患者就医体验差",
        effectiveness_type="efficiency_gain",
        effectiveness_metric="患者等待时间减少 45%",
        data_level="L3",
        expected_benefit="提高医疗资源利用率并缩短等待时间",
        ranking_tags="新星",
        ranking_dimensions="4,5",
    ),
]


# 8个维度：5个现有 + 3个新增（增长趋势、用户增长、市场热度）
DEFAULT_DIMENSIONS = [
    {
        "name": "用户满意度",
        "description": "基于用户反馈和使用数据评估应用的满意度",
        "calculation_method": "基于应用的月调用量和用户评分计算",
        "weight": 2.5,
        "is_active": True,
    },
    {
        "name": "业务价值",
        "description": "评估应用对业务的提升作用",
        "calculation_method": "基于应用的成效类型和指标计算",
        "weight": 2.5,
        "is_active": True,
    },
    {
        "name": "技术创新性",
        "description": "评估应用的技术方案和创新点",
        "calculation_method": "基于应用的难度等级计算",
        "weight": 1.5,
        "is_active": True,
    },
    {
        "name": "使用活跃度",
        "description": "评估应用的使用频率和用户活跃度",
        "calculation_method": "基于应用的月调用量计算",
        "weight": 1.5,
        "is_active": True,
    },
    {
        "name": "稳定性和安全性",
        "description": "评估应用的可靠性和安全性",
        "calculation_method": "基于应用的状态和错误率计算",
        "weight": 1.0,
        "is_active": True,
    },
    # 新增维度
    {
        "name": "增长趋势",
        "description": "评估应用的增长速度和发展潜力",
        "calculation_method": "基于上月调用量增长率和新增用户计算",
        "weight": 2.0,
        "is_active": True,
    },
    {
        "name": "用户增长",
        "description": "评估应用的用户增长速度",
        "calculation_method": "基于新增用户数和用户留存率计算",
        "weight": 1.5,
        "is_active": True,
    },
    {
        "name": "市场热度",
        "description": "评估应用在市场上的关注度和传播度",
        "calculation_method": "基于搜索次数、分享次数和收藏次数计算",
        "weight": 1.5,
        "is_active": True,
    },
]

# 榜单配置
DEFAULT_RANKING_CONFIGS = [
    {
        "id": "excellent",
        "name": "优秀应用榜",
        "description": "综合评估应用的业务价值和技术水平，突出成熟稳定的优秀应用",
        "dimensions_config": json.dumps([
            {"dim_id": 1, "weight": 2.5},  # 用户满意度
            {"dim_id": 2, "weight": 3.0},  # 业务价值（权重更高）
            {"dim_id": 3, "weight": 2.0},  # 技术创新性
            {"dim_id": 4, "weight": 1.5},  # 使用活跃度
            {"dim_id": 5, "weight": 1.0},  # 稳定性和安全性
        ]),
        "calculation_method": "composite",
        "is_active": True,
    },
    {
        "id": "trend",
        "name": "趋势榜",
        "description": "关注应用的增长速度和市场热度，突出新兴潜力应用",
        "dimensions_config": json.dumps([
            {"dim_id": 1, "weight": 1.5},  # 用户满意度
            {"dim_id": 2, "weight": 1.5},  # 业务价值
            {"dim_id": 4, "weight": 2.0},  # 使用活跃度
            {"dim_id": 6, "weight": 2.5},  # 增长趋势（权重更高）
            {"dim_id": 7, "weight": 2.0},  # 用户增长（权重更高）
            {"dim_id": 8, "weight": 1.5},  # 市场热度（权重更高）
        ]),
        "calculation_method": "growth_rate",
        "is_active": True,
    },
]


def create_submission_direct(db: Session, payload: dict) -> Submission:
    """直接创建申报记录，不经过Pydantic验证"""
    submission = Submission(
        app_name=payload["app_name"],
        unit_name=payload["unit_name"],
        contact=payload["contact"],
        contact_phone=payload.get("contact_phone", ""),
        contact_email=payload.get("contact_email", ""),
        category=payload["category"],
        scenario=payload["scenario"],
        embedded_system=payload["embedded_system"],
        problem_statement=payload["problem_statement"],
        effectiveness_type=payload["effectiveness_type"],
        effectiveness_metric=payload["effectiveness_metric"],
        data_level=payload["data_level"],
        expected_benefit=payload["expected_benefit"],
        status="pending",
        ranking_enabled=payload.get("ranking_enabled", True),
        ranking_weight=payload.get("ranking_weight", 1.0),
        ranking_tags=payload.get("ranking_tags", ""),
        ranking_dimensions=payload.get("ranking_dimensions", ""),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def approve_submission_and_create_app(db: Session, submission: Submission) -> App:
    if submission.status != "pending":
        raise ValueError("submission is not pending")

    app = App(
        name=submission.app_name,
        org=submission.unit_name,
        section="province",
        category=submission.category,
        description=submission.scenario,
        status="available",
        monthly_calls=0.0,
        release_date=date.today(),
        api_open=True,
        difficulty="Medium",
        contact_name=submission.contact,
        highlight="",
        access_mode="direct",
        access_url="",
        target_system=submission.embedded_system,
        target_users="",
        problem_statement=submission.problem_statement,
        effectiveness_type=submission.effectiveness_type,
        effectiveness_metric=submission.effectiveness_metric,
        cover_image_url="",
        ranking_enabled=submission.ranking_enabled,
        ranking_weight=submission.ranking_weight,
        ranking_tags=submission.ranking_tags,
        # 新增增长指标字段（初始化为模拟数据）
        last_month_calls=0.0,
        new_users_count=0,
        search_count=0,
        share_count=0,
        favorite_count=0,
    )

    db.add(app)
    submission.status = "approved"
    db.commit()
    db.refresh(app)
    return app


def calculate_app_score(
    app: App,
    ranking_config: RankingConfig,
    dimensions: list[RankingDimension],
    app_setting: AppRankingSetting | None = None
) -> int:
    """
    根据榜单配置计算应用得分

    1. 解析榜单配置的维度权重
    2. 计算各维度得分
    3. 应用权重系数
    4. 返回最终分数
    """
    # 解析维度配置
    dim_config = json.loads(ranking_config.dimensions_config) if ranking_config.dimensions_config else []
    dim_weight_map = {d["dim_id"]: d["weight"] for d in dim_config}

    # 如果没有维度配置，使用默认计算
    if not dim_config or not dimensions:
        return max(0, min(int(app.monthly_calls * 10), 1000))

    # 计算基础分数
    base_score = 0.0
    total_weight = 0.0

    for dimension in dimensions:
        if dimension.id not in dim_weight_map:
            continue

        dimension_score = 0
        if dimension.name == "用户满意度":
            dimension_score = min(int(app.monthly_calls * 10), 100)
        elif dimension.name == "业务价值":
            if app.effectiveness_type == "revenue_growth":
                dimension_score = 100
            elif app.effectiveness_type == "efficiency_gain":
                dimension_score = 80
            elif app.effectiveness_type == "cost_reduction":
                dimension_score = 70
            else:
                dimension_score = 60
        elif dimension.name == "技术创新性":
            if app.difficulty == "High":
                dimension_score = 100
            elif app.difficulty == "Medium":
                dimension_score = 70
            else:
                dimension_score = 40
        elif dimension.name == "使用活跃度":
            dimension_score = min(int(app.monthly_calls * 5), 100)
        elif dimension.name == "稳定性和安全性":
            if app.status == "available":
                dimension_score = 100
            elif app.status == "beta":
                dimension_score = 80
            else:
                dimension_score = 60
        elif dimension.name == "增长趋势":
            # 基于上月调用量增长率计算
            if app.last_month_calls > 0:
                growth_rate = (app.monthly_calls - app.last_month_calls) / app.last_month_calls
                dimension_score = min(max(int(growth_rate * 100), 0), 100)
            else:
                dimension_score = 50
        elif dimension.name == "用户增长":
            # 基于新增用户数计算
            dimension_score = min(int(app.new_users_count / 10), 100)
        elif dimension.name == "市场热度":
            # 基于搜索、分享、收藏计算
            heat_score = app.search_count + app.share_count * 2 + app.favorite_count * 3
            dimension_score = min(int(heat_score / 10), 100)
        else:
            dimension_score = 50

        weight = dim_weight_map[dimension.id]
        base_score += dimension_score * weight
        total_weight += weight

    # 归一化
    if total_weight > 0:
        final_score = base_score / total_weight
    else:
        final_score = base_score

    # 应用权重系数（如果应用有自定义设置）
    if app_setting and app_setting.weight_factor:
        final_score *= app_setting.weight_factor

    return max(0, min(int(final_score), 1000))


def sync_rankings(db: Session, ranking_config_id: str | None = None) -> int:
    """
    同步排行榜数据

    1. 获取榜单配置
    2. 获取参与该榜单的所有应用（通过 AppRankingSetting）
    3. 计算每个应用的分数
    4. 生成 Ranking 记录
    """
    updated_count = 0

    # 获取需要同步的榜单配置
    configs_query = db.query(RankingConfig).filter(RankingConfig.is_active.is_(True))
    if ranking_config_id:
        configs_query = configs_query.filter(RankingConfig.id == ranking_config_id)
    configs = configs_query.all()

    # 获取所有维度
    dimensions = (
        db.query(RankingDimension)
        .filter(RankingDimension.is_active.is_(True))
        .all()
    )

    for config in configs:
        # 获取参与该榜单的应用设置
        app_settings = (
            db.query(AppRankingSetting)
            .filter(
                AppRankingSetting.ranking_config_id == config.id,
                AppRankingSetting.is_enabled.is_(True)
            )
            .all()
        )

        # 获取应用列表
        app_ids = [s.app_id for s in app_settings]
        apps = db.query(App).filter(App.id.in_(app_ids)).all()
        app_map = {app.id: app for app in apps}
        setting_map = {s.app_id: s for s in app_settings}

        # 计算分数
        app_scores = []
        for app_id in app_ids:
            app = app_map.get(app_id)
            setting = setting_map.get(app_id)
            if not app:
                continue

            score = calculate_app_score(app, config, dimensions, setting)
            app_scores.append((app, score, setting))

        # 排序
        app_scores.sort(key=lambda x: x[1], reverse=True)

        # 生成 Ranking 记录
        for position, (app, score, setting) in enumerate(app_scores, start=1):
            tag = setting.custom_tags if setting and setting.custom_tags else DEFAULT_RANKING_TAG

            existing = (
                db.query(Ranking)
                .filter(
                    Ranking.ranking_config_id == config.id,
                    Ranking.app_id == app.id
                )
                .first()
            )

            if existing:
                existing.position = position
                existing.score = score
                existing.tag = tag
                existing.ranking_type = config.id  # 同步更新
            else:
                db.add(
                    Ranking(
                        ranking_config_id=config.id,
                        ranking_type=config.id,
                        position=position,
                        app_id=app.id,
                        tag=tag,
                        score=score,
                        metric_type=config.calculation_method,
                        value_dimension=app.effectiveness_type,
                        usage_30d=int(app.monthly_calls * 1000),
                        declared_at=date.today(),
                    )
                )
            updated_count += 1

        # 重新排序所有排名
        rankings = (
            db.query(Ranking)
            .filter(Ranking.ranking_config_id == config.id)
            .order_by(Ranking.score.desc())
            .all()
        )
        for index, ranking in enumerate(rankings, start=1):
            ranking.position = index

    db.commit()
    return updated_count


def seed_data(db: Session) -> None:
    """初始化数据库数据
    - 集团应用直接录入（系统内置）
    - 省内应用通过申报流程录入
    - 初始化排行榜维度和榜单配置
    """
    try:
        if db.query(App).count() > 0 or db.query(Submission).count() > 0:
            return
    except Exception as exc:
        print(f"Database error during seed: {exc}")
        return

    # 1. 初始化维度
    try:
        if db.query(RankingDimension).count() == 0:
            for dimension in DEFAULT_DIMENSIONS:
                db.add(RankingDimension(**dimension))
            db.commit()
            print(f"Seeded {len(DEFAULT_DIMENSIONS)} ranking dimensions")
    except Exception as exc:
        print(f"Error seeding ranking dimensions: {exc}")
        db.rollback()

    # 2. 初始化榜单配置
    try:
        if db.query(RankingConfig).count() == 0:
            for config in DEFAULT_RANKING_CONFIGS:
                db.add(RankingConfig(**config))
            db.commit()
            print(f"Seeded {len(DEFAULT_RANKING_CONFIGS)} ranking configs")
    except Exception as exc:
        print(f"Error seeding ranking configs: {exc}")
        db.rollback()

    # 1. 录入集团应用（直接录入，不走申报流程）
    try:
        for app in GROUP_APPS:
            app.setdefault("ranking_enabled", False)  # 集团应用不参与排行榜
            app.setdefault("ranking_weight", 1.0)
            app.setdefault("ranking_tags", "")
            app.setdefault("last_ranking_update", None)
            db.add(App(**app))
        db.commit()
        print(f"Seeded {len(GROUP_APPS)} group apps")
    except Exception as exc:
        print(f"Error seeding group apps: {exc}")
        db.rollback()

    # 2. 省内应用通过申报流程录入
    try:
        approved_ids = []
        approved_apps = []
        for index, payload in enumerate(PROVINCE_SUBMISSIONS):
            # 创建申报
            submission = create_submission_direct(db, payload)
            # 前7个申报自动审批通过（模拟审核流程）
            if index < 7:
                approved = approve_submission_and_create_app(db, submission)
                approved_ids.append(approved.id)
                approved_apps.append(approved)
                print(f"Approved submission {submission.id} -> app {approved.id}")

        # 3. 初始化应用榜单设置（在同步排行榜之前）
        if approved_apps:
            configs = db.query(RankingConfig).filter(RankingConfig.is_active.is_(True)).all()
            for app in approved_apps:
                for config in configs:
                    # 检查是否已存在
                    existing = (
                        db.query(AppRankingSetting)
                        .filter(
                            AppRankingSetting.app_id == app.id,
                            AppRankingSetting.ranking_config_id == config.id
                        )
                        .first()
                    )
                    if not existing:
                        db.add(
                            AppRankingSetting(
                                app_id=app.id,
                                ranking_config_id=config.id,
                                is_enabled=True,
                                weight_factor=1.0,
                                custom_tags=app.ranking_tags or DEFAULT_RANKING_TAG,
                            )
                        )
            db.commit()
            print(f"Initialized ranking settings for {len(approved_apps)} apps")

        # 4. 同步排行榜数据
        if approved_ids:
            sync_rankings(db)
            print(f"Synced rankings for {len(approved_ids)} apps")
    except Exception as exc:
        print(f"Error seeding province submissions: {exc}")
        db.rollback()
