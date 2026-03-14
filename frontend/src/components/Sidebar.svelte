<script lang="ts">
  import { onMount } from "svelte";
  import {
    playlists,
    authStatus,
    syncProgress,
    folders,
    navigateTo,
    currentPage,
    currentPlaylistId,
    addToast,
    draggingVideoItemId,
    draggingVideoPlaylistId,
  } from "../lib/stores";
  import {
    loginUrl,
    logout,
    startSync,
    subscribeSyncProgress,
    getPlaylists,
    getFolders,
    createFolder,
    updateFolder,
    deleteFolder as apiDeleteFolder,
    moveVideos,
  } from "../lib/api";
  import type { Folder } from "../lib/types";

  let filter = $state("");
  let draggingPlaylistId = $state<string | null>(null);
  let dragOverFolderId = $state<number | null>(null);
  let dragOverPlaylistId = $state<string | null>(null);
  let newFolderName = $state("");
  let showNewFolder = $state(false);

  // Is a video being dragged from the detail view?
  const isDraggingVideo = $derived($draggingVideoItemId !== null);

  onMount(async () => {
    try {
      const f = await getFolders();
      folders.set(f);
    } catch {
      // not authed yet
    }
  });

  async function handleSync() {
    try {
      await startSync();
      subscribeSyncProgress(
        (progress) => {
          syncProgress.set(progress);
          if (progress.status === "done") {
            addToast(progress.message || "Sync complete", "success");
            getPlaylists().then((p) => playlists.set(p));
          } else if (progress.status === "error") {
            addToast(progress.message || "Sync failed", "error");
          }
        },
        () => addToast("Lost connection to sync", "error")
      );
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  async function handleLogout() {
    await logout();
    authStatus.set({ authenticated: false, channel_title: null });
    playlists.set([]);
    folders.set([]);
  }

  function healthPercent(available: number, unavailable: number): number {
    const total = available + unavailable;
    if (total === 0) return 100;
    return Math.round((available / total) * 100);
  }

  function fuzzyMatch(text: string, query: string): boolean {
    const lower = text.toLowerCase();
    const q = query.toLowerCase();
    let qi = 0;
    for (let i = 0; i < lower.length && qi < q.length; i++) {
      if (lower[i] === q[qi]) qi++;
    }
    return qi === q.length;
  }

  const filteredPlaylists = $derived(
    filter
      ? $playlists.filter((p) => fuzzyMatch(p.title, filter))
      : $playlists
  );

  const folderedIds = $derived(new Set($folders.flatMap((f) => f.playlist_ids)));
  const unfolderedPlaylists = $derived(
    filteredPlaylists.filter((p) => !folderedIds.has(p.id))
  );

  // ── Playlist drag (reorder into folders) ──
  function onPlaylistDragStart(e: DragEvent, playlistId: string) {
    draggingPlaylistId = playlistId;
    e.dataTransfer!.effectAllowed = "move";
    e.dataTransfer!.setData("application/x-playlist", playlistId);
  }

  function onFolderDragOver(e: DragEvent, folderId: number) {
    e.preventDefault();
    dragOverFolderId = folderId;
  }

  function onFolderDragLeave() {
    dragOverFolderId = null;
  }

  async function onDropOnFolder(e: DragEvent, folder: Folder) {
    e.preventDefault();
    dragOverFolderId = null;

    // Handle video drop onto folder's playlist? No — folders aren't playlists.
    // Handle playlist drag into folder.
    if (!draggingPlaylistId) return;
    if (folder.playlist_ids.includes(draggingPlaylistId)) {
      draggingPlaylistId = null;
      return;
    }

    for (const f of $folders) {
      if (f.id !== folder.id && f.playlist_ids.includes(draggingPlaylistId)) {
        const updated = f.playlist_ids.filter((id) => id !== draggingPlaylistId);
        await updateFolder(f.id, { playlist_ids: updated });
      }
    }

    const newIds = [...folder.playlist_ids, draggingPlaylistId];
    await updateFolder(folder.id, { playlist_ids: newIds });
    folders.set(await getFolders());
    draggingPlaylistId = null;
  }

  async function onDropOnUnfoldered(e: DragEvent) {
    e.preventDefault();
    if (!draggingPlaylistId) return;
    for (const f of $folders) {
      if (f.playlist_ids.includes(draggingPlaylistId)) {
        const updated = f.playlist_ids.filter((id) => id !== draggingPlaylistId);
        await updateFolder(f.id, { playlist_ids: updated });
      }
    }
    folders.set(await getFolders());
    draggingPlaylistId = null;
  }

  // ── Video drop onto a playlist in the sidebar ──
  function onPlaylistItemDragOver(e: DragEvent, plId: string) {
    if (!isDraggingVideo) return;
    // Don't allow dropping onto the source playlist
    if (plId === $draggingVideoPlaylistId) return;
    e.preventDefault();
    dragOverPlaylistId = plId;
  }

  function onPlaylistItemDragLeave() {
    dragOverPlaylistId = null;
  }

  async function onDropOnPlaylistItem(e: DragEvent, targetPlId: string) {
    e.preventDefault();
    dragOverPlaylistId = null;

    const videoItemId = $draggingVideoItemId;
    const sourcePlId = $draggingVideoPlaylistId;
    if (!videoItemId || !sourcePlId || targetPlId === sourcePlId) return;

    draggingVideoItemId.set(null);
    draggingVideoPlaylistId.set(null);

    try {
      const result = await moveVideos(sourcePlId, targetPlId, [videoItemId]);
      addToast(`Moved ${result.moved} video`, "success");
      getPlaylists().then((p) => playlists.set(p));
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }

  async function handleCreateFolder() {
    if (!newFolderName.trim()) return;
    await createFolder(newFolderName.trim());
    folders.set(await getFolders());
    newFolderName = "";
    showNewFolder = false;
  }

  async function handleDeleteFolder(id: number) {
    await apiDeleteFolder(id);
    folders.set(await getFolders());
  }
</script>

{#snippet playlistItem(pl: typeof $playlists[0], indent: boolean)}
  {@const health = healthPercent(pl.available_count, pl.unavailable_count)}
  {@const isDropTarget = isDraggingVideo && pl.id !== $draggingVideoPlaylistId}
  <button
    draggable={!isDraggingVideo ? "true" : "false"}
    ondragstart={(e) => onPlaylistDragStart(e, pl.id)}
    ondragover={(e) => onPlaylistItemDragOver(e, pl.id)}
    ondragleave={onPlaylistItemDragLeave}
    ondrop={(e) => onDropOnPlaylistItem(e, pl.id)}
    onclick={() => navigateTo("playlist", pl.id)}
    class="flex w-full items-center gap-2 py-1.5 text-left text-sm transition-colors hover:bg-surface-hover {indent ? 'px-6' : 'px-4'} {!isDraggingVideo ? 'cursor-grab active:cursor-grabbing' : ''} {$currentPage === 'playlist' && $currentPlaylistId === pl.id ? 'bg-surface-hover' : ''} {dragOverPlaylistId === pl.id ? 'ring-1 ring-accent bg-accent/20' : ''}"
  >
    <span
      class="h-2 w-2 shrink-0 rounded-full"
      class:bg-green={health >= 90}
      class:bg-yellow={health >= 50 && health < 90}
      class:bg-red={health < 50}
    ></span>
    <span class="truncate">{pl.title}</span>
    <span class="ml-auto text-xs text-text-muted">{pl.item_count}</span>
  </button>
{/snippet}

<aside class="flex h-screen w-64 shrink-0 flex-col border-r border-border bg-surface">
  <div class="border-b border-border p-4">
    <h1 class="text-lg font-bold text-accent">YT List Manager</h1>
    {#if $authStatus.authenticated}
      <p class="mt-1 text-xs text-text-muted">{$authStatus.channel_title}</p>
    {/if}
  </div>

  {#if !$authStatus.authenticated}
    <div class="p-4">
      <a
        href={loginUrl}
        class="block rounded bg-accent px-4 py-2 text-center text-sm font-medium text-white hover:bg-accent-hover"
      >
        Sign in with Google
      </a>
    </div>
  {:else}
    <div class="flex gap-2 border-b border-border p-3">
      <button
        onclick={handleSync}
        disabled={$syncProgress.status === "syncing"}
        class="flex-1 rounded bg-accent px-3 py-1.5 text-xs font-medium text-white hover:bg-accent-hover disabled:opacity-50"
      >
        {$syncProgress.status === "syncing" ? "Syncing..." : "Sync All"}
      </button>
      <button
        onclick={handleLogout}
        class="rounded border border-border px-3 py-1.5 text-xs text-text-muted hover:bg-surface-hover"
      >
        Logout
      </button>
    </div>

    {#if $syncProgress.status === "syncing"}
      <div class="border-b border-border px-3 py-2">
        <p class="text-xs text-text-muted">
          {$syncProgress.current_playlist || "Starting..."}
        </p>
        <div class="mt-1 h-1 w-full rounded bg-border">
          <div
            class="h-1 rounded bg-accent transition-all"
            style="width: {$syncProgress.playlists_total > 0
              ? ($syncProgress.playlists_done / $syncProgress.playlists_total) * 100
              : 0}%"
          ></div>
        </div>
      </div>
    {/if}

    <nav class="flex-1 overflow-y-auto">
      <button
        onclick={() => navigateTo("dashboard")}
        class="w-full px-4 py-2 text-left text-sm hover:bg-surface-hover"
        class:bg-surface-hover={$currentPage === "dashboard"}
      >
        Dashboard
      </button>
      <button
        onclick={() => navigateTo("overlaps")}
        class="w-full px-4 py-2 text-left text-sm hover:bg-surface-hover"
        class:bg-surface-hover={$currentPage === "overlaps"}
      >
        Overlaps
      </button>

      <div class="mt-2 border-t border-border pt-2">
        <div class="px-3 pb-2">
          <input
            bind:value={filter}
            placeholder="Filter playlists..."
            class="w-full rounded border border-border bg-bg px-2 py-1 text-xs text-text placeholder:text-text-muted"
          />
        </div>

        <!-- Folders -->
        {#each $folders as folder (folder.id)}
          {@const folderPlaylists = filteredPlaylists.filter((p) => folder.playlist_ids.includes(p.id))}
          <div
            role="group"
            aria-label="Folder: {folder.name}"
            class="border-b border-border/50"
            ondragover={(e) => onFolderDragOver(e, folder.id)}
            ondragleave={onFolderDragLeave}
            ondrop={(e) => onDropOnFolder(e, folder)}
            class:bg-surface-hover={dragOverFolderId === folder.id}
          >
            <div class="group flex items-center gap-1 px-4 py-1">
              <span class="text-xs text-text-muted">&#9660;</span>
              <span class="flex-1 text-xs font-semibold uppercase text-text-muted">{folder.name}</span>
              <button
                onclick={() => handleDeleteFolder(folder.id)}
                class="rounded p-0.5 text-text-muted opacity-0 hover:text-red group-hover:opacity-100"
                title="Delete folder"
              >
                <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            {#each folderPlaylists as pl (pl.id)}
              {@render playlistItem(pl, true)}
            {/each}
          </div>
        {/each}

        <!-- Unfoldered playlists -->
        <div
          role="group"
          aria-label="Unfoldered playlists"
          class="pt-1"
          ondragover={(e) => { e.preventDefault(); }}
          ondrop={onDropOnUnfoldered}
        >
          <div class="flex items-center px-4 py-1">
            <p class="flex-1 text-xs font-semibold uppercase text-text-muted">Playlists</p>
            <button
              onclick={() => (showNewFolder = !showNewFolder)}
              class="rounded p-0.5 text-text-muted hover:text-text"
              title="New folder"
            >
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>

          {#if showNewFolder}
            <div class="flex gap-1 px-4 pb-2">
              <input
                bind:value={newFolderName}
                placeholder="Folder name"
                onkeydown={(e) => e.key === "Enter" && handleCreateFolder()}
                class="flex-1 rounded border border-border bg-bg px-2 py-1 text-xs text-text"
              />
              <button onclick={handleCreateFolder} class="rounded bg-accent px-2 py-1 text-xs text-white">Add</button>
            </div>
          {/if}

          {#each unfolderedPlaylists as pl (pl.id)}
            {@render playlistItem(pl, false)}
          {/each}
        </div>
      </div>
    </nav>
  {/if}
</aside>
