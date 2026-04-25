<script lang="ts">
  import { onDestroy } from 'svelte';
  import { state, elapsed, lyrics } from '$lib/stores/player';
  import { parseLRC, type LRCLine } from '$lib/utils';
  import type { LyricsResponse } from '$lib/types';

  let lines: LRCLine[] = [];
  let plainLines: string[] = [];
  let meta = '';
  let modeLabel = '';
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
    modeLabel = '';
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
      modeLabel = 'Synced';
      statusMsg = '';
    } else if (data.plain) {
      plainLines = data.plain.split('\n').map((line) => line || '\u00A0');
      modeLabel = 'Plain';
      statusMsg = '';
    } else {
      statusMsg = 'No lyrics found for this track.';
    }

    if (data.artist || data.title) {
      meta = `${data.artist ?? ''} - ${data.title ?? ''}`;
    }
  }

  let scrollRAF: number | null = null;

  function clampScrollTop(value: number) {
    const maxScrollTop = Math.max(container.scrollHeight - container.clientHeight, 0);
    return Math.min(Math.max(value, 0), maxScrollTop);
  }

  function scrollLineIntoLyricsView(line: HTMLDivElement) {
    const containerRect = container.getBoundingClientRect();
    const lineRect = line.getBoundingClientRect();
    const centeredTop =
      container.scrollTop +
      lineRect.top -
      containerRect.top -
      (container.clientHeight - lineRect.height) / 2;

    container.scrollTo({
      top: clampScrollTop(centeredTop),
      behavior: 'smooth'
    });
  }

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
        if (el) scrollLineIntoLyricsView(el);
      });
    }
  }

  onDestroy(() => {
    if (scrollRAF) cancelAnimationFrame(scrollRAF);
  });
</script>

<div class="lyrics-card card">
  <div class="lyrics-header">
    <div>
      <div class="lyrics-kicker">Lyrics</div>
      <h2>{meta || 'Track text'}</h2>
    </div>
    {#if modeLabel}
      <span class="lyrics-mode">{modeLabel}</span>
    {/if}
  </div>

  <div class="lyrics-body" bind:this={container}>
    {#if statusMsg}
      <div class="lyrics-empty">{statusMsg}</div>
    {:else if lines.length > 0}
      {#each lines as line, i (i)}
        <div class="lyrics-line" class:active={i === activeIdx} class:past={i < activeIdx} data-i={i}>
          {line.text}
        </div>
      {/each}
    {:else if plainLines.length > 0}
      {#each plainLines as line, i (i)}
        <div class="lyrics-line plain">{line}</div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .lyrics-card {
    display: grid;
    gap: 14px;
    height: 420px;
    max-height: 420px;
    padding: 16px;
  }

  .lyrics-header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 12px;
  }

  .lyrics-kicker {
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .lyrics-header h2 {
    margin-top: 4px;
    font-size: 15px;
    line-height: 1.4;
    word-break: break-word;
  }

  .lyrics-mode {
    min-height: 28px;
    padding: 0 10px;
    border: 1px solid var(--border);
    border-radius: 999px;
    color: var(--text-muted);
    font-size: 12px;
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
  }

  .lyrics-body {
    min-height: 0;
    overflow-y: auto;
    max-height: 100%;
  }

  .lyrics-line {
    max-width: 72ch;
    padding: 8px 0;
    color: rgba(238, 242, 255, 0.55);
    font-size: 14px;
    line-height: 1.75;
  }

  .lyrics-line.active {
    color: var(--text);
    font-weight: 600;
  }

  .lyrics-line.past {
    opacity: 0.5;
  }

  .lyrics-line.plain {
    color: rgba(238, 242, 255, 0.72);
  }

  .lyrics-empty {
    color: var(--text-muted);
    font-size: 14px;
    padding: 12px 0;
  }

  @media (max-width: 640px) {
    .lyrics-card {
      height: 280px;
      max-height: 280px;
    }

    .lyrics-header {
      flex-direction: column;
      align-items: start;
    }

    .lyrics-line {
      font-size: 13px;
    }
  }
</style>
