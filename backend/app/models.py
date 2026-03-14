from pydantic import BaseModel


class PlaylistSummary(BaseModel):
    id: str
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
    item_count: int = 0
    published_at: str | None = None
    last_synced_at: str | None = None
    available_count: int = 0
    unavailable_count: int = 0


class Video(BaseModel):
    id: str
    title: str | None = None
    channel_title: str | None = None
    thumbnail_url: str | None = None
    duration: str | None = None
    status: str = "available"
    playlist_item_id: str | None = None
    position: int | None = None
    added_at: str | None = None


class PlaylistDetail(BaseModel):
    id: str
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
    item_count: int = 0
    published_at: str | None = None
    last_synced_at: str | None = None
    videos: list[Video] = []


class OverlapPair(BaseModel):
    playlist_a_id: str
    playlist_a_title: str
    playlist_b_id: str
    playlist_b_title: str
    shared_video_ids: list[str]
    count: int


class RemoveVideosRequest(BaseModel):
    playlist_item_ids: list[str]


class MoveVideosRequest(BaseModel):
    source_playlist_id: str
    target_playlist_id: str
    playlist_item_ids: list[str]
    delete_from_source: bool = True


class MergeRequest(BaseModel):
    source_playlist_ids: list[str]
    target_playlist_id: str
    delete_sources: bool = False


class RenamePlaylistRequest(BaseModel):
    title: str


class Folder(BaseModel):
    id: int
    name: str
    playlist_ids: list[str] = []


class CreateFolderRequest(BaseModel):
    name: str


class UpdateFolderRequest(BaseModel):
    name: str | None = None
    playlist_ids: list[str] | None = None


class AuthStatus(BaseModel):
    authenticated: bool
    channel_title: str | None = None


class SyncProgress(BaseModel):
    status: str  # idle | syncing | done | error
    current_playlist: str | None = None
    playlists_done: int = 0
    playlists_total: int = 0
    message: str | None = None


class QuotaInfo(BaseModel):
    estimated_used: int = 0
    daily_limit: int = 10000
