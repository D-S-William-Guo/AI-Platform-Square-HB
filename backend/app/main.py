"""AI Platform Square — FastAPI application entry point.

Routes are organized into domain-specific router modules under `.routers`.
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import (
    get_allowed_hosts,
    get_allowed_origins,
    is_api_docs_enabled,
    resolve_runtime_path,
    settings,
)
from .database import ensure_database_schema_ready

# ── Router imports ──────────────────────────────────────────────────────────
from .routers.auth import router as auth_router
from .routers.meta import router as meta_router
from .routers.apps import router as apps_router
from .routers.rankings import router as rankings_router
from .routers.submissions import router as submissions_router
from .routers.ranking_configs import router as ranking_configs_router
from .routers.ranking_settings import router as ranking_settings_router
from .routers.admin_users import router as admin_users_router
from .routers.admin_review import router as admin_review_router
from .routers.upload import router as upload_router
from .routers.audit import router as audit_router
from .routers.integration import router as integration_router
from .routers.frontend import router as frontend_router

logger = logging.getLogger(__name__)

# ── Paths & constants ───────────────────────────────────────────────────────
STATIC_DIR = resolve_runtime_path(settings.static_dir)
UPLOAD_DIR = resolve_runtime_path(settings.upload_dir)
IMAGE_DIR = resolve_runtime_path(settings.image_dir)
# FRONTEND_DIST_DIR now lives in routers/frontend.py (_frontend_dist_dir)

# ── Upload helpers (shared with upload router) ──────────────────────────────
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_DOC_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md"}
ALLOWED_DOC_MIME_TYPES = {
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain", "text/markdown", "text/x-markdown",
}
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_DOC_FILE_SIZE = 20 * 1024 * 1024


def validate_image(file) -> tuple[bool, str]:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"仅支持 {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))} 格式的图片"
    if (file.content_type or "").lower() not in ALLOWED_IMAGE_MIME_TYPES:
        return False, "上传的文件不是有效的图片"
    return True, ""


def validate_document(file) -> tuple[bool, str]:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_DOC_EXTENSIONS:
        return False, f"仅支持 {', '.join(sorted(ALLOWED_DOC_EXTENSIONS))} 格式的文档"
    ct = (file.content_type or "").lower()
    if ct and ct not in ALLOWED_DOC_MIME_TYPES:
        return False, "上传的文件类型不受支持"
    return True, ""


def save_image(file, submission_id=None, context="submission") -> dict:
    ext = Path(file.filename).suffix.lower()
    uid = str(uuid.uuid4())[:8]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"{ts}_{uid}{ext}"
    if submission_id:
        sd = UPLOAD_DIR / "submissions" / str(submission_id)
        up = f"submissions/{submission_id}"
    elif context == "group_app":
        sd = UPLOAD_DIR / "group-apps" / "temp"
        up = "group-apps/temp"
    else:
        sd = UPLOAD_DIR / "submissions" / "temp"
        up = "submissions/temp"
    sd.mkdir(parents=True, exist_ok=True)
    fp = sd / fn
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail="图片大小不能超过 5MB")
    with open(fp, "wb") as f:
        f.write(content)
    tp = sd / f"thumb_{fn}"
    with Image.open(fp) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((300, 200), Image.Resampling.LANCZOS)
        img.save(tp, "JPEG", quality=85)
    bu = f"{settings.api_prefix}/static/uploads"
    return {"image_url": f"{bu}/{up}/{fn}", "thumbnail_url": f"{bu}/{up}/thumb_{fn}",
            "original_name": file.filename, "file_size": len(content),
            "width": img.width, "height": img.height}


def save_document(file) -> dict:
    ext = Path(file.filename).suffix.lower()
    uid = str(uuid.uuid4())[:8]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"{ts}_{uid}{ext}"
    sd = UPLOAD_DIR / "docs"
    sd.mkdir(parents=True, exist_ok=True)
    fp = sd / fn
    content = file.file.read()
    if len(content) > MAX_DOC_FILE_SIZE:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail="文档大小不能超过 20MB")
    with open(fp, "wb") as f:
        f.write(content)
    return {"file_url": f"{settings.api_prefix}/static/uploads/docs/{fn}",
            "original_name": file.filename, "file_size": len(content),
            "mime_type": file.content_type or ""}


# ── Frontend helpers (delegated to router) ──────────────────────────────────
from .routers.frontend import (  # noqa: E402
    resolve_frontend_asset,
    get_frontend_index_file,
)


def validate_static_upload_path_consistency(static_dir: Path, upload_dir: Path) -> None:
    expected_upload_dir = (static_dir / "uploads").resolve()
    resolved_upload_dir = upload_dir.resolve()
    if resolved_upload_dir != expected_upload_dir:
        raise RuntimeError(
            f"Invalid runtime path config: UPLOAD_DIR must resolve to STATIC_DIR/uploads. "
            f"Got STATIC_DIR={static_dir}, UPLOAD_DIR={upload_dir}, expected={expected_upload_dir}."
        )


def ensure_runtime_directories() -> None:
    validate_static_upload_path_consistency(STATIC_DIR, UPLOAD_DIR)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


# ── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_runtime_directories()
    ensure_database_schema_ready()
    yield


# ── App creation ────────────────────────────────────────────────────────────
docs_enabled = is_api_docs_enabled(settings)
app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url=f"{settings.api_prefix}/openapi.json" if docs_enabled else None,
)

allowed_hosts = get_allowed_hosts(settings)
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

allowed_origins = get_allowed_origins(settings)
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ── Static mounts ───────────────────────────────────────────────────────────
ensure_runtime_directories()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount(f"{settings.api_prefix}/static", StaticFiles(directory=str(STATIC_DIR)), name="api-static")

# ── Router registration ─────────────────────────────────────────────────────
app.include_router(meta_router)
app.include_router(auth_router)
app.include_router(apps_router)
app.include_router(rankings_router)
app.include_router(submissions_router)
app.include_router(upload_router)
app.include_router(audit_router)
app.include_router(admin_users_router)
app.include_router(admin_review_router)
app.include_router(integration_router)
app.include_router(ranking_configs_router)
app.include_router(ranking_settings_router)
app.include_router(frontend_router)

# ── Compatibility re-exports (used by tests) ────────────────────────────────
from .identity import get_identity_provider  # noqa: E402, F401
identity_provider = get_identity_provider(settings)  # noqa: E402
from .services.ranking_service import (  # noqa: E402, F401
    calculate_app_score,
    calculate_dimension_score,
    calculate_three_layer_score,
    sync_rankings_service,
)
from .dependencies import (  # noqa: E402, F401
    clear_rate_limit_state,
    paginate_query,
    require_admin_token,
    require_auth_session,
    structured_error_detail,
)
# Re-export test-referenced route functions (tests import from app.main)
from .routers.rankings import (  # noqa: E402, F401
    list_historical_rankings,
    resolve_latest_run_id,
)
from .routers.frontend import (  # noqa: E402, F401
    serve_frontend_app,
    serve_frontend_index,
)
