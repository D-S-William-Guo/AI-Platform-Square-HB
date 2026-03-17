import logging
import os
import uuid
import json
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Body, Cookie, Depends, FastAPI, File, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from sqlalchemy import func, inspect, or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from .auth_utils import generate_session_token, hash_password, verify_password
from .config import resolve_runtime_path, settings
from .database import Base, engine, get_db
from .models import (
    ActionLog,
    App,
    AppDimensionScore,
    AppRankingSetting,
    AuthSession,
    HistoricalRanking,
    Ranking,
    RankingAuditLog,
    RankingConfig,
    RankingDimension,
    RankingLog,
    Submission,
    SubmissionImage,
    User,
)
from .schemas import (
    ActionLogOut,
    AppDetail,
    AuthLoginRequest,
    AuthLoginResponse,
    AuthMeResponse,
    ImageUploadResponse,
    DocumentUploadResponse,
    RankingItem,
    Recommendation,
    RuleLink,
    Stats,
    SubmissionCreate,
    SubmissionOut,
    SubmissionManageTokenPayload,
    SubmissionSelfUpdate,
    SubmissionApprovePayload,
    RankingDimensionCreate,
    RankingDimensionUpdate,
    RankingDimensionOut,
    RankingLogOut,
    RankingAuditLogOut,
    AppDimensionScoreOut,
    DimensionScoreUpdate,
    HistoricalRankingOut,
    GroupAppCreate,
    RankingConfigCreate,
    RankingConfigUpdate,
    RankingConfigOut,
    AppRankingSettingCreate,
    AppRankingSettingSaveRequest,
    AppRankingSettingSaveResponse,
    AppRankingSettingUpdate,
    AppRankingSettingOut,
    DimensionConfigItem,
    RankingConfigWithDimensions,
    UserPublic,
    UserImportRequest,
    UserImportResponse,
    UserRoleUpdatePayload,
    UserStatusUpdatePayload,
)
from .seed import seed_data
from .venv_utils import venv_reader

APP_STATUS_VALUES = {"available", "approval", "beta", "offline"}
METRIC_TYPES = {"composite", "growth_rate", "likes"}
VALUE_DIMENSIONS = {"cost_reduction", "efficiency_gain", "perception_uplift", "revenue_growth"}
DATA_LEVEL_VALUES = {"L1", "L2", "L3", "L4"}
DEFAULT_RANKING_TAG = "推荐"
STATIC_DIR = resolve_runtime_path(settings.static_dir)
UPLOAD_DIR = resolve_runtime_path(settings.upload_dir)
IMAGE_DIR = resolve_runtime_path(settings.image_dir)


logger = logging.getLogger(__name__)


def validate_static_upload_path_consistency(static_dir: Path, upload_dir: Path) -> None:
    """校验上传目录与 /static 挂载目录一致，避免返回的 /static/uploads/... 出现 404。"""
    expected_upload_dir = (static_dir / "uploads").resolve()
    resolved_upload_dir = upload_dir.resolve()
    if resolved_upload_dir != expected_upload_dir:
        raise RuntimeError(
            "Invalid runtime path config: UPLOAD_DIR must resolve to STATIC_DIR/uploads "
            f"to match '/static/uploads/...'. Got STATIC_DIR={static_dir}, "
            f"UPLOAD_DIR={upload_dir}, expected={expected_upload_dir}."
        )


def ensure_runtime_directories() -> None:
    validate_static_upload_path_consistency(STATIC_DIR, UPLOAD_DIR)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def ensure_additive_schema_columns() -> None:
    """为历史数据库补齐增量字段，避免版本升级后因缺列导致 500。"""
    expected_columns = {
        "apps": {
            "detail_doc_url": {
                "mysql": "VARCHAR(500) DEFAULT ''",
                "sqlite": "TEXT DEFAULT ''",
            },
            "detail_doc_name": {
                "mysql": "VARCHAR(255) DEFAULT ''",
                "sqlite": "TEXT DEFAULT ''",
            },
            "created_by_user_id": {
                "mysql": "INT NULL",
                "sqlite": "INTEGER",
            },
            "created_from_submission_id": {
                "mysql": "INT NULL",
                "sqlite": "INTEGER",
            },
            "approved_by_user_id": {
                "mysql": "INT NULL",
                "sqlite": "INTEGER",
            },
            "approved_at": {
                "mysql": "DATETIME NULL",
                "sqlite": "DATETIME",
            },
        },
        "submissions": {
            "manage_token": {
                "mysql": "VARCHAR(64) DEFAULT ''",
                "sqlite": "TEXT DEFAULT ''",
            },
            "detail_doc_url": {
                "mysql": "VARCHAR(500) DEFAULT ''",
                "sqlite": "TEXT DEFAULT ''",
            },
            "detail_doc_name": {
                "mysql": "VARCHAR(255) DEFAULT ''",
                "sqlite": "TEXT DEFAULT ''",
            },
            "submitter_user_id": {
                "mysql": "INT NULL",
                "sqlite": "INTEGER",
            },
            "approved_by_user_id": {
                "mysql": "INT NULL",
                "sqlite": "INTEGER",
            },
            "approved_at": {
                "mysql": "DATETIME NULL",
                "sqlite": "DATETIME",
            },
            "rejected_by_user_id": {
                "mysql": "INT NULL",
                "sqlite": "INTEGER",
            },
            "rejected_at": {
                "mysql": "DATETIME NULL",
                "sqlite": "DATETIME",
            },
            "rejected_reason": {
                "mysql": "VARCHAR(255) DEFAULT ''",
                "sqlite": "TEXT DEFAULT ''",
            },
            "updated_at": {
                "mysql": "DATETIME NULL",
                "sqlite": "DATETIME",
            },
        },
        "app_dimension_scores": {
            "ranking_config_id": {
                "mysql": "VARCHAR(50) NULL",
                "sqlite": "TEXT",
            },
        },
    }
    with engine.begin() as conn:
        inspector = inspect(conn)
        for table_name, columns in expected_columns.items():
            existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
            for col_name, defs in columns.items():
                if col_name in existing_cols:
                    continue
                if conn.dialect.name == "sqlite":
                    sqlite_def = defs["sqlite"]
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {sqlite_def}"))
                else:
                    col_def = defs["mysql"]
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}"))

        existing_indexes = {idx["name"] for idx in inspector.get_indexes("app_dimension_scores")}
        if "uq_app_dim_scores_app_config_dim_period" not in existing_indexes:
            if conn.dialect.name == "sqlite":
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uq_app_dim_scores_app_config_dim_period "
                        "ON app_dimension_scores (app_id, ranking_config_id, dimension_id, period_date)"
                    )
                )
            else:
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX uq_app_dim_scores_app_config_dim_period "
                        "ON app_dimension_scores (app_id, ranking_config_id, dimension_id, period_date)"
                    )
                )


def ensure_submission_manage_tokens() -> None:
    """回填历史 submissions.manage_token，确保自助管理接口可用。"""
    db = Session(bind=engine)
    try:
        rows = (
            db.query(Submission)
            .filter(or_(Submission.manage_token.is_(None), Submission.manage_token == ""))
            .all()
        )
        if not rows:
            return
        for row in rows:
            row.manage_token = uuid.uuid4().hex
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def normalize_dedupe_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def resolve_ranking_scope_id(ranking_type: str | None = None, ranking_config_id: str | None = None) -> str:
    """收敛榜单标识：统一使用 ranking_config_id，ranking_type 仅作兼容入参。"""
    return (ranking_config_id or ranking_type or "").strip() or "excellent"


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_runtime_directories()
    Base.metadata.create_all(bind=engine)
    ensure_additive_schema_columns()
    ensure_submission_manage_tokens()
    db = next(get_db())
    try:
        seed_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_submission_payload(payload: SubmissionCreate) -> None:
    if payload.effectiveness_type not in VALUE_DIMENSIONS:
        raise HTTPException(status_code=422, detail="Invalid effectiveness_type")
    if payload.data_level not in DATA_LEVEL_VALUES:
        raise HTTPException(status_code=422, detail="Invalid data_level")


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    return authorization[7:].strip() or None


def load_active_session(db: Session, token: str | None) -> AuthSession | None:
    if not token:
        return None
    session = (
        db.query(AuthSession)
        .options(joinedload(AuthSession.user))
        .filter(AuthSession.token_jti == token)
        .first()
    )
    if not session:
        return None
    if session.revoked_at is not None:
        return None
    if session.expires_at <= datetime.utcnow():
        return None
    if not session.user or not session.user.is_active:
        return None
    return session


def to_public_user(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        chinese_name=user.chinese_name,
        role=user.role,
        phone=user.phone or "",
        email=user.email or "",
        department=user.department or "",
        is_active=bool(user.is_active),
    )


def write_action_log(
    db: Session,
    *,
    action: str,
    actor_user: User | None = None,
    resource_type: str = "",
    resource_id: str = "",
    request_id: str = "",
    payload_summary: str = "",
) -> None:
    db.add(
        ActionLog(
            actor_user_id=actor_user.id if actor_user else None,
            actor_role=(actor_user.role if actor_user else ""),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            payload_summary=payload_summary,
        )
    )


def upsert_users(
    db: Session,
    *,
    payload: UserImportRequest,
) -> UserImportResponse:
    normalized_inputs: dict[str, dict] = {}
    for item in payload.users:
        username = item.username.strip()
        if not username:
            continue
        normalized_inputs[username.lower()] = {
            "username": username,
            "chinese_name": item.chinese_name.strip(),
            "phone": item.phone.strip(),
            "email": item.email.strip(),
            "department": item.department.strip(),
            "is_active": item.is_active,
        }

    if not normalized_inputs:
        raise HTTPException(status_code=422, detail="导入用户列表为空")

    existing_rows = (
        db.query(User)
        .filter(func.lower(User.username).in_(list(normalized_inputs.keys())))
        .all()
    )
    existing_map = {row.username.lower(): row for row in existing_rows}

    created = 0
    updated = 0
    unchanged = 0

    for key, item in normalized_inputs.items():
        user = existing_map.get(key)
        if not user:
            db.add(
                User(
                    username=item["username"],
                    chinese_name=item["chinese_name"] or item["username"],
                    role="user",
                    phone=item["phone"],
                    email=item["email"],
                    department=item["department"],
                    is_active=item["is_active"],
                    password_hash=hash_password(settings.user_default_password),
                )
            )
            created += 1
            continue

        changed = False
        if user.chinese_name != item["chinese_name"]:
            user.chinese_name = item["chinese_name"]
            changed = True
        if (user.phone or "") != item["phone"]:
            user.phone = item["phone"]
            changed = True
        if (user.email or "") != item["email"]:
            user.email = item["email"]
            changed = True
        if (user.department or "") != item["department"]:
            user.department = item["department"]
            changed = True
        if bool(user.is_active) != bool(item["is_active"]):
            user.is_active = item["is_active"]
            changed = True
            if not item["is_active"]:
                db.query(AuthSession).filter(
                    AuthSession.user_id == user.id,
                    AuthSession.revoked_at.is_(None),
                ).update(
                    {AuthSession.revoked_at: datetime.utcnow()},
                    synchronize_session=False,
                )

        if changed:
            updated += 1
        else:
            unchanged += 1

    db.flush()
    return UserImportResponse(
        created=created,
        updated=updated,
        unchanged=unchanged,
        source=payload.source,
    )


def require_user_sync_token(
    x_user_sync_token: str | None = Header(default=None, alias="X-User-Sync-Token"),
) -> None:
    configured = settings.user_sync_token.strip()
    if not configured:
        raise HTTPException(status_code=503, detail="USER_SYNC_TOKEN 未配置，外部用户同步接口已禁用")
    if not x_user_sync_token:
        raise HTTPException(status_code=401, detail="缺少用户同步令牌")
    if x_user_sync_token != configured:
        raise HTTPException(status_code=403, detail="用户同步令牌无效")


def require_auth_session(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    auth_cookie_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
) -> AuthSession:
    token = extract_bearer_token(authorization) or auth_cookie_token
    if not token or token == settings.admin_token:
        raise HTTPException(status_code=401, detail="请先登录")
    session = load_active_session(db, token)
    if not session:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return session


def get_optional_auth_session(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    auth_cookie_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
) -> AuthSession | None:
    token = extract_bearer_token(authorization) or auth_cookie_token
    if not token or token == settings.admin_token:
        return None
    session = load_active_session(db, token)
    if not session:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return session


def require_admin_token(
    db: Session = Depends(get_db),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(default=None),
    auth_cookie_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
) -> User | None:
    bearer_token = extract_bearer_token(authorization)
    has_any_credential = bool(x_admin_token or bearer_token or auth_cookie_token)

    if x_admin_token:
        if x_admin_token != settings.admin_token:
            raise HTTPException(status_code=403, detail="无权限访问")
        return None

    if bearer_token == settings.admin_token:
        return None

    for candidate in (bearer_token, auth_cookie_token):
        if not candidate or candidate == settings.admin_token:
            continue
        session = load_active_session(db, candidate)
        if session:
            if session.user.role != "admin":
                raise HTTPException(status_code=403, detail="无权限访问")
            return session.user

    if has_any_credential:
        raise HTTPException(status_code=403, detail="无权限访问")
    raise HTTPException(status_code=401, detail="缺少管理员令牌")

def write_ranking_audit_log(
    db: Session,
    *,
    action: str,
    ranking_type: str | None = None,
    ranking_config_id: str | None = None,
    period_date: date | None = None,
    run_id: str | None = None,
    actor: str = "system",
    payload_summary: str = "",
    ) -> None:
    db.add(
        RankingAuditLog(
            action=action,
            ranking_type=ranking_type,
            ranking_config_id=ranking_config_id,
            period_date=period_date,
            run_id=run_id,
            actor=actor,
            payload_summary=payload_summary,
        )
    )


def structured_error_detail(
    *,
    code: str,
    message: str,
    field_errors: list[dict[str, str]] | None = None,
) -> dict:
    return {
        "code": code,
        "message": message,
        "field_errors": field_errors or [],
    }


def load_single_dimension_score(
    db: Session,
    *,
    app_id: int,
    ranking_config_id: str | None,
    dimension_id: int,
    period_date: date,
) -> AppDimensionScore | None:
    """读取同日维度分值并清理重复脏数据，仅保留最新一条。"""
    records = (
        db.query(AppDimensionScore)
        .filter(
            AppDimensionScore.app_id == app_id,
            AppDimensionScore.ranking_config_id == ranking_config_id,
            AppDimensionScore.dimension_id == dimension_id,
            AppDimensionScore.period_date == period_date,
        )
        .order_by(AppDimensionScore.updated_at.desc(), AppDimensionScore.id.desc())
        .all()
    )
    if not records:
        return None
    primary = records[0]
    for stale in records[1:]:
        db.delete(stale)
    return primary

def validate_submission_ranking_fields(
    ranking_weight: float,
    ranking_tags: str,
    ranking_dimensions: str,
) -> None:
    if ranking_weight < 0.1 or ranking_weight > 10.0:
        raise HTTPException(status_code=422, detail="ranking_weight must be between 0.1 and 10.0")
    if len(ranking_tags) > 255:
        raise HTTPException(status_code=422, detail="ranking_tags must not exceed 255 characters")
    if len(ranking_dimensions) > 500:
        raise HTTPException(status_code=422, detail="ranking_dimensions must not exceed 500 characters")


def calculate_app_score(app: App, dimensions: list[RankingDimension]) -> int:
    """Deprecated: 保留旧版评分逻辑仅用于审计/回顾，不作为当前榜单权威计算路径。"""
    logger.warning("Deprecated ranking path used: calculate_app_score(). Use sync_rankings_service() as source of truth.")
    if not dimensions:
        return max(0, min(int(app.monthly_calls * 10), 1000))

    base_score = 0.0
    for dimension in dimensions:
        dimension_score = 0
        if dimension.name == "用户满意度":
            dimension_score = min(int(app.monthly_calls * 10), 100)
        elif dimension.name == "业务价值":
            if app.effectiveness_type == "revenue_growth":
                dimension_score = 100
            elif app.effectiveness_type == "efficiency_gain":
                dimension_score = 80
            elif app.effectiveness_type == "cost_reduction":
                dimension_score = 70
            else:
                dimension_score = 60
        elif dimension.name == "技术创新性":
            if app.difficulty == "High":
                dimension_score = 100
            elif app.difficulty == "Medium":
                dimension_score = 70
            else:
                dimension_score = 40
        elif dimension.name == "使用活跃度":
            dimension_score = min(int(app.monthly_calls * 5), 100)
        elif dimension.name == "稳定性和安全性":
            if app.status == "available":
                dimension_score = 100
            elif app.status == "beta":
                dimension_score = 80
            else:
                dimension_score = 60
        else:
            dimension_score = 50

        base_score += dimension_score * dimension.weight

    final_score = int(base_score * app.ranking_weight)
    return max(0, min(final_score, 1000))


def calculate_dimension_score(app: App, dimension: RankingDimension) -> tuple[int, str]:
    """
    计算应用在某个维度的得分和计算详情
    返回：(得分, 计算详情说明)
    """
    dimension_score = 0
    calculation_detail = ""
    
    if dimension.name == "用户满意度":
        dimension_score = min(int(app.monthly_calls * 10), 100)
        calculation_detail = f"基于月调用量计算：{app.monthly_calls} * 10 = {dimension_score}分"
    elif dimension.name == "业务价值":
        if app.effectiveness_type == "revenue_growth":
            dimension_score = 100
            calculation_detail = "成效类型为拉动收入，获得满分100分"
        elif app.effectiveness_type == "efficiency_gain":
            dimension_score = 80
            calculation_detail = "成效类型为增效，获得80分"
        elif app.effectiveness_type == "cost_reduction":
            dimension_score = 70
            calculation_detail = "成效类型为降本，获得70分"
        else:
            dimension_score = 60
            calculation_detail = "成效类型为感知提升，获得60分"
    elif dimension.name == "技术创新性":
        if app.difficulty == "High":
            dimension_score = 100
            calculation_detail = "难度等级为高，获得满分100分"
        elif app.difficulty == "Medium":
            dimension_score = 70
            calculation_detail = "难度等级为中，获得70分"
        else:
            dimension_score = 40
            calculation_detail = "难度等级为低，获得40分"
    elif dimension.name == "使用活跃度":
        dimension_score = min(int(app.monthly_calls * 5), 100)
        calculation_detail = f"基于月调用量计算：{app.monthly_calls} * 5 = {dimension_score}分"
    elif dimension.name == "稳定性和安全性":
        if app.status == "available":
            dimension_score = 100
            calculation_detail = "应用状态为可用，获得满分100分"
        elif app.status == "beta":
            dimension_score = 80
            calculation_detail = "应用状态为试运行，获得80分"
        else:
            dimension_score = 60
            calculation_detail = f"应用状态为{app.status}，获得60分"
    else:
        dimension_score = 50
        calculation_detail = "默认评分50分"
    
    return dimension_score, calculation_detail


def calculate_three_layer_score(
    app: App,
    config_dimensions: list[dict],
    dimension_map: dict[int, RankingDimension],
    weight_factor: float = 1.0,
) -> int:
    """三层榜单权威评分路径（纯计算函数，用于稳定性回归锚点）。"""
    base_score = 0.0
    for dim_config in config_dimensions:
        dim_id = dim_config.get("dim_id")
        weight = dim_config.get("weight", 1.0)
        dimension = dimension_map.get(dim_id)
        if not dimension:
            continue
        dim_score, _ = calculate_dimension_score(app, dimension)
        base_score += dim_score * weight

    final_score = int(base_score * weight_factor)
    return max(0, min(final_score, 1000))


def sync_rankings_service(db: Session, run_id: str | None = None) -> tuple[int, str]:
    """
    同步排行榜数据（支持三层架构）
    - 遍历每个榜单配置
    - 获取参与该榜单的应用
    - 根据榜单配置的维度权重计算得分
    - 生成排名并保存历史数据
    """
    import json
    
    # 获取所有活跃的榜单配置
    ranking_configs = (
        db.query(RankingConfig)
        .filter(RankingConfig.is_active.is_(True))
        .all()
    )
    active_config_ids = {config.id for config in ranking_configs}

    # 全局清理：非活跃（或已删除）配置的实时榜单记录，避免首页残留脏数据
    stale_realtime_query = db.query(Ranking)
    if active_config_ids:
        stale_realtime_query = stale_realtime_query.filter(~Ranking.ranking_config_id.in_(active_config_ids))
    removed_global_realtime_rows = stale_realtime_query.delete(synchronize_session=False)
    
    # 获取所有维度
    dimensions = (
        db.query(RankingDimension)
        .filter(RankingDimension.is_active.is_(True))
        .order_by(RankingDimension.id)
        .all()
    )
    
    # 创建维度ID到维度对象的映射
    dimension_map = {d.id: d for d in dimensions}
    
    updated_count = 0
    today = datetime.now().date()
    current_run_id = (run_id or str(uuid.uuid4())).strip()
    if not current_run_id:
        current_run_id = str(uuid.uuid4())
    
    for config in ranking_configs:
        config_dimension_updates = 0
        config_ranking_updates = 0
        config_historical_updates = 0

        # 解析榜单配置的维度权重
        try:
            config_dimensions = json.loads(config.dimensions_config) if config.dimensions_config else []
        except json.JSONDecodeError:
            config_dimensions = []
        
        # 获取参与该榜单的应用设置
        app_settings = (
            db.query(AppRankingSetting)
            .filter(
                AppRankingSetting.ranking_config_id == config.id,
                AppRankingSetting.is_enabled.is_(True)
            )
            .options(joinedload(AppRankingSetting.app))
            .all()
        )
        
        # 计算每个应用的得分
        app_scores = []
        for setting in app_settings:
            app = setting.app
            if not app or app.section != "province":
                continue

            # 维度分值来源收敛规则：
            # 1) 手动评分（calculation_detail 以“手动调整评分”开头）优先
            # 2) 否则按规则自动计算并落库
            weighted_dimension_score = 0.0
            for dim_config in config_dimensions:
                dim_id = dim_config.get("dim_id")
                weight = dim_config.get("weight", 1.0)

                dimension = dimension_map.get(dim_id)
                if not dimension:
                    continue

                # 保存维度评分
                existing_score = load_single_dimension_score(
                    db,
                    app_id=app.id,
                    ranking_config_id=config.id,
                    dimension_id=dimension.id,
                    period_date=today,
                )

                is_manual_score = bool(existing_score and (existing_score.calculation_detail or "").startswith("手动调整评分"))
                if is_manual_score:
                    dim_score = existing_score.score
                    existing_score.dimension_name = dimension.name
                    existing_score.weight = weight
                    existing_score.updated_at = datetime.utcnow()
                else:
                    dim_score, calc_detail = calculate_dimension_score(app, dimension)
                    if existing_score:
                        existing_score.dimension_name = dimension.name
                        existing_score.score = dim_score
                        existing_score.weight = weight
                        existing_score.calculation_detail = calc_detail
                        existing_score.updated_at = datetime.utcnow()
                    else:
                        db.add(
                            AppDimensionScore(
                                app_id=app.id,
                                ranking_config_id=config.id,
                                dimension_id=dimension.id,
                                dimension_name=dimension.name,
                                score=dim_score,
                                weight=weight,
                                calculation_detail=calc_detail,
                                period_date=today
                            )
                        )
                weighted_dimension_score += dim_score * weight
                config_dimension_updates += 1

            # 应用权重因子（使用已收敛的维度分值）
            final_score = max(0, min(int(weighted_dimension_score * setting.weight_factor), 1000))
            
            app_scores.append({
                "app": app,
                "setting": setting,
                "score": final_score
            })
        
        # 按得分排序
        # 明确同分规则：分数降序；同分按 app_id 升序，避免重算后顺序抖动
        app_scores.sort(key=lambda x: (-x["score"], x["app"].id))

        # 清理不再参与该榜单的实时排名（解决“换榜后旧榜仍残留”问题）
        participating_app_ids = {item["app"].id for item in app_scores}
        stale_rankings_query = db.query(Ranking).filter(Ranking.ranking_config_id == config.id)
        if participating_app_ids:
            stale_rankings_query = stale_rankings_query.filter(~Ranking.app_id.in_(participating_app_ids))
        removed_realtime_rows = stale_rankings_query.delete(synchronize_session=False)

        # 更新或创建排名记录
        for index, item in enumerate(app_scores, start=1):
            app = item["app"]
            setting = item["setting"]

            score = item["score"]
            
            tag = setting.custom_tags.strip() if setting.custom_tags else DEFAULT_RANKING_TAG
            usage_30d = int(app.monthly_calls * 1000) if app.monthly_calls else 0
            
            existing = (
                db.query(Ranking)
                .filter(
                    Ranking.ranking_config_id == config.id,
                    Ranking.app_id == app.id
                )
                .first()
            )
            
            if existing:
                existing.position = index
                existing.score = score
                existing.tag = tag
                existing.usage_30d = usage_30d
                existing.updated_at = datetime.utcnow()
            else:
                db.add(
                    Ranking(
                        ranking_config_id=config.id,
                        ranking_type=config.id,  # 保持兼容性
                        position=index,
                        app_id=app.id,
                        tag=tag,
                        score=score,
                        metric_type=config.calculation_method or "composite",
                        value_dimension=app.effectiveness_type,
                        usage_30d=usage_30d,
                        declared_at=today,
                    )
                )
            config_ranking_updates += 1
            
            # 保存历史榜单数据
            historical = (
                db.query(HistoricalRanking)
                .filter(
                    HistoricalRanking.ranking_config_id == config.id,
                    HistoricalRanking.app_id == app.id,
                    HistoricalRanking.period_date == today,
                    HistoricalRanking.run_id == current_run_id
                )
                .first()
            )
            
            if historical:
                historical.position = index
                historical.score = score
                historical.tag = tag
            else:
                db.add(
                    HistoricalRanking(
                        ranking_config_id=config.id,
                        ranking_type=config.id,  # 保持兼容性
                        period_date=today,
                        run_id=current_run_id,
                        position=index,
                        app_id=app.id,
                        app_name=app.name,
                        app_org=app.org,
                        tag=tag,
                        score=score,
                        metric_type=config.calculation_method or "composite",
                        value_dimension=app.effectiveness_type,
                        usage_30d=usage_30d
                    )
                )
            config_historical_updates += 1

            updated_count += 1

        write_ranking_audit_log(
            db,
            action="rankings_sync_config_published",
            ranking_type=config.id,
            ranking_config_id=config.id,
            period_date=today,
            run_id=current_run_id,
            actor="system",
            payload_summary=(
                f"dimension_score_updates={config_dimension_updates},"
                f"ranking_updates={config_ranking_updates},"
                f"historical_ranking_updates={config_historical_updates},"
                f"realtime_removed={removed_realtime_rows}"
            ),
        )

    if removed_global_realtime_rows:
        write_ranking_audit_log(
            db,
            action="rankings_sync_global_realtime_cleanup",
            ranking_type="all",
            period_date=today,
            run_id=current_run_id,
            actor="system",
            payload_summary=f"removed_realtime={removed_global_realtime_rows}",
        )

    db.commit()
    return updated_count, current_run_id


def sync_after_chain_mutation(db: Session, trigger: str) -> tuple[int, str]:
    """链路节点发生增删改后，统一触发榜单重算并返回运行信息。"""
    try:
        # SessionLocal 关闭了 autoflush，先显式 flush，避免同步阶段读不到本次变更。
        db.flush()
        updated_count, run_id = sync_rankings_service(db)
        write_ranking_audit_log(
            db,
            action=f"{trigger}_triggered_sync",
            ranking_type="all",
            period_date=datetime.utcnow().date(),
            run_id=run_id,
            actor="system",
            payload_summary=f"updated_count={updated_count}",
        )
        db.commit()
        return updated_count, run_id
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"链路同步失败: {str(exc)}") from exc


@app.get(f"{settings.api_prefix}/health")
def health_check():
    return {"status": "ok"}


@app.post(f"{settings.api_prefix}/auth/login", response_model=AuthLoginResponse)
def auth_login(
    payload: AuthLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    username = payload.username.strip()
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
    db.commit()

    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.environment.lower() in {"prod", "production"},
        samesite="lax",
        max_age=ttl_hours * 3600,
    )

    return AuthLoginResponse(
        access_token=token,
        token_type="bearer",
        expires_at=expires_at,
        user=to_public_user(user),
    )


@app.get(f"{settings.api_prefix}/auth/me", response_model=AuthMeResponse)
def auth_me(auth_session: AuthSession = Depends(require_auth_session)):
    return AuthMeResponse(
        expires_at=auth_session.expires_at,
        user=to_public_user(auth_session.user),
    )


@app.post(f"{settings.api_prefix}/auth/logout")
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
    response.delete_cookie(settings.auth_cookie_name)
    return {"message": "已退出登录"}


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

    try:
        return query.order_by(App.id).all()
    except SQLAlchemyError:
        # 数据库表结构可能不完整，回退到 SQL 查询并补齐兼容字段。
        try:
            result = db.execute(text("""
                SELECT id, name, org, section, category, description, status, monthly_calls, release_date,
                       api_open, difficulty, contact_name, highlight, access_mode, access_url,
                       detail_doc_url, detail_doc_name,
                       target_system, target_users, problem_statement, effectiveness_type, effectiveness_metric,
                       cover_image_url
                FROM apps
                ORDER BY id
            """))
            apps = []
            for row in result:
                apps.append({
                    "id": row.id,
                    "name": row.name,
                    "org": row.org,
                    "section": row.section,
                    "category": row.category,
                    "description": row.description,
                    "status": row.status,
                    "monthly_calls": row.monthly_calls,
                    "release_date": row.release_date,
                    "api_open": row.api_open,
                    "difficulty": row.difficulty,
                    "contact_name": row.contact_name,
                    "highlight": row.highlight,
                    "access_mode": row.access_mode,
                    "access_url": row.access_url,
                    "detail_doc_url": row.detail_doc_url or "",
                    "detail_doc_name": row.detail_doc_name or "",
                    "target_system": row.target_system,
                    "target_users": row.target_users,
                    "problem_statement": row.problem_statement,
                    "effectiveness_type": row.effectiveness_type,
                    "effectiveness_metric": row.effectiveness_metric,
                    "cover_image_url": row.cover_image_url,
                    "ranking_enabled": True,
                    "ranking_weight": 1.0,
                    "ranking_tags": "",
                    "last_ranking_update": None,
                })
            return apps
        except SQLAlchemyError:
            return []


@app.get(f"{settings.api_prefix}/apps/{{app_id}}", response_model=AppDetail)
def get_app_detail(app_id: int, db: Session = Depends(get_db)):
    try:
        item = db.query(App).filter(App.id == app_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="App not found")
        return item
    except HTTPException:
        raise
    except SQLAlchemyError:
        # 数据库表结构可能不完整，使用 SQL 查询获取兼容字段
        try:
            result = db.execute(text("""
                SELECT id, name, org, section, category, description, status, monthly_calls, release_date,
                       api_open, difficulty, contact_name, highlight, access_mode, access_url,
                       detail_doc_url, detail_doc_name,
                       target_system, target_users, problem_statement, effectiveness_type, effectiveness_metric,
                       cover_image_url
                FROM apps
                WHERE id = :app_id
            """), {"app_id": app_id})
            
            row = result.first()
            if not row:
                raise HTTPException(status_code=404, detail="App not found")
            
            # 构造应用对象
            app_dict = {
                "id": row.id,
                "name": row.name,
                "org": row.org,
                "section": row.section,
                "category": row.category,
                "description": row.description,
                "status": row.status,
                "monthly_calls": row.monthly_calls,
                "release_date": row.release_date,
                "api_open": row.api_open,
                "difficulty": row.difficulty,
                "contact_name": row.contact_name,
                "highlight": row.highlight,
                "access_mode": row.access_mode,
                "access_url": row.access_url,
                "detail_doc_url": row.detail_doc_url or "",
                "detail_doc_name": row.detail_doc_name or "",
                "target_system": row.target_system,
                "target_users": row.target_users,
                "problem_statement": row.problem_statement,
                "effectiveness_type": row.effectiveness_type,
                "effectiveness_metric": row.effectiveness_metric,
                "cover_image_url": row.cover_image_url,
                # 添加默认值
                "ranking_enabled": True,
                "ranking_weight": 1.0,
                "ranking_tags": "",
                "last_ranking_update": None
            }
            return app_dict
        except SQLAlchemyError:
            raise HTTPException(status_code=404, detail="App not found")


def resolve_latest_run_id(db: Session, ranking_type: str, period_date: date) -> str | None:
    """返回某榜单在指定日期最新发布的 run_id（旧数据可能为空）。"""
    scope_id = resolve_ranking_scope_id(ranking_type=ranking_type)
    latest_with_run = (
        db.query(HistoricalRanking.run_id)
        .filter(
            or_(
                HistoricalRanking.ranking_config_id == scope_id,
                HistoricalRanking.ranking_type == scope_id,
            )
        )
        .filter(HistoricalRanking.period_date == period_date)
        .filter(HistoricalRanking.run_id.is_not(None))
        .order_by(HistoricalRanking.created_at.desc())
        .first()
    )
    return latest_with_run[0] if latest_with_run else None


@app.get(f"{settings.api_prefix}/rankings", response_model=list[RankingItem])
def list_rankings(
    ranking_type: str = "excellent",
    ranking_config_id: str | None = Query(default=None, description="榜单配置ID（兼容前端 ranking_config_id 参数）"),
    period_date: date | None = Query(default=None, description="查询历史榜单日期，格式：YYYY-MM-DD；不传则返回实时榜单"),
    db: Session = Depends(get_db)
):
    """
    获取应用榜单
    - 榜单仅展示省内应用
    - 支持按日期查询历史榜单
    - 不传日期则返回实时榜单（Ranking 表），用于首页/管理页即时展示
    """
    scope_id = resolve_ranking_scope_id(ranking_type=ranking_type, ranking_config_id=ranking_config_id)

    def _to_ranking_item(
        *,
        app: App,
        ranking_config_id_value: str | None,
        position: int,
        tag: str,
        score: int,
        metric_type: str,
        value_dimension: str,
        usage_30d: int,
        declared_at: date,
        updated_at: datetime | None = None,
    ) -> dict:
        return {
            "ranking_config_id": ranking_config_id_value,
            "position": position,
            "tag": tag,
            "score": score,
            "likes": None,
            "metric_type": metric_type,
            "value_dimension": value_dimension,
            "usage_30d": usage_30d,
            "declared_at": declared_at,
            "updated_at": updated_at,
            "app": app,
        }

    try:
        if period_date:
            # 查询指定日期的历史榜单
            selected_run_id = resolve_latest_run_id(db, scope_id, period_date)
            historical_query = (
                db.query(HistoricalRanking)
                .filter(HistoricalRanking.period_date == period_date)
                .filter(
                    or_(
                        HistoricalRanking.ranking_config_id == scope_id,
                        HistoricalRanking.ranking_type == scope_id,
                    )
                )
            )
            if selected_run_id is not None:
                historical_query = historical_query.filter(HistoricalRanking.run_id == selected_run_id)
            else:
                historical_query = historical_query.filter(HistoricalRanking.run_id.is_(None))

            historical_rankings = historical_query.order_by(HistoricalRanking.position).all()
            result = []
            for hr in historical_rankings:
                app = db.query(App).filter(App.id == hr.app_id).first()
                if app and app.section == "province":
                    result.append(
                        _to_ranking_item(
                            app=app,
                            ranking_config_id_value=hr.ranking_config_id,
                            position=hr.position,
                            tag=hr.tag,
                            score=hr.score,
                            metric_type=hr.metric_type,
                            value_dimension=hr.value_dimension,
                            usage_30d=hr.usage_30d,
                            declared_at=hr.period_date,
                            updated_at=getattr(hr, "updated_at", None),
                        )
                    )
            return result
        # 查询实时榜单（Ranking 表）
        realtime_query = (
            db.query(Ranking)
            .filter(
                or_(
                    Ranking.ranking_config_id == scope_id,
                    Ranking.ranking_type == scope_id,
                )
            )
        )

        realtime_rows = realtime_query.order_by(Ranking.position).all()
        result = []
        for row in realtime_rows:
            app = db.query(App).filter(App.id == row.app_id).first()
            if app and app.section == "province":
                result.append(
                    _to_ranking_item(
                        app=app,
                        ranking_config_id_value=row.ranking_config_id,
                        position=row.position,
                        tag=row.tag,
                        score=row.score,
                        metric_type=row.metric_type,
                        value_dimension=row.value_dimension,
                        usage_30d=row.usage_30d,
                        declared_at=row.declared_at,
                        updated_at=row.updated_at,
                    )
                )
        return result
    except Exception as e:
        # 数据库表结构可能不完整，返回空列表
        print(f"Error in list_rankings: {e}")
        return []


@app.get(f"{settings.api_prefix}/recommendations", response_model=list[Recommendation])
def recommendations():
    return [
        Recommendation(title="智能客服助手", scene="7×24 小时自动应答"),
        Recommendation(title="AI会议助手", scene="自动生成会议纪要"),
        Recommendation(title="智能数据分析", scene="一键生成分析报告"),
    ]


@app.get(f"{settings.api_prefix}/stats", response_model=Stats)
def app_stats(db: Session = Depends(get_db)):
    """
    获取申报统计数据
    数据来源：
    - pending: 数据库中状态为"pending"的申报数量
    - approved_period: 数据库中状态为"approved"的申报数量
    - total_apps: 数据库中所有应用的数量
    """
    pending = db.query(Submission).filter(Submission.status == "pending").count()
    approved_period = db.query(Submission).filter(Submission.status == "approved").count()
    total_apps = db.query(App).count()
    return Stats(pending=pending, approved_period=approved_period, total_apps=total_apps)


@app.get(f"{settings.api_prefix}/rules", response_model=list[RuleLink])
def rules():
    base = settings.oa_rule_base_url.rstrip("/")
    return [
        RuleLink(title="如何申报应用", href=f"{base}/ai-app-square/rules/submission"),
        RuleLink(title="上榜评选标准", href=f"{base}/ai-app-square/rules/ranking"),
        RuleLink(title="API接入指南", href=f"{base}/ai-app-square/rules/api-integration"),
    ]


@app.get(f"{settings.api_prefix}/submissions", response_model=list[SubmissionOut])
def list_submissions(
    status: str | None = Query(default=None, description="按状态筛选：pending, approved, rejected, withdrawn"),
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取申报列表
    """
    query = db.query(Submission)
    if status:
        query = query.filter(Submission.status == status)
    return query.order_by(Submission.created_at.desc()).all()


@app.post(f"{settings.api_prefix}/submissions", response_model=SubmissionOut)
def create_submission(
    payload: SubmissionCreate,
    request: Request,
    auth_session: AuthSession = Depends(require_auth_session),
    db: Session = Depends(get_db),
):
    validate_submission_payload(payload)
    normalized_name = normalize_dedupe_text(payload.app_name)
    normalized_unit = normalize_dedupe_text(payload.unit_name)
    existing = (
        db.query(Submission)
        .filter(
            func.lower(func.trim(Submission.app_name)) == normalized_name,
            func.lower(func.trim(Submission.unit_name)) == normalized_unit,
            Submission.status.in_(("pending", "approved")),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="该应用已存在待审核或已通过的申报记录，请勿重复提交")

    submission_data = payload.model_dump()
    # 收敛：申报阶段不再写入排行榜参数，保留历史字段仅做兼容读取。
    submission_data["ranking_enabled"] = False
    submission_data["ranking_weight"] = 1.0
    submission_data["ranking_tags"] = ""
    submission_data["ranking_dimensions"] = ""
    submitter = auth_session.user
    submission = Submission(
        **submission_data,
        manage_token=uuid.uuid4().hex,
        submitter_user_id=submitter.id,
    )
    db.add(submission)
    try:
        db.flush()
        write_action_log(
            db,
            action="submission.create",
            actor_user=submitter,
            resource_type="submission",
            resource_id=str(submission.id),
            request_id=request.headers.get("X-Request-Id", ""),
            payload_summary=f"app_name={submission.app_name},unit_name={submission.unit_name}",
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="检测到重复申报，请勿重复提交")
    db.refresh(submission)
    return submission


@app.get(f"{settings.api_prefix}/submissions/mine", response_model=list[SubmissionOut])
def list_my_submissions(
    auth_session: AuthSession = Depends(require_auth_session),
    db: Session = Depends(get_db),
):
    """当前登录用户查看自己的申报记录。"""
    return (
        db.query(Submission)
        .filter(Submission.submitter_user_id == auth_session.user.id)
        .order_by(Submission.created_at.desc())
        .all()
    )


@app.put(f"{settings.api_prefix}/submissions/{{submission_id}}/mine", response_model=SubmissionOut)
def update_my_submission(
    submission_id: int,
    payload: SubmissionCreate,
    request: Request,
    auth_session: AuthSession = Depends(require_auth_session),
    db: Session = Depends(get_db),
):
    """当前登录用户修改本人申报（仅 pending）。"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.submitter_user_id != auth_session.user.id:
        raise HTTPException(status_code=403, detail="无权限修改他人申报")
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核申报允许修改")

    normalized_name = normalize_dedupe_text(payload.app_name)
    normalized_unit = normalize_dedupe_text(payload.unit_name)
    duplicate = (
        db.query(Submission)
        .filter(
            Submission.id != submission_id,
            func.lower(func.trim(Submission.app_name)) == normalized_name,
            func.lower(func.trim(Submission.unit_name)) == normalized_unit,
            Submission.status.in_(("pending", "approved")),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="该应用已存在待审核或已通过的申报记录，请勿重复提交")

    validate_submission_payload(payload)
    update_fields = payload.model_dump()
    update_fields["ranking_dimensions"] = ""
    for key, value in update_fields.items():
        setattr(submission, key, value)

    write_action_log(
        db,
        action="submission.update_mine",
        actor_user=auth_session.user,
        resource_type="submission",
        resource_id=str(submission.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"app_name={submission.app_name},unit_name={submission.unit_name}",
    )
    db.commit()
    db.refresh(submission)
    return submission


@app.post(f"{settings.api_prefix}/submissions/{{submission_id}}/mine/withdraw")
def withdraw_my_submission(
    submission_id: int,
    request: Request,
    auth_session: AuthSession = Depends(require_auth_session),
    db: Session = Depends(get_db),
):
    """当前登录用户撤回本人申报（仅 pending）。"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.submitter_user_id != auth_session.user.id:
        raise HTTPException(status_code=403, detail="无权限撤回他人申报")
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核申报可撤回")

    submission.status = "withdrawn"
    write_action_log(
        db,
        action="submission.withdraw_mine",
        actor_user=auth_session.user,
        resource_type="submission",
        resource_id=str(submission.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"status={submission.status}",
    )
    db.commit()
    return {"message": "申报已撤回", "submission_id": submission_id}


@app.get(f"{settings.api_prefix}/submissions/self", response_model=SubmissionOut)
def get_submission_self(
    manage_token: str = Query(..., min_length=16, max_length=128),
    db: Session = Depends(get_db)
):
    """
    通过管理令牌查询本人申报（用于申报人查看/修改/撤回）。
    """
    submission = db.query(Submission).filter(Submission.manage_token == manage_token).first()
    if not submission:
        raise HTTPException(status_code=404, detail="未找到对应申报")
    return submission


@app.put(f"{settings.api_prefix}/submissions/{{submission_id}}/self", response_model=SubmissionOut)
def update_submission_self(
    submission_id: int,
    payload: SubmissionSelfUpdate,
    request: Request,
    auth_session: AuthSession = Depends(require_auth_session),
    db: Session = Depends(get_db)
):
    """
    申报人修改本人申报（仅 pending）。
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.submitter_user_id is not None:
        if submission.submitter_user_id != auth_session.user.id:
            raise HTTPException(status_code=403, detail="无权限修改他人申报")
    elif submission.manage_token != payload.manage_token:
        # 历史兼容：旧匿名申报仍允许通过 manage_token 修改
        raise HTTPException(status_code=403, detail="管理令牌无效")
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核申报允许修改")

    normalized_name = normalize_dedupe_text(payload.app_name)
    normalized_unit = normalize_dedupe_text(payload.unit_name)
    duplicate = (
        db.query(Submission)
        .filter(
            Submission.id != submission_id,
            func.lower(func.trim(Submission.app_name)) == normalized_name,
            func.lower(func.trim(Submission.unit_name)) == normalized_unit,
            Submission.status.in_(("pending", "approved")),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="该应用已存在待审核或已通过的申报记录，请勿重复提交")

    create_payload = SubmissionCreate(**payload.model_dump(exclude={"manage_token"}))
    validate_submission_payload(create_payload)

    update_fields = create_payload.model_dump()
    # 收敛：ranking_dimensions 停写。
    update_fields["ranking_dimensions"] = ""
    for key, value in update_fields.items():
        setattr(submission, key, value)

    write_action_log(
        db,
        action="submission.update_self",
        actor_user=auth_session.user,
        resource_type="submission",
        resource_id=str(submission.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"app_name={submission.app_name},unit_name={submission.unit_name}",
    )
    db.commit()
    db.refresh(submission)
    return submission


@app.post(f"{settings.api_prefix}/submissions/{{submission_id}}/withdraw")
def withdraw_submission_self(
    submission_id: int,
    payload: SubmissionManageTokenPayload,
    request: Request,
    auth_session: AuthSession = Depends(require_auth_session),
    db: Session = Depends(get_db)
):
    """
    申报人撤回本人申报（仅 pending）。
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.submitter_user_id is not None:
        if submission.submitter_user_id != auth_session.user.id:
            raise HTTPException(status_code=403, detail="无权限撤回他人申报")
    elif submission.manage_token != payload.manage_token:
        raise HTTPException(status_code=403, detail="管理令牌无效")
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核申报可撤回")

    submission.status = "withdrawn"
    write_action_log(
        db,
        action="submission.withdraw",
        actor_user=auth_session.user,
        resource_type="submission",
        resource_id=str(submission.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"status={submission.status}",
    )
    db.commit()
    return {"message": "申报已撤回", "submission_id": submission_id}


@app.get(f"{settings.api_prefix}/meta/enums")
def list_enums():
    return {
        "app_status": sorted(APP_STATUS_VALUES),
        "ranking_metric_type": sorted(METRIC_TYPES),
        "value_dimension": sorted(VALUE_DIMENSIONS),
        "data_level": sorted(DATA_LEVEL_VALUES),
    }


# 排行维度管理 API

@app.get(f"{settings.api_prefix}/ranking-dimensions", response_model=list[RankingDimensionOut])
def get_ranking_dimensions(
    is_active: bool | None = None,
    db: Session = Depends(get_db)
):
    """
    获取排行维度列表
    """
    query = db.query(RankingDimension)
    if is_active is not None:
        query = query.filter(RankingDimension.is_active == is_active)
    return query.order_by(RankingDimension.id).all()


@app.get(f"{settings.api_prefix}/ranking-dimensions/{{dimension_id}}/scores", response_model=list[AppDimensionScoreOut])
def list_dimension_scores(
    dimension_id: int,
    period_date: date | None = Query(default=None, description="查询日期，格式：YYYY-MM-DD"),
    ranking_config_id: str | None = Query(default=None, description="榜单配置ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定维度的应用评分列表
    """
    try:
        query = db.query(AppDimensionScore).filter(AppDimensionScore.dimension_id == dimension_id)
        if ranking_config_id is not None:
            query = query.filter(AppDimensionScore.ranking_config_id == ranking_config_id.strip())
        if period_date:
            query = query.filter(AppDimensionScore.period_date == period_date)
        else:
            today = datetime.now().date()
            query = query.filter(AppDimensionScore.period_date == today)
        return query.order_by(AppDimensionScore.score.desc()).all()
    except Exception as e:
        return []


@app.get(f"{settings.api_prefix}/apps/{{app_id}}/dimension-scores", response_model=list[AppDimensionScoreOut])
def list_app_dimension_scores(
    app_id: int,
    period_date: date | None = Query(default=None, description="查询日期，格式：YYYY-MM-DD"),
    ranking_config_id: str | None = Query(default=None, description="榜单配置ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定应用在各维度的评分详情
    """
    try:
        query = db.query(AppDimensionScore).filter(AppDimensionScore.app_id == app_id)
        if ranking_config_id is not None:
            query = query.filter(AppDimensionScore.ranking_config_id == ranking_config_id.strip())
        if period_date:
            query = query.filter(AppDimensionScore.period_date == period_date)
        else:
            today = datetime.now().date()
            query = query.filter(AppDimensionScore.period_date == today)
        return query.order_by(AppDimensionScore.dimension_id).all()
    except Exception as e:
        return []


@app.put(f"{settings.api_prefix}/apps/{{app_id}}/ranking-params")
def update_app_ranking_params(
    app_id: int,
    ranking_enabled: bool | None = None,
    ranking_weight: float | None = None,
    ranking_tags: str | None = None,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新应用排行参数
    """
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")

    if ranking_weight is not None and (ranking_weight < 0.1 or ranking_weight > 10.0):
        raise HTTPException(status_code=422, detail="ranking_weight must be between 0.1 and 10.0")
    if ranking_tags is not None and len(ranking_tags) > 255:
        raise HTTPException(status_code=422, detail="ranking_tags must not exceed 255 characters")
    
    if ranking_enabled is not None:
        app.ranking_enabled = ranking_enabled
    if ranking_weight is not None:
        app.ranking_weight = ranking_weight
    if ranking_tags is not None:
        app.ranking_tags = ranking_tags
    app.last_ranking_update = datetime.utcnow()
    
    updated_count, run_id = sync_after_chain_mutation(db, "app_ranking_params_updated")
    db.refresh(app)
    return {"message": "排行参数更新成功", "app_id": app_id, "synced": updated_count, "run_id": run_id}


@app.put(f"{settings.api_prefix}/apps/{{app_id}}/dimension-scores/{{dimension_id}}")
def update_app_dimension_score_api(
    app_id: int,
    dimension_id: int,
    payload: DimensionScoreUpdate | None = None,
    score: int | None = Query(default=None, ge=0, le=100),
    ranking_config_id: str | None = Query(default=None, description="榜单配置ID"),
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新应用在某个维度的评分（手动调整）
    """
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    dimension = db.query(RankingDimension).filter(RankingDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="维度不存在")

    resolved_score = payload.score if payload is not None else score
    if resolved_score is None:
        raise HTTPException(status_code=422, detail="score is required")
    config_id = ranking_config_id.strip() if ranking_config_id else None
    if config_id:
        config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="榜单配置不存在")
    
    today = datetime.now().date()
    
    # 查找或创建评分记录
    score_record = load_single_dimension_score(
        db,
        app_id=app_id,
        ranking_config_id=config_id,
        dimension_id=dimension_id,
        period_date=today,
    )
    before_score = score_record.score if score_record else None

    if score_record:
        score_record.score = resolved_score
        score_record.dimension_name = dimension.name
        score_record.weight = dimension.weight
        score_record.calculation_detail = f"手动调整评分: {resolved_score}分"
    else:
        score_record = AppDimensionScore(
            app_id=app_id,
            ranking_config_id=config_id,
            dimension_id=dimension_id,
            dimension_name=dimension.name,
            period_date=today,
            score=resolved_score,
            weight=dimension.weight,
            calculation_detail=f"手动调整评分: {resolved_score}分"
        )
        db.add(score_record)
    write_ranking_audit_log(
        db,
        action="dimension_score_manual_saved",
        ranking_type=None,
        ranking_config_id=config_id,
        period_date=today,
        actor=admin_user.username if admin_user else "system",
        payload_summary=(
            f"app_id={app_id},dimension_id={dimension_id},"
            f"before={before_score},after={resolved_score}"
        ),
    )
    updated_count, run_id = sync_after_chain_mutation(db, "dimension_score_updated")
    db.refresh(score_record)
    return {
        "message": "维度评分更新成功",
        "app_id": app_id,
        "dimension_id": dimension_id,
        "score": resolved_score,
        "synced": updated_count,
        "run_id": run_id,
    }


@app.get(f"{settings.api_prefix}/rankings/historical", response_model=list[HistoricalRankingOut])
def list_historical_rankings(
    ranking_type: str = "excellent",
    period_date: date | None = Query(default=None, description="查询日期，格式：YYYY-MM-DD"),
    run_id: str | None = Query(default=None, description="可选发布批次ID；不传则日期模式返回最新 run_id"),
    db: Session = Depends(get_db)
):
    """
    获取历史榜单数据（默认返回最新发布批次的只读快照）
    """
    try:
        scope_id = resolve_ranking_scope_id(ranking_type=ranking_type)
        query = db.query(HistoricalRanking).filter(
            or_(
                HistoricalRanking.ranking_config_id == scope_id,
                HistoricalRanking.ranking_type == scope_id,
            )
        )
        target_date = period_date
        if target_date is None:
            latest_date_row = (
                db.query(HistoricalRanking.period_date)
                .filter(
                    or_(
                        HistoricalRanking.ranking_config_id == scope_id,
                        HistoricalRanking.ranking_type == scope_id,
                    )
                )
                .order_by(HistoricalRanking.period_date.desc())
                .first()
            )
            if latest_date_row is None:
                return []
            target_date = latest_date_row[0]

        query = query.filter(HistoricalRanking.period_date == target_date)
        selected_run_id = run_id if run_id is not None else resolve_latest_run_id(db, scope_id, target_date)
        if selected_run_id is not None:
            query = query.filter(HistoricalRanking.run_id == selected_run_id)
        else:
            query = query.filter(HistoricalRanking.run_id.is_(None))
        return query.order_by(HistoricalRanking.position).all()
    except Exception as e:
        return []


@app.get(f"{settings.api_prefix}/rankings/available-dates")
def list_available_ranking_dates(
    ranking_type: str = "excellent",
    db: Session = Depends(get_db)
):
    """
    获取可用的榜单日期列表
    """
    try:
        scope_id = resolve_ranking_scope_id(ranking_type=ranking_type)
        dates = (
            db.query(HistoricalRanking.period_date)
            .filter(
                or_(
                    HistoricalRanking.ranking_config_id == scope_id,
                    HistoricalRanking.ranking_type == scope_id,
                )
            )
            .distinct()
            .order_by(HistoricalRanking.period_date.desc())
            .all()
        )
        return {"dates": [d[0].isoformat() for d in dates]}
    except Exception as e:
        return {"dates": []}


@app.get(f"{settings.api_prefix}/ranking-dimensions/{{dimension_id}}", response_model=RankingDimensionOut)
def get_ranking_dimension(
    dimension_id: int,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取排行维度详情
    """
    dimension = db.query(RankingDimension).filter(RankingDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="排行维度不存在")
    return dimension


@app.post(f"{settings.api_prefix}/ranking-dimensions", response_model=RankingDimensionOut)
def create_ranking_dimension(
    payload: RankingDimensionCreate,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    创建排行维度
    """
    # 检查名称是否已存在
    existing = db.query(RankingDimension).filter(RankingDimension.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="排行维度名称已存在")
    
    # 创建排行维度
    dimension = RankingDimension(**payload.model_dump())
    db.add(dimension)
    db.flush()
    
    # 记录日志
    log = RankingLog(
        action="create",
        dimension_id=dimension.id,
        dimension_name=dimension.name,
        changes=f"创建了排行维度: {dimension.name}",
        operator="system"
    )
    db.add(log)
    write_ranking_audit_log(
        db,
        action="ranking_dimension_created",
        ranking_type="all",
        period_date=datetime.utcnow().date(),
        actor="system",
        payload_summary=f"dimension_id={dimension.id},name={dimension.name}",
    )
    sync_after_chain_mutation(db, "ranking_dimension_created")
    db.refresh(dimension)

    return dimension


@app.put(f"{settings.api_prefix}/ranking-dimensions/{{dimension_id}}", response_model=RankingDimensionOut)
def update_ranking_dimension(
    dimension_id: int,
    payload: RankingDimensionUpdate,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新排行维度
    """
    dimension = db.query(RankingDimension).filter(RankingDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="排行维度不存在")
    
    # 检查名称是否已被其他维度使用
    if payload.name and payload.name != dimension.name:
        existing = db.query(RankingDimension).filter(RankingDimension.name == payload.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="排行维度名称已存在")
    
    # 记录变更
    changes = []
    name_changed = False
    if payload.name and payload.name != dimension.name:
        changes.append(f"名称: {dimension.name} → {payload.name}")
        dimension.name = payload.name
        name_changed = True
    if payload.description is not None and payload.description != dimension.description:
        changes.append("描述已更新")
        dimension.description = payload.description
    if payload.calculation_method is not None and payload.calculation_method != dimension.calculation_method:
        changes.append("计算方法已更新")
        dimension.calculation_method = payload.calculation_method
    if payload.weight is not None and payload.weight != dimension.weight:
        changes.append(f"权重: {dimension.weight} → {payload.weight}")
        dimension.weight = payload.weight
    if payload.is_active is not None and payload.is_active != dimension.is_active:
        changes.append(f"状态: {'启用' if dimension.is_active else '禁用'} → {'启用' if payload.is_active else '禁用'}")
        dimension.is_active = payload.is_active
    
    # 维度更名需要级联更新快照字段，避免历史评分展示名称漂移
    if name_changed:
        (
            db.query(AppDimensionScore)
            .filter(AppDimensionScore.dimension_id == dimension.id)
            .update({"dimension_name": dimension.name}, synchronize_session=False)
        )
    
    # 记录日志
    if changes:
        log = RankingLog(
            action="update",
            dimension_id=dimension.id,
            dimension_name=dimension.name,
            changes="; ".join(changes),
            operator="system"
        )
        db.add(log)
        write_ranking_audit_log(
            db,
            action="ranking_dimension_updated",
            ranking_type="all",
            period_date=datetime.utcnow().date(),
            actor="system",
            payload_summary=f"dimension_id={dimension.id},changes={' | '.join(changes)}",
        )
    sync_after_chain_mutation(db, "ranking_dimension_updated")
    db.refresh(dimension)

    return dimension


@app.delete(f"{settings.api_prefix}/ranking-dimensions/{{dimension_id}}")
def delete_ranking_dimension(
    dimension_id: int,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    删除排行维度
    """
    dimension = db.query(RankingDimension).filter(RankingDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="排行维度不存在")
    
    import json

    # 从榜单配置中剔除被删除维度
    touched_configs = 0
    for config in db.query(RankingConfig).all():
        try:
            dim_items = json.loads(config.dimensions_config) if config.dimensions_config else []
        except json.JSONDecodeError:
            dim_items = []
        filtered_items = [item for item in dim_items if item.get("dim_id") != dimension_id]
        if len(filtered_items) != len(dim_items):
            config.dimensions_config = json.dumps(filtered_items, ensure_ascii=False)
            touched_configs += 1

    removed_scores = (
        db.query(AppDimensionScore)
        .filter(AppDimensionScore.dimension_id == dimension_id)
        .delete(synchronize_session=False)
    )

    # 记录日志
    log = RankingLog(
        action="delete",
        # 删除动作不再保留外键，避免 FK 校验开启时阻塞删除
        dimension_id=None,
        dimension_name=dimension.name,
        changes=f"删除了排行维度: {dimension.name}",
        operator="system"
    )
    db.add(log)
    write_ranking_audit_log(
        db,
        action="ranking_dimension_deleted",
        ranking_type="all",
        period_date=datetime.utcnow().date(),
        actor="system",
        payload_summary=(
            f"dimension_id={dimension.id},name={dimension.name},"
            f"removed_scores={removed_scores},touched_configs={touched_configs}"
        ),
    )

    # 删除排行维度
    db.delete(dimension)
    synced, run_id = sync_after_chain_mutation(db, "ranking_dimension_deleted")

    return {
        "message": "排行维度已删除",
        "removed_scores": removed_scores,
        "touched_configs": touched_configs,
        "synced": synced,
        "run_id": run_id,
    }


@app.get(f"{settings.api_prefix}/ranking-logs", response_model=list[RankingLogOut])
def get_ranking_logs(
    limit: int = 100,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取排行维度变更日志
    """
    return db.query(RankingLog).order_by(RankingLog.created_at.desc()).limit(limit).all()


@app.get(f"{settings.api_prefix}/ranking-audit-logs", response_model=list[RankingAuditLogOut])
def get_ranking_audit_logs(
    limit: int = 100,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """获取排行榜审计日志。"""
    return db.query(RankingAuditLog).order_by(RankingAuditLog.created_at.desc()).limit(limit).all()


@app.get(f"{settings.api_prefix}/action-logs", response_model=list[ActionLogOut])
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


@app.get(f"{settings.api_prefix}/admin/users", response_model=list[UserPublic])
def list_users(
    q: str | None = Query(default=None),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    _: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        query = query.filter(
            or_(
                User.username.contains(q),
                User.chinese_name.contains(q),
                User.email.contains(q),
                User.department.contains(q),
            )
        )
    if role:
        if role not in {"user", "admin"}:
            raise HTTPException(status_code=422, detail="Invalid role")
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))

    return query.order_by(User.id.asc()).all()


@app.put(f"{settings.api_prefix}/admin/users/{{user_id}}/role", response_model=UserPublic)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdatePayload,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == payload.role:
        return user

    if user.role == "admin" and payload.role != "admin":
        active_admin_count = (
            db.query(User)
            .filter(User.role == "admin", User.is_active.is_(True))
            .count()
        )
        if active_admin_count <= 1:
            raise HTTPException(status_code=409, detail="至少需要保留一个启用状态的管理员账号")

    old_role = user.role
    user.role = payload.role
    write_action_log(
        db,
        action="user.role_updated",
        actor_user=admin_user,
        resource_type="user",
        resource_id=str(user.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"username={user.username},old={old_role},new={user.role}",
    )
    db.commit()
    db.refresh(user)
    return user


@app.put(f"{settings.api_prefix}/admin/users/{{user_id}}/status", response_model=UserPublic)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdatePayload,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if bool(user.is_active) == bool(payload.is_active):
        return user

    if user.role == "admin" and user.is_active and not payload.is_active:
        active_admin_count = (
            db.query(User)
            .filter(User.role == "admin", User.is_active.is_(True))
            .count()
        )
        if active_admin_count <= 1:
            raise HTTPException(status_code=409, detail="至少需要保留一个启用状态的管理员账号")

    if admin_user and admin_user.id == user.id and not payload.is_active:
        raise HTTPException(status_code=409, detail="不能禁用当前登录管理员账号")

    old_status = bool(user.is_active)
    user.is_active = payload.is_active
    if not payload.is_active:
        db.query(AuthSession).filter(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None),
        ).update(
            {AuthSession.revoked_at: datetime.utcnow()},
            synchronize_session=False,
        )

    write_action_log(
        db,
        action="user.status_updated",
        actor_user=admin_user,
        resource_type="user",
        resource_id=str(user.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"username={user.username},old={old_status},new={bool(user.is_active)}",
    )
    db.commit()
    db.refresh(user)
    return user


@app.post(f"{settings.api_prefix}/admin/users/import", response_model=UserImportResponse)
def import_users(
    payload: UserImportRequest,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    try:
        result = upsert_users(db, payload=payload)
        write_action_log(
            db,
            action="user.import",
            actor_user=admin_user,
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
        raise HTTPException(status_code=500, detail=f"导入用户失败: {str(exc)}") from exc


@app.post(f"{settings.api_prefix}/integration/users/sync", response_model=UserImportResponse)
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


# 数据联动 API

@app.post(f"{settings.api_prefix}/rankings/sync")
def sync_rankings(
    run_id: str | None = Query(default=None, description="可选发布批次ID；不传则自动生成 UUID"),
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    同步排行榜数据，确保集团应用和省内应用信息保持一致
    """
    try:
        updated_count, generated_run_id = sync_rankings_service(db, run_id=run_id)
        return {"message": "排行榜数据同步成功", "updated_count": updated_count, "run_id": generated_run_id}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"同步失败: {str(exc)}") from exc


def validate_publish_preconditions(db: Session) -> dict[str, int]:
    active_configs = db.query(RankingConfig).filter(RankingConfig.is_active.is_(True)).all()
    if not active_configs:
        raise HTTPException(
            status_code=409,
            detail=structured_error_detail(
                code="publish_precheck_failed",
                message="无可发布榜单：请先启用至少一个榜单配置",
            ),
        )

    config_ids = [cfg.id for cfg in active_configs]
    enabled_settings = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.ranking_config_id.in_(config_ids),
            AppRankingSetting.is_enabled.is_(True),
        )
        .count()
    )
    if enabled_settings == 0:
        raise HTTPException(
            status_code=409,
            detail=structured_error_detail(
                code="publish_precheck_failed",
                message="无可发布应用：请先在“应用参与”中启用至少一个应用",
            ),
        )

    invalid_configs = []
    for config in active_configs:
        configured_dims = _collect_config_dimension_ids(config)
        if not configured_dims:
            invalid_configs.append(config.id)
    if invalid_configs:
        raise HTTPException(
            status_code=409,
            detail=structured_error_detail(
                code="publish_precheck_failed",
                message="存在未配置维度的启用榜单，请先完善榜单配置",
                field_errors=[{"field": "ranking_config_id", "message": cid} for cid in invalid_configs],
            ),
        )

    return {
        "active_configs": len(active_configs),
        "enabled_settings": enabled_settings,
    }


@app.post(f"{settings.api_prefix}/rankings/publish")
def publish_rankings(
    run_id: str | None = Query(default=None, description="可选发布批次ID；不传则自动生成 UUID"),
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    """榜单发布入口：预校验 + 同步 + 发布审计。"""
    try:
        checked = validate_publish_preconditions(db)
        updated_count, generated_run_id = sync_rankings_service(db, run_id=run_id)
        write_ranking_audit_log(
            db,
            action="ranking_publish_completed",
            ranking_type="all",
            ranking_config_id=None,
            period_date=datetime.utcnow().date(),
            run_id=generated_run_id,
            actor="system",
            payload_summary=(
                f"active_configs={checked['active_configs']},"
                f"enabled_settings={checked['enabled_settings']},"
                f"updated_count={updated_count}"
            ),
        )
        db.commit()
        return {
            "message": "榜单发布成功",
            "updated_count": updated_count,
            "run_id": generated_run_id,
            "published_date": datetime.utcnow().date().isoformat(),
            "checked": checked,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发布失败: {str(exc)}") from exc


@app.post(f"{settings.api_prefix}/apps/batch-update-ranking-params")
def batch_update_ranking_params(
    apps: list[int],
    ranking_weight: float = 1.0,
    ranking_enabled: bool = True,
    ranking_tags: str = "",
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    批量更新应用的排行榜参数
    """
    try:
        # 验证参数
        if ranking_weight < 0.1 or ranking_weight > 10.0:
            raise HTTPException(status_code=422, detail="ranking_weight must be between 0.1 and 10.0")
        if len(ranking_tags) > 255:
            raise HTTPException(status_code=422, detail="ranking_tags must not exceed 255 characters")
        if not apps:
            raise HTTPException(status_code=422, detail="apps list cannot be empty")
        
        updated_count = 0
        for app_id in apps:
            app = db.query(App).filter(App.id == app_id).first()
            if app:
                app.ranking_weight = ranking_weight
                app.ranking_enabled = ranking_enabled
                app.ranking_tags = ranking_tags
                app.last_ranking_update = datetime.utcnow()
                updated_count += 1
        
        synced, run_id = sync_after_chain_mutation(db, "batch_ranking_params_updated")
        return {"message": "批量更新成功", "updated_count": updated_count, "synced": synced, "run_id": run_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@app.post(f"{settings.api_prefix}/submissions/{{submission_id}}/approve-and-create-app")
def approve_submission_and_create_app(
    submission_id: int,
    request: Request,
    payload: SubmissionApprovePayload | None = None,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    审批申报并创建应用,同时传递排行榜参数
    只有通过审核的省内应用才能进入排行榜评估体系
    """
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="申报不存在")
        
        if submission.status != "pending":
            raise HTTPException(status_code=400, detail="申报状态不是待审批")

        resolved_status = (payload.status if payload and payload.status else "available")
        if resolved_status not in APP_STATUS_VALUES:
            raise HTTPException(status_code=422, detail="Invalid status")

        resolved_access_mode = (payload.access_mode if payload and payload.access_mode else "profile")
        if resolved_access_mode not in {"direct", "profile"}:
            raise HTTPException(status_code=422, detail="Invalid access_mode")

        normalized_name = normalize_dedupe_text(submission.app_name)
        normalized_unit = normalize_dedupe_text(submission.unit_name)
        existing_app = (
            db.query(App)
            .filter(
                App.section == "province",
                func.lower(func.trim(App.name)) == normalized_name,
                func.lower(func.trim(App.org)) == normalized_unit,
            )
            .first()
        )
        if existing_app:
            raise HTTPException(status_code=409, detail="已存在同名同单位省内应用，不能重复创建")

        submission_document = (
            db.query(SubmissionImage)
            .filter(
                SubmissionImage.submission_id == submission_id,
                SubmissionImage.is_cover.is_(False),
            )
            .order_by(SubmissionImage.created_at.desc())
            .first()
        )
        document_url = submission_document.image_url if submission_document else ""
        approved_at = datetime.utcnow()

        app = App(
            name=submission.app_name,
            org=submission.unit_name,
            section="province",
            category=submission.category,
            description=submission.scenario,
            status=resolved_status,
            monthly_calls=payload.monthly_calls if payload and payload.monthly_calls is not None else 0.0,
            release_date=datetime.now().date(),
            api_open=True,
            difficulty=(payload.difficulty.strip() if payload and payload.difficulty else "Medium"),
            contact_name=submission.contact,
            highlight="",
            access_mode=resolved_access_mode,
            access_url=(
                payload.access_url.strip()
                if payload and payload.access_url
                else ""
            ),
            detail_doc_url=submission.detail_doc_url or document_url,
            detail_doc_name=submission.detail_doc_name or (submission_document.original_name if submission_document else ""),
            target_system=(
                payload.target_system.strip()
                if payload and payload.target_system
                else submission.embedded_system
            ),
            target_users=(payload.target_users.strip() if payload and payload.target_users else ""),
            problem_statement=submission.problem_statement,
            effectiveness_type=submission.effectiveness_type,
            effectiveness_metric=submission.effectiveness_metric,
            cover_image_url=submission.cover_image_url,
            created_by_user_id=submission.submitter_user_id,
            created_from_submission_id=submission.id,
            approved_by_user_id=(admin_user.id if admin_user else None),
            approved_at=approved_at,
            ranking_enabled=False,
            ranking_weight=1.0,
            ranking_tags="",
        )

        db.add(app)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="检测到重复应用创建请求，已拒绝")

        active_configs = (
            db.query(RankingConfig)
            .filter(RankingConfig.is_active.is_(True))
            .all()
        )
        for config in active_configs:
            db.add(
                AppRankingSetting(
                    app_id=app.id,
                    ranking_config_id=config.id,
                    is_enabled=False,
                    weight_factor=1.0,
                    custom_tags="",
                )
            )

        submission.status = "approved"
        submission.approved_at = approved_at
        submission.approved_by_user_id = admin_user.id if admin_user else None
        submission.rejected_at = None
        submission.rejected_by_user_id = None
        submission.rejected_reason = ""
        write_action_log(
            db,
            action="submission.approve",
            actor_user=admin_user,
            resource_type="submission",
            resource_id=str(submission.id),
            request_id=request.headers.get("X-Request-Id", ""),
            payload_summary=f"app_id={app.id},app_name={app.name}",
        )
        updated_count, run_id = sync_after_chain_mutation(db, "submission_approved_and_created_app")
        db.refresh(app)

        return {
            "message": "审批成功并创建应用",
            "app_id": app.id,
            "synced": updated_count,
            "run_id": run_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@app.post(f"{settings.api_prefix}/submissions/{{submission_id}}/reject")
def reject_submission(
    submission_id: int,
    request: Request,
    reason: str | None = Body(default=None, embed=True),
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    拒绝申报
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="申报不存在")
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="仅待审核申报可拒绝")

    submission.status = "rejected"
    submission.rejected_reason = (reason or "").strip()
    submission.rejected_at = datetime.utcnow()
    submission.rejected_by_user_id = admin_user.id if admin_user else None
    submission.approved_at = None
    submission.approved_by_user_id = None
    write_action_log(
        db,
        action="submission.reject",
        actor_user=admin_user,
        resource_type="submission",
        resource_id=str(submission.id),
        request_id=request.headers.get("X-Request-Id", ""),
        payload_summary=f"reason={submission.rejected_reason}",
    )
    db.commit()
    return {
        "message": "申报已拒绝",
        "submission_id": submission_id,
        "reason": submission.rejected_reason,
    }


# 集团应用专用录入接口（仅管理员使用）
@app.post(f"{settings.api_prefix}/admin/group-apps", response_model=AppDetail)
def create_group_app(
    payload: GroupAppCreate,
    request: Request,
    admin_user: User | None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    集团应用专用录入接口
    集团应用为系统内置，通过此接口直接录入，不走申报流程
    """
    try:
        app = App(
            name=payload.name,
            org=payload.org,
            section="group",  # 集团应用
            category=payload.category,
            description=payload.description,
            status=payload.status,
            monthly_calls=payload.monthly_calls,
            release_date=datetime.now().date(),
            api_open=payload.api_open,
            difficulty=payload.difficulty,
            contact_name=payload.contact_name,
            highlight=payload.highlight,
            access_mode=payload.access_mode,
            access_url=payload.access_url,
            detail_doc_url="",
            detail_doc_name="",
            target_system=payload.target_system,
            target_users=payload.target_users,
            problem_statement=payload.problem_statement,
            effectiveness_type=payload.effectiveness_type,
            effectiveness_metric=payload.effectiveness_metric,
            cover_image_url=payload.cover_image_url,
            created_by_user_id=(admin_user.id if admin_user else None),
            created_from_submission_id=None,
            approved_by_user_id=(admin_user.id if admin_user else None),
            approved_at=datetime.utcnow(),
            ranking_enabled=False,
            ranking_weight=1.0,
            ranking_tags="",
        )
        db.add(app)
        db.flush()
        write_action_log(
            db,
            action="app.create_group",
            actor_user=admin_user,
            resource_type="app",
            resource_id=str(app.id),
            request_id=request.headers.get("X-Request-Id", ""),
            payload_summary=f"name={app.name},org={app.org}",
        )
        db.commit()
        db.refresh(app)
        return app
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建集团应用失败: {str(e)}")


# Image upload configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_DOC_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_DOC_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md"}


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


def validate_document(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded document file"""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_DOC_EXTENSIONS:
        return False, f"仅支持 {', '.join(sorted(ALLOWED_DOC_EXTENSIONS))} 格式的文档"
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
    base_url = f"{settings.api_prefix}/static/uploads"
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


def save_document(file: UploadFile) -> dict:
    """Save document file"""
    ext = Path(file.filename).suffix.lower()
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{unique_id}{ext}"

    save_dir = UPLOAD_DIR / "docs"
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / filename

    with open(file_path, "wb") as f:
        content = file.file.read()
        if len(content) > MAX_DOC_FILE_SIZE:
            raise HTTPException(status_code=413, detail="文档大小不能超过 20MB")
        f.write(content)

    file_url = f"{settings.api_prefix}/static/uploads/docs/{filename}"
    return {
        "file_url": file_url,
        "original_name": file.filename,
        "file_size": len(content),
        "mime_type": file.content_type or "",
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


@app.post(f"{settings.api_prefix}/upload/document", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload document file"""
    is_valid, error_msg = validate_document(file)
    if not is_valid:
        return DocumentUploadResponse(
            success=False,
            file_url="",
            original_name=file.filename,
            file_size=0,
            message=error_msg,
        )

    try:
        result = save_document(file)
        return DocumentUploadResponse(
            success=True,
            file_url=result["file_url"],
            original_name=result["original_name"],
            file_size=result["file_size"],
            message="文档上传成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        return DocumentUploadResponse(
            success=False,
            file_url="",
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
    mime_type: str = "",
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
        mime_type=mime_type,
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
            "mime_type": img.mime_type,
            "is_cover": img.is_cover,
            "created_at": img.created_at,
        }
        for img in images
    ]


# Mount static files
ensure_runtime_directories()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount(f"{settings.api_prefix}/static", StaticFiles(directory=str(STATIC_DIR)), name="api-static")


# ==================== 三层架构排行榜系统 API ====================

@app.get(f"{settings.api_prefix}/ranking-configs", response_model=list[RankingConfigOut])
def list_ranking_configs(
    is_active: bool | None = Query(default=None, description="按启用状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取榜单配置列表
    """
    query = db.query(RankingConfig)
    if is_active is not None:
        query = query.filter(RankingConfig.is_active == is_active)
    return query.order_by(RankingConfig.id).all()


@app.get(f"{settings.api_prefix}/ranking-configs/{{config_id}}", response_model=RankingConfigOut)
def get_ranking_config(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    获取榜单配置详情
    """
    config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")
    return config


@app.get(f"{settings.api_prefix}/ranking-configs/{{config_id}}/with-dimensions", response_model=RankingConfigWithDimensions)
def get_ranking_config_with_dimensions(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    获取榜单配置详情（包含维度配置）
    """
    config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")
    
    import json
    dimensions_config = json.loads(config.dimensions_config) if config.dimensions_config else []
    
    return {
        "id": config.id,
        "name": config.name,
        "description": config.description,
        "dimensions": [DimensionConfigItem(**d) for d in dimensions_config],
        "calculation_method": config.calculation_method,
        "is_active": config.is_active,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }


@app.post(f"{settings.api_prefix}/ranking-configs", response_model=RankingConfigOut)
def create_ranking_config(
    payload: RankingConfigCreate,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    创建榜单配置
    """
    # 检查ID是否已存在
    existing = db.query(RankingConfig).filter(RankingConfig.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="榜单配置ID已存在")
    
    config = RankingConfig(**payload.model_dump())
    db.add(config)
    db.flush()
    write_ranking_audit_log(
        db,
        action="ranking_config_created",
        ranking_type=config.id,
        ranking_config_id=config.id,
        period_date=datetime.utcnow().date(),
        actor="system",
        payload_summary=f"name={config.name},is_active={config.is_active}",
    )
    sync_after_chain_mutation(db, "ranking_config_created")
    db.refresh(config)
    return config


@app.put(f"{settings.api_prefix}/ranking-configs/{{config_id}}", response_model=RankingConfigOut)
def update_ranking_config(
    config_id: str,
    payload: RankingConfigUpdate,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新榜单配置
    """
    config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")
    
    if payload.name is not None:
        config.name = payload.name
    if payload.description is not None:
        config.description = payload.description
    if payload.dimensions_config is not None:
        config.dimensions_config = payload.dimensions_config
    if payload.calculation_method is not None:
        config.calculation_method = payload.calculation_method
    if payload.is_active is not None:
        config.is_active = payload.is_active

    write_ranking_audit_log(
        db,
        action="ranking_config_updated",
        ranking_type=config.id,
        ranking_config_id=config.id,
        period_date=datetime.utcnow().date(),
        actor="system",
        payload_summary="fields=name/description/dimensions_config/calculation_method/is_active",
    )
    sync_after_chain_mutation(db, "ranking_config_updated")
    db.refresh(config)
    return config


@app.delete(f"{settings.api_prefix}/ranking-configs/{{config_id}}")
def delete_ranking_config(
    config_id: str,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    删除榜单配置
    """
    config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")

    removed_settings = (
        db.query(AppRankingSetting)
        .filter(AppRankingSetting.ranking_config_id == config_id)
        .delete(synchronize_session=False)
    )
    removed_realtime = (
        db.query(Ranking)
        .filter(Ranking.ranking_config_id == config_id)
        .delete(synchronize_session=False)
    )
    removed_historical = (
        db.query(HistoricalRanking)
        .filter(HistoricalRanking.ranking_config_id == config_id)
        .delete(synchronize_session=False)
    )

    write_ranking_audit_log(
        db,
        action="ranking_config_deleted",
        ranking_type=config.id,
        ranking_config_id=config.id,
        period_date=datetime.utcnow().date(),
        actor="system",
        payload_summary=(
            f"name={config.name},removed_settings={removed_settings},"
            f"removed_realtime={removed_realtime},removed_historical={removed_historical}"
        ),
    )
    db.delete(config)
    synced, run_id = sync_after_chain_mutation(db, "ranking_config_deleted")
    return {
        "message": "榜单配置已删除",
        "removed_settings": removed_settings,
        "removed_realtime": removed_realtime,
        "removed_historical": removed_historical,
        "synced": synced,
        "run_id": run_id,
    }


@app.get(f"{settings.api_prefix}/apps/{{app_id}}/ranking-settings", response_model=list[AppRankingSettingOut])
def list_app_ranking_settings(
    app_id: int,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取应用的榜单设置列表
    """
    settings_list = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.app_id == app_id,
            AppRankingSetting.ranking_config_id.is_not(None),
        )
        .options(joinedload(AppRankingSetting.ranking_config))
        .all()
    )
    return settings_list


def _serialize_setting_snapshot(setting: AppRankingSetting | None) -> dict[str, object]:
    if setting is None:
        return {}
    return {
        "id": setting.id,
        "app_id": setting.app_id,
        "ranking_config_id": setting.ranking_config_id,
        "is_enabled": setting.is_enabled,
        "weight_factor": setting.weight_factor,
        "custom_tags": setting.custom_tags,
    }


def _collect_config_dimension_ids(config: RankingConfig) -> set[int]:
    config_dim_ids: set[int] = set()
    if not config.dimensions_config:
        return config_dim_ids
    try:
        dimensions_config = json.loads(config.dimensions_config)
    except json.JSONDecodeError:
        return config_dim_ids
    if not isinstance(dimensions_config, list):
        return config_dim_ids
    for item in dimensions_config:
        if isinstance(item, dict) and isinstance(item.get("dim_id"), int):
            config_dim_ids.add(item["dim_id"])
    return config_dim_ids


@app.post(
    f"{settings.api_prefix}/apps/{{app_id}}/ranking-settings/save",
    response_model=AppRankingSettingSaveResponse,
)
def save_app_ranking_setting_atomically(
    app_id: int,
    payload: AppRankingSettingSaveRequest,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    """原子保存应用榜单参与设置与维度评分，失败则整单回滚。"""
    try:
        app = db.query(App).filter(App.id == app_id).first()
        if not app:
            raise HTTPException(status_code=404, detail="应用不存在")

        config_id = payload.ranking_config_id.strip()
        if not config_id:
            raise HTTPException(
                status_code=422,
                detail=structured_error_detail(
                    code="validation_error",
                    message="参数校验失败",
                    field_errors=[{"field": "ranking_config_id", "message": "请选择榜单"}],
                ),
            )

        config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="榜单配置不存在")

        target_setting: AppRankingSetting | None = None
        if payload.setting_id is not None:
            target_setting = (
                db.query(AppRankingSetting)
                .filter(
                    AppRankingSetting.id == payload.setting_id,
                    AppRankingSetting.app_id == app_id,
                )
                .first()
            )
            if not target_setting:
                raise HTTPException(status_code=404, detail="榜单设置不存在")
        else:
            target_setting = (
                db.query(AppRankingSetting)
                .filter(
                    AppRankingSetting.app_id == app_id,
                    AppRankingSetting.ranking_config_id == config_id,
                )
                .first()
            )

        duplicate_setting = (
            db.query(AppRankingSetting)
            .filter(
                AppRankingSetting.app_id == app_id,
                AppRankingSetting.ranking_config_id == config_id,
                AppRankingSetting.id != (target_setting.id if target_setting else -1),
            )
            .first()
        )
        if duplicate_setting:
            raise HTTPException(status_code=409, detail="该应用已参与所选榜单，请直接编辑已有配置")

        config_dim_ids = _collect_config_dimension_ids(config)
        active_dims = {
            dim.id: dim
            for dim in db.query(RankingDimension)
            .filter(RankingDimension.id.in_(config_dim_ids))
            .filter(RankingDimension.is_active.is_(True))
            .all()
        } if config_dim_ids else {}

        field_errors: list[dict[str, str]] = []
        seen_dimension_ids: set[int] = set()
        for index, item in enumerate(payload.dimension_scores):
            field_prefix = f"dimension_scores[{index}]"
            if item.dimension_id in seen_dimension_ids:
                field_errors.append({"field": f"{field_prefix}.dimension_id", "message": "维度重复提交"})
                continue
            seen_dimension_ids.add(item.dimension_id)
            if item.dimension_id not in config_dim_ids:
                field_errors.append({"field": f"{field_prefix}.dimension_id", "message": "该维度不属于当前榜单配置"})
                continue
            if item.dimension_id not in active_dims:
                field_errors.append({"field": f"{field_prefix}.dimension_id", "message": "维度不存在或未启用"})

        if field_errors:
            raise HTTPException(
                status_code=422,
                detail=structured_error_detail(
                    code="validation_error",
                    message="参数校验失败",
                    field_errors=field_errors,
                ),
            )

        before_snapshot = _serialize_setting_snapshot(target_setting)
        if target_setting is None:
            target_setting = AppRankingSetting(
                app_id=app_id,
                ranking_config_id=config_id,
                is_enabled=payload.is_enabled,
                weight_factor=payload.weight_factor,
                custom_tags=payload.custom_tags,
            )
            db.add(target_setting)
            action = "app_ranking_setting_saved_created"
        else:
            target_setting.ranking_config_id = config_id
            target_setting.is_enabled = payload.is_enabled
            target_setting.weight_factor = payload.weight_factor
            target_setting.custom_tags = payload.custom_tags
            action = "app_ranking_setting_saved_updated"

        db.flush()
        today = datetime.now().date()
        updated_dimensions = 0
        for item in payload.dimension_scores:
            score_record = load_single_dimension_score(
                db,
                app_id=app_id,
                ranking_config_id=config_id,
                dimension_id=item.dimension_id,
                period_date=today,
            )
            dimension = active_dims[item.dimension_id]
            if score_record:
                score_record.score = item.score
                score_record.dimension_name = dimension.name
                score_record.weight = dimension.weight
                score_record.calculation_detail = f"手动调整评分: {item.score}分"
            else:
                db.add(
                    AppDimensionScore(
                        app_id=app_id,
                        ranking_config_id=config_id,
                        dimension_id=item.dimension_id,
                        dimension_name=dimension.name,
                        score=item.score,
                        weight=dimension.weight,
                        calculation_detail=f"手动调整评分: {item.score}分",
                        period_date=today,
                    )
                )
            updated_dimensions += 1

        after_snapshot = _serialize_setting_snapshot(target_setting)
        write_ranking_audit_log(
            db,
            action=action,
            ranking_type=config_id,
            ranking_config_id=config_id,
            period_date=datetime.utcnow().date(),
            actor="system",
            payload_summary=(
                f"app_id={app_id},before={json.dumps(before_snapshot, ensure_ascii=False)},"
                f"after={json.dumps(after_snapshot, ensure_ascii=False)},"
                f"updated_dimensions={updated_dimensions}"
            ),
        )
        synced, run_id = sync_after_chain_mutation(db, "app_ranking_setting_saved_atomic")
        db.refresh(target_setting)
        return {
            "setting": target_setting,
            "updated_dimensions": updated_dimensions,
            "synced": synced,
            "run_id": run_id,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存失败: {str(exc)}") from exc


@app.post(f"{settings.api_prefix}/apps/{{app_id}}/ranking-settings", response_model=AppRankingSettingOut)
def create_app_ranking_setting(
    app_id: int,
    payload: AppRankingSettingCreate,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    创建应用榜单设置
    """
    if not payload.ranking_config_id.strip():
        raise HTTPException(status_code=422, detail="ranking_config_id is required")

    # 检查应用是否存在
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 检查榜单配置是否存在
    config = db.query(RankingConfig).filter(RankingConfig.id == payload.ranking_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")
    
    # 检查是否已存在
    existing = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.app_id == app_id,
            AppRankingSetting.ranking_config_id == payload.ranking_config_id
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="该榜单设置已存在")
    
    setting = AppRankingSetting(
        app_id=app_id,
        **payload.model_dump()
    )
    db.add(setting)
    db.flush()
    write_ranking_audit_log(
        db,
        action="app_ranking_setting_created",
        ranking_type=payload.ranking_config_id,
        ranking_config_id=payload.ranking_config_id,
        period_date=datetime.utcnow().date(),
        actor="system",
        payload_summary=(
            f"app_id={app_id},before={{}},"
            f"after={json.dumps(_serialize_setting_snapshot(setting), ensure_ascii=False)}"
        ),
    )
    sync_after_chain_mutation(db, "app_ranking_setting_created")
    db.refresh(setting)
    return setting


@app.put(f"{settings.api_prefix}/apps/{{app_id}}/ranking-settings/{{setting_id}}", response_model=AppRankingSettingOut)
def update_app_ranking_setting(
    app_id: int,
    setting_id: int,
    payload: AppRankingSettingUpdate,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    更新应用榜单设置
    """
    setting = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.id == setting_id,
            AppRankingSetting.app_id == app_id
        )
        .first()
    )
    if not setting:
        raise HTTPException(status_code=404, detail="榜单设置不存在")

    before_snapshot = _serialize_setting_snapshot(setting)
    if payload.ranking_config_id is not None and payload.ranking_config_id != setting.ranking_config_id:
        new_config_id = payload.ranking_config_id.strip()
        if not new_config_id:
            raise HTTPException(status_code=422, detail="ranking_config_id must not be empty")

        config = db.query(RankingConfig).filter(RankingConfig.id == new_config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="榜单配置不存在")

        duplicate_setting = (
            db.query(AppRankingSetting)
            .filter(
                AppRankingSetting.app_id == app_id,
                AppRankingSetting.ranking_config_id == new_config_id,
                AppRankingSetting.id != setting_id,
            )
            .first()
        )
        if duplicate_setting:
            raise HTTPException(status_code=400, detail="该榜单设置已存在")

        setting.ranking_config_id = new_config_id

    if payload.is_enabled is not None:
        setting.is_enabled = payload.is_enabled
    if payload.weight_factor is not None:
        setting.weight_factor = payload.weight_factor
    if payload.custom_tags is not None:
        setting.custom_tags = payload.custom_tags

    after_snapshot = _serialize_setting_snapshot(setting)
    write_ranking_audit_log(
        db,
        action="app_ranking_setting_updated",
        ranking_type=setting.ranking_config_id,
        ranking_config_id=setting.ranking_config_id,
        period_date=datetime.utcnow().date(),
        actor="system",
        payload_summary=(
            f"app_id={app_id},before={json.dumps(before_snapshot, ensure_ascii=False)},"
            f"after={json.dumps(after_snapshot, ensure_ascii=False)}"
        ),
    )
    sync_after_chain_mutation(db, "app_ranking_setting_updated")
    db.refresh(setting)
    return setting


@app.delete(f"{settings.api_prefix}/apps/{{app_id}}/ranking-settings/{{setting_id}}")
def delete_app_ranking_setting(
    app_id: int,
    setting_id: int,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    删除应用榜单设置
    """
    setting = (
        db.query(AppRankingSetting)
        .filter(
            AppRankingSetting.id == setting_id,
            AppRankingSetting.app_id == app_id
        )
        .first()
    )
    if not setting:
        raise HTTPException(status_code=404, detail="榜单设置不存在")

    before_snapshot = _serialize_setting_snapshot(setting)
    write_ranking_audit_log(
        db,
        action="app_ranking_setting_deleted",
        ranking_type=setting.ranking_config_id,
        ranking_config_id=setting.ranking_config_id,
        period_date=datetime.utcnow().date(),
        actor="system",
        payload_summary=(
            f"app_id={app_id},before={json.dumps(before_snapshot, ensure_ascii=False)},"
            "after={}"
        ),
    )
    db.delete(setting)
    synced, run_id = sync_after_chain_mutation(db, "app_ranking_setting_deleted")
    return {"message": "榜单设置已删除", "synced": synced, "run_id": run_id}


@app.get(f"{settings.api_prefix}/app-ranking-settings", response_model=list[AppRankingSettingOut])
def list_all_app_ranking_settings(
    ranking_config_id: Optional[str] = None,
    _: None = Depends(require_admin_token),
    db: Session = Depends(get_db)
):
    """
    获取所有应用榜单设置列表（支持按榜单配置筛选）
    """
    query = db.query(AppRankingSetting).options(
        joinedload(AppRankingSetting.app),
        joinedload(AppRankingSetting.ranking_config)
    )

    query = query.filter(AppRankingSetting.ranking_config_id.is_not(None))

    if ranking_config_id:
        query = query.filter(AppRankingSetting.ranking_config_id == ranking_config_id)
    
    settings_list = query.all()
    return settings_list
