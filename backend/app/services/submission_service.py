"""申报业务服务——申报校验、去重、字段构建与变更申请。

从 main.py 提取，可脱离 HTTP 层独立测试。
"""

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import get_app_category_options, settings
from ..dependencies import structured_error_detail
from ..models import App, AppChangeRequest, Submission


APP_CATEGORY_OPTIONS = get_app_category_options(settings)
APP_CATEGORY_VALUES = set(APP_CATEGORY_OPTIONS)
APP_DIFFICULTY_VALUES = {"Low", "Medium", "High"}
VALUE_DIMENSIONS = {"cost_reduction", "efficiency_gain", "perception_uplift", "revenue_growth"}
DATA_LEVEL_VALUES = {"L1", "L2", "L3", "L4"}


# ---------------------------------------------------------------------------
# 文本标准化
# ---------------------------------------------------------------------------

def normalize_dedupe_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


# ---------------------------------------------------------------------------
# 申报负载校验
# ---------------------------------------------------------------------------

def validate_submission_payload(payload) -> None:
    """校验 SubmissionCreate schema 的枚举字段。"""
    if payload.effectiveness_type not in VALUE_DIMENSIONS:
        raise HTTPException(status_code=422, detail="Invalid effectiveness_type")
    if payload.data_level not in DATA_LEVEL_VALUES:
        raise HTTPException(status_code=422, detail="Invalid data_level")
    if payload.category not in APP_CATEGORY_VALUES:
        raise HTTPException(status_code=422, detail="Invalid category")
    if payload.difficulty not in APP_DIFFICULTY_VALUES:
        raise HTTPException(status_code=422, detail="Invalid difficulty")


def validate_review_reason(reason: str | None) -> str:
    normalized_reason = (reason or "").strip()
    if len(normalized_reason) < 2:
        raise HTTPException(
            status_code=422,
            detail=structured_error_detail(
                code="validation_error",
                message="拒绝原因至少 2 个字符",
                field_errors=[{"field": "reason", "message": "拒绝原因不能为空"}],
            ),
        )
    if len(normalized_reason) > 255:
        raise HTTPException(
            status_code=422,
            detail=structured_error_detail(
                code="validation_error",
                message="拒绝原因长度超限",
                field_errors=[{"field": "reason", "message": "拒绝原因最多 255 个字符"}],
            ),
        )
    return normalized_reason


def validate_group_app_payload(payload) -> None:
    """校验 GroupAppCreate 的枚举字段。"""
    APP_STATUS_VALUES = {"available", "approval", "beta", "offline"}
    if payload.category not in APP_CATEGORY_VALUES:
        raise HTTPException(status_code=422, detail="Invalid category")
    if payload.status not in APP_STATUS_VALUES:
        raise HTTPException(status_code=422, detail="Invalid status")
    if payload.difficulty not in APP_DIFFICULTY_VALUES:
        raise HTTPException(status_code=422, detail="Invalid difficulty")
    if payload.access_mode not in {"direct", "profile"}:
        raise HTTPException(status_code=422, detail="Invalid access_mode")
    if payload.effectiveness_type not in VALUE_DIMENSIONS:
        raise HTTPException(status_code=422, detail="Invalid effectiveness_type")


# ---------------------------------------------------------------------------
# 字段构建与去重
# ---------------------------------------------------------------------------

def build_submission_update_fields(
    payload,
    *,
    company: str,
    department: str,
) -> dict:
    validate_submission_payload(payload)
    update_fields = payload.model_dump()
    update_fields["company"] = company
    update_fields["department"] = department
    update_fields["unit_name"] = company
    update_fields["ranking_enabled"] = False
    update_fields["ranking_weight"] = 1.0
    update_fields["ranking_tags"] = ""
    update_fields["ranking_dimensions"] = ""
    return update_fields


def ensure_no_duplicate_active_submission(
    db: Session,
    *,
    app_name: str,
    unit_name: str,
    exclude_submission_id: int | None = None,
) -> None:
    query = db.query(Submission).filter(
        func.lower(func.trim(Submission.app_name)) == normalize_dedupe_text(app_name),
        func.lower(func.trim(Submission.unit_name)) == normalize_dedupe_text(unit_name),
        Submission.status.in_(("pending", "approved")),
    )
    if exclude_submission_id is not None:
        query = query.filter(Submission.id != exclude_submission_id)
    if query.first():
        raise HTTPException(status_code=409, detail="该应用已存在待审核或已通过的申报记录，请勿重复提交")


def ensure_no_duplicate_province_app(
    db: Session,
    *,
    app_name: str,
    unit_name: str,
    exclude_app_id: int | None = None,
) -> None:
    query = db.query(App).filter(
        App.section == "province",
        func.lower(func.trim(App.name)) == normalize_dedupe_text(app_name),
        func.lower(func.trim(App.org)) == normalize_dedupe_text(unit_name),
    )
    if exclude_app_id is not None:
        query = query.filter(App.id != exclude_app_id)
    if query.first():
        raise HTTPException(status_code=409, detail="已存在同名同单位省内应用，不能重复创建")


# ---------------------------------------------------------------------------
# 字段应用
# ---------------------------------------------------------------------------

def apply_submission_fields(target: Submission | AppChangeRequest, fields: dict) -> None:
    for key, value in fields.items():
        if hasattr(target, key):
            setattr(target, key, value)


def apply_change_request_to_app(app: App, change_request: AppChangeRequest) -> None:
    app.name = change_request.app_name
    app.org = change_request.unit_name
    app.company = change_request.company or change_request.unit_name
    app.department = change_request.department or ""
    app.category = change_request.category
    app.description = change_request.scenario
    app.monthly_calls = change_request.monthly_calls or 0.0
    app.difficulty = change_request.difficulty or "Medium"
    app.contact_name = change_request.contact
    app.detail_doc_url = change_request.detail_doc_url or ""
    app.detail_doc_name = change_request.detail_doc_name or ""
    app.target_system = change_request.embedded_system
    app.problem_statement = change_request.problem_statement
    app.effectiveness_type = change_request.effectiveness_type
    app.effectiveness_metric = change_request.effectiveness_metric
    app.cover_image_url = change_request.cover_image_url or ""
