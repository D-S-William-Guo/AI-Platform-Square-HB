from datetime import date, datetime
from pydantic import BaseModel


class AppBase(BaseModel):
    id: int
    name: str
    org: str
    section: str
    category: str
    description: str
    status: str
    monthly_calls: float
    release_date: date


class AppDetail(AppBase):
    api_open: bool
    difficulty: str
    contact_name: str
    highlight: str

    class Config:
        from_attributes = True


class RankingItem(BaseModel):
    position: int
    tag: str
    score: int
    declared_at: date
    app: AppBase


class Recommendation(BaseModel):
    title: str
    scene: str


class Stats(BaseModel):
    pending: int
    approved_period: int
    total_apps: int


class RuleLink(BaseModel):
    title: str
    href: str


class SubmissionCreate(BaseModel):
    app_name: str
    unit_name: str
    contact: str


class SubmissionOut(BaseModel):
    id: int
    app_name: str
    unit_name: str
    contact: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
