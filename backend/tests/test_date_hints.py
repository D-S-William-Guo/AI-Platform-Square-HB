from datetime import date
from typing import get_args

from app import models


def test_models_importable():
    assert models is not None


def test_date_hints_align_with_date_columns():
    release_date_hint = models.App.__annotations__["release_date"]
    declared_at_hint = models.Ranking.__annotations__["declared_at"]

    assert date in get_args(release_date_hint)
    assert date in get_args(declared_at_hint)
