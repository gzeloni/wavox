<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { session } from '$lib/stores/session';
  import { api } from '$lib/api';
  import AppHeader from '$lib/components/AppHeader.svelte';
  import GuildSelector from '$lib/components/GuildSelector.svelte';
  import type { Guild, GuildOverview } from '$lib/types';

  let adminGuilds: Guild[] = [];
  let selectedId: string | null = null;
  let overview: GuildOverview | null = null;
  let loading = false;
  let error = '';

  $: if (!$session.loading && !$session.me) goto('/');
  $: if (!$session.loading && $session.me && !$session.me.guilds.some((g) => g.is_admin)) {
    goto('/app');
  }

  onMount(async () => {
    try {
      const res = await api.adminGuilds();
      adminGuilds = res.guilds;
      if (adminGuilds.length === 1) select(adminGuilds[0].id);
    } catch (e) {
      error = (e as Error).message;
    }
  });

  async function select(id: string) {
    selectedId = id;
    overview = null;
    loading = true;
    error = '';
    try {
      const data = await api.adminOverview(id);
      overview = (data as GuildOverview).guild_name !== undefined ? (data as GuildOverview) : null;
    } catch (e) {
      error = (e as Error).message;
    }
    loading = false;
  }

  async function refresh() {
    if (selectedId) await select(selectedId);
  }
</script>

<svelte:head>
  <title>Wavox — Admin</title>
</svelte:head>

{#if $session.me}
  <div class="shell">
    <AppHeader />

    <div class="page">
      <section class="workspace-banner">
        <div class="workspace-banner-main">
          <div class="eyebrow">Guild Operations</div>
          <h1 class="page-title">Admin visibility for the servers you manage.</h1>
          <p class="page-subtitle">
            Inspect playback posture, queue depth, recent activity, and top listeners without
            leaving the same product shell used by the player workspace.
          </p>
        </div>
      </section>

      <GuildSelector
        guilds={adminGuilds}
        selectedId={selectedId}
        onSelect={select}
        label="Administered Guilds"
      />

      {#if error}
        <div class="card empty-state">{error}</div>
      {:else if !selectedId}
        <div class="card empty-state">Select a guild to load its operational overview.</div>
      {:else if loading}
        <div class="card empty-state">Loading overview...</div>
      {:else if !overview}
        <div class="card empty-state">No data available for this guild yet.</div>
      {:else}
        <section class="admin-overview">
          <div class="admin-stat">
            <span class="admin-stat-label">Guild</span>
            <strong>{overview.guild_name ?? '-'}</strong>
          </div>
          <div class="admin-stat">
            <span class="admin-stat-label">Members</span>
            <strong>{overview.member_count ?? '-'}</strong>
          </div>
          <div class="admin-stat">
            <span class="admin-stat-label">Voice</span>
            <strong>{overview.voice_connected ? overview.voice_channel ?? 'Connected' : 'Disconnected'}</strong>
          </div>
          <div class="admin-stat">
            <span class="admin-stat-label">Queue</span>
            <strong>{overview.queue_size}</strong>
          </div>
        </section>

        <section class="content-grid">
          <div class="section-card">
            <div class="section-head">
              <div>
                <h2>Top Tracks</h2>
                <p>Most replayed titles in this guild.</p>
              </div>
            </div>
            {#if overview.top_tracks.length === 0}
              <div class="empty-state">No plays yet.</div>
            {:else}
              <ul class="data-list ranked">
                {#each overview.top_tracks as t, i}
                  <li>
                    <span class="pos">{String(i + 1).padStart(2, '0')}</span>
                    <span class="data-list-key">{t.title}</span>
                    <span class="data-list-meta">{t.plays}x</span>
                  </li>
                {/each}
              </ul>
            {/if}
          </div>

          <div class="section-card">
            <div class="section-head">
              <div>
                <h2>Most Active</h2>
                <p>Users with the highest tracked play count.</p>
              </div>
            </div>
            {#if overview.most_active.length === 0}
              <div class="empty-state">No users tracked.</div>
            {:else}
              <ul class="data-list ranked">
                {#each overview.most_active as u, i}
                  <li>
                    <span class="pos">{String(i + 1).padStart(2, '0')}</span>
                    <span class="data-list-key">
                      {#if u.user_id}
                        <a
                          href={`https://discord.com/users/${u.user_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          @{u.user_id}
                        </a>
                      {:else}
                        Unknown
                      {/if}
                    </span>
                    <span class="data-list-meta">{u.plays}x</span>
                  </li>
                {/each}
              </ul>
            {/if}
          </div>

          <div class="section-card full">
            <div class="section-head">
              <div>
                <h2>Recent Plays</h2>
                <p>Latest track activity captured for this guild.</p>
              </div>
              <button class="btn btn-ghost btn-sm" on:click={refresh}>Refresh</button>
            </div>
            {#if overview.recent.length === 0}
              <div class="empty-state">No recent plays.</div>
            {:else}
              <ul class="data-list recent-list">
                {#each overview.recent as r, i (i)}
                  <li>
                    <span class="data-list-key">{r.title}</span>
                    <span class="data-list-meta">{r.played_at.slice(0, 16).replace('T', ' ')}</span>
                  </li>
                {/each}
              </ul>
            {/if}
          </div>
        </section>
      {/if}
    </div>
  </div>
{/if}

<style>
  .admin-overview {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
  }

  .admin-stat {
    padding: 16px 18px;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.02);
    display: grid;
    gap: 8px;
  }

  .admin-stat-label {
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .admin-stat strong {
    font-size: 14px;
    line-height: 1.35;
  }

  .pos {
    width: 28px;
    color: var(--text-muted);
    font-size: 11px;
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 900px) {
    .admin-overview {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 560px) {
    .admin-overview {
      grid-template-columns: 1fr;
    }
  }
</style>
