<script lang="ts">
  import { confirmState, resolveConfirm } from "../lib/stores";
</script>

{#if $confirmState}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
    onkeydown={(e) => e.key === "Escape" && resolveConfirm(false)}
  >
    <div class="mx-4 w-full max-w-sm rounded-lg border border-border bg-surface p-6 shadow-xl">
      <p class="text-sm text-text">{$confirmState.message}</p>
      <div class="mt-5 flex justify-end gap-3">
        <button
          onclick={() => resolveConfirm(false)}
          class="rounded border border-border px-4 py-1.5 text-sm text-text-muted hover:bg-surface-hover"
        >
          Cancel
        </button>
        <button
          onclick={() => resolveConfirm(true)}
          class="rounded bg-accent px-4 py-1.5 text-sm font-medium text-white hover:bg-accent-hover"
          class:!bg-red={$confirmState.destructive}
          class:hover:!opacity-80={$confirmState.destructive}
        >
          {$confirmState.confirmLabel || "Confirm"}
        </button>
      </div>
    </div>
  </div>
{/if}
