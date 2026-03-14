<script lang="ts">
  import { onMount } from "svelte";
  import { authStatus, playlists, folders, currentPage, currentPlaylistId, initRouter } from "./lib/stores";
  import { getAuthStatus, getPlaylists, getFolders } from "./lib/api";
  import Sidebar from "./components/Sidebar.svelte";
  import Toast from "./components/Toast.svelte";
  import ConfirmDialog from "./components/ConfirmDialog.svelte";
  import Dashboard from "./pages/Dashboard.svelte";
  import PlaylistDetail from "./pages/PlaylistDetail.svelte";
  import Overlaps from "./pages/Overlaps.svelte";

  onMount(async () => {
    initRouter();
    try {
      const status = await getAuthStatus();
      authStatus.set(status);
      if (status.authenticated) {
        const [pls, flds] = await Promise.all([getPlaylists(), getFolders()]);
        playlists.set(pls);
        folders.set(flds);
      }
    } catch {
      // Backend not running
    }
  });
</script>

<div class="flex h-screen overflow-hidden bg-bg">
  <Sidebar />
  <main class="flex-1 overflow-y-auto p-6">
    {#if $currentPage === "dashboard"}
      <Dashboard />
    {:else if $currentPage === "playlist" && $currentPlaylistId}
      <PlaylistDetail playlistId={$currentPlaylistId} />
    {:else if $currentPage === "overlaps"}
      <Overlaps />
    {/if}
  </main>
</div>

<Toast />
<ConfirmDialog />
