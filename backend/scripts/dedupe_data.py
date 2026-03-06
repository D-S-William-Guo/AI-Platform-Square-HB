#!/usr/bin/env python3
"""Deduplicate submissions/apps/rankings before applying unique constraints.

Default mode is dry-run. Use --apply to write changes.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import App, AppDimensionScore, AppRankingSetting, HistoricalRanking, Ranking, Submission


@dataclass
class DedupeResult:
    duplicate_submissions: int = 0
    duplicate_apps: int = 0
    duplicate_rankings: int = 0


def normalize(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def dedupe_submissions(db: Session, apply_changes: bool) -> int:
    submissions = (
        db.query(Submission)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .all()
    )

    seen: set[tuple[str, str, str]] = set()
    duplicates: list[Submission] = []

    for row in submissions:
        key = (normalize(row.app_name), normalize(row.unit_name), row.status)
        if key in seen:
            duplicates.append(row)
        else:
            seen.add(key)

    if apply_changes:
        for row in duplicates:
            db.delete(row)

    return len(duplicates)


def dedupe_apps(db: Session, apply_changes: bool) -> int:
    apps = db.query(App).order_by(App.id.asc()).all()

    keep_by_key: dict[tuple[str, str, str], App] = {}
    to_remove: list[App] = []

    for app in apps:
        key = (app.section, normalize(app.name), normalize(app.org))
        if key in keep_by_key:
            to_remove.append(app)
        else:
            keep_by_key[key] = app

    if apply_changes:
        for app in to_remove:
            keeper = keep_by_key[(app.section, normalize(app.name), normalize(app.org))]
            db.query(Ranking).filter(Ranking.app_id == app.id).update({Ranking.app_id: keeper.id})
            db.query(HistoricalRanking).filter(HistoricalRanking.app_id == app.id).update({HistoricalRanking.app_id: keeper.id})
            db.query(AppDimensionScore).filter(AppDimensionScore.app_id == app.id).update({AppDimensionScore.app_id: keeper.id})
            db.query(AppRankingSetting).filter(AppRankingSetting.app_id == app.id).update({AppRankingSetting.app_id: keeper.id})
            db.delete(app)

    return len(to_remove)


def dedupe_rankings(db: Session, apply_changes: bool) -> int:
    rankings = (
        db.query(Ranking)
        .order_by(Ranking.updated_at.desc(), Ranking.id.desc())
        .all()
    )

    seen: set[tuple[str, int]] = set()
    duplicates: list[Ranking] = []

    for row in rankings:
        key = (row.ranking_config_id, row.app_id)
        if key in seen:
            duplicates.append(row)
        else:
            seen.add(key)

    if apply_changes:
        for row in duplicates:
            db.delete(row)

    return len(duplicates)


def run(apply_changes: bool) -> DedupeResult:
    db = SessionLocal()
    result = DedupeResult()
    try:
        result.duplicate_submissions = dedupe_submissions(db, apply_changes)
        result.duplicate_apps = dedupe_apps(db, apply_changes)
        result.duplicate_rankings = dedupe_rankings(db, apply_changes)

        if apply_changes:
            db.commit()
        else:
            db.rollback()
    finally:
        db.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Deduplicate data before adding unique constraints")
    parser.add_argument("--apply", action="store_true", help="Apply dedupe changes to database")
    args = parser.parse_args()

    result = run(args.apply)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[dedupe:{mode}] duplicate submissions: {result.duplicate_submissions}")
    print(f"[dedupe:{mode}] duplicate apps: {result.duplicate_apps}")
    print(f"[dedupe:{mode}] duplicate rankings: {result.duplicate_rankings}")


if __name__ == "__main__":
    main()
