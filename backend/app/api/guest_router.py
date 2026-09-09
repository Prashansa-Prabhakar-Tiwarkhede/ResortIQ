import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.auth import require_role
from app.models import models as m
from app.services.realtime import manager

router = APIRouter(prefix="/guest", tags=["guest"])

SERVICES = [
    {"id": "spa", "name": "Spa & Wellness", "description": "Signature massages, sauna, and steam rooms overlooking the valley."},
    {"id": "restaurant", "name": "Restaurant", "description": "Farm-to-table dining with regional and international menus."},
    {"id": "pool", "name": "Infinity Pool", "description": "Open 6 AM – 10 PM, poolside service available."},
    {"id": "activities", "name": "Activities", "description": "Guided treks, cycling tours, and cultural excursions."},
    {"id": "room_service", "name": "Room Service", "description": "Available 24/7 across all room categories."},
    {"id": "events", "name": "Events", "description": "Sunset yoga, live music evenings, and cooking classes."},
]


@router.get("/services")
def services():
    return SERVICES


@router.get("/recommendations")
def personalized_recommendations(db: Session = Depends(get_db), user=Depends(require_role("guest"))):
    prefs = db.query(m.GuestPreference).filter(m.GuestPreference.guest_id == user.guest_id).all()
    if not prefs:
        return [{"title": "Explore Azure Valley Resort", "reason": "Popular with most guests this week.", "service": "activities"}]
    top = sorted(prefs, key=lambda p: p.weight, reverse=True)[:2]
    mapping = {
        "wellness": ("Sunset yoga session", "spa"),
        "adventure": ("Guided valley trek", "activities"),
        "dining": ("Chef's tasting menu", "restaurant"),
        "cultural": ("Local artisan market tour", "activities"),
        "relaxation": ("Poolside cabana afternoon", "pool"),
    }
    out = []
    for p in top:
        title, service = mapping.get(p.category, ("Resort experience", "activities"))
        out.append({
            "title": title,
            "reason": f"Because you enjoyed {p.category} activities, you may like this.",
            "service": service,
        })
    return out


class GuestRequestCreate(BaseModel):
    text: str
    category: str = "general"


@router.post("/requests")
def create_request(payload: GuestRequestCreate, db: Session = Depends(get_db), user=Depends(require_role("guest"))):
    req = m.GuestRequest(guest_id=user.guest_id, text=payload.text, category=payload.category, status="pending")
    db.add(req)
    db.flush()

    # Auto-create an operational task, connecting guest experience to staff ops
    staff = db.query(m.Staff).filter(m.Staff.department == "Housekeeping").first()
    task = m.Task(
        title=f"Guest request: {payload.text[:60]}",
        description=payload.text,
        category="guest_request",
        priority="normal",
        assigned_staff_id=staff.id if staff else None,
        status="assigned" if staff else "pending",
        due_at=dt.datetime.utcnow() + dt.timedelta(hours=2),
        ai_source="Guest portal",
    )
    db.add(task)
    db.flush()
    req.task_id = task.id
    req.status = "assigned"

    db.add(m.Alert(severity="low", message=f"Guest request: {payload.text[:60]}", source_module="guest"))
    db.commit()
    db.refresh(req)
    manager.broadcast({"type": "alert", "message": f"Guest request: {payload.text[:60]}", "severity": "low"})
    return {"id": req.id, "status": req.status, "task_id": req.task_id}


@router.get("/requests")
def list_my_requests(db: Session = Depends(get_db), user=Depends(require_role("guest"))):
    reqs = db.query(m.GuestRequest).filter(m.GuestRequest.guest_id == user.guest_id).order_by(m.GuestRequest.created_at.desc()).all()
    out = []
    for r in reqs:
        task_status = None
        if r.task_id:
            t = db.query(m.Task).get(r.task_id)
            task_status = t.status if t else None
        out.append({
            "id": r.id, "text": r.text, "category": r.category,
            "status": task_status or r.status, "created_at": r.created_at.isoformat(),
        })
    return out


class ReviewCreate(BaseModel):
    text: str


POSITIVE_WORDS = {"amazing", "wonderful", "great", "excellent", "love", "loved", "beautiful", "friendly", "clean", "attentive", "spacious", "quiet"}
NEGATIVE_WORDS = {"slow", "delay", "delayed", "long", "frustrating", "disconnect", "disconnecting", "wait", "too", "cold", "dirty", "rude"}

TOPIC_KEYWORDS = {
    "Housekeeping": {"housekeeping", "towel", "towels", "cleaning", "clean", "room"},
    "Wi-Fi": {"wifi", "wi-fi", "internet", "connection", "disconnect", "disconnecting"},
    "Restaurant": {"restaurant", "food", "dining", "menu", "breakfast"},
    "Response Time": {"response", "wait", "waiting", "slow", "delay", "delayed", "long"},
    "Staff": {"staff", "friendly", "attentive", "service", "rude"},
    "Spa": {"spa", "massage", "wellness"},
    "Pool": {"pool", "swim", "swimming"},
    "Villa": {"villa", "suite", "value", "spacious"},
    "Room Service": {"room service"},
}


def _extract_topics(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            found.append(topic)
    return found or ["General"]


def _score_sentiment(text: str):
    words = set(text.lower().replace(".", "").replace(",", "").split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    score = max(-1.0, min(1.0, (pos - neg) / max(pos + neg, 1)))
    label = "positive" if score > 0.2 else ("negative" if score < -0.2 else "neutral")
    return round(score, 2), label


@router.post("/reviews")
def submit_review(payload: ReviewCreate, db: Session = Depends(get_db), user=Depends(require_role("guest"))):
    score, label = _score_sentiment(payload.text)
    topics = ",".join(_extract_topics(payload.text))
    review = m.Review(guest_id=user.guest_id, text=payload.text, sentiment_score=score, sentiment_label=label, topics=topics)
    db.add(review)
    db.commit()
    db.refresh(review)

    if label == "negative":
        db.add(m.Alert(severity="medium", message=f"New negative review: {payload.text[:60]}", source_module="sentiment"))
        db.commit()
        manager.broadcast({"type": "alert", "message": f"New negative review: {payload.text[:60]}", "severity": "medium"})

    return {"id": review.id, "sentiment_score": score, "sentiment_label": label, "topics": topics}


@router.get("/sentiment")
def sentiment_analytics(db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    reviews = db.query(m.Review).order_by(m.Review.created_at.asc()).all()
    total = len(reviews) or 1

    positive = sum(1 for r in reviews if r.sentiment_label == "positive")
    neutral = sum(1 for r in reviews if r.sentiment_label == "neutral")
    negative = sum(1 for r in reviews if r.sentiment_label == "negative")

    topic_counts: dict[str, int] = {}
    for r in reviews:
        for topic in (r.topics or "General").split(","):
            topic = topic.strip() or "General"
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

    top_issues = sorted(
        [{"topic": t, "count": c, "pct": round(c / total * 100, 1)} for t, c in topic_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )[:5]

    recent = [
        {"id": r.id, "text": r.text, "sentiment_label": r.sentiment_label, "sentiment_score": r.sentiment_score,
         "topics": r.topics, "created_at": r.created_at.isoformat()}
        for r in reversed(reviews[-10:])
    ]

    avg_score = round(sum(r.sentiment_score for r in reviews) / total, 2) if reviews else 0

    return {
        "total_reviews": len(reviews),
        "positive_pct": round(positive / total * 100, 1),
        "neutral_pct": round(neutral / total * 100, 1),
        "negative_pct": round(negative / total * 100, 1),
        "average_score": avg_score,
        "top_issues": top_issues,
        "recent_reviews": recent,
        "recommended_action": (
            f"Increase {top_issues[0]['topic'].lower()} coverage during peak hours."
            if top_issues and top_issues[0]["topic"] in ("Housekeeping", "Response Time")
            else "Sentiment is trending healthy — no immediate action needed."
        ),
    }
