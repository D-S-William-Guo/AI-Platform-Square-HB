import logging
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from sqlalchemy.orm import Session, joinedload

from pydantic_settings import BaseSettings


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "AI App Square API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./ai_app_square.db"
    oa_rule_base_url: str = "https://oa.example.internal"
    static_dir: str = "static"
    upload_dir: str = "static/uploads"
    image_dir: str = "static/images"


settings = Settings()


def resolve_runtime_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()

import sys
import types

config_module = types.ModuleType("app.config")
config_module.settings = settings
config_module.resolve_runtime_path = resolve_runtime_path
sys.modules.setdefault("app.config", config_module)

from .database import Base, engine, get_db
from .models import App, Ranking, Submission, SubmissionImage, RankingDimension, RankingLog, AppDimensionScore, HistoricalRanking, RankingConfig, AppRankingSetting
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
    RankingConfigCreate,
    RankingConfigUpdate,
    RankingConfigOut,
    AppRankingSettingCreate,
    AppRankingSettingUpdate,
    AppRankingSettingOut,
    DimensionConfigItem,
    RankingConfigWithDimensions,
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

app = FastAPI(title=settings.app_name)

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
    validate_submission_ranking_fields(
        payload.ranking_weight, payload.ranking_tags, payload.ranking_dimensions
    )


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




def sync_rankings_service(db: Session) -> int:
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
    
    for config in ranking_configs:
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
                
            # 根据榜单配置的维度权重计算得分（权威路径）
            for dim_config in config_dimensions:
                dim_id = dim_config.get("dim_id")
                weight = dim_config.get("weight", 1.0)

                dimension = dimension_map.get(dim_id)
                if not dimension:
                    continue

                dim_score, calc_detail = calculate_dimension_score(app, dimension)

                # 保存维度评分
                existing_score = (
                    db.query(AppDimensionScore)
                    .filter(
                        AppDimensionScore.app_id == app.id,
                        AppDimensionScore.dimension_id == dimension.id,
                        AppDimensionScore.period_date == today
                    )
                    .first()
                )
                
                if existing_score:
                    existing_score.score = dim_score
                    existing_score.weight = weight
                    existing_score.calculation_detail = calc_detail
                    existing_score.updated_at = datetime.utcnow()
                else:
                    db.add(
                        AppDimensionScore(
                            app_id=app.id,
                            dimension_id=dimension.id,
                            dimension_name=dimension.name,
                            score=dim_score,
                            weight=weight,
                            calculation_detail=calc_detail,
                            period_date=today
                        )
                    )
            
            # 应用权重因子
            final_score = calculate_three_layer_score(
                app=app,
                config_dimensions=config_dimensions,
                dimension_map=dimension_map,
                weight_factor=setting.weight_factor,
            )
            
            app_scores.append({
                "app": app,
                "setting": setting,
                "score": final_score
            })
        
        # 按得分排序
        app_scores.sort(key=lambda x: x["score"], reverse=True)
        
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
            
            # 保存历史榜单数据
            historical = (
                db.query(HistoricalRanking)
                .filter(
                    HistoricalRanking.ranking_config_id == config.id,
                    HistoricalRanking.app_id == app.id,
                    HistoricalRanking.period_date == today
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
            
            updated_count += 1
    
    db.commit()
    return updated_count


@app.on_event("startup")
def on_startup():
    ensure_runtime_directories()

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
    try:
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
        
        apps = query.order_by(App.id).all()
        return apps
    except Exception as e:
        # 数据库表结构可能不完整，返回简化的应用列表
        # 这里可以从数据库直接执行SQL查询，只获取存在的字段
        try:
            import sqlalchemy
            # 直接执行SQL查询，只选择基本字段
            result = db.execute(sqlalchemy.text("""
                SELECT id, name, org, section, category, description, status, monthly_calls, release_date,
                       api_open, difficulty, contact_name, highlight, access_mode, access_url,
                       target_system, target_users, problem_statement, effectiveness_type, effectiveness_metric,
                       cover_image_url
                FROM apps
                ORDER BY id
            """))
            
            # 构造应用列表
            apps = []
            for row in result:
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
                apps.append(app_dict)
            return apps
        except Exception:
            # 如果还是失败，返回空列表
            return []


@app.get(f"{settings.api_prefix}/apps/{{app_id}}", response_model=AppDetail)
def get_app_detail(app_id: int, db: Session = Depends(get_db)):
    try:
        item = db.query(App).filter(App.id == app_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="App not found")
        return item
    except Exception as e:
        # 数据库表结构可能不完整，使用SQL查询获取基本信息
        try:
            import sqlalchemy
            result = db.execute(sqlalchemy.text("""
                SELECT id, name, org, section, category, description, status, monthly_calls, release_date,
                       api_open, difficulty, contact_name, highlight, access_mode, access_url,
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
        except Exception:
            raise HTTPException(status_code=404, detail="App not found")


@app.get(f"{settings.api_prefix}/rankings", response_model=list[RankingItem])
def list_rankings(
    ranking_type: str = "excellent",
    period_date: date | None = Query(default=None, description="查询历史榜单日期，格式：YYYY-MM-DD。不传则返回最新一期历史榜单"),
    db: Session = Depends(get_db)
):
    """
    获取应用榜单
    - 榜单仅展示省内应用
    - 支持按日期查询历史榜单
    - 不传日期则返回最新一期的历史榜单数据
    """
    try:
        if period_date:
            # 查询指定日期的历史榜单
            historical_rankings = (
                db.query(HistoricalRanking)
                .filter(HistoricalRanking.ranking_type == ranking_type)
                .filter(HistoricalRanking.period_date == period_date)
                .order_by(HistoricalRanking.position)
                .all()
            )
            
            # 转换为 RankingItem 格式
            result = []
            for hr in historical_rankings:
                app = db.query(App).filter(App.id == hr.app_id).first()
                if app and app.section == "province":
                    result.append({
                        "position": hr.position,
                        "tag": hr.tag,
                        "score": hr.score,
                        "likes": None,
                        "metric_type": hr.metric_type,
                        "value_dimension": hr.value_dimension,
                        "usage_30d": hr.usage_30d,
                        "declared_at": hr.period_date,
                        "app": app
                    })
            return result
        else:
            # 查询最新一期的历史榜单
            latest_date = (
                db.query(HistoricalRanking.period_date)
                .filter(HistoricalRanking.ranking_type == ranking_type)
                .order_by(HistoricalRanking.period_date.desc())
                .first()
            )
            
            if latest_date:
                # 使用最新日期查询
                historical_rankings = (
                    db.query(HistoricalRanking)
                    .filter(HistoricalRanking.ranking_type == ranking_type)
                    .filter(HistoricalRanking.period_date == latest_date[0])
                    .order_by(HistoricalRanking.position)
                    .all()
                )
                
                # 转换为 RankingItem 格式
                result = []
                for hr in historical_rankings:
                    app = db.query(App).filter(App.id == hr.app_id).first()
                    if app and app.section == "province":
                        result.append({
                            "position": hr.position,
                            "tag": hr.tag,
                            "score": hr.score,
                            "likes": None,
                            "metric_type": hr.metric_type,
                            "value_dimension": hr.value_dimension,
                            "usage_30d": hr.usage_30d,
                            "declared_at": hr.period_date,
                            "app": app
                        })
                return result
            else:
                # 没有历史数据，返回空列表
                return []
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
    status: str | None = Query(default=None, description="按状态筛选：pending, approved, rejected"),
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
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db)):
    validate_submission_payload(payload)
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
    db: Session = Depends(get_db)
):
    """
    获取指定维度的应用评分列表
    """
    try:
        query = db.query(AppDimensionScore).filter(AppDimensionScore.dimension_id == dimension_id)
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
    db: Session = Depends(get_db)
):
    """
    获取指定应用在各维度的评分详情
    """
    try:
        query = db.query(AppDimensionScore).filter(AppDimensionScore.app_id == app_id)
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
    db: Session = Depends(get_db)
):
    """
    更新应用排行参数
    """
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    if ranking_enabled is not None:
        app.ranking_enabled = ranking_enabled
    if ranking_weight is not None:
        app.ranking_weight = ranking_weight
    if ranking_tags is not None:
        app.ranking_tags = ranking_tags
    
    db.commit()
    db.refresh(app)
    return {"message": "排行参数更新成功", "app_id": app_id}


@app.put(f"{settings.api_prefix}/apps/{{app_id}}/dimension-scores/{{dimension_id}}")
def update_app_dimension_score_api(
    app_id: int,
    dimension_id: int,
    score: int,
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
    
    today = datetime.now().date()
    
    # 查找或创建评分记录
    score_record = db.query(AppDimensionScore).filter(
        AppDimensionScore.app_id == app_id,
        AppDimensionScore.dimension_id == dimension_id,
        AppDimensionScore.period_date == today
    ).first()
    
    if score_record:
        score_record.score = score
        score_record.calculation_detail = f"手动调整评分: {score}分"
    else:
        score_record = AppDimensionScore(
            app_id=app_id,
            dimension_id=dimension_id,
            period_date=today,
            score=score,
            calculation_detail=f"手动调整评分: {score}分"
        )
        db.add(score_record)
    
    db.commit()
    db.refresh(score_record)
    return {"message": "维度评分更新成功", "app_id": app_id, "dimension_id": dimension_id, "score": score}


@app.get(f"{settings.api_prefix}/rankings/historical", response_model=list[HistoricalRankingOut])
def list_historical_rankings(
    ranking_type: str = "excellent",
    period_date: date | None = Query(default=None, description="查询日期，格式：YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取历史榜单数据
    """
    try:
        query = db.query(HistoricalRanking).filter(HistoricalRanking.ranking_type == ranking_type)
        if period_date:
            query = query.filter(HistoricalRanking.period_date == period_date)
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
        dates = (
            db.query(HistoricalRanking.period_date)
            .filter(HistoricalRanking.ranking_type == ranking_type)
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
    db.commit()
    db.refresh(dimension)
    
    # 记录日志
    log = RankingLog(
        action="create",
        dimension_id=dimension.id,
        dimension_name=dimension.name,
        changes=f"创建了排行维度: {dimension.name}",
        operator="system"
    )
    db.add(log)
    db.commit()
    
    return dimension


@app.put(f"{settings.api_prefix}/ranking-dimensions/{{dimension_id}}", response_model=RankingDimensionOut)
def update_ranking_dimension(
    dimension_id: int,
    payload: RankingDimensionUpdate,
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
    if payload.name and payload.name != dimension.name:
        changes.append(f"名称: {dimension.name} → {payload.name}")
        dimension.name = payload.name
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
    
    # 保存更新
    db.commit()
    db.refresh(dimension)
    
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
        db.commit()
    
    return dimension


@app.delete(f"{settings.api_prefix}/ranking-dimensions/{{dimension_id}}")
def delete_ranking_dimension(
    dimension_id: int,
    db: Session = Depends(get_db)
):
    """
    删除排行维度
    """
    dimension = db.query(RankingDimension).filter(RankingDimension.id == dimension_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="排行维度不存在")
    
    # 记录日志
    log = RankingLog(
        action="delete",
        dimension_id=dimension.id,
        dimension_name=dimension.name,
        changes=f"删除了排行维度: {dimension.name}",
        operator="system"
    )
    db.add(log)
    
    # 删除排行维度
    db.delete(dimension)
    db.commit()
    
    return {"message": "排行维度已删除"}


@app.get(f"{settings.api_prefix}/ranking-logs", response_model=list[RankingLogOut])
def get_ranking_logs(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取排行维度变更日志
    """
    return db.query(RankingLog).order_by(RankingLog.created_at.desc()).limit(limit).all()


# 数据联动 API

@app.post(f"{settings.api_prefix}/rankings/sync")
def sync_rankings(db: Session = Depends(get_db)):
    """
    同步排行榜数据，确保集团应用和省内应用信息保持一致
    """
    try:
        updated_count = sync_rankings_service(db)
        return {"message": "排行榜数据同步成功", "updated_count": updated_count}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"同步失败: {str(exc)}") from exc


@app.post(f"{settings.api_prefix}/apps/batch-update-ranking-params")
def batch_update_ranking_params(
    apps: list[int],
    ranking_weight: float = 1.0,
    ranking_enabled: bool = True,
    ranking_tags: str = "",
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
        
        db.commit()
        
        return {"message": "批量更新成功", "updated_count": updated_count}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@app.post(f"{settings.api_prefix}/submissions/{{submission_id}}/approve-and-create-app")
def approve_submission_and_create_app(
    submission_id: int,
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

        validate_submission_ranking_fields(submission.ranking_weight, submission.ranking_tags, submission.ranking_dimensions)

        app = App(
            name=submission.app_name,
            org=submission.unit_name,
            section="province",
            category=submission.category,
            description=submission.scenario,
            status="available",
            monthly_calls=0.0,
            release_date=datetime.now().date(),
            api_open=True,
            difficulty="Medium",
            contact_name=submission.contact,
            highlight="",
            access_mode="direct",
            target_users="",
            problem_statement=submission.problem_statement,
            effectiveness_type=submission.effectiveness_type,
            effectiveness_metric=submission.effectiveness_metric,
            cover_image_url=submission.cover_image_url,
            ranking_enabled=submission.ranking_enabled,
            ranking_weight=submission.ranking_weight,
            ranking_tags=submission.ranking_tags,
        )

        db.add(app)
        submission.status = "approved"
        db.commit()
        db.refresh(app)
        
        # 自动同步排行榜数据
        sync_rankings_service(db)
        
        return {"message": "审批成功并创建应用", "app_id": app.id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


# 集团应用专用录入接口（仅管理员使用）
@app.post(f"{settings.api_prefix}/admin/group-apps", response_model=AppDetail)
def create_group_app(
    payload: GroupAppCreate,
    admin_token: str = Query(..., description="管理员令牌"),
    db: Session = Depends(get_db)
):
    """
    集团应用专用录入接口
    集团应用为系统内置，通过此接口直接录入，不走申报流程
    """
    # 简单的管理员令牌验证（生产环境应使用更安全的认证方式）
    if admin_token != "admin-secret-token":
        raise HTTPException(status_code=403, detail="无权限访问")
    
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
            target_system=payload.target_system,
            target_users=payload.target_users,
            problem_statement=payload.problem_statement,
            effectiveness_type=payload.effectiveness_type,
            effectiveness_metric=payload.effectiveness_metric,
            cover_image_url=payload.cover_image_url,
            ranking_enabled=payload.ranking_enabled,
            ranking_weight=payload.ranking_weight,
            ranking_tags=payload.ranking_tags,
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        return app
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建集团应用失败: {str(e)}")


# Image upload configuration
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
ensure_runtime_directories()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


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
    db.commit()
    db.refresh(config)
    return config


@app.put(f"{settings.api_prefix}/ranking-configs/{{config_id}}", response_model=RankingConfigOut)
def update_ranking_config(
    config_id: str,
    payload: RankingConfigUpdate,
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
    
    db.commit()
    db.refresh(config)
    return config


@app.delete(f"{settings.api_prefix}/ranking-configs/{{config_id}}")
def delete_ranking_config(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    删除榜单配置
    """
    config = db.query(RankingConfig).filter(RankingConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="榜单配置不存在")
    
    db.delete(config)
    db.commit()
    return {"message": "榜单配置已删除"}


@app.get(f"{settings.api_prefix}/apps/{{app_id}}/ranking-settings", response_model=list[AppRankingSettingOut])
def list_app_ranking_settings(
    app_id: int,
    db: Session = Depends(get_db)
):
    """
    获取应用的榜单设置列表
    """
    settings_list = (
        db.query(AppRankingSetting)
        .filter(AppRankingSetting.app_id == app_id)
        .options(joinedload(AppRankingSetting.ranking_config))
        .all()
    )
    return settings_list


@app.post(f"{settings.api_prefix}/apps/{{app_id}}/ranking-settings", response_model=AppRankingSettingOut)
def create_app_ranking_setting(
    app_id: int,
    payload: AppRankingSettingCreate,
    db: Session = Depends(get_db)
):
    """
    创建应用榜单设置
    """
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
    db.commit()
    db.refresh(setting)
    return setting


@app.put(f"{settings.api_prefix}/apps/{{app_id}}/ranking-settings/{{setting_id}}", response_model=AppRankingSettingOut)
def update_app_ranking_setting(
    app_id: int,
    setting_id: int,
    payload: AppRankingSettingUpdate,
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
    
    if payload.is_enabled is not None:
        setting.is_enabled = payload.is_enabled
    if payload.weight_factor is not None:
        setting.weight_factor = payload.weight_factor
    if payload.custom_tags is not None:
        setting.custom_tags = payload.custom_tags
    
    db.commit()
    db.refresh(setting)
    return setting


@app.delete(f"{settings.api_prefix}/apps/{{app_id}}/ranking-settings/{{setting_id}}")
def delete_app_ranking_setting(
    app_id: int,
    setting_id: int,
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
    
    db.delete(setting)
    db.commit()
    return {"message": "榜单设置已删除"}


@app.get(f"{settings.api_prefix}/app-ranking-settings", response_model=list[AppRankingSettingOut])
def list_all_app_ranking_settings(
    ranking_config_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取所有应用榜单设置列表（支持按榜单配置筛选）
    """
    query = db.query(AppRankingSetting).options(
        joinedload(AppRankingSetting.app),
        joinedload(AppRankingSetting.ranking_config)
    )
    
    if ranking_config_id:
        query = query.filter(AppRankingSetting.ranking_config_id == ranking_config_id)
    
    settings_list = query.all()
    return settings_list
