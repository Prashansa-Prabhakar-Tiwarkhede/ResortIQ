-- ResortIQ database schema (Postgres/Supabase dialect)
-- The running app uses SQLAlchemy models (see backend/app/models/models.py) which
-- create this same schema automatically. This file is provided for reference and
-- for teams who want to provision the schema directly in Postgres/Supabase.

CREATE TABLE staff (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    shift TEXT DEFAULT 'morning',
    phone TEXT DEFAULT ''
);

CREATE TABLE guests (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    tier TEXT DEFAULT 'standard'
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('manager','staff','guest')),
    staff_id INTEGER REFERENCES staff(id),
    guest_id INTEGER REFERENCES guests(id),
    name TEXT NOT NULL
);

CREATE TABLE guest_preferences (
    id SERIAL PRIMARY KEY,
    guest_id INTEGER REFERENCES guests(id),
    category TEXT,
    weight FLOAT DEFAULT 1.0
);

CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    number TEXT UNIQUE,
    type TEXT,
    block TEXT,
    price FLOAT
);

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES rooms(id),
    guest_id INTEGER REFERENCES guests(id),
    check_in TIMESTAMP,
    check_out TIMESTAMP,
    status TEXT DEFAULT 'confirmed'
);

CREATE TABLE occupancy_records (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    occupancy_pct FLOAT,
    revenue FLOAT
);

CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    name TEXT,
    type TEXT,
    location TEXT,
    install_date TIMESTAMP
);

CREATE TABLE equipment_readings (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER REFERENCES equipment(id),
    ts TIMESTAMP DEFAULT now(),
    temperature FLOAT,
    energy FLOAT,
    vibration FLOAT,
    runtime_hours FLOAT,
    days_since_maintenance INTEGER
);

CREATE TABLE maintenance_records (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER REFERENCES equipment(id),
    date TIMESTAMP DEFAULT now(),
    type TEXT,
    notes TEXT DEFAULT ''
);

CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    name TEXT,
    unit TEXT,
    current_stock FLOAT,
    avg_daily_usage FLOAT
);

CREATE TABLE inventory_transactions (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES inventory_items(id),
    ts TIMESTAMP DEFAULT now(),
    delta FLOAT,
    reason TEXT
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    guest_id INTEGER REFERENCES guests(id),
    text TEXT,
    sentiment_score FLOAT,
    sentiment_label TEXT,
    topics TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE ai_predictions (
    id SERIAL PRIMARY KEY,
    module TEXT,
    subject_type TEXT,
    subject_id INTEGER,
    subject_label TEXT,
    risk_score FLOAT,
    confidence FLOAT,
    features_json TEXT,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE ai_recommendations (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES ai_predictions(id),
    title TEXT,
    description TEXT,
    severity TEXT CHECK (severity IN ('critical','high','medium','low')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
    expected_impact TEXT,
    created_at TIMESTAMP DEFAULT now(),
    decided_at TIMESTAMP,
    decided_by TEXT
);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    recommendation_id INTEGER REFERENCES ai_recommendations(id),
    title TEXT,
    description TEXT,
    category TEXT,
    priority TEXT DEFAULT 'normal',
    assigned_staff_id INTEGER REFERENCES staff(id),
    location TEXT DEFAULT '',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','assigned','in_progress','completed','cancelled')),
    created_at TIMESTAMP DEFAULT now(),
    due_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT DEFAULT '',
    ai_source TEXT DEFAULT '',
    expected_impact TEXT DEFAULT ''
);

CREATE TABLE task_outcomes (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id),
    before_metric FLOAT,
    after_metric FLOAT,
    note TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE guest_requests (
    id SERIAL PRIMARY KEY,
    guest_id INTEGER REFERENCES guests(id),
    text TEXT,
    category TEXT DEFAULT 'general',
    status TEXT DEFAULT 'pending',
    task_id INTEGER REFERENCES tasks(id),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    severity TEXT,
    message TEXT,
    source_module TEXT,
    created_at TIMESTAMP DEFAULT now(),
    is_read BOOLEAN DEFAULT false
);

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    actor TEXT,
    action TEXT,
    detail TEXT DEFAULT '',
    ts TIMESTAMP DEFAULT now()
);

-- Example Row Level Security (Supabase). Adapt policies to your auth model.
-- ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "staff_see_own_tasks" ON tasks FOR SELECT
--   USING (assigned_staff_id = (SELECT staff_id FROM users WHERE id = auth.uid()));
