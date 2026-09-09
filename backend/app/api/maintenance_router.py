import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_role
from app.models import models as m

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/risks")
def list_risks(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    preds = (
        db.query(m.AIPrediction)
        .filter(m.AIPrediction.module == "maintenance")
        .order_by(m.AIPrediction.risk_score.desc())
        .all()
    )
    out = []
    for p in preds:
        equipment = db.query(m.Equipment).get(p.subject_id)
        rec = db.query(m.AIRecommendation).filter(m.AIRecommendation.prediction_id == p.id).first()
        out.append({
            "prediction_id": p.id,
            "equipment_id": p.subject_id,
            "equipment_name": p.subject_label,
            "location": equipment.location if equipment else "",
            "risk_score": p.risk_score,
            "confidence": p.confidence,
            "status": ("CRITICAL" if p.risk_score >= 75 else "HIGH" if p.risk_score >= 50
                       else "MEDIUM" if p.risk_score >= 25 else "LOW"),
            "explanation": p.explanation,
            "recommendation": ({
                "id": rec.id, "title": rec.title, "description": rec.description,
                "severity": rec.severity, "status": rec.status, "expected_impact": rec.expected_impact,
            } if rec else None),
        })
    return out


@router.get("/risks/{prediction_id}/explanation")
def explanation(prediction_id: int, db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    p = db.query(m.AIPrediction).get(prediction_id)
    if not p:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {
        "risk_score": p.risk_score,
        "confidence": p.confidence,
        "explanation": p.explanation,
        "contributions": json.loads(p.features_json) if p.features_json else [],
    }
