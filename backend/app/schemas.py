from datetime import date, datetime

from pydantic import BaseModel, Field


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
    access_mode: str
    access_url: str
    target_system: str
    target_users: str
    problem_statement: str
    effectiveness_type: str
    effectiveness_metric: str

    class Config:
        from_attributes = True


class RankingItem(BaseModel):
    position: int
    tag: str
    score: int
    likes: int | None
    metric_type: str
    value_dimension: str
    usage_30d: int
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
    app_name: str = Field(min_length=2, max_length=120)
    unit_name: str = Field(min_length=2, max_length=120)
    contact: str = Field(min_length=2, max_length=80)
    scenario: str = Field(min_length=20, max_length=500)
    embedded_system: str = Field(min_length=2, max_length=120)
    problem_statement: str = Field(min_length=10, max_length=255)
    effectiveness_type: str
    effectiveness_metric: str = Field(min_length=2, max_length=120)
    data_level: str
    expected_benefit: str = Field(min_length=10, max_length=300)


class SubmissionOut(BaseModel):
    id: int
    app_name: str
    unit_name: str
    contact: str
    scenario: str
    embedded_system: str
    problem_statement: str
    effectiveness_type: str
    effectiveness_metric: str
    data_level: str
    expected_benefit: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
