<script lang="ts">
  import { page } from '$app/stores';
  import { session } from '$lib/stores/session';
  import { avatarUrl } from '$lib/utils';

  export let onAvatarClick: (() => void) | null = null;

  $: me = $session.me;
  $: hasAdmin = (me?.guilds ?? []).some((g) => g.is_admin);
  $: avatar = me ? avatarUrl(me.user_id, me.avatar, 64) : null;
  $: path = $page.url.pathname;
</script>

<div class="header">
  <div class="brand">W<span>avox</span></div>

  {#if me}
    <nav class="header-nav">
      <a href="/app" class="nav-link" class:active={path.startsWith('/app')}>Dashboard</a>
      {#if hasAdmin}
        <a href="/admin" class="nav-link" class:active={path.startsWith('/admin')}>
          Admin
        </a>
      {/if}
    </nav>

    <div class="user-info">
      {#if avatar}
        <img
          class="user-avatar"
          src={avatar}
          alt=""
          title="View your stats"
          on:click={() => onAvatarClick?.()}
        />
      {/if}
      <span class="user-name">{me.username}</span>
      <a href="/dashboard/logout" class="btn btn-ghost btn-sm" data-sveltekit-reload>Logout</a>
    </div>
  {/if}
</div>
