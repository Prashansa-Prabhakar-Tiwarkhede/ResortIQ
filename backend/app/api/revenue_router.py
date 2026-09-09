import datetime as dt
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import require_role
from app.models import models as m
from app.ml.demand import forecast_next_7_days
from app.ml.revenue import price_recommendation
from app.services.ai_pipeline import upsert_prediction_and_recommendation

router = APIRouter(prefix="/revenue", tags=["revenue"])

ROOM_TYPE_IDS = {"Deluxe": 1, "Premium": 2, "Suite": 3, "Villa": 4}


@router.get("/recommendations")
def revenue_recommendations(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    records = db.query(m.OccupancyRecord).order_by(m.OccupancyRecord.date.asc()).all()
    history = [r.occupancy_pct for r in records]
    forecast = forecast_next_7_days(history)
    weekend_occupancy = max(f["occupancy_pct"] for f in forecast)

    today = dt.datetime.utcnow()
    two_weeks_ago = today - dt.timedelta(days=14)

    out = []
    for room_type in ROOM_TYPE_IDS.keys():
        rooms = db.query(m.Room).filter(m.Room.type == room_type).all()
        if not rooms:
            continue
        room_ids = [r.id for r in rooms]
        current_price = sum(r.price for r in rooms) / len(rooms)

        recent_bookings = (
            db.query(m.Booking)
            .filter(m.Booking.room_id.in_(room_ids), m.Booking.check_in >= two_weeks_ago)
            .count()
        )
        baseline_bookings = max(2.0, len(rooms) * 1.2)  # rough expected bookings per 2 weeks

        result = price_recommendation(room_type, current_price, recent_bookings, baseline_bookings, weekend_occupancy)

        rec = None
        if abs(result["adjustment_pct"]) >= 3:
            severity = "high" if abs(result["adjustment_pct"]) >= 10 else "medium"
            _, rec = upsert_prediction_and_recommendation(
                db, module="revenue", subject_type="room_type", subject_id=ROOM_TYPE_IDS[room_type],
                subject_label=room_type, risk_score=result["risk_score"], confidence=result["confidence"],
                explanation=result["explanation"],
                severity=severity, title=f"{result['action'].capitalize()} {room_type} pricing",
                description=result["recommendation_text"],
                expected_impact=f"Projected revenue impact: {result['expected_revenue_impact_pct']:+.1f}%; expected occupancy {result['expected_occupancy']}%.",
            )
            db.commit()

        out.append({
            "room_type": room_type,
            "current_price": round(current_price),
            "recommended_price": result["recommended_price"],
            "adjustment_pct": result["adjustment_pct"],
            "expected_occupancy": result["expected_occupancy"],
            "expected_revenue_impact_pct": result["expected_revenue_impact_pct"],
            "explanation": result["explanation"],
            "recommendation": ({
                "id": rec.id, "title": rec.title, "description": rec.description,
                "severity": rec.severity, "status": rec.status, "expected_impact": rec.expected_impact,
            } if rec else None),
        })
    return out
