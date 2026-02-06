from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from .database import Base


class App(Base):
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    org: Mapped[str] = mapped_column(String(60), nullable=False)
    section: Mapped[str] = mapped_column(String(20), nullable=False)  # group | province
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # available | approval
    monthly_calls: Mapped[float] = mapped_column(Float, nullable=False)
    release_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    api_open: Mapped[bool] = mapped_column(Boolean, default=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="Low")
    contact_name: Mapped[str] = mapped_column(String(50), default="")
    highlight: Mapped[str] = mapped_column(String(200), default="")


class Ranking(Base):
    __tablename__ = "rankings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ranking_type: Mapped[str] = mapped_column(String(20), nullable=False)  # excellent | trend
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), nullable=False)
    tag: Mapped[str] = mapped_column(String(20), default="推荐")
    score: Mapped[int] = mapped_column(Integer, default=0)
    declared_at: Mapped[datetime] = mapped_column(Date, nullable=False)

    app = relationship("App")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit_name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
