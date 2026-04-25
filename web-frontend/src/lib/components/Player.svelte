<script lang="ts">
  import { state, elapsed, guildId } from '$lib/stores/player';
  import { api } from '$lib/api';
  import { fmtTime } from '$lib/utils';
  import type { PlaybackAction } from '$lib/types';

  const loopLabels: Record<string, string> = {
    off: 'Off',
    track: 'Track',
    queue: 'Queue'
  };

  async function send(action: PlaybackAction, extra: Record<string, unknown> = {}) {
    const id = $guildId;
    if (!id) return;
    try {
      await api.playback(id, action, extra);
    } catch {
      /* ignore */
    }
  }

  function togglePlay() {
    if (!$state) return;
    send($state.is_playing ? 'pause' : 'resume');
  }

  function seek(e: MouseEvent) {
    if (!$state?.now_playing?.duration) return;
    const target = e.currentTarget as HTMLDivElement;
    const rect = target.getBoundingClientRect();
    const pos = Math.floor(((e.clientX - rect.left) / rect.width) * $state.now_playing.duration);
    send('goto', { position: pos });
  }

  function seekWithKeyboard(e: KeyboardEvent) {
    if (!$state?.now_playing?.duration) return;
    const current = clamped;
    const step = 5;
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      send('goto', { position: Math.max(current - step, 0) });
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      send('goto', { position: Math.min(current + step, dur) });
    }
  }

  let sourceHost = '';

  $: np = $state?.now_playing ?? null;
  $: dur = np?.duration ?? 0;
  $: clamped = Math.min($elapsed, dur);
  $: pct = dur > 0 ? Math.min((clamped / dur) * 100, 100) : 0;
  $: loopMode = $state?.loop_mode ?? 'off';
  $: queueDepth = $state?.queue?.length ?? 0;
  $: if (np?.webpage_url) {
    try {
      sourceHost = new URL(np.webpage_url).hostname.replace(/^www\./, '');
    } catch {
      sourceHost = '';
    }
  } else {
    sourceHost = '';
  }
</script>

<div class="player-card card">
  {#if !np}
    <div class="empty-state">Nothing playing right now.</div>
  {:else}
    <div class="player-head">
      <div class="player-copy">
        <div class="player-kicker">Now Playing</div>
        <h2 class="player-title">{np.title ?? '-'}</h2>
        <div class="player-meta">
          <span>{sourceHost || 'source unavailable'}</span>
          <span>{queueDepth} queued</span>
          <span>Loop {loopLabels[loopMode]}</span>
        </div>
      </div>
      {#if np.thumbnail}
        <img class="track-thumb" src={np.thumbnail} alt="" />
      {/if}
    </div>

    <div class="player-readout">
      <div class="readout-item">
        <span class="readout-label">State</span>
        <strong>
          {#if $state?.is_playing}
            Playing
          {:else if $state?.is_paused}
            Paused
          {:else}
            Idle
          {/if}
        </strong>
      </div>
      <div class="readout-item">
        <span class="readout-label">Elapsed</span>
        <strong>{fmtTime(clamped)}</strong>
      </div>
      <div class="readout-item">
        <span class="readout-label">Remaining</span>
        <strong>{fmtTime(Math.max(dur - clamped, 0))}</strong>
      </div>
    </div>

    <div class="progress-block">
      <div
        class="progress-bar"
        on:click={seek}
        on:keydown={seekWithKeyboard}
        role="slider"
        tabindex="0"
        aria-valuenow={clamped}
        aria-valuemin="0"
        aria-valuemax={dur}
      >
        <div class="progress-fill" style="width:{pct}%"></div>
      </div>
      <div class="progress-times">
        <span>{fmtTime(clamped)}</span>
        <span>{fmtTime(dur)}</span>
      </div>
    </div>

    <div class="controls">
      <button type="button" class="ctrl-btn" on:click={() => send('shuffle')} aria-label="Shuffle">Shf</button>
      <button type="button" class="ctrl-btn" on:click={() => send('previous')} aria-label="Previous">Prev</button>
      <button type="button" class="ctrl-btn main" on:click={togglePlay} aria-label="Play/Pause">
        {#if $state?.is_playing}Pause{:else}Play{/if}
      </button>
      <button type="button" class="ctrl-btn" on:click={() => send('skip')} aria-label="Skip">Next</button>
      <button type="button" class="ctrl-btn" class:active={loopMode !== 'off'} on:click={() => send('loop')} aria-label="Loop">Loop</button>
      <button type="button" class="ctrl-btn danger" on:click={() => send('stop')} aria-label="Stop">Stop</button>
    </div>
  {/if}
</div>

<style>
  .player-card {
    display: grid;
    gap: 16px;
    padding: 18px;
  }

  .player-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 16px;
    align-items: start;
  }

  .player-copy {
    min-width: 0;
  }

  .player-kicker,
  .readout-label {
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .player-title {
    margin-top: 6px;
    font-size: 1.15rem;
    line-height: 1.3;
    word-break: break-word;
  }

  .player-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 14px;
    margin-top: 8px;
    color: var(--text-muted);
    font-size: 12px;
  }

  .track-thumb {
    width: 96px;
    height: 96px;
    border-radius: 8px;
    object-fit: cover;
    border: 1px solid var(--border);
    background: var(--surface2);
  }

  .player-readout {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
  }

  .readout-item {
    display: grid;
    gap: 6px;
    padding: 12px;
    border: 1px solid rgba(96, 121, 197, 0.16);
    border-radius: 8px;
    background: var(--surface2);
  }

  .readout-item strong {
    font-size: 13px;
    line-height: 1.35;
    word-break: break-word;
  }

  .progress-block {
    display: grid;
    gap: 8px;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    overflow: hidden;
    cursor: pointer;
  }

  .progress-fill {
    height: 100%;
    background: var(--primary);
  }

  .progress-times {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    color: var(--text-muted);
    font-size: 11px;
    font-variant-numeric: tabular-nums;
  }

  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .ctrl-btn {
    min-width: 56px;
    min-height: 36px;
    padding: 0 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: transparent;
    color: var(--text);
    cursor: pointer;
  }

  .ctrl-btn:hover,
  .ctrl-btn.active {
    background: var(--surface2);
  }

  .ctrl-btn.main {
    background: var(--primary);
    border-color: var(--primary);
    color: #041018;
  }

  .ctrl-btn.main:hover {
    background: var(--primary-hover);
    border-color: var(--primary-hover);
  }

  .ctrl-btn.danger:hover {
    border-color: rgba(239, 68, 68, 0.45);
    color: #ffd6d6;
  }

  @media (max-width: 720px) {
    .player-head {
      grid-template-columns: 1fr;
    }

    .player-readout {
      grid-template-columns: 1fr;
    }

    .track-thumb {
      width: 80px;
      height: 80px;
    }

    .controls {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .ctrl-btn {
      width: 100%;
      min-width: 0;
    }
  }
</style>
