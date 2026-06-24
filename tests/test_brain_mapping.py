from datetime import datetime, timezone

from brain.write_stance import (
    build_stance,
    parse_float_field,
    rating_to_direction_conviction,
)


def test_rating_map():
    assert rating_to_direction_conviction("Buy") == ("long", 0.8)
    assert rating_to_direction_conviction("Overweight") == ("long", 0.6)
    assert rating_to_direction_conviction("Hold") == ("flat", 0.0)
    assert rating_to_direction_conviction("Underweight") == ("short", 0.6)
    assert rating_to_direction_conviction("Sell") == ("short", 0.8)


def test_rating_map_unknown_is_flat():
    assert rating_to_direction_conviction("") == ("flat", 0.0)
    assert rating_to_direction_conviction("garbage") == ("flat", 0.0)


def test_parse_float_field():
    md = "**Rating**: Buy\n\n**Price Target**: 1.2345\n"
    assert parse_float_field(md, "Price Target") == 1.2345
    assert parse_float_field(md, "Stop Loss") is None
    assert parse_float_field(None, "Price Target") is None


def test_build_stance_pulls_target_and_stop():
    final_state = {
        "final_trade_decision": "**Rating**: Buy\n**Executive Summary**: Go long.\n**Price Target**: 1.1500",
        "trader_investment_plan": "**Action**: Buy\n**Stop Loss**: 1.0900",
    }
    now = datetime(2026, 6, 24, tzinfo=timezone.utc)
    stance = build_stance("eurusd", "Buy", final_state, ttl_minutes=120, now=now)
    assert stance.instrument == "EURUSD"
    assert stance.direction == "long"
    assert stance.conviction == 0.8
    assert stance.target == 1.1500
    assert stance.invalidation == 1.0900
    assert stance.ttl_minutes == 120
    assert "Go long" in stance.rationale


def test_build_stance_hold_is_flat_no_levels():
    stance = build_stance("GBPUSD", "Hold", {})
    assert stance.direction == "flat"
    assert stance.conviction == 0.0
    assert stance.target is None
    assert stance.invalidation is None
