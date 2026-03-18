import aiosqlite
import os
from pathlib import Path

DB_PATH = Path(os.getenv("DATABASE_PATH", "data.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS playlists (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    thumbnail_url TEXT,
    item_count INTEGER DEFAULT 0,
    published_at TEXT,
    last_synced_at TEXT
);

CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    title TEXT,
    channel_title TEXT,
    thumbnail_url TEXT,
    duration TEXT,
    status TEXT DEFAULT 'available',
    last_checked_at TEXT
);

CREATE TABLE IF NOT EXISTS playlist_videos (
    playlist_item_id TEXT PRIMARY KEY,
    playlist_id TEXT REFERENCES playlists(id),
    video_id TEXT REFERENCES videos(id),
    position INTEGER,
    added_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_pv_playlist ON playlist_videos(playlist_id);
CREATE INDEX IF NOT EXISTS idx_pv_video ON playlist_videos(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);

CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    token_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quota (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    date TEXT NOT NULL,
    units_used INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS folder_playlists (
    folder_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
    playlist_id TEXT REFERENCES playlists(id) ON DELETE CASCADE,
    PRIMARY KEY (folder_id, playlist_id)
);
"""


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()
