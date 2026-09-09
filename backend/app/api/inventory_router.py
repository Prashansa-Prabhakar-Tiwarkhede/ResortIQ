from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_role
from app.models import models as m
from app.ml.inventory import forecast_item
from app.services.ai_pipeline import upsert_prediction_and_recommendation

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/forecast")
def inventory_forecast(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    latest_occ = db.query(m.OccupancyRecord).order_by(m.OccupancyRecord.date.desc()).first()
    occupancy_pct = latest_occ.occupancy_pct if latest_occ else 75.0

    items = db.query(m.InventoryItem).all()
    out = []
    for item in items:
        result = forecast_item(item.name, item.unit, item.current_stock, item.avg_daily_usage, occupancy_pct)

        severity = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium"}.get(result["status"])
        rec = None
        if severity:
            _, rec = upsert_prediction_and_recommendation(
                db, module="inventory", subject_type="inventory_item", subject_id=item.id,
                subject_label=item.name, risk_score=result["risk_score"], confidence=result["confidence"],
                explanation=result["explanation"],
                severity=severity, title=f"Reorder {item.name}",
                description=result["recommendation_text"],
                expected_impact=f"Avoids stockout in {result['days_remaining']} days; restocks to a {result['reorder_qty']}{item.unit} buffer.",
            )
            db.commit()

        out.append({
            "id": item.id, "name": item.name, "unit": item.unit,
            "current_stock": item.current_stock, "predicted_daily_usage": result["predicted_daily_usage"],
            "days_remaining": result["days_remaining"], "status": result["status"],
            "explanation": result["explanation"],
            "recommendation": ({
                "id": rec.id, "title": rec.title, "description": rec.description,
                "severity": rec.severity, "status": rec.status, "expected_impact": rec.expected_impact,
            } if rec else None),
        })
    out.sort(key=lambda x: x["days_remaining"])
    return out
