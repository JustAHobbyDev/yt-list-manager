<script lang="ts">
  import { onMount } from "svelte";
  import { addToast } from "../lib/stores";
  import { getOverlaps } from "../lib/api";
  import type { OverlapPair } from "../lib/types";
  import OverlapMatrix from "../components/OverlapMatrix.svelte";
  import MergeWizard from "../components/MergeWizard.svelte";

  let overlaps = $state<OverlapPair[]>([]);
  let loading = $state(true);

  async function load() {
    loading = true;
    try {
      overlaps = await getOverlaps();
    } catch (e: any) {
      addToast(e.message, "error");
    } finally {
      loading = false;
    }
  }

  onMount(load);
</script>

<div>
  <h2 class="mb-4 text-2xl font-bold">Playlist Overlaps</h2>

  {#if loading}
    <p class="py-8 text-center text-text-muted">Loading...</p>
  {:else}
    <div class="mb-8 rounded-lg border border-border">
      <OverlapMatrix {overlaps} />
    </div>

    <MergeWizard onDone={load} />
  {/if}
</div>
