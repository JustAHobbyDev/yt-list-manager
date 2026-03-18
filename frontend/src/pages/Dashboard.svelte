<script lang="ts">
  import { playlists, authStatus, addToast, showConfirm, isSystemPlaylist } from "../lib/stores";
  import { removeAllUnavailable, removeEmptyPlaylists, getPlaylists } from "../lib/api";
  import PlaylistCard from "../components/PlaylistCard.svelte";

  const totalVideos = $derived($playlists.reduce((s, p) => s + p.item_count, 0));
  const totalUnavailable = $derived($playlists.reduce((s, p) => s + p.unavailable_count, 0));
  const emptyCount = $derived(
    $playlists.filter((p) => p.item_count === 0 && !isSystemPlaylist(p.id)).length
  );

  async function handleRemoveAllUnavailable() {
    const ok = await showConfirm({
      message: `Remove all ${totalUnavailable} unavailable videos across all playlists?`,
      confirmLabel: "Remove All",
      destructive: true,
    });
    if (!ok) return;
    try {
      const result = await removeAllUnavailable();
      addToast(`Removed ${result.removed} unavailable video(s)`, "success");
      getPlaylists().then((p) => playlists.set(p));
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  async function handleRemoveEmptyPlaylists() {
    const ok = await showConfirm({
      message: `Delete ${emptyCount} empty playlist(s)? This cannot be undone.`,
      confirmLabel: "Delete",
      destructive: true,
    });
    if (!ok) return;
    try {
      const result = await removeEmptyPlaylists();
      addToast(`Deleted ${result.removed} empty playlist(s)`, "success");
      getPlaylists().then((p) => playlists.set(p));
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }
</script>

<div>
  <div class="mb-6 flex items-end justify-between">
    <div>
      <h2 class="text-2xl font-bold">Dashboard</h2>
      <p class="text-sm text-text-muted">
        {$playlists.length} playlists &middot; {totalVideos} videos
        {#if totalUnavailable > 0}
          &middot; <span class="text-red">{totalUnavailable} unavailable</span>
        {/if}
      </p>
    </div>
    <div class="flex gap-2">
      {#if totalUnavailable > 0}
        <button
          onclick={handleRemoveAllUnavailable}
          class="rounded bg-red px-4 py-2 text-sm font-medium text-white hover:opacity-80"
        >
          Remove All {totalUnavailable} Unavailable
        </button>
      {/if}
      {#if emptyCount > 0}
        <button
          onclick={handleRemoveEmptyPlaylists}
          class="rounded bg-red px-4 py-2 text-sm font-medium text-white hover:opacity-80"
        >
          Delete {emptyCount} Empty
        </button>
      {/if}
    </div>
  </div>

  {#if !$authStatus.authenticated}
    <div class="flex flex-col items-center justify-center py-20 text-center">
      <p class="mb-2 text-lg text-text-muted">Sign in to manage your YouTube playlists</p>
      <p class="text-sm text-text-muted">Click "Sign in with Google" in the sidebar to get started.</p>
    </div>
  {:else if $playlists.length === 0}
    <div class="flex flex-col items-center justify-center py-20 text-center">
      <p class="mb-2 text-lg text-text-muted">No playlists yet</p>
      <p class="text-sm text-text-muted">Click "Sync All" to fetch your playlists from YouTube.</p>
    </div>
  {:else}
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {#each $playlists as pl (pl.id)}
        <PlaylistCard playlist={pl} />
      {/each}
    </div>
  {/if}
</div>
