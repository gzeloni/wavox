<script lang="ts">
  import AppHeader from '$lib/components/AppHeader.svelte';
  import OperatorPreview from '$lib/components/OperatorPreview.svelte';
  import { session } from '$lib/stores/session';

  $: loading = $session.loading;
  $: me = $session.me;
</script>

<svelte:head>
  <title>Wavox</title>
</svelte:head>

<div class="shell">
  <AppHeader />

  <div class="page page-home">
    <section class="entry-grid">
      <div class="entry-copy">
        <div class="eyebrow">Console</div>
        <h1 class="page-title page-title-home">Discord playback control, queue, and lyrics.</h1>
        <p class="entry-text">
          Wavox exposes the active player state through a single browser-facing runtime. Sign in to
          operate a guild session or inspect the system documentation.
        </p>

        {#if loading}
          <div class="entry-actions">
            <span class="btn btn-subtle">Loading session...</span>
          </div>
        {:else if me}
          <div class="entry-actions">
            <a href="/app" class="btn btn-primary">Open Dashboard</a>
            {#if me.guilds.some((g) => g.is_admin)}
              <a href="/admin" class="btn btn-ghost">Open Admin Panel</a>
            {/if}
          </div>
        {:else}
          <div class="entry-actions">
            <a href="/login" class="btn btn-primary" data-sveltekit-reload>
              Sign in with Discord
            </a>
            <a href="/docs/invite" class="btn btn-ghost">Invite Guide</a>
          </div>
        {/if}
      </div>

      <OperatorPreview />
    </section>

    <section class="section-card home-reference">
      <div class="section-head">
        <div>
          <h2>Available Surfaces</h2>
          <p>Use the app for control. Use docs for setup and reference.</p>
        </div>
      </div>
      <div class="home-reference-grid">
        <ul class="data-list">
          <li><a class="data-list-key" href="/app">Dashboard workspace</a></li>
          <li><a class="data-list-key" href="/admin">Admin overview</a></li>
        </ul>
        <ul class="data-list">
          <li><a class="data-list-key" href="/docs">System overview</a></li>
          <li><a class="data-list-key" href="/docs/invite">Invite guide</a></li>
          <li><a class="data-list-key" href="/docs/privacy">Privacy and terms</a></li>
        </ul>
      </div>
    </section>
  </div>
</div>

<style>
  .home-reference-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }

  @media (max-width: 768px) {
    .home-reference-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
