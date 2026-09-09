from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import require_role
from app.models import models as m
from app.ml.staffing import department_requirement, ROOMS_PER_STAFF
from app.services.ai_pipeline import upsert_prediction_and_recommendation

router = APIRouter(prefix="/staff", tags=["staffing"])


DEPARTMENT_IDS = {name: i + 1 for i, name in enumerate(ROOMS_PER_STAFF.keys())}


@router.get("/recommendations")
def staffing_recommendations(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    latest_occ = db.query(m.OccupancyRecord).order_by(m.OccupancyRecord.date.desc()).first()
    occupancy_pct = latest_occ.occupancy_pct if latest_occ else 75.0
    total_rooms = db.query(m.Room).count() or 1

    out = []
    for department in ROOMS_PER_STAFF.keys():
        current_staff = db.query(m.Staff).filter(m.Staff.department == department).count()
        result = department_requirement(department, current_staff, occupancy_pct, total_rooms)

        rec = None
        if result["gap"] > 0:
            severity = "high" if result["gap"] >= 3 else "medium"
            _, rec = upsert_prediction_and_recommendation(
                db, module="staffing", subject_type="department", subject_id=DEPARTMENT_IDS[department],
                subject_label=department, risk_score=result["risk_score"], confidence=result["confidence"],
                explanation=result["explanation"],
                severity=severity, title=f"{department} needs additional evening staff",
                description=result["recommendation_text"],
                expected_impact=f"Closes a {result['gap']}-person staffing gap during peak turnover.",
            )
            db.commit()

        out.append({
            "department": department,
            "current_staff": result["current_staff"],
            "required_staff": result["required_staff"],
            "gap": result["gap"],
            "explanation": result["explanation"],
            "recommendation": ({
                "id": rec.id, "title": rec.title, "description": rec.description,
                "severity": rec.severity, "status": rec.status, "expected_impact": rec.expected_impact,
            } if rec else None),
        })
    out.sort(key=lambda x: x["gap"], reverse=True)
    return out
