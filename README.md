# Aaron studio — Night Blue visual refresh (v0.3)

**Start with [`COLOUR_AND_COPY_UPDATE.md`](COLOUR_AND_COPY_UPDATE.md)** for exact instructions to install this version over the earlier BarberOS project.

# BarberOS — Aaron Binions Pilot (v0.2)

A **local development pilot**, not a live booking service. Separate, reusable `aaron-binions` shop seeded into the existing BarberOS multi-tenant FastAPI database. Includes a purpose-designed responsive AB Studio storefront, a working booking flow, and a single-barber admin dashboard.

## How to run

Requirements: Python 3.11+ recommended, Node.js 20+, npm.

**Backend (terminal 1)**

```bash
cd backend
python3 -m venv .venv              # only for a fresh clone
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Frontend (terminal 2)**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Use the top local-only bar to switch between **Customer Website** and **Admin Dashboard**.

The backend creates a new `aaron-binions` shop once at startup, preserving the original `northside` shop and its bookings if you already have a local SQLite DB. Do not delete `backend/barberos.db` if you want to keep its appointments. The sample services and hours are seeded only once; after that, edits in the dashboard persist.

Optional config: copy `frontend/.env.example` to `frontend/.env` and `backend/.env.example` to `backend/.env`. IMPORTANT: Python does not automatically load `.env`; export variables in your shell or use an explicit dotenv runner if you need to change backend config.

## What's implemented

- Mobile-first AB concept storefront: editorial typography, Instagram profile portrait, service list, about section, screenshot-derived review quotes, Instagram link, Monasterevin area only.
- Booking: server-authoritative time slots, single barber, date selection, customer details, persisted SQLite appointment, duplicate slot rejected, confirmation **in the browser only**.
- Dashboard: today's bookings, date navigation, cancel a booking (no outbound message), weekly opening days/times, one-off closures or special hours, list/remove exceptions, update services and prices, toggle service visibility, add service.
- Multi-tenant schema: shops, staff, services, weekly hours, exceptions, appointments; API namespaced by `shops/{slug}`.
- Basic local demo token guards for admin endpoints. **Not production authentication**.

## What is not implemented

- Real logins, tenant membership/role-based access, secret management, CSRF/session controls, rate limiting, spam/bot protection, GDPR policies, audit logs or consent workflows.
- Deposits/payments, booking reminder emails or SMS, reschedule workflows, barber work breaks, notification of cancellations, automatic conflict resolution after a schedule change.
- Public deployment, domains, real verified prices/services/opening hours, approved logo or approved review reuse.
- Proper migrations (currently `Base.metadata.create_all`).

**Do not connect real customers until these are addressed.** The screenshot-derived materials and testimonials must be approved by Aaron, including reviews originating at other shops. The logo `AB.` is a temporary concept, **not Aaron's official brand**. Sample services/prices/hours are fictional until verified.

## What changed from original v0.1

```text
backend/app/seed.py              NEW: tenant-isolated Aaron seed (preserves existing DB)
backend/app/main.py              EDIT: seed wiring, service editor endpoints,
                                 cancel booking, list/delete exceptions
frontend/src/api.js              EDIT: reusable slug/API adapter + admin endpoints
frontend/src/main.jsx            REPLACE: local-only preview switch
frontend/src/config/studio.js    NEW: public marketing content and review excerpts
frontend/src/components/BookingFlow.jsx NEW: reusable 3-step booking panel
frontend/src/pages/Storefront.jsx NEW: styled AB landing page
frontend/src/pages/Dashboard.jsx  NEW: one-person business dashboard
frontend/src/utils.js            NEW: shared date/price utilities
frontend/src/style.css           REPLACE: modern, responsive site + dashboard styles
frontend/public/media/           NEW: provided profile / review screenshot crops
frontend/index.html              EDIT: page metadata and fonts
frontend/.env.example            NEW: per-shop frontend config
backend/.env.example             NEW: local backend defaults
.gitignore                       NEW: no secrets, databases, environments, build output
```

## Important architecture details

- The source of truth for availability is `backend/app/scheduling.py`; frontend only displays returned slots.
- A barber's ID, tenant ID, and chosen service are validated together in API endpoints.
- The local DB defaults to `sqlite:///./barberos.db` relative to the backend working directory. PostgreSQL supported by `DATABASE_URL`, but no production migration/infrastructure is included.
- Default weekly demo hours are Mon–Sat 10:00–18:00, Sunday off. Edit in the dashboard.
- The demo token (`local-demo-only`) is intentionally simple for local development. Never put a production secret in a `VITE_` environment variable (Vite embeds these in the client bundle).
- Only the location **area** is public: Monasterevin, Co. Kildare. Do not expose the home address without explicit permission.
- Increasing deployment scale requires Postgres, migrations, secure auth and tenant permissions, transactions, observability, and test coverage.

## API

Backend: http://127.0.0.1:8000/docs

Public:
- `GET /api/shops/aaron-binions`
- `GET /api/shops/aaron-binions/availability?day=YYYY-MM-DD&service_id=1&barber_id=1`
- `POST /api/shops/aaron-binions/appointments`

Demo-admin (requires `X-Admin-Token` header):
- `GET /api/shops/aaron-binions/appointments?day=YYYY-MM-DD`
- `PUT /api/shops/aaron-binions/appointments/{id}/cancel`
- `PUT /api/shops/aaron-binions/hours`
- `GET|PUT /api/shops/aaron-binions/exceptions`
- `DELETE /api/shops/aaron-binions/exceptions/{day}`
- `GET /api/shops/aaron-binions/admin/services`
- `POST /api/shops/aaron-binions/services`
- `PUT /api/shops/aaron-binions/services/{id}`

## Moving to a new barber

Keep the API and components. Create the next shop through a new seed/onboarding route with a unique slug; add brand content under `frontend/src/config`, and configure `VITE_SHOP_SLUG`. A production SaaS should serve brand configuration from the backend rather than rely on a build-time marketing file. **Do not clone the application separately for every barber**; this demo is an intermediate step toward a dynamic multi-tenant frontend.
