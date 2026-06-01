"""Upload routes."""
import uuid as _uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from PIL import Image as PILImage
from sqlalchemy.orm import Session
from ..config import resolve_runtime_path, settings
from ..dependencies import enforce_rate_limit, require_submit_permission
from ..database import get_db
from ..models import Submission, SubmissionImage
from ..schemas import DocumentUploadResponse, ImageUploadResponse

router = APIRouter(prefix=settings.api_prefix)
STATIC_DIR = resolve_runtime_path(settings.static_dir)
UPLOAD_DIR = resolve_runtime_path(settings.upload_dir)
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_DOC_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_DOC_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md"}
ALLOWED_DOC_MIME_TYPES = {"application/pdf","application/msword","application/vnd.openxmlformats-officedocument.wordprocessingml.document","text/plain","text/markdown","text/x-markdown"}

def _validate_image(file):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"仅支持 {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))} 格式的图片"
    if (file.content_type or "").lower() not in ALLOWED_IMAGE_MIME_TYPES:
        return False, "上传的文件不是有效的图片"
    return True, ""

def _validate_document(file):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_DOC_EXTENSIONS:
        return False, f"仅支持 {', '.join(sorted(ALLOWED_DOC_EXTENSIONS))} 格式的文档"
    ct = (file.content_type or "").lower()
    if ct and ct not in ALLOWED_DOC_MIME_TYPES:
        return False, "上传的文件类型不受支持"
    return True, ""

def _save_image(file, submission_id=None, context="submission"):
    ext = Path(file.filename).suffix.lower()
    uid = str(_uuid.uuid4())[:8]
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
        raise HTTPException(status_code=413, detail="图片大小不能超过 5MB")
    with open(fp, "wb") as f: f.write(content)
    tp = sd / f"thumb_{fn}"
    with PILImage.open(fp) as img:
        if img.mode in ("RGBA","P"): img = img.convert("RGB")
        img.thumbnail((300,200), PILImage.Resampling.LANCZOS)
        img.save(tp, "JPEG", quality=85)
    bu = f"static/uploads"
    return {"image_url":f"{bu}/{up}/{fn}","thumbnail_url":f"{bu}/{up}/thumb_{fn}","original_name":file.filename,"file_size":len(content),"width":img.width if hasattr(img,'width') else 0,"height":img.height if hasattr(img,'height') else 0}

def _save_document(file):
    ext = Path(file.filename).suffix.lower()
    uid = str(_uuid.uuid4())[:8]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"{ts}_{uid}{ext}"
    sd = UPLOAD_DIR / "docs"; sd.mkdir(parents=True, exist_ok=True)
    fp = sd / fn
    content = file.file.read()
    if len(content) > MAX_DOC_FILE_SIZE:
        raise HTTPException(status_code=413, detail="文档大小不能超过 20MB")
    with open(fp, "wb") as f: f.write(content)
    return {"file_url":f"static/uploads/docs/{fn}","original_name":file.filename,"file_size":len(content),"mime_type":file.content_type or ""}

@router.post("/upload/image", response_model=ImageUploadResponse)
async def upload_image(request: Request, file: UploadFile = File(...), context: str = Form(default="submission"), _=Depends(require_submit_permission)):
    enforce_rate_limit(request, bucket="upload_image", limit=20, window_seconds=300)
    if context not in {"submission","group_app"}:
        return ImageUploadResponse(success=False, image_url="", thumbnail_url="", original_name=file.filename, file_size=0, message="无效的上传场景")
    ok, msg = _validate_image(file)
    if not ok: return ImageUploadResponse(success=False, image_url="", thumbnail_url="", original_name=file.filename, file_size=0, message=msg)
    try:
        r = _save_image(file, context=context)
        return ImageUploadResponse(success=True, **{k:r[k] for k in ("image_url","thumbnail_url","original_name","file_size") if k in r}, message="图片上传成功")
    except HTTPException: raise
    except Exception as e:
        return ImageUploadResponse(success=False, image_url="", thumbnail_url="", original_name=file.filename, file_size=0, message=f"上传失败: {e}")

@router.post("/upload/document", response_model=DocumentUploadResponse)
async def upload_document(request: Request, file: UploadFile = File(...), _=Depends(require_submit_permission)):
    enforce_rate_limit(request, bucket="upload_document", limit=20, window_seconds=300)
    ok, msg = _validate_document(file)
    if not ok: return DocumentUploadResponse(success=False, file_url="", original_name=file.filename, file_size=0, message=msg)
    try:
        r = _save_document(file)
        return DocumentUploadResponse(success=True, file_url=r["file_url"], original_name=r["original_name"], file_size=r["file_size"], message="文档上传成功")
    except HTTPException: raise
    except Exception as e:
        return DocumentUploadResponse(success=False, file_url="", original_name=file.filename, file_size=0, message=f"上传失败: {e}")

@router.post("/submissions/{submission_id}/images")
def associate_image(submission_id: int, image_url: str, thumbnail_url: str, original_name: str, file_size: int, mime_type: str = "", is_cover: bool = False, _=Depends(require_submit_permission), db: Session = Depends(get_db)):
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s: raise HTTPException(status_code=404, detail="申报记录不存在")
    img = SubmissionImage(submission_id=submission_id, image_url=image_url, thumbnail_url=thumbnail_url, original_name=original_name, file_size=file_size, mime_type=mime_type, is_cover=is_cover)
    db.add(img)
    if is_cover: s.cover_image_id = img.id
    db.commit(); db.refresh(img)
    return {"success":True,"image_id":img.id,"message":"图片关联成功"}

@router.get("/submissions/{submission_id}/images")
def get_submission_images(submission_id: int, db: Session = Depends(get_db)):
    return [{"id":i.id,"image_url":i.image_url,"thumbnail_url":i.thumbnail_url,"original_name":i.original_name,"file_size":i.file_size,"mime_type":i.mime_type,"is_cover":i.is_cover,"created_at":i.created_at} for i in db.query(SubmissionImage).filter(SubmissionImage.submission_id == submission_id).all()]
