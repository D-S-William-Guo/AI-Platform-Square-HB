from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import app.main as main


class RecordingQuery:
    def __init__(self, first_result=None, all_result=None):
        self.first_result = first_result
        self.all_result = all_result if all_result is not None else []
        self.filters: list[tuple[str, ...]] = []
        self.ordering = None

    def filter(self, *conditions):
        self.filters.append(tuple(str(c) for c in conditions))
        return self

    def order_by(self, ordering):
        self.ordering = str(ordering)
        return self

    def first(self):
        return self.first_result

    def all(self):
        return self.all_result


class RecordingDB:
    def __init__(self, queries: list[RecordingQuery]):
        self._queries = list(queries)

    def query(self, *_args, **_kwargs):
        if not self._queries:
            raise AssertionError("No more query objects configured")
        return self._queries.pop(0)


def _build_dimension_map():
    return {
        1: SimpleNamespace(id=1, name="用户满意度"),
        2: SimpleNamespace(id=2, name="业务价值"),
        3: SimpleNamespace(id=3, name="技术创新性"),
    }


def test_calculate_three_layer_score_clamps_to_zero_when_weight_factor_negative():
    app = SimpleNamespace(monthly_calls=12.5, effectiveness_type="efficiency_gain", difficulty="Medium", status="available")
    config_dimensions = [{"dim_id": 1, "weight": 1.0}, {"dim_id": 2, "weight": 1.0}]

    score = main.calculate_three_layer_score(
        app=app,
        config_dimensions=config_dimensions,
        dimension_map=_build_dimension_map(),
        weight_factor=-2.0,
    )

    assert score == 0


def test_calculate_three_layer_score_clamps_to_thousand_when_weight_factor_large():
    app = SimpleNamespace(monthly_calls=50, effectiveness_type="revenue_growth", difficulty="High", status="available")
    config_dimensions = [{"dim_id": 1, "weight": 1.0}, {"dim_id": 2, "weight": 1.0}, {"dim_id": 3, "weight": 1.0}]

    score = main.calculate_three_layer_score(
        app=app,
        config_dimensions=config_dimensions,
        dimension_map=_build_dimension_map(),
        weight_factor=5.0,
    )

    assert score == 1000


def test_sorting_order_is_stable_for_same_input_with_tied_scores():
    app_scores = [
        {"app_id": "app-a", "score": 300},
        {"app_id": "app-b", "score": 500},
        {"app_id": "app-c", "score": 500},
        {"app_id": "app-d", "score": 450},
        {"app_id": "app-e", "score": 300},
    ]

    run1 = [*app_scores]
    run2 = [*app_scores]
    run1.sort(key=lambda x: x["score"], reverse=True)
    run2.sort(key=lambda x: x["score"], reverse=True)

    assert [item["app_id"] for item in run1] == ["app-b", "app-c", "app-d", "app-a", "app-e"]
    assert [item["app_id"] for item in run1] == [item["app_id"] for item in run2]


def test_resolve_latest_run_id_returns_latest_non_null_run_id():
    query = RecordingQuery(first_result=("run-newest",))
    db = RecordingDB([query])

    resolved = main.resolve_latest_run_id(db, ranking_type="excellent", period_date=date(2025, 1, 1))

    assert resolved == "run-newest"
    assert any("historical_rankings.run_id IS NOT NULL" in cond for f in query.filters for cond in f)


def test_list_historical_rankings_uses_latest_run_id_in_date_mode(monkeypatch):
    query = RecordingQuery(all_result=[])
    db = RecordingDB([query])

    monkeypatch.setattr(main, "resolve_latest_run_id", lambda *_args, **_kwargs: "run-latest")

    main.list_historical_rankings(
        ranking_type="excellent",
        period_date=date(2025, 1, 1),
        run_id=None,
        db=db,
    )

    assert any("historical_rankings.run_id = :run_id_1" in cond for f in query.filters for cond in f)


def test_list_historical_rankings_falls_back_to_null_run_id_when_no_latest(monkeypatch):
    query = RecordingQuery(all_result=[])
    db = RecordingDB([query])

    monkeypatch.setattr(main, "resolve_latest_run_id", lambda *_args, **_kwargs: None)

    main.list_historical_rankings(
        ranking_type="excellent",
        period_date=date(2025, 1, 1),
        run_id=None,
        db=db,
    )

    assert any("historical_rankings.run_id IS NULL" in cond for f in query.filters for cond in f)


def test_list_historical_rankings_prefers_explicit_run_id_over_latest(monkeypatch):
    query = RecordingQuery(all_result=[])
    db = RecordingDB([query])

    def _unexpected_call(*_args, **_kwargs):
        raise AssertionError("resolve_latest_run_id should not be called when run_id is explicitly provided")

    monkeypatch.setattr(main, "resolve_latest_run_id", _unexpected_call)

    main.list_historical_rankings(
        ranking_type="excellent",
        period_date=date(2025, 1, 1),
        run_id="run-manual",
        db=db,
    )

    assert any("historical_rankings.run_id = :run_id_1" in cond for f in query.filters for cond in f)
