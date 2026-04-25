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
    <div>
      <div class="queue-kicker">Queue</div>
      <h2>Up Next</h2>
    </div>
    {#if q.length > 0}
      <button class="queue-clear-btn" on:click={clearQueue}>Clear</button>
    {/if}
  </div>

  {#if q.length === 0}
    <div class="queue-empty">No queued tracks.</div>
  {:else}
    <ul class="queue-list">
      {#each q as t, i (i)}
        <li class="queue-item">
          <span class="queue-pos">{String(i + 1).padStart(2, '0')}</span>
          <button class="queue-play-btn" title="Play now" on:click={() => skipTo(i + 1)} aria-label="Play">
            Play
          </button>
          <span class="queue-title">{t.title ?? 'Unknown'}</span>
          <span class="queue-dur">{fmtTime(t.duration)}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .queue-card {
    display: grid;
    gap: 14px;
    padding: 16px;
    height: 100%;
  }

  .queue-header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 12px;
  }

  .queue-kicker {
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .queue-header h2 {
    margin-top: 4px;
    font-size: 15px;
  }

  .queue-clear-btn,
  .queue-play-btn {
    min-height: 30px;
    padding: 0 10px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: transparent;
    color: var(--text-muted);
    font-size: 12px;
    cursor: pointer;
  }

  .queue-clear-btn:hover,
  .queue-play-btn:hover {
    background: rgba(255, 255, 255, 0.03);
    color: var(--text);
  }

  .queue-list {
    list-style: none;
    display: grid;
    gap: 0;
  }

  .queue-item {
    display: grid;
    grid-template-columns: auto auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(96, 121, 197, 0.14);
  }

  .queue-item:last-child {
    border-bottom: 0;
  }

  .queue-pos,
  .queue-dur {
    color: var(--text-muted);
    font-size: 11px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .queue-title {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 13px;
  }

  .queue-empty {
    color: var(--text-muted);
    font-size: 13px;
  }

  @media (max-width: 640px) {
    .queue-item {
      grid-template-columns: auto auto 1fr;
      grid-template-areas:
        'pos action dur'
        'title title title';
    }

    .queue-pos {
      grid-area: pos;
    }

    .queue-play-btn {
      grid-area: action;
    }

    .queue-title {
      grid-area: title;
      white-space: normal;
    }

    .queue-dur {
      grid-area: dur;
      justify-self: end;
    }
  }
</style>
