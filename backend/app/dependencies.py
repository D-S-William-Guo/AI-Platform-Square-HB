"""FastAPI 共享依赖注入与认证/鉴权工具函数。

从 main.py 提取，作为路由器和服务层共用的基础设施。
"""

import json
import logging
import math
from collections import defaultdict, deque
from datetime import date, datetime, timedelta
from threading import Lock
from time import monotonic
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .auth_utils import hash_password, validate_password_strength
from .config import (
    is_auth_cookie_secure,
    is_development_environment,
    settings,
)
from .database import get_db
from .models import (
    ActionLog,
    AuthSession,
    RankingAuditLog,
    User,
)
from .schemas import (
    PaginatedResponse,
    UserImportRequest,
    UserImportResponse,
    UserPublic,
)

logger = logging.getLogger(__name__)

rate_limit_lock = Lock()
rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)


# ---------------------------------------------------------------------------
# 路由标识解析
# ---------------------------------------------------------------------------

def resolve_ranking_scope_id(ranking_type: str | None = None, ranking_config_id: str | None = None) -> str:
    """收敛榜单标识：统一使用 ranking_config_id，ranking_type 仅作兼容入参。"""
    return (ranking_config_id or ranking_type or "").strip() or "excellent"


# ---------------------------------------------------------------------------
# 会话与认证
# ---------------------------------------------------------------------------

def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    return authorization[7:].strip() or None


def load_active_session(db: Session, token: str | None) -> AuthSession | None:
    if not token:
        return None
    session = (
        db.query(AuthSession)
        .options(joinedload(AuthSession.user))
        .filter(AuthSession.token_jti == token)
        .first()
    )
    if not session:
        return None
    if session.revoked_at is not None:
        return None
    if session.expires_at <= datetime.utcnow():
        return None
    if not session.user or not session.user.is_active:
        return None
    return session


# ---------------------------------------------------------------------------
# FastAPI Depends 函数
# ---------------------------------------------------------------------------

def require_auth_session(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    auth_cookie_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
) -> AuthSession:
    token = extract_bearer_token(authorization) or auth_cookie_token
    if not token:
        raise HTTPException(status_code=401, detail="请先登录")
    session = load_active_session(db, token)
    if not session:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return session


def require_submit_permission(
    auth_session: AuthSession = Depends(require_auth_session),
) -> AuthSession:
    # Phase 2: 登录用户统一可申报，管理员也可沿用同一链路。
    reject_if_password_change_required(auth_session.user)
    return auth_session


def get_optional_auth_session(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    auth_cookie_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
) -> AuthSession | None:
    token = extract_bearer_token(authorization) or auth_cookie_token
    if not token:
        return None
    session = load_active_session(db, token)
    if not session:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return session


def require_admin_token(
    db: Session = Depends(get_db),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(default=None),
    auth_cookie_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
) -> User | None:
    bearer_token = extract_bearer_token(authorization)
    if x_admin_token:
        raise HTTPException(status_code=401, detail="X-Admin-Token 已下线，请使用管理员登录态")

    for candidate in (bearer_token, auth_cookie_token):
        if not candidate:
            continue
        session = load_active_session(db, candidate)
        if session:
            if session.user.role != "admin":
                raise HTTPException(status_code=403, detail="无权限访问")
            reject_if_password_change_required(session.user)
            return session.user
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")

    raise HTTPException(status_code=401, detail="请先登录管理员账号")


def require_user_sync_token(
    x_user_sync_token: str | None = Header(default=None, alias="X-User-Sync-Token"),
) -> None:
    configured = settings.user_sync_token.strip()
    if not configured:
        raise HTTPException(status_code=503, detail="USER_SYNC_TOKEN 未配置，外部用户同步接口已禁用")
    if not x_user_sync_token:
        raise HTTPException(status_code=401, detail="缺少用户同步令牌")
    if x_user_sync_token != configured:
        raise HTTPException(status_code=403, detail="用户同步令牌无效")


def require_development_mode() -> None:
    if not is_development_environment(settings):
        raise HTTPException(status_code=404, detail="Not found")


# ---------------------------------------------------------------------------
# 用户相关工具
# ---------------------------------------------------------------------------

def to_public_user(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        chinese_name=user.chinese_name,
        role=user.role,
        phone=user.phone or "",
        email=user.email or "",
        company=user.company or "",
        department=user.department or "",
        is_active=bool(user.is_active),
        can_submit=bool(user.can_submit),
        must_change_password=bool(user.must_change_password),
    )


def reject_if_password_change_required(user: User) -> None:
    if user.must_change_password:
        raise HTTPException(status_code=403, detail="请先修改初始密码")


def validate_new_password_or_422(password: str) -> None:
    try:
        validate_password_strength(password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# 通用数据工具
# ---------------------------------------------------------------------------

def paginate_query(query, page: int, page_size: int):
    total = query.order_by(None).count()
    total_pages = math.ceil(total / page_size) if total else 0
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


def structured_error_detail(
    *,
    code: str,
    message: str,
    field_errors: list[dict[str, str]] | None = None,
) -> dict:
    return {
        "code": code,
        "message": message,
        "field_errors": field_errors or [],
    }


def build_audit_payload_summary(
    *,
    intent: str = "",
    result: str = "",
    return_to: str = "",
    context: str = "",
    user_role: str = "anonymous",
) -> str:
    return json.dumps(
        {
            "intent": intent,
            "result": result,
            "return_to": return_to,
            "context": context,
            "user_role": user_role,
        },
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# 审计日志
# ---------------------------------------------------------------------------

def write_action_log(
    db: Session,
    *,
    action: str,
    actor_user: User | None = None,
    resource_type: str = "",
    resource_id: str = "",
    request_id: str = "",
    payload_summary: str = "",
) -> None:
    db.add(
        ActionLog(
            actor_user_id=actor_user.id if actor_user else None,
            actor_role=(actor_user.role if actor_user else ""),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            payload_summary=payload_summary,
        )
    )


def write_ranking_audit_log(
    db: Session,
    *,
    action: str,
    ranking_type: str | None = None,
    ranking_config_id: str | None = None,
    period_date: date | None = None,
    run_id: str | None = None,
    actor: str = "system",
    payload_summary: str = "",
) -> None:
    db.add(
        RankingAuditLog(
            action=action,
            ranking_type=ranking_type,
            ranking_config_id=ranking_config_id,
            period_date=period_date,
            run_id=run_id,
            actor=actor,
            payload_summary=payload_summary,
        )
    )


def ranking_audit_actor(user: User | None) -> str:
    return user.username if user else "system"


# ---------------------------------------------------------------------------
# 限流
# ---------------------------------------------------------------------------

def clear_rate_limit_state() -> None:
    with rate_limit_lock:
        rate_limit_buckets.clear()


def enforce_rate_limit(
    request: Request,
    *,
    bucket: str,
    limit: int,
    window_seconds: int,
    key_suffix: str = "",
    detail: str = "请求过于频繁，请稍后再试",
) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = monotonic()
    key = f"{bucket}:{client_ip}:{key_suffix.strip().lower()}"
    with rate_limit_lock:
        entries = rate_limit_buckets[key]
        while entries and now - entries[0] >= window_seconds:
            entries.popleft()
        if len(entries) >= limit:
            raise HTTPException(status_code=429, detail=detail)
        entries.append(now)


# ---------------------------------------------------------------------------
# 用户导入
# ---------------------------------------------------------------------------

def upsert_users(
    db: Session,
    *,
    payload: UserImportRequest,
) -> UserImportResponse:
    normalized_inputs: dict[str, dict] = {}
    for item in payload.users:
        username = item.username.strip()
        if not username:
            continue
        normalized_inputs[username.lower()] = {
            "username": username,
            "chinese_name": item.chinese_name.strip(),
            "phone": item.phone.strip(),
            "email": item.email.strip(),
            "company": item.company.strip(),
            "department": item.department.strip(),
            "is_active": item.is_active,
        }

    if not normalized_inputs:
        raise HTTPException(status_code=422, detail="导入用户列表为空")

    existing_rows = (
        db.query(User)
        .filter(func.lower(User.username).in_(list(normalized_inputs.keys())))
        .all()
    )
    existing_map = {row.username.lower(): row for row in existing_rows}

    created = 0
    updated = 0
    unchanged = 0

    for key, item in normalized_inputs.items():
        user = existing_map.get(key)
        if not user:
            db.add(
                User(
                    username=item["username"],
                    chinese_name=item["chinese_name"] or item["username"],
                    role="user",
                    phone=item["phone"],
                    email=item["email"],
                    company=item["company"],
                    department=item["department"],
                    is_active=item["is_active"],
                    can_submit=False,
                    password_hash=hash_password(settings.user_default_password),
                    must_change_password=True,
                )
            )
            created += 1
            continue

        changed = False
        if user.chinese_name != item["chinese_name"]:
            user.chinese_name = item["chinese_name"]
            changed = True
        if (user.phone or "") != item["phone"]:
            user.phone = item["phone"]
            changed = True
        if (user.email or "") != item["email"]:
            user.email = item["email"]
            changed = True
        if (user.company or "") != item["company"]:
            user.company = item["company"]
            changed = True
        if (user.department or "") != item["department"]:
            user.department = item["department"]
            changed = True
        if bool(user.is_active) != bool(item["is_active"]):
            user.is_active = item["is_active"]
            changed = True
            if not item["is_active"]:
                db.query(AuthSession).filter(
                    AuthSession.user_id == user.id,
                    AuthSession.revoked_at.is_(None),
                ).update(
                    {AuthSession.revoked_at: datetime.utcnow()},
                    synchronize_session=False,
                )

        if changed:
            updated += 1
        else:
            unchanged += 1

    db.flush()
    return UserImportResponse(
        created=created,
        updated=updated,
        unchanged=unchanged,
        source=payload.source,
    )
