"""
Seeds the ResortIQ demo database with realistic data for "Azure Valley Resort".
Run with: python seed.py
"""
import datetime as dt
import random
import json

from app.database import Base, engine, SessionLocal
from app.models import models as m
from app.auth import hash_password
from app.ml.maintenance import predict_risk, FEATURE_NAMES

random.seed(7)

FIRST_NAMES = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Rohan", "Kavya",
               "Arjun", "Neha", "Karan", "Divya", "Suresh", "Meera", "Aditya", "Pooja",
               "Manoj", "Ritu", "Sandeep", "Isha"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Iyer", "Reddy", "Nair", "Gupta", "Singh",
              "Kapoor", "Menon", "Rao", "Das", "Malhotra", "Chopra", "Bose"]

ROOM_TYPES = [("Deluxe", 7999), ("Premium", 11999), ("Suite", 18999), ("Villa", 32999)]
BLOCKS = ["A", "B", "C", "D"]
DEPARTMENTS = ["Maintenance", "Housekeeping", "Front Desk", "F&B", "Spa & Wellness"]
EQUIPMENT_TYPES = [
    ("AC Unit", "HVAC"), ("Elevator", "Vertical Transport"), ("Generator", "Power"),
    ("Water Pump", "Plumbing"), ("Refrigerator", "Kitchen"), ("Pool Filtration", "Pool"),
]
INVENTORY = [
    ("Milk", "L", 42, 28), ("Bath Towels", "pcs", 320, 45), ("Bedsheets", "pcs", 180, 22),
    ("Toiletry Kits", "pcs", 260, 40), ("Drinking Water Bottles", "pcs", 900, 210),
    ("Cleaning Solution", "L", 60, 9), ("Coffee Beans", "kg", 35, 6), ("Table Linen", "pcs", 140, 18),
]
GUEST_PREF_CATEGORIES = ["wellness", "adventure", "dining", "cultural", "relaxation"]
REVIEW_TEMPLATES = [
    ("The room was beautiful but housekeeping took too long to respond.", -0.5, "Housekeeping,Response Time"),
    ("Amazing stay! The spa and pool were wonderful.", 0.8, "Spa,Pool"),
    ("Wi-Fi kept disconnecting throughout our stay, quite frustrating.", -0.6, "Wi-Fi"),
    ("Loved the sunset yoga session, staff were attentive.", 0.7, "Activities,Staff"),
    ("Food was good but the restaurant wait time was too long.", -0.3, "Restaurant,Wait Time"),
    ("Excellent service overall, will definitely come back.", 0.9, "Service"),
    ("Room service was slow during peak hours.", -0.4, "Room Service"),
    ("Beautiful property, clean rooms, friendly staff.", 0.85, "Cleanliness,Staff"),
    ("Housekeeping delayed our towel request by over an hour.", -0.55, "Housekeeping"),
    ("Great value for money, the villa was spacious and quiet.", 0.75, "Villa,Value"),
]


def wipe_and_create():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def run():
    wipe_and_create()
    db = SessionLocal()

    # ---------- Staff ----------
    staff_list = []
    for i in range(18):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        dept = DEPARTMENTS[i % len(DEPARTMENTS)]
        s = m.Staff(name=name, department=dept, shift=random.choice(["morning", "evening", "night"]),
                    phone=f"98{random.randint(10000000,99999999)}")
        db.add(s)
        staff_list.append(s)
    db.flush()

    # ---------- Guests ----------
    guests = []
    for i in range(35):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        g = m.Guest(name=name, email=f"{name.split()[0].lower()}{i}@example.com",
                    phone=f"98{random.randint(10000000,99999999)}",
                    tier=random.choice(["standard", "standard", "gold", "platinum"]))
        db.add(g)
        guests.append(g)
    db.flush()

    for g in guests:
        for cat in random.sample(GUEST_PREF_CATEGORIES, k=random.randint(1, 3)):
            db.add(m.GuestPreference(guest_id=g.id, category=cat, weight=round(random.uniform(0.4, 1.0), 2)))

    # ---------- Rooms ----------
    rooms = []
    room_no = 100
    for block in BLOCKS:
        room_no = 100
        for _ in range(13):
            rtype, price = random.choice(ROOM_TYPES)
            r = m.Room(number=f"{block}{room_no}", type=rtype, block=f"Block {block}",
                       price=price + random.randint(-500, 1500))
            db.add(r)
            rooms.append(r)
            room_no += 1
    db.flush()

    # ---------- Bookings ----------
    today = dt.datetime.utcnow()
    for _ in range(120):
        room = random.choice(rooms)
        guest = random.choice(guests)
        start_offset = random.randint(-20, 10)
        check_in = today + dt.timedelta(days=start_offset)
        check_out = check_in + dt.timedelta(days=random.randint(1, 5))
        status = "checked_out" if check_out < today else ("checked_in" if check_in <= today else "confirmed")
        db.add(m.Booking(room_id=room.id, guest_id=guest.id, check_in=check_in, check_out=check_out, status=status))

    # ---------- Occupancy history (last 21 days) ----------
    base = 70
    for i in range(21, 0, -1):
        date = today - dt.timedelta(days=i)
        weekday_bump = [0, 2, 4, 8, 14, 20, 12][date.weekday()]
        occ = min(98, max(45, base + weekday_bump + random.randint(-5, 5)))
        revenue = occ * 1350 * random.uniform(0.9, 1.1)
        db.add(m.OccupancyRecord(date=date, occupancy_pct=occ, revenue=round(revenue, 2)))

    # ---------- Equipment + readings (drives predictive maintenance) ----------
    equipment_objs = []
    for i in range(1, 23):
        etype, category = EQUIPMENT_TYPES[i % len(EQUIPMENT_TYPES)]
        install = today - dt.timedelta(days=random.randint(180, 3000))
        e = m.Equipment(name=f"{etype} #{i}", type=category,
                         location=f"Block {random.choice(BLOCKS)} / Floor {random.randint(1,4)}",
                         install_date=install)
        db.add(e)
        equipment_objs.append(e)
    db.flush()

    # Make Equipment #? an obvious "AC Unit #27"-style hero case for the demo.
    hero = None
    for e in equipment_objs:
        if e.name.startswith("AC Unit"):
            hero = e
            break

    equipment_features = {}
    for e in equipment_objs:
        age_years = (today - e.install_date).days / 365
        is_hero = (hero is not None and e.id == hero.id)
        if is_hero:
            energy_dev, temp_dev, vib, runtime, days_since_maint = 18.0, 7.0, 2.6, 92.0, 23.0
        else:
            energy_dev = max(0, random.gauss(3, 6))
            temp_dev = max(0, random.gauss(0.5, 2))
            vib = max(0.1, random.gauss(1.0, 0.6))
            runtime = max(10, random.gauss(60, 20))
            days_since_maint = max(1, random.gauss(30, 20))

        db.add(m.EquipmentReading(
            equipment_id=e.id, ts=today, temperature=22 + temp_dev, energy=100 + energy_dev,
            vibration=vib, runtime_hours=runtime, days_since_maintenance=int(days_since_maint),
        ))
        equipment_features[e.id] = {
            "energy_deviation_pct": energy_dev, "temperature_deviation_c": temp_dev,
            "vibration_index": vib, "runtime_hours_weekly": runtime,
            "days_since_maintenance": days_since_maint, "equipment_age_years": age_years,
        }
        db.add(m.MaintenanceRecord(equipment_id=e.id,
                                    date=today - dt.timedelta(days=int(days_since_maint)),
                                    type="routine_inspection", notes="Standard scheduled inspection."))

    # ---------- Inventory ----------
    inventory_objs = []
    for name, unit, stock, usage in INVENTORY:
        item = m.InventoryItem(name=name, unit=unit, current_stock=stock, avg_daily_usage=usage)
        db.add(item)
        inventory_objs.append(item)
    db.flush()

    # ---------- Reviews ----------
    for guest in random.sample(guests, k=20):
        text, score, topics = random.choice(REVIEW_TEMPLATES)
        label = "positive" if score > 0.2 else ("negative" if score < -0.2 else "neutral")
        db.add(m.Review(guest_id=guest.id, text=text, sentiment_score=score,
                         sentiment_label=label, topics=topics,
                         created_at=today - dt.timedelta(days=random.randint(0, 20))))

    db.commit()

    # ---------- AI predictions + recommendations (real inference, not hard-coded) ----------
    for e in equipment_objs:
        feats = equipment_features[e.id]
        result = predict_risk(feats)
        pred = m.AIPrediction(
            module="maintenance", subject_type="equipment", subject_id=e.id, subject_label=e.name,
            risk_score=result["risk_score"], confidence=result["confidence"],
            features_json=json.dumps(result["contributions"]), explanation=result["explanation"],
        )
        db.add(pred)
        db.flush()

        if result["risk_score"] >= 50:
            severity = "critical" if result["risk_score"] >= 75 else "high"
            rec = m.AIRecommendation(
                prediction_id=pred.id,
                title=f"{e.name} needs preventive maintenance",
                description=f"{result['explanation']} Schedule preventive maintenance within the next 24 hours.",
                severity=severity, status="pending",
                expected_impact=f"Reduces failure risk from {result['risk_score']}% to an estimated single digits and avoids unplanned downtime.",
            )
            db.add(rec)
            db.flush()
            db.add(m.Alert(severity=severity,
                            message=f"{e.name} — {result['status']} failure risk ({result['risk_score']}%)",
                            source_module="maintenance"))

    # A couple of inventory / demand / staffing alerts for the "What needs my attention" panel
    milk = next(i for i in inventory_objs if i.name == "Milk")
    days_remaining = round(milk.current_stock / milk.avg_daily_usage, 1)
    if days_remaining < 3:
        db.add(m.Alert(severity="medium",
                        message=f"{milk.name} inventory may run out in {days_remaining} days",
                        source_module="inventory"))
        pred = m.AIPrediction(module="inventory", subject_type="inventory_item", subject_id=milk.id,
                               subject_label=milk.name, risk_score=round((1 - days_remaining/3)*100, 1),
                               confidence=88, features_json="{}",
                               explanation=f"Current stock ({milk.current_stock}{milk.unit}) covers only {days_remaining} days at the predicted usage rate of {milk.avg_daily_usage}{milk.unit}/day.")
        db.add(pred)
        db.flush()
        db.add(m.AIRecommendation(prediction_id=pred.id, title=f"Reorder {milk.name}",
                                   description=f"Reorder {int(milk.avg_daily_usage*3)}{milk.unit} of {milk.name} before tomorrow morning to avoid stockout.",
                                   severity="medium", status="pending",
                                   expected_impact="Avoids service disruption to F&B and room service."))

    db.add(m.Alert(severity="medium", message="Weekend occupancy expected to reach 94%+", source_module="demand"))

    db.commit()

    # ---------- Users (demo credentials) ----------
    demo_staff = staff_list[0]
    demo_guest = guests[0]
    users = [
        m.User(email="manager@resortiq.demo", password_hash=hash_password("demo1234"),
               role="manager", name="Resort Manager"),
        m.User(email="staff@resortiq.demo", password_hash=hash_password("demo1234"),
               role="staff", staff_id=demo_staff.id, name=demo_staff.name),
        m.User(email="guest@resortiq.demo", password_hash=hash_password("demo1234"),
               role="guest", guest_id=demo_guest.id, name=demo_guest.name),
    ]
    db.add_all(users)
    db.commit()

    print("Seed complete:")
    print(f"  Rooms: {len(rooms)}  Staff: {len(staff_list)}  Guests: {len(guests)}")
    print(f"  Equipment: {len(equipment_objs)}  Inventory items: {len(inventory_objs)}")
    if hero:
        print(f"  Hero maintenance demo unit: {hero.name} (id={hero.id})")
    print("  Demo logins: manager@resortiq.demo / staff@resortiq.demo / guest@resortiq.demo  (password: demo1234)")
    db.close()


if __name__ == "__main__":
    run()
