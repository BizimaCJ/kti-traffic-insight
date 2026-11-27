# Kigali Traffic Insight

Traffic information and incident alerts for Nyabugogo, Kigali (simulated data prototype). The prototype covers Nyabugogo Terminal and two nearby intersections: **Nyabugogo-Kinamba** and **Nyabugogo-Muhima**.

- **Back end:** Django + Django REST Framework + PostgreSQL (`backend/`)
- **Front end:** React + Vite, blue-themed, responsive (`frontend/`; a ready-built copy is in `frontend/dist`)

It implements every requirement in the SRS (v1.1): FR 1-21 and the measurable NFRs.

## Set up and run (every step)

**You need:** Git and Python 3.10 or newer. Node.js is **not** needed to run the app, because the built front end is already in `frontend/dist`. (PostgreSQL is optional: the quick start below uses SQLite.)

### 1. Get the code

```bash
git clone https://github.com/<your-username>/kti-traffic-insight.git
cd kti-traffic-insight/backend
```

### 2. Create a virtual environment and install the dependencies

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Choose the database

Quick start (SQLite, nothing to install). Create the file `backend/.env` containing exactly this one line:

```
KTI_DATABASE_URL=sqlite:///db.sqlite3
```

macOS / Linux: `echo "KTI_DATABASE_URL=sqlite:///db.sqlite3" > .env`
Windows (PowerShell): `"KTI_DATABASE_URL=sqlite:///db.sqlite3" | Out-File -Encoding ascii .env`

*Or use PostgreSQL:* create a database and user, then `cp .env.example .env` and set the port, user and password in `KTI_DATABASE_URL` to match.

```bash
sudo -u postgres psql -c "CREATE USER kti WITH PASSWORD 'kti_dev_password' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE kti OWNER kti;"
```

### 4. Create the tables and load the data

Run these from the `backend` folder with the virtual environment active:

```bash
python manage.py migrate                                              # create the tables
python manage.py seed                                                 # Nyabugogo Terminal, Nyabugogo-Kinamba, Nyabugogo-Muhima and their roads
python manage.py create_admin --username admin --name "Admin One"     # asks you for a password (at least 10 characters)
python manage.py backfill --days 7                                    # a week of simulated history
python manage.py simulate --scenario peak_hour                        # one round of live simulated data
```

### 5. Start the app

```bash
python manage.py runserver
```

Open http://localhost:8000. The administrator login is at http://localhost:8000/admin/login (use the username and password from step 4).

Keep the data changing while you demo, in a **second terminal** (activate the virtual environment again first):

```bash
python manage.py simulate --scenario auto --loop --interval 30
```

Scenarios: `normal`, `peak_hour`, `incident`, `flooding`, `auto` (by Kigali time of day, with a small chance of an incident or flooding).

There is no public registration for administrators.

## Changing the front end

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, forwards /api to Django on :8000
npm run build      # writes frontend/dist, which Django serves
```

## Tests

```bash
cd backend && source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
KTI_DATABASE_URL=sqlite:///:memory: python manage.py test tests    # 85 tests, no setup (macOS / Linux)
# Windows PowerShell: $env:KTI_DATABASE_URL="sqlite:///:memory:"; python manage.py test tests
# On PostgreSQL the database user needs CREATEDB: sudo -u postgres psql -c "ALTER USER kti CREATEDB;"
```

## How it is organised

```
backend/apps/
  network/     roads and intersections, seed data, /api/network
  traffic/     traffic levels (SRS 4.3.2), readings, history
  incidents/   anonymous reports, status rules (SRS 4.3.1), admin review workflow
  alerts/      alert rules (SRS 4.3.3), publish and withdraw
  audit/       audit log of every administrator action
  accounts/    administrator login, logout, 15-minute session
  routing/     journey planner: delay and alternative routes
  simulation/  simulated data generator, `simulate` and `backfill` commands
  overview/    one request for the overview page
  core/        permissions, throttling, error format
frontend/src/  pages, components, context, lib (api client, formatting)
```
In each app: `models.py` (data), `services.py` (business rules), `views.py` (HTTP only), `serializers.py`.

  - The map is a schematic drawn from each intersection's `map_x`/`map_y` (no map provider is named in the SRS).
- The two nearby intersections are **Nyabugogo-Kinamba** and **Nyabugogo-Muhima**. Coordinates can be added at `/django-admin/` (create a superuser with `python manage.py createsuperuser`).
- Thresholds and limits are in `.env` (see `.env.example`).
