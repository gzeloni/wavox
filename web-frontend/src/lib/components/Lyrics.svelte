<script lang="ts">
  import { onDestroy } from 'svelte';
  import { state, elapsed, lyrics } from '$lib/stores/player';
  import { parseLRC, type LRCLine } from '$lib/utils';
  import type { LyricsResponse } from '$lib/types';

  let lines: LRCLine[] = [];
  let plainLines: string[] = [];
  let meta = '';
  let statusMsg = 'Play a track to see synced lyrics.';
  let currentUrl: string | null = null;
  let currentLyricsKey = '';
  let container: HTMLDivElement;
  let activeIdx = -1;

  $: np = $state?.now_playing ?? null;
  $: handleTrackChange(np?.webpage_url ?? null, np?.title ?? null, $lyrics);
  $: updateActive($elapsed);

  function resetLyrics() {
    lines = [];
    plainLines = [];
    meta = '';
    activeIdx = -1;
  }

  function handleTrackChange(url: string | null, title: string | null, data: LyricsResponse | null) {
    const lyricsKey = `${url ?? ''}:${data?.title ?? ''}:${data?.artist ?? ''}:${data?.synced ? 'synced' : ''}:${data?.plain ? 'plain' : ''}`;
    if (url === currentUrl && lyricsKey === currentLyricsKey) return;
    currentUrl = url;
    currentLyricsKey = lyricsKey;
    resetLyrics();

    if (!title) {
      statusMsg = 'Play a track to see synced lyrics.';
      return;
    }

    if (!data) {
      statusMsg = 'Loading lyrics...';
      return;
    }

    if (data.synced) {
      lines = parseLRC(data.synced);
      statusMsg = '';
    } else if (data.plain) {
      plainLines = data.plain.split('\n').map((l) => l || '\u00A0');
      statusMsg = '';
    } else {
      statusMsg = 'No lyrics found for this track.';
    }
    if (data.artist || data.title) {
      meta = `${data.artist ?? ''} - ${data.title ?? ''}`;
    }
  }

  let scrollRAF: number | null = null;
  function updateActive(e: number) {
    if (lines.length === 0) return;
    let idx = -1;
    for (let i = lines.length - 1; i >= 0; i--) {
      if (e >= lines[i].time) {
        idx = i;
        break;
      }
    }
    if (idx !== activeIdx) {
      activeIdx = idx;
      if (scrollRAF) cancelAnimationFrame(scrollRAF);
      scrollRAF = requestAnimationFrame(() => {
        const el = container?.querySelector<HTMLDivElement>(`[data-i="${idx}"]`);
        el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    }
  }

  onDestroy(() => {
    if (scrollRAF) cancelAnimationFrame(scrollRAF);
  });
</script>

<div class="lyrics-card card">
  <div class="lyrics-header">
    <h2>Lyrics</h2>
    <span class="lyrics-meta">{meta}</span>
  </div>
  <div class="lyrics-body" bind:this={container}>
    {#if statusMsg}
      <div class="lyrics-empty">{statusMsg}</div>
    {:else if lines.length > 0}
      {#each lines as line, i (i)}
        <div
          class="lyrics-line"
          class:active={i === activeIdx}
          class:past={i < activeIdx}
          data-i={i}
        >
          {line.text}
        </div>
      {/each}
    {:else if plainLines.length > 0}
      {#each plainLines as line, i (i)}
        <div class="lyrics-line">{line}</div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .lyrics-card {
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  .lyrics-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .lyrics-header h2 {
    font-size: 0.9rem;
    font-weight: 600;
  }
  .lyrics-meta {
    font-size: 11px;
    color: var(--text-muted);
  }
  .lyrics-body {
    flex: 1;
    overflow-y: auto;
    max-height: 420px;
  }
  .lyrics-line {
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 13px;
    line-height: 1.8;
    color: var(--text-muted);
    transition: all 0.3s ease;
  }
  .lyrics-line.active {
    color: var(--text);
    background: var(--primary-glow);
    font-weight: 500;
  }
  .lyrics-line.past {
    color: var(--text-muted);
    opacity: 0.5;
  }
  .lyrics-empty {
    text-align: center;
    padding: 40px 16px;
    color: var(--text-muted);
    font-size: 13px;
  }
  @media (max-width: 768px) {
    .lyrics-body {
      max-height: 250px;
    }
  }
</style>
