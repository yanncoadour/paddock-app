# Paddock

Application de pronostics F1 (sans licence officielle) en Flutter + FastAPI.

## Backend (FastAPI)

### Lancer avec Docker Compose

```bash
docker compose up --build
```

Le backend est disponible sur http://localhost:8000 et expose `GET /health`.

### Lancer en local sans Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Mobile (Flutter)

```bash
cd mobile
flutter pub get
flutter run
```

## Structure

- `backend/` : API FastAPI
- `mobile/` : application Flutter
- `docs/` : documentation
