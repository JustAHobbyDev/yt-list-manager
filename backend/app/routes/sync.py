import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from starlette.responses import StreamingResponse

from app.auth import RequireCreds
from app.database import get_db
from app.models import SyncProgress, QuotaInfo
from app.youtube import (
    fetch_my_playlists,
    fetch_playlist_items,
    check_video_statuses,
    get_quota,
)

router = APIRouter(tags=["sync"])

# Global sync state
_sync_progress = SyncProgress(status="idle")
_sync_lock = asyncio.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _sync_playlist(creds, playlist_id: str):
    db = await get_db()
    try:
        items = await fetch_playlist_items(creds, playlist_id)

        await db.execute(
            "DELETE FROM playlist_videos WHERE playlist_id = ?", (playlist_id,)
        )

        video_ids = []
        for item in items:
            video_ids.append(item["video_id"])
            await db.execute(
                """INSERT INTO videos (id, title, channel_title, thumbnail_url)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                     title = COALESCE(excluded.title, videos.title),
                     channel_title = COALESCE(excluded.channel_title, videos.channel_title),
                     thumbnail_url = COALESCE(excluded.thumbnail_url, videos.thumbnail_url)""",
                (item["video_id"], item["title"], item["channel_title"], item["thumbnail_url"]),
            )
            await db.execute(
                """INSERT OR REPLACE INTO playlist_videos
                   (playlist_item_id, playlist_id, video_id, position, added_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    item["playlist_item_id"],
                    playlist_id,
                    item["video_id"],
                    item["position"],
                    item["added_at"],
                ),
            )

        if video_ids:
            statuses = await check_video_statuses(creds, video_ids)
            now = _now()
            for vid, info in statuses.items():
                await db.execute(
                    """UPDATE videos SET status = ?, duration = ?, last_checked_at = ?
                       WHERE id = ?""",
                    (info["status"], info["duration"], now, vid),
                )

        await db.execute(
            "UPDATE playlists SET last_synced_at = ?, item_count = ? WHERE id = ?",
            (_now(), len(items), playlist_id),
        )
        await db.commit()
    finally:
        await db.close()


@router.post("/api/sync")
async def sync_all(creds: RequireCreds):
    global _sync_progress
    if _sync_lock.locked():
        raise HTTPException(status_code=409, detail="Sync already in progress")

    async def do_sync():
        global _sync_progress
        async with _sync_lock:
            try:
                playlists = await fetch_my_playlists(creds)
                _sync_progress = SyncProgress(
                    status="syncing",
                    playlists_total=len(playlists),
                )

                db = await get_db()
                try:
                    for pl in playlists:
                        await db.execute(
                            """INSERT INTO playlists (id, title, description, thumbnail_url, item_count, published_at)
                               VALUES (?, ?, ?, ?, ?, ?)
                               ON CONFLICT(id) DO UPDATE SET
                                 title = excluded.title,
                                 description = excluded.description,
                                 thumbnail_url = excluded.thumbnail_url,
                                 item_count = excluded.item_count,
                                 published_at = excluded.published_at""",
                            (pl["id"], pl["title"], pl["description"], pl["thumbnail_url"], pl["item_count"], pl["published_at"]),
                        )
                    await db.commit()
                finally:
                    await db.close()

                for i, pl in enumerate(playlists):
                    _sync_progress = SyncProgress(
                        status="syncing",
                        current_playlist=pl["title"],
                        playlists_done=i,
                        playlists_total=len(playlists),
                    )
                    await _sync_playlist(creds, pl["id"])

                _sync_progress = SyncProgress(
                    status="done",
                    playlists_done=len(playlists),
                    playlists_total=len(playlists),
                    message=f"Synced {len(playlists)} playlists",
                )
            except Exception as e:
                _sync_progress = SyncProgress(status="error", message=str(e))

    asyncio.create_task(do_sync())
    return {"ok": True, "message": "Sync started"}


@router.post("/api/sync/{playlist_id}")
async def sync_one(playlist_id: str, creds: RequireCreds):
    global _sync_progress
    if _sync_lock.locked():
        raise HTTPException(status_code=409, detail="Sync already in progress")

    async def do_sync():
        global _sync_progress
        async with _sync_lock:
            try:
                _sync_progress = SyncProgress(
                    status="syncing", current_playlist=playlist_id, playlists_total=1
                )
                await _sync_playlist(creds, playlist_id)
                _sync_progress = SyncProgress(
                    status="done", playlists_done=1, playlists_total=1
                )
            except Exception as e:
                _sync_progress = SyncProgress(status="error", message=str(e))

    asyncio.create_task(do_sync())
    return {"ok": True}


@router.get("/api/sync/status")
async def sync_status_sse():
    async def event_stream():
        last = None
        while True:
            data = _sync_progress.model_dump_json()
            if data != last:
                yield f"data: {data}\n\n"
                last = data
            if _sync_progress.status in ("done", "error", "idle"):
                yield f"data: {data}\n\n"
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/api/quota", response_model=QuotaInfo)
async def quota():
    return get_quota()
