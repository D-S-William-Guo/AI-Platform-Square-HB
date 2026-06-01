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
router = APIRouter()  # No prefix — frontend routes are at root level

# FRONTEND_DIST_DIR resolved at call time to allow monkeypatching in tests
def _frontend_dist_dir():
    return (Path(__file__).resolve().parents[3] / "frontend" / "dist").resolve()


def resolve_frontend_asset(full_path: str) -> Path | None:
    requested = full_path.strip("/")
    if not requested:
        return None
    dist = _frontend_dist_dir()
    requested_parts = [part for part in requested.split("/") if part]
    for idx in range(len(requested_parts)):
        candidate = (dist / Path(*requested_parts[idx:])).resolve()
        try:
            candidate.relative_to(dist)
        except ValueError:
            return None
        if candidate.is_file():
            return candidate
    return None


def get_frontend_index_file() -> Path | None:
    index_file = _frontend_dist_dir() / "index.html"
    if index_file.is_file():
        return index_file
    return None

@router.get("/", include_in_schema=False)
def serve_frontend_index():
    index_file = get_frontend_index_file()
    if not index_file:
        raise HTTPException(status_code=404, detail="Frontend build artifact is missing")
    return FileResponse(index_file)


@router.get("/{full_path:path}", include_in_schema=False)
def serve_frontend_app(full_path: str):
    normalized_path = full_path.strip("/")
    if normalized_path == settings.api_prefix.strip("/") or normalized_path.startswith(f"{settings.api_prefix.strip('/')}/"):
        raise HTTPException(status_code=404, detail="Not Found")

    asset_path = resolve_frontend_asset(full_path)
    if asset_path:
        return FileResponse(asset_path)

    index_file = get_frontend_index_file()
    if not index_file:
        raise HTTPException(status_code=404, detail="Frontend build artifact is missing")
    return FileResponse(index_file)
