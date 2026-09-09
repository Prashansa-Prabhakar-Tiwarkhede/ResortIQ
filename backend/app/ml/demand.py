"""
Demand forecasting: statistical model combining weekday seasonality
(learned from historical occupancy_records) with recent booking momentum.
Simple, explainable, and good enough for a 7-day operational forecast.
"""
import datetime as dt
import numpy as np

WEEKDAY_BASE = {
    0: 0.72,  # Mon
    1: 0.75,
    2: 0.78,
    3: 0.83,
    4: 0.91,
    5: 0.96,
    6: 0.89,  # Sun
}


def forecast_next_7_days(recent_occupancy: list[float]) -> list[dict]:
    """recent_occupancy: last ~14 days of occupancy_pct (0-100) from DB, most recent last."""
    momentum = 0.0
    if len(recent_occupancy) >= 7:
        recent_avg = np.mean(recent_occupancy[-7:]) / 100
        older_avg = np.mean(recent_occupancy[-14:-7]) / 100 if len(recent_occupancy) >= 14 else recent_avg
        momentum = recent_avg - older_avg

    today = dt.date.today()
    out = []
    for i in range(1, 8):
        day = today + dt.timedelta(days=i)
        base = WEEKDAY_BASE[day.weekday()]
        projected = np.clip(base + momentum * 0.5, 0.35, 0.99)
        out.append({
            "date": day.isoformat(),
            "day": day.strftime("%A"),
            "occupancy_pct": round(float(projected) * 100, 1),
        })
    return out
