from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import models as m

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    alerts = db.query(m.Alert).order_by(m.Alert.created_at.desc()).limit(30).all()
    return [
        {"id": a.id, "severity": a.severity, "message": a.message,
         "source_module": a.source_module, "created_at": a.created_at.isoformat(),
         "is_read": a.is_read}
        for a in alerts
    ]


@router.post("/{alert_id}/read")
def mark_read(alert_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    a = db.query(m.Alert).get(alert_id)
    if a:
        a.is_read = True
        db.commit()
    return {"ok": True}
