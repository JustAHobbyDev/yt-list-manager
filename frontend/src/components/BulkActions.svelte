<script lang="ts">
  import type { PlaylistSummary } from "../lib/types";
  import { playlists, addToast, showConfirm } from "../lib/stores";
  import { removeVideos, moveVideos } from "../lib/api";

  let {
    selectedIds = [],
    playlistId,
    onDone,
  }: {
    selectedIds: string[];
    playlistId: string;
    onDone?: () => void;
  } = $props();

  let moveTarget = $state("");
  let showMovePanel = $state(false);

  async function handleDelete() {
    const ok = await showConfirm({
      message: `Remove ${selectedIds.length} video(s) from this playlist?`,
      confirmLabel: "Remove",
      destructive: true,
    });
    if (!ok) return;
    try {
      const result = await removeVideos(playlistId, selectedIds);
      addToast(`Removed ${result.removed} video(s)`, "success");
      onDone?.();
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  async function handleMove() {
    if (!moveTarget) return;
    try {
      const result = await moveVideos(playlistId, moveTarget, selectedIds);
      addToast(`Moved ${result.moved} video(s)`, "success");
      showMovePanel = false;
      onDone?.();
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  const otherPlaylists = $derived($playlists.filter((p) => p.id !== playlistId));
</script>

{#if selectedIds.length > 0}
  <div class="flex items-center gap-3 rounded-lg border border-border bg-surface px-4 py-2">
    <span class="text-sm text-text-muted">{selectedIds.length} selected</span>

    <button
      onclick={handleDelete}
      class="rounded bg-red px-3 py-1 text-xs font-medium text-white hover:opacity-80"
    >
      Remove
    </button>

    <button
      onclick={() => (showMovePanel = !showMovePanel)}
      class="rounded border border-border px-3 py-1 text-xs font-medium text-text hover:bg-surface-hover"
    >
      Move to...
    </button>

    {#if showMovePanel}
      <select
        bind:value={moveTarget}
        class="rounded border border-border bg-bg px-2 py-1 text-xs text-text"
      >
        <option value="">Select playlist...</option>
        {#each otherPlaylists as pl (pl.id)}
          <option value={pl.id}>{pl.title}</option>
        {/each}
      </select>
      <button
        onclick={handleMove}
        disabled={!moveTarget}
        class="rounded bg-accent px-3 py-1 text-xs font-medium text-white hover:bg-accent-hover disabled:opacity-50"
      >
        Move
      </button>
    {/if}
  </div>
{/if}
