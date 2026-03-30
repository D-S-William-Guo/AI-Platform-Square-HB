import uuid
from datetime import date, datetime

from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    chinese_name: Mapped[str] = mapped_column(String(80), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")  # user | admin
    phone: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    department: Mapped[str] = mapped_column(String(120), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    can_submit: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("AuthSession", back_populates="user")
    action_logs = relationship("ActionLog", back_populates="actor_user")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    token_jti: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ip: Mapped[str] = mapped_column(String(80), default="")
    user_agent: Mapped[str] = mapped_column(String(255), default="")

    user = relationship("User", back_populates="sessions")


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    actor_role: Mapped[str] = mapped_column(String(20), default="")
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(80), default="")
    resource_id: Mapped[str] = mapped_column(String(80), default="")
    request_id: Mapped[str] = mapped_column(String(64), default="")
    payload_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    actor_user = relationship("User", back_populates="action_logs")


class App(Base):
    __tablename__ = "apps"
    __table_args__ = (
        UniqueConstraint("section", "name", "org", name="uq_apps_section_name_org"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    org: Mapped[str] = mapped_column(String(60), nullable=False)
    section: Mapped[str] = mapped_column(String(20), nullable=False)  # group | province
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # available | approval | beta | offline
    monthly_calls: Mapped[float] = mapped_column(Float, nullable=False)
    release_date: Mapped[date] = mapped_column(Date, nullable=False)
    api_open: Mapped[bool] = mapped_column(Boolean, default=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="Low")
    contact_name: Mapped[str] = mapped_column(String(50), default="")
    highlight: Mapped[str] = mapped_column(String(200), default="")
    access_mode: Mapped[str] = mapped_column(String(20), default="direct")  # direct | profile
    access_url: Mapped[str] = mapped_column(String(255), default="")
    detail_doc_url: Mapped[str] = mapped_column(String(500), default="")
    detail_doc_name: Mapped[str] = mapped_column(String(255), default="")
    target_system: Mapped[str] = mapped_column(String(120), default="")
    target_users: Mapped[str] = mapped_column(String(120), default="")
    problem_statement: Mapped[str] = mapped_column(String(255), default="")
    effectiveness_type: Mapped[str] = mapped_column(String(40), default="cost_reduction")
    effectiveness_metric: Mapped[str] = mapped_column(String(120), default="")
    cover_image_url: Mapped[str] = mapped_column(String(500), default="")
    # 用户关联字段（审计与追溯）
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_from_submission_id: Mapped[int | None] = mapped_column(ForeignKey("submissions.id"), nullable=True, index=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 排行榜相关字段
    ranking_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    ranking_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=True)
    ranking_tags: Mapped[str] = mapped_column(String(255), default="", nullable=True)
    last_ranking_update: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 新增增长指标字段
    last_month_calls: Mapped[float] = mapped_column(Float, default=0.0, nullable=True)
    new_users_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    search_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    # 关联关系
    rankings = relationship("Ranking", back_populates="app")
    ranking_settings = relationship("AppRankingSetting", back_populates="app")


class Ranking(Base):
    __tablename__ = "rankings"
    __table_args__ = (
        UniqueConstraint("ranking_config_id", "app_id", name="uq_rankings_config_app"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 外键关联榜单配置
    ranking_config_id: Mapped[str] = mapped_column(ForeignKey("ranking_configs.id"), nullable=False)
    # 保留 ranking_type 用于快速识别和兼容旧代码
    ranking_type: Mapped[str] = mapped_column(String(20), nullable=False)  # excellent | trend
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), nullable=False)
    tag: Mapped[str] = mapped_column(String(20), default="推荐")
    score: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metric_type: Mapped[str] = mapped_column(String(20), default="composite")  # composite | growth_rate | likes
    value_dimension: Mapped[str] = mapped_column(String(40), default="cost_reduction")
    usage_30d: Mapped[int] = mapped_column(Integer, default=0)
    declared_at: Mapped[date] = mapped_column(Date, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 关联关系
    app = relationship("App", back_populates="rankings")
    ranking_config = relationship("RankingConfig", back_populates="rankings")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("app_name", "unit_name", "status", name="uq_submissions_name_unit_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit_name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact: Mapped[str] = mapped_column(String(80), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), default="")
    contact_email: Mapped[str] = mapped_column(String(120), default="")
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    scenario: Mapped[str] = mapped_column(String(500), nullable=False)
    embedded_system: Mapped[str] = mapped_column(String(120), nullable=False)
    problem_statement: Mapped[str] = mapped_column(String(255), nullable=False)
    effectiveness_type: Mapped[str] = mapped_column(String(40), nullable=False)
    effectiveness_metric: Mapped[str] = mapped_column(String(120), nullable=False)
    data_level: Mapped[str] = mapped_column(String(10), nullable=False)
    expected_benefit: Mapped[str] = mapped_column(String(300), nullable=False)
    monthly_calls: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty: Mapped[str] = mapped_column(String(20), default="Medium")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    submitter_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejected_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejected_reason: Mapped[str] = mapped_column(String(255), default="")
    manage_token: Mapped[str] = mapped_column(String(64), default=lambda: uuid.uuid4().hex, nullable=False)
    cover_image_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_image_url: Mapped[str] = mapped_column(String(500), default="")
    detail_doc_url: Mapped[str] = mapped_column(String(500), default="")
    detail_doc_name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 排行榜相关字段
    ranking_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ranking_weight: Mapped[float] = mapped_column(Float, default=1.0)
    ranking_tags: Mapped[str] = mapped_column(String(255), default="")
    ranking_dimensions: Mapped[str] = mapped_column(String(500), default="")  # 逗号分隔的维度ID列表


class SubmissionImage(Base):
    __tablename__ = "submission_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(500), default="")
    original_name: Mapped[str] = mapped_column(String(255), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String(50), default="")
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    submission = relationship("Submission")


class RankingDimension(Base):
    __tablename__ = "ranking_dimensions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    calculation_method: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RankingLog(Base):
    __tablename__ = "ranking_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # create | update | delete
    dimension_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dimension_name: Mapped[str] = mapped_column(String(100), nullable=False)
    changes: Mapped[str] = mapped_column(Text, nullable=False)
    operator: Mapped[str] = mapped_column(String(100), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RankingAuditLog(Base):
    """排行榜审计日志（面向 HistoricalRanking 真相源链路）"""
    __tablename__ = "ranking_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    ranking_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ranking_config_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    period_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor: Mapped[str] = mapped_column(String(100), default="system")
    payload_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AppDimensionScore(Base):
    """应用在各维度的评分数据"""
    __tablename__ = "app_dimension_scores"
    __table_args__ = (
        UniqueConstraint(
            "app_id",
            "ranking_config_id",
            "dimension_id",
            "period_date",
            name="uq_app_dim_scores_app_config_dim_period",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), nullable=False)
    ranking_config_id: Mapped[str | None] = mapped_column(
        ForeignKey("ranking_configs.id"),
        nullable=True,
        index=True,
    )
    dimension_id: Mapped[int] = mapped_column(ForeignKey("ranking_dimensions.id"), nullable=False)
    dimension_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100分
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    calculation_detail: Mapped[str] = mapped_column(Text, default="")  # 计算详情说明
    period_date: Mapped[date] = mapped_column(Date, nullable=False)  # 统计周期日期
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    app = relationship("App")
    dimension = relationship("RankingDimension")
    ranking_config = relationship("RankingConfig")


class HistoricalRanking(Base):
    """历史榜单数据"""
    __tablename__ = "historical_rankings"
    __table_args__ = (
        UniqueConstraint(
            "ranking_config_id",
            "app_id",
            "period_date",
            "run_id",
            name="uq_historical_rankings_period_run_app",
        ),
        Index("idx_historical_rankings_type_period_run", "ranking_type", "period_date", "run_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 外键关联榜单配置
    ranking_config_id: Mapped[str] = mapped_column(ForeignKey("ranking_configs.id"), nullable=False)
    # 保留 ranking_type 用于快速识别
    ranking_type: Mapped[str] = mapped_column(String(20), nullable=False)  # excellent | trend
    period_date: Mapped[date] = mapped_column(Date, nullable=False)  # 榜单周期日期
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), nullable=False)
    app_name: Mapped[str] = mapped_column(String(120), nullable=False)
    app_org: Mapped[str] = mapped_column(String(60), nullable=False)
    tag: Mapped[str] = mapped_column(String(20), default="推荐")
    score: Mapped[int] = mapped_column(Integer, default=0)
    metric_type: Mapped[str] = mapped_column(String(20), default="composite")
    value_dimension: Mapped[str] = mapped_column(String(40), default="cost_reduction")
    usage_30d: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    app = relationship("App")
    ranking_config = relationship("RankingConfig", back_populates="historical_rankings")


# ==================== 三层架构新表 ====================

class RankingConfig(Base):
    """榜单配置表 - 第二层：榜单配置层"""
    __tablename__ = "ranking_configs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # excellent, trend
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    # 维度配置 JSON格式: [{"dim_id": 1, "weight": 2.5}, ...]
    dimensions_config: Mapped[str] = mapped_column(Text, default="[]")
    calculation_method: Mapped[str] = mapped_column(String(50), default="composite")  # composite | growth_rate
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    app_settings = relationship("AppRankingSetting", back_populates="ranking_config")
    rankings = relationship("Ranking", back_populates="ranking_config")
    historical_rankings = relationship("HistoricalRanking", back_populates="ranking_config")


class AppRankingSetting(Base):
    """应用榜单设置表 - 第三层：应用参与层"""
    __tablename__ = "app_ranking_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), nullable=False)
    ranking_config_id: Mapped[Optional[str]] = mapped_column(ForeignKey("ranking_configs.id"), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    weight_factor: Mapped[float] = mapped_column(Float, default=1.0)  # 权重系数
    custom_tags: Mapped[str] = mapped_column(String(255), default="")  # 该榜单的自定义标签
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    app = relationship("App", back_populates="ranking_settings")
    ranking_config = relationship("RankingConfig", back_populates="app_settings")
