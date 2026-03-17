from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


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
    detail_doc_url: str = ""
    detail_doc_name: str = ""
    target_system: str
    target_users: str
    problem_statement: str
    effectiveness_type: str
    effectiveness_metric: str
    cover_image_url: str
    created_by_user_id: int | None = None
    created_from_submission_id: int | None = None
    approved_by_user_id: int | None = None
    approved_at: datetime | None = None
    # 排行榜相关字段
    ranking_enabled: bool | None = None
    ranking_weight: float | None = None
    ranking_tags: str | None = None
    last_ranking_update: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RankingItem(BaseModel):
    ranking_config_id: str | None = None
    position: int
    tag: str
    score: int
    likes: int | None
    metric_type: str
    value_dimension: str
    usage_30d: int
    declared_at: date
    updated_at: datetime | None = None
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


class UserPublic(BaseModel):
    id: int
    username: str
    chinese_name: str
    role: str
    phone: str
    email: str
    department: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AuthLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=80)
    password: str = Field(..., min_length=1, max_length=128)


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserPublic


class AuthMeResponse(BaseModel):
    expires_at: datetime
    user: UserPublic


class ActionLogOut(BaseModel):
    id: int
    actor_user_id: int | None
    actor_username: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str
    request_id: str
    payload_summary: str
    created_at: datetime

class SubmissionCreate(BaseModel):
    app_name: str = Field(min_length=2, max_length=120)
    unit_name: str = Field(min_length=2, max_length=120)
    contact: str = Field(min_length=2, max_length=80)
    contact_phone: str = Field(default="", max_length=20)
    contact_email: str = Field(default="", max_length=120)
    category: str = Field(min_length=2, max_length=30)
    scenario: str = Field(min_length=20, max_length=500)
    embedded_system: str = Field(min_length=2, max_length=120)
    problem_statement: str = Field(min_length=10, max_length=255)
    effectiveness_type: str
    effectiveness_metric: str = Field(min_length=2, max_length=120)
    data_level: str
    expected_benefit: str = Field(min_length=10, max_length=300)
    cover_image_url: str = Field(default="", max_length=500)
    detail_doc_url: str = Field(default="", max_length=500)
    detail_doc_name: str = Field(default="", max_length=255)
    # 排行榜相关字段
    ranking_enabled: bool = Field(default=True)
    ranking_weight: float = Field(default=1.0, ge=0.1, le=10.0)
    ranking_tags: str = Field(default="", max_length=255)
    ranking_dimensions: str = Field(default="", max_length=500)


class SubmissionOut(BaseModel):
    id: int
    app_name: str
    unit_name: str
    contact: str
    contact_phone: str
    contact_email: str
    category: str
    scenario: str
    embedded_system: str
    problem_statement: str
    effectiveness_type: str
    effectiveness_metric: str
    data_level: str
    expected_benefit: str
    status: str
    submitter_user_id: int | None = None
    approved_by_user_id: int | None = None
    approved_at: datetime | None = None
    rejected_by_user_id: int | None = None
    rejected_at: datetime | None = None
    rejected_reason: str = ""
    manage_token: str
    cover_image_url: str
    detail_doc_url: str
    detail_doc_name: str
    created_at: datetime
    updated_at: datetime | None = None
    # 排行榜相关字段
    ranking_enabled: bool
    ranking_weight: float
    ranking_tags: str
    ranking_dimensions: str

    model_config = ConfigDict(from_attributes=True)


class SubmissionApprovePayload(BaseModel):
    status: str | None = None
    monthly_calls: float | None = Field(default=None, ge=0)
    difficulty: str | None = Field(default=None, max_length=20)
    target_system: str | None = Field(default=None, max_length=120)
    target_users: str | None = Field(default=None, max_length=120)
    access_mode: str | None = None
    access_url: str | None = Field(default=None, max_length=255)


class SubmissionManageTokenPayload(BaseModel):
    manage_token: str = Field(min_length=16, max_length=128)


class SubmissionSelfUpdate(SubmissionCreate):
    manage_token: str = Field(min_length=16, max_length=128)


class ImageUploadResponse(BaseModel):
    success: bool
    image_url: str
    thumbnail_url: str
    original_name: str
    file_size: int
    message: str


class DocumentUploadResponse(BaseModel):
    success: bool
    file_url: str
    original_name: str
    file_size: int
    message: str


class RankingDimensionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    calculation_method: str = Field(..., min_length=1)
    weight: float = Field(..., ge=0.1, le=10.0)
    is_active: bool = True


class RankingDimensionCreate(RankingDimensionBase):
    pass


class RankingDimensionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1)
    calculation_method: str | None = Field(None, min_length=1)
    weight: float | None = Field(None, ge=0.1, le=10.0)
    is_active: bool | None = None


class RankingDimensionOut(RankingDimensionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RankingLogOut(BaseModel):
    id: int
    action: str
    dimension_id: int | None
    dimension_name: str
    changes: str
    operator: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RankingAuditLogOut(BaseModel):
    id: int
    action: str
    ranking_type: str | None
    ranking_config_id: str | None
    period_date: date | None
    run_id: str | None
    actor: str
    payload_summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppDimensionScoreOut(BaseModel):
    """应用维度评分输出"""
    id: int
    app_id: int
    dimension_id: int
    dimension_name: str
    score: int
    weight: float
    calculation_detail: str
    period_date: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DimensionScoreUpdate(BaseModel):
    score: int = Field(..., ge=0, le=100)


class HistoricalRankingOut(BaseModel):
    """历史榜单输出"""
    id: int
    ranking_type: str
    period_date: date
    run_id: str | None = None
    position: int
    app_id: int
    app_name: str
    app_org: str
    tag: str
    score: int
    metric_type: str
    value_dimension: str
    usage_30d: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupAppCreate(BaseModel):
    """集团应用创建（专用录入）"""
    name: str = Field(..., min_length=2, max_length=120)
    org: str = Field(..., min_length=2, max_length=60)
    category: str = Field(..., min_length=2, max_length=30)
    description: str = Field(..., min_length=10)
    status: str = Field(default="available")
    monthly_calls: float = Field(default=0.0)
    api_open: bool = Field(default=False)
    difficulty: str = Field(default="Low")
    contact_name: str = Field(default="", max_length=50)
    highlight: str = Field(default="", max_length=200)
    access_mode: str = Field(default="direct")
    access_url: str = Field(default="", max_length=255)
    target_system: str = Field(default="", max_length=120)
    target_users: str = Field(default="", max_length=120)
    problem_statement: str = Field(default="", max_length=255)
    effectiveness_type: str = Field(default="cost_reduction")
    effectiveness_metric: str = Field(default="", max_length=120)
    cover_image_url: str = Field(default="", max_length=500)
    ranking_enabled: bool = Field(default=True)
    ranking_weight: float = Field(default=1.0, ge=0.1, le=10.0)
    ranking_tags: str = Field(default="", max_length=255)


# ==================== 三层架构排行榜系统 Schemas ====================

class RankingConfigBase(BaseModel):
    """榜单配置基础模型"""
    id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    dimensions_config: str = Field(default="[]")  # JSON格式
    calculation_method: str = Field(default="composite")
    is_active: bool = Field(default=True)


class RankingConfigCreate(RankingConfigBase):
    """创建榜单配置"""
    pass


class RankingConfigUpdate(BaseModel):
    """更新榜单配置"""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    dimensions_config: str | None = None
    calculation_method: str | None = None
    is_active: bool | None = None


class RankingConfigOut(RankingConfigBase):
    """榜单配置输出"""
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppRankingSettingBase(BaseModel):
    """应用榜单设置基础模型"""
    app_id: int
    ranking_config_id: str | None = None
    is_enabled: bool = False
    weight_factor: float = Field(default=1.0, ge=0.1, le=10.0)
    custom_tags: str = Field(default="", max_length=255)


class AppRankingSettingCreate(BaseModel):
    """创建应用榜单设置"""
    ranking_config_id: str
    is_enabled: bool = False
    weight_factor: float = Field(default=1.0, ge=0.1, le=10.0)
    custom_tags: str = Field(default="", max_length=255)


class AppRankingSettingUpdate(BaseModel):
    """更新应用榜单设置"""
    ranking_config_id: str | None = Field(None, min_length=1, max_length=50)
    is_enabled: bool | None = None
    weight_factor: float | None = Field(None, ge=0.1, le=10.0)
    custom_tags: str | None = Field(None, max_length=255)


class AppRankingSettingOut(AppRankingSettingBase):
    """应用榜单设置输出"""
    id: int
    created_at: datetime
    updated_at: datetime
    ranking_config: RankingConfigOut | None = None

    model_config = ConfigDict(from_attributes=True)


class AppDimensionScoreInput(BaseModel):
    """应用维度评分输入"""
    dimension_id: int = Field(..., ge=1)
    score: int = Field(..., ge=0, le=100)


class AppRankingSettingSaveRequest(BaseModel):
    """原子保存应用榜单参与与维度评分"""
    setting_id: int | None = None
    ranking_config_id: str = Field(..., min_length=1, max_length=50)
    is_enabled: bool = True
    weight_factor: float = Field(default=1.0, ge=0.1, le=10.0)
    custom_tags: str = Field(default="", max_length=255)
    dimension_scores: list[AppDimensionScoreInput] = Field(default_factory=list)


class AppRankingSettingSaveResponse(BaseModel):
    """原子保存结果"""
    setting: AppRankingSettingOut
    updated_dimensions: int
    synced: int
    run_id: str


class DimensionConfigItem(BaseModel):
    """维度配置项"""
    dim_id: int
    weight: float


class RankingConfigWithDimensions(BaseModel):
    """带维度详情的榜单配置"""
    id: str
    name: str
    description: str
    dimensions: list[DimensionConfigItem]
    calculation_method: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
