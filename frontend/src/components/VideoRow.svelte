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
    available: "bg-green",
    unavailable: "bg-red",
    private: "bg-yellow",
    deleted: "bg-gray",
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

<tr
  class="border-b border-border hover:bg-surface-hover"
  draggable="true"
  ondragstart={onDragStart}
  ondragend={onDragEnd}
>
  <td class="w-8 px-3 py-2">
    <input
      type="checkbox"
      checked={selected}
      onchange={() => onToggle?.(video.playlist_item_id!)}
      class="accent-accent"
    />
  </td>
  <td class="w-10 px-2 py-2">
    <span class="inline-block h-2.5 w-2.5 rounded-full {statusColor[video.status]}"></span>
  </td>
  <td class="w-24 py-2">
    {#if video.thumbnail_url}
      <img src={video.thumbnail_url} alt="" class="h-12 w-20 rounded object-cover" />
    {:else}
      <div class="flex h-12 w-20 items-center justify-center rounded bg-surface-hover text-xs text-text-muted">
        N/A
      </div>
    {/if}
  </td>
  <td class="max-w-xs truncate px-3 py-2 text-sm">
    {#if video.status === "available"}
      <a href={videoUrl} target="_blank" rel="noopener" class="text-text hover:text-accent hover:underline">
        {video.title || "Untitled"}
      </a>
    {:else}
      <span class="text-text-muted">{video.title || "Unavailable video"}</span>
    {/if}
  </td>
  <td class="px-3 py-2 text-sm text-text-muted">
    {video.channel_title || "--"}
  </td>
  <td class="px-3 py-2 text-sm text-text-muted">
    {formatDuration(video.duration)}
  </td>
  <td class="px-3 py-2 text-xs capitalize text-text-muted">
    {video.status}
  </td>
  <td class="w-28 px-2 py-2">
    <select
      bind:value={moveTarget}
      onchange={handleMoveSelect}
      class="w-full rounded border border-border bg-bg px-1 py-0.5 text-xs text-text-muted"
    >
      <option value="">Move to...</option>
      {#each otherPlaylists as pl (pl.id)}
        <option value={pl.id}>{pl.title}</option>
      {/each}
    </select>
  </td>
  <td class="w-10 px-2 py-2">
    <button
      onclick={() => onDelete?.(video.playlist_item_id!)}
      class="rounded p-1 text-text-muted hover:bg-red/20 hover:text-red"
      title="Remove from playlist"
    >
      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    </button>
  </td>
</tr>
