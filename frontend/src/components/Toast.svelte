<script lang="ts">
  import { toasts } from "../lib/stores";
</script>

<div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
  {#each $toasts as toast (toast.id)}
    <div
      class="rounded-lg px-4 py-3 text-sm shadow-lg transition-all"
      class:bg-green-900={toast.type === "success"}
      class:text-green-200={toast.type === "success"}
      class:bg-red-900={toast.type === "error"}
      class:text-red-200={toast.type === "error"}
      class:bg-surface={toast.type === "info"}
      class:text-text={toast.type === "info"}
      class:border={toast.type === "info"}
      class:border-border={toast.type === "info"}
    >
      {toast.message}
    </div>
  {/each}
</div>
