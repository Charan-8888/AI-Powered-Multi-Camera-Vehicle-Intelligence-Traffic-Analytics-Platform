# ANPR Vehicle Intelligence MVP

Django REST API for cameras, vehicles, number-plate detections, and reconstructed trajectories.

## Local setup

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `DB_PASSWORD` in `backend/.env` to the local PostgreSQL password, then create the database and run migrations:

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\createdb.exe' -h localhost -p 5432 -U postgres anpr_mvp
python manage.py migrate
python manage.py runserver
```

## API

| Endpoint | Purpose |
| --- | --- |
| `GET, POST /api/cameras/` | Camera registry |
| `GET, POST /api/vehicles/` | Normalized Indian vehicle registrations |
| `GET, POST /api/detections/` | Timestamped camera detections |
| `GET, POST /api/trajectories/` | Vehicle paths across cameras |
| `GET /api/dashboard/stats/` | MVP dashboard totals |

## Verification

```powershell
cd backend
python manage.py check
python manage.py test --settings=config.settings_test
```

The test settings deliberately use an in-memory SQLite database so tests do not require a PostgreSQL password. The application configuration remains PostgreSQL-first through `backend/.env`.

## Deployment

The repository includes `render.yaml`, which provisions the Django API and a managed PostgreSQL database on Render. It supplies a generated production `SECRET_KEY`, a private database URL, migrations, and a health check. The React app is a static Vite build; set `VITE_API_BASE_URL` to the deployed API URL followed by `/api` when deploying it to Vercel or Render Static Sites.

Do not commit `backend/.env`, local database files, Python virtual environments, runtime model caches, datasets, or downloaded test video. The production plate and vehicle checkpoints are intentionally versioned so the scan API can run after deployment.
