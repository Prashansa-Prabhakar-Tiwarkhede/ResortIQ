"""
Predictive maintenance model.

Trains a RandomForestClassifier on synthetically generated but realistic
sensor histories (energy deviation, temperature deviation, vibration,
runtime hours, days since last maintenance, equipment age) labeled with a
failure/no-failure outcome. This is a real, trained model (not a hard-coded
number) - in a production deployment this would train on the resort's
actual historical sensor + failure-ticket data via the same feature schema.

The module also produces a human-readable explanation by ranking the
feature contributions (feature value vs. "normal" baseline, weighted by the
model's global feature importances) - a lightweight, transparent stand-in
for SHAP that's fast enough to run on every request.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier

FEATURE_NAMES = [
    "energy_deviation_pct",
    "temperature_deviation_c",
    "vibration_index",
    "runtime_hours_weekly",
    "days_since_maintenance",
    "equipment_age_years",
]

# "Normal" baselines used to describe how far a reading is from expected.
BASELINE = {
    "energy_deviation_pct": 2.0,
    "temperature_deviation_c": 0.5,
    "vibration_index": 1.0,
    "runtime_hours_weekly": 60.0,
    "days_since_maintenance": 30.0,
    "equipment_age_years": 3.0,
}

_model: RandomForestClassifier | None = None


def _generate_training_data(n=6000, seed=42):
    """
    Each feature is drawn independently, then converted to a 0-1 "abnormality"
    score relative to a realistic operating range, weighted, and thresholded
    to produce the failure label. Noise is kept small relative to signal so
    the learned probabilities stay well-calibrated and explainable.
    """
    rng = np.random.default_rng(seed)
    X = np.zeros((n, len(FEATURE_NAMES)))
    y = np.zeros(n, dtype=int)

    # (min, max) realistic operating ranges used to normalize abnormality
    ranges = {
        "energy_deviation_pct": (0, 25),
        "temperature_deviation_c": (0, 9),
        "vibration_index": (0.2, 3.0),
        "runtime_hours_weekly": (20, 100),
        "days_since_maintenance": (0, 90),
        "equipment_age_years": (0, 15),
    }
    weights = {
        "energy_deviation_pct": 0.22,
        "temperature_deviation_c": 0.22,
        "vibration_index": 0.20,
        "runtime_hours_weekly": 0.14,
        "days_since_maintenance": 0.16,
        "equipment_age_years": 0.06,
    }

    for i in range(n):
        energy_dev = np.clip(rng.gamma(2.0, 3.0), 0, 30)
        temp_dev = np.clip(rng.gamma(1.5, 1.2), 0, 12)
        vibration = np.clip(rng.gamma(2.0, 0.6), 0.1, 4)
        runtime = np.clip(rng.normal(60, 20), 10, 110)
        days_since_maint = np.clip(rng.gamma(1.8, 18), 0, 150)
        age = np.clip(rng.gamma(2.0, 2.0), 0, 20)

        raw = {
            "energy_deviation_pct": energy_dev, "temperature_deviation_c": temp_dev,
            "vibration_index": vibration, "runtime_hours_weekly": runtime,
            "days_since_maintenance": days_since_maint, "equipment_age_years": age,
        }
        risk = 0.0
        for f, (lo, hi) in ranges.items():
            norm = np.clip((raw[f] - lo) / (hi - lo), 0, 1)
            risk += weights[f] * norm
        risk += rng.normal(0, 0.03)  # small label noise
        failed = 1 if risk > 0.42 else 0

        X[i] = [energy_dev, temp_dev, vibration, runtime, days_since_maint, age]
        y[i] = failed
    return X, y


def get_model() -> RandomForestClassifier:
    global _model
    if _model is None:
        X, y = _generate_training_data()
        _model = RandomForestClassifier(
            n_estimators=200, max_depth=6, random_state=42, class_weight="balanced"
        )
        _model.fit(X, y)
    return _model


def predict_risk(features: dict) -> dict:
    """
    features: dict with keys matching FEATURE_NAMES
    returns: risk_score (0-100), confidence (0-100), status label, explanation text,
             and ranked feature contributions.
    """
    model = get_model()
    x = np.array([[features[f] for f in FEATURE_NAMES]])
    proba = model.predict_proba(x)[0]
    failure_proba = float(proba[1]) if len(proba) > 1 else float(proba[0])
    risk_score = round(failure_proba * 100, 1)

    # confidence: how far the tree votes agree (spread across trees)
    tree_votes = np.array([t.predict(x)[0] for t in model.estimators_])
    agreement = max(tree_votes.mean(), 1 - tree_votes.mean())
    confidence = round(agreement * 100, 1)

    if risk_score >= 75:
        status = "CRITICAL"
    elif risk_score >= 50:
        status = "HIGH"
    elif risk_score >= 25:
        status = "MEDIUM"
    else:
        status = "LOW"

    importances = model.feature_importances_
    contributions = []
    for i, fname in enumerate(FEATURE_NAMES):
        val = features[fname]
        baseline = BASELINE[fname]
        deviation = val - baseline
        contributions.append({
            "feature": fname,
            "value": round(val, 1),
            "baseline": baseline,
            "deviation": round(deviation, 1),
            "importance": round(float(importances[i]), 3),
            "impact": round(float(importances[i]) * max(deviation, 0), 3),
        })
    contributions.sort(key=lambda c: c["impact"], reverse=True)

    explanation_parts = []
    label_map = {
        "energy_deviation_pct": lambda c: f"abnormal energy consumption (+{c['deviation']:.0f}% above baseline)",
        "temperature_deviation_c": lambda c: f"temperature anomaly (+{c['deviation']:.1f}°C above normal)",
        "vibration_index": lambda c: f"elevated vibration levels ({c['value']:.1f}x baseline)",
        "runtime_hours_weekly": lambda c: f"high weekly runtime ({c['value']:.0f} hrs)",
        "days_since_maintenance": lambda c: f"maintenance overdue by {c['deviation']:.0f} days",
        "equipment_age_years": lambda c: f"equipment age ({c['value']:.1f} years)",
    }
    for c in contributions[:4]:
        if c["deviation"] > 0.5:
            explanation_parts.append(label_map[c["feature"]](c))

    if explanation_parts:
        explanation = "Risk increased because of " + ", ".join(explanation_parts) + "."
    else:
        explanation = "All monitored readings are within normal operating ranges."

    return {
        "risk_score": risk_score,
        "confidence": confidence,
        "status": status,
        "explanation": explanation,
        "contributions": contributions,
    }
