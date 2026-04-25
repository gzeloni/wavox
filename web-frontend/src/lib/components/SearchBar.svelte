<script lang="ts">
  import { api } from '$lib/api';
  import { guildId } from '$lib/stores/player';
  import { fmtTime } from '$lib/utils';
  import type { SearchResult } from '$lib/types';

  let query = '';
  let suggestions: SearchResult[] = [];
  let open = false;
  let loading = false;
  let timer: ReturnType<typeof setTimeout> | null = null;

  async function fetchSuggestions(q: string) {
    const id = $guildId;
    if (!id || q.length < 2 || q.startsWith('http://') || q.startsWith('https://')) {
      close();
      return;
    }
    loading = true;
    open = true;
    try {
      suggestions = await api.search(id, q);
    } catch {
      suggestions = [];
    }
    loading = false;
  }

  function onInput() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fetchSuggestions(query.trim()), 400);
  }

  function close() {
    open = false;
    suggestions = [];
  }

  async function play(q: string) {
    const id = $guildId;
    if (!id || !q) return;
    await api.playback(id, 'play', { query: q });
    query = '';
    close();
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') play(query.trim());
    if (e.key === 'Escape') close();
  }

  function handleDocClick(e: MouseEvent) {
    if (!(e.target as HTMLElement).closest('.search-wrapper')) close();
  }
</script>

<svelte:window on:click={handleDocClick} />

<div class="search-bar">
  <div class="search-wrapper">
    <input
      type="text"
      class="search-input"
      placeholder="Search or paste a URL to play..."
      autocomplete="off"
      bind:value={query}
      on:input={onInput}
      on:keydown={onKeydown}
    />
    {#if open}
      <div class="search-suggestions">
        {#if loading}
          <div class="search-loading">Searching...</div>
        {:else if suggestions.length === 0}
          <div class="search-loading">No results found.</div>
        {:else}
          {#each suggestions as r, i (r.url || i)}
            <button
              type="button"
              class="search-suggestion"
              on:click={() => play(r.url || r.title)}
            >
              <div class="info">
                <div class="title">{r.title}</div>
                <div class="channel">{r.channel}</div>
              </div>
              <span class="dur">{fmtTime(r.duration)}</span>
              <span class="source source-{r.source}">{r.source[0].toUpperCase()}</span>
            </button>
          {/each}
        {/if}
      </div>
    {/if}
  </div>
  <button class="search-btn" on:click={() => play(query.trim())}>
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
    Play
  </button>
</div>

<style>
  .search-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
  }
  .search-wrapper {
    position: relative;
    flex: 1;
  }
  .search-input {
    width: 100%;
    padding: 10px 16px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    font-size: 14px;
    font-family: inherit;
    transition: border-color 0.2s;
  }
  .search-input:focus {
    outline: none;
    border-color: var(--primary);
  }
  .search-input::placeholder {
    color: var(--text-muted);
  }
  .search-btn {
    padding: 10px 20px;
    border-radius: 10px;
    border: none;
    background: var(--primary);
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .search-btn:hover {
    background: var(--primary-hover);
  }
  .search-suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 50;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-top: 4px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    max-height: 320px;
    overflow-y: auto;
  }
  .search-suggestion {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    cursor: pointer;
    transition: background 0.15s;
    width: 100%;
    border: none;
    background: transparent;
    color: inherit;
    text-align: left;
    font: inherit;
  }
  .search-suggestion:hover {
    background: var(--surface2);
  }
  .info {
    flex: 1;
    min-width: 0;
  }
  .title {
    font-size: 13px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .channel {
    font-size: 11px;
    color: var(--text-muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .dur {
    font-size: 11px;
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .source {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 700;
    color: #fff;
  }
  .source-youtube {
    background: #ff0000;
  }
  .source-spotify {
    background: #1db954;
  }
  .source-soundcloud {
    background: #ff5500;
  }
  .search-loading {
    padding: 16px;
    text-align: center;
    color: var(--text-muted);
    font-size: 12px;
  }
</style>
