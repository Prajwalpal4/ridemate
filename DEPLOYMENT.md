# RideMate - Deployment Guide (100% free)

**Stack:** Flask app on **Render** (free) + PostgreSQL database on **Supabase** (free).
Your data is stored in Supabase, so it is NOT lost when the website restarts or you refresh the browser.

---

## Step 1 - Create the database (Supabase)

1. Go to supabase.com -> sign up -> **New project**. Save the database password you choose.
2. Wait until the project is ready.
3. Click the **Connect** button at the top -> choose **Session pooler**.
4. Copy the connection string. It looks like:

   `postgresql://postgres.<project-ref>:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres`

5. Replace `[YOUR-PASSWORD]` with your real password.
   - If your password has special characters (`@ # / : ?`), write them in URL form
     (for example `@` becomes `%40`). The easiest fix is to choose a password with only letters and numbers.

> **Why the "pooler" string?** The default "direct" string works only over IPv6 and may fail from Render.
> The pooler string works everywhere. If you see "Network is unreachable" in the Render logs, this is the cause.

You do **not** need to run any SQL by hand: the app creates all tables, indexes and stored
procedures by itself the first time it starts.

## Step 2 - Put the code on GitHub

1. Create a new GitHub repository (private or public).
2. Upload the whole `Ridemate` folder contents (the file `app.py` must be at the top level of the repo).
3. `.gitignore` already keeps your local database file and secrets out of GitHub.

## Step 3 - Deploy on Render

1. render.com -> **New -> Web Service** -> connect your GitHub repo.
   (Or use **New -> Blueprint**; it reads `render.yaml` and fills everything for you.)
2. Settings:
   - Runtime: **Python**
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --workers 1 --threads 4 --timeout 60`
   - Plan: **Free**
   - Health check path: `/health`
3. Environment variables:
   - `DATABASE_URL` = the Supabase pooler string from Step 1
   - `SECRET_KEY` = any long random text (30+ characters). The app refuses to start on Render without it.
   - `PYTHON_VERSION` = `3.12.8`
4. Click **Deploy**. When it says "Live", open your `https://<name>.onrender.com` link.

## Step 4 - Add demo data (recommended before your presentation)

The database starts empty. To load 4 demo accounts and 4 upcoming rides, run **once** on your own computer:

```
pip install -r requirements.txt
set DATABASE_URL=<your Supabase pooler string>        (Windows CMD)
$env:DATABASE_URL="<your Supabase pooler string>"      (Windows PowerShell)
python seed_demo.py
```

Demo logins (password `demo123`):
`driver1@demo.com`, `driver2@demo.com`, `passenger1@demo.com`, `passenger2@demo.com`

(`database/migration_seed.sql` holds your old local test data. Those rides are from the past, so they will
not show in "Find Rides". You normally do not need it. If you want it, paste it in Supabase -> SQL Editor.)

## Step 5 - Keep it awake (important for viva / demo day)

Free plans go to sleep:
- **Render free** sleeps after about 15 minutes with no visits. The next visit takes ~30-60 seconds to wake up.
- **Supabase free** pauses a project after 1 week with no activity, and you must restore it by hand.

Fix for both: create a free monitor at **uptimerobot.com** that opens
`https://<name>.onrender.com/health` every 5-10 minutes. That page runs a tiny database query,
so both Render and Supabase stay awake.
**Also open the site yourself 10 minutes before your presentation** to be safe.

## Run on your own computer (no setup needed)

```
pip install -r requirements.txt
python seed_demo.py     (optional demo data)
python app.py           -> http://localhost:10000
```
With no `DATABASE_URL` set, the app uses the local SQLite file `database/ridemate.db`.

## Good to know
- Free Supabase database size limit: 500 MB (more than enough for this project).
- Render's free disk is temporary, so this project does not save uploaded files. Everything lives in the database.
- Database design: 4 tables (`users`, `rides`, `bookings`, `notifications`), foreign keys, a UNIQUE index that stops
  double bookings, and PostgreSQL stored routines in `database/procedures.sql`.
