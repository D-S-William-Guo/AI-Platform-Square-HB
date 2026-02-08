from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from .config import settings
from .database import Base, engine, get_db
from .models import App, Ranking, Submission
from .schemas import (
    AppDetail,
    RankingItem,
    Recommendation,
    RuleLink,
    Stats,
    SubmissionCreate,
    SubmissionOut,
)
from .seed import seed_data

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
