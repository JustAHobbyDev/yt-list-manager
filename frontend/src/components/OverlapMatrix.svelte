<script lang="ts">
  import type { OverlapPair } from "../lib/types";
  import { navigateTo } from "../lib/stores";

  let { overlaps }: { overlaps: OverlapPair[] } = $props();
</script>

{#if overlaps.length === 0}
  <p class="py-8 text-center text-text-muted">No overlapping videos found between playlists.</p>
{:else}
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-border text-left text-xs text-text-muted">
          <th class="px-4 py-2">Playlist A</th>
          <th class="px-4 py-2">Playlist B</th>
          <th class="px-4 py-2 text-right">Shared Videos</th>
        </tr>
      </thead>
      <tbody>
        {#each overlaps as pair (pair.playlist_a_id + pair.playlist_b_id)}
          <tr class="border-b border-border hover:bg-surface-hover">
            <td class="px-4 py-2">
              <button
                onclick={() => navigateTo("playlist", pair.playlist_a_id)}
                class="text-accent hover:underline"
              >
                {pair.playlist_a_title}
              </button>
            </td>
            <td class="px-4 py-2">
              <button
                onclick={() => navigateTo("playlist", pair.playlist_b_id)}
                class="text-accent hover:underline"
              >
                {pair.playlist_b_title}
              </button>
            </td>
            <td class="px-4 py-2 text-right font-mono">{pair.count}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}
