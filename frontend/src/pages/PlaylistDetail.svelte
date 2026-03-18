<script lang="ts">
  import { addToast, navigateTo, showConfirm, playlists, syncProgress, applyMoveToPlaylists, videoMoveEvent, isSystemPlaylist } from "../lib/stores";
  import {
    getPlaylist,
    removeUnavailable,
    removeVideos,
    moveVideos,
    renamePlaylist,
    deletePlaylist,
    startSyncOne,
    subscribeSyncProgress,
    getPlaylists,
  } from "../lib/api";
  import type { PlaylistDetail as PlaylistDetailType } from "../lib/types";
  import VideoRow from "../components/VideoRow.svelte";
  import VideoCard from "../components/VideoCard.svelte";
  import BulkActions from "../components/BulkActions.svelte";

  let { playlistId }: { playlistId: string } = $props();

  let detail = $state<PlaylistDetailType | null>(null);
  let loading = $state(true);
  let selected = $state<Set<string>>(new Set());
  let viewMode = $state<"table" | "gallery">("table");
  let editing = $state(false);
  let editTitle = $state("");

  async function load() {
    loading = true;
    try {
      detail = await getPlaylist(playlistId);
    } catch (e: any) {
      addToast(e.message, "error");
    } finally {
      loading = false;
    }
  }

  function refreshPlaylists() {
    getPlaylists().then((p) => playlists.set(p));
  }

  function toggleSelect(itemId: string) {
    const next = new Set(selected);
    if (next.has(itemId)) next.delete(itemId);
    else next.add(itemId);
    selected = next;
  }

  function toggleAll() {
    if (!detail) return;
    if (selected.size === detail.videos.length) {
      selected = new Set();
    } else {
      selected = new Set(detail.videos.map((v) => v.playlist_item_id!));
    }
  }

  async function handleDeleteVideo(playlistItemId: string) {
    try {
      const result = await removeVideos(playlistId, [playlistItemId]);
      addToast(`Removed ${result.removed} video`, "success");
      await load();
      refreshPlaylists();
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  async function handleMoveVideo(playlistItemId: string, targetPlaylistId: string) {
    try {
      const video = detail?.videos.find((v) => v.playlist_item_id === playlistItemId);
      const result = await moveVideos(playlistId, targetPlaylistId, [playlistItemId]);
      addToast(`Moved ${result.moved} video`, "success");
      if (detail) {
        detail.videos = detail.videos.filter((v) => v.playlist_item_id !== playlistItemId);
      }
      const isAvailable = video?.status === "available" ? 1 : 0;
      applyMoveToPlaylists(playlistId, targetPlaylistId, 1, isAvailable, 1 - isAvailable);
      getPlaylists().then((p) => playlists.set(p));
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  async function handleRemoveUnavailable() {
    const count = detail?.videos.filter((v) => v.status !== "available").length || 0;
    const ok = await showConfirm({
      message: `Remove ${count} unavailable video(s) from this playlist?`,
      confirmLabel: "Remove",
      destructive: true,
    });
    if (!ok) return;
    try {
      const result = await removeUnavailable(playlistId);
      addToast(`Removed ${result.removed} unavailable video(s)`, "success");
      await load();
      refreshPlaylists();
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  async function handleSyncPlaylist() {
    try {
      await startSyncOne(playlistId);
      subscribeSyncProgress(
        (progress) => {
          syncProgress.set(progress);
          if (progress.status === "done") {
            addToast("Playlist synced", "success");
            load();
            refreshPlaylists();
          } else if (progress.status === "error") {
            addToast(progress.message || "Sync failed", "error");
          }
        },
        () => addToast("Lost connection to sync", "error")
      );
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  function startRename() {
    if (!detail) return;
    editTitle = detail.title;
    editing = true;
  }

  async function saveRename() {
    if (!detail || !editTitle.trim()) return;
    try {
      await renamePlaylist(playlistId, editTitle.trim());
      detail.title = editTitle.trim();
      addToast("Playlist renamed", "success");
      refreshPlaylists();
    } catch (e: any) {
      addToast(e.message, "error");
    }
    editing = false;
  }

  async function handleDeletePlaylist() {
    if (!detail) return;
    const ok = await showConfirm({
      message: `Delete playlist "${detail.title}" from YouTube? This cannot be undone.`,
      confirmLabel: "Delete",
      destructive: true,
    });
    if (!ok) return;
    try {
      await deletePlaylist(playlistId);
      addToast("Playlist deleted", "success");
      refreshPlaylists();
      navigateTo("dashboard");
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  $effect(() => {
    playlistId;
    load();
    selected = new Set();
  });

  $effect(() => {
    const ev = $videoMoveEvent;
    if (ev && ev.sourcePlaylistId === playlistId && detail) {
      const ids = new Set(ev.itemIds);
      detail.videos = detail.videos.filter((v) => !ids.has(v.playlist_item_id!));
      videoMoveEvent.set(null);
    }
  });

  const unavailableCount = $derived(
    detail?.videos.filter((v) => v.status !== "available").length || 0
  );
</script>

{#if loading}
  <div class="flex items-center justify-center py-20">
    <p class="text-text-muted">Loading...</p>
  </div>
{:else if detail}
  <div>
    <div class="mb-4 flex items-start justify-between">
      <div>
        <button
          onclick={() => navigateTo("dashboard")}
          class="mb-2 text-xs text-text-muted hover:text-text"
        >
          &larr; Back to Dashboard
        </button>
        {#if editing}
          <div class="flex items-center gap-2">
            <input
              bind:value={editTitle}
              onkeydown={(e) => e.key === "Enter" && saveRename()}
              class="rounded border border-border bg-bg px-2 py-1 text-2xl font-bold text-text"
            />
            <button onclick={saveRename} class="rounded bg-accent px-3 py-1 text-xs text-white hover:bg-accent-hover">Save</button>
            <button onclick={() => (editing = false)} class="rounded border border-border px-3 py-1 text-xs text-text-muted hover:bg-surface-hover">Cancel</button>
          </div>
        {:else}
          <div class="flex items-center gap-2">
            <h2 class="text-2xl font-bold">{detail.title}</h2>
            <button onclick={startRename} class="rounded p-1 text-text-muted hover:text-text" title="Rename">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          </div>
        {/if}
        <p class="text-sm text-text-muted">
          {detail.videos.length} videos
          {#if unavailableCount > 0}
            &middot; <span class="text-red">{unavailableCount} unavailable</span>
          {/if}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <div class="flex rounded border border-border">
          <button
            onclick={() => (viewMode = "table")}
            class="px-2 py-1.5"
            class:bg-surface-hover={viewMode === "table"}
            title="Table view"
          >
            <svg class="h-4 w-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
          </button>
          <button
            onclick={() => (viewMode = "gallery")}
            class="px-2 py-1.5"
            class:bg-surface-hover={viewMode === "gallery"}
            title="Gallery view"
          >
            <svg class="h-4 w-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
            </svg>
          </button>
        </div>
        <button
          onclick={handleSyncPlaylist}
          class="rounded border border-border px-3 py-1.5 text-xs text-text-muted hover:bg-surface-hover"
        >
          Re-sync
        </button>
        {#if unavailableCount > 0}
          <button
            onclick={handleRemoveUnavailable}
            class="rounded bg-red px-3 py-1.5 text-xs font-medium text-white hover:opacity-80"
          >
            Remove {unavailableCount} Unavailable
          </button>
        {/if}
        {#if !isSystemPlaylist(playlistId)}
          <button
            onclick={handleDeletePlaylist}
            class="rounded border border-red/50 px-3 py-1.5 text-xs text-red hover:bg-red/10"
            title="Delete playlist"
          >
            Delete Playlist
          </button>
        {/if}
      </div>
    </div>

    <BulkActions
      selectedIds={[...selected]}
      {playlistId}
      onDone={(movedIds) => {
        if (movedIds && detail) {
          const ids = new Set(movedIds);
          const moved = detail.videos.filter((v) => ids.has(v.playlist_item_id!));
          detail.videos = detail.videos.filter((v) => !ids.has(v.playlist_item_id!));
          // BulkActions doesn't expose the target playlist id, so only refresh counts via server
          getPlaylists().then((p) => playlists.set(p));
          selected = new Set();
        } else {
          selected = new Set();
          load();
          refreshPlaylists();
        }
      }}
    />

    {#if viewMode === "table"}
      <div class="mt-4 overflow-x-auto rounded-lg border border-border">
        <table class="w-full">
          <thead>
            <tr class="border-b border-border text-left text-xs text-text-muted">
              <th class="w-8 px-3 py-2">
                <input
                  type="checkbox"
                  checked={detail.videos.length > 0 && selected.size === detail.videos.length}
                  onchange={toggleAll}
                  class="accent-accent"
                />
              </th>
              <th class="w-10 px-2 py-2"></th>
              <th class="w-24 py-2"></th>
              <th class="px-3 py-2">Title</th>
              <th class="px-3 py-2">Channel</th>
              <th class="px-3 py-2">Duration</th>
              <th class="px-3 py-2">Status</th>
              <th class="w-28 px-2 py-2">Move</th>
              <th class="w-10 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {#each detail.videos as video (video.playlist_item_id)}
              <VideoRow
                {video}
                {playlistId}
                selected={selected.has(video.playlist_item_id!)}
                onToggle={toggleSelect}
                onDelete={handleDeleteVideo}
                onMove={handleMoveVideo}
              />
            {/each}
          </tbody>
        </table>
      </div>
    {:else}
      <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {#each detail.videos as video (video.playlist_item_id)}
          <VideoCard
            {video}
            {playlistId}
            selected={selected.has(video.playlist_item_id!)}
            onToggle={toggleSelect}
            onDelete={handleDeleteVideo}
            onMove={handleMoveVideo}
          />
        {/each}
      </div>
    {/if}
  </div>
{/if}
