from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class App(Base):
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    org: Mapped[str] = mapped_column(String(60), nullable=False)
    section: Mapped[str] = mapped_column(String(20), nullable=False)  # group | province
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # available | approval | beta | offline
    monthly_calls: Mapped[float] = mapped_column(Float, nullable=False)
    release_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    api_open: Mapped[bool] = mapped_column(Boolean, default=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="Low")
    contact_name: Mapped[str] = mapped_column(String(50), default="")
    highlight: Mapped[str] = mapped_column(String(200), default="")
    access_mode: Mapped[str] = mapped_column(String(20), default="direct")  # direct | profile
    access_url: Mapped[str] = mapped_column(String(255), default="")
    target_system: Mapped[str] = mapped_column(String(120), default="")
    target_users: Mapped[str] = mapped_column(String(120), default="")
    problem_statement: Mapped[str] = mapped_column(String(255), default="")
    effectiveness_type: Mapped[str] = mapped_column(String(40), default="cost_reduction")
    effectiveness_metric: Mapped[str] = mapped_column(String(120), default="")
    cover_image_url: Mapped[str] = mapped_column(String(500), default="")


class Ranking(Base):
    __tablename__ = "rankings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ranking_type: Mapped[str] = mapped_column(String(20), nullable=False)  # excellent | trend
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), nullable=False)
    tag: Mapped[str] = mapped_column(String(20), default="推荐")
    score: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metric_type: Mapped[str] = mapped_column(String(20), default="composite")  # composite | growth_rate | likes
    value_dimension: Mapped[str] = mapped_column(String(40), default="cost_reduction")
    usage_30d: Mapped[int] = mapped_column(Integer, default=0)
    declared_at: Mapped[datetime] = mapped_column(Date, nullable=False)

    app = relationship("App")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit_name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact: Mapped[str] = mapped_column(String(80), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), default="")
    contact_email: Mapped[str] = mapped_column(String(120), default="")
    scenario: Mapped[str] = mapped_column(String(500), nullable=False)
    embedded_system: Mapped[str] = mapped_column(String(120), nullable=False)
    problem_statement: Mapped[str] = mapped_column(String(255), nullable=False)
    effectiveness_type: Mapped[str] = mapped_column(String(40), nullable=False)
    effectiveness_metric: Mapped[str] = mapped_column(String(120), nullable=False)
    data_level: Mapped[str] = mapped_column(String(10), nullable=False)
    expected_benefit: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    cover_image_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
