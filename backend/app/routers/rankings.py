"""Auto-generated router from main.py."""
import json as _json, logging, math, uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Body, Depends, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from ..auth_utils import generate_session_token, hash_password, verify_password
from ..config import *
from ..database import ensure_database_schema_ready, get_db
from ..identity import get_identity_provider
from ..models import *
from ..schemas import *
from ..dependencies import *
from ..services.ranking_service import *
from ..services.submission_service import *
from ..venv_utils import venv_reader
logger = logging.getLogger(__name__)
router = APIRouter(prefix=settings.api_prefix)


# Module-level helpers

def resolve_latest_run_id(db: Session, ranking_type: str, period_date: date) -> str | None:
    """返回某榜单在指定日期最新发布的 run_id（旧数据可能为空）。"""
    scope_id = resolve_ranking_scope_id(ranking_type=ranking_type)
    latest_with_run = (
        db.query(HistoricalRanking.run_id)
        .filter(
            or_(
                HistoricalRanking.ranking_config_id == scope_id,
                HistoricalRanking.ranking_type == scope_id,
            )
        )
        .filter(HistoricalRanking.period_date == period_date)
        .filter(HistoricalRanking.run_id.is_not(None))
        .order_by(HistoricalRanking.created_at.desc())
        .first()
    )
    return latest_with_run[0] if latest_with_run else None

@router.get(f"/rankings", response_model=list[RankingItem])
def list_rankings(
    ranking_type: str = "excellent",
    ranking_config_id: str | None = Query(default=None, description="榜单配置ID（兼容前端 ranking_config_id 参数）"),
    company: str | None = Query(default=None, description="按公司筛选省内榜单"),
    period_date: date | None = Query(default=None, description="查询历史榜单日期，格式：YYYY-MM-DD；不传则返回实时榜单"),
    db: Session = Depends(get_db)
):
    """
    获取应用榜单
    - 榜单仅展示省内应用
    - 支持按日期查询历史榜单
    - 不传日期则返回实时榜单（Ranking 表），用于首页/管理页即时展示
    """
    scope_id = resolve_ranking_scope_id(ranking_type=ranking_type, ranking_config_id=ranking_config_id)

    def _to_ranking_item(
        *,
        app: App,
        ranking_config_id_value: str | None,
        position: int,
        tag: str,
        score: int,
        metric_type: str,
        value_dimension: str,
        usage_30d: int,
        declared_at: date,
        updated_at: datetime | None = None,
    ) -> dict:
        return {
            "ranking_config_id": ranking_config_id_value,
            "position": position,
            "tag": tag,
            "score": score,
            "likes": None,
            "metric_type": metric_type,
            "value_dimension": value_dimension,
            "usage_30d": usage_30d,
            "declared_at": declared_at,
            "updated_at": updated_at,
            "app": app,
        }

    try:
        if period_date:
            # 查询指定日期的历史榜单
            selected_run_id = resolve_latest_run_id(db, scope_id, period_date)
            historical_query = (
                db.query(HistoricalRanking)
                .filter(HistoricalRanking.period_date == period_date)
                .filter(
                    or_(
                        HistoricalRanking.ranking_config_id == scope_id,
                        HistoricalRanking.ranking_type == scope_id,
                    )
                )
            )
            if selected_run_id is not None:
                historical_query = historical_query.filter(HistoricalRanking.run_id == selected_run_id)
            else:
                historical_query = historical_query.filter(HistoricalRanking.run_id.is_(None))

            historical_rankings = historical_query.order_by(HistoricalRanking.position).all()
            result = []
            for hr in historical_rankings:
                app = db.query(App).filter(App.id == hr.app_id).first()
                if app and app.section == "province":
                    if company and (app.company or app.org) != company:
                        continue
                    result.append(
                        _to_ranking_item(
                            app=app,
                            ranking_config_id_value=hr.ranking_config_id,
                            position=hr.position,
                            tag=hr.tag,
                            score=hr.score,
                            metric_type=hr.metric_type,
                            value_dimension=hr.value_dimension,
                            usage_30d=hr.usage_30d,
                            declared_at=hr.period_date,
                            updated_at=getattr(hr, "updated_at", None),
                        )
                    )
            return result
        # 查询实时榜单（Ranking 表）
        realtime_query = (
            db.query(Ranking)
            .filter(
                or_(
                    Ranking.ranking_config_id == scope_id,
                    Ranking.ranking_type == scope_id,
                )
            )
        )

        realtime_rows = realtime_query.order_by(Ranking.position).all()
        result = []
        for row in realtime_rows:
            app = db.query(App).filter(App.id == row.app_id).first()
            if app and app.section == "province":
                if company and (app.company or app.org) != company:
                    continue
                result.append(
                    _to_ranking_item(
                        app=app,
                        ranking_config_id_value=row.ranking_config_id,
                        position=row.position,
                        tag=row.tag,
                        score=row.score,
                        metric_type=row.metric_type,
                        value_dimension=row.value_dimension,
                        usage_30d=row.usage_30d,
                        declared_at=row.declared_at,
                        updated_at=row.updated_at,
                    )
                )
        return result
    except Exception as e:
        # 数据库表结构可能不完整，返回空列表
        print(f"Error in list_rankings: {e}")
        return []


@router.get(f"/recommendations", response_model=list[Recommendation])
def recommendations():
    return [
        Recommendation(title="智能客服助手", scene="7×24 小时自动应答"),
        Recommendation(title="AI会议助手", scene="自动生成会议纪要"),
        Recommendation(title="智能数据分析", scene="一键生成分析报告"),
    ]


@router.get(f"/stats", response_model=Stats)
def app_stats(db: Session = Depends(get_db)):
    """
    获取申报统计数据
    数据来源：
    - pending: 数据库中状态为"pending"的申报数量
    - approved_period: 数据库中状态为"approved"的申报数量
    - total_apps: 数据库中所有应用的数量
    """
    pending = db.query(Submission).filter(Submission.status == "pending").count()
    approved_period = db.query(Submission).filter(Submission.status == "approved").count()
    total_apps = db.query(App).count()
    return Stats(pending=pending, approved_period=approved_period, total_apps=total_apps)


@router.get(f"/rules", response_model=list[RuleLink])
def rules():
    base = settings.oa_rule_base_url.rstrip("/")
    return [
        RuleLink(title="如何申报应用", href=f"{base}/ai-app-square/rules/submission"),
        RuleLink(title="上榜评选标准", href=f"{base}/ai-app-square/rules/ranking"),
        RuleLink(title="API接入指南", href=f"{base}/ai-app-square/rules/api-integration"),
    ]


@router.get(f"/rankings/historical", response_model=list[HistoricalRankingOut])
def list_historical_rankings(
    ranking_type: str = "excellent",
    company: str | None = Query(default=None, description="按公司筛选历史榜单"),
    period_date: date | None = Query(default=None, description="查询日期，格式：YYYY-MM-DD"),
    run_id: str | None = Query(default=None, description="可选发布批次ID；不传则日期模式返回最新 run_id"),
    db: Session = Depends(get_db)
):
    """
    获取历史榜单数据（默认返回最新发布批次的只读快照）
    """
    try:
        scope_id = resolve_ranking_scope_id(ranking_type=ranking_type)
        query = db.query(HistoricalRanking).filter(
            or_(
                HistoricalRanking.ranking_config_id == scope_id,
                HistoricalRanking.ranking_type == scope_id,
            )
        )
        target_date = period_date
        if target_date is None:
            latest_date_row = (
                db.query(HistoricalRanking.period_date)
                .filter(
                    or_(
                        HistoricalRanking.ranking_config_id == scope_id,
                        HistoricalRanking.ranking_type == scope_id,
                    )
                )
                .order_by(HistoricalRanking.period_date.desc())
                .first()
            )
            if latest_date_row is None:
                return []
            target_date = latest_date_row[0]

        query = query.filter(HistoricalRanking.period_date == target_date)
        if company:
            query = query.filter(HistoricalRanking.app_org == company)
        selected_run_id = run_id if run_id is not None else resolve_latest_run_id(db, scope_id, target_date)
        if selected_run_id is not None:
            query = query.filter(HistoricalRanking.run_id == selected_run_id)
        else:
            query = query.filter(HistoricalRanking.run_id.is_(None))
        rows = query.order_by(HistoricalRanking.position).all()
        result: list[HistoricalRankingOut] = []
        for row in rows:
            app_company = row.app.company if row.app else row.app_org
            app_department = row.app.department if row.app else ""
            result.append(
                HistoricalRankingOut(
                    id=row.id,
                    ranking_type=row.ranking_type,
                    period_date=row.period_date,
                    run_id=row.run_id,
                    position=row.position,
                    app_id=row.app_id,
                    app_name=row.app_name,
                    app_org=row.app_org,
                    company=app_company or row.app_org,
                    department=app_department or "",
                    tag=row.tag,
                    score=row.score,
                    metric_type=row.metric_type,
                    value_dimension=row.value_dimension,
                    usage_30d=row.usage_30d,
                    created_at=row.created_at,
                )
            )
        return result
    except Exception as e:
        return []


@router.get(f"/rankings/available-dates")
def list_available_ranking_dates(
    ranking_type: str = "excellent",
    db: Session = Depends(get_db)
):
    """
    获取可用的榜单日期列表
    """
    try:
        scope_id = resolve_ranking_scope_id(ranking_type=ranking_type)
        dates = (
            db.query(HistoricalRanking.period_date)
            .filter(
                or_(
                    HistoricalRanking.ranking_config_id == scope_id,
                    HistoricalRanking.ranking_type == scope_id,
                )
            )
            .distinct()
            .order_by(HistoricalRanking.period_date.desc())
            .all()
        )
        return {"dates": [d[0].isoformat() for d in dates]}
    except Exception as e:
        return {"dates": []}


@router.post(f"/rankings/sync")
def sync_rankings(
    run_id: str | None = Query(default=None, description="可选发布批次ID；不传则自动生成 UUID"),
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    同步排行榜数据，确保集团应用和省内应用信息保持一致
    """
    try:
        updated_count, generated_run_id = sync_rankings_service(
            db,
            run_id=run_id,
            actor=ranking_audit_actor(admin_user),
        )
        return {"message": "排行榜数据同步成功", "updated_count": updated_count, "run_id": generated_run_id}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"同步失败: {str(exc)}") from exc


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
                message="无可发布应用：请先在“应用参与”中启用至少一个应用",
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


@router.post(f"/rankings/publish")
def publish_rankings(
    run_id: str | None = Query(default=None, description="可选发布批次ID；不传则自动生成 UUID"),
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    """榜单发布入口：预校验 + 同步 + 发布审计。"""
    try:
        checked = validate_publish_preconditions(db)
        actor = ranking_audit_actor(admin_user)
        updated_count, generated_run_id = sync_rankings_service(db, run_id=run_id, actor=actor)
        write_ranking_audit_log(
            db,
            action="ranking_publish_completed",
            ranking_type="all",
            ranking_config_id=None,
            period_date=datetime.utcnow().date(),
            run_id=generated_run_id,
            actor=actor,
            payload_summary=(
                f"active_configs={checked['active_configs']},"
                f"enabled_settings={checked['enabled_settings']},"
                f"updated_count={updated_count}"
            ),
        )
        db.commit()
        return {
            "message": "榜单发布成功",
            "updated_count": updated_count,
            "run_id": generated_run_id,
            "published_date": datetime.utcnow().date().isoformat(),
            "checked": checked,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发布失败: {str(exc)}") from exc

