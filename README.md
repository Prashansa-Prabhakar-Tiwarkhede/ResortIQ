
# ResortIQ

### AI-Powered Resort Operations, Guest Experience & Revenue Intelligence
**Demo property: Azure Valley Resort**

> ResortIQ predicts problems before they happen and turns AI recommendations into real operational actions.

---

## The problem

Resort data is fragmented across occupancy, staffing, maintenance, inventory, and guest
feedback systems. Managers end up reactive instead of predictive.

ResortIQ unifies these into one closed loop:

```
DATA → AI PREDICTION → EXPLANATION → RECOMMENDATION → MANAGER APPROVAL → STAFF TASK → OUTCOME → FEEDBACK
```

This is not another dashboard. It's a decision-and-action layer: every prediction comes
with a plain-English explanation and a recommended action, and approving that action
automatically creates and assigns a real task, whose completion feeds back into the
prediction (see the flagship maintenance demo below).

## Status of this build

This repository implements **Phase 1 and Phase 2**, end-to-end and verified working:

**Phase 1:**
- Authentication + role-based access (manager / staff / guest)
- Full database schema and realistic seed data for Azure Valley Resort
- **Predictive maintenance module** — a trained `RandomForestClassifier`, not a
  hard-coded number — with feature-importance-based explanations
- Manager Dashboard: KPIs, Resort Intelligence Score, "What Needs My Attention",
  7-day occupancy forecast chart, session impact metrics
- AI Command Center: every recommendation with prediction, explanation, expected
  impact, and Approve/Reject
- Staff Dashboard: assigned tasks, Start/Complete with notes
- Guest portal: services, personalized recommendations, request submission
  (auto-creates a staff task), feedback with lightweight sentiment scoring
- Full audit trail and alerts
- **The closed-loop maintenance demo works end-to-end**: AI flags a unit at ~90%+
  failure risk → manager approves → task auto-assigned to a maintenance staff member
  → staff starts and completes it → risk recalculates down to single digits → impact
  dashboard updates.

**Phase 2 (this update):**
- **Inventory Intelligence** (`/manager/inventory`): predicted daily usage scaled to
  current occupancy, days-of-stock-remaining, and reorder recommendations. Approving
  a reorder actually increases the item's stock in the database (logged as an
  `inventory_transactions` row) — not just a status flip.
- **Staff Optimization** (`/manager/staff`): required headcount per department derived
  from occupied rooms ÷ a department-specific service ratio, flagged against the
  current roster, with a plain-English turnover explanation.
- **Revenue Intelligence** (`/manager/revenue`): per-room-type pricing recommendations
  from recent booking momentum vs. a baseline and forecast weekend occupancy.
  Approving actually updates the `rooms` table prices.
- **Dedicated Maintenance page** (`/manager/maintenance`): the full ranked risk list
  with expandable explanations.
- All three new modules feed the same `ai_predictions` → `ai_recommendations` →
  approve/reject pipeline as maintenance, and their recommendations appear
  automatically in the AI Command Center alongside maintenance ones.
- Idempotent recommendation generation: revisiting a page recomputes the latest
  prediction but won't spam duplicate recommendations while one is already
  pending or approved for the same subject.

**Phase 3 (this update):**
- **Guest Sentiment Analytics** (`/manager/guests`): aggregate positive/neutral/negative
  breakdown, top recurring guest issues ranked by topic, and recent reviews — all
  computed live from the `reviews` table.
- Topic extraction: guest-submitted reviews are auto-tagged with topics
  (Housekeeping, Wi-Fi, Restaurant, Staff, Response Time, etc.) via keyword
  matching, so new feedback flows straight into the analytics without manual
  labeling.
- A negative review now raises an alert automatically, same as any other
  AI-detected issue.
- **Realtime updates via WebSockets**: a `/ws` endpoint broadcasts task updates,
  recommendation approvals/rejections, and new alerts to every connected client.
  The Manager Dashboard, AI Command Center, and Staff Dashboard all subscribe and
  refresh live — e.g. a staff member completing a task updates the manager's risk
  score without a page reload. Tested with a live WebSocket client that received
  the broadcast within the same request/response cycle as the triggering action.

Not yet built (straightforward extensions of the same architecture — see
**Roadmap** below): swapping the lexicon sentiment scorer for a hosted NLP/LLM
call, and `/manager/guests` / `/manager/tasks` / `/manager/analytics` as fully
distinct routes beyond the sentiment page already added (their underlying data
is already served by existing endpoints).

## Architecture

```
resortiq/
├── frontend/            React + Vite + TypeScript + Tailwind + Recharts
│   └── src/{components,pages,layouts,hooks,services,types}
├── backend/              FastAPI + SQLAlchemy
│   ├── app/{api,models,services,ml,schemas}
│   └── seed.py
├── database/
│   └── schema.sql        Reference Postgres/Supabase schema
├── .env.example
├── docker-compose.yml
└── README.md
```

**Stack:** FastAPI + SQLAlchemy (SQLite in demo mode, Postgres/Supabase via
`DATABASE_URL`), JWT auth, scikit-learn for maintenance risk, React + Vite +
TypeScript + Tailwind + Recharts for the frontend.

**AI approach:** hybrid — a real trained model for maintenance risk (with
explanations derived from the model's feature importances), statistical/rule-based
logic for demand forecasting and sentiment, and a clean separation everywhere
between **prediction** (stored in `ai_predictions`) and **recommendation** (stored
in `ai_recommendations`, actioned into `tasks`).

## Database schema

See [`database/schema.sql`](database/schema.sql) for the full reference schema
(Postgres/Supabase dialect). The running app creates the same schema automatically
via SQLAlchemy models in `backend/app/models/models.py` — no manual migration
needed in demo mode.

Core tables: `users`, `staff`, `guests`, `guest_preferences`, `rooms`, `bookings`,
`occupancy_records`, `equipment`, `equipment_readings`, `maintenance_records`,
`inventory_items`, `inventory_transactions`, `reviews`, `guest_requests`,
`ai_predictions`, `ai_recommendations`, `tasks`, `task_outcomes`, `alerts`,
`audit_log`.

## API endpoints (implemented)

```
POST  /auth/login

GET   /dashboard/summary              KPIs + Resort Intelligence Score
GET   /dashboard/attention             "What needs my attention" feed
GET   /dashboard/occupancy/forecast    7-day forecast + history
GET   /dashboard/impact                Session impact metrics

GET   /maintenance/risks
GET   /maintenance/risks/{id}/explanation

GET   /inventory/forecast              → usage forecast + reorder recommendations
GET   /staff/recommendations           → per-department staffing gaps
GET   /revenue/recommendations         → per-room-type pricing recommendations

GET   /recommendations
POST  /recommendations/{id}/approve    → module-specific: creates a task (maintenance/staffing),
                                          restocks inventory, or applies a price change (revenue)
POST  /recommendations/{id}/reject

GET   /tasks
PATCH /tasks/{id}                      start / complete / notes

GET   /alerts
POST  /alerts/{id}/read

GET   /guest/services
GET   /guest/recommendations
POST  /guest/requests                  → auto-creates a housekeeping task
GET   /guest/requests
POST  /guest/reviews                   → sentiment scored + topic-tagged inline
GET   /guest/sentiment                 → aggregate sentiment analytics (manager)

WS    /ws                              realtime broadcast: task_update, recommendation_update, alert
```

Interactive API docs: `http://localhost:8000/docs` (FastAPI's built-in Swagger UI).

## AI/ML modules

| Module | Approach |
|---|---|
| Predictive maintenance | `RandomForestClassifier` trained at startup on synthetic labeled sensor data (energy, temperature, vibration, runtime, days-since-maintenance, age). Explanations are generated by ranking each feature's deviation from baseline weighted by the model's learned feature importances. |
| Demand forecasting | Weekday seasonality baseline blended with recent booking momentum computed from `occupancy_records`. |
| Inventory intelligence | Predicted daily usage scales with current occupancy relative to a 75% baseline; days-remaining and reorder quantity (sized to a ~4-day buffer) follow directly. |
| Staff optimization | Required headcount = occupied rooms ÷ a department-specific rooms-per-staff service ratio (e.g. Housekeeping 6, Front Desk 25), compared against the current roster. |
| Revenue intelligence | Price adjustment blends recent booking momentum for a room type (vs. a baseline share) with forecast weekend occupancy, bounded to a realistic ±8–15% range. |
| Guest sentiment | Lightweight lexicon-based scorer plus keyword-based topic extraction (swap in a hosted NLP/LLM API by setting `AI_API_KEY` — not required in demo mode). |

Every prediction is confidence-labeled (LOW/MEDIUM/HIGH/CRITICAL) and stored with
its explanation — nothing is shown as an unexplained number. Inventory, staffing,
and revenue recommendations share the exact same `ai_predictions` →
`ai_recommendations` → approve/reject pipeline as maintenance; only what
"approve" *does* differs per module (assign a task, restock inventory, or
reprice rooms).

Every prediction is confidence-labeled (LOW/MEDIUM/HIGH/CRITICAL) and stored with
its explanation — nothing is shown as an unexplained number.

## Setup & running locally

### Requirements
Python 3.10+, Node 18+. No external accounts or paid APIs required in demo mode.

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate    # optional but recommended
pip install -r requirements.txt
cp ../.env.example .env      # defaults already work out of the box
python seed.py                # populates resortiq.db with Azure Valley Resort demo data
uvicorn app.main:app --reload --port 8000
```

API now running at `http://localhost:8000` (docs at `/docs`).

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env          # points at http://localhost:8000 by default
npm run dev
```

App now running at `http://localhost:5173`.

### 3. Or with Docker

```bash
docker compose up --build
```

## Demo credentials

| Role | Email | Password |
|---|---|---|
| Manager | `manager@resortiq.demo` | `demo1234` |
| Staff | `staff@resortiq.demo` | `demo1234` |
| Guest | `guest@resortiq.demo` | `demo1234` |

## Hackathon demo flow (verified working)

1. Sign in as **Manager** → dashboard shows the Resort Intelligence Score and
   "What Needs My Attention", including a critical AC unit alert.
2. Open **AI Command Center** → see the equipment's failure risk (~90%+), the
   plain-English explanation (energy/temperature/vibration deviations,
   maintenance overdue), and the recommended action.
3. Click **Approve & Assign** → a task is created and automatically assigned to
   an available maintenance staff member.
4. Sign out, sign in as **Staff** → the task appears as HIGH/CRITICAL priority
   with location and reason.
5. Click **Start Task**, then **Complete Task** with notes.
6. Sign back in as **Manager** → the equipment's risk score has been
   recalculated down to single digits, and the Impact panel shows a prevented
   failure.

This is the same loop the guest portal uses for service requests: a guest
submitting "please send extra towels" auto-creates a housekeeping task the
guest can then watch move from Assigned → In Progress → Completed.

## Environment variables

See [`.env.example`](.env.example). `DEMO_MODE=true` (default) requires nothing
beyond what's listed — SQLite and the built-in ML/rule-based logic need no
external services. To point at Postgres/Supabase instead, set `DATABASE_URL`
and the `SUPABASE_*` values and set `DEMO_MODE=false`; the SQLAlchemy models are
already Postgres-compatible.

## Realtime updates

A WebSocket endpoint at `/ws` broadcasts three message types — `task_update`,
`recommendation_update`, and `alert` — to every connected client whenever a
staff member changes a task's status, a manager approves/rejects a
recommendation, or a new alert is raised (including guest requests and
negative reviews). The connection is thread-safe from FastAPI's sync request
handlers via `asyncio.run_coroutine_threadsafe`, so no request has to be made
async just to broadcast. The frontend's `useRealtime` hook auto-reconnects on
drop and the Manager Dashboard, AI Command Center, and Staff Dashboard all
subscribe to refresh their data live — no manual page reload needed to see
another role's action reflected.

## Roadmap (next phases)

- Phase 4: swap the lexicon sentiment scorer for a hosted NLP/LLM call when
  `AI_API_KEY` is set, with automatic fallback to the local scorer
- Phase 5: `/manager/tasks` and `/manager/analytics` as distinct routes with
  dedicated charts (data already served by existing endpoints)
- Phase 6: push WebSocket messages to specific staff members (task
  reassignment) rather than a single broadcast channel, and add a small
  "Live" connection indicator in the UI
