import type {
  AuthStatus,
  PlaylistSummary,
  PlaylistDetail,
  OverlapPair,
  SyncProgress,
  QuotaInfo,
  Folder,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

// Auth
export const getAuthStatus = () => request<AuthStatus>("/auth/status");
export const logout = () => request<{ ok: boolean }>("/auth/logout", { method: "POST" });
export const loginUrl = `${BASE}/auth/login`;

// Playlists
export const getPlaylists = () => request<PlaylistSummary[]>("/playlists");
export const getPlaylist = (id: string) => request<PlaylistDetail>(`/playlists/${id}`);
export const getOverlaps = () => request<OverlapPair[]>("/playlists/overlaps");

export const renamePlaylist = (id: string, title: string) =>
  request<{ ok: boolean }>(`/playlists/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });

export const deletePlaylist = (id: string) =>
  request<{ ok: boolean }>(`/playlists/${id}`, { method: "DELETE" });

export const removeVideos = (playlistId: string, playlistItemIds: string[]) =>
  request<{ removed: number; errors: any[] }>(`/playlists/${playlistId}/remove-videos`, {
    method: "POST",
    body: JSON.stringify({ playlist_item_ids: playlistItemIds }),
  });

export const removeUnavailable = (playlistId: string) =>
  request<{ removed: number; errors: any[] }>(`/playlists/${playlistId}/remove-unavailable`, {
    method: "POST",
  });

export const removeAllUnavailable = () =>
  request<{ removed: number; errors: any[] }>("/playlists/remove-all-unavailable", {
    method: "POST",
  });

export const removeEmptyPlaylists = () =>
  request<{ removed: number; errors: any[] }>("/playlists/remove-empty", {
    method: "POST",
  });

export const moveVideos = (
  sourcePlaylistId: string,
  targetPlaylistId: string,
  playlistItemIds: string[],
  deleteFromSource = true
) =>
  request<{ moved: number; errors: any[] }>("/playlists/move-videos", {
    method: "POST",
    body: JSON.stringify({
      source_playlist_id: sourcePlaylistId,
      target_playlist_id: targetPlaylistId,
      playlist_item_ids: playlistItemIds,
      delete_from_source: deleteFromSource,
    }),
  });

export const mergePlaylists = (
  sourcePlaylistIds: string[],
  targetPlaylistId: string,
  deleteSources = false
) =>
  request<{ added: number; skipped_duplicates: number; errors: any[] }>("/playlists/merge", {
    method: "POST",
    body: JSON.stringify({
      source_playlist_ids: sourcePlaylistIds,
      target_playlist_id: targetPlaylistId,
      delete_sources: deleteSources,
    }),
  });

// Folders
export const getFolders = () => request<Folder[]>("/playlists/folders/list");
export const createFolder = (name: string) =>
  request<Folder>("/playlists/folders", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
export const updateFolder = (id: number, data: { name?: string; playlist_ids?: string[] }) =>
  request<Folder>(`/playlists/folders/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
export const deleteFolder = (id: number) =>
  request<{ ok: boolean }>(`/playlists/folders/${id}`, { method: "DELETE" });

// Sync
export const startSync = () => request<{ ok: boolean }>("/sync", { method: "POST" });
export const startSyncOne = (id: string) =>
  request<{ ok: boolean }>(`/sync/${id}`, { method: "POST" });

export function subscribeSyncProgress(
  onMessage: (progress: SyncProgress) => void,
  onError?: (err: Event) => void
): EventSource {
  const es = new EventSource(`${BASE}/sync/status`);
  es.onmessage = (e) => {
    const data: SyncProgress = JSON.parse(e.data);
    onMessage(data);
    if (data.status === "done" || data.status === "error") {
      es.close();
    }
  };
  es.onerror = (e) => {
    onError?.(e);
    es.close();
  };
  return es;
}

// Quota
export const getQuota = () => request<QuotaInfo>("/quota");
