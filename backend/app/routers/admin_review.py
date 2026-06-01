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

APP_STATUS_VALUES = {"available", "approval", "beta", "offline"}
APP_DIFFICULTY_VALUES = {"Low", "Medium", "High"}
VALUE_DIMENSIONS = {"cost_reduction", "efficiency_gain", "perception_uplift", "revenue_growth"}
DATA_LEVEL_VALUES = {"L1", "L2", "L3", "L4"}

@router.post(f"/submissions/{{submission_id}}/approve-and-create-app")
def approve_submission_and_create_app(
    submission_id: int,
    request: Request,
    payload: SubmissionApprovePayload | None = None,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    审批申报并创建应用,同时传递排行榜参数
    只有通过审核的省内应用才能进入排行榜评估体系
    """
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="申报不存在")
        
        if submission.status != "pending":
            raise HTTPException(status_code=400, detail="申报状态不是待审批")

        resolved_status = (payload.status if payload and payload.status else "available")
        if resolved_status not in APP_STATUS_VALUES:
            raise HTTPException(status_code=422, detail="Invalid status")

        resolved_access_mode = (payload.access_mode if payload and payload.access_mode else "profile")
        if resolved_access_mode not in {"direct", "profile"}:
            raise HTTPException(status_code=422, detail="Invalid access_mode")
        resolved_monthly_calls = (
            payload.monthly_calls
            if payload and payload.monthly_calls is not None
            else submission.monthly_calls
        )
        resolved_difficulty = (
            payload.difficulty.strip()
            if payload and payload.difficulty
            else (submission.difficulty or "Medium")
        )
        if resolved_difficulty not in APP_DIFFICULTY_VALUES:
            raise HTTPException(status_code=422, detail="Invalid difficulty")

        normalized_name = normalize_dedupe_text(submission.app_name)
        normalized_unit = normalize_dedupe_text(submission.unit_name)
        existing_app = (
            db.query(App)
            .filter(
                App.section == "province",
                func.lower(func.trim(App.name)) == normalized_name,
                func.lower(func.trim(App.org)) == normalized_unit,
            )
            .first()
        )
        if existing_app:
            raise HTTPException(status_code=409, detail="已存在同名同单位省内应用，不能重复创建")

        submission_document = (
            db.query(SubmissionImage)
            .filter(
                SubmissionImage.submission_id == submission_id,
                SubmissionImage.is_cover.is_(False),
            )
            .order_by(SubmissionImage.created_at.desc())
            .first()
        )
        document_url = submission_document.image_url if submission_document else ""
        approved_at = datetime.utcnow()

        app = App(
            name=submission.app_name,
            org=submission.unit_name,
            company=submission.company or submission.unit_name,
            department=submission.department or "",
            section="province",
            category=submission.category,
            description=submission.scenario,
            status=resolved_status,
            monthly_calls=resolved_monthly_calls if resolved_monthly_calls is not None else 0.0,
            release_date=datetime.now().date(),
            api_open=True,
            difficulty=resolved_difficulty,
            contact_name=submission.contact,
            highlight="",
            access_mode=resolved_access_mode,
            access_url=(
                payload.access_url.strip()
                if payload and payload.access_url
                else ""
            ),
            detail_doc_url=submission.detail_doc_url or document_url,
            detail_doc_name=submission.detail_doc_name or (submission_document.original_name if submission_document else ""),
            target_system=(
                payload.target_system.strip()
                if payload and payload.target_system
                else submission.embedded_system
            ),
            target_users=(payload.target_users.strip() if payload and payload.target_users else ""),
            problem_statement=submission.problem_statement,
            effectiveness_type=submission.effectiveness_type,
            effectiveness_metric=submission.effectiveness_metric,
            cover_image_url=submission.cover_image_url,
            created_by_user_id=submission.submitter_user_id,
            created_from_submission_id=submission.id,
            approved_by_user_id=(admin_user.id if admin_user else None),
            approved_at=approved_at,
            ranking_enabled=False,
            ranking_weight=1.0,
            ranking_tags="",
        )

        db.add(app)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="检测到重复应用创建请求，已拒绝")

        active_configs = (
            db.query(RankingConfig)
            .filter(RankingConfig.is_active.is_(True))
            .all()
        )
        for config in active_configs:
            db.add(
                AppRankingSetting(
                    app_id=app.id,
                    ranking_config_id=config.id,
                    is_enabled=False,
                    weight_factor=1.0,
                    custom_tags="",
                )
            )

        submission.status = "approved"
        submission.approved_at = approved_at
        submission.approved_by_user_id = admin_user.id if admin_user else None
        submission.rejected_at = None
        submission.rejected_by_user_id = None
        submission.rejected_reason = ""
        write_action_log(
            db,
            action="submission.approve",
            actor_user=admin_user,
            resource_type="submission",
            resource_id=str(submission.id),
            request_id=request.headers.get("X-Request-Id", ""),
            payload_summary=f"app_id={app.id},app_name={app.name}",
        )
        updated_count, run_id = sync_after_chain_mutation(
            db,
            "submission_approved_and_created_app",
            actor=ranking_audit_actor(admin_user),
        )
        db.refresh(app)

        return {
            "message": "审批成功并创建应用",
            "app_id": app.id,
            "synced": updated_count,
            "run_id": run_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.post(f"/submissions/{{submission_id}}/reject")
def reject_submission(
    submission_id: int,
    request: Request,
    reason: str | None = Body(default=None, embed=True),
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    拒绝申报
    """
    normalized_reason = validate_review_reason(reason)

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核申报可拒绝")

    submission.status = "rejected"
    submission.rejected_reason = normalized_reason
    submission.rejected_at = datetime.utcnow()
    submission.rejected_by_user_id = admin_user.id if admin_user else None
    submission.approved_at = None
    submission.approved_by_user_id = None
    write_action_log(
        db,
        action="submission.reject",
        actor_user=admin_user,
        resource_type="submission",
        resource_id=str(submission.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"reason={submission.rejected_reason}",
    )
    db.commit()
    return {
        "message": "申报已拒绝",
        "submission_id": submission_id,
        "reason": submission.rejected_reason,
    }


@router.get(f"/admin/app-change-requests", response_model=list[AppChangeRequestOut])
def list_app_change_requests(
    status: str | None = Query(default=None, description="按状态筛选：pending, approved, rejected"),
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    """管理员查看应用变更申请。"""
    query = db.query(AppChangeRequest)
    if status:
        query = query.filter(AppChangeRequest.status == status)
    return query.order_by(AppChangeRequest.created_at.desc()).all()


@router.post(f"/admin/app-change-requests/{{change_request_id}}/approve")
def approve_app_change_request(
    change_request_id: int,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    """管理员通过应用变更申请，并更新正式应用与来源申报快照。"""
    change_request = db.query(AppChangeRequest).filter(AppChangeRequest.id == change_request_id).first()
    if not change_request:
        raise HTTPException(status_code=404, detail="应用变更申请不存在")
    if change_request.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核变更申请可通过")

    app_row = db.query(App).filter(App.id == change_request.app_id).first()
    if not app_row:
        raise HTTPException(status_code=404, detail="变更申请关联的应用不存在")
    source_submission = (
        db.query(Submission)
        .filter(Submission.id == change_request.source_submission_id)
        .first()
    )
    if not source_submission:
        raise HTTPException(status_code=404, detail="变更申请关联的来源申报不存在")

    ensure_no_duplicate_active_submission(
        db,
        app_name=change_request.app_name,
        unit_name=change_request.unit_name,
        exclude_submission_id=source_submission.id,
    )
    ensure_no_duplicate_province_app(
        db,
        app_name=change_request.app_name,
        unit_name=change_request.unit_name,
        exclude_app_id=app_row.id,
    )

    submission_fields = {
        key: getattr(change_request, key)
        for key in (
            "app_name",
            "unit_name",
            "company",
            "department",
            "contact",
            "contact_phone",
            "contact_email",
            "category",
            "scenario",
            "embedded_system",
            "problem_statement",
            "effectiveness_type",
            "effectiveness_metric",
            "data_level",
            "expected_benefit",
            "monthly_calls",
            "difficulty",
            "cover_image_url",
            "detail_doc_url",
            "detail_doc_name",
        )
    }
    apply_submission_fields(source_submission, submission_fields)
    apply_change_request_to_app(app_row, change_request)
    change_request.status = "approved"
    change_request.review_reason = ""
    change_request.reviewed_at = datetime.utcnow()
    change_request.reviewer_user_id = admin_user.id if admin_user else None

    write_action_log(
        db,
        action="app_change_request.approve",
        actor_user=admin_user,
        resource_type="app_change_request",
        resource_id=str(change_request.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"app_id={app_row.id},app_name={app_row.name}",
    )
    updated_count, run_id = sync_after_chain_mutation(
        db,
        "app_change_request_approved",
        actor=ranking_audit_actor(admin_user),
    )
    return {
        "message": "应用变更已通过",
        "change_request_id": change_request.id,
        "app_id": app_row.id,
        "synced": updated_count,
        "run_id": run_id,
    }


@router.post(f"/admin/app-change-requests/{{change_request_id}}/reject")
def reject_app_change_request(
    change_request_id: int,
    request: Request,
    reason: str | None = Body(default=None, embed=True),
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    """管理员驳回应用变更申请。"""
    normalized_reason = validate_review_reason(reason)
    change_request = db.query(AppChangeRequest).filter(AppChangeRequest.id == change_request_id).first()
    if not change_request:
        raise HTTPException(status_code=404, detail="应用变更申请不存在")
    if change_request.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核变更申请可驳回")

    change_request.status = "rejected"
    change_request.review_reason = normalized_reason
    change_request.reviewed_at = datetime.utcnow()
    change_request.reviewer_user_id = admin_user.id if admin_user else None
    write_action_log(
        db,
        action="app_change_request.reject",
        actor_user=admin_user,
        resource_type="app_change_request",
        resource_id=str(change_request.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"reason={change_request.review_reason}",
    )
    db.commit()
    return {
        "message": "应用变更已驳回",
        "change_request_id": change_request.id,
        "reason": change_request.review_reason,
    }

@router.post(f"/admin/group-apps", response_model=AppDetail)
def create_group_app(
    payload: GroupAppCreate,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    集团应用专用录入接口
    集团应用为系统内置，通过此接口直接录入，不走申报流程
    """
    try:
        validate_group_app_payload(payload)
        app = App(
            name=payload.name,
            org=payload.org,
            company=payload.org,
            department="",
            section="group",  # 集团应用
            category=payload.category,
            description=payload.description,
            status=payload.status,
            monthly_calls=payload.monthly_calls,
            release_date=datetime.now().date(),
            api_open=payload.api_open,
            difficulty=payload.difficulty,
            contact_name=payload.contact_name,
            highlight=payload.highlight,
            access_mode=payload.access_mode,
            access_url=payload.access_url,
            detail_doc_url="",
            detail_doc_name="",
            target_system=payload.target_system,
            target_users=payload.target_users,
            problem_statement=payload.problem_statement,
            effectiveness_type=payload.effectiveness_type,
            effectiveness_metric=payload.effectiveness_metric,
            cover_image_url=payload.cover_image_url,
            created_by_user_id=(admin_user.id if admin_user else None),
            created_from_submission_id=None,
            approved_by_user_id=(admin_user.id if admin_user else None),
            approved_at=datetime.utcnow(),
            ranking_enabled=False,
            ranking_weight=1.0,
            ranking_tags="",
        )
        db.add(app)
        db.flush()
        write_action_log(
            db,
            action="app.create_group",
            actor_user=admin_user,
            resource_type="app",
            resource_id=str(app.id),
            request_id=request.headers.get("X-Request-Id", ""),
            payload_summary=f"name={app.name},org={app.org}",
        )
        db.commit()
        db.refresh(app)
        return app
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建集团应用失败: {str(e)}")


@router.get(f"/admin/apps", response_model=PaginatedResponse[AppDetail])
def admin_list_apps(
    section: str | None = Query(default=None, description="group/province"),
    status: str | None = Query(default=None, description="available/approval/beta/offline"),
    company: str | None = Query(default=None, description="按公司筛选"),
    q: str | None = Query(default=None, description="按名称或描述搜索"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    query = db.query(App)
    if section:
        if section not in {"group", "province"}:
            raise HTTPException(status_code=422, detail="Invalid section")
        query = query.filter(App.section == section)
    if status:
        if status not in APP_STATUS_VALUES:
            raise HTTPException(status_code=422, detail="Invalid status")
        query = query.filter(App.status == status)
    if company:
        query = query.filter(App.company == company)
    if q:
        query = query.filter(
            or_(
                App.name.contains(q),
                App.description.contains(q),
                App.org.contains(q),
                App.company.contains(q),
                App.department.contains(q),
                App.category.contains(q),
            )
        )
    return paginate_query(query.order_by(App.id), page, page_size)


@router.put(f"/admin/apps/{{app_id}}/status")
def admin_update_app_status(
    app_id: int,
    payload: AdminAppStatusUpdate,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")

    new_status = payload.status.strip()
    if new_status not in APP_STATUS_VALUES:
        raise HTTPException(status_code=422, detail="Invalid status")

    old_status = app.status
    disabled_settings = 0
    app.status = new_status

    # 省内应用下架后自动失去参与资格（历史快照保留，新榜单不再可选）。
    if app.section == "province" and new_status == "offline":
        disabled_settings = (
            db.query(AppRankingSetting)
            .filter(
                AppRankingSetting.app_id == app.id,
                AppRankingSetting.is_enabled.is_(True),
            )
            .update(
                {
                    AppRankingSetting.is_enabled: False,
                    AppRankingSetting.updated_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )

    write_action_log(
        db,
        action="app.status_updated",
        actor_user=admin_user,
        resource_type="app",
        resource_id=str(app.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=(
            f"section={app.section},old={old_status},new={new_status},"
            f"disabled_settings={disabled_settings}"
        ),
    )

    synced = 0
    run_id = ""
    if app.section == "province":
        synced, run_id = sync_after_chain_mutation(
            db,
            "app_status_updated",
            actor=ranking_audit_actor(admin_user),
        )
    else:
        db.commit()
    db.refresh(app)
    return {
        "message": "应用状态已更新",
        "app_id": app.id,
        "old_status": old_status,
        "new_status": app.status,
        "disabled_settings": disabled_settings,
        "synced": synced,
        "run_id": run_id,
    }


# Image upload configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
