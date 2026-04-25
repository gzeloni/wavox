<script lang="ts">
  import { session } from '$lib/stores/session';

  $: loading = $session.loading;
  $: me = $session.me;
</script>

<svelte:head>
  <title>Wavox</title>
</svelte:head>

<div class="landing">
  <div class="logo">W<span>avox</span></div>
  <p class="tagline">A powerful Discord music bot — YouTube, SoundCloud, Spotify.</p>

  {#if loading}
    <div class="muted">Loading...</div>
  {:else if me}
    <div class="cta-row">
      <a href="/app" class="btn btn-primary">Open Dashboard</a>
      {#if me.guilds.some((g) => g.is_admin)}
        <a href="/admin" class="btn btn-ghost">Admin Panel</a>
      {/if}
    </div>
  {:else}
    <a href="/dashboard/login" class="btn btn-primary" data-sveltekit-reload>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.36-.698.772-1.362 1.225-1.993a.076.076 0 0 0-.041-.107 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.125-.093.25-.19.372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>
      Sign in with Discord
    </a>
  {/if}

  <div class="links">
    <a href="/docs/">Docs</a>
    <a href="/docs/invite/">Invite</a>
    <a href="/docs/terms/">Terms</a>
    <a href="/docs/privacy/">Privacy</a>
  </div>
</div>

<style>
  .landing {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    gap: 20px;
    padding: 20px;
  }
  .logo {
    font-size: 3rem;
    font-weight: 700;
    letter-spacing: -1px;
  }
  .logo span {
    color: var(--primary);
  }
  .tagline {
    color: var(--text-muted);
    font-size: 15px;
    text-align: center;
    max-width: 420px;
  }
  .cta-row {
    display: flex;
    gap: 12px;
  }
  .muted {
    color: var(--text-muted);
    font-size: 13px;
  }
  .links {
    display: flex;
    gap: 16px;
    margin-top: 24px;
    font-size: 13px;
  }
  .links a {
    color: var(--text-muted);
  }
  .links a:hover {
    color: var(--primary);
  }
</style>
