from types import SimpleNamespace

from app.main import calculate_three_layer_score


def test_three_layer_score_is_stable_for_same_input():
    app = SimpleNamespace(
        monthly_calls=12.5,
        effectiveness_type="efficiency_gain",
        difficulty="Medium",
        status="available",
    )
    dimension_map = {
        1: SimpleNamespace(id=1, name="用户满意度"),
        2: SimpleNamespace(id=2, name="业务价值"),
    }
    config_dimensions = [
        {"dim_id": 1, "weight": 0.6},
        {"dim_id": 2, "weight": 0.4},
    ]

    first = calculate_three_layer_score(app, config_dimensions, dimension_map, weight_factor=1.0)
    second = calculate_three_layer_score(app, config_dimensions, dimension_map, weight_factor=1.0)

    assert first == second
    assert first == 92
