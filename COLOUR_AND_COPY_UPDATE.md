# Aaron's BarberOS — Night Blue UI refresh (v0.3)

This is a **complete replacement source folder** for the prior Aaron pilot, not a screenshot or static design. The React storefront has been redesigned around night-blue and white. Booking, schedules, services, and admin actions still use the FastAPI backend from v0.2.

## Update an existing local project

The project folder shown previously was `~/Desktop/barberos-mvp`.

1. Download `BarberOS-Aaron-Blue-v03.zip` and extract it on the Desktop. You should have `~/Desktop/BarberOS-Aaron-Blue-v03/`.
2. Stop the currently running backend and frontend with Ctrl+C.
3. From Terminal:

```bash
cd ~/Desktop/barberos-mvp
rsync -av \
  --exclude '.git/' --exclude '.venv/' --exclude 'node_modules/' \
  --exclude '*.db' --exclude '*.sqlite*' --exclude '.env' \
  ~/Desktop/BarberOS-Aaron-Blue-v03/ ./
```

4. Restart the backend:

```bash
cd ~/Desktop/barberos-mvp/backend
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

5. In a **second** terminal, run the frontend:

```bash
cd ~/Desktop/barberos-mvp/frontend
npm install
npm run dev
```

6. Open http://localhost:5173, then refresh the page (Cmd+Shift+R if the old version persists).

### Quick verification

```bash
ls frontend/src/blue-refresh.css frontend/src/pages/Storefront.jsx
rg 'Aaron Binions|Book an appointment' frontend/src/pages/Storefront.jsx
```

The page should show `Aaron Binions.` as the hero title on a navy background, a white services section, and a blue/white studio dashboard.

## What changed

- `frontend/src/pages/Storefront.jsx`: replaced the previous loud editorial marketing layout with a conventional barbershop website, readable headings and straight-ahead business copy.
- `frontend/src/blue-refresh.css`: new isolated **night blue / white** visual system, including responsive storefront styling and booking/admin colour overrides.
- `frontend/src/main.jsx`: imports the new visual layer after the existing `style.css`.
- `frontend/src/components/BookingFlow.jsx`: cleaner booking copy; clicking a particular service now opens the booking flow with **that service already selected**.
- `frontend/src/pages/Dashboard.jsx`: clearer dashboard headings and labels.
- `frontend/index.html`: updated title and browser theme colour.

No backend endpoints, schema or booking availability calculations were changed.

## Preview only

- Prices, services and business hours are placeholders pending Aaron's confirmation.
- The Instagram picture is extracted from the user-provided screenshot; a proper portrait or haircut photo would improve image quality.
- Reviews are from screenshots provided in the project. Some were originally posted for other barbershops. Permission and attribution must be checked before public launch.
- Do **not** deploy the current demo admin endpoints publicly. Authentication, privacy and confirmation messages are still needed.

## Commit the verified update

```bash
cd ~/Desktop/barberos-mvp
git status --short
git add frontend/src frontend/index.html COLOUR_AND_COPY_UPDATE.md
git commit -m "style: refresh Aaron website with night blue design and simpler copy"
git push
```
