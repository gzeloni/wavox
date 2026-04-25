<script lang="ts">
  import { state, elapsed, guildId } from '$lib/stores/player';
  import { api } from '$lib/api';
  import { fmtTime } from '$lib/utils';
  import type { PlaybackAction } from '$lib/types';

  const loopLabels: Record<string, string> = { off: '', track: 'Looping track', queue: 'Looping queue' };

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

  $: np = $state?.now_playing ?? null;
  $: dur = np?.duration ?? 0;
  $: clamped = Math.min($elapsed, dur);
  $: pct = dur > 0 ? Math.min((clamped / dur) * 100, 100) : 0;
  $: loopMode = $state?.loop_mode ?? 'off';
</script>

<div class="player-card card">
  {#if !np}
    <div class="empty-state">Nothing playing right now.</div>
  {:else}
    <div class="track-info">
      {#if np.thumbnail}
        <img class="track-thumb" src={np.thumbnail} alt="" />
      {/if}
      <div class="track-details">
        <div class="track-title">{np.title ?? '-'}</div>
        <div class="track-status">
          <div
            class="status-dot"
            class:playing={$state?.is_playing}
            class:paused={$state?.is_paused}
          />
          <span>
            {#if $state?.is_playing}
              Playing
            {:else if $state?.is_paused}
              Paused
            {:else}
              Stopped
            {/if}
          </span>
        </div>
      </div>
    </div>

    <div class="progress">
      <div class="progress-bar" on:click={seek} role="slider" tabindex="0" aria-valuenow={clamped}>
        <div class="progress-fill" style="width:{pct}%"></div>
      </div>
      <div class="progress-times">
        <span>{fmtTime(clamped)}</span>
        <span>{fmtTime(dur)}</span>
      </div>
    </div>

    <div class="controls">
      <button class="ctrl-btn" title="Shuffle" on:click={() => send('shuffle')} aria-label="Shuffle">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
      </button>
      <button class="ctrl-btn" title="Previous" on:click={() => send('previous')} aria-label="Previous">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
      </button>
      <button class="ctrl-btn main" title="Play/Pause" on:click={togglePlay} aria-label="Play/Pause">
        {#if $state?.is_playing}
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6zm8 0h4v16h-4z"/></svg>
        {:else}
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        {/if}
      </button>
      <button class="ctrl-btn" title="Skip" on:click={() => send('skip')} aria-label="Skip">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
      </button>
      <button class="ctrl-btn" class:active={loopMode !== 'off'} title="Loop" on:click={() => send('loop')} aria-label="Loop">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
      </button>
      <button class="ctrl-btn danger" title="Stop & Disconnect" on:click={() => send('stop')} aria-label="Stop">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
      </button>
    </div>
    <div class="loop-label">{loopLabels[loopMode] ?? ''}</div>
  {/if}
</div>

<style>
  .player-card {
    padding: 28px;
    margin-bottom: 20px;
  }
  .track-info {
    display: flex;
    gap: 20px;
    margin-bottom: 24px;
  }
  .track-thumb {
    width: 100px;
    height: 100px;
    border-radius: 12px;
    object-fit: cover;
    background: var(--surface2);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  }
  .track-details {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 6px;
    min-width: 0;
  }
  .track-title {
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.4;
  }
  .track-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--text-muted);
  }
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--text-muted);
  }
  .status-dot.playing {
    background: var(--green);
  }
  .status-dot.paused {
    background: var(--red);
  }
  .progress {
    margin-bottom: 24px;
  }
  .progress-bar {
    width: 100%;
    height: 5px;
    background: var(--surface2);
    border-radius: 3px;
    overflow: hidden;
    cursor: pointer;
    transition: height 0.15s;
  }
  .progress-bar:hover {
    height: 8px;
  }
  .progress-fill {
    height: 100%;
    background: var(--primary);
    border-radius: 3px;
    transition: width 0.3s linear;
  }
  .progress-times {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 11px;
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
  }
  .controls {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
  }
  .ctrl-btn {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: none;
    background: var(--surface2);
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
  }
  .ctrl-btn:hover {
    background: var(--border);
    color: var(--text);
  }
  .ctrl-btn.active {
    background: var(--primary);
    color: #fff;
  }
  .ctrl-btn.main {
    width: 48px;
    height: 48px;
    background: var(--primary);
    color: #fff;
  }
  .ctrl-btn.main:hover {
    background: var(--primary-hover);
    transform: scale(1.05);
  }
  .ctrl-btn.danger:hover {
    background: var(--red);
    color: #fff;
  }
  .loop-label {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 8px;
    text-align: center;
    min-height: 16px;
  }
</style>
