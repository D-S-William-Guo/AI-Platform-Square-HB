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

@router.get(f"/submissions", response_model=list[SubmissionOut])
def list_submissions(
    status: str | None = Query(default=None, description="按状态筛选：pending, approved, rejected, withdrawn"),
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取申报列表
    """
    query = db.query(Submission)
    if status:
        query = query.filter(Submission.status == status)
    return query.order_by(Submission.created_at.desc()).all()


@router.post(f"/submissions", response_model=SubmissionOut)
def create_submission(
    payload: SubmissionCreate,
    request: Request,
    auth_session: AuthSession = Depends(require_submit_permission),
    db: Session = Depends(get_db),
):
    validate_submission_payload(payload)
    submitter = auth_session.user
    resolved_company = (submitter.company or payload.unit_name).strip()
    resolved_department = (submitter.department or "").strip()
    if not resolved_company:
        raise HTTPException(status_code=422, detail="当前账号未配置所属公司，无法提交申报")
    ensure_no_duplicate_active_submission(
        db,
        app_name=payload.app_name,
        unit_name=resolved_company,
    )

    submission_data = build_submission_update_fields(
        payload,
        company=resolved_company,
        department=resolved_department,
    )
    submission = Submission(
        **submission_data,
        manage_token=uuid.uuid4().hex,
        submitter_user_id=submitter.id,
    )
    db.add(submission)
    try:
        db.flush()
        write_action_log(
            db,
            action="submission.create",
            actor_user=submitter,
            resource_type="submission",
            resource_id=str(submission.id),
            request_id=request.headers.get("X-Request-Id", ""),
            payload_summary=f"app_name={submission.app_name},unit_name={submission.unit_name}",
        )
        write_action_log(
            db,
            action="submission.create.success",
            actor_user=submitter,
            resource_type="submission",
            resource_id=str(submission.id),
            request_id=request.headers.get("X-Request-Id", ""),
            payload_summary=build_audit_payload_summary(
                intent="submit",
                result="success",
                context="api.submissions.create",
                user_role=submitter.role,
            ),
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        write_action_log(
            db,
            action="submission.create.failed",
            actor_user=submitter,
            resource_type="submission",
            resource_id="",
            request_id=request.headers.get("X-Request-Id", ""),
            payload_summary=build_audit_payload_summary(
                intent="submit",
                result="failed",
                context="api.submissions.create.integrity_error",
                user_role=submitter.role,
            ),
        )
        db.commit()
        raise HTTPException(status_code=409, detail="检测到重复申报，请勿重复提交")
    db.refresh(submission)
    return submission


@router.get(f"/submissions/mine", response_model=list[SubmissionOut])
def list_my_submissions(
    auth_session: AuthSession = Depends(require_submit_permission),
    db: Session = Depends(get_db),
):
    """当前登录用户查看自己的申报记录。"""
    return (
        db.query(Submission)
        .filter(Submission.submitter_user_id == auth_session.user.id)
        .order_by(Submission.created_at.desc())
        .all()
    )


@router.put(f"/submissions/{{submission_id}}/mine", response_model=SubmissionOut)
def update_my_submission(
    submission_id: int,
    payload: SubmissionCreate,
    request: Request,
    auth_session: AuthSession = Depends(require_submit_permission),
    db: Session = Depends(get_db),
):
    """当前登录用户修改本人申报（仅 pending）。"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.submitter_user_id != auth_session.user.id:
        raise HTTPException(status_code=403, detail="无权限修改他人申报")
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核申报允许修改")

    resolved_company = (auth_session.user.company or payload.unit_name).strip()
    resolved_department = (auth_session.user.department or "").strip()
    if not resolved_company:
        raise HTTPException(status_code=422, detail="当前账号未配置所属公司，无法更新申报")

    ensure_no_duplicate_active_submission(
        db,
        app_name=payload.app_name,
        unit_name=resolved_company,
        exclude_submission_id=submission_id,
    )

    update_fields = build_submission_update_fields(
        payload,
        company=resolved_company,
        department=resolved_department,
    )
    apply_submission_fields(submission, update_fields)

    write_action_log(
        db,
        action="submission.update_mine",
        actor_user=auth_session.user,
        resource_type="submission",
        resource_id=str(submission.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"app_name={submission.app_name},unit_name={submission.unit_name}",
    )
    db.commit()
    db.refresh(submission)
    return submission


@router.post(f"/submissions/{{submission_id}}/mine/withdraw")
def withdraw_my_submission(
    submission_id: int,
    request: Request,
    auth_session: AuthSession = Depends(require_submit_permission),
    db: Session = Depends(get_db),
):
    """当前登录用户撤回本人申报（仅 pending）。"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.submitter_user_id != auth_session.user.id:
        raise HTTPException(status_code=403, detail="无权限撤回他人申报")
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核申报可撤回")

    submission.status = "withdrawn"
    write_action_log(
        db,
        action="submission.withdraw_mine",
        actor_user=auth_session.user,
        resource_type="submission",
        resource_id=str(submission.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"status={submission.status}",
    )
    db.commit()
    return {"message": "申报已撤回", "submission_id": submission_id}


@router.post(f"/submissions/{{submission_id}}/mine/resubmit", response_model=SubmissionOut)
def resubmit_my_rejected_submission(
    submission_id: int,
    payload: SubmissionCreate,
    request: Request,
    auth_session: AuthSession = Depends(require_submit_permission),
    db: Session = Depends(get_db),
):
    """当前登录用户修改本人已拒绝申报并重新提交审核。"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.submitter_user_id != auth_session.user.id:
        raise HTTPException(status_code=403, detail="无权限重新提交他人申报")
    if submission.status != "rejected":
        raise HTTPException(status_code=400, detail="仅已拒绝申报允许修改后重提")

    resolved_company = (auth_session.user.company or submission.company or payload.unit_name).strip()
    resolved_department = (auth_session.user.department or submission.department or "").strip()
    if not resolved_company:
        raise HTTPException(status_code=422, detail="当前账号未配置所属公司，无法重新提交申报")

    ensure_no_duplicate_active_submission(
        db,
        app_name=payload.app_name,
        unit_name=resolved_company,
        exclude_submission_id=submission_id,
    )
    ensure_no_duplicate_province_app(
        db,
        app_name=payload.app_name,
        unit_name=resolved_company,
    )

    update_fields = build_submission_update_fields(
        payload,
        company=resolved_company,
        department=resolved_department,
    )
    apply_submission_fields(submission, update_fields)
    submission.status = "pending"
    submission.rejected_at = None
    submission.rejected_by_user_id = None
    submission.rejected_reason = ""
    submission.approved_at = None
    submission.approved_by_user_id = None

    write_action_log(
        db,
        action="submission.resubmit_mine",
        actor_user=auth_session.user,
        resource_type="submission",
        resource_id=str(submission.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"app_name={submission.app_name},unit_name={submission.unit_name}",
    )
    db.commit()
    db.refresh(submission)
    return submission


@router.get(f"/app-change-requests/mine", response_model=list[AppChangeRequestOut])
def list_my_app_change_requests(
    auth_session: AuthSession = Depends(require_submit_permission),
    db: Session = Depends(get_db),
):
    """当前登录用户查看自己的应用变更申请。"""
    return (
        db.query(AppChangeRequest)
        .filter(AppChangeRequest.submitter_user_id == auth_session.user.id)
        .order_by(AppChangeRequest.created_at.desc())
        .all()
    )


@router.post(
    "/submissions/{submission_id}/mine/change-request",
    response_model=AppChangeRequestOut,
)
def create_my_app_change_request(
    submission_id: int,
    payload: SubmissionCreate,
    request: Request,
    auth_session: AuthSession = Depends(require_submit_permission),
    db: Session = Depends(get_db),
):
    """当前登录用户对本人已通过申报创建应用变更申请。"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.submitter_user_id != auth_session.user.id:
        raise HTTPException(status_code=403, detail="无权限修改他人申报创建的应用")
    if submission.status != "approved":
        raise HTTPException(status_code=400, detail="仅已通过申报允许发起应用变更申请")

    app_row = (
        db.query(App)
        .filter(
            App.section == "province",
            App.created_from_submission_id == submission.id,
        )
        .first()
    )
    if not app_row:
        raise HTTPException(status_code=404, detail="未找到该申报对应的省内应用")

    pending_change = (
        db.query(AppChangeRequest)
        .filter(
            AppChangeRequest.app_id == app_row.id,
            AppChangeRequest.status == "pending",
        )
        .first()
    )
    if pending_change:
        raise HTTPException(status_code=409, detail="该应用已有待审核变更申请，请等待处理后再提交")

    resolved_company = (submission.company or submission.unit_name or app_row.company or app_row.org).strip()
    resolved_department = (submission.department or app_row.department or "").strip()
    if not resolved_company:
        raise HTTPException(status_code=422, detail="应用缺少所属公司，无法创建变更申请")

    ensure_no_duplicate_active_submission(
        db,
        app_name=payload.app_name,
        unit_name=resolved_company,
        exclude_submission_id=submission.id,
    )
    ensure_no_duplicate_province_app(
        db,
        app_name=payload.app_name,
        unit_name=resolved_company,
        exclude_app_id=app_row.id,
    )

    change_fields = build_submission_update_fields(
        payload,
        company=resolved_company,
        department=resolved_department,
    )
    for compatibility_key in ("ranking_enabled", "ranking_weight", "ranking_tags", "ranking_dimensions"):
        change_fields.pop(compatibility_key, None)
    change_request = AppChangeRequest(
        app_id=app_row.id,
        source_submission_id=submission.id,
        submitter_user_id=auth_session.user.id,
        **change_fields,
    )
    db.add(change_request)
    db.flush()
    write_action_log(
        db,
        action="app_change_request.create",
        actor_user=auth_session.user,
        resource_type="app_change_request",
        resource_id=str(change_request.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"app_id={app_row.id},app_name={change_request.app_name}",
    )
    db.commit()
    db.refresh(change_request)
    return change_request
