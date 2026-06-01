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


# Helper: resolve settings snapshot (from main.py)
def _serialize_setting(app_setting):
    if app_setting is None: return {}
    return {"id":app_setting.id,"app_id":app_setting.app_id,"ranking_config_id":app_setting.ranking_config_id,"is_enabled":app_setting.is_enabled,"weight_factor":app_setting.weight_factor,"custom_tags":app_setting.custom_tags}

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


def _serialize_setting(setting: AppRankingSetting | None) -> dict[str, object]:
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


def _collect_config_dimension_ids(config: RankingConfig) -> set[int]:
    config_dim_ids: set[int] = set()
    if not config.dimensions_config:
        return config_dim_ids
    try:
        dimensions_config = json.loads(config.dimensions_config)
    except json.JSONDecodeError:
        return config_dim_ids
    if not isinstance(dimensions_config, list):
        return config_dim_ids
    for item in dimensions_config:
        if isinstance(item, dict) and isinstance(item.get("dim_id"), int):
            config_dim_ids.add(item["dim_id"])
    return config_dim_ids


@router.post(
    "/apps/{app_id}/ranking-settings/save",
    response_model=AppRankingSettingSaveResponse,
)
def save_app_ranking_setting_atomically(
    app_id: int,
    payload: AppRankingSettingSaveRequest,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    """原子保存应用榜单参与设置与维度评分，失败则整单回滚。"""
    try:
        app = db.query(App).filter(App.id == app_id).first()
        if not app:
            raise HTTPException(status_code=404, detail="应用不存在")
        if app.section == "province" and app.status == "offline":
            raise HTTPException(status_code=409, detail="省内下架应用不可新增、保存或启用榜单参与")

        config_id = payload.ranking_config_id.strip()
        if not config_id:
            raise HTTPException(
                status_code=422,
                detail=structured_error_detail(
                    code="validation_error",
                    message="参数校验失败",
                    field_errors=[{"field": "ranking_config_id", "message": "请选择榜单"}],
                ),
            )

        config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="榜单配置不存在")

        target_setting: AppRankingSetting | None = None
        if payload.setting_id is not None:
            target_setting = (
                db.query(AppRankingSetting)
                .filter(
                    AppRankingSetting.id == payload.setting_id,
                    AppRankingSetting.app_id == app_id,
                )
                .first()
            )
            if not target_setting:
                raise HTTPException(status_code=404, detail="榜单设置不存在")
        else:
            target_setting = (
                db.query(AppRankingSetting)
                .filter(
                    AppRankingSetting.app_id == app_id,
                    AppRankingSetting.ranking_config_id == config_id,
                )
                .first()
            )

        duplicate_setting = (
            db.query(AppRankingSetting)
            .filter(
                AppRankingSetting.app_id == app_id,
                AppRankingSetting.ranking_config_id == config_id,
                AppRankingSetting.id != (target_setting.id if target_setting else -1),
            )
            .first()
        )
        if duplicate_setting:
            raise HTTPException(status_code=409, detail="该应用已参与所选榜单，请直接编辑已有配置")

        config_dim_ids = _collect_config_dimension_ids(config)
        active_dims = {
            dim.id: dim
            for dim in db.query(RankingDimension)
            .filter(RankingDimension.id.in_(config_dim_ids))
            .filter(RankingDimension.is_active.is_(True))
            .all()
        } if config_dim_ids else {}

        field_errors: list[dict[str, str]] = []
        seen_dimension_ids: set[int] = set()
        for index, item in enumerate(payload.dimension_scores):
            field_prefix = f"dimension_scores[{index}]"
            if item.dimension_id in seen_dimension_ids:
                field_errors.append({"field": f"{field_prefix}.dimension_id", "message": "维度重复提交"})
                continue
            seen_dimension_ids.add(item.dimension_id)
            if item.dimension_id not in config_dim_ids:
                field_errors.append({"field": f"{field_prefix}.dimension_id", "message": "该维度不属于当前榜单配置"})
                continue
            if item.dimension_id not in active_dims:
                field_errors.append({"field": f"{field_prefix}.dimension_id", "message": "维度不存在或未启用"})

        if field_errors:
            raise HTTPException(
                status_code=422,
                detail=structured_error_detail(
                    code="validation_error",
                    message="参数校验失败",
                    field_errors=field_errors,
                ),
            )

        before_snapshot = _serialize_setting(target_setting)
        if target_setting is None:
            target_setting = AppRankingSetting(
                app_id=app_id,
                ranking_config_id=config_id,
                is_enabled=payload.is_enabled,
                weight_factor=payload.weight_factor,
                custom_tags=payload.custom_tags,
            )
            db.add(target_setting)
            action = "app_ranking_setting_saved_created"
        else:
            target_setting.ranking_config_id = config_id
            target_setting.is_enabled = payload.is_enabled
            target_setting.weight_factor = payload.weight_factor
            target_setting.custom_tags = payload.custom_tags
            action = "app_ranking_setting_saved_updated"

        db.flush()
        today = datetime.now().date()
        updated_dimensions = 0
        for item in payload.dimension_scores:
            score_record = load_single_dimension_score(
                db,
                app_id=app_id,
                ranking_config_id=config_id,
                dimension_id=item.dimension_id,
                period_date=today,
            )
            dimension = active_dims[item.dimension_id]
            if score_record:
                score_record.score = item.score
                score_record.dimension_name = dimension.name
                score_record.weight = dimension.weight
                score_record.calculation_detail = f"手动调整评分: {item.score}分"
            else:
                db.add(
                    AppDimensionScore(
                        app_id=app_id,
                        ranking_config_id=config_id,
                        dimension_id=item.dimension_id,
                        dimension_name=dimension.name,
                        score=item.score,
                        weight=dimension.weight,
                        calculation_detail=f"手动调整评分: {item.score}分",
                        period_date=today,
                    )
                )
            updated_dimensions += 1

        after_snapshot = _serialize_setting(target_setting)
        actor = ranking_audit_actor(admin_user)
        write_ranking_audit_log(
            db,
            action=action,
            ranking_config_id=config_id,
            period_date=datetime.utcnow().date(),
            actor=actor,
            payload_summary=(
                f"app_id={app_id},before={json.dumps(before_snapshot, ensure_ascii=False)},"
                f"after={json.dumps(after_snapshot, ensure_ascii=False)},"
                f"updated_dimensions={updated_dimensions}"
            ),
        )
        synced, run_id = sync_after_chain_mutation(db, "app_ranking_setting_saved_atomic", actor=actor)
        db.refresh(target_setting)
        return {
            "setting": target_setting,
            "updated_dimensions": updated_dimensions,
            "synced": synced,
            "run_id": run_id,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存失败: {str(exc)}") from exc


@router.post(f"/apps/{{app_id}}/ranking-settings", response_model=AppRankingSettingOut)
def create_app_ranking_setting(
    app_id: int,
    payload: AppRankingSettingCreate,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    创建应用榜单设置
    """
    if not payload.ranking_config_id.strip():
        raise HTTPException(status_code=422, detail="ranking_config_id is required")

    # 检查应用是否存在
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    if app.section == "province" and app.status == "offline":
        raise HTTPException(status_code=409, detail="省内下架应用不可新增榜单参与")
    
    # 检查榜单配置是否存在
    config = db.query(RankingConfig).filter(RankingConfig.id == payload.ranking_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")
    
    # 检查是否已存在
    existing = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.app_id == app_id,
            AppRankingSetting.ranking_config_id == payload.ranking_config_id
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="该榜单设置已存在")
    
    setting = AppRankingSetting(
        app_id=app_id,
        **payload.model_dump()
    )
    db.add(setting)
    db.flush()
    actor = ranking_audit_actor(admin_user)
    write_ranking_audit_log(
        db,
        action="app_ranking_setting_created",
        ranking_config_id=payload.ranking_config_id,
        period_date=datetime.utcnow().date(),
        actor=actor,
        payload_summary=(
            f"app_id={app_id},before={{}},"
            f"after={json.dumps(_serialize_setting(setting), ensure_ascii=False)}"
        ),
    )
    sync_after_chain_mutation(db, "app_ranking_setting_created", actor=actor)
    db.refresh(setting)
    return setting


@router.put(f"/apps/{{app_id}}/ranking-settings/{{setting_id}}", response_model=AppRankingSettingOut)
def update_app_ranking_setting(
    app_id: int,
    setting_id: int,
    payload: AppRankingSettingUpdate,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新应用榜单设置
    """
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")

    setting = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.id == setting_id,
            AppRankingSetting.app_id == app_id
        )
        .first()
    )
    if not setting:
        raise HTTPException(status_code=404, detail="榜单设置不存在")

    if app.section == "province" and app.status == "offline":
        only_disable = (
            payload.is_enabled is False
            and payload.ranking_config_id is None
            and payload.weight_factor is None
            and payload.custom_tags is None
        )
        if not only_disable:
            raise HTTPException(status_code=409, detail="省内下架应用不可新增、保存或启用榜单参与")

    before_snapshot = _serialize_setting(setting)
    if payload.ranking_config_id is not None and payload.ranking_config_id != setting.ranking_config_id:
        new_config_id = payload.ranking_config_id.strip()
        if not new_config_id:
            raise HTTPException(status_code=422, detail="ranking_config_id must not be empty")

        config = db.query(RankingConfig).filter(RankingConfig.id == new_config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="榜单配置不存在")

        duplicate_setting = (
            db.query(AppRankingSetting)
            .filter(
                AppRankingSetting.app_id == app_id,
                AppRankingSetting.ranking_config_id == new_config_id,
                AppRankingSetting.id != setting_id,
            )
            .first()
        )
        if duplicate_setting:
            raise HTTPException(status_code=400, detail="该榜单设置已存在")

        setting.ranking_config_id = new_config_id

    if payload.is_enabled is not None:
        setting.is_enabled = payload.is_enabled
    if payload.weight_factor is not None:
        setting.weight_factor = payload.weight_factor
    if payload.custom_tags is not None:
        setting.custom_tags = payload.custom_tags

    after_snapshot = _serialize_setting(setting)
    actor = ranking_audit_actor(admin_user)
    write_ranking_audit_log(
        db,
        action="app_ranking_setting_updated",
        ranking_config_id=setting.ranking_config_id,
        period_date=datetime.utcnow().date(),
        actor=actor,
        payload_summary=(
            f"app_id={app_id},before={json.dumps(before_snapshot, ensure_ascii=False)},"
            f"after={json.dumps(after_snapshot, ensure_ascii=False)}"
        ),
    )
    sync_after_chain_mutation(db, "app_ranking_setting_updated", actor=actor)
    db.refresh(setting)
    return setting


@router.delete(f"/apps/{{app_id}}/ranking-settings/{{setting_id}}")
def delete_app_ranking_setting(
    app_id: int,
    setting_id: int,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    删除应用榜单设置
    """
    setting = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.id == setting_id,
            AppRankingSetting.app_id == app_id
        )
        .first()
    )
    if not setting:
        raise HTTPException(status_code=404, detail="榜单设置不存在")

    before_snapshot = _serialize_setting(setting)
    actor = ranking_audit_actor(admin_user)
    write_ranking_audit_log(
        db,
        action="app_ranking_setting_deleted",
        ranking_config_id=setting.ranking_config_id,
        period_date=datetime.utcnow().date(),
        actor=actor,
        payload_summary=(
            f"app_id={app_id},before={json.dumps(before_snapshot, ensure_ascii=False)},"
            "after={}"
        ),
    )
    db.delete(setting)
    synced, run_id = sync_after_chain_mutation(db, "app_ranking_setting_deleted", actor=actor)
    return {"message": "榜单设置已删除", "synced": synced, "run_id": run_id}


@router.get(f"/app-ranking-settings", response_model=list[AppRankingSettingOut])
def list_all_app_ranking_settings(
    ranking_config_id: Optional[str] = None,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取所有应用榜单设置列表（支持按榜单配置筛选）
    """
    query = db.query(AppRankingSetting).options(
        joinedload(AppRankingSetting.app),
        joinedload(AppRankingSetting.ranking_config)
    )

    query = query.filter(AppRankingSetting.ranking_config_id.is_not(None))

    if ranking_config_id:
        query = query.filter(AppRankingSetting.ranking_config_id == ranking_config_id)
    
    settings_list = query.all()
    return settings_list

