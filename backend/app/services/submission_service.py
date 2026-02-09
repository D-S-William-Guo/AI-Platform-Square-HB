from datetime import datetime

from sqlalchemy.orm import Session

from ..domain import DATA_LEVEL_VALUES, VALUE_DIMENSIONS
from ..models import App, Submission
from ..schemas import SubmissionCreate


def validate_submission_payload(payload: SubmissionCreate) -> None:
    if payload.effectiveness_type not in VALUE_DIMENSIONS:
        raise ValueError("Invalid effectiveness_type")
    if payload.data_level not in DATA_LEVEL_VALUES:
        raise ValueError("Invalid data_level")
    if payload.ranking_weight < 0.1 or payload.ranking_weight > 10.0:
        raise ValueError("ranking_weight must be between 0.1 and 10.0")
    if len(payload.ranking_tags) > 255:
        raise ValueError("ranking_tags must not exceed 255 characters")
    if len(payload.ranking_dimensions) > 500:
        raise ValueError("ranking_dimensions must not exceed 500 characters")


def create_submission(db: Session, payload: SubmissionCreate) -> Submission:
    validate_submission_payload(payload)
    submission = Submission(**payload.model_dump())
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def approve_submission_and_create_app(db: Session, submission: Submission) -> App:
    if submission.status != "pending":
        raise ValueError("submission is not pending")

    app = App(
        name=submission.app_name,
        org=submission.unit_name,
        section="province",
        category=submission.category,
        description=submission.scenario,
        status="available",
        monthly_calls=0.0,
        release_date=datetime.now().date(),
        effectiveness_type=submission.effectiveness_type,
        effectiveness_metric=submission.effectiveness_metric,
        ranking_enabled=submission.ranking_enabled,
        ranking_weight=submission.ranking_weight,
        ranking_tags=submission.ranking_tags,
    )

    db.add(app)
    submission.status = "approved"
    db.commit()
    db.refresh(app)
    return app
