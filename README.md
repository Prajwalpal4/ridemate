# RideMate

RideMate is a college carpool/ride-sharing web application built with Flask and PostgreSQL.

## Features

- Student registration and login
- Driver and Passenger roles
- Driver dashboard
- Offer a ride
- Find available rides
- Book rides
- Driver booking accept/reject
- Booking status
- Notifications
- User profile
- CSRF protection
- Password hashing
- PostgreSQL production database
- SQLite local-development fallback
- `/health` production health endpoint
- Gunicorn production server
- Render deployment configuration

## Technology

- Python
- Flask
- PostgreSQL / Supabase
- SQLite for local development
- Gunicorn
- HTML/CSS/JavaScript

## Project structure

```text
app.py
database.py
helpers.py
requirements.txt
render.yaml
seed_demo.py
database/
routes/
templates/
static/
uploads/
```

## Run locally

Create and activate a virtual environment, then:

```bash
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:10000
```

Without `DATABASE_URL`, the application uses local SQLite.

## Production deployment

Recommended free architecture:

```text
GitHub -> Render Free Web Service -> Supabase PostgreSQL
```

Set these Render environment variables:

```text
DATABASE_URL=<Supabase PostgreSQL pooler connection string>
SECRET_KEY=<long random secret>
PYTHON_VERSION=3.12.8
```

Render commands:

```text
Build: pip install -r requirements.txt
Start: gunicorn app:app --workers 1 --threads 4 --timeout 60
Health check: /health
```

See `DEPLOYMENT.md` for the complete deployment procedure.

## Demo data

Optional:

```bash
python seed_demo.py
```

The demo accounts use password `demo123`. Do not use these credentials for a real production service.

## Security

- Production requires `SECRET_KEY`.
- `.env` and local database files are ignored by Git.
- Passwords are hashed.
- POST requests require a CSRF token.
- Production sessions use secure HTTP-only cookies.
- Production data should be stored in PostgreSQL, not the Render local filesystem.

## Important free-hosting note

Render's free filesystem is ephemeral, so application data must not depend on local SQLite in production. RideMate uses PostgreSQL through `DATABASE_URL` when deployed.
