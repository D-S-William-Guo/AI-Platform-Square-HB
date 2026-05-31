"""认证路由: login, logout, me, change-password, provider, sso exchange."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth_utils import generate_session_token, hash_password, verify_password
from ..config import is_auth_cookie_secure, settings
from ..database import get_db
from ..dependencies import (
    build_audit_payload_summary,
    enforce_rate_limit,
    reject_if_password_change_required,
    require_auth_session,
    to_public_user,
    validate_new_password_or_422,
    write_action_log,
)
from ..identity import get_identity_provider
from ..models import AuthSession, User
from ..schemas import (
    AuthAssertionExchangeRequest,
    AuthLoginRequest,
    AuthLoginResponse,
    AuthMeResponse,
    AuthProviderInfoResponse,
    ChangePasswordRequest,
)

router = APIRouter(prefix=settings.api_prefix)
identity_provider = get_identity_provider(settings)


@router.post("/auth/login", response_model=AuthLoginResponse)
def auth_login(
    payload: AuthLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    identity_provider.ensure_password_login_allowed()
    username = payload.username.strip()
    enforce_rate_limit(
        request,
        bucket="auth_login",
        limit=10,
        window_seconds=60,
        key_suffix=username.lower(),
        detail="登录尝试过于频繁，请约1分钟后重试",
    )
    user = (
        db.query(User)
        .filter(func.lower(User.username) == username.lower())
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    ttl_hours = max(1, settings.auth_session_ttl_hours)
    issued_at = datetime.utcnow()
    expires_at = issued_at + timedelta(hours=ttl_hours)
    token = generate_session_token()

    db.add(
        AuthSession(
            user_id=user.id,
            token_jti=token,
            issued_at=issued_at,
            expires_at=expires_at,
            ip=(request.client.host if request.client else ""),
            user_agent=request.headers.get("user-agent", ""),
        )
    )
    write_action_log(
        db,
        action="auth.login",
        actor_user=user,
        resource_type="session",
        resource_id=token[:16],
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary="login_success",
    )
    write_action_log(
        db,
        action="auth.login.success",
        actor_user=user,
        resource_type="auth",
        resource_id=user.username,
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=build_audit_payload_summary(
            intent="",
            result="success",
            context="auth.login",
            user_role=user.role,
        ),
    )
    db.commit()

    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=is_auth_cookie_secure(settings),
        samesite="lax",
        max_age=ttl_hours * 3600,
        path="/",
    )

    return AuthLoginResponse(
        access_token=token,
        token_type="bearer",
        expires_at=expires_at,
        user=to_public_user(user),
    )


@router.get("/auth/provider", response_model=AuthProviderInfoResponse)
def get_auth_provider_info():
    descriptor = identity_provider.describe()
    return AuthProviderInfoResponse(
        mode=descriptor.mode,
        display_name=descriptor.display_name,
        login_url=descriptor.login_url,
        local_login_enabled=descriptor.local_login_enabled,
        configured=descriptor.configured,
        message=descriptor.message,
    )


@router.post("/auth/sso/exchange")
def exchange_auth_assertion(payload: AuthAssertionExchangeRequest):
    if settings.auth_provider_mode == "local":
        raise HTTPException(status_code=409, detail="当前环境未启用外部统一登录")
    identity_provider.exchange_assertion(payload.assertion)
    raise HTTPException(status_code=501, detail="统一登录断言交换尚未实现")


@router.get("/auth/me", response_model=AuthMeResponse)
def auth_me(auth_session: AuthSession = Depends(require_auth_session)):
    return AuthMeResponse(
        expires_at=auth_session.expires_at,
        user=to_public_user(auth_session.user),
    )


@router.post("/auth/logout")
def auth_logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth_session: AuthSession = Depends(require_auth_session),
):
    auth_session.revoked_at = datetime.utcnow()
    write_action_log(
        db,
        action="auth.logout",
        actor_user=auth_session.user,
        resource_type="session",
        resource_id=auth_session.token_jti[:16],
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary="logout_success",
    )
    db.commit()
    response.delete_cookie(settings.auth_cookie_name, path="/")
    return {"message": "已退出登录"}


@router.post("/auth/change-password", response_model=AuthMeResponse)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth_session: AuthSession = Depends(require_auth_session),
):
    user = auth_session.user
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="当前密码错误")

    new_password = payload.new_password.strip()
    validate_new_password_or_422(new_password)
    if verify_password(new_password, user.password_hash):
        raise HTTPException(status_code=422, detail="新密码不能与当前密码相同")

    now = datetime.utcnow()
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    user.password_changed_at = now
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.id != auth_session.id,
        AuthSession.revoked_at.is_(None),
    ).update(
        {AuthSession.revoked_at: now},
        synchronize_session=False,
    )
    write_action_log(
        db,
        action="auth.password.changed",
        actor_user=user,
        resource_type="user",
        resource_id=str(user.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary="self_service_password_change",
    )
    db.commit()
    db.refresh(user)
    return AuthMeResponse(
        expires_at=auth_session.expires_at,
        user=to_public_user(user),
    )
