<script lang="ts">
  import { playlists, addToast, showConfirm } from "../lib/stores";
  import { mergePlaylists } from "../lib/api";

  let {
    onDone,
  }: {
    onDone?: () => void;
  } = $props();

  let selectedSources = $state<Set<string>>(new Set());
  let targetId = $state("");
  let loading = $state(false);

  function toggleSource(id: string) {
    const next = new Set(selectedSources);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    selectedSources = next;
  }

  const availableTargets = $derived(
    $playlists.filter((p) => !selectedSources.has(p.id))
  );

  async function handleMerge() {
    if (selectedSources.size === 0 || !targetId) return;
    const ok = await showConfirm({
      message: `Merge ${selectedSources.size} playlist(s) into the target? This will add non-duplicate videos.`,
      confirmLabel: "Merge",
    });
    if (!ok) return;

    loading = true;
    try {
      const result = await mergePlaylists([...selectedSources], targetId);
      addToast(
        `Added ${result.added} videos, skipped ${result.skipped_duplicates} duplicates`,
        "success"
      );
      onDone?.();
    } catch (e: any) {
      addToast(e.message, "error");
    } finally {
      loading = false;
    }
  }
</script>

<div class="rounded-lg border border-border bg-surface p-4">
  <h3 class="mb-3 text-sm font-semibold">Merge Playlists</h3>

  <div class="mb-4">
    <p class="mb-2 text-xs text-text-muted">Select source playlists:</p>
    <div class="flex max-h-48 flex-col gap-1 overflow-y-auto">
      {#each $playlists as pl (pl.id)}
        <label class="flex items-center gap-2 rounded px-2 py-1 text-sm hover:bg-surface-hover">
          <input
            type="checkbox"
            checked={selectedSources.has(pl.id)}
            onchange={() => toggleSource(pl.id)}
            class="accent-accent"
          />
          {pl.title}
          <span class="ml-auto text-xs text-text-muted">{pl.item_count}</span>
        </label>
      {/each}
    </div>
  </div>

  <div class="mb-4">
    <p class="mb-2 text-xs text-text-muted">Merge into:</p>
    <select
      bind:value={targetId}
      class="w-full rounded border border-border bg-bg px-3 py-2 text-sm text-text"
    >
      <option value="">Select target playlist...</option>
      {#each availableTargets as pl (pl.id)}
        <option value={pl.id}>{pl.title}</option>
      {/each}
    </select>
  </div>

  <button
    onclick={handleMerge}
    disabled={selectedSources.size === 0 || !targetId || loading}
    class="rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50"
  >
    {loading ? "Merging..." : "Merge"}
  </button>
</div>
