"""
Revenue intelligence: recommends a price adjustment per room type based on
recent booking momentum for that type relative to a baseline share, and the
forecast weekend occupancy.
"""


def price_recommendation(
    room_type: str, current_price: float, recent_bookings: int, baseline_bookings: float, weekend_occupancy_pct: float
) -> dict:
    demand_index = recent_bookings / max(baseline_bookings, 0.5)  # >1 = above-average demand
    demand_pct_above_baseline = round((demand_index - 1) * 100, 1)

    # Map demand + weekend pressure into a bounded price adjustment.
    adjustment_pct = max(-8.0, min(15.0, demand_pct_above_baseline * 0.4 + (weekend_occupancy_pct - 85) * 0.3))
    recommended_price = round(current_price * (1 + adjustment_pct / 100), -1)  # round to nearest 10

    expected_occupancy = round(min(99, weekend_occupancy_pct + (2 if adjustment_pct < 0 else -1 if adjustment_pct > 8 else 0)), 1)
    expected_revenue_impact = round(adjustment_pct * 0.7, 1)  # some demand elasticity assumed

    confidence = 74.0
    risk_score = round(min(100, abs(adjustment_pct) * 5), 1)  # "risk" here = magnitude of pricing opportunity

    explanation = (
        f"Demand for {room_type} rooms is {demand_pct_above_baseline:+.0f}% vs. the current weekly average, "
        f"with weekend occupancy trending toward {weekend_occupancy_pct:.0f}%."
    )
    action = "increase" if adjustment_pct > 0 else "decrease"
    recommendation_text = (
        f"{'Increase' if adjustment_pct > 0 else 'Decrease'} {room_type} pricing by {abs(adjustment_pct):.0f}% "
        f"(₹{int(current_price):,} → ₹{int(recommended_price):,})."
    )

    return {
        "current_price": current_price,
        "recommended_price": recommended_price,
        "adjustment_pct": round(adjustment_pct, 1),
        "expected_occupancy": expected_occupancy,
        "expected_revenue_impact_pct": expected_revenue_impact,
        "risk_score": risk_score,
        "confidence": confidence,
        "explanation": explanation,
        "recommendation_text": recommendation_text,
        "action": action,
    }
