import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_role
from app.models import models as m
from app.services.realtime import manager

router = APIRouter(prefix="/recommendations", tags=["ai-command-center"])

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _least_busy_staff(db: Session, department: str | None = None):
    q = db.query(m.Staff)
    if department:
        q = q.filter(m.Staff.department == department)
    candidates = q.all() or db.query(m.Staff).all()
    if not candidates:
        return None
    counts = {
        s.id: db.query(m.Task).filter(
            m.Task.assigned_staff_id == s.id, m.Task.status.in_(["assigned", "in_progress"])
        ).count()
        for s in candidates
    }
    return min(candidates, key=lambda s: counts[s.id])


@router.get("")
def list_recommendations(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    recs = db.query(m.AIRecommendation).order_by(m.AIRecommendation.created_at.desc()).all()
    out = []
    for r in recs:
        pred = db.query(m.AIPrediction).get(r.prediction_id)
        out.append({
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "severity": r.severity,
            "status": r.status,
            "expected_impact": r.expected_impact,
            "created_at": r.created_at.isoformat(),
            "module": pred.module if pred else None,
            "risk_score": pred.risk_score if pred else None,
            "confidence": pred.confidence if pred else None,
            "explanation": pred.explanation if pred else None,
            "subject_label": pred.subject_label if pred else None,
            "subject_id": pred.subject_id if pred else None,
        })
    out.sort(key=lambda r: (r["status"] != "pending", SEVERITY_ORDER.get(r["severity"], 9)))
    return out


@router.post("/{rec_id}/approve")
def approve(rec_id: int, db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    rec = db.query(m.AIRecommendation).get(rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recommendation already {rec.status}")

    pred = db.query(m.AIPrediction).get(rec.prediction_id)
    module = pred.module if pred else "general"

    rec.status = "approved"
    rec.decided_at = dt.datetime.utcnow()
    rec.decided_by = user.name

    # --- Module-specific approval action ---

    if module == "maintenance":
        staff = _least_busy_staff(db, "Maintenance")
        location = ""
        if pred and pred.subject_id:
            eq = db.query(m.Equipment).get(pred.subject_id)
            location = eq.location if eq else ""
        priority = {"critical": "critical", "high": "high", "medium": "normal", "low": "low"}.get(rec.severity, "normal")
        task = m.Task(
            recommendation_id=rec.id, title=rec.title, description=rec.description, category=module,
            priority=priority, assigned_staff_id=staff.id if staff else None, location=location,
            status="assigned" if staff else "pending", due_at=dt.datetime.utcnow() + dt.timedelta(hours=24),
            ai_source=f"AI {module} module — risk {pred.risk_score if pred else '?'}%", expected_impact=rec.expected_impact,
        )
        db.add(task)
        db.add(m.AuditLog(actor=user.name, action="approved_recommendation",
                           detail=f"Recommendation #{rec.id} approved; task assigned to {staff.name if staff else 'unassigned'}"))
        db.commit()
        db.refresh(task)
        result = {"status": "approved", "task_id": task.id, "assigned_to": staff.name if staff else None}
        manager.broadcast({"type": "recommendation_update", "id": rec.id, "status": "approved", "module": module})
        return result

    elif module == "inventory" and pred and pred.subject_id:
        item = db.query(m.InventoryItem).get(pred.subject_id)
        reorder_qty = 0
        if item:
            reorder_qty = round(item.avg_daily_usage * 4, 1)
            item.current_stock += reorder_qty
            db.add(m.InventoryTransaction(item_id=item.id, delta=reorder_qty, reason="AI-approved reorder"))
            db.add(m.AuditLog(actor=user.name, action="approved_recommendation",
                               detail=f"Recommendation #{rec.id} approved; {item.name} restocked by {reorder_qty}{item.unit}"))
        db.commit()
        result = {"status": "approved", "restocked_by": reorder_qty}
        manager.broadcast({"type": "recommendation_update", "id": rec.id, "status": "approved", "module": module})
        return result

    elif module == "revenue" and pred and pred.subject_id:
        room_type = pred.subject_label
        rooms = db.query(m.Room).filter(m.Room.type == room_type).all()
        rooms_updated = 0
        if rooms:
            from app.ml.demand import forecast_next_7_days
            from app.ml.revenue import price_recommendation

            records = db.query(m.OccupancyRecord).order_by(m.OccupancyRecord.date.asc()).all()
            history = [r.occupancy_pct for r in records]
            forecast = forecast_next_7_days(history)
            weekend_occupancy = max(f["occupancy_pct"] for f in forecast)

            today = dt.datetime.utcnow()
            two_weeks_ago = today - dt.timedelta(days=14)
            room_ids = [r.id for r in rooms]
            current_price = sum(r.price for r in rooms) / len(rooms)
            recent_bookings = (
                db.query(m.Booking)
                .filter(m.Booking.room_id.in_(room_ids), m.Booking.check_in >= two_weeks_ago)
                .count()
            )
            baseline_bookings = max(2.0, len(rooms) * 1.2)
            result_calc = price_recommendation(room_type, current_price, recent_bookings, baseline_bookings, weekend_occupancy)

            for r in rooms:
                delta = r.price * (result_calc["adjustment_pct"] / 100)
                r.price = round(r.price + delta, -1)
                rooms_updated += 1

        db.add(m.AuditLog(actor=user.name, action="approved_recommendation",
                           detail=f"Recommendation #{rec.id} approved; pricing updated for {rooms_updated} {room_type} rooms"))
        db.commit()
        result = {"status": "approved", "room_type": room_type, "rooms_updated": rooms_updated}
        manager.broadcast({"type": "recommendation_update", "id": rec.id, "status": "approved", "module": module})
        return result

    elif module == "staffing":
        task = m.Task(
            recommendation_id=rec.id, title=rec.title, description=rec.description, category=module,
            priority="normal", assigned_staff_id=None, status="pending",
            due_at=dt.datetime.utcnow() + dt.timedelta(hours=24),
            ai_source=f"AI {module} module", expected_impact=rec.expected_impact,
        )
        db.add(task)
        db.add(m.AuditLog(actor=user.name, action="approved_recommendation",
                           detail=f"Recommendation #{rec.id} approved; roster change logged for {pred.subject_label if pred else ''}"))
        db.commit()
        db.refresh(task)
        result = {"status": "approved", "task_id": task.id, "assigned_to": None}
        manager.broadcast({"type": "recommendation_update", "id": rec.id, "status": "approved", "module": module})
        return result

    else:
        db.add(m.AuditLog(actor=user.name, action="approved_recommendation", detail=f"Recommendation #{rec.id} approved"))
        db.commit()
        manager.broadcast({"type": "recommendation_update", "id": rec.id, "status": "approved", "module": module})
        return {"status": "approved"}


@router.post("/{rec_id}/reject")
def reject(rec_id: int, db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    rec = db.query(m.AIRecommendation).get(rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recommendation already {rec.status}")
    rec.status = "rejected"
    rec.decided_at = dt.datetime.utcnow()
    rec.decided_by = user.name
    db.add(m.AuditLog(actor=user.name, action="rejected_recommendation", detail=f"Recommendation #{rec.id} rejected"))
    db.commit()
    manager.broadcast({"type": "recommendation_update", "id": rec.id, "status": "rejected"})
    return {"status": "rejected"}
