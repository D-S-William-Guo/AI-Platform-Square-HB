import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from sqlalchemy.orm import Session, joinedload

from .config import settings
from .database import Base, engine, get_db
from .models import App, Ranking, Submission, SubmissionImage
from .schemas import (
    AppDetail,
    ImageUploadResponse,
    RankingItem,
    Recommendation,
    RuleLink,
    Stats,
    SubmissionCreate,
    SubmissionOut,
)
from .seed import seed_data
from .venv_utils import venv_reader

APP_STATUS_VALUES = {"available", "approval", "beta", "offline"}
METRIC_TYPES = {"composite", "growth_rate", "likes"}
VALUE_DIMENSIONS = {"cost_reduction", "efficiency_gain", "perception_uplift", "revenue_growth"}
DATA_LEVEL_VALUES = {"L1", "L2", "L3", "L4"}

app = FastAPI(title=settings.app_name)

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


@app.get(f"{settings.api_prefix}/health")
def health_check():
    return {"status": "ok"}


@app.get(f"{settings.api_prefix}/venv/info")
def get_venv_info():
    """
    获取虚拟环境信息
    """
    return venv_reader.get_venv_info()


@app.get(f"{settings.api_prefix}/venv/python-path")
def get_venv_python_path():
    """
    获取虚拟环境中Python可执行文件的路径
    """
    python_path = venv_reader.get_venv_python_path()
    if python_path:
        return {"python_path": str(python_path)}
    return {"error": "Virtual environment not found or invalid"}


@app.get(f"{settings.api_prefix}/venv/site-packages")
def get_venv_site_packages():
    """
    获取虚拟环境中site-packages目录的路径
    """
    site_packages = venv_reader.get_venv_site_packages()
    if site_packages:
        return {"site_packages_path": str(site_packages)}
    return {"error": "Virtual environment not found or invalid"}


@app.get(f"{settings.api_prefix}/apps", response_model=list[AppDetail])
def list_apps(
    section: str | None = Query(default=None),
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
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
    if category and category != "全部":
        query = query.filter(App.category == category)
    if q:
        query = query.filter(App.name.contains(q) | App.description.contains(q))
    return query.order_by(App.id).all()


@app.get(f"{settings.api_prefix}/apps/{{app_id}}", response_model=AppDetail)
def get_app_detail(app_id: int, db: Session = Depends(get_db)):
    item = db.query(App).filter(App.id == app_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="App not found")
    return item


@app.get(f"{settings.api_prefix}/rankings", response_model=list[RankingItem])
def list_rankings(ranking_type: str = "excellent", db: Session = Depends(get_db)):
    return (
        db.query(Ranking)
        .options(joinedload(Ranking.app))
        .filter(Ranking.ranking_type == ranking_type)
        .order_by(Ranking.position)
        .all()
    )


@app.get(f"{settings.api_prefix}/recommendations", response_model=list[Recommendation])
def recommendations():
    return [
        Recommendation(title="智能客服助手", scene="7×24 小时自动应答"),
        Recommendation(title="AI会议助手", scene="自动生成会议纪要"),
        Recommendation(title="智能数据分析", scene="一键生成分析报告"),
    ]


@app.get(f"{settings.api_prefix}/stats", response_model=Stats)
def app_stats(db: Session = Depends(get_db)):
    pending = db.query(Submission).filter(Submission.status == "pending").count()
    approved_period = db.query(Submission).filter(Submission.status == "approved").count()
    total_apps = db.query(App).count()
    return Stats(pending=pending or 12, approved_period=approved_period or 7, total_apps=total_apps or 86)


@app.get(f"{settings.api_prefix}/rules", response_model=list[RuleLink])
def rules():
    base = settings.oa_rule_base_url.rstrip("/")
    return [
        RuleLink(title="如何申报应用", href=f"{base}/ai-app-square/rules/submission"),
        RuleLink(title="上榜评选标准", href=f"{base}/ai-app-square/rules/ranking"),
        RuleLink(title="API接入指南", href=f"{base}/ai-app-square/rules/api-integration"),
    ]


@app.post(f"{settings.api_prefix}/submissions", response_model=SubmissionOut)
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db)):
    if payload.effectiveness_type not in VALUE_DIMENSIONS:
        raise HTTPException(status_code=422, detail="Invalid effectiveness_type")
    if payload.data_level not in DATA_LEVEL_VALUES:
        raise HTTPException(status_code=422, detail="Invalid data_level")

    submission = Submission(**payload.model_dump())
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@app.get(f"{settings.api_prefix}/meta/enums")
def list_enums():
    return {
        "app_status": sorted(APP_STATUS_VALUES),
        "ranking_metric_type": sorted(METRIC_TYPES),
        "value_dimension": sorted(VALUE_DIMENSIONS),
        "data_level": sorted(DATA_LEVEL_VALUES),
    }


# Image upload configuration
UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def validate_image(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded image file"""
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"仅支持 {', '.join(ALLOWED_EXTENSIONS)} 格式的图片"
    
    # Check content type
    if not file.content_type.startswith("image/"):
        return False, "上传的文件不是有效的图片"
    
    return True, ""


def save_image(file: UploadFile, submission_id: int | None = None) -> dict:
    """Save image and create thumbnail"""
    # Generate unique filename
    ext = Path(file.filename).suffix.lower()
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{unique_id}{ext}"
    
    # Create directory structure
    if submission_id:
        save_dir = UPLOAD_DIR / "submissions" / str(submission_id)
    else:
        save_dir = UPLOAD_DIR / "temp"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Save original image
    file_path = save_dir / filename
    with open(file_path, "wb") as f:
        content = file.file.read()
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="图片大小不能超过 5MB")
        f.write(content)
    
    # Create thumbnail
    thumb_filename = f"thumb_{filename}"
    thumb_path = save_dir / thumb_filename
    
    with Image.open(file_path) as img:
        # Convert to RGB if necessary
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Create thumbnail (300x200)
        img.thumbnail((300, 200), Image.Resampling.LANCZOS)
        img.save(thumb_path, "JPEG", quality=85)
        
        # Get image dimensions
        width, height = img.size
    
    # Generate URLs
    base_url = "/static/uploads"
    if submission_id:
        image_url = f"{base_url}/submissions/{submission_id}/{filename}"
        thumbnail_url = f"{base_url}/submissions/{submission_id}/{thumb_filename}"
    else:
        image_url = f"{base_url}/temp/{filename}"
        thumbnail_url = f"{base_url}/temp/{thumb_filename}"
    
    return {
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "original_name": file.filename,
        "file_size": len(content),
        "width": width,
        "height": height,
    }


@app.post(f"{settings.api_prefix}/upload/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload image file"""
    # Validate file
    is_valid, error_msg = validate_image(file)
    if not is_valid:
        return ImageUploadResponse(
            success=False,
            image_url="",
            thumbnail_url="",
            original_name=file.filename,
            file_size=0,
            message=error_msg,
        )
    
    try:
        # Save image
        result = save_image(file)
        
        return ImageUploadResponse(
            success=True,
            image_url=result["image_url"],
            thumbnail_url=result["thumbnail_url"],
            original_name=result["original_name"],
            file_size=result["file_size"],
            message="图片上传成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        return ImageUploadResponse(
            success=False,
            image_url="",
            thumbnail_url="",
            original_name=file.filename,
            file_size=0,
            message=f"上传失败: {str(e)}",
        )


@app.post(f"{settings.api_prefix}/submissions/{{submission_id}}/images")
def associate_image(
    submission_id: int,
    image_url: str,
    thumbnail_url: str,
    original_name: str,
    file_size: int,
    is_cover: bool = False,
    db: Session = Depends(get_db),
):
    """Associate uploaded image with submission"""
    # Check if submission exists
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报记录不存在")
    
    # Create image record
    image = SubmissionImage(
        submission_id=submission_id,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        original_name=original_name,
        file_size=file_size,
        is_cover=is_cover,
    )
    db.add(image)
    
    # Update cover image if this is the cover
    if is_cover:
        submission.cover_image_id = image.id
    
    db.commit()
    db.refresh(image)
    
    return {
        "success": True,
        "image_id": image.id,
        "message": "图片关联成功",
    }


@app.get(f"{settings.api_prefix}/submissions/{{submission_id}}/images")
def get_submission_images(submission_id: int, db: Session = Depends(get_db)):
    """Get all images for a submission"""
    images = db.query(SubmissionImage).filter(
        SubmissionImage.submission_id == submission_id
    ).all()
    
    return [
        {
            "id": img.id,
            "image_url": img.image_url,
            "thumbnail_url": img.thumbnail_url,
            "original_name": img.original_name,
            "file_size": img.file_size,
            "is_cover": img.is_cover,
            "created_at": img.created_at,
        }
        for img in images
    ]


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
