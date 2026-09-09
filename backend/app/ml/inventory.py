"""
Inventory intelligence: predicts days-of-stock-remaining from current stock and
a demand-adjusted daily usage rate (usage scales with occupancy - a resort at
95% occupancy consumes more towels/food than one at 60%), and recommends a
reorder quantity sized to cover a safety buffer.
"""
import math

STATUS_THRESHOLDS = [
    (1.0, "CRITICAL"),
    (2.0, "HIGH"),
    (4.0, "MEDIUM"),
]


def predicted_daily_usage(base_avg_usage: float, occupancy_pct: float) -> float:
    # Usage scales roughly linearly with occupancy around a 75% baseline.
    factor = max(0.5, occupancy_pct / 75.0)
    return round(base_avg_usage * factor, 1)


def forecast_item(name: str, unit: str, current_stock: float, base_avg_usage: float, occupancy_pct: float) -> dict:
    usage = predicted_daily_usage(base_avg_usage, occupancy_pct)
    days_remaining = round(current_stock / max(usage, 0.01), 1)

    status = "LOW"
    for threshold, label in STATUS_THRESHOLDS:
        if days_remaining <= threshold:
            status = label
            break

    risk_score = round(max(0.0, min(100.0, (5 - days_remaining) / 5 * 100)), 1)

    reorder_qty = math.ceil(usage * 4)  # cover ~4 days including lead time buffer
    explanation = (
        f"Current stock ({current_stock:g}{unit}) covers only {days_remaining} days at the "
        f"predicted usage rate of {usage:g}{unit}/day, driven by {occupancy_pct:.0f}% occupancy."
    )
    recommendation_text = f"Reorder {reorder_qty}{unit} of {name} before tomorrow morning."

    return {
        "predicted_daily_usage": usage,
        "days_remaining": days_remaining,
        "status": status,
        "risk_score": risk_score,
        "confidence": 82.0,
        "reorder_qty": reorder_qty,
        "explanation": explanation,
        "recommendation_text": recommendation_text,
    }
