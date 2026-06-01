"""排行榜核心业务服务——榜单同步、维度评分、发布预校验。

从 main.py 提取，可脱离 HTTP 层独立测试。
"""

import json as _json
import logging
import uuid as _uuid
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from ..dependencies import structured_error_detail, write_ranking_audit_log
from ..models import (
    App,
    AppDimensionScore,
    AppRankingSetting,
    HistoricalRanking,
    Ranking,
    RankingConfig,
    RankingDimension,
)

logger = logging.getLogger(__name__)
DEFAULT_RANKING_TAG = "推荐"


# ---------------------------------------------------------------------------
# 维度评分读取与清理
# ---------------------------------------------------------------------------

def load_single_dimension_score(
    db: Session,
    *,
    app_id: int,
    ranking_config_id: str | None,
    dimension_id: int,
    period_date: date,
) -> AppDimensionScore | None:
    """读取同日维度分值并清理重复脏数据，仅保留最新一条。"""
    records = (
        db.query(AppDimensionScore)
        .filter(
            AppDimensionScore.app_id == app_id,
            AppDimensionScore.ranking_config_id == ranking_config_id,
            AppDimensionScore.dimension_id == dimension_id,
            AppDimensionScore.period_date == period_date,
        )
        .order_by(AppDimensionScore.updated_at.desc(), AppDimensionScore.id.desc())
        .all()
    )
    if not records:
        return None
    primary = records[0]
    for stale in records[1:]:
        db.delete(stale)
    return primary


# ---------------------------------------------------------------------------
# 排行榜字段校验
# ---------------------------------------------------------------------------

def validate_submission_ranking_fields(
    ranking_weight: float,
    ranking_tags: str,
    ranking_dimensions: str,
) -> None:
    if ranking_weight < 0.1 or ranking_weight > 10.0:
        raise HTTPException(status_code=422, detail="ranking_weight must be between 0.1 and 10.0")
    if len(ranking_tags) > 255:
        raise HTTPException(status_code=422, detail="ranking_tags must not exceed 255 characters")
    if len(ranking_dimensions) > 500:
        raise HTTPException(status_code=422, detail="ranking_dimensions must not exceed 500 characters")


# ---------------------------------------------------------------------------
# 评分计算（旧版 / 维度 / 三层）
# ---------------------------------------------------------------------------

def calculate_app_score(app: App, dimensions: list[RankingDimension]) -> int:
    """Deprecated: 保留旧版评分逻辑仅用于审计/回顾，不作为当前榜单权威计算路径。"""
    logger.warning("Deprecated ranking path used: calculate_app_score(). Use sync_rankings_service() as source of truth.")
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


def calculate_three_layer_score(
    app: App,
    config_dimensions: list[dict],
    dimension_map: dict[int, RankingDimension],
    weight_factor: float = 1.0,
) -> int:
    """三层榜单权威评分路径（纯计算函数，用于稳定性回归锚点）。"""
    base_score = 0.0
    for dim_config in config_dimensions:
        dim_id = dim_config.get("dim_id")
        weight = dim_config.get("weight", 1.0)
        dimension = dimension_map.get(dim_id)
        if not dimension:
            continue
        dim_score, _ = calculate_dimension_score(app, dimension)
        base_score += dim_score * weight

    final_score = int(base_score * weight_factor)
    return max(0, min(final_score, 1000))


# ---------------------------------------------------------------------------
# 榜单同步核心服务
# ---------------------------------------------------------------------------

def sync_rankings_service(db: Session, run_id: str | None = None, actor: str = "system") -> tuple[int, str]:
    """
    同步排行榜数据（支持三层架构）
    - 遍历每个榜单配置
    - 获取参与该榜单的应用
    - 根据榜单配置的维度权重计算得分
    - 生成排名并保存历史数据
    """
    # 获取所有活跃的榜单配置
    ranking_configs = (
        db.query(RankingConfig)
        .filter(RankingConfig.is_active.is_(True))
        .all()
    )
    active_config_ids = {config.id for config in ranking_configs}

    # 全局清理：非活跃（或已删除）配置的实时榜单记录，避免首页残留脏数据
    stale_realtime_query = db.query(Ranking)
    if active_config_ids:
        stale_realtime_query = stale_realtime_query.filter(~Ranking.ranking_config_id.in_(active_config_ids))
    removed_global_realtime_rows = stale_realtime_query.delete(synchronize_session=False)

    # 获取所有维度
    dimensions = (
        db.query(RankingDimension)
        .filter(RankingDimension.is_active.is_(True))
        .order_by(RankingDimension.id)
        .all()
    )

    # 创建维度ID到维度对象的映射
    dimension_map = {d.id: d for d in dimensions}

    updated_count = 0
    today = datetime.now().date()
    current_run_id = (run_id or str(_uuid.uuid4())).strip()
    if not current_run_id:
        current_run_id = str(_uuid.uuid4())

    for config in ranking_configs:
        config_dimension_updates = 0
        config_ranking_updates = 0
        config_historical_updates = 0

        # 解析榜单配置的维度权重
        try:
            config_dimensions = _json.loads(config.dimensions_config) if config.dimensions_config else []
        except _json.JSONDecodeError:
            config_dimensions = []

        # 获取参与该榜单的应用设置
        app_settings = (
            db.query(AppRankingSetting)
            .filter(
                AppRankingSetting.ranking_config_id == config.id,
                AppRankingSetting.is_enabled.is_(True)
            )
            .options(joinedload(AppRankingSetting.app))
            .all()
        )

        # 计算每个应用的得分
        app_scores = []
        for setting in app_settings:
            app = setting.app
            if not app or app.section != "province" or app.status == "offline":
                continue

            # 维度分值来源收敛规则：
            # 1) 手动评分（calculation_detail 以"手动调整评分"开头）优先
            # 2) 否则按规则自动计算并落库
            weighted_dimension_score = 0.0
            for dim_config in config_dimensions:
                dim_id = dim_config.get("dim_id")
                weight = dim_config.get("weight", 1.0)

                dimension = dimension_map.get(dim_id)
                if not dimension:
                    continue

                # 保存维度评分
                existing_score = load_single_dimension_score(
                    db,
                    app_id=app.id,
                    ranking_config_id=config.id,
                    dimension_id=dimension.id,
                    period_date=today,
                )

                is_manual_score = bool(existing_score and (existing_score.calculation_detail or "").startswith("手动调整评分"))
                if is_manual_score:
                    dim_score = existing_score.score
                    existing_score.dimension_name = dimension.name
                    existing_score.weight = weight
                    existing_score.updated_at = datetime.utcnow()
                else:
                    dim_score, calc_detail = calculate_dimension_score(app, dimension)
                    if existing_score:
                        existing_score.dimension_name = dimension.name
                        existing_score.score = dim_score
                        existing_score.weight = weight
                        existing_score.calculation_detail = calc_detail
                        existing_score.updated_at = datetime.utcnow()
                    else:
                        db.add(
                            AppDimensionScore(
                                app_id=app.id,
                                ranking_config_id=config.id,
                                dimension_id=dimension.id,
                                dimension_name=dimension.name,
                                score=dim_score,
                                weight=weight,
                                calculation_detail=calc_detail,
                                period_date=today
                            )
                        )
                weighted_dimension_score += dim_score * weight
                config_dimension_updates += 1

            # 应用权重因子（使用已收敛的维度分值）
            final_score = max(0, min(int(weighted_dimension_score * setting.weight_factor), 1000))

            app_scores.append({
                "app": app,
                "setting": setting,
                "score": final_score
            })

        # 按得分排序
        # 明确同分规则：分数降序；同分按 app_id 升序，避免重算后顺序抖动
        app_scores.sort(key=lambda x: (-x["score"], x["app"].id))

        # 清理不再参与该榜单的实时排名（解决"换榜后旧榜仍残留"问题）
        participating_app_ids = {item["app"].id for item in app_scores}
        stale_rankings_query = db.query(Ranking).filter(Ranking.ranking_config_id == config.id)
        if participating_app_ids:
            stale_rankings_query = stale_rankings_query.filter(~Ranking.app_id.in_(participating_app_ids))
        removed_realtime_rows = stale_rankings_query.delete(synchronize_session=False)

        # 更新或创建排名记录
        for index, item in enumerate(app_scores, start=1):
            app = item["app"]
            setting = item["setting"]

            score = item["score"]

            tag = setting.custom_tags.strip() if setting.custom_tags else DEFAULT_RANKING_TAG
            usage_30d = int(app.monthly_calls * 1000) if app.monthly_calls else 0

            existing = (
                db.query(Ranking)
                .filter(
                    Ranking.ranking_config_id == config.id,
                    Ranking.app_id == app.id
                )
                .first()
            )

            if existing:
                existing.position = index
                existing.score = score
                existing.tag = tag
                existing.usage_30d = usage_30d
                existing.updated_at = datetime.utcnow()
            else:
                db.add(
                    Ranking(
                        ranking_config_id=config.id,
                        ranking_type=config.id,  # 保持兼容性
                        position=index,
                        app_id=app.id,
                        tag=tag,
                        score=score,
                        metric_type=config.calculation_method or "composite",
                        value_dimension=app.effectiveness_type,
                        usage_30d=usage_30d,
                        declared_at=today,
                    )
                )
            config_ranking_updates += 1

            # 保存历史榜单数据
            historical = (
                db.query(HistoricalRanking)
                .filter(
                    HistoricalRanking.ranking_config_id == config.id,
                    HistoricalRanking.app_id == app.id,
                    HistoricalRanking.period_date == today,
                    HistoricalRanking.run_id == current_run_id
                )
                .first()
            )

            if historical:
                historical.position = index
                historical.score = score
                historical.tag = tag
            else:
                db.add(
                    HistoricalRanking(
                        ranking_config_id=config.id,
                        ranking_type=config.id,  # 保持兼容性
                        period_date=today,
                        run_id=current_run_id,
                        position=index,
                        app_id=app.id,
                        app_name=app.name,
                        app_org=app.org,
                        tag=tag,
                        score=score,
                        metric_type=config.calculation_method or "composite",
                        value_dimension=app.effectiveness_type,
                        usage_30d=usage_30d
                    )
                )
            config_historical_updates += 1

            updated_count += 1

        write_ranking_audit_log(
            db,
            action="rankings_sync_config_published",
            ranking_type=config.id,
            ranking_config_id=config.id,
            period_date=today,
            run_id=current_run_id,
            actor=actor,
            payload_summary=(
                f"dimension_score_updates={config_dimension_updates},"
                f"ranking_updates={config_ranking_updates},"
                f"historical_ranking_updates={config_historical_updates},"
                f"realtime_removed={removed_realtime_rows}"
            ),
        )

    if removed_global_realtime_rows:
        write_ranking_audit_log(
            db,
            action="rankings_sync_global_realtime_cleanup",
            ranking_type="all",
            period_date=today,
            run_id=current_run_id,
            actor=actor,
            payload_summary=f"removed_realtime={removed_global_realtime_rows}",
        )

    db.commit()
    return updated_count, current_run_id


# ---------------------------------------------------------------------------
# 链式变更触发
# ---------------------------------------------------------------------------

def sync_after_chain_mutation(db: Session, trigger: str, actor: str = "system") -> tuple[int, str]:
    """链路节点发生增删改后，统一触发榜单重算并返回运行信息。"""
    try:
        # SessionLocal 关闭了 autoflush，先显式 flush，避免同步阶段读不到本次变更。
        db.flush()
        updated_count, run_id = sync_rankings_service(db, actor=actor)
        write_ranking_audit_log(
            db,
            action=f"{trigger}_triggered_sync",
            ranking_type="all",
            period_date=datetime.utcnow().date(),
            run_id=run_id,
            actor=actor,
            payload_summary=f"updated_count={updated_count}",
        )
        db.commit()
        return updated_count, run_id
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"链路同步失败: {str(exc)}") from exc


# ---------------------------------------------------------------------------
# 榜单发布预校验
# ---------------------------------------------------------------------------

def validate_publish_preconditions(db: Session) -> dict[str, int]:
    active_configs = db.query(RankingConfig).filter(RankingConfig.is_active.is_(True)).all()
    if not active_configs:
        raise HTTPException(
            status_code=409,
            detail=structured_error_detail(
                code="publish_precheck_failed",
                message="无可发布榜单：请先启用至少一个榜单配置",
            ),
        )

    config_ids = [cfg.id for cfg in active_configs]
    enabled_settings = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.ranking_config_id.in_(config_ids),
            AppRankingSetting.is_enabled.is_(True),
        )
        .count()
    )
    if enabled_settings == 0:
        raise HTTPException(
            status_code=409,
            detail=structured_error_detail(
                code="publish_precheck_failed",
                message='无可发布应用：请先在"应用参与"中启用至少一个应用',
            ),
        )

    invalid_configs = []
    for config in active_configs:
        configured_dims = _collect_config_dimension_ids(config)
        if not configured_dims:
            invalid_configs.append(config.id)
    if invalid_configs:
        raise HTTPException(
            status_code=409,
            detail=structured_error_detail(
                code="publish_precheck_failed",
                message="存在未配置维度的启用榜单，请先完善榜单配置",
                field_errors=[{"field": "ranking_config_id", "message": cid} for cid in invalid_configs],
            ),
        )

    return {
        "active_configs": len(active_configs),
        "enabled_settings": enabled_settings,
    }


# ---------------------------------------------------------------------------
# 序列化 / 维度收集
# ---------------------------------------------------------------------------

def serialize_setting_snapshot(setting: AppRankingSetting | None) -> dict[str, object]:
    if setting is None:
        return {}
    return {
        "id": setting.id,
        "app_id": setting.app_id,
        "ranking_config_id": setting.ranking_config_id,
        "is_enabled": setting.is_enabled,
        "weight_factor": setting.weight_factor,
        "custom_tags": setting.custom_tags,
    }


def collect_config_dimension_ids(config: RankingConfig) -> set[int]:
    config_dim_ids: set[int] = set()
    if not config.dimensions_config:
        return config_dim_ids
    try:
        dimensions_config = _json.loads(config.dimensions_config)
    except _json.JSONDecodeError:
        return config_dim_ids
    if not isinstance(dimensions_config, list):
        return config_dim_ids
    for item in dimensions_config:
        if isinstance(item, dict) and isinstance(item.get("dim_id"), int):
            config_dim_ids.add(item["dim_id"])
    return config_dim_ids
