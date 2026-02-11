import os
import uuid
from datetime import date, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from sqlalchemy.orm import Session, joinedload

from .config import settings
from .database import Base, engine, get_db
from .models import App, Ranking, Submission, SubmissionImage, RankingDimension, RankingLog, AppDimensionScore, HistoricalRanking
from .schemas import (
    AppDetail,
    ImageUploadResponse,
    RankingItem,
    Recommendation,
    RuleLink,
    Stats,
    SubmissionCreate,
    SubmissionOut,
    RankingDimensionCreate,
    RankingDimensionUpdate,
    RankingDimensionOut,
    RankingLogOut,
    AppDimensionScoreOut,
    HistoricalRankingOut,
    GroupAppCreate,
)
from .seed import seed_data
from .venv_utils import venv_reader
from .validators import validate_submission_payload, validate_app_status
from .services import calculate_app_score, calculate_dimension_score, sync_rankings_service
from .middleware import setup_error_handlers

app = FastAPI(
    title=settings.app_name,
    description="AI应用广场API - 提供应用管理、排行榜、申报审核等功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 设置错误处理
setup_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_data(db)
    finally:
        db.close()


@app.get(f"{settings.api_prefix}/health", tags=["系统"])
def health_check():
    """健康检查接口"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get(f"{settings.api_prefix}/venv/info", tags=["虚拟环境"])
def get_venv_info():
    """获取虚拟环境信息"""
    return venv_reader.get_venv_info()


@app.get(f"{settings.api_prefix}/venv/python-path", tags=["虚拟环境"])
def get_venv_python_path():
    """获取虚拟环境中Python可执行文件的路径"""
    python_path = venv_reader.get_venv_python_path()
    if python_path:
        return {"python_path": str(python_path)}
    return {"error": "Virtual environment not found or invalid"}


@app.get(f"{settings.api_prefix}/venv/site-packages", tags=["虚拟环境"])
def get_venv_site_packages():
    """获取虚拟环境中site-packages目录的路径"""
    site_packages = venv_reader.get_venv_site_packages()
    if site_packages:
        return {"site_packages_path": str(site_packages)}
    return {"error": "Virtual environment not found or invalid"}


@app.get(f"{settings.api_prefix}/apps", response_model=list[AppDetail], tags=["应用"])
def list_apps(
    section: str | None = Query(default=None, description="筛选区域：group-集团, province-省内"),
    status: str | None = Query(default=None, description="筛选状态"),
    category: str | None = Query(default=None, description="筛选分类"),
    q: str | None = Query(default=None, description="搜索关键词"),
    db: Session = Depends(get_db),
):
    """获取应用列表"""
    query = db.query(App)
    if section:
        query = query.filter(App.section == section)
    if status:
        validate_app_status(status)
        query = query.filter(App.status == status)
    if category and category != "全部":
        query = query.filter(App.category == category)
    if q:
        query = query.filter(App.name.contains(q) | App.description.contains(q))
    
    apps = query.order_by(App.id).all()
    return apps
