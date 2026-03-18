import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from googleapiclient.errors import HttpError

load_dotenv()

from app.database import init_db
from app.routes import auth, playlists, sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="YT List Manager", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(playlists.router)
app.include_router(sync.router)


@app.exception_handler(HttpError)
async def youtube_http_error_handler(request: Request, exc: HttpError):
    details = exc.error_details if isinstance(exc.error_details, list) else []
    reason = details[0].get("reason", "") if details else ""
    if int(exc.status_code) == 403 and reason == "quotaExceeded":
        return JSONResponse(
            status_code=429,
            content={"detail": "YouTube API quota exceeded. Resets daily at midnight Pacific Time."},
        )
    return JSONResponse(
        status_code=int(exc.status_code),
        content={"detail": exc._get_reason() or str(exc)},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}
