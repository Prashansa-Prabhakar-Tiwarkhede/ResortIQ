import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base


def now():
    return dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # manager | staff | guest
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=True)
    name = Column(String, nullable=False)


class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    shift = Column(String, default="morning")
    phone = Column(String, default="")
    tasks = relationship("Task", back_populates="assigned_staff")


class Guest(Base):
    __tablename__ = "guests"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, default="")
    phone = Column(String, default="")
    tier = Column(String, default="standard")


class GuestPreference(Base):
    __tablename__ = "guest_preferences"
    id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.id"))
    category = Column(String)
    weight = Column(Float, default=1.0)


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True)
    number = Column(String, unique=True)
    type = Column(String)  # Deluxe/Premium/Suite/Villa
    block = Column(String)
    price = Column(Float)


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    guest_id = Column(Integer, ForeignKey("guests.id"))
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    status = Column(String, default="confirmed")


class OccupancyRecord(Base):
    __tablename__ = "occupancy_records"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    occupancy_pct = Column(Float)
    revenue = Column(Float)


class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    location = Column(String)
    install_date = Column(DateTime)
    readings = relationship("EquipmentReading", back_populates="equipment")


class EquipmentReading(Base):
    __tablename__ = "equipment_readings"
    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    ts = Column(DateTime, default=now)
    temperature = Column(Float)
    energy = Column(Float)
    vibration = Column(Float)
    runtime_hours = Column(Float)
    days_since_maintenance = Column(Integer)
    equipment = relationship("Equipment", back_populates="readings")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    date = Column(DateTime, default=now)
    type = Column(String)
    notes = Column(Text, default="")


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    unit = Column(String)
    current_stock = Column(Float)
    avg_daily_usage = Column(Float)


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"))
    ts = Column(DateTime, default=now)
    delta = Column(Float)
    reason = Column(String)


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.id"))
    text = Column(Text)
    sentiment_score = Column(Float)
    sentiment_label = Column(String)
    topics = Column(String, default="")
    created_at = Column(DateTime, default=now)


class GuestRequest(Base):
    __tablename__ = "guest_requests"
    id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.id"))
    text = Column(Text)
    category = Column(String, default="general")
    status = Column(String, default="pending")
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    created_at = Column(DateTime, default=now)


class AIPrediction(Base):
    __tablename__ = "ai_predictions"
    id = Column(Integer, primary_key=True)
    module = Column(String)  # maintenance | demand | inventory | sentiment | staffing | revenue
    subject_type = Column(String)  # equipment | resort | inventory_item ...
    subject_id = Column(Integer, nullable=True)
    subject_label = Column(String)
    risk_score = Column(Float)
    confidence = Column(Float)
    features_json = Column(Text)  # JSON string of feature contributions
    explanation = Column(Text)
    created_at = Column(DateTime, default=now)


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"
    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey("ai_predictions.id"))
    title = Column(String)
    description = Column(Text)
    severity = Column(String)  # critical | high | medium | low
    status = Column(String, default="pending")  # pending | approved | rejected
    expected_impact = Column(String)
    created_at = Column(DateTime, default=now)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String, nullable=True)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    recommendation_id = Column(Integer, ForeignKey("ai_recommendations.id"), nullable=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    priority = Column(String, default="normal")  # low|normal|high|critical
    assigned_staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    location = Column(String, default="")
    status = Column(String, default="pending")  # pending|assigned|in_progress|completed|cancelled
    created_at = Column(DateTime, default=now)
    due_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, default="")
    ai_source = Column(String, default="")
    expected_impact = Column(String, default="")

    assigned_staff = relationship("Staff", back_populates="tasks")


class TaskOutcome(Base):
    __tablename__ = "task_outcomes"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    before_metric = Column(Float)
    after_metric = Column(Float)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=now)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    severity = Column(String)  # critical|high|medium|low
    message = Column(String)
    source_module = Column(String)
    created_at = Column(DateTime, default=now)
    is_read = Column(Boolean, default=False)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    actor = Column(String)
    action = Column(String)
    detail = Column(String, default="")
    ts = Column(DateTime, default=now)
