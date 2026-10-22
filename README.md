# BarberOS — Runnable barber booking MVP

A polished customer-facing barbershop site + shop dashboard + working FastAPI scheduling and booking backend.

## What actually works

- Shared shop data (services, barbers, weekly hours) served by the API
- Service → barber → day/time → customer details → saved appointment
- Server-authoritative slots (15-minute start intervals), duration-aware, timezone-aware
- Dashboard daily appointments, editable seven-day opening hours, one-off closures/extra openings
- Availability recalculated from the database after scheduling changes
- PostgreSQL row-level serialization per barber to prevent concurrent overlapping bookings
- SQLite default for low-friction local demos, optional PostgreSQL via Docker
- Mobile-friendly customer site and shop dashboard

## Run locally on your Mac

**Terminal 1 — Backend (Python 3.11+)**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend (Node 20+)**

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Switch between **Customer website** and **Shop dashboard** using the top navigation. The first API startup automatically seeds a fictional demo shop called Northside.

A demo-only admin header uses `local-demo-only` by default. Never deploy this mechanism to production.

## Optional: start with PostgreSQL

```bash
docker compose up -d
cd backend
DATABASE_URL='postgresql+psycopg://barberos:barberos@localhost:5432/barberos' uvicorn app.main:app --reload --port 8000
```

Ensure the backend and database URLs use the same environment every time. SQLite creates `backend/barberos.db` when the API starts.

## Modular structure

```
frontend/
  src/api.js        # Centralised API adapter
  src/main.jsx      # Storefront, booking flow and barber dashboard (split into features next)
  src/style.css     # Design system and responsive UI
backend/
  app/database.py   # Configurable database + session
  app/models.py     # Tenant-aware data model
  app/scheduling.py # Pure scheduling policy functions
  app/main.py       # HTTP endpoints, request validation, demo seed
compose.yaml        # Optional PostgreSQL
```

## Critical before taking real customer bookings

This is **an MVP development demo, not production SaaS**. There is no real login, staff working-hour constraints, breaks, customer email delivery, SMS, cancellation management, payment integration, tenant membership authorization, booking-rate limits, privacy controls, auditing, database migrations, or GDPR compliance package. Public APIs are intentionally unauthenticated for demonstration. The admin token lives in the frontend bundle and is not secure.

1. Replace demo admin token with managed authentication, RBAC and tenant-bound server sessions. Restrict shop provisioning and protect personal data.
2. Switch to PostgreSQL with Alembic migration management. Add database conflict/exclusion constraints where appropriate.
3. Add barber-specific schedules, breaks, leave, buffer times, blackout overrides and visible appointment conflict warnings when hours are reduced.
4. Add confirmation email via a queued worker, retries, audit events, no-show and cancellation policies, secure contact verification and data retention.
5. Add Stripe Connect and subscription billing, rate limits, abuse checks, privacy notice, GDPR processor agreements, monitoring and backups.
6. Replace external demo photography and fictional addresses with licensed client assets and verified details.
7. Split `main.jsx` into `features/storefront`, `features/booking`, `features/dashboard`, and `shared/ui` as the codebase grows. Keep API rules authoritative.

### Known pilot limitations
- Schedule changes **do not cancel existing appointments**: manual review is necessary.
- DST fall-back repeated hours are not individually offered; more advanced timezone handling is required for late-night operations.
- SQLite has no PostgreSQL-style row locking; multi-user booking concurrency must be tested on PostgreSQL before real operation.
- Sample staff are assumed available during all shop opening hours.
- No live email is sent despite booking confirmation on screen.
