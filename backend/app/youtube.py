from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from app.models import QuotaInfo

# In-memory quota tracker (resets on restart)
_quota_used = 0


def _track(units: int):
    global _quota_used
    _quota_used += units


def get_quota() -> QuotaInfo:
    return QuotaInfo(estimated_used=_quota_used)


def reset_quota():
    global _quota_used
    _quota_used = 0


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
        _track(1)
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
        _track(1)
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
        _track(1)

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
    _track(50)


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
    _track(50)
    return response["id"]


async def delete_playlist(creds: Credentials, playlist_id: str):
    service = get_service(creds)
    service.playlists().delete(id=playlist_id).execute()
    _track(50)


async def rename_playlist(creds: Credentials, playlist_id: str, new_title: str):
    service = get_service(creds)
    service.playlists().update(
        part="snippet",
        body={
            "id": playlist_id,
            "snippet": {"title": new_title},
        },
    ).execute()
    _track(50)
