"""Auto-generated router from main.py."""
import json as _json, logging, math, uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Body, Depends, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy import func, or_  # or_ still used for keyword search
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

@router.get(f"/ranking-dimensions", response_model=list[RankingDimensionOut])
def get_ranking_dimensions(
    is_active: bool | None = None,
    db: Session = Depends(get_db)
):
    """
    获取排行维度列表
    """
    query = db.query(RankingDimension)
    if is_active is not None:
        query = query.filter(RankingDimension.is_active == is_active)
    return query.order_by(RankingDimension.id).all()


@router.get(f"/ranking-dimensions/{{dimension_id}}/scores", response_model=list[AppDimensionScoreOut])
def list_dimension_scores(
    dimension_id: int,
    period_date: date | None = Query(default=None, description="查询日期，格式：YYYY-MM-DD"),
    ranking_config_id: str | None = Query(default=None, description="榜单配置ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定维度的应用评分列表
    """
    try:
        query = db.query(AppDimensionScore).filter(AppDimensionScore.dimension_id == dimension_id)
        if ranking_config_id is not None:
            query = query.filter(AppDimensionScore.ranking_config_id == ranking_config_id.strip())
        if period_date:
            query = query.filter(AppDimensionScore.period_date == period_date)
        else:
            today = datetime.now().date()
            query = query.filter(AppDimensionScore.period_date == today)
        return query.order_by(AppDimensionScore.score.desc()).all()
    except Exception as e:
        return []


@router.get(f"/apps/{{app_id}}/dimension-scores", response_model=list[AppDimensionScoreOut])
def list_app_dimension_scores(
    app_id: int,
    period_date: date | None = Query(default=None, description="查询日期，格式：YYYY-MM-DD"),
    ranking_config_id: str | None = Query(default=None, description="榜单配置ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定应用在各维度的评分详情
    """
    try:
        query = db.query(AppDimensionScore).filter(AppDimensionScore.app_id == app_id)
        if ranking_config_id is not None:
            query = query.filter(AppDimensionScore.ranking_config_id == ranking_config_id.strip())
        if period_date:
            query = query.filter(AppDimensionScore.period_date == period_date)
        else:
            today = datetime.now().date()
            query = query.filter(AppDimensionScore.period_date == today)
        return query.order_by(AppDimensionScore.dimension_id).all()
    except Exception as e:
        return []


@router.put(f"/apps/{{app_id}}/ranking-params")
def update_app_ranking_params(
    app_id: int,
    ranking_enabled: bool | None = None,
    ranking_weight: float | None = None,
    ranking_tags: str | None = None,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新应用排行参数
    """
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    if app.section == "province" and app.status == "offline":
        raise HTTPException(status_code=409, detail="省内下架应用不可参与榜单")

    if ranking_weight is not None and (ranking_weight < 0.1 or ranking_weight > 10.0):
        raise HTTPException(status_code=422, detail="ranking_weight must be between 0.1 and 10.0")
    if ranking_tags is not None and len(ranking_tags) > 255:
        raise HTTPException(status_code=422, detail="ranking_tags must not exceed 255 characters")
    
    if ranking_enabled is not None:
        app.ranking_enabled = ranking_enabled
    if ranking_weight is not None:
        app.ranking_weight = ranking_weight
    if ranking_tags is not None:
        app.ranking_tags = ranking_tags
    app.last_ranking_update = datetime.utcnow()
    
    updated_count, run_id = sync_after_chain_mutation(
        db,
        "app_ranking_params_updated",
        actor=ranking_audit_actor(admin_user),
    )
    db.refresh(app)
    return {"message": "排行参数更新成功", "app_id": app_id, "synced": updated_count, "run_id": run_id}


@router.put(f"/apps/{{app_id}}/dimension-scores/{{dimension_id}}")
def update_app_dimension_score_api(
    app_id: int,
    dimension_id: int,
    payload: DimensionScoreUpdate | None = None,
    score: int | None = Query(default=None, ge=0, le=100),
    ranking_config_id: str | None = Query(default=None, description="榜单配置ID"),
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新应用在某个维度的评分（手动调整）
    """
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    if app.section == "province" and app.status == "offline":
        raise HTTPException(status_code=409, detail="省内下架应用不可参与榜单评分")
    
    dimension = db.query(RankingDimension).filter(RankingDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="维度不存在")

    resolved_score = payload.score if payload is not None else score
    if resolved_score is None:
        raise HTTPException(status_code=422, detail="score is required")
    config_id = ranking_config_id.strip() if ranking_config_id else None
    if config_id:
        config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="榜单配置不存在")
    
    today = datetime.now().date()
    
    # 查找或创建评分记录
    score_record = load_single_dimension_score(
        db,
        app_id=app_id,
        ranking_config_id=config_id,
        dimension_id=dimension_id,
        period_date=today,
    )
    before_score = score_record.score if score_record else None

    if score_record:
        score_record.score = resolved_score
        score_record.dimension_name = dimension.name
        score_record.weight = dimension.weight
        score_record.calculation_detail = f"手动调整评分: {resolved_score}分"
    else:
        score_record = AppDimensionScore(
            app_id=app_id,
            ranking_config_id=config_id,
            dimension_id=dimension_id,
            dimension_name=dimension.name,
            period_date=today,
            score=resolved_score,
            weight=dimension.weight,
            calculation_detail=f"手动调整评分: {resolved_score}分"
        )
        db.add(score_record)
    actor = ranking_audit_actor(admin_user)
    write_ranking_audit_log(
        db,
        action="dimension_score_manual_saved",
        ranking_config_id=config_id,
        period_date=today,
        actor=actor,
        payload_summary=(
            f"app_id={app_id},dimension_id={dimension_id},"
            f"before={before_score},after={resolved_score}"
        ),
    )
    updated_count, run_id = sync_after_chain_mutation(db, "dimension_score_updated", actor=actor)
    db.refresh(score_record)
    return {
        "message": "维度评分更新成功",
        "app_id": app_id,
        "dimension_id": dimension_id,
        "score": resolved_score,
        "synced": updated_count,
        "run_id": run_id,
    }


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
            HistoricalRanking.ranking_config_id == scope_id
        )
        target_date = period_date
        if target_date is None:
            latest_date_row = (
                db.query(HistoricalRanking.period_date)
                .filter(HistoricalRanking.ranking_config_id == scope_id)
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
                    ranking_type=row.ranking_config_id,
                    ranking_config_id=row.ranking_config_id,
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
                HistoricalRanking.ranking_config_id == scope_id
            )
            .distinct()
            .order_by(HistoricalRanking.period_date.desc())
            .all()
        )
        return {"dates": [d[0].isoformat() for d in dates]}
    except Exception as e:
        return {"dates": []}


@router.get(f"/ranking-dimensions/{{dimension_id}}", response_model=RankingDimensionOut)
def get_ranking_dimension(
    dimension_id: int,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取排行维度详情
    """
    dimension = db.query(RankingDimension).filter(RankingDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="排行维度不存在")
    return dimension


@router.post(f"/ranking-dimensions", response_model=RankingDimensionOut)
def create_ranking_dimension(
    payload: RankingDimensionCreate,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    创建排行维度
    """
    # 检查名称是否已存在
    existing = db.query(RankingDimension).filter(RankingDimension.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="排行维度名称已存在")
    
    # 创建排行维度
    dimension = RankingDimension(**payload.model_dump())
    db.add(dimension)
    db.flush()
    
    actor = ranking_audit_actor(admin_user)
    # 记录日志
    log = RankingLog(
        action="create",
        dimension_id=dimension.id,
        dimension_name=dimension.name,
        changes=f"创建了排行维度: {dimension.name}",
        operator=actor
    )
    db.add(log)
    write_ranking_audit_log(
        db,
        action="ranking_dimension_created",
        period_date=datetime.utcnow().date(),
        actor=actor,
        payload_summary=f"dimension_id={dimension.id},name={dimension.name}",
    )
    sync_after_chain_mutation(db, "ranking_dimension_created", actor=actor)
    db.refresh(dimension)

    return dimension


@router.put(f"/ranking-dimensions/{{dimension_id}}", response_model=RankingDimensionOut)
def update_ranking_dimension(
    dimension_id: int,
    payload: RankingDimensionUpdate,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新排行维度
    """
    dimension = db.query(RankingDimension).filter(RankingDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="排行维度不存在")
    
    # 检查名称是否已被其他维度使用
    if payload.name and payload.name != dimension.name:
        existing = db.query(RankingDimension).filter(RankingDimension.name == payload.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="排行维度名称已存在")
    
    actor = ranking_audit_actor(admin_user)
    # 记录变更
    changes = []
    name_changed = False
    if payload.name and payload.name != dimension.name:
        changes.append(f"名称: {dimension.name} → {payload.name}")
        dimension.name = payload.name
        name_changed = True
    if payload.description is not None and payload.description != dimension.description:
        changes.append("描述已更新")
        dimension.description = payload.description
    if payload.calculation_method is not None and payload.calculation_method != dimension.calculation_method:
        changes.append("计算方法已更新")
        dimension.calculation_method = payload.calculation_method
    if payload.weight is not None and payload.weight != dimension.weight:
        changes.append(f"权重: {dimension.weight} → {payload.weight}")
        dimension.weight = payload.weight
    if payload.is_active is not None and payload.is_active != dimension.is_active:
        changes.append(f"状态: {'启用' if dimension.is_active else '禁用'} → {'启用' if payload.is_active else '禁用'}")
        dimension.is_active = payload.is_active
    
    # 维度更名需要级联更新快照字段，避免历史评分展示名称漂移
    if name_changed:
        (
            db.query(AppDimensionScore)
            .filter(AppDimensionScore.dimension_id == dimension.id)
            .update({"dimension_name": dimension.name}, synchronize_session=False)
        )
    
    # 记录日志
    if changes:
        log = RankingLog(
            action="update",
            dimension_id=dimension.id,
            dimension_name=dimension.name,
            changes="; ".join(changes),
            operator=actor
        )
        db.add(log)
        write_ranking_audit_log(
            db,
            action="ranking_dimension_updated",
            period_date=datetime.utcnow().date(),
            actor=actor,
            payload_summary=f"dimension_id={dimension.id},changes={' | '.join(changes)}",
        )
    sync_after_chain_mutation(db, "ranking_dimension_updated", actor=actor)
    db.refresh(dimension)

    return dimension


@router.delete(f"/ranking-dimensions/{{dimension_id}}")
def delete_ranking_dimension(
    dimension_id: int,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    删除排行维度
    """
    dimension = db.query(RankingDimension).filter(RankingDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="排行维度不存在")
    
    import json

    # 从榜单配置中剔除被删除维度
    touched_configs = 0
    for config in db.query(RankingConfig).all():
        try:
            dim_items = json.loads(config.dimensions_config) if config.dimensions_config else []
        except json.JSONDecodeError:
            dim_items = []
        filtered_items = [item for item in dim_items if item.get("dim_id") != dimension_id]
        if len(filtered_items) != len(dim_items):
            config.dimensions_config = json.dumps(filtered_items, ensure_ascii=False)
            touched_configs += 1

    removed_scores = (
        db.query(AppDimensionScore)
        .filter(AppDimensionScore.dimension_id == dimension_id)
        .delete(synchronize_session=False)
    )

    actor = ranking_audit_actor(admin_user)
    # 记录日志
    log = RankingLog(
        action="delete",
        # 删除动作不再保留外键，避免 FK 校验开启时阻塞删除
        dimension_id=None,
        dimension_name=dimension.name,
        changes=f"删除了排行维度: {dimension.name}",
        operator=actor
    )
    db.add(log)
    write_ranking_audit_log(
        db,
        action="ranking_dimension_deleted",
        period_date=datetime.utcnow().date(),
        actor=actor,
        payload_summary=(
            f"dimension_id={dimension.id},name={dimension.name},"
            f"removed_scores={removed_scores},touched_configs={touched_configs}"
        ),
    )

    # 删除排行维度
    db.delete(dimension)
    synced, run_id = sync_after_chain_mutation(db, "ranking_dimension_deleted", actor=actor)

    return {
        "message": "排行维度已删除",
        "removed_scores": removed_scores,
        "touched_configs": touched_configs,
        "synced": synced,
        "run_id": run_id,
    }


@router.get(f"/ranking-logs", response_model=list[RankingLogOut])
def get_ranking_logs(
    limit: int = 100,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取排行维度变更日志
    """
    return db.query(RankingLog).order_by(RankingLog.created_at.desc()).limit(limit).all()


@router.get(f"/ranking-audit-logs", response_model=list[RankingAuditLogOut])
def get_ranking_audit_logs(
    limit: int = 100,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """获取排行榜审计日志。"""
    return db.query(RankingAuditLog).order_by(RankingAuditLog.created_at.desc()).limit(limit).all()


@router.get(f"/ranking-configs", response_model=list[RankingConfigOut])
def list_ranking_configs(
    is_active: bool | None = Query(default=None, description="按启用状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取榜单配置列表
    """
    query = db.query(RankingConfig)
    if is_active is not None:
        query = query.filter(RankingConfig.is_active == is_active)
    return query.order_by(RankingConfig.id).all()


@router.get(f"/admin/ranking-configs", response_model=PaginatedResponse[RankingConfigOut])
def admin_list_ranking_configs(
    is_active: bool | None = Query(default=None, description="按启用状态筛选"),
    q: str | None = Query(default=None, description="按ID、名称或描述搜索"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    query = db.query(RankingConfig)
    if is_active is not None:
        query = query.filter(RankingConfig.is_active == is_active)
    if q:
        query = query.filter(
            or_(
                RankingConfig.id.contains(q),
                RankingConfig.name.contains(q),
                RankingConfig.description.contains(q),
            )
        )
    return paginate_query(query.order_by(RankingConfig.id), page, page_size)


@router.get(f"/ranking-configs/{{config_id}}", response_model=RankingConfigOut)
def get_ranking_config(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    获取榜单配置详情
    """
    config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")
    return config


@router.get(f"/ranking-configs/{{config_id}}/with-dimensions", response_model=RankingConfigWithDimensions)
def get_ranking_config_with_dimensions(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    获取榜单配置详情（包含维度配置）
    """
    config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")
    
    import json
    dimensions_config = json.loads(config.dimensions_config) if config.dimensions_config else []
    
    return {
        "id": config.id,
        "name": config.name,
        "description": config.description,
        "dimensions": [DimensionConfigItem(**d) for d in dimensions_config],
        "calculation_method": config.calculation_method,
        "is_active": config.is_active,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }


@router.post(f"/ranking-configs", response_model=RankingConfigOut)
def create_ranking_config(
    payload: RankingConfigCreate,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    创建榜单配置
    """
    # 检查ID是否已存在
    existing = db.query(RankingConfig).filter(RankingConfig.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="榜单配置ID已存在")
    
    config = RankingConfig(**payload.model_dump())
    db.add(config)
    db.flush()
    actor = ranking_audit_actor(admin_user)
    write_ranking_audit_log(
        db,
        action="ranking_config_created",
        ranking_config_id=config.id,
        period_date=datetime.utcnow().date(),
        actor=actor,
        payload_summary=f"name={config.name},is_active={config.is_active}",
    )
    sync_after_chain_mutation(db, "ranking_config_created", actor=actor)
    db.refresh(config)
    return config


@router.put(f"/ranking-configs/{{config_id}}", response_model=RankingConfigOut)
def update_ranking_config(
    config_id: str,
    payload: RankingConfigUpdate,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新榜单配置
    """
    config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")
    
    if payload.name is not None:
        config.name = payload.name
    if payload.description is not None:
        config.description = payload.description
    if payload.dimensions_config is not None:
        config.dimensions_config = payload.dimensions_config
    if payload.calculation_method is not None:
        config.calculation_method = payload.calculation_method
    if payload.is_active is not None:
        config.is_active = payload.is_active

    actor = ranking_audit_actor(admin_user)
    write_ranking_audit_log(
        db,
        action="ranking_config_updated",
        ranking_config_id=config.id,
        period_date=datetime.utcnow().date(),
        actor=actor,
        payload_summary="fields=name/description/dimensions_config/calculation_method/is_active",
    )
    sync_after_chain_mutation(db, "ranking_config_updated", actor=actor)
    db.refresh(config)
    return config


@router.delete(f"/ranking-configs/{{config_id}}")
def delete_ranking_config(
    config_id: str,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    删除榜单配置
    """
    config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")

    removed_settings = (
        db.query(AppRankingSetting)
        .filter(AppRankingSetting.ranking_config_id == config_id)
        .delete(synchronize_session=False)
    )
    removed_realtime = (
        db.query(Ranking)
        .filter(Ranking.ranking_config_id == config_id)
        .delete(synchronize_session=False)
    )
    removed_historical = (
        db.query(HistoricalRanking)
        .filter(HistoricalRanking.ranking_config_id == config_id)
        .delete(synchronize_session=False)
    )

    actor = ranking_audit_actor(admin_user)
    write_ranking_audit_log(
        db,
        action="ranking_config_deleted",
        ranking_config_id=config.id,
        period_date=datetime.utcnow().date(),
        actor=actor,
        payload_summary=(
            f"name={config.name},removed_settings={removed_settings},"
            f"removed_realtime={removed_realtime},removed_historical={removed_historical}"
        ),
    )
    db.delete(config)
    synced, run_id = sync_after_chain_mutation(db, "ranking_config_deleted", actor=actor)
    return {
        "message": "榜单配置已删除",
        "removed_settings": removed_settings,
        "removed_realtime": removed_realtime,
        "removed_historical": removed_historical,
        "synced": synced,
        "run_id": run_id,
    }


@router.get(f"/apps/{{app_id}}/ranking-settings", response_model=list[AppRankingSettingOut])
def list_app_ranking_settings(
    app_id: int,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取应用的榜单设置列表
    """
    settings_list = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.app_id == app_id,
            AppRankingSetting.ranking_config_id.is_not(None),
        )
        .options(joinedload(AppRankingSetting.ranking_config))
        .all()
    )
    return settings_list


def _serialize_setting_snapshot(setting: AppRankingSetting | None) -> dict[str, object]:
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


