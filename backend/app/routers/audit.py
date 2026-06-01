"""Auto-generated router."""
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

AUDIT_EVENT_WHITELIST = {
    "auth.intent.submit.click",
    "auth.intent.admin.click",
    "route.guard.redirect_login.submit",
    "route.guard.redirect_login.admin",
    "auth.login.success",
    "auth.login.denied_admin_role",
    "submission.modal.auto_open",
    "submission.create.success",
    "submission.create.failed",
    "route.guard.denied_admin",
}

@router.get(f"/action-logs", response_model=list[ActionLogOut])
def get_action_logs(
    limit: int = Query(default=100, ge=1, le=500),
    action: str | None = Query(default=None),
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    query = db.query(ActionLog).options(joinedload(ActionLog.actor_user))
    if action:
        query = query.filter(ActionLog.action == action)
    rows = (
        query.order_by(ActionLog.created_at.desc(), ActionLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        ActionLogOut(
            id=row.id,
            actor_user_id=row.actor_user_id,
            actor_username=row.actor_user.username if row.actor_user else "",
            actor_role=row.actor_role,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            request_id=row.request_id,
            payload_summary=row.payload_summary,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post(f"/audit/events")
def create_audit_event(
    payload: AuditEventIn,
    request: Request,
    db: Session = Depends(get_db),
    auth_session: AuthSession | None = Depends(get_optional_auth_session),
):
    enforce_rate_limit(
        request,
        bucket="audit_events",
        limit=60,
        window_seconds=60,
    )
    event_name = payload.event_name.strip()
    if event_name not in AUDIT_EVENT_WHITELIST:
        raise HTTPException(status_code=422, detail="unsupported audit event")

    actor_user = auth_session.user if auth_session else None
    user_role = actor_user.role if actor_user else "anonymous"
    write_action_log(
        db,
        action=event_name,
        actor_user=actor_user,
        resource_type="audit_event",
        resource_id=(payload.context or "").strip()[:80],
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=build_audit_payload_summary(
            intent=payload.intent.strip(),
            result=payload.result.strip(),
            return_to=payload.return_to.strip(),
            context=payload.context.strip(),
            user_role=user_role,
        ),
    )
    db.commit()
    return {"ok": True}
