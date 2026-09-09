import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.auth import require_role, get_current_user
from app.models import models as m
from app.ml.maintenance import predict_risk
from app.services.realtime import manager

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _serialize(t: m.Task, db: Session):
    staff = db.query(m.Staff).get(t.assigned_staff_id) if t.assigned_staff_id else None
    return {
        "id": t.id, "title": t.title, "description": t.description, "category": t.category,
        "priority": t.priority, "status": t.status, "location": t.location,
        "assigned_staff": staff.name if staff else None, "assigned_staff_id": t.assigned_staff_id,
        "created_at": t.created_at.isoformat(), "due_at": t.due_at.isoformat() if t.due_at else None,
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "notes": t.notes, "ai_source": t.ai_source, "expected_impact": t.expected_impact,
        "recommendation_id": t.recommendation_id,
    }


@router.get("")
def list_tasks(staff_id: int | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(m.Task)
    if user.role == "staff":
        q = q.filter(m.Task.assigned_staff_id == user.staff_id)
    elif staff_id is not None:
        q = q.filter(m.Task.assigned_staff_id == staff_id)
    tasks = q.order_by(m.Task.created_at.desc()).all()
    return [_serialize(t, db) for t in tasks]


class TaskUpdate(BaseModel):
    status: str | None = None  # in_progress | completed | cancelled
    notes: str | None = None


@router.patch("/{task_id}")
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.query(m.Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if user.role == "staff" and task.assigned_staff_id != user.staff_id:
        raise HTTPException(status_code=403, detail="This task is not assigned to you")

    if payload.notes is not None:
        task.notes = payload.notes

    if payload.status == "in_progress" and task.status in ("pending", "assigned"):
        task.status = "in_progress"
        task.started_at = dt.datetime.utcnow()
        db.add(m.AuditLog(actor=user.name, action="task_started", detail=f"Task #{task.id} started"))

    elif payload.status == "completed" and task.status != "completed":
        task.status = "completed"
        task.completed_at = dt.datetime.utcnow()
        db.add(m.AuditLog(actor=user.name, action="task_completed", detail=f"Task #{task.id} completed"))

        # --- Closed loop: recalculate maintenance risk after task completion ---
        before_metric, after_metric = None, None
        if task.category == "maintenance" and task.recommendation_id:
            rec = db.query(m.AIRecommendation).get(task.recommendation_id)
            pred = db.query(m.AIPrediction).get(rec.prediction_id) if rec else None
            if pred and pred.subject_id:
                before_metric = pred.risk_score
                # simulate the effect of completed preventive maintenance
                improved = predict_risk({
                    "energy_deviation_pct": 1.0, "temperature_deviation_c": 0.3,
                    "vibration_index": 0.6, "runtime_hours_weekly": 40.0,
                    "days_since_maintenance": 0.0, "equipment_age_years": 3.0,
                })
                after_metric = improved["risk_score"]
                pred.risk_score = after_metric
                pred.explanation = "Risk lowered after preventive maintenance was completed; readings back within normal range."
                equipment = db.query(m.Equipment).get(pred.subject_id)
                if equipment:
                    db.add(m.MaintenanceRecord(equipment_id=equipment.id, type="preventive_maintenance",
                                                notes=task.notes or "Preventive maintenance completed."))
                db.add(m.Alert(severity="low",
                                message=f"{pred.subject_label} — risk reduced to {after_metric}% after maintenance",
                                source_module="maintenance"))

        db.add(m.TaskOutcome(task_id=task.id, before_metric=before_metric or 0,
                              after_metric=after_metric if after_metric is not None else 0,
                              note="Task completed" + (f"; risk {before_metric}% → {after_metric}%" if before_metric else "")))

    elif payload.status == "cancelled":
        task.status = "cancelled"

    db.commit()
    db.refresh(task)
    result = _serialize(task, db)
    manager.broadcast({"type": "task_update", "task": result})
    return result
