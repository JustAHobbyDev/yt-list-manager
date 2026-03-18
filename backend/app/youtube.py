from datetime import datetime
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from app.models import QuotaInfo
from app.database import get_db

_PACIFIC = ZoneInfo("America/Los_Angeles")


def _pacific_today() -> str:
    return datetime.now(_PACIFIC).strftime("%Y-%m-%d")


async def _track(units: int):
    today = _pacific_today()
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO quota (id, date, units_used) VALUES (1, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 units_used = CASE WHEN date = excluded.date
                              THEN units_used + excluded.units_used
                              ELSE excluded.units_used END,
                 date = excluded.date""",
            (today, units),
        )
        await db.commit()
    finally:
        await db.close()


async def get_quota() -> QuotaInfo:
    today = _pacific_today()
    db = await get_db()
    try:
        cursor = await db.execute("SELECT date, units_used FROM quota WHERE id = 1")
        row = await cursor.fetchone()
    finally:
        await db.close()
    if row and row["date"] == today:
        return QuotaInfo(estimated_used=row["units_used"])
    return QuotaInfo(estimated_used=0)


def get_service(creds: Credentials):
    return build("youtube", "v3", credentials=creds)


async def fetch_my_playlists(creds: Credentials) -> list[dict]:
    service = get_service(creds)
    playlists = []
    request = service.playlists().list(
        part="snippet,contentDetails",
        mine=True,
        maxResults=50,
    )
    while request:
        response = request.execute()
        await _track(1)
        for item in response.get("items", []):
            playlists.append({
                "id": item["id"],
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
                "thumbnail_url": item["snippet"]["thumbnails"].get("medium", {}).get("url"),
                "item_count": item["contentDetails"]["itemCount"],
                "published_at": item["snippet"]["publishedAt"],
            })
        request = service.playlists().list_next(request, response)
    return playlists


async def fetch_playlist_items(creds: Credentials, playlist_id: str) -> list[dict]:
    service = get_service(creds)
    items = []
    request = service.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=50,
    )
    while request:
        response = request.execute()
        await _track(1)
        for item in response.get("items", []):
            video_id = item["contentDetails"]["videoId"]
            snippet = item["snippet"]
            items.append({
                "playlist_item_id": item["id"],
                "video_id": video_id,
                "title": snippet.get("title"),
                "channel_title": snippet.get("videoOwnerChannelTitle"),
                "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                "position": snippet.get("position", 0),
                "added_at": snippet.get("publishedAt"),
            })
        request = service.playlistItems().list_next(request, response)
    return items


async def check_video_statuses(creds: Credentials, video_ids: list[str]) -> dict[str, dict]:
    """Check status of videos in batches of 50. Returns {video_id: {status, duration}}."""
    service = get_service(creds)
    results = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        response = service.videos().list(
            part="status,contentDetails",
            id=",".join(batch),
        ).execute()
        await _track(1)

        found_ids = set()
        for item in response.get("items", []):
            vid = item["id"]
            found_ids.add(vid)
            upload_status = item["status"].get("uploadStatus", "")
            privacy = item["status"].get("privacyStatus", "")

            if upload_status == "rejected" or upload_status == "deleted":
                status = "deleted"
            elif privacy == "private":
                status = "private"
            else:
                status = "available"

            results[vid] = {
                "status": status,
                "duration": item["contentDetails"].get("duration"),
            }

        for vid in batch:
            if vid not in found_ids:
                results[vid] = {"status": "unavailable", "duration": None}

    return results


async def delete_playlist_item(creds: Credentials, playlist_item_id: str):
    service = get_service(creds)
    service.playlistItems().delete(id=playlist_item_id).execute()
    await _track(50)


async def insert_playlist_item(creds: Credentials, playlist_id: str, video_id: str) -> str:
    service = get_service(creds)
    response = service.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id,
                },
            }
        },
    ).execute()
    await _track(50)
    return response["id"]


async def delete_playlist(creds: Credentials, playlist_id: str):
    service = get_service(creds)
    service.playlists().delete(id=playlist_id).execute()
    await _track(50)


async def rename_playlist(creds: Credentials, playlist_id: str, new_title: str):
    service = get_service(creds)
    service.playlists().update(
        part="snippet",
        body={
            "id": playlist_id,
            "snippet": {"title": new_title},
        },
    ).execute()
    await _track(50)
