<script lang="ts">
  import { onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { session } from '$lib/stores/session';
  import { guildId, selectGuild, disconnectGuild } from '$lib/stores/player';
  import AppHeader from '$lib/components/AppHeader.svelte';
  import GuildSelector from '$lib/components/GuildSelector.svelte';
  import SearchBar from '$lib/components/SearchBar.svelte';
  import Player from '$lib/components/Player.svelte';
  import Queue from '$lib/components/Queue.svelte';
  import Lyrics from '$lib/components/Lyrics.svelte';
  import ProfileModal from '$lib/components/ProfileModal.svelte';

  let profileOpen = false;

  $: if (!$session.loading && !$session.me) goto('/');

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

    <GuildSelector
      guilds={$session.me.guilds}
      selectedId={$guildId}
      onSelect={selectGuild}
    />

    {#if $guildId}
      <SearchBar />
      <div class="main-layout">
        <div class="main-left">
          <Player />
          <Queue />
        </div>
        <div class="main-right">
          <Lyrics />
        </div>
      </div>
    {:else}
      <div class="card empty-state">Select a server above to see playback.</div>
    {/if}
  </div>

  <ProfileModal open={profileOpen} onClose={() => (profileOpen = false)} />
{/if}

<style>
  .main-layout {
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 20px;
  }
  .main-left,
  .main-right {
    min-width: 0;
  }
  @media (max-width: 768px) {
    .main-layout {
      grid-template-columns: 1fr;
    }
  }
</style>
