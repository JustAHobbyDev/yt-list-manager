<script lang="ts">
  import type { PlaylistSummary } from "../lib/types";
  import { navigateTo } from "../lib/stores";

  let { playlist }: { playlist: PlaylistSummary } = $props();

  const health = $derived(
    playlist.available_count + playlist.unavailable_count > 0
      ? Math.round(
          (playlist.available_count / (playlist.available_count + playlist.unavailable_count)) * 100
        )
      : 100
  );
</script>

<button
  onclick={() => navigateTo("playlist", playlist.id)}
  class="flex flex-col overflow-hidden rounded-lg border border-border bg-surface text-left transition hover:border-text-muted"
>
  {#if playlist.thumbnail_url}
    <img
      src={playlist.thumbnail_url}
      alt={playlist.title}
      class="h-32 w-full object-cover"
    />
  {:else}
    <div class="flex h-32 w-full items-center justify-center bg-surface-hover text-text-muted">
      No thumbnail
    </div>
  {/if}

  <div class="flex flex-1 flex-col p-3">
    <h3 class="truncate text-sm font-medium">{playlist.title}</h3>
    <p class="mt-1 text-xs text-text-muted">{playlist.item_count} videos</p>

    <div class="mt-2 flex items-center gap-2">
      <div class="h-1.5 flex-1 rounded bg-border">
        <div
          class="h-1.5 rounded transition-all"
          class:bg-green={health >= 90}
          class:bg-yellow={health >= 50 && health < 90}
          class:bg-red={health < 50}
          style="width: {health}%"
        ></div>
      </div>
      <span class="text-xs text-text-muted">{health}%</span>
    </div>

    {#if playlist.unavailable_count > 0}
      <p class="mt-1 text-xs text-red">
        {playlist.unavailable_count} unavailable
      </p>
    {/if}
  </div>
</button>
