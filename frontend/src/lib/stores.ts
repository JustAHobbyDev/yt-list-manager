import { writable, get } from "svelte/store";
import type { AuthStatus, PlaylistSummary, SyncProgress, Folder } from "./types";

export const authStatus = writable<AuthStatus>({ authenticated: false, channel_title: null });
export const playlists = writable<PlaylistSummary[]>([]);
export const folders = writable<Folder[]>([]);
export const syncProgress = writable<SyncProgress>({
  status: "idle",
  current_playlist: null,
  playlists_done: 0,
  playlists_total: 0,
  message: null,
});
export const toasts = writable<{ id: number; message: string; type: "success" | "error" | "info" }[]>([]);

let toastId = 0;
export function addToast(message: string, type: "success" | "error" | "info" = "info") {
  const id = ++toastId;
  toasts.update((t) => [...t, { id, message, type }]);
  setTimeout(() => {
    toasts.update((t) => t.filter((x) => x.id !== id));
  }, 4000);
}

// ── Confirm dialog ──────────────────────────────────────────────
interface ConfirmOptions {
  message: string;
  confirmLabel?: string;
  destructive?: boolean;
}

export const confirmState = writable<(ConfirmOptions & { _resolve: (v: boolean) => void }) | null>(null);

export function showConfirm(opts: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    confirmState.set({ ...opts, _resolve: resolve });
  });
}

export function resolveConfirm(value: boolean) {
  const state = get(confirmState);
  if (state) {
    state._resolve(value);
    confirmState.set(null);
  }
}

// ── History-based router ────────────────────────────────────────
export const currentPage = writable<string>("dashboard");
export const currentPlaylistId = writable<string | null>(null);

function stateToUrl(page: string, playlistId?: string | null): string {
  if (page === "playlist" && playlistId) return `/playlist/${playlistId}`;
  if (page === "overlaps") return "/overlaps";
  return "/";
}

function urlToState(path: string): { page: string; playlistId: string | null } {
  const playlistMatch = path.match(/^\/playlist\/(.+)$/);
  if (playlistMatch) return { page: "playlist", playlistId: playlistMatch[1] };
  if (path === "/overlaps") return { page: "overlaps", playlistId: null };
  return { page: "dashboard", playlistId: null };
}

export function navigateTo(page: string, playlistId?: string) {
  const pid = playlistId ?? null;
  currentPage.set(page);
  currentPlaylistId.set(pid);
  const url = stateToUrl(page, pid);
  history.pushState({ page, playlistId: pid }, "", url);
}

export function initRouter() {
  // Set initial state from URL
  const { page, playlistId } = urlToState(window.location.pathname);
  currentPage.set(page);
  currentPlaylistId.set(playlistId);
  history.replaceState({ page, playlistId }, "", stateToUrl(page, playlistId));

  // Listen for back/forward
  window.addEventListener("popstate", (e) => {
    if (e.state) {
      currentPage.set(e.state.page);
      currentPlaylistId.set(e.state.playlistId);
    } else {
      const { page, playlistId } = urlToState(window.location.pathname);
      currentPage.set(page);
      currentPlaylistId.set(playlistId);
    }
  });
}

// ── Global drag state (videos dragged from detail onto sidebar playlists) ──
export const draggingVideoItemId = writable<string | null>(null);
export const draggingVideoPlaylistId = writable<string | null>(null);
