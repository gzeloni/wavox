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

    <div class="page-head">
      <h1>Admin Panel <span class="admin-badge">Admin</span></h1>
      <p class="sub">Server-wide analytics and controls for guilds you administer.</p>
    </div>

    <GuildSelector
      guilds={adminGuilds}
      selectedId={selectedId}
      onSelect={select}
      label="Administered Servers"
    />

    {#if error}
      <div class="card empty-state">{error}</div>
    {:else if !selectedId}
      <div class="card empty-state">Select a server to view its stats.</div>
    {:else if loading}
      <div class="card empty-state">Loading overview...</div>
    {:else if !overview}
      <div class="card empty-state">No data available for this server yet.</div>
    {:else}
      <div class="overview-grid">
        <div class="stat-tile">
          <div class="stat-label">Guild</div>
          <div class="stat-value-text">{overview.guild_name ?? '-'}</div>
        </div>
        <div class="stat-tile">
          <div class="stat-label">Members</div>
          <div class="stat-value">{overview.member_count ?? '-'}</div>
        </div>
        <div class="stat-tile">
          <div class="stat-label">Voice</div>
          <div class="stat-value-text">
            {#if overview.voice_connected}
              <span class="green">● {overview.voice_channel ?? 'Connected'}</span>
            {:else}
              <span class="muted">Disconnected</span>
            {/if}
          </div>
        </div>
        <div class="stat-tile">
          <div class="stat-label">Queue</div>
          <div class="stat-value">{overview.queue_size}</div>
        </div>
      </div>

      <div class="panels">
        <div class="card">
          <div class="card-head">
            <h2>Top Tracks</h2>
          </div>
          {#if overview.top_tracks.length === 0}
            <div class="empty-state">No plays yet.</div>
          {:else}
            <ul class="list">
              {#each overview.top_tracks as t, i}
                <li>
                  <span class="pos">{i + 1}.</span>
                  <span class="title">{t.title}</span>
                  <span class="count">{t.plays}x</span>
                </li>
              {/each}
            </ul>
          {/if}
        </div>

        <div class="card">
          <div class="card-head">
            <h2>Most Active</h2>
          </div>
          {#if overview.most_active.length === 0}
            <div class="empty-state">No users tracked.</div>
          {:else}
            <ul class="list">
              {#each overview.most_active as u, i}
                <li>
                  <span class="pos">{i + 1}.</span>
                  <span class="title">
                    {#if u.user_id}
                      <a
                        href={`https://discord.com/users/${u.user_id}`}
                        target="_blank"
                        rel="noopener noreferrer">@{u.user_id}</a
                      >
                    {:else}
                      Unknown
                    {/if}
                  </span>
                  <span class="count">{u.plays}x</span>
                </li>
              {/each}
            </ul>
          {/if}
        </div>

        <div class="card full">
          <div class="card-head">
            <h2>Recent Plays</h2>
            <button class="btn btn-ghost btn-sm" on:click={refresh}>Refresh</button>
          </div>
          {#if overview.recent.length === 0}
            <div class="empty-state">No recent plays.</div>
          {:else}
            <ul class="list">
              {#each overview.recent as r, i (i)}
                <li>
                  <span class="title">{r.title}</span>
                  <span class="count">{r.played_at.slice(0, 16).replace('T', ' ')}</span>
                </li>
              {/each}
            </ul>
          {/if}
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .page-head {
    margin-bottom: 24px;
  }
  .page-head h1 {
    font-size: 1.5rem;
    font-weight: 700;
  }
  .sub {
    color: var(--text-muted);
    font-size: 13px;
    margin-top: 6px;
  }
  .overview-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 20px;
  }
  .stat-tile {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
  }
  .stat-label {
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }
  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary);
  }
  .stat-value-text {
    font-size: 0.95rem;
    font-weight: 600;
  }
  .green {
    color: var(--green);
  }
  .muted {
    color: var(--text-muted);
  }
  .panels {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .panels .full {
    grid-column: 1 / -1;
  }
  .card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .card-head h2 {
    font-size: 0.9rem;
    font-weight: 600;
  }
  .list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .list li {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    font-size: 13px;
  }
  .list li:hover {
    background: var(--surface2);
  }
  .pos {
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
    min-width: 22px;
  }
  .title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .count {
    color: var(--text-muted);
    font-size: 12px;
  }
  @media (max-width: 768px) {
    .overview-grid {
      grid-template-columns: repeat(2, 1fr);
    }
    .panels {
      grid-template-columns: 1fr;
    }
  }
</style>
