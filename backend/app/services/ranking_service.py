from datetime import datetime

from sqlalchemy.orm import Session

from ..models import App, Ranking, RankingDimension

DEFAULT_TAG = "推荐"


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


def sync_rankings(db: Session) -> int:
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

    for ranking_type in ["excellent", "trend"]:
        for app in apps:
            score = calculate_app_score(app, dimensions)
            metric_type = "composite" if ranking_type == "excellent" else "growth_rate"
            usage_30d = int(app.monthly_calls * 1000)
            tag = app.ranking_tags.strip() if app.ranking_tags else DEFAULT_TAG

            existing = (
                db.query(Ranking)
                .filter(Ranking.ranking_type == ranking_type, Ranking.app_id == app.id)
                .first()
            )

            if existing:
                existing.score = score
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
                        score=score,
                        metric_type=metric_type,
                        value_dimension=app.effectiveness_type,
                        usage_30d=usage_30d,
                        declared_at=datetime.now().date(),
                    )
                )
            updated_count += 1

        rankings = (
            db.query(Ranking)
            .filter(Ranking.ranking_type == ranking_type)
            .order_by(Ranking.score.desc())
            .all()
        )
        for index, ranking in enumerate(rankings, start=1):
            ranking.position = index

    db.commit()
    return updated_count
