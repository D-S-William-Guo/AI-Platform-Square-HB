from fastapi import HTTPException

from .schemas import SubmissionCreate

APP_STATUS_VALUES = {"available", "approval", "beta", "offline"}
METRIC_TYPES = {"composite", "growth_rate", "likes"}
VALUE_DIMENSIONS = {"cost_reduction", "efficiency_gain", "perception_uplift", "revenue_growth"}
DATA_LEVEL_VALUES = {"L1", "L2", "L3", "L4"}


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


def validate_app_status(status: str) -> None:
    if status not in APP_STATUS_VALUES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {', '.join(APP_STATUS_VALUES)}")


def validate_metric_type(metric_type: str) -> None:
    if metric_type not in METRIC_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid metric_type. Must be one of: {', '.join(METRIC_TYPES)}")
