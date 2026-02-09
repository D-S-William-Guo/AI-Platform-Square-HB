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
from .models import App, Ranking, Submission, SubmissionImage, RankingDimension, RankingLog
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
def list_rankings(ranking_type: str = "excellent", db: Session = Depends(get_db)):
    try:
        return (
            db.query(Ranking)
            .options(joinedload(Ranking.app))
            .filter(Ranking.ranking_type == ranking_type)
            .order_by(Ranking.position)
            .all()
        )
    except Exception as e:
        # 数据库表结构可能不完整，返回空列表
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


@app.post(f"{settings.api_prefix}/submissions", response_model=SubmissionOut)
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db)):
    if payload.effectiveness_type not in VALUE_DIMENSIONS:
        raise HTTPException(status_code=422, detail="Invalid effectiveness_type")
    if payload.data_level not in DATA_LEVEL_VALUES:
        raise HTTPException(status_code=422, detail="Invalid data_level")
    
    # 验证排行榜相关字段
    if payload.ranking_weight < 0.1 or payload.ranking_weight > 10.0:
        raise HTTPException(status_code=422, detail="ranking_weight must be between 0.1 and 10.0")
    if len(payload.ranking_tags) > 255:
        raise HTTPException(status_code=422, detail="ranking_tags must not exceed 255 characters")
    if len(payload.ranking_dimensions) > 500:
        raise HTTPException(status_code=422, detail="ranking_dimensions must not exceed 500 characters")

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
        import sqlalchemy
        
        # 检查并创建必要的数据库表
        try:
            # 检查rankings表是否存在
            db.execute(sqlalchemy.text("SELECT 1 FROM rankings LIMIT 1"))
        except:
            # 创建rankings表
            db.execute(sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ranking_type VARCHAR(50) NOT NULL,
                    position INTEGER NOT NULL,
                    app_id INTEGER NOT NULL,
                    tag VARCHAR(50) NOT NULL,
                    score INTEGER NOT NULL,
                    likes INTEGER DEFAULT 0,
                    metric_type VARCHAR(50) DEFAULT 'composite',
                    value_dimension VARCHAR(50) DEFAULT 'efficiency_gain',
                    usage_30d INTEGER DEFAULT 0,
                    declared_at DATE NOT NULL,
                    updated_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (app_id) REFERENCES apps (id)
                )
            """))
            db.commit()
        
        try:
            # 检查ranking_dimensions表是否存在
            db.execute(sqlalchemy.text("SELECT 1 FROM ranking_dimensions LIMIT 1"))
        except:
            # 创建ranking_dimensions表
            db.execute(sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS ranking_dimensions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    calculation_method TEXT,
                    weight FLOAT DEFAULT 1.0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.commit()
            
            # 插入默认排行维度
            default_dimensions = [
                {"name": "用户满意度", "description": "基于用户反馈和使用数据评估应用的满意度", "calculation_method": "基于应用的月调用量和用户评分计算", "weight": 3.0, "is_active": True},
                {"name": "业务价值", "description": "评估应用对业务的提升作用", "calculation_method": "基于应用的成效类型和指标计算", "weight": 2.5, "is_active": True},
                {"name": "技术创新性", "description": "评估应用的技术方案和创新点", "calculation_method": "基于应用的难度等级计算", "weight": 2.0, "is_active": True},
                {"name": "使用活跃度", "description": "评估应用的使用频率和用户活跃度", "calculation_method": "基于应用的月调用量计算", "weight": 1.5, "is_active": True},
                {"name": "稳定性和安全性", "description": "评估应用的可靠性和安全性", "calculation_method": "基于应用的状态和错误率计算", "weight": 1.0, "is_active": True}
            ]
            
            for dim in default_dimensions:
                db.execute(sqlalchemy.text("""
                    INSERT INTO ranking_dimensions (name, description, calculation_method, weight, is_active)
                    VALUES (:name, :description, :calculation_method, :weight, :is_active)
                """), dim)
            db.commit()
        
        # 直接执行SQL查询获取应用数据，避免使用ORM导致的字段问题
        result = db.execute(sqlalchemy.text("""
            SELECT id, name, org, section, category, description, status, monthly_calls, release_date,
                   api_open, difficulty, contact_name, highlight, access_mode, access_url,
                   target_system, target_users, problem_statement, effectiveness_type, effectiveness_metric,
                   cover_image_url
            FROM apps
        """))
        
        # 构造应用对象列表
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
                "ranking_enabled": True,
                "ranking_weight": 1.0,
                "ranking_tags": "",
                "last_ranking_update": None
            }
            apps.append(app_dict)
        
        updated_count = 0
        
        # 获取所有活跃的排行维度
        dimensions = []
        try:
            dim_result = db.execute(sqlalchemy.text("""
                SELECT id, name, description, calculation_method, weight, is_active
                FROM ranking_dimensions
                WHERE is_active = 1
            """))
            for row in dim_result:
                dimensions.append({
                    "id": row.id,
                    "name": row.name,
                    "description": row.description,
                    "calculation_method": row.calculation_method,
                    "weight": row.weight,
                    "is_active": row.is_active
                })
        except:
            # 如果维度表不存在，使用默认维度
            dimensions = []
        
        # 为每个应用创建或更新排行榜记录
        for app in apps:
            # 计算得分
            try:
                # 基于多个维度计算得分
                base_score = 0
                
                # 基于月调用量计算基础得分
                base_score += min(int(app['monthly_calls'] * 10), 100) * 0.3
                
                # 基于状态计算得分
                if app['status'] == 'available':
                    base_score += 100 * 0.2
                elif app['status'] == 'beta':
                    base_score += 80 * 0.2
                else:
                    base_score += 60 * 0.2
                
                # 基于难度计算得分
                if app['difficulty'] == 'High':
                    base_score += 100 * 0.2
                elif app['difficulty'] == 'Medium':
                    base_score += 70 * 0.2
                else:
                    base_score += 40 * 0.2
                
                # 基于成效类型计算得分
                if app['effectiveness_type'] == 'revenue_growth':
                    base_score += 100 * 0.1
                elif app['effectiveness_type'] == 'efficiency_gain':
                    base_score += 80 * 0.1
                elif app['effectiveness_type'] == 'cost_reduction':
                    base_score += 70 * 0.1
                else:
                    base_score += 60 * 0.1
                
                score = int(base_score)
            except Exception as e:
                print(f"Error calculating score for app {app['id']}: {e}")
                # 如果计算失败，使用默认得分
                score = 50
            
            # 检查是否已存在排行榜记录
            try:
                existing = db.execute(sqlalchemy.text("""
                    SELECT id FROM rankings WHERE app_id = :app_id AND ranking_type = 'excellent'
                """), {"app_id": app['id']})
                existing_id = existing.scalar()
                
                if existing_id:
                    # 更新现有记录
                    db.execute(sqlalchemy.text("""
                        UPDATE rankings SET score = :score, updated_at = :updated_at
                        WHERE id = :id
                    """), {
                        "score": score,
                        "updated_at": datetime.utcnow(),
                        "id": existing_id
                    })
                else:
                    # 获取下一个位置
                    try:
                        max_pos = db.execute(sqlalchemy.text("""
                            SELECT COUNT(*) FROM rankings WHERE ranking_type = 'excellent'
                        """)).scalar()
                        position = max_pos + 1
                    except Exception as e:
                        print(f"Error getting max position: {e}")
                        position = 1
                    
                    # 创建新记录
                    try:
                        db.execute(sqlalchemy.text("""
                            INSERT INTO rankings (ranking_type, position, app_id, tag, score, metric_type, value_dimension, usage_30d, declared_at, updated_at)
                            VALUES (:ranking_type, :position, :app_id, :tag, :score, :metric_type, :value_dimension, :usage_30d, :declared_at, :updated_at)
                        """), {
                            "ranking_type": "excellent",
                            "position": position,
                            "app_id": app['id'],
                            "tag": "推荐",
                            "score": score,
                            "metric_type": "composite",
                            "value_dimension": app['effectiveness_type'],
                            "usage_30d": 0,
                            "declared_at": datetime.now().date(),
                            "updated_at": datetime.utcnow()
                        })
                    except Exception as e:
                        print(f"Error inserting ranking for app {app['id']}: {e}")
                        continue
                updated_count += 1
            except Exception as e:
                print(f"Error processing app {app['id']}: {e}")
                continue
        
        # 重新排序排行榜
        try:
            # 获取所有排行记录并按得分排序
            rank_result = db.execute(sqlalchemy.text("""
                SELECT id, score FROM rankings WHERE ranking_type = 'excellent' ORDER BY score DESC
            """))
            
            # 更新位置
            for i, row in enumerate(rank_result, 1):
                db.execute(sqlalchemy.text("""
                    UPDATE rankings SET position = :position WHERE id = :id
                """), {
                    "position": i,
                    "id": row.id
                })
        except Exception as e:
            print(f"Error reordering rankings: {e}")
        
        db.commit()
        
        return {"message": "排行榜数据同步成功", "updated_count": updated_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


def calculate_app_score(app: App, db: Session) -> int:
    """
    计算应用的排行榜得分
    """
    # 获取所有活跃的排行维度
    active_dimensions = db.query(RankingDimension).filter(RankingDimension.is_active == True).all()
    
    # 基础得分
    base_score = 0
    
    # 根据维度计算得分
    for dimension in active_dimensions:
        # 这里可以根据实际情况实现具体的维度得分计算逻辑
        # 例如：基于应用的使用数据、用户反馈等计算得分
        dimension_score = 0
        
        # 根据维度类型计算得分
        if dimension.name == "用户满意度":
            # 假设用户满意度得分基于应用的使用数据
            dimension_score = min(int(app.monthly_calls * 10), 100)
        elif dimension.name == "业务价值":
            # 假设业务价值得分基于应用的成效类型
            if app.effectiveness_type == "revenue_growth":
                dimension_score = 100
            elif app.effectiveness_type == "efficiency_gain":
                dimension_score = 80
            elif app.effectiveness_type == "cost_reduction":
                dimension_score = 70
            else:
                dimension_score = 60
        elif dimension.name == "技术创新性":
            # 假设技术创新性得分基于应用的难度
            if app.difficulty == "High":
                dimension_score = 100
            elif app.difficulty == "Medium":
                dimension_score = 70
            else:
                dimension_score = 40
        elif dimension.name == "使用活跃度":
            # 假设使用活跃度得分基于应用的月调用量
            dimension_score = min(int(app.monthly_calls * 5), 100)
        elif dimension.name == "稳定性和安全性":
            # 假设稳定性和安全性得分基于应用的状态
            if app.status == "available":
                dimension_score = 100
            elif app.status == "beta":
                dimension_score = 80
            else:
                dimension_score = 60
        else:
            # 默认得分
            dimension_score = 50
        
        # 加权计算
        base_score += dimension_score * dimension.weight
    
    # 应用自身权重调整
    final_score = int(base_score * app.ranking_weight)
    
    # 确保得分在合理范围内
    return max(0, min(final_score, 1000))


def get_next_position(db: Session) -> int:
    """
    获取下一个排名位置
    """
    # 获取当前最大位置
    max_position = db.query(Ranking).filter(Ranking.ranking_type == "excellent").count()
    return max_position + 1


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
    """
    try:
        # 获取申报信息
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="申报不存在")
        
        if submission.status != "pending":
            raise HTTPException(status_code=400, detail="申报状态不是待审批")
        
        # 验证排行榜参数
        if submission.ranking_weight < 0.1 or submission.ranking_weight > 10.0:
            raise HTTPException(status_code=422, detail="ranking_weight must be between 0.1 and 10.0")
        if len(submission.ranking_tags) > 255:
            raise HTTPException(status_code=422, detail="ranking_tags must not exceed 255 characters")
        if len(submission.ranking_dimensions) > 500:
            raise HTTPException(status_code=422, detail="ranking_dimensions must not exceed 500 characters")
        
        # 创建应用
        app = App(
            name=submission.app_name,
            org=submission.unit_name,
            section="province",  # 省内应用
            category=submission.category,
            description=submission.scenario,
            status="available",
            monthly_calls=0.0,
            release_date=datetime.now().date(),
            effectiveness_type=submission.effectiveness_type,
            effectiveness_metric=submission.effectiveness_metric,
            # 传递排行榜参数
            ranking_enabled=submission.ranking_enabled,
            ranking_weight=submission.ranking_weight,
            ranking_tags=submission.ranking_tags
        )
        
        db.add(app)
        submission.status = "approved"
        db.commit()
        
        return {"message": "审批成功并创建应用", "app_id": app.id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


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