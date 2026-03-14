<script lang="ts">
  import type { Video } from "../lib/types";
  import { playlists, draggingVideoItemId, draggingVideoPlaylistId } from "../lib/stores";

  let {
    video,
    playlistId,
    selected = false,
    onToggle,
    onDelete,
    onMove,
  }: {
    video: Video;
    playlistId: string;
    selected?: boolean;
    onToggle?: (id: string) => void;
    onDelete?: (id: string) => void;
    onMove?: (playlistItemId: string, targetPlaylistId: string) => void;
  } = $props();

  let moveTarget = $state("");

  const statusColor: Record<string, string> = {
    available: "border-green",
    unavailable: "border-red",
    private: "border-yellow",
    deleted: "border-gray",
  };

  function formatDuration(iso: string | null): string {
    if (!iso) return "--:--";
    const match = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
    if (!match) return iso;
    const h = match[1] ? `${match[1]}:` : "";
    const m = (match[2] || "0").padStart(h ? 2 : 1, "0");
    const s = (match[3] || "0").padStart(2, "0");
    return `${h}${m}:${s}`;
  }

  const videoUrl = $derived(`https://www.youtube.com/watch?v=${video.id}`);
  const otherPlaylists = $derived($playlists.filter((p) => p.id !== playlistId));

  function handleMoveSelect(e: Event) {
    const target = (e.target as HTMLSelectElement).value;
    if (!target) return;
    onMove?.(video.playlist_item_id!, target);
    moveTarget = "";
  }

  function onDragStart(e: DragEvent) {
    draggingVideoItemId.set(video.playlist_item_id);
    draggingVideoPlaylistId.set(playlistId);
    e.dataTransfer!.effectAllowed = "move";
    e.dataTransfer!.setData("text/plain", video.playlist_item_id!);
  }

  function onDragEnd() {
    draggingVideoItemId.set(null);
    draggingVideoPlaylistId.set(null);
  }
</script>

<div
  class="group relative overflow-hidden rounded-lg border {statusColor[video.status]} bg-surface transition hover:border-text-muted"
  draggable="true"
  ondragstart={onDragStart}
  ondragend={onDragEnd}
  role="listitem"
>
  <div class="absolute left-2 top-2 z-10">
    <input
      type="checkbox"
      checked={selected}
      onchange={() => onToggle?.(video.playlist_item_id!)}
      class="accent-accent"
    />
  </div>
  <button
    onclick={() => onDelete?.(video.playlist_item_id!)}
    class="absolute right-2 top-2 z-10 rounded bg-bg/70 p-1 text-text-muted opacity-0 transition hover:text-red group-hover:opacity-100"
    title="Remove from playlist"
  >
    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
    </svg>
  </button>

  {#if video.thumbnail_url}
    <div class="relative">
      <img src={video.thumbnail_url} alt="" class="aspect-video w-full object-cover" />
      <span class="absolute bottom-1 right-1 rounded bg-bg/80 px-1.5 py-0.5 text-xs text-text">
        {formatDuration(video.duration)}
      </span>
    </div>
  {:else}
    <div class="flex aspect-video w-full items-center justify-center bg-surface-hover text-xs text-text-muted">
      No thumbnail
    </div>
  {/if}

  <div class="p-2">
    {#if video.status === "available"}
      <a href={videoUrl} target="_blank" rel="noopener" class="line-clamp-2 text-xs font-medium text-text hover:text-accent">
        {video.title || "Untitled"}
      </a>
    {:else}
      <p class="line-clamp-2 text-xs text-text-muted">{video.title || "Unavailable video"}</p>
    {/if}
    <p class="mt-0.5 truncate text-xs text-text-muted">{video.channel_title || "--"}</p>
    <select
      bind:value={moveTarget}
      onchange={handleMoveSelect}
      class="mt-1 w-full rounded border border-border bg-bg px-1 py-0.5 text-xs text-text-muted opacity-0 transition group-hover:opacity-100"
    >
      <option value="">Move to...</option>
      {#each otherPlaylists as pl (pl.id)}
        <option value={pl.id}>{pl.title}</option>
      {/each}
    </select>
  </div>
</div>
