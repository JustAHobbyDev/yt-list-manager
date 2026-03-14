from fastapi import APIRouter, HTTPException

from app.auth import RequireCreds
from app.database import get_db
from app.models import (
    PlaylistSummary,
    PlaylistDetail,
    Video,
    OverlapPair,
    RemoveVideosRequest,
    MoveVideosRequest,
    MergeRequest,
    RenamePlaylistRequest,
    Folder,
    CreateFolderRequest,
    UpdateFolderRequest,
)
from app.youtube import (
    delete_playlist_item,
    insert_playlist_item,
    delete_playlist as yt_delete_playlist,
    rename_playlist as yt_rename_playlist,
)

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


@router.get("", response_model=list[PlaylistSummary])
async def list_playlists(creds: RequireCreds):
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT p.*,
                   COUNT(CASE WHEN v.status = 'available' THEN 1 END) AS available_count,
                   COUNT(CASE WHEN v.status != 'available' THEN 1 END) AS unavailable_count
            FROM playlists p
            LEFT JOIN playlist_videos pv ON pv.playlist_id = p.id
            LEFT JOIN videos v ON v.id = pv.video_id
            GROUP BY p.id
            ORDER BY p.title
        """)
        rows = await cursor.fetchall()
        return [PlaylistSummary(**dict(row)) for row in rows]
    finally:
        await db.close()


@router.get("/overlaps", response_model=list[OverlapPair])
async def overlaps(creds: RequireCreds):
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT
                pv1.playlist_id AS playlist_a_id,
                p1.title AS playlist_a_title,
                pv2.playlist_id AS playlist_b_id,
                p2.title AS playlist_b_title,
                GROUP_CONCAT(pv1.video_id) AS shared_video_ids_str,
                COUNT(*) AS count
            FROM playlist_videos pv1
            JOIN playlist_videos pv2
                ON pv1.video_id = pv2.video_id
                AND pv1.playlist_id < pv2.playlist_id
            JOIN playlists p1 ON p1.id = pv1.playlist_id
            JOIN playlists p2 ON p2.id = pv2.playlist_id
            GROUP BY pv1.playlist_id, pv2.playlist_id
            HAVING count > 0
            ORDER BY count DESC
        """)
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["shared_video_ids"] = d.pop("shared_video_ids_str", "").split(",")
            results.append(OverlapPair(**d))
        return results
    finally:
        await db.close()


@router.get("/{playlist_id}", response_model=PlaylistDetail)
async def get_playlist(playlist_id: str, creds: RequireCreds):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
        pl = await cursor.fetchone()
        if not pl:
            raise HTTPException(status_code=404, detail="Playlist not found")

        cursor = await db.execute("""
            SELECT v.*, pv.playlist_item_id, pv.position, pv.added_at
            FROM playlist_videos pv
            JOIN videos v ON v.id = pv.video_id
            WHERE pv.playlist_id = ?
            ORDER BY pv.position
        """, (playlist_id,))
        video_rows = await cursor.fetchall()
        videos = [Video(**dict(r)) for r in video_rows]

        return PlaylistDetail(**dict(pl), videos=videos)
    finally:
        await db.close()


@router.patch("/{playlist_id}")
async def rename_playlist_endpoint(playlist_id: str, body: RenamePlaylistRequest, creds: RequireCreds):
    await yt_rename_playlist(creds, playlist_id, body.title)
    db = await get_db()
    try:
        await db.execute("UPDATE playlists SET title = ? WHERE id = ?", (body.title, playlist_id))
        await db.commit()
    finally:
        await db.close()
    return {"ok": True}


@router.delete("/{playlist_id}")
async def delete_playlist_endpoint(playlist_id: str, creds: RequireCreds):
    await yt_delete_playlist(creds, playlist_id)
    db = await get_db()
    try:
        await db.execute("DELETE FROM playlist_videos WHERE playlist_id = ?", (playlist_id,))
        await db.execute("DELETE FROM folder_playlists WHERE playlist_id = ?", (playlist_id,))
        await db.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        await db.commit()
    finally:
        await db.close()
    return {"ok": True}


@router.post("/{playlist_id}/remove-videos")
async def remove_videos(playlist_id: str, body: RemoveVideosRequest, creds: RequireCreds):
    errors = []
    for item_id in body.playlist_item_ids:
        try:
            await delete_playlist_item(creds, item_id)
            db = await get_db()
            try:
                await db.execute("DELETE FROM playlist_videos WHERE playlist_item_id = ?", (item_id,))
                await db.commit()
            finally:
                await db.close()
        except Exception as e:
            errors.append({"playlist_item_id": item_id, "error": str(e)})

    return {
        "removed": len(body.playlist_item_ids) - len(errors),
        "errors": errors,
    }


@router.post("/{playlist_id}/remove-unavailable")
async def remove_unavailable(playlist_id: str, creds: RequireCreds):
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT pv.playlist_item_id
            FROM playlist_videos pv
            JOIN videos v ON v.id = pv.video_id
            WHERE pv.playlist_id = ? AND v.status != 'available'
        """, (playlist_id,))
        rows = await cursor.fetchall()
    finally:
        await db.close()

    item_ids = [row["playlist_item_id"] for row in rows]
    if not item_ids:
        return {"removed": 0, "errors": []}

    return await remove_videos(playlist_id, RemoveVideosRequest(playlist_item_ids=item_ids), creds)


@router.post("/remove-all-unavailable")
async def remove_all_unavailable(creds: RequireCreds):
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT pv.playlist_item_id, pv.playlist_id
            FROM playlist_videos pv
            JOIN videos v ON v.id = pv.video_id
            WHERE v.status != 'available'
        """)
        rows = await cursor.fetchall()
    finally:
        await db.close()

    if not rows:
        return {"removed": 0, "errors": []}

    errors = []
    for row in rows:
        try:
            await delete_playlist_item(creds, row["playlist_item_id"])
            db = await get_db()
            try:
                await db.execute("DELETE FROM playlist_videos WHERE playlist_item_id = ?", (row["playlist_item_id"],))
                await db.commit()
            finally:
                await db.close()
        except Exception as e:
            errors.append({"playlist_item_id": row["playlist_item_id"], "error": str(e)})

    return {"removed": len(rows) - len(errors), "errors": errors}


@router.post("/move-videos")
async def move_videos(body: MoveVideosRequest, creds: RequireCreds):
    db = await get_db()
    try:
        placeholders = ",".join("?" for _ in body.playlist_item_ids)
        cursor = await db.execute(
            f"SELECT playlist_item_id, video_id FROM playlist_videos WHERE playlist_item_id IN ({placeholders})",
            body.playlist_item_ids,
        )
        rows = await cursor.fetchall()
        item_to_video = {r["playlist_item_id"]: r["video_id"] for r in rows}
    finally:
        await db.close()

    errors = []
    for item_id in body.playlist_item_ids:
        video_id = item_to_video.get(item_id)
        if not video_id:
            errors.append({"playlist_item_id": item_id, "error": "Not found in DB"})
            continue
        try:
            await insert_playlist_item(creds, body.target_playlist_id, video_id)
            if body.delete_from_source:
                await delete_playlist_item(creds, item_id)
                db = await get_db()
                try:
                    await db.execute("DELETE FROM playlist_videos WHERE playlist_item_id = ?", (item_id,))
                    await db.commit()
                finally:
                    await db.close()
        except Exception as e:
            errors.append({"playlist_item_id": item_id, "error": str(e)})

    return {"moved": len(body.playlist_item_ids) - len(errors), "errors": errors}


@router.post("/merge")
async def merge_playlists(body: MergeRequest, creds: RequireCreds):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT video_id FROM playlist_videos WHERE playlist_id = ?",
            (body.target_playlist_id,),
        )
        existing = {row["video_id"] for row in await cursor.fetchall()}

        to_add: list[str] = []
        seen = set(existing)
        for src_id in body.source_playlist_ids:
            cursor = await db.execute(
                "SELECT video_id FROM playlist_videos WHERE playlist_id = ? ORDER BY position",
                (src_id,),
            )
            for row in await cursor.fetchall():
                vid = row["video_id"]
                if vid not in seen:
                    seen.add(vid)
                    to_add.append(vid)
    finally:
        await db.close()

    errors = []
    for vid in to_add:
        try:
            await insert_playlist_item(creds, body.target_playlist_id, vid)
        except Exception as e:
            errors.append({"video_id": vid, "error": str(e)})

    return {
        "added": len(to_add) - len(errors),
        "skipped_duplicates": len(existing),
        "errors": errors,
    }


# ── Folders ──────────────────────────────────────────────────────

@router.get("/folders/list", response_model=list[Folder])
async def list_folders(creds: RequireCreds):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM folders ORDER BY name")
        folders = []
        for row in await cursor.fetchall():
            c2 = await db.execute(
                "SELECT playlist_id FROM folder_playlists WHERE folder_id = ?", (row["id"],)
            )
            pids = [r["playlist_id"] for r in await c2.fetchall()]
            folders.append(Folder(id=row["id"], name=row["name"], playlist_ids=pids))
        return folders
    finally:
        await db.close()


@router.post("/folders", response_model=Folder)
async def create_folder(body: CreateFolderRequest, creds: RequireCreds):
    db = await get_db()
    try:
        cursor = await db.execute("INSERT INTO folders (name) VALUES (?)", (body.name,))
        await db.commit()
        return Folder(id=cursor.lastrowid, name=body.name)
    finally:
        await db.close()


@router.patch("/folders/{folder_id}", response_model=Folder)
async def update_folder(folder_id: int, body: UpdateFolderRequest, creds: RequireCreds):
    db = await get_db()
    try:
        if body.name is not None:
            await db.execute("UPDATE folders SET name = ? WHERE id = ?", (body.name, folder_id))
        if body.playlist_ids is not None:
            await db.execute("DELETE FROM folder_playlists WHERE folder_id = ?", (folder_id,))
            for pid in body.playlist_ids:
                await db.execute(
                    "INSERT OR IGNORE INTO folder_playlists (folder_id, playlist_id) VALUES (?, ?)",
                    (folder_id, pid),
                )
        await db.commit()

        cursor = await db.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
        row = await cursor.fetchone()
        c2 = await db.execute("SELECT playlist_id FROM folder_playlists WHERE folder_id = ?", (folder_id,))
        pids = [r["playlist_id"] for r in await c2.fetchall()]
        return Folder(id=row["id"], name=row["name"], playlist_ids=pids)
    finally:
        await db.close()


@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: int, creds: RequireCreds):
    db = await get_db()
    try:
        await db.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        await db.commit()
    finally:
        await db.close()
    return {"ok": True}
