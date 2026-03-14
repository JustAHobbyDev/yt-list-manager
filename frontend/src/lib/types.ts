export interface PlaylistSummary {
  id: string;
  title: string;
  description: string | null;
  thumbnail_url: string | null;
  item_count: number;
  published_at: string | null;
  last_synced_at: string | null;
  available_count: number;
  unavailable_count: number;
}

export interface Video {
  id: string;
  title: string | null;
  channel_title: string | null;
  thumbnail_url: string | null;
  duration: string | null;
  status: "available" | "unavailable" | "private" | "deleted";
  playlist_item_id: string | null;
  position: number | null;
  added_at: string | null;
}

export interface PlaylistDetail {
  id: string;
  title: string;
  description: string | null;
  thumbnail_url: string | null;
  item_count: number;
  published_at: string | null;
  last_synced_at: string | null;
  videos: Video[];
}

export interface OverlapPair {
  playlist_a_id: string;
  playlist_a_title: string;
  playlist_b_id: string;
  playlist_b_title: string;
  shared_video_ids: string[];
  count: number;
}

export interface AuthStatus {
  authenticated: boolean;
  channel_title: string | null;
}

export interface SyncProgress {
  status: "idle" | "syncing" | "done" | "error";
  current_playlist: string | null;
  playlists_done: number;
  playlists_total: number;
  message: string | null;
}

export interface QuotaInfo {
  estimated_used: number;
  daily_limit: number;
}

export interface Folder {
  id: number;
  name: string;
  playlist_ids: string[];
}
