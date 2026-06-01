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

@router.post(f"/integration/users/sync", response_model=UserImportResponse)
def sync_users_from_integration(
    payload: UserImportRequest,
    request: Request,
    _: None = Depends(require_user_sync_token),
    db: Session = Depends(get_db),
):
    try:
        result = upsert_users(db, payload=payload)
        write_action_log(
            db,
            action="user.sync_external",
            actor_user=None,
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
        raise HTTPException(status_code=500, detail=f"外部用户同步失败: {str(exc)}") from exc

