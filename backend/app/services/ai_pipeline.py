from sqlalchemy.orm import Session
from app.models import models as m


def upsert_prediction_and_recommendation(
    db: Session,
    module: str,
    subject_type: str,
    subject_id: int,
    subject_label: str,
    risk_score: float,
    confidence: float,
    explanation: str,
    features_json: str = "{}",
    severity: str | None = None,
    title: str | None = None,
    description: str | None = None,
    expected_impact: str | None = None,
    create_recommendation: bool = True,
):
    """
    Always refreshes the latest prediction snapshot for this subject.
    Only creates a NEW recommendation if none is currently pending/approved
    for this subject, so repeated GETs don't spam duplicate recommendations.
    """
    pred = m.AIPrediction(
        module=module, subject_type=subject_type, subject_id=subject_id, subject_label=subject_label,
        risk_score=risk_score, confidence=confidence, features_json=features_json, explanation=explanation,
    )
    db.add(pred)
    db.flush()

    existing = (
        db.query(m.AIRecommendation)
        .join(m.AIPrediction, m.AIRecommendation.prediction_id == m.AIPrediction.id)
        .filter(
            m.AIPrediction.module == module,
            m.AIPrediction.subject_type == subject_type,
            m.AIPrediction.subject_id == subject_id,
            m.AIRecommendation.status.in_(["pending", "approved"]),
        )
        .order_by(m.AIRecommendation.created_at.desc())
        .first()
    )

    if existing:
        return pred, existing

    if create_recommendation and title:
        rec = m.AIRecommendation(
            prediction_id=pred.id, title=title, description=description or explanation,
            severity=severity or "medium", status="pending", expected_impact=expected_impact or "",
        )
        db.add(rec)
        db.flush()
        return pred, rec

    return pred, None
