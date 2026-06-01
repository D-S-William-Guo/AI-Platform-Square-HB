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

@router.get(f"/admin/users", response_model=PaginatedResponse[UserPublic])
def list_users(
    q: str | None = Query(default=None),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        query = query.filter(
            or_(
                User.username.contains(q),
                User.chinese_name.contains(q),
                User.email.contains(q),
                User.company.contains(q),
                User.department.contains(q),
            )
        )
    if role:
        if role not in {"user", "admin"}:
            raise HTTPException(status_code=422, detail="Invalid role")
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))

    rows = paginate_query(query.order_by(User.id.asc()), page, page_size)
    return PaginatedResponse(
        items=[to_public_user(user) for user in rows.items],
        page=rows.page,
        page_size=rows.page_size,
        total=rows.total,
        total_pages=rows.total_pages,
    )


@router.post(f"/admin/users", response_model=UserPublic)
def create_admin_user(
    payload: AdminUserCreatePayload,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(func.lower(User.username) == payload.username.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")

    password = (payload.password or settings.user_default_password).strip()
    validate_new_password_or_422(password)
    user = User(
        username=payload.username.strip(),
        chinese_name=payload.chinese_name.strip(),
        role=payload.role,
        phone=payload.phone.strip(),
        email=payload.email.strip(),
        company=payload.company.strip(),
        department=payload.department.strip(),
        is_active=payload.is_active,
        can_submit=payload.can_submit,
        password_hash=hash_password(password),
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    write_action_log(
        db,
        action="user.created",
        actor_user=admin_user,
        resource_type="user",
        resource_id=str(user.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=(
            f"username={user.username},role={user.role},active={bool(user.is_active)},"
            f"can_submit={bool(user.can_submit)}"
        ),
    )
    db.commit()
    db.refresh(user)
    return user


@router.put(f"/admin/users/{{user_id}}", response_model=UserPublic)
def update_admin_user(
    user_id: int,
    payload: AdminUserUpdatePayload,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    next_role = payload.role
    next_active = bool(payload.is_active)

    if user.role == "admin" and next_role != "admin":
        active_admin_count = (
            db.query(User)
            .filter(User.role == "admin", User.is_active.is_(True))
            .count()
        )
        if user.is_active and active_admin_count <= 1:
            raise HTTPException(status_code=409, detail="至少需要保留一个启用状态的管理员账号")

    if user.role == "admin" and user.is_active and not next_active:
        active_admin_count = (
            db.query(User)
            .filter(User.role == "admin", User.is_active.is_(True))
            .count()
        )
        if active_admin_count <= 1:
            raise HTTPException(status_code=409, detail="至少需要保留一个启用状态的管理员账号")

    if admin_user and admin_user.id == user.id and not next_active:
        raise HTTPException(status_code=409, detail="不能禁用当前登录管理员账号")

    old_snapshot = {
        "role": user.role,
        "is_active": bool(user.is_active),
        "can_submit": bool(user.can_submit),
        "company": user.company or "",
        "department": user.department or "",
        "phone": user.phone or "",
        "email": user.email or "",
        "chinese_name": user.chinese_name,
    }

    user.chinese_name = payload.chinese_name.strip()
    user.company = payload.company.strip()
    user.department = payload.department.strip()
    user.phone = payload.phone.strip()
    user.email = payload.email.strip()
    user.role = next_role
    user.is_active = next_active
    user.can_submit = bool(payload.can_submit)

    if payload.password and payload.password.strip():
        password = payload.password.strip()
        validate_new_password_or_422(password)
        user.password_hash = hash_password(password)
        user.must_change_password = True
        user.password_changed_at = None

    if not next_active:
        db.query(AuthSession).filter(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None),
        ).update(
            {AuthSession.revoked_at: datetime.utcnow()},
            synchronize_session=False,
        )

    write_action_log(
        db,
        action="user.updated",
        actor_user=admin_user,
        resource_type="user",
        resource_id=str(user.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=(
            f"username={user.username},old_role={old_snapshot['role']},new_role={user.role},"
            f"old_active={old_snapshot['is_active']},new_active={bool(user.is_active)},"
            f"old_can_submit={old_snapshot['can_submit']},new_can_submit={bool(user.can_submit)},"
            f"old_company={old_snapshot['company']},new_company={user.company},"
            f"old_department={old_snapshot['department']},new_department={user.department}"
        ),
    )
    db.commit()
    db.refresh(user)
    return user


@router.put(f"/admin/users/{{user_id}}/role", response_model=UserPublic)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdatePayload,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == payload.role:
        return user

    if user.role == "admin" and payload.role != "admin":
        active_admin_count = (
            db.query(User)
            .filter(User.role == "admin", User.is_active.is_(True))
            .count()
        )
        if active_admin_count <= 1:
            raise HTTPException(status_code=409, detail="至少需要保留一个启用状态的管理员账号")

    old_role = user.role
    user.role = payload.role
    write_action_log(
        db,
        action="user.role_updated",
        actor_user=admin_user,
        resource_type="user",
        resource_id=str(user.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"username={user.username},old={old_role},new={user.role}",
    )
    db.commit()
    db.refresh(user)
    return user


@router.put(f"/admin/users/{{user_id}}/submit-permission", response_model=UserPublic)
def update_user_submit_permission(
    user_id: int,
    payload: UserSubmitPermissionUpdatePayload,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if bool(user.can_submit) == bool(payload.can_submit):
        return user

    old_value = bool(user.can_submit)
    user.can_submit = payload.can_submit
    write_action_log(
        db,
        action="user.submit_permission_updated",
        actor_user=admin_user,
        resource_type="user",
        resource_id=str(user.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"username={user.username},old={old_value},new={bool(user.can_submit)}",
    )
    db.commit()
    db.refresh(user)
    return user


@router.put(f"/admin/users/{{user_id}}/status", response_model=UserPublic)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdatePayload,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if bool(user.is_active) == bool(payload.is_active):
        return user

    if user.role == "admin" and user.is_active and not payload.is_active:
        active_admin_count = (
            db.query(User)
            .filter(User.role == "admin", User.is_active.is_(True))
            .count()
        )
        if active_admin_count <= 1:
            raise HTTPException(status_code=409, detail="至少需要保留一个启用状态的管理员账号")

    if admin_user and admin_user.id == user.id and not payload.is_active:
        raise HTTPException(status_code=409, detail="不能禁用当前登录管理员账号")

    old_status = bool(user.is_active)
    user.is_active = payload.is_active
    if not payload.is_active:
        db.query(AuthSession).filter(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None),
        ).update(
            {AuthSession.revoked_at: datetime.utcnow()},
            synchronize_session=False,
        )

    write_action_log(
        db,
        action="user.status_updated",
        actor_user=admin_user,
        resource_type="user",
        resource_id=str(user.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"username={user.username},old={old_status},new={bool(user.is_active)}",
    )
    db.commit()
    db.refresh(user)
    return user


@router.post(f"/admin/users/import", response_model=UserImportResponse)
def import_users(
    payload: UserImportRequest,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    try:
        result = upsert_users(db, payload=payload)
        write_action_log(
            db,
            action="user.import",
            actor_user=admin_user,
            resource_type="user",
            resource_id="",
            request_id=request.headers.get("X-Request-Id", ""),
            payload_summary=(
                f"source={result.source},created={result.created},"
                f"updated={result.updated},unchanged={result.unchanged}"
            ),
        )
        db.commit()
        return result
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
