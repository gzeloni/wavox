<script lang="ts">
  import { onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { session } from '$lib/stores/session';
  import { guildId, state, selectGuild, disconnectGuild } from '$lib/stores/player';
  import AppHeader from '$lib/components/AppHeader.svelte';
  import GuildSelector from '$lib/components/GuildSelector.svelte';
  import SearchBar from '$lib/components/SearchBar.svelte';
  import Player from '$lib/components/Player.svelte';
  import Queue from '$lib/components/Queue.svelte';
  import Lyrics from '$lib/components/Lyrics.svelte';
  import ProfileModal from '$lib/components/ProfileModal.svelte';

  let profileOpen = false;

  $: if (!$session.loading && !$session.me) goto('/');
  $: selectedGuild = $session.me?.guilds.find((guild) => guild.id === $guildId) ?? null;
  $: playbackState = $state?.is_playing ? 'Playing' : $state?.is_paused ? 'Paused' : 'Idle';
  $: queueSize = $state?.queue?.length ?? 0;
  $: loopMode = $state?.loop_mode ?? 'off';

  onDestroy(() => {
    disconnectGuild();
  });
</script>

<svelte:head>
  <title>Wavox — Dashboard</title>
</svelte:head>

{#if $session.me}
  <div class="shell">
    <AppHeader onAvatarClick={() => (profileOpen = true)} />

    <div class="page">
      <section class="workspace-banner">
        <div class="workspace-banner-main">
          <div class="eyebrow">Playback Workspace</div>
          <h1 class="page-title">Guild transport, queue, and lyrics.</h1>
          <p class="page-subtitle">
            The browser reflects backend state. Use this screen to control the active session and
            inspect what is happening now.
          </p>
        </div>

        <div class="workspace-pills">
          <span class="status-chip">
            <span class="status-chip-label">Guild</span>
            <strong>{selectedGuild?.name ?? 'None selected'}</strong>
          </span>
          <span class="status-chip">
            <span class="status-chip-label">State</span>
            <strong>{playbackState}</strong>
          </span>
          <span class="status-chip">
            <span class="status-chip-label">Queue</span>
            <strong>{queueSize}</strong>
          </span>
          <span class="status-chip">
            <span class="status-chip-label">Loop</span>
            <strong>{loopMode}</strong>
          </span>
        </div>
      </section>

      <GuildSelector
        guilds={$session.me.guilds}
        selectedId={$guildId}
        onSelect={selectGuild}
        label="Active Guilds"
      />

      {#if $guildId}
        <SearchBar />

        <section class="workspace-grid">
          <div class="workspace-player">
            <Player />
          </div>
          <aside class="workspace-queue">
            <Queue />
          </aside>
          <div class="workspace-lyrics">
            <Lyrics />
          </div>
        </section>
      {:else}
        <div class="card empty-state">
          Select an active guild to load the playback workspace.
        </div>
      {/if}
    </div>
  </div>

  <ProfileModal open={profileOpen} onClose={() => (profileOpen = false)} />
{/if}

<style>
  .workspace-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.75fr);
    grid-template-areas:
      'player queue'
      'lyrics lyrics';
    gap: 14px;
  }

  .workspace-player {
    grid-area: player;
    min-width: 0;
  }

  .workspace-queue {
    grid-area: queue;
    min-width: 0;
  }

  .workspace-lyrics {
    grid-area: lyrics;
    min-width: 0;
  }

  .workspace-banner {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 14px;
    align-items: start;
  }

  .workspace-pills {
    display: flex;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 8px;
  }

  .status-chip {
    min-width: 104px;
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--surface2);
    display: grid;
    gap: 5px;
  }

  .status-chip-label {
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .status-chip strong {
    font-size: 13px;
    font-weight: 650;
    color: var(--text);
  }

  @media (max-width: 1100px) {
    .workspace-banner {
      grid-template-columns: 1fr;
    }

    .workspace-pills {
      justify-content: flex-start;
    }

    .workspace-grid {
      grid-template-columns: 1fr;
      grid-template-areas:
        'player'
        'queue'
        'lyrics';
    }
  }

  @media (max-width: 640px) {
    .workspace-pills {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
</style>
