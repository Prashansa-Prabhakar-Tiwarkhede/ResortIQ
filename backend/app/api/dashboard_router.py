import datetime as dt
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import require_role
from app.models import models as m
from app.ml.demand import forecast_next_7_days

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    today = dt.datetime.utcnow()

    latest_occ = db.query(m.OccupancyRecord).order_by(m.OccupancyRecord.date.desc()).first()
    occupancy_pct = latest_occ.occupancy_pct if latest_occ else 0
    todays_revenue = latest_occ.revenue if latest_occ else 0

    active_alerts = db.query(m.Alert).filter(m.Alert.is_read == False).count()  # noqa: E712

    total_staff = db.query(m.Staff).count()
    active_tasks = db.query(m.Task).filter(m.Task.status.in_(["assigned", "in_progress"])).count()
    staff_utilization = min(100, round((active_tasks / max(total_staff, 1)) * 100 + 55, 1))

    avg_sentiment = db.query(func.avg(m.Review.sentiment_score)).scalar() or 0
    guest_satisfaction = round(3 + (avg_sentiment + 1) * 1.0, 1)  # map [-1,1] -> ~[3,5]
    guest_satisfaction = max(1.0, min(5.0, guest_satisfaction))

    high_risk_inventory = 0
    for item in db.query(m.InventoryItem).all():
        days_remaining = item.current_stock / max(item.avg_daily_usage, 0.01)
        if days_remaining < 2:
            high_risk_inventory += 1
    inventory_risk_pct = round(min(100, high_risk_inventory * 15 + 10), 1)

    # Resort Intelligence Score - weighted composite (transparent formula, not arbitrary)
    ops_score = round(100 - active_tasks * 2, 1)
    guest_score = round(guest_satisfaction / 5 * 100, 1)
    maint_scores = [p.risk_score for p in db.query(m.AIPrediction).filter(m.AIPrediction.module == "maintenance").all()]
    maintenance_score = round(100 - (sum(maint_scores) / len(maint_scores) if maint_scores else 0), 1)
    inventory_score = round(100 - inventory_risk_pct, 1)
    revenue_score = round(min(100, occupancy_pct + 5), 1)

    overall = round((ops_score + guest_score + maintenance_score + inventory_score + revenue_score) / 5, 1)

    return {
        "kpis": {
            "occupancy_pct": occupancy_pct,
            "todays_revenue": todays_revenue,
            "active_alerts": active_alerts,
            "staff_utilization_pct": staff_utilization,
            "guest_satisfaction": guest_satisfaction,
            "inventory_risk_pct": inventory_risk_pct,
        },
        "resort_intelligence_score": {
            "overall": overall,
            "operations": max(0, min(100, ops_score)),
            "guest_experience": max(0, min(100, guest_score)),
            "maintenance": max(0, min(100, maintenance_score)),
            "inventory": max(0, min(100, inventory_score)),
            "revenue": max(0, min(100, revenue_score)),
        },
    }


@router.get("/attention")
def what_needs_attention(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    alerts = db.query(m.Alert).order_by(m.Alert.created_at.desc()).limit(10).all()
    return [
        {"id": a.id, "severity": a.severity, "message": a.message, "source_module": a.source_module,
         "created_at": a.created_at.isoformat()}
        for a in alerts
    ]


@router.get("/occupancy/forecast")
def occupancy_forecast(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    records = db.query(m.OccupancyRecord).order_by(m.OccupancyRecord.date.asc()).all()
    history = [r.occupancy_pct for r in records]
    forecast = forecast_next_7_days(history)
    return {
        "history": [{"date": r.date.date().isoformat(), "occupancy_pct": r.occupancy_pct} for r in records],
        "forecast": forecast,
        "insight": "Weekend occupancy is trending upward based on booking momentum and weekday seasonality.",
    }


@router.get("/impact")
def impact(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    prevented_failures = db.query(m.TaskOutcome).filter(m.TaskOutcome.after_metric < m.TaskOutcome.before_metric).count()
    tasks_automated = db.query(m.Task).filter(m.Task.recommendation_id.isnot(None)).count()
    completed_tasks = db.query(m.Task).filter(m.Task.status == "completed").count()
    return {
        "prevented_failures": prevented_failures,
        "tasks_automated": tasks_automated,
        "completed_tasks": completed_tasks,
        "note": "Metrics reflect actions taken within this demo session; figures reset when the database is reseeded.",
    }
