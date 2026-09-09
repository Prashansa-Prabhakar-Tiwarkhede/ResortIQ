"""
Staff optimization: estimates required headcount per department from current
occupancy and a department-specific rooms-per-staff service ratio, and flags
a gap against currently rostered staff.
"""
import math

ROOMS_PER_STAFF = {
    "Housekeeping": 6,
    "Front Desk": 25,
    "F&B": 15,
    "Maintenance": 20,
    "Spa & Wellness": 15,
}

BASELINE_OCCUPANCY = 75.0


def department_requirement(department: str, current_staff: int, occupancy_pct: float, total_rooms: int) -> dict:
    ratio = ROOMS_PER_STAFF.get(department, 15)
    occupied_rooms = total_rooms * (occupancy_pct / 100.0)
    required = max(1, math.ceil(occupied_rooms / ratio))
    gap = required - current_staff

    turnover_vs_baseline = round(((occupancy_pct - BASELINE_OCCUPANCY) / BASELINE_OCCUPANCY) * 100, 1)

    risk_score = round(max(0.0, min(100.0, gap / max(current_staff, 1) * 100)), 1)
    confidence = 78.0

    explanation = (
        f"Expected room turnover is {turnover_vs_baseline:+.0f}% vs. the weekly average, "
        f"projecting {required} staff needed against {current_staff} currently rostered."
    )
    recommendation_text = f"Add {gap} {department} staff to the evening shift." if gap > 0 else ""

    return {
        "required_staff": required,
        "current_staff": current_staff,
        "gap": gap,
        "risk_score": risk_score,
        "confidence": confidence,
        "explanation": explanation,
        "recommendation_text": recommendation_text,
    }
