# YouTube Playlist Manager

## Dev Setup

### Backend
```bash
cd backend && uv run uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend && npm run dev
```

## Tech Stack
- Backend: Python 3.12+ / FastAPI / SQLite (aiosqlite) / google-api-python-client
- Frontend: Svelte 5 / Vite / Tailwind CSS 4 / TypeScript
- Package management: uv (backend), npm (frontend)

## Architecture
- Backend serves API at http://localhost:8000
- Frontend dev server at http://localhost:5173, proxied to backend
- Google OAuth uses http://localhost:8000/api/auth/callback as redirect URI
- All YouTube data cached in SQLite; only re-fetched on explicit sync
- YouTube API quota: 10,000 units/day; reads=1 unit, writes=50 units

## Conventions
- Backend routes in `backend/app/routes/`
- Pydantic models in `backend/app/models.py`
- Frontend API calls through `frontend/src/lib/api.ts`
- Svelte stores using runes in `frontend/src/lib/stores.ts`
