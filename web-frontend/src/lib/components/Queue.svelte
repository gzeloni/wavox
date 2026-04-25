<script lang="ts">
  import { state, guildId } from '$lib/stores/player';
  import { api } from '$lib/api';
  import { fmtTime } from '$lib/utils';

  $: q = $state?.queue ?? [];

  async function skipTo(position: number) {
    const id = $guildId;
    if (!id) return;
    await api.playback(id, 'skip_to', { position });
  }

  async function clearQueue() {
    const id = $guildId;
    if (!id) return;
    await api.playback(id, 'clear');
  }
</script>

<div class="queue-card card">
  <div class="queue-header">
    <h2>Queue</h2>
    <div class="queue-actions">
      {#if q.length > 0}
        <span class="queue-count">{q.length} track{q.length > 1 ? 's' : ''}</span>
        <button class="queue-clear-btn" on:click={clearQueue}>Clear</button>
      {/if}
    </div>
  </div>

  {#if q.length === 0}
    <div class="queue-empty">Queue is empty</div>
  {:else}
    <ul class="queue-list">
      {#each q as t, i (i)}
        <li class="queue-item">
          <span class="queue-pos">{i + 1}</span>
          <button class="queue-play-btn" title="Play now" on:click={() => skipTo(i + 1)} aria-label="Play">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
          </button>
          <span class="queue-title">{t.title ?? 'Unknown'}</span>
          <span class="queue-dur">{fmtTime(t.duration)}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .queue-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }
  .queue-header h2 {
    font-size: 0.9rem;
    font-weight: 600;
  }
  .queue-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .queue-count {
    color: var(--text-muted);
    font-size: 12px;
  }
  .queue-clear-btn {
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-muted);
    font-size: 11px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .queue-clear-btn:hover {
    border-color: var(--red);
    color: var(--red);
  }
  .queue-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .queue-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 10px;
    transition: background 0.15s;
    position: relative;
  }
  .queue-item:hover {
    background: var(--surface2);
  }
  .queue-pos {
    color: var(--text-muted);
    font-size: 12px;
    min-width: 22px;
    text-align: right;
    font-variant-numeric: tabular-nums;
    transition: opacity 0.15s;
  }
  .queue-play-btn {
    display: none;
    position: absolute;
    left: 12px;
    width: 22px;
    height: 22px;
    border: none;
    border-radius: 50%;
    background: var(--primary);
    color: #fff;
    cursor: pointer;
    align-items: center;
    justify-content: center;
    padding: 0;
    transition: transform 0.1s;
  }
  .queue-play-btn :global(svg) {
    width: 10px;
    height: 10px;
  }
  .queue-play-btn:hover {
    transform: scale(1.15);
  }
  .queue-item:hover .queue-pos {
    opacity: 0;
  }
  .queue-item:hover .queue-play-btn {
    display: flex;
  }
  .queue-title {
    flex: 1;
    font-size: 13px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .queue-dur {
    color: var(--text-muted);
    font-size: 12px;
    font-variant-numeric: tabular-nums;
  }
  .queue-empty {
    text-align: center;
    padding: 24px;
    color: var(--text-muted);
    font-size: 13px;
  }
</style>
