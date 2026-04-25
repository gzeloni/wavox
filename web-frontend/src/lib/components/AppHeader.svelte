<script lang="ts">
  import { page } from '$app/stores';
  import { session } from '$lib/stores/session';
  import { avatarUrl } from '$lib/utils';

  export let onAvatarClick: (() => void) | null = null;
  export let showAuth = true;
  export let showDocs = true;
  export let showDashboard = true;
  export let compact = false;

  $: me = $session.me;
  $: hasAdmin = (me?.guilds ?? []).some((g) => g.is_admin);
  $: avatar = me ? avatarUrl(me.user_id, me.avatar, 64) : null;
  $: path = $page.url.pathname;
  $: dashboardVisible = showDashboard && Boolean(me);
</script>

<div class="header" class:compact>
  <a href="/" class="brand" aria-label="Wavox home">
    <img class="brand-icon" src="/wavox.png" alt="" />
    <strong class="brand-name">Wavox</strong>
  </a>

  <nav class="header-nav">
    <a href="/" class="nav-link" class:active={path === '/'}>Home</a>
    {#if dashboardVisible}
      <a href="/app" class="nav-link" class:active={path.startsWith('/app')}>Dashboard</a>
    {/if}
    {#if me && hasAdmin}
      <a href="/admin" class="nav-link" class:active={path.startsWith('/admin')}>
        Admin
      </a>
    {/if}
    {#if showDocs}
      <a href="/docs" class="nav-link" class:active={path.startsWith('/docs')}>Docs</a>
    {/if}
  </nav>

  {#if showAuth}
    <div class="user-info">
      {#if me}
        {#if avatar}
          <button type="button" class="avatar-button" title="View your stats" on:click={() => onAvatarClick?.()}>
            <img
              class="user-avatar"
              src={avatar}
              alt=""
            />
          </button>
        {/if}
        <span class="user-name">{me.username}</span>
        <a href="/logout" class="btn btn-ghost btn-sm" data-sveltekit-reload>Logout</a>
      {:else}
        <a href="/login" class="btn btn-primary btn-sm" data-sveltekit-reload>
          Sign in
        </a>
      {/if}
    </div>
  {/if}
</div>

<style>
  .compact {
    margin-bottom: 20px;
  }

  .avatar-button {
    padding: 0;
    border: 0;
    background: transparent;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
</style>
