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

APP_STATUS_VALUES = {"available", "approval", "beta", "offline"}

@router.get(f"/apps", response_model=list[AppDetail])
def list_apps(
    section: str | None = Query(default=None),
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    company: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(App)
    if section:
        query = query.filter(App.section == section)
    if status:
        if status not in APP_STATUS_VALUES:
            raise HTTPException(status_code=422, detail="Invalid status")
        query = query.filter(App.status == status)
    else:
        # 对外列表默认隐藏下架应用；管理端请使用 /api/admin/apps。
        query = query.filter(App.status != "offline")
    if category and category != "全部":
        query = query.filter(App.category == category)
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
            )
        )

    return query.order_by(App.id).all()


@router.get(f"/apps/{{app_id}}", response_model=AppDetail)
def get_app_detail(app_id: int, db: Session = Depends(get_db)):
    item = db.query(App).filter(App.id == app_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="App not found")
    return item


