from datetime import datetime

from sqlalchemy.orm import Session

from ..models import App, Ranking, RankingDimension, AppDimensionScore, HistoricalRanking

DEFAULT_RANKING_TAG = "推荐"


def calculate_app_score(app: App, dimensions: list[RankingDimension]) -> int:
    if not dimensions:
        return max(0, min(int(app.monthly_calls * 10), 1000))

    base_score = 0.0
    for dimension in dimensions:
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
        else:
            dimension_score = 50

        base_score += dimension_score * dimension.weight

    final_score = int(base_score * app.ranking_weight)
    return max(0, min(final_score, 1000))


def calculate_dimension_score(app: App, dimension: RankingDimension) -> tuple[int, str]:
    """
    计算应用在某个维度的得分和计算详情
    返回：(得分, 计算详情说明)
    """
    dimension_score = 0
    calculation_detail = ""
    
    if dimension.name == "用户满意度":
        dimension_score = min(int(app.monthly_calls * 10), 100)
        calculation_detail = f"基于月调用量计算：{app.monthly_calls} * 10 = {dimension_score}分"
    elif dimension.name == "业务价值":
        if app.effectiveness_type == "revenue_growth":
            dimension_score = 100
            calculation_detail = "成效类型为拉动收入，获得满分100分"
        elif app.effectiveness_type == "efficiency_gain":
            dimension_score = 80
            calculation_detail = "成效类型为增效，获得80分"
        elif app.effectiveness_type == "cost_reduction":
            dimension_score = 70
            calculation_detail = "成效类型为降本，获得70分"
        else:
            dimension_score = 60
            calculation_detail = "成效类型为感知提升，获得60分"
    elif dimension.name == "技术创新性":
        if app.difficulty == "High":
            dimension_score = 100
            calculation_detail = "难度等级为高，获得满分100分"
        elif app.difficulty == "Medium":
            dimension_score = 70
            calculation_detail = "难度等级为中，获得70分"
        else:
            dimension_score = 40
            calculation_detail = "难度等级为低，获得40分"
    elif dimension.name == "使用活跃度":
        dimension_score = min(int(app.monthly_calls * 5), 100)
        calculation_detail = f"基于月调用量计算：{app.monthly_calls} * 5 = {dimension_score}分"
    elif dimension.name == "稳定性和安全性":
        if app.status == "available":
            dimension_score = 100
            calculation_detail = "应用状态为可用，获得满分100分"
        elif app.status == "beta":
            dimension_score = 80
            calculation_detail = "应用状态为试运行，获得80分"
        else:
            dimension_score = 60
            calculation_detail = f"应用状态为{app.status}，获得60分"
    else:
        dimension_score = 50
        calculation_detail = "默认评分50分"
    
    return dimension_score, calculation_detail


def sync_rankings_service(db: Session) -> int:
    """
    同步排行榜数据
    - 计算所有省内应用的维度评分
    - 生成综合评分和排名
    - 保存历史榜单数据
    """
    dimensions = (
        db.query(RankingDimension)
        .filter(RankingDimension.is_active.is_(True))
        .order_by(RankingDimension.id)
        .all()
    )

    apps = (
        db.query(App)
        .filter(App.section == "province", App.ranking_enabled.is_(True))
        .order_by(App.id)
        .all()
    )

    updated_count = 0
    today = datetime.now().date()

    for ranking_type in ["excellent", "trend"]:
        for app in apps:
            # 计算各维度得分并保存
            base_score = 0.0
            for dimension in dimensions:
                dim_score, calc_detail = calculate_dimension_score(app, dimension)
                weighted_score = dim_score * dimension.weight
                base_score += weighted_score
                
                # 保存或更新维度评分
                existing_score = (
                    db.query(AppDimensionScore)
                    .filter(
                        AppDimensionScore.app_id == app.id,
                        AppDimensionScore.dimension_id == dimension.id,
                        AppDimensionScore.period_date == today
                    )
                    .first()
                )
                
                if existing_score:
                    existing_score.score = dim_score
                    existing_score.weight = dimension.weight
                    existing_score.calculation_detail = calc_detail
                    existing_score.updated_at = datetime.utcnow()
                else:
                    db.add(
                        AppDimensionScore(
                            app_id=app.id,
                            dimension_id=dimension.id,
                            dimension_name=dimension.name,
                            score=dim_score,
                            weight=dimension.weight,
                            calculation_detail=calc_detail,
                            period_date=today
                        )
                    )
            
            # 计算最终综合得分
            final_score = int(base_score * app.ranking_weight)
            final_score = max(0, min(final_score, 1000))
            
            metric_type = "composite" if ranking_type == "excellent" else "growth_rate"
            usage_30d = int(app.monthly_calls * 1000)
            tag = app.ranking_tags.strip() if app.ranking_tags else DEFAULT_RANKING_TAG

            existing = (
                db.query(Ranking)
                .filter(Ranking.ranking_type == ranking_type, Ranking.app_id == app.id)
                .first()
            )

            if existing:
                existing.score = final_score
                existing.metric_type = metric_type
                existing.value_dimension = app.effectiveness_type
                existing.usage_30d = usage_30d
                existing.tag = tag
                existing.updated_at = datetime.utcnow()
            else:
                position = (
                    db.query(Ranking)
                    .filter(Ranking.ranking_type == ranking_type)
                    .count()
                    + 1
                )
                db.add(
                    Ranking(
                        ranking_type=ranking_type,
                        position=position,
                        app_id=app.id,
                        tag=tag,
                        score=final_score,
                        metric_type=metric_type,
                        value_dimension=app.effectiveness_type,
                        usage_30d=usage_30d,
                        declared_at=today,
                    )
                )
            updated_count += 1

        # 重新排序并更新排名位置
        rankings = (
            db.query(Ranking)
            .filter(Ranking.ranking_type == ranking_type)
            .order_by(Ranking.score.desc())
            .all()
        )
        for index, ranking in enumerate(rankings, start=1):
            ranking.position = index
            
            # 保存历史榜单数据
            historical = (
                db.query(HistoricalRanking)
                .filter(
                    HistoricalRanking.ranking_type == ranking_type,
                    HistoricalRanking.app_id == ranking.app_id,
                    HistoricalRanking.period_date == today
                )
                .first()
            )
            
            if historical:
                historical.position = index
                historical.score = ranking.score
                historical.tag = ranking.tag
            else:
                db.add(
                    HistoricalRanking(
                        ranking_type=ranking_type,
                        period_date=today,
                        position=index,
                        app_id=ranking.app_id,
                        app_name=ranking.app.name,
                        app_org=ranking.app.org,
                        tag=ranking.tag,
                        score=ranking.score,
                        metric_type=ranking.metric_type,
                        value_dimension=ranking.value_dimension,
                        usage_30d=ranking.usage_30d
                    )
                )

    db.commit()
    return updated_count
