<script lang="ts">
  import { api } from '$lib/api';
  import { guildId } from '$lib/stores/player';
  import { session } from '$lib/stores/session';
  import { avatarUrl } from '$lib/utils';
  import type { UserStats } from '$lib/types';

  export let open = false;
  export let onClose: () => void;

  let loading = false;
  let data: UserStats | null = null;
  let message = '';

  $: if (open) load();

  async function load() {
    const id = $guildId;
    data = null;
    message = '';
    if (!id) {
      message = 'Select a server first to see your stats.';
      return;
    }
    loading = true;
    try {
      const result = await api.userStatus(id);
      if (!result || !(result as UserStats).total_plays) {
        message = 'No listening data in the last 30 days.';
      } else {
        data = result as UserStats;
      }
    } catch {
      message = 'Failed to load stats.';
    }
    loading = false;
  }

  function backdrop(e: MouseEvent) {
    if (e.target === e.currentTarget) onClose();
  }

  function backdropKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }

  $: avatar = $session.me ? avatarUrl($session.me.user_id, $session.me.avatar, 128) : null;
  const HOUR_LABELS = ['00 - 06', '06 - 12', '12 - 18', '18 - 24'];
</script>

{#if open}
  <div class="modal-overlay" on:click={backdrop} on:keydown={backdropKeydown} tabindex="-1">
    <div class="modal" role="dialog" aria-modal="true" tabindex="-1">
      <button class="modal-close" on:click={onClose} aria-label="Close">&times;</button>
      {#if avatar}
        <img class="modal-avatar" src={avatar} alt="" />
      {/if}
      <div class="modal-username">{$session.me?.username ?? ''}</div>
      <div class="modal-sub">Last 30 days</div>

      {#if loading}
        <div class="modal-empty">Loading stats...</div>
      {:else if message}
        <div class="modal-empty">{message}</div>
      {:else if data}
        <div class="stat-grid">
          <div class="stat-box"><div class="stat-value">{data.total_plays}</div><div class="stat-label">Plays</div></div>
          <div class="stat-box"><div class="stat-value">{data.total_skips}</div><div class="stat-label">Skips</div></div>
          <div class="stat-box"><div class="stat-value">{data.total_likes}</div><div class="stat-label">Likes</div></div>
        </div>
        <div class="rate-grid">
          <div class="rate-box"><div class="rate-value">{data.skip_rate}%</div><div class="rate-label">Skip Rate</div></div>
          <div class="rate-box"><div class="rate-value">{data.like_rate}%</div><div class="rate-label">Like Rate</div></div>
          <div class="rate-box"><div class="rate-value">{data.repeat_rate}%</div><div class="rate-label">Repeat Rate</div></div>
        </div>

        {#if data.top_tracks?.length}
          <div class="modal-section">
            <h3>Top Tracks</h3>
            <ul class="modal-list">
              {#each data.top_tracks as t, i}
                <li><span><span class="pos">{i + 1}.</span> {t.title}</span><span class="count">{t.plays}x</span></li>
              {/each}
            </ul>
          </div>
        {/if}

        {#if data.top_artists?.length}
          <div class="modal-section">
            <h3>Top Artists</h3>
            <ul class="modal-list">
              {#each data.top_artists as a, i}
                <li><span><span class="pos">{i + 1}.</span> {a.artist}</span><span class="count">{a.plays}x</span></li>
              {/each}
            </ul>
          </div>
        {/if}

        {#if data.hour_blocks}
          {@const total = data.hour_blocks.reduce((a, b) => a + b, 0) || 1}
          <div class="modal-section">
            <h3>Listening Hours</h3>
            {#each data.hour_blocks as count, i}
              {@const pct = Math.round((count / total) * 100)}
              <div class="hour-row">
                <span class="hour-label">{HOUR_LABELS[i]}</span>
                <div class="hour-bar-bg"><div class="hour-bar-fill" style="width:{pct}%"></div></div>
                <span class="hour-pct">{pct}%</span>
              </div>
            {/each}
          </div>
        {/if}
      {/if}
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(3, 4, 10, 0.82);
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .modal {
    background: var(--surface);
    border-radius: 10px;
    border: 1px solid var(--border);
    padding: 20px;
    max-width: 480px;
    width: 90%;
    max-height: 85vh;
    overflow-y: auto;
    position: relative;
  }
  .modal-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    background: rgba(255, 255, 255, 0.04);
    color: var(--text-muted);
    cursor: pointer;
    font-size: 18px;
    transition: all 0.2s;
  }
  .modal-close:hover {
    background: rgba(255, 255, 255, 0.08);
    color: var(--text);
  }
  .modal-avatar {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    border: 1px solid var(--border);
    margin: 0 auto 12px;
    display: block;
  }
  .modal-username {
    text-align: center;
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 4px;
  }
  .modal-sub {
    text-align: center;
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 24px;
  }
  .stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 24px;
  }
  .stat-box {
    background: var(--surface2);
    border: 1px solid rgba(96, 121, 197, 0.14);
    border-radius: 8px;
    padding: 14px;
    text-align: center;
  }
  .stat-value {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--primary);
  }
  .stat-label {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 4px;
  }
  .rate-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 24px;
  }
  .rate-box {
    text-align: center;
  }
  .rate-value {
    font-size: 1.1rem;
    font-weight: 600;
  }
  .rate-label {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 2px;
  }
  .modal-section {
    margin-bottom: 20px;
  }
  .modal-section h3 {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .modal-list {
    list-style: none;
  }
  .modal-list li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    border-radius: 8px;
    font-size: 13px;
  }
  .modal-list li:hover {
    background: rgba(255, 255, 255, 0.03);
  }
  .pos {
    color: var(--text-muted);
    margin-right: 10px;
    min-width: 18px;
    font-variant-numeric: tabular-nums;
    display: inline-block;
  }
  .count {
    color: var(--text-muted);
    font-size: 12px;
  }
  .hour-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 0;
    font-size: 13px;
  }
  .hour-label {
    min-width: 70px;
    color: var(--text-muted);
  }
  .hour-bar-bg {
    flex: 1;
    height: 8px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 4px;
    overflow: hidden;
  }
  .hour-bar-fill {
    height: 100%;
    background: var(--primary);
    border-radius: 4px;
    transition: width 0.3s;
  }
  .hour-pct {
    min-width: 36px;
    text-align: right;
    font-size: 12px;
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
  }
  .modal-empty {
    text-align: center;
    padding: 24px;
    color: var(--text-muted);
    font-size: 13px;
  }
</style>
